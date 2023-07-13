import abc
import platform
import logging
from typing import List, Optional, Dict
import Elements.pyECSS.utilities as util
from ctypes import Structure, POINTER, cast, byref
from Elements.pyGLV.GL.Scene import Scene
import Elements.pyECSS.System as System
from Elements.pyGLV.GL.Shader import ShaderGLDecorator, InitGLShaderSystem, RenderGLShaderSystem
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyECSS.Entity import Entity
import Elements.pyECSS.Component as Component
from Elements.pyGLV.XR.options import options
from OpenGL import GL, WGL
import glfw

import xr

logger = logging.getLogger("XRprogram.OpenGLPlugin")

class GraphicsPlugin(object):
    
    @abc.abstractmethod
    def __enter__(self):
        pass

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abc.abstractmethod
    def get_supported_swapchain_sample_count(self, xr_view_configuration_view: xr.ViewConfigurationView) -> int:
        pass

    @property
    @abc.abstractmethod
    def graphics_binding(self) -> Structure:
        pass

    @property
    @abc.abstractmethod
    def initialize_device(self, instance: xr.Instance, system_id: xr.SystemId) -> None:
        pass

    @property
    @abc.abstractmethod
    def instance_extensions(self):
        pass

    @abc.abstractmethod
    def poll_events(self) -> bool:
        pass

    @abc.abstractmethod
    def select_color_swapchain_format(self, runtime_formats) -> int:
        pass

    @property
    @abc.abstractmethod
    def swapchain_image_type(self):
        pass

    @abc.abstractmethod
    def update_options(self, options) -> None:
        pass

    @abc.abstractmethod
    def Render_View(self, 
                    layer_view: xr.CompositionLayerProjectionView,
                    swapchain_image_base_ptr: POINTER(xr.SwapchainImageBaseHeader),
                    _swapchain_format: int,
                    scene: Scene,
                    renderUpdate: System
                    #mirror=False
                    ):
        pass

class OpenGLPlugin(GraphicsPlugin):
    def __init__(self,options: options) -> None:
        super().__init__()

        if platform.system() == "Windows":
            self._graphics_binding = xr.GraphicsBindingOpenGLWin32KHR()
        else:
            raise NotImplementedError
        self.swapchain_image_buffers: List[xr.SwapchainImageOpenGLKHR] = []  # To keep the swapchain images alive
        self.swapchain_framebuffer: Optional[int] = None
        self.debug_message_proc = None  # To keep the callback alive
        self.background_clear_color = options.background_clear_color
        self.window = None
        self.color_to_depth_map: Dict[int, int] = {}
        self.debug_message_proc = None

    @property
    def instance_extensions(self) -> List[str]:
        return [xr.KHR_OPENGL_ENABLE_EXTENSION_NAME]
    
    def focus_window(self):
        glfw.focus_window(self.window)
        glfw.make_context_current(self.window)

    def get_depth_texture(self, color_texture) -> int:
        # If a depth-stencil view has already been created for this back-buffer, use it.
        if color_texture in self.color_to_depth_map:
            return self.color_to_depth_map[color_texture]
        # This back-buffer has no corresponding depth-stencil texture, so create one with matching dimensions.
        GL.glBindTexture(GL.GL_TEXTURE_2D, color_texture)
        width = GL.glGetTexLevelParameteriv(GL.GL_TEXTURE_2D, 0, GL.GL_TEXTURE_WIDTH)
        height = GL.glGetTexLevelParameteriv(GL.GL_TEXTURE_2D, 0, GL.GL_TEXTURE_HEIGHT)

        depth_texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, depth_texture)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_DEPTH_COMPONENT32, width, height, 0, GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT, None)
        self.color_to_depth_map[color_texture] = depth_texture
        return depth_texture

    def initialize_device(self, 
                          instance: xr.Instance, 
                          system_id: xr.SystemId,
                          renderer: InitGLShaderSystem):
        scene = Scene()
        pfn_get_open_gl_graphics_requirements_khr = cast(
            xr.get_instance_proc_addr(
                instance,
                "xrGetOpenGLGraphicsRequirementsKHR",
            ),
            xr.PFN_xrGetOpenGLGraphicsRequirementsKHR
        )
        graphics_requirements = xr.GraphicsRequirementsOpenGLKHR()
        result = pfn_get_open_gl_graphics_requirements_khr(instance, system_id, byref(graphics_requirements))
        result = xr.check_result(xr.Result(result))
        if result.is_exception():
            raise result
        # Initialize the gl extensions. Note we have to open a window.
        if not glfw.init():
            raise xr.XrException("GLFW initialization failed")
        glfw.window_hint(glfw.DOUBLEBUFFER, False)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 5)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        self.window = glfw.create_window(640, 480, "GLFW Window", None, None)
        if self.window is None:
            raise xr.XrException("Failed to create GLFW window")
        glfw.make_context_current(self.window)
        glfw.show_window(self.window)
        glfw.swap_interval(0)
        glfw.focus_window(self.window)
        major = GL.glGetIntegerv(GL.GL_MAJOR_VERSION)
        minor = GL.glGetIntegerv(GL.GL_MINOR_VERSION)
        desired_api_version = xr.Version(major, minor, 0)
        if graphics_requirements.min_api_version_supported > desired_api_version.number():
            ms = xr.Version(graphics_requirements.min_api_version_supported).number()
            raise xr.XrException(f"Runtime does not support desired Graphics API and/or version {hex(ms)}")
        if platform.system() == "Windows":
            self._graphics_binding.h_dc = WGL.wglGetCurrentDC()
            self._graphics_binding.h_glrc = WGL.wglGetCurrentContext()

        #Add other platforms cases here

        self.debug_message_proc = GL.GLDEBUGPROC(self.opengl_debug_message_callback)
        GL.glDebugMessageCallback(self.debug_message_proc, None)
        self.initialize_resources(renderer,scene)

    def initialize_resources(self,renderer: InitGLShaderSystem,scene: Scene):
        self.swapchain_framebuffer = GL.glGenFramebuffers(1)
        #scene.world.traverse_visit(renderer, scene.world.root)
        for component in scene.world.root:
            if component is not None:
                if component.getClassName()=="VertexArray":
                    renderer.apply2VertexArray(component)
                elif component.getClassName()=="RenderMesh":
                    renderer.apply2RenderMesh(component)
                elif component.getClassName()=="Shader":
                    renderer.apply2Shader(component)
                elif component.getClassName()=="ShaderGLDecorator":
                    renderer.apply2ShaderGLDecorator(component)




    @property
    def swapchain_image_type(self):
        return xr.SwapchainImageOpenGLKHR

    @property
    def graphics_binding(self) -> Structure:
        return self._graphics_binding
    
    @staticmethod
    def opengl_debug_message_callback(_source, _msg_type, _msg_id, severity, length, raw, _user):
        """Redirect OpenGL debug messages"""
        log_level = {
            GL.GL_DEBUG_SEVERITY_HIGH: logging.ERROR,
            GL.GL_DEBUG_SEVERITY_MEDIUM: logging.WARNING,
            GL.GL_DEBUG_SEVERITY_LOW: logging.INFO,
            GL.GL_DEBUG_SEVERITY_NOTIFICATION: logging.DEBUG,
        }[severity]
        logger.log(log_level, f"OpenGL Message: {raw[0:length].decode()}")

    def get_supported_swapchain_sample_count(self, xr_view_configuration_view: xr.ViewConfigurationView) -> int:
        return 1
    
    def select_color_swapchain_format(self, runtime_formats):
        # List of supported color swapchain formats.
        supported_color_swapchain_formats = [
            GL.GL_RGB10_A2,
            GL.GL_RGBA16F,
            GL.GL_RGBA8,
            GL.GL_RGBA8_SNORM,
            GL.GL_SRGB8,
            GL.GL_SRGB8_ALPHA8,
        ]
        for rf in runtime_formats:
            for sf in supported_color_swapchain_formats:
                if rf == sf:
                    return sf
        raise RuntimeError("No runtime swapchain format supported for color swapchain")
    
    def Render_View(self, 
                    layer_view: xr.CompositionLayerProjectionView,
                    swapchain_image_base_ptr: POINTER(xr.SwapchainImageBaseHeader),
                    _swapchain_format: int,
                    scene: Scene,
                    renderUpdate: RenderGLShaderSystem,
                    mirror=False
                    ):
        assert layer_view.sub_image.image_array_index == 0
        glfw.make_context_current(self.window)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER,self.swapchain_framebuffer)

        swapchain_image = cast(swapchain_image_base_ptr, POINTER(xr.SwapchainImageOpenGLKHR)).contents
        GL.glViewport(layer_view.sub_image.image_rect.offset.x,
                      layer_view.sub_image.image_rect.offset.y,
                      layer_view.sub_image.image_rect.extent.width,
                      layer_view.sub_image.image_rect.extent.height)

        GL.glFrontFace(GL.GL_CW)
        GL.glCullFace(GL.GL_BACK)
        GL.glEnable(GL.GL_CULL_FACE)
        GL.glEnable(GL.GL_DEPTH_TEST)
        
        color_texture = swapchain_image.image
        depth_texture = self.get_depth_texture(color_texture)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, color_texture, 0)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT, GL.GL_TEXTURE_2D, depth_texture, 0)

        GL.glClearColor(*self.background_clear_color)
        GL.glClearDepth(1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT | GL.GL_STENCIL_BUFFER_BIT)
        
        #fov is used for an Ortho Projection
        proj = util.ortho(layer_view.fov.angle_left,
                          layer_view.fov.angle_right,
                          layer_view.fov.angle_down,
                          layer_view.fov.angle_up,
                          0.05,
                          100.0)

        #openXR calls this position
        eye = util.vec(layer_view.pose.position.x,
                           layer_view.pose.position.y,
                           layer_view.pose.position.z
                           )

        #openXR calls this orientation
        target = util.vec(layer_view.pose.orientation.x,
                        layer_view.pose.orientation.y,
                        layer_view.pose.orientation.z) 

        up = util.vec(1.0,1.0,1.0)
            
        view = util.lookat(eye,target,up)

        print("Visiting vertex arrays")
        #Traverse world
        for component in scene.world.root:
            if component is not None:
                if component.getClassName()=="VertexArray":
                    renderUpdate.apply2VertexArray(component)
        print("After Visiting vertex arrays")

        #Update each shader's projection & view
        element: Entity
        for element in scene.world.root:
            if element is not None and element.getClassName()=="ShaderGLDecorator":
                #Note: All shaders should get their View-Projection the same way for this loop to work
                element.setUniformVariable(key='Proj', value=proj, mat4=True)
                element.setUniformVariable(key='View', value=view, mat4=True)

        if mirror:
            GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, 0)
            w, h = layer_view.sub_image.image_rect.extent.width, layer_view.sub_image.image_rect.extent.height
            GL.glBlitFramebuffer(
                0, 0, w, h, 0, 0,
                640, 480,
                GL.GL_COLOR_BUFFER_BIT,
                GL.GL_NEAREST
            )

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

