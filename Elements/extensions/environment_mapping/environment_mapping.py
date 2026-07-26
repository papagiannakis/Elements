"""
Environment Mapping Extension
Applies mirror-like reflection effects to entities.
"""

import numpy as np
from PIL import Image

import Elements.pyECSS.math_utilities as util
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from Elements.pyGLV.GL.Textures import Texture3D, texture_data


ENV_MAP_VERT = """
#version 410
layout (location=0) in vec4 vPosition;
layout (location=1) in vec4 vColor;
layout (location=2) in vec4 vNormal;

out vec4 pos;
out vec3 normal;

uniform mat4 modelViewProj;
uniform mat4 model;

void main() {
    gl_Position = modelViewProj * vPosition;
    pos = model * vPosition;
    // Calculate normal in world space
    normal = mat3(transpose(inverse(model))) * vNormal.xyz;
}
"""

ENV_MAP_FRAG = """
#version 410
in vec4 pos;
in vec3 normal;
out vec4 outputColor;

uniform samplerCube environmentMap;
uniform vec3 tintColor;
uniform float tintStrength;
uniform vec3 viewPos;

void main() {
    vec3 N = normalize(normal);
    vec3 I = normalize(pos.xyz - viewPos); // Incident vector
    vec3 R = reflect(I, N);                // Reflection vector

    vec3 envColor = texture(environmentMap, R).rgb;
    vec3 finalColor = mix(envColor, envColor * tintColor, tintStrength);
    
    outputColor = vec4(finalColor, 1.0);
}
"""
#helpers to create cubemaps
def create_solid_cubemap(color=(0.5, 0.7, 1.0, 1.0), size=1024):
    """Creates a single-color cubemap for testing/fallback."""
    # make 0-1 float color to 0-255 int
    color_int = tuple(int(c * 255) for c in color)
    
    # Generate one 
    img = Image.new('RGBA', (size, size), color_int)
    img_bytes = img.tobytes("raw", "RGBA", 0, -1)
    
    # then replicate for all 6 faces
    faces = [texture_data(size, size, img_bytes) for _ in range(6)]
    return Texture3D(faces)

def create_cubemap_files(filepaths):
    """
    Creates a Texture3D from a list of 6 file paths.
    Order: [Right, Left, Top, Bottom, Front, Back]
    """
    faces = []
    for path in filepaths:
        img = Image.open(path).convert("RGBA")
        faces.append(texture_data(img.height, img.width, img.tobytes("raw", "RGBA", 0, -1)))
    return Texture3D(faces)


class EnvironmentMapping:
    """Helper to apply reflection shaders to entities."""

    @staticmethod
    def apply(entity, scene, cubemap=None, tint_color=(1.0, 1.0, 1.0), tint_strength=0.0):
        """
        Attaches the reflection shader and cubemap to an entity.
        Returns the shader decorator for future updates (like viewPos).
        """
        # Remove old shader if it exists so we don't stack them
        old_shader = entity.getChildByType(ShaderGLDecorator.getClassName())
        if old_shader:
            scene.world.removeComponent(entity, old_shader)

        # my new shader
        shader = Shader(vertex_source=ENV_MAP_VERT, fragment_source=ENV_MAP_FRAG)
        shader_dec = scene.world.addComponent(entity, ShaderGLDecorator(shader))
        
        # Defaults
        if cubemap is None:
            cubemap = create_solid_cubemap()
            
        # uniforms
        shader_dec.component.texture3DDict['environmentMap'] = cubemap
        shader_dec.setUniformVariable(key='tintColor', value=np.array(tint_color), float3=True)
        shader_dec.setUniformVariable(key='tintStrength', value=tint_strength, float1=True)
        shader_dec.setUniformVariable(key='viewPos', value=np.array([0.0, 0.0, 0.0]), float3=True)
        
        return shader_dec