from __future__ import annotations
from abc import ABC, abstractmethod
import sys
import numpy as np
import OpenGL.GL as gl
import ctypes
from Elements.pyECSS.System import System
from Elements.pyECSS.Component import Component, BasicTransform, CompNullIterator
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyECSS.math_utilities import ortho, lookat, perspective
from Elements.definitions import SHADER_DIR

# unlike a standard Shader, this class holds specific 
# logic for depth shaders (Pass 1) and shadow receivers (Pass 2).
class ShadowShader(Component):
    """
    An OpenGL-GLSL Shader container Component class specifically for Shadows.
    """
    
    # Every GLSL shader this class uses lives in its own file under Elements/assets/shaders,
    # each carrying the explanation that used to sit here:
    #   pass 1 (depth maps)  DirDepth.vert/.frag, PointDepth.vert/.geom/.frag
    #   pass 2 (shading)     DirPhong.vert/.frag, PointPhong.vert/.frag
    #   debug views          ShadowDebug.vert, ShadowDebugDir.frag, ShadowDebugPoint.frag
    # Construct with vertex_import_file= / fragment_import_file=; a ShadowShader built with
    # neither falls back to the directional Phong pair in init().

    def __init__(self, name=None, type=None, id=None,
                 vertex_source=None, fragment_source=None, geometry_source=None,
                 vertex_import_file=None, fragment_import_file=None):
        super().__init__(name, type, id)

        self._parent = self
        self._glid = None

        self._texture = None

        # Dictionaries to hold uniform values
        self._mat4fDict = {}
        self._mat3fDict = {}
        self._float1fDict = {}
        self._float3fDict = {}
        self._float4fDict = {}
        self._aaaDict = {}
        self._textureDict = {}
        self._texture3DDict ={}

        # Prioritize import from file, and then from shader source string (same convention as
        # Elements.pyGLV.GL.Shader.Shader)
        if vertex_import_file is not None:
            try:
                f = open(vertex_import_file, 'r')
            except OSError:
                print("Could not open/read vertex shader file:", vertex_import_file)
                sys.exit()
            with f:
                self._vertex_source = f.read()
        else:
            self._vertex_source = vertex_source

        if fragment_import_file is not None:
            try:
                f = open(fragment_import_file, 'r')
            except OSError:
                print("Could not open/read fragment shader file:", fragment_import_file)
                sys.exit()
            with f:
                self._fragment_source = f.read()
        else:
            self._fragment_source = fragment_source

        self._geometry_source = geometry_source

    @property
    def glid(self): return self._glid
    
    def __del__(self):
        if self._glid:
            if gl and gl.glIsProgram(self._glid):
                gl.glDeleteProgram(self._glid)
    
    def disableShader(self):
        gl.glUseProgram(0)
    
    def enableShader(self):
        if self._glid is None:
            print(f"Error: Attempting to use uninitialized shader: {self.name}")
            return
        
        gl.glUseProgram(self._glid)
        
        # Apply all stored uniforms to the shader
        for k, v in self._mat4fDict.items():
            loc = gl.glGetUniformLocation(self._glid, k)
            if loc != -1: gl.glUniformMatrix4fv(loc, 1, True, v)
        for k, v in self._float1fDict.items():
            loc = gl.glGetUniformLocation(self._glid, k)
            if loc != -1: gl.glUniform1f(loc, v)
        for k, v in self._float3fDict.items():
            loc = gl.glGetUniformLocation(self._glid, k)
            if loc != -1: gl.glUniform3fv(loc, 1, v)
        for k, v in self._aaaDict.items():
            loc = gl.glGetUniformLocation(self._glid, k)
            if loc != -1: gl.glUniform1i(loc, int(v))
        for k,v in self._textureDict.items():
            loc = gl.glGetUniformLocation(self._glid, k)
            gl.glUniform1i(loc, v._texure_channel)
            v.bind()

    def setUniformVariable(self, key, value, mat4=False, float1=False, float3=False, boolean=False, texture=False, **kwargs):
        if mat4: self._mat4fDict[key] = value
        if float1: self._float1fDict[key] = value
        if float3: self._float3fDict[key] = value
        if boolean: self._aaaDict[key] = value 
        if texture: self._textureDict[key] = value
            
    @staticmethod
    def _compile_shader(src, shader_type):
        shader = gl.glCreateShader(shader_type)
        gl.glShaderSource(shader, src)
        gl.glCompileShader(shader)
        status = gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS)
        if not status:
            log = gl.glGetShaderInfoLog(shader).decode('ascii')
            gl.glDeleteShader(shader)
            print(f'Compile failed for {shader_type}\n{log}')
            return None
        return shader
        
    def init(self):
        # Default to Phong Directional if no source provided
        # Default to Phong Directional, read from its file only if nothing was supplied.
        if not self._vertex_source: self._vertex_source = (SHADER_DIR / "DirPhong.vert").read_text()
        if not self._fragment_source: self._fragment_source = (SHADER_DIR / "DirPhong.frag").read_text()

        vert = self._compile_shader(self._vertex_source, gl.GL_VERTEX_SHADER)
        frag = self._compile_shader(self._fragment_source, gl.GL_FRAGMENT_SHADER)
        
        geom = None
        if self._geometry_source:
            geom = self._compile_shader(self._geometry_source, gl.GL_GEOMETRY_SHADER)

        if vert and frag:
            self._glid = gl.glCreateProgram()
            gl.glAttachShader(self._glid, vert)
            gl.glAttachShader(self._glid, frag)
            if geom:
                gl.glAttachShader(self._glid, geom)
                
            gl.glLinkProgram(self._glid)
            gl.glDeleteShader(vert)
            gl.glDeleteShader(frag)
            if geom: gl.glDeleteShader(geom)

            status = gl.glGetProgramiv(self._glid, gl.GL_LINK_STATUS)
            if not status:
                print(gl.glGetProgramInfoLog(self._glid).decode('ascii'))
                gl.glDeleteProgram(self._glid)
                self._glid = None
    
    def update(self): pass
    def accept(self, system: System): pass
    def __iter__(self) -> CompNullIterator: return CompNullIterator(self)

class ShadowMappingSystem(System):
    def __init__(self, name=None, type=None, id=None, lightNode=None, lightTargetNode=None, shadowMapSize=1024, lightType="directional"):
        super().__init__(name, type, id)
        
        self._lightNode = lightNode 
        self._lightTargetNode = lightTargetNode 
        self._lightType = lightType 
        self._shadowMapSize = shadowMapSize

        # Framebuffer Object (FBO) variables
        # The FBO acts as a hidden canvas we draw to before drawing to the screen.
        self._depthMapFBO = None
        self._depthMapTexture = None
        self._depthShader = None
        self._depthShaderID = None

        # PASS MODE:
        # 0 = Idle
        # 1 = Generating Shadow Map (Depth Pass)
        # 2 = Rendering Scene (Lighting Pass)
        self._pass_mode = 0 
        
        self._lightSpaceMatrix = None
        self._shadowTransforms = [] 
        self._currentLightPos = np.array([0,0,0])
        self._far_plane = 100.0
        
        self._window_width = 1024
        self._window_height = 768

        # Debug/Viz Shader containers       
        self._debugShader = None
        self._quadVAO = None

    def init(self):
        # Create Framebuffer & Texture to store Depth
        self._depthMapFBO = gl.glGenFramebuffers(1)
        self._depthMapTexture = gl.glGenTextures(1)
        
        if self._lightType == "point":
            # A Cube Map is 6 textures combined into one.
            gl.glBindTexture(gl.GL_TEXTURE_CUBE_MAP, self._depthMapTexture)
            for i in range(6):
                # Allocate memory for 6 faces, 32-bit Float Depth
                gl.glTexImage2D(gl.GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, gl.GL_DEPTH_COMPONENT, 
                                self._shadowMapSize, self._shadowMapSize, 0, gl.GL_DEPTH_COMPONENT, gl.GL_FLOAT, None)
            gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
            gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
            gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP, gl.GL_TEXTURE_WRAP_R, gl.GL_CLAMP_TO_EDGE)
            
            self._depthShader = ShadowShader(name="PointDepth",
                                             vertex_import_file=SHADER_DIR / "PointDepth.vert",
                                             fragment_import_file=SHADER_DIR / "PointDepth.frag",
                                             # ShadowShader has no geometry_import_file, so read it here.
                                             geometry_source=(SHADER_DIR / "PointDepth.geom").read_text())
        else:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self._depthMapTexture)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_DEPTH_COMPONENT, 
                            self._shadowMapSize, self._shadowMapSize, 0, gl.GL_DEPTH_COMPONENT, gl.GL_FLOAT, None)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_BORDER)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_BORDER)
            gl.glTexParameterfv(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_BORDER_COLOR, [1.0, 1.0, 1.0, 1.0])

            self._depthShader = ShadowShader(name="DirDepth",
                                             vertex_import_file=SHADER_DIR / "DirDepth.vert",
                                             fragment_import_file=SHADER_DIR / "DirDepth.frag")
            
        # Attach Texture to FBO
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._depthMapFBO)
        if self._lightType == "point":
             gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, self._depthMapTexture, 0)
        else:
             gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, gl.GL_TEXTURE_2D, self._depthMapTexture, 0)
        
        # Tell OpenGL we do NOT want to render color data, only Depth.
        gl.glDrawBuffer(gl.GL_NONE)
        gl.glReadBuffer(gl.GL_NONE)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        self._depthShader.init()
        self._depthShaderID = self._depthShader.glid
        
        self._init_debug()

    def _init_debug(self):
        """
        Sets up the quad used for the debug view.
        """
        frag_file = "ShadowDebugPoint.frag" if self._lightType == "point" else "ShadowDebugDir.frag"

        self._debugShader = ShadowShader(name="DebugShadow",
                                         vertex_import_file=SHADER_DIR / "ShadowDebug.vert",
                                         fragment_import_file=SHADER_DIR / frag_file)
        self._debugShader.init()
        # simple 2D Quad covering the screen (Normalized Device Coords: -1 to 1)
        quadVertices = np.array([
            -1.0,  1.0,  0.0, 1.0,
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,
            -1.0,  1.0,  0.0, 1.0,
             1.0, -1.0,  1.0, 0.0,
             1.0,  1.0,  1.0, 1.0
        ], dtype=np.float32)
        
        self._quadVAO = gl.glGenVertexArrays(1)
        VBO = gl.glGenBuffers(1)
        gl.glBindVertexArray(self._quadVAO)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, quadVertices.nbytes, quadVertices, gl.GL_STATIC_DRAW)
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))
        gl.glBindVertexArray(0)

    def render_debug_view(self):
        """
        Renders the Depth Map to the Full Screen.
        """
        if self._debugShader is None or self._quadVAO is None: return

        # Force Full Screen Viewport
        gl.glViewport(0, 0, self._window_width, self._window_height)
        
        # Disable Depth Test (Draw on top of everything)
        gl.glDisable(gl.GL_DEPTH_TEST)
        
        # Enable Shader
        self._debugShader.enableShader()
        
        # bind Texture 
        if self._lightType == "point":
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_CUBE_MAP, self._depthMapTexture)
            # The Debug Point shader uses 'samplerCube depthMap'
            gl.glUniform1i(gl.glGetUniformLocation(self._debugShader.glid, "depthMap"), 0)
        else:
            gl.glActiveTexture(gl.GL_TEXTURE0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self._depthMapTexture)
            gl.glUniform1i(gl.glGetUniformLocation(self._debugShader.glid, "depthMap"), 0)
        
        # draw
        gl.glBindVertexArray(self._quadVAO)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)
        gl.glBindVertexArray(0)
        
        self._debugShader.disableShader()
        gl.glEnable(gl.GL_DEPTH_TEST)

    def set_viewport_dimensions(self, width, height):
        self._window_width = width
        self._window_height = height
    
    def get_light_transform(self):
        """
        Extracts the current dynamic position of the light from the Scene Graph.
        """
        pos = np.array([0.0, 5.0, 0.0])
        target = np.array([0.0, 0.0, 0.0])
        if self._lightNode and isinstance(self._lightNode, Entity):
            trans = self._lightNode.getChildByType(BasicTransform.getClassName())
            if trans: pos = trans.l2world[:3, 3]
        if self._lightTargetNode and isinstance(self._lightTargetNode, Entity):
            trans = self._lightTargetNode.getChildByType(BasicTransform.getClassName())
            if trans: target = trans.l2world[:3, 3]
        self._currentLightPos = pos
        return pos, target

    def render(self, scene_root):
        """
        Executes the Two-Pass Rendering Algorithm.
        """
        lightPos, lightTarget = self.get_light_transform()

        # The light needs its own View and Projection matrices.
        if self._lightType == "point":
            aspect = float(self._shadowMapSize) / float(self._shadowMapSize)
            shadowProj = perspective(90.0, aspect, 1.0, self._far_plane)

            # For Point Lights, we generate 6 LookAt matrices (one per direction)
            self._shadowTransforms = []
            self._shadowTransforms.append(shadowProj @ lookat(lightPos, lightPos + np.array([1, 0, 0]), np.array([0, -1, 0])))
            self._shadowTransforms.append(shadowProj @ lookat(lightPos, lightPos + np.array([-1, 0, 0]), np.array([0, -1, 0])))
            self._shadowTransforms.append(shadowProj @ lookat(lightPos, lightPos + np.array([0, 1, 0]), np.array([0, 0, 1])))
            self._shadowTransforms.append(shadowProj @ lookat(lightPos, lightPos + np.array([0, -1, 0]), np.array([0, 0, -1])))
            self._shadowTransforms.append(shadowProj @ lookat(lightPos, lightPos + np.array([0, 0, 1]), np.array([0, -1, 0])))
            self._shadowTransforms.append(shadowProj @ lookat(lightPos, lightPos + np.array([0, 0, -1]), np.array([0, -1, 0])))
        else:
            # Directional lights use Orthographic projection (parallel rays)
            lightProjection = ortho(-10.0, 10.0, -10.0, 10.0, 1.0, 100.0)
            lightView = lookat(lightPos, lightTarget, np.array([0.0, 1.0, 0.0]))
            self._lightSpaceMatrix = lightProjection @ lightView

        # !OUR FIRST PASS! SHADOW MAP GENERATION 
        self._pass_mode = 1

        # Switch Viewport to match Shadow Map resolution
        gl.glViewport(0, 0, self._shadowMapSize, self._shadowMapSize)
        # Bind our custom Framebuffer (render to texture, not screen)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._depthMapFBO)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT)


        # gl.glEnable(gl.GL_CULL_FACE)
        # gl.glCullFace(gl.GL_BACK)

        # Render Scene
        if self._depthShader.glid is not None:
            self._depthShader.enableShader()
            if self._lightType == "point":
                # Upload all 6 matrices to the Geometry Shader
                for i in range(6):
                    loc = gl.glGetUniformLocation(self._depthShaderID, f"shadowMatrices[{i}]")
                    gl.glUniformMatrix4fv(loc, 1, True, self._shadowTransforms[i])
                gl.glUniform1f(gl.glGetUniformLocation(self._depthShaderID, "far_plane"), self._far_plane)
                gl.glUniform3fv(gl.glGetUniformLocation(self._depthShaderID, "lightPos"), 1, self._currentLightPos)
            else:
                gl.glUniformMatrix4fv(gl.glGetUniformLocation(self._depthShaderID, "lightSpaceMatrix"), 1, True, self._lightSpaceMatrix)
            
            # Recursively draw all objects
            self._local_traverse(scene_root)
            self._depthShader.disableShader()

        # gl.glCullFace(gl.GL_BACK) 
        # gl.glDisable(gl.GL_CULL_FACE)
        
        # Unbind FBO (Go back to default screen buffer)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

        # !OUR SECOND PASS! RENDER SCENE WITH SHADOWS
        self._pass_mode = 2

        # Reset Viewport to Window Size
        gl.glViewport(0, 0, self._window_width, self._window_height)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # Render Scene (This triggers apply2VertexArray with Mode 2 logic)
        self._local_traverse(scene_root)
        self._pass_mode = 0

    def _local_traverse(self, node):
        """ Recursive scene graph traversal """
        if node is None: return
        if isinstance(node, (Entity, Component)):
            node.accept(self)
        if hasattr(node, "_children") and node._children is not None:
            for child in node._children:
                self._local_traverse(child)

    def apply2VertexArray(self, vertexArray: VertexArray):
        """
        This function is called for every object in the scene.
        It decides HOW to draw the object based on the current Pass Mode.
        """
        parent = vertexArray.parent
        if not parent or not isinstance(parent, Entity): return
        trans = parent.getChildByType(BasicTransform.getClassName())
        if not trans: return
        if self._depthShaderID is None: return

        # PASS 1 LOGIC (Draw Depth)
        if self._pass_mode == 1:
            # use the simple Depth Shader. No colors, no textures.
            # Just geometry position.
            gl.glUniformMatrix4fv(gl.glGetUniformLocation(self._depthShaderID, "model"), 1, True, trans.l2world)
            vertexArray.draw()
            
        # PASS 2 LOGIC (Draw Lighting + Shadows)
        elif self._pass_mode == 2:
            # We look for the 'ShadowShader' component on the object
            compShader = parent.getChildByType(ShadowShader.getClassName())
            if compShader:
                compShader.enableShader()
                pid = compShader.glid
                if pid:
                    # Upload Standard Matrix
                    gl.glUniformMatrix4fv(gl.glGetUniformLocation(pid, "model"), 1, True, trans.l2world)
                    gl.glUniform3fv(gl.glGetUniformLocation(pid, "lightPos"), 1, self._currentLightPos)
                    
                    # Bind the Shadow Map we generated in Pass 1
                    if self._lightType == "point":
                        gl.glActiveTexture(gl.GL_TEXTURE1) # Slot 1
                        gl.glBindTexture(gl.GL_TEXTURE_CUBE_MAP, self._depthMapTexture)
                        gl.glUniform1i(gl.glGetUniformLocation(pid, "shadowMap"), 1)
                        gl.glUniform1f(gl.glGetUniformLocation(pid, "far_plane"), self._far_plane)
                    else:
                        gl.glUniformMatrix4fv(gl.glGetUniformLocation(pid, "lightSpaceMatrix"), 1, True, self._lightSpaceMatrix)
                        gl.glActiveTexture(gl.GL_TEXTURE1)
                        gl.glBindTexture(gl.GL_TEXTURE_2D, self._depthMapTexture)
                        gl.glUniform1i(gl.glGetUniformLocation(pid, "shadowMap"), 1)
                    
                    vertexArray.draw()
                    compShader.disableShader()
    
    def apply2RenderMesh(self, renderMesh): pass
    def apply2Shader(self, shader): pass
    def apply2ShaderGLDecorator(self, shaderGLDecorator): pass