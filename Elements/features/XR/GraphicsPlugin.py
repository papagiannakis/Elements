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

class XR_Shaders:
    COLOR_VERT_MVP_XR = """
        #version 410

        layout (location=0) in vec4 vPosition;
        layout (location=1) in vec4 vColor;

        out     vec4 color;

        uniform mat4 model;
        uniform mat4 View;
        uniform mat4 Proj;

        
        void main()
        {
            gl_Position =  Proj * View * model * vPos;
            color = vColor;
        }
    """
    COLOR_FRAG_XR = """
        #version 410

        in vec4 color;
        out vec4 outputColor;

        void main()
        {
            outputColor = color;
            //outputColor = vec4(0.1, 0.1, 0.1, 1);
        }
    """
    VERT_PHONG_MVP_XR = """
        #version 410

        layout (location=0) in vec4 vPosition;
        layout (location=1) in vec4 vColor;
        layout (location=2) in vec4 vNormal;

        out     vec4 pos;
        out     vec4 color;
        out     vec3 normal;
        
        uniform mat4 model;
        uniform mat4 View;
        uniform mat4 Proj;

        void main()
        {
            gl_Position =  Proj * View * model * vPos;
            pos = model * vPosition;
            color = vColor;
            normal = mat3(transpose(inverse(model))) * vNormal.xyz;
        }
    """
    FRAG_PHONG_XR = """
        #version 410

        in vec4 pos;
        in vec4 color;
        in vec3 normal;

        out vec4 outputColor;

        // Phong products
        uniform vec3 ambientColor;
        uniform float ambientStr;

        // Lighting 
        uniform vec3 viewPos;
        uniform vec3 lightPos;
        uniform vec3 lightColor;
        uniform float lightIntensity;

        // Material
        uniform float shininess;
        uniform vec3 matColor;

        void main()
        {
            vec3 norm = normalize(normal);
            vec3 lightDir = normalize(lightPos - pos.xyz);
            vec3 viewDir = normalize(viewPos - pos.xyz);
            vec3 reflectDir = reflect(-lightDir, norm);
            

            // Ambient
            vec3 ambientProduct = ambientStr * ambientColor;
            // Diffuse
            float diffuseStr = max(dot(norm, lightDir), 0.0);
            vec3 diffuseProduct = diffuseStr * lightColor;
            // Specular
            float specularStr = pow(max(dot(viewDir, reflectDir), 0.0), 32);
            vec3 specularProduct = shininess * specularStr * color.xyz;
            
            vec3 result = (ambientProduct + (diffuseProduct + specularProduct) * lightIntensity) * color.xyz;
            outputColor = vec4(result, 1);
        }
    """
    SIMPLE_TEXTURE_VERT_XR = """
        #version 410

        layout (location=0) in vec4 vPos;
        layout (location=1) in vec2 vTexCoord;

        out vec2 fragmentTexCoord;

        uniform mat4 model;
        uniform mat4 View;
        uniform mat4 Proj;

        void main()
        {
            gl_Position =  Proj * View * model * vPos;
            fragmentTexCoord = vTexCoord;
        }
    """
    SIMPLE_TEXTURE_FRAG_XR = """
        #version 410
        
        in vec2 fragmentTexCoord;

        out vec4 color;

        uniform sampler2D ImageTexture;

        void main()
        {
            //vec2 flipped_texcoord = vec2(fragmentTexCoord.x, 1.0 - fragmentTexCoord.y);
            //color = texture(ImageTexture,flipped_texcoord);

            color = texture(ImageTexture,fragmentTexCoord);
        }
    """
    SIMPLE_TEXTURE_PHONG_VERT_XR = """
        #version 410

        layout (location=0) in vec4 vPos;
        layout (location=1) in vec4 vNormal;
        layout (location=2) in vec2 vTexCoord;

        out vec2 fragmentTexCoord;
        out vec4 pos;
        out vec3 normal;

        uniform mat4 model;
        uniform mat4 View;
        uniform mat4 Proj;

        void main()
        {
            gl_Position =  Proj * View * model * vPos;
            pos = model * vPos;
            fragmentTexCoord = vTexCoord;
            normal = mat3(transpose(inverse(model))) * vNormal.xyz;
        }
    """
    SIMPLE_TEXTURE_PHONG_FRAG_XR = """
        #version 410
        
        in vec2 fragmentTexCoord;
        in vec4 pos;
        in vec3 normal;

        out vec4 outputColor;

        // Phong products
        uniform vec3 ambientColor;
        uniform float ambientStr;

        // Lighting 
        uniform vec3 viewPos;
        uniform vec3 lightPos;
        uniform vec3 lightColor;
        uniform float lightIntensity;

        // Material
        uniform float shininess;
        //uniform vec3 matColor;

        uniform sampler2D ImageTexture;

        void main()
        {
            vec3 norm = normalize(normal);
            vec3 lightDir = normalize(lightPos - pos.xyz);
            vec3 viewDir = normalize(viewPos - pos.xyz);
            vec3 reflectDir = reflect(-lightDir, norm);

            // Ambient
            vec3 ambientProduct = ambientStr * ambientColor;
            // Diffuse
            float diffuseStr = max(dot(norm, lightDir), 0.0);
            vec3 diffuseProduct = diffuseStr * lightColor;
            // Specular
            float specularStr = pow(max(dot(viewDir, reflectDir), 0.0), 32);

            vec4 tex = texture(ImageTexture,fragmentTexCoord);

            vec3 specularProduct = shininess * specularStr * tex.xyz;
            
            vec3 result = (ambientProduct + (diffuseProduct + specularProduct) * lightIntensity) * tex.xyz;
            outputColor = vec4(result, 1);
        }

    """
    TEXTURE_3D_VERT_XR = """
        #version 410

        layout (location=0) in vec4 vPos;

        out vec3 TexCoords;

        uniform mat4 model;
        uniform mat4 View;
        uniform mat4 Proj;

        void main()
        {
            gl_Position = Proj * View * model * vPos;
            TexCoords = vPos.xyz;
        }

    """
    TEXTURE_3D_FRAG_XR = """
        #version 410

        in vec3 TexCoords;

        out vec4 FragColor;

        uniform samplerCube cubemap; 

        void main()
        {             
            FragColor = texture(cubemap, TexCoords);
        } 
    """
    STATIC_SKYBOX_VERT_XR = """
        #version 410

        layout (location = 0) in vec4 vPos;

        out vec3 TexCoords;

        uniform mat4 Proj;
        uniform mat4 View;

        void main()
        {
            mat4 viewPos = mat4(mat3(View)); //removes Translation
            gl_Position = Proj * viewPos * vPos;

            //gl_Position = Proj * View * vPos; // with Translation

            TexCoords = vPos.xyz;
        } 

    """
    STATIC_SKYBOX_FRAG_XR = """
        #version 410
    
        out vec4 FragColor;

        in vec3 TexCoords;

        uniform samplerCube cubemap;

        void main()
        {    
            FragColor = texture(cubemap, TexCoords);
        }
    """

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
                    mirror=False
                    ):
        assert layer_view.sub_image.image_array_index == 0

        scene = Scene()
        
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
        
        """
        proj = util.ortho(layer_view.fov.angle_left,
                          layer_view.fov.angle_right,
                          layer_view.fov.angle_down,
                          layer_view.fov.angle_up,
                          0.05,
                          100.0)
        """

        aspect_ratio = layer_view.sub_image.image_rect.extent.width / layer_view.sub_image.image_rect.extent.height
        print(layer_view.sub_image.image_rect.extent.width)
        print(layer_view.sub_image.image_rect.extent.height)
        #aspect_ratio = 1.0

        proj = util.perspective(100.0,aspect_ratio,0.05,100.0)

        to_view = util.translate(layer_view.pose.position.x,
                           layer_view.pose.position.y,
                           layer_view.pose.position.z) @ util.quaternion_matrix(util.quaternion(layer_view.pose.orientation.x,
                                                                                                layer_view.pose.orientation.y,
                                                                                                layer_view.pose.orientation.z,
                                                                                                layer_view.pose.orientation.w)) @ util.scale(1.0,1.0,1.0)
        #view = invert_rigid_body(to_view)
        #view = util.inverse(to_view)

        view = to_view

        #Traverse Vertex Arrays
        scene.world.traverse_visit(renderUpdate,scene.world.root)

        #Update each shader's projection & view
        element: Entity
        for element in scene.world.root:
            if element is not None and element.getClassName()=="ShaderGLDecorator":
                #Note: All shaders should get their View and Projection the same way for this loop to work
                element.setUniformVariable(key='Proj', value=proj, mat4=True)
                element.setUniformVariable(key='View', value=view, mat4=True)

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