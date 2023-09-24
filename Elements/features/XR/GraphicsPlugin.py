import abc
import platform
import logging
from typing import List, Optional, Dict
import Elements.pyECSS.math_utilities as util
from ctypes import Structure, POINTER, cast, byref
from Elements.pyGLV.GL.Scene import Scene
import Elements.pyECSS.System as System
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, RenderGLShaderSystem
from Elements.pyECSS.Entity import Entity
from Elements.features.XR.options import options
from OpenGL import GL, WGL
import glfw
import numpy as np
import math
import xr

logger = logging.getLogger("XRprogram.OpenGLPlugin")

def invert_rigid_body(m):
        """
        
        """
        result = np.empty([4,4],dtype=np.float32)
        result[0,0] = m[0,0]
        result[0,1] = m[1,0]
        result[0,2] = m[2,0]
        result[0,3] = 0.0
        result[1,0] = m[0,1]
        result[1,1] = m[1,1]
        result[1,2] = m[2,1]
        result[1,3] = 0.0
        result[2,0] = m[0,2]
        result[2,1] = m[1,2]
        result[2,2] = m[2,2]
        result[2,3] = 0.0
        result[3,0] = -(m[0,0] * m[3,0] + m[0,1] * m[3,1] + m[0,2] * m[3,2])
        result[3,1] = -(m[1,0] * m[3,0] + m[1,1] * m[3,1] + m[1,2] * m[3,2])
        result[3,2] = -(m[2,0] * m[3,0] + m[2,1] * m[3,1] + m[2,2] * m[3,2])
        result[3,3] = 1.0

        return result

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

        self.head: Entity
        self.head = None

        self.gizmos_Mode = "DISAPPEAR"
        self.all_gizmos = set()
        self.translate_gizmos = set()
        self.rotation_gizmos = set()
        self.scaling_gizmos = set()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.window:
            glfw.make_context_current(self.window)
        if self.swapchain_framebuffer is not None:
            GL.glDeleteFramebuffers(1, [self.swapchain_framebuffer])
        
        self.swapchain_framebuffer = None
        self.program = None

        for color, depth in self.color_to_depth_map.items():
            if depth is not None:
                GL.glDeleteTextures(1, [depth])
        self.color_to_depth_map = {}
        if self.window is not None:
            glfw.destroy_window(self.window)
            self.window = None
        glfw.terminate()

    @property
    def instance_extensions(self) -> List[str]:
        return [xr.KHR_OPENGL_ENABLE_EXTENSION_NAME]
    
    def set_Head(self,_Head: Entity):
        """
        Setter method for Head Entity
        Arguments:
            self: self
            _Head: Head Entity
        Returns:
            None
        """
        self.head = _Head

    def set_translation_gizmos(self,x: str,y: str,z: str):
        """
        """
        self.translate_gizmos.add(x)
        self.translate_gizmos.add(y)
        self.translate_gizmos.add(z)
        
        self.all_gizmos.add(x)
        self.all_gizmos.add(y)
        self.all_gizmos.add(z)

    def set_rotation_gizmos(self,x: str,y: str,z: str):
        """
        """
        self.rotation_gizmos.add(x)
        self.rotation_gizmos.add(y)
        self.rotation_gizmos.add(z)
        
        self.all_gizmos.add(x)
        self.all_gizmos.add(y)
        self.all_gizmos.add(z)

    def set_scaling_gizmos(self,x: str,y: str,z: str,line_X: str,line_y: str,line_z: str):
        """
        """
        self.scaling_gizmos.add(x)
        self.scaling_gizmos.add(y)
        self.scaling_gizmos.add(z)
        self.scaling_gizmos.add(line_X)
        self.scaling_gizmos.add(line_y)
        self.scaling_gizmos.add(line_z)
        
        self.all_gizmos.add(x)
        self.all_gizmos.add(y)
        self.all_gizmos.add(z)
        self.all_gizmos.add(line_X)
        self.all_gizmos.add(line_y)
        self.all_gizmos.add(line_z)

    def set_gizmos_mode(self, _mode: str):
        self.gizmos_Mode = _mode

    def is_active_gizmo(self,name: str):
        """
        
        """
        if name in self.translate_gizmos and self.gizmos_Mode=="Translate":
            return True
        if name in self.rotation_gizmos and self.gizmos_Mode=="Rotate":
            return True
        if name in self.scaling_gizmos and self.gizmos_Mode=="Scale":
            return True

        return False
    
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
        print(f"OpenGL version {major}.{minor}")
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
        self.initialize_resources(renderer)

    def initialize_resources(self,renderer: InitGLShaderSystem):
        """
        Initialize only the required components for 
        Arguments:
            self: self
            renderer: System that initializes all the required elements from the scene
        Returns:
            None
        """
        scene = Scene()
        self.swapchain_framebuffer = GL.glGenFramebuffers(1)
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
    
    def poll_events(self) -> bool:
        glfw.poll_events()
        return glfw.window_should_close(self.window)

    def Render_View(self, 
                    layer_view: xr.CompositionLayerProjectionView,
                    swapchain_image_base_ptr: POINTER(xr.SwapchainImageBaseHeader),
                    _swapchain_format: int,
                    renderUpdate: RenderGLShaderSystem,
                    offset=util.vec(0.064),
                    mirror=False
                    ):
        """
        Renders scene from a given view
        Arguments:
            self: self
            layer_view: holds all necessary information needed to render a view
            swapchain_image_base_ptr:
            _swapchain_format:
            renderUpdate: System that updates uniform variables from the scene
            mirror: if true show left eye's view  on the glfw window
        Returns:
            None
        """
        assert layer_view.sub_image.image_array_index == 0

        scene = Scene()
        
        glfw.make_context_current(self.window)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER,self.swapchain_framebuffer)

        swapchain_image = cast(swapchain_image_base_ptr, POINTER(xr.SwapchainImageOpenGLKHR)).contents
        GL.glViewport(layer_view.sub_image.image_rect.offset.x,
                      layer_view.sub_image.image_rect.offset.y,
                      layer_view.sub_image.image_rect.extent.width,
                      layer_view.sub_image.image_rect.extent.height)
        print("Inside Render_View:")
        print("Viewport parameters:")
        print("offset: (x,y) = (",layer_view.sub_image.image_rect.offset.x,",",layer_view.sub_image.image_rect.offset.y,")")
        print("Width: ",layer_view.sub_image.image_rect.extent.width)
        print("Height: ",layer_view.sub_image.image_rect.extent.height)

        GL.glFrontFace(GL.GL_CCW)
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
        
        scene.world.traverse_visit(renderUpdate,scene.world.root)

        model_head = self.head.getChild(0).l2world
        position = layer_view.pose.position
        orientation = layer_view.pose.orientation
        fov = layer_view.fov
        translation = model_head @ util.translate(position.x,position.y,position.z)
        rotation = create_xr_quaternion(util.quaternion(orientation.x,orientation.y,orientation.z,orientation.w))
        print("View Translation: ",position)
        print("View Rotation: ",orientation)
        print("fov: ",fov)

        #aspect_ratio = layer_view.sub_image.image_rect.extent.width / layer_view.sub_image.image_rect.extent.height
        #aspect_ratio = layer_view.sub_image.image_rect.extent.height / layer_view.sub_image.image_rect.extent.width
        #proj = util.perspective(100.0,aspect_ratio,0.01,60.0)

        proj = create_xr_projection(math.tan(fov.angle_left),
                                    math.tan(fov.angle_right),
                                    math.tan(fov.angle_up),
                                    math.tan(fov.angle_down),0.01,120.0)

        #view = translation @ rotation @ util.scale(2.5,2.5,2.5) 
        view = rotation @ translation @ util.scale(2.5,2.5,2.5)

        #Update each shader's projection & view
        element: Entity
        for element in scene.world.root:
            if element is not None and element.getClassName()=="ShaderGLDecorator":
                model = element.parent.getChild(0).l2world
                #model = element.parent.getChild(0).l2world @ util.translate(offset)
                mvp = proj @ view @ model

                parent = element.parent.name

                if parent not in self.all_gizmos:
                    element.setUniformVariable(key='Proj', value=proj, mat4=True)
                    element.setUniformVariable(key='View', value=view, mat4=True)
                    element.setUniformVariable(key='model', value=model, mat4=True)
                    element.setUniformVariable(key='modelViewProj', value=mvp, mat4=True)
                else:
                    if self.is_active_gizmo(parent):
                        element.setUniformVariable(key='modelViewProj', value=mvp, mat4=True)
                    else:
                        element.setUniformVariable(key='modelViewProj', value=0.0, mat4=True)


        #if mirror:
        #    GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, 0)
        #    w, h = layer_view.sub_image.image_rect.extent.width, layer_view.sub_image.image_rect.extent.height
        #    GL.glBlitFramebuffer(
        #        0, 0, w, h, 0, 0,
        #        640, 480,
        #        GL.GL_COLOR_BUFFER_BIT,
        #        GL.GL_NEAREST
        #    )

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    def window_should_close(self):
        return glfw.window_should_close(self.window)

def create_xr_projection(tan_angle_left, tan_angle_right, tan_angle_up,tan_angle_down, near_z, far_z):
    
    tan_angle_width = tan_angle_right - tan_angle_left
    tan_angle_height = tan_angle_up - tan_angle_down #OpenGL
    offset_z = near_z

    result = np.empty([4,4],dtype=np.float32)

    if far_z <= near_z:
            # place the far plane at infinity
            result[0][0] = 2.0 / tan_angle_width
            result[0][1] = 0.0
            result[0][2] = (tan_angle_right + tan_angle_left) / tan_angle_width
            result[0][3] = 0.0

            result[1][0] = 0.0
            result[1][1] = 2.0 / tan_angle_height
            result[1][2] = (tan_angle_up + tan_angle_down) / tan_angle_height
            result[1][3] = 0.0

            result[2][0] = 0.0
            result[2][1] = 0.0
            result[2][2] = -1.0
            result[2][3] = -(near_z + offset_z)
    else:
            # normal projection
            result[0][0] = 2.0 / tan_angle_width
            result[0][1] = 0.0
            result[0][2] = (tan_angle_right + tan_angle_left) / tan_angle_width
            result[0][3] = 0.0

            result[1][0] = 0.0
            result[1][1] = 2.0 / tan_angle_height
            result[1][2] = (tan_angle_up + tan_angle_down) / tan_angle_height
            result[1][3] = 0.0

            result[2][0] = 0.0
            result[2][1] = 0.0
            result[2][2] = -(far_z + offset_z) / (far_z - near_z)
            result[2][3] = -(far_z * (near_z + offset_z)) / (far_z - near_z)

    result[3][0] = 0.0
    result[3][1] = 0.0
    result[3][2] = -1.0
    result[3][3] = 0.0

    return result

def create_xr_quaternion(quat):

    x2 = quat[0] + quat[0]
    y2 = quat[1] + quat[1]
    z2 = quat[2] + quat[2]

    xx2 = quat[0] * x2
    yy2 = quat[1] * y2
    zz2 = quat[2] * z2

    yz2 = quat[1] * z2
    wx2 = quat[3] * x2
    xy2 = quat[0] * y2
    wz2 = quat[3] * z2
    xz2 = quat[0] * z2
    wy2 = quat[3] * y2

    result = np.empty([4,4],dtype=np.float32)

    result[0][0] = 1.0 - yy2 - zz2
    result[0][1] = xy2 + wz2
    result[0][2] = xz2 - wy2
    result[0][3] = 0.0

    result[1][0] = xy2 - wz2
    result[1][1] = 1.0 - xx2 - zz2
    result[1][2] = yz2 + wx2
    result[1][3] = 0.0

    result[2][0] = xz2 + wy2
    result[2][1] = yz2 - wx2
    result[2][2] = 1.0 - xx2 - yy2
    result[2][3] = 0.0

    result[3][0] = 0.0
    result[3][1] = 0.0
    result[3][2] = 0.0
    result[3][3] = 1.0

    return result