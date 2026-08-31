"""
Environment Mapping Extension
Applies mirror-like reflection effects to entities.
"""

import numpy as np
from PIL import Image

import Elements.pyECSS.math_utilities as util
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from Elements.pyGLV.GL.Textures import Texture3D, texture_data
from Elements.definitions import SHADER_DIR


ENV_MAP_VERT = (SHADER_DIR / "EnvironmentMapping.vert").read_text()

ENV_MAP_FRAG = (SHADER_DIR / "EnvironmentMapping.frag").read_text()
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