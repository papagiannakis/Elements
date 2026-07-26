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

# unlike a standard Shader, this class holds specific 
# logic for depth shaders (Pass 1) and shadow receivers (Pass 2).
class ShadowShader(Component):
    """
    An OpenGL-GLSL Shader container Component class specifically for Shadows.
    """
    
    # PASS 1, SHADOW MAP GENERATION SHADERS

    # Vertex Shader for Directional Lights (Orthographic Projection)
    # In a standard render, we output Color and Normal.
    # Here, we ONLY care about position. We just need to know "how far is this pixel?"
    VERT_DIR_DEPTH = """
        #version 410
        layout (location = 0) in vec4 vPosition;
    
        // we use 'lightSpaceMatrix' instead of the Camera's 'projection * view'.
        // This transforms the vertex as seen from the LIGHT'S point of view.
        uniform mat4 lightSpaceMatrix; 
        uniform mat4 model; 
        
        void main() {
            // transform vertex to world space (model) then to light space.
            gl_Position = lightSpaceMatrix * model * vPosition;
        }
    """

    # Fragment Shader for Directional Lights
    # We do not output color here. OpenGL automatically writes the Z-value 
    # to the Depth Buffer, which is all we need for the Shadow Map.
    FRAG_DIR_DEPTH = """
        #version 410
        void main() { 
        //
        }
    """
    
    # Vertex Shader for Point Lights (Perspective Projection)
    VERT_POINT_DEPTH = """
        #version 410 
        layout (location = 0) in vec4 vPosition;
        uniform mat4 model;
        void main() {
            gl_Position = model * vPosition;
        }
    """


    # ==========================================================================
    # GEOMETRY SHADER FOR POINT LIGHTS
    # A Point Light emits light in all directions (360 degrees). To calculate 
    # shadows, we cannot just take one "photo" (Depth Map). We need 6 photos 
    # to form a cube surrounding the light (Top, Bottom, Left, Right, Front, Back).
    #
    # Without a Geometry Shader:
    # We would have to tell the CPU to render the entire scene 6 separate times, 
    # changing the camera angle each time. This is very slow.
    #
    # With a Geometry Shader:
    # We send the scene to the GPU only ONCE. This shader acts like a photocopier.
    # It takes 1 triangle as input, runs a loop 6 times, rotates the triangle 
    # to look at a specific face, and sends it to a specific "Layer" of the 
    # Cube Map texture. This is called "Layered Rendering".
    # ==========================================================================

    
    # Geometry Shader for Point Lights
    # It takes 1 triangle and renders it 6 times,
    # once for each face of the Cube Map (Up, Down, Left, Right, Front, Back)
    GEOM_POINT_DEPTH = """
        #version 410
        layout (triangles) in;
        layout (triangle_strip, max_vertices=18) out;

        uniform mat4 shadowMatrices[6]; // The 6 View Matrices of the Light

        out vec4 FragPos; // Passed to Fragment shader to calc distance

        void main() {
            for(int face = 0; face < 6; ++face) {
                gl_Layer = face; // built in variable, selects which Cubemap face to draw to
                for(int i = 0; i < 3; ++i) {
                    FragPos = gl_in[i].gl_Position;
                    gl_Position = shadowMatrices[face] * FragPos;
                    EmitVertex();
                }
                EndPrimitive();
            }
        }
    """

    # Fragment Shader for Point Lights
    # Unlike Directional lights, we manually calculate linear distance here.
    FRAG_POINT_DEPTH = """
        #version 410
        in vec4 FragPos;

        uniform vec3 lightPos;
        uniform float far_plane;

        void main() {
            float lightDistance = length(FragPos.xyz - lightPos);
            // map to [0,1] range by dividing by far_plane
            lightDistance = lightDistance / far_plane;
            gl_FragDepth = lightDistance;
        }
    """    
    
    
    ################################################################
    # PASS 2, SCENE RENDERING SHADERS - PHONG + SHADOWS

    # VERTEX SHADER FOR SCENE RENDERING (PASS 2)
    # a standard shader, but calculates 'FragPosLightSpace'.
    VERT_DIR_PHONG = """
        #version 410
        layout (location = 0) in vec4 vPosition;
        layout (location = 1) in vec4 vColor;
        layout (location = 2) in vec4 vNormal;
        layout (location = 3) in vec2 vTexCoord; 

        out vec4 FragPos;
        out vec3 Normal;
        out vec2 TexCoords;
        
        // This tells the Fragment Shader where this pixel 
        // lands on the Shadow Map texture we created in Pass 1.
        out vec4 FragPosLightSpace; 
        out vec4 Color;

        uniform mat4 projection;
        uniform mat4 view;
        uniform mat4 model;
        uniform mat4 lightSpaceMatrix; // passed again to calculate shadow coordinates

        void main() {
            FragPos = model * vPosition; // world position
            Normal = transpose(inverse(mat3(model))) * vNormal.xyz; // normal scaling
            TexCoords = vTexCoord;
            Color = vColor;
            
            // where this vertex is inside the Light's View
            FragPosLightSpace = lightSpaceMatrix * FragPos;
            
            // camera position
            gl_Position = projection * view * FragPos;
        }
    """
    
    # fragment shader for Directional Lights with Phong shading and Shadows
    FRAG_DIR_PHONG = """
        #version 410 core
        out vec4 FragColor;
        in vec4 FragPos;
        in vec3 Normal;
        in vec2 TexCoords;
        in vec4 FragPosLightSpace;
        in vec4 Color;

        // Textures
        uniform sampler2D ImageTexture;
        uniform bool useTexture;

        // Shadow Resources
        uniform sampler2D shadowMap;

        // Light & View
        uniform vec3 lightPos;
        uniform vec3 viewPos;
        uniform vec3 lightColor;
        
        // Settings
        uniform int uHasShadow;     // 1 = Shadows Enabled
        uniform int uSoftShadows;   // 1 = PCF Enabled
        uniform float uPcfDisk;     // Radius of soft shadow sample
        uniform int uDebugMode;     // 0=Normal, 1=DepthMap, 2=Comparison
        uniform float uShadowBias;  // Threshold to prevent Shadow Acne

        // Visualization Colors
        uniform vec3 uLitColorViz;    // Color for lit areas in Debug Mode 2
        uniform vec3 uShadowColorViz; // Color for shadow areas in Debug Mode 2

        void main() {
            // Normalize Input Vectors (Interpolation de-normalizes them)   
            vec3 norm = normalize(Normal);
            vec3 lightDir = normalize(lightPos - FragPos.xyz);
            vec3 viewDir = normalize(viewPos - FragPos.xyz);
            vec3 reflectDir = reflect(-lightDir, norm);
            
            // Determine Material Color (Texture or Vertex Color)
            vec3 matColor = useTexture ? texture(ImageTexture, TexCoords).xyz : Color.rgb;

            // --- SHADOW CALCULATION --
            float shadow = 0.0;

            // How far is THIS pixel from the light?
            float currentDepth = 0.0;

            float closestDepth = 0.0;
            
            // Perspective Divide (convert to NDC -1..1)
            vec3 projCoords = FragPosLightSpace.xyz / FragPosLightSpace.w;
            // Transform to Texture Coordinates (0..1)
            projCoords = projCoords * 0.5 + 0.5;
            
            // Only calc shadow if the pixel is within the light's view frustum
            if (uHasShadow == 1 && projCoords.z <= 1.0) {
                currentDepth = projCoords.z;
                
                float bias = uShadowBias;

                if (uSoftShadows == 1) {
                    // Percentage Closer Filtering (PCF)
                    // We sample neighbors to smooth jagged edges.
                    vec2 texelSize = 1.0 / textureSize(shadowMap, 0);
                    float radius = max(uPcfDisk, 1.0); 
                    for(int x = -1; x <= 1; ++x) {
                        for(int y = -1; y <= 1; ++y) {
                            float pcfDepth = texture(shadowMap, projCoords.xy + vec2(x, y) * texelSize * radius).r; 
                            
                            // If currentDepth > pcfDepth, we are behind something (Shadow)
                            shadow += currentDepth - bias > pcfDepth ? 1.0 : 0.0;        
                        
                        
                        }    
                    }
                    shadow /= 9.0; // Average the 9 samples
                } else {
                    closestDepth = texture(shadowMap, projCoords.xy).r;
                    shadow = currentDepth - bias > closestDepth ? 1.0 : 0.0;
                }
            }

            // --- VISUALIZATION ---

            // Fetch raw depth (unbiased)
            closestDepth = texture(shadowMap, projCoords.xy).r;

            // Light Depth View
            if (uDebugMode == 1) {
                if(projCoords.x < 0.0 || projCoords.x > 1.0 || projCoords.y < 0.0 || projCoords.y > 1.0) FragColor = vec4(0,0,0,1);
                else FragColor = vec4(vec3(closestDepth), 1.0); 
                return;
            }
            
            // Shadow Comparison (Red/Green)
            if (uDebugMode == 2) {
                if (shadow > 0.0) FragColor = vec4(uShadowColorViz, 1.0); // Shadow
                else FragColor = vec4(uLitColorViz, 1.0); // Lit
                return;
            }

            // --- PHONG MODEL  ---
            
            // Ambient
            vec3 ambientProduct = 0.2 * matColor;

            // Diffuse
            float diffuseStr = max(dot(norm, lightDir), 0.0);
            vec3 diffuseProduct = diffuseStr * lightColor;

            vec3 halfwayDir = normalize(lightDir + viewDir);  
            float specularStr = pow(max(dot(norm, halfwayDir), 0.0), 64.0);
            vec3 specularProduct = 0.5 * specularStr * matColor;


            // Final Composition
            // Ambient is always present. Diffuse & Specular are blocked by shadow.
            vec3 lightingParts = (diffuseProduct + specularProduct) * (1.0 - shadow);
            vec3 result = (ambientProduct + lightingParts) * matColor;
            
            FragColor = vec4(result, 1.0);
        }
    """
    
    VERT_POINT_PHONG = """
        #version 410 
        layout (location = 0) in vec4 vPosition;
        layout (location = 1) in vec4 vColor;
        layout (location = 2) in vec4 vNormal;
        layout (location = 3) in vec2 vTexCoord; 

        out vec4 FragPos;
        out vec3 Normal;
        out vec2 TexCoords;
        out vec4 Color;

        uniform mat4 projection;
        uniform mat4 view;
        uniform mat4 model;

        void main() {
            FragPos = model * vPosition;
            Normal = transpose(inverse(mat3(model))) * vNormal.xyz;
            TexCoords = vTexCoord;
            Color = vColor;
            gl_Position = projection * view * FragPos;
        }
    """


    # FRAGMENT SHADER FOR POINT LIGHTS
    FRAG_POINT_PHONG = """
        #version 410 
        out vec4 FragColor;
        in vec4 FragPos;
        in vec3 Normal;
        in vec2 TexCoords;
        in vec4 Color;

        uniform sampler2D ImageTexture;
        uniform bool useTexture;

        // Point lights use a Cube Map (3D Texture)
        uniform samplerCube shadowMap;

        uniform vec3 lightPos;
        uniform vec3 viewPos;
        uniform vec3 lightColor;
        uniform float far_plane;
        
        uniform int uHasShadow;
        uniform int uSoftShadows;
        uniform float uPcfDisk;
        uniform int uDebugMode;
        uniform float uShadowBias;

        uniform vec3 uLitColorViz;
        uniform vec3 uShadowColorViz;

        // --- PCF OFFSET ARRAY ---
        // These are 20 pre-defined directions relative to the center.
        // We use them to peek at neighboring pixels in the shadow map to average the result.
        vec3 gridSamplingDisk[20] = vec3[](
           vec3(1, 1, 1), vec3( 1, -1, 1), vec3(-1, -1, 1), vec3(-1, 1, 1),
           vec3(1, 1, -1), vec3( 1, -1, -1), vec3(-1, -1, -1), vec3(-1, 1, -1),
           vec3(1, 1, 0), vec3( 1, -1, 0), vec3(-1, -1, 0), vec3(-1, 1, 0),
           vec3(1, 0, 1), vec3(-1, 0, 1), vec3( 1, 0, -1), vec3(-1, 0, -1),
           vec3(0, 1, 1), vec3( 0, -1, 1), vec3( 0, -1, -1), vec3( 0, 1, -1));


        void main() {           
            vec3 norm = normalize(Normal);
            vec3 lightDir = normalize(lightPos - FragPos.xyz);
            vec3 viewDir = normalize(viewPos - FragPos.xyz);
            vec3 reflectDir = reflect(-lightDir, norm);
            
            vec3 matColor = useTexture ? texture(ImageTexture, TexCoords).rgb : Color.rgb;

            // Shadow Calculation
            vec3 fragToLight = FragPos.xyz - lightPos;

            // How far is THIS pixel from the light?
            float currentDepth = length(fragToLight);

            float bias = uShadowBias; 
            float shadow = 0.0;
            float closestDepthRaw = 0.0;

            if (uHasShadow == 1) {
                if (uSoftShadows == 1) {
                // Soft Shadows: Average 20 samples from the cube map
                // Instead of testing just 1 point, we test 20 points around the vector.
                // This blurs the edge of the shadow.

                    int samples = 20;

                    // The further away the pixel is, the larger the sampling radius should be.
                    
                    float diskRadius = (1.0 + (currentDepth / far_plane)) / 25.0; 
                    diskRadius *= max(uPcfDisk, 0.1);
                    for(int i = 0; i < samples; ++i) {
                        // Sample the cube map with an offset
                        float val = texture(shadowMap, fragToLight + gridSamplingDisk[i] * diskRadius).r;
                        val *= far_plane; // Remap [0,1] to [0, far_plane]

                        // The Comparison: Is my depth > stored depth?
                        if(currentDepth - bias > val) shadow += 1.0;
                    }
                    shadow /= float(samples); // Average the results (e.g., if 10/20 are blocked, shadow is 0.5
                } else {
                // Hard Shadows 
                    float val = texture(shadowMap, fragToLight).r;
                    val *= far_plane;
                    if(currentDepth - bias > val) shadow = 1.0;
                }
            }

            // Raw depth for visualizer
            closestDepthRaw = texture(shadowMap, fragToLight).r;

            if (uDebugMode == 1) {
                //float contrastDepth = pow(closestDepthRaw, 0.15);
                FragColor = vec4(vec3(closestDepthRaw), 1.0); 
                return;
            }
            if (uDebugMode == 2) {
                if (shadow > 0.0) FragColor = vec4(uShadowColorViz, 1.0);
                else FragColor = vec4(uLitColorViz, 1.0);
                return;
            }

            // PHONG MODEL
            // Ambient
            vec3 ambientProduct = 0.1 * matColor;

            // Diffuse
            float diffuseStr = max(dot(norm, lightDir), 0.0);
            vec3 diffuseProduct = diffuseStr * lightColor;

            // Specular
                
            // Blinn-Phong uses the "Halfway" vector (Light + View)
            vec3 halfwayDir = normalize(lightDir + viewDir);  
            float specularStr = pow(max(dot(norm, halfwayDir), 0.0), 64.0);
            vec3 specularProduct = 0.5 * specularStr * matColor;

            // Final Composition
            vec3 lightingParts = (diffuseProduct + specularProduct) * (1.0 - shadow);
            vec3 result = (ambientProduct + lightingParts) * matColor;

            FragColor = vec4(result, 1.0);
        }
    """
   # --- DEBUG (& VISUALIZATION) VERTEX SHADER (Shared) ---
    VERT_DEBUG = """
        #version 410 
        layout (location = 0) in vec2 vPos;
        layout (location = 1) in vec2 vTex;
        out vec2 TexCoords;
        void main() {
            gl_Position = vec4(vPos, 0.0, 1.0); 
            TexCoords = vTex;
        }
    """
    
    #--- DEBUG (& VISUALIZATION) FRAG SHADER (For Directional Lights / 2D)
    FRAG_DEBUG_DIR = """
        #version 410 
        out vec4 FragColor;
        in vec2 TexCoords;
        
        uniform sampler2D depthMap;
        
        void main() {             
            float depthValue = texture(depthMap, TexCoords).r;
            // contrast stretch, to enhance visibility
            float contrast = pow(depthValue, 4.0); 
            FragColor = vec4(vec3(contrast), 1.0);
        }
    """

    # --- DEBUG (& VISUALIZATION) FRAG SHADER (For Point Lights / CubeMaps) 
    # This unwraps the 3D Cube Map onto a 2D screen.
    # It renders the Cube Map as an unfolded "Cross" layout.
    # Grid Layout (4x3):
    #       [+Y]
    # [-X]  [+Z]  [+X]  [-Z]
    #       [-Y]
    FRAG_DEBUG_POINT = """
        #version 410
        out vec4 FragColor;
        in vec2 TexCoords;
        
        uniform samplerCube depthMap;
        
        void main() {
            vec2 uv = TexCoords;
            // Map 0..1 UVs to a 4x3 Grid
            // x: 0..4, y: 0..3
            float col = floor(uv.x * 4.0);
            float row = floor(uv.y * 3.0);
            
            // Local UV coordinates inside each grid cell (0..1)
            vec2 subUV = vec2(fract(uv.x * 4.0), fract(uv.y * 3.0));
            // Map subUV to -1..1 range for direction calculation
            vec2 boxUV = subUV * 2.0 - 1.0; 

            vec3 dir = vec3(0.0);
            bool valid = false;

            // Row 1 (Middle): The horizontal strip
            if (row == 1.0) {
                if (col == 0.0) { 
                    // Left Face (-X)
                    dir = vec3(-1.0, -boxUV.y, boxUV.x); 
                    valid = true; 
                } 
                else if (col == 1.0) { 
                    // Front Face (+Z)
                    dir = vec3(boxUV.x, -boxUV.y, 1.0); 
                    valid = true; 
                } 
                else if (col == 2.0) { 
                    // Right Face (+X)
                    dir = vec3(1.0, -boxUV.y, -boxUV.x); 
                    valid = true; 
                } 
                else if (col == 3.0) { 
                    // Back Face (-Z)
                    dir = vec3(-boxUV.x, -boxUV.y, -1.0); 
                    valid = true; 
                }
            }
            // Vertical Strip (Top/Bottom) aligned with Front Face (+Z) which is col 1
            if (col == 1.0) {
                if (row == 2.0) { 
                    // Top Face (+Y)
                    dir = vec3(boxUV.x, 1.0, boxUV.y); 
                    valid = true; 
                }
                if (row == 0.0) { 
                    // Bottom Face (-Y)
                    dir = vec3(boxUV.x, -1.0, -boxUV.y); 
                    valid = true; 
                }
            }

            if (!valid) {
                // Draw Dark Grey for empty spaces in the cross
                FragColor = vec4(0.1, 0.1, 0.1, 1.0); 
                return;
            }
            
            float depthValue = texture(depthMap, normalize(dir)).r;
            
            // contrast stretch, to enhance visibility
            float display = 1.0 - depthValue;
            display = pow(display, 15.0);

            FragColor = vec4(vec3(display), 1.0);

        }
    """

    def __init__(self, name=None, type=None, id=None, 
                 vertex_source=None, fragment_source=None, geometry_source=None):
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
        
        self._vertex_source = vertex_source
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
        if not self._vertex_source: self._vertex_source = ShadowShader.VERT_DIR_PHONG
        if not self._fragment_source: self._fragment_source = ShadowShader.FRAG_DIR_PHONG

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
            
            self._depthShader = ShadowShader(name="PointDepth", vertex_source=ShadowShader.VERT_POINT_DEPTH, fragment_source=ShadowShader.FRAG_POINT_DEPTH, geometry_source=ShadowShader.GEOM_POINT_DEPTH)
        else:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self._depthMapTexture)
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_DEPTH_COMPONENT, 
                            self._shadowMapSize, self._shadowMapSize, 0, gl.GL_DEPTH_COMPONENT, gl.GL_FLOAT, None)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_BORDER)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_BORDER)
            gl.glTexParameterfv(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_BORDER_COLOR, [1.0, 1.0, 1.0, 1.0])

            self._depthShader = ShadowShader(name="DirDepth", vertex_source=ShadowShader.VERT_DIR_DEPTH, fragment_source=ShadowShader.FRAG_DIR_DEPTH)
            
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
        frag_source = ShadowShader.FRAG_DEBUG_DIR
        if self._lightType == "point":
            frag_source = ShadowShader.FRAG_DEBUG_POINT
            
        self._debugShader = ShadowShader(name="DebugShadow", 
                                         vertex_source=ShadowShader.VERT_DEBUG, 
                                         fragment_source=frag_source)
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