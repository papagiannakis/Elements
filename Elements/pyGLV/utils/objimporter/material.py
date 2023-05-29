import os
from Elements.pyECSS.System import System
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
import numpy as np

from typing import Tuple


from Elements.pyGLV.GL.Textures import Texture

base_dir = os.path.dirname(__file__)

class Material:
    def __init__(self, name=None):
        self.name = name

    def init(self):
        pass

    def update_shader_properties(self, shader_decorator_component: ShaderGLDecorator):
        pass


# Foreach type of Material also implement its decorator
class StandardMaterial(Material):

    __WHITE = (b'\xff\xff\xff\xff',1,1)
    __BLACK = (b'\x00\x00\x00\xff',1,1)
    __NORMAL = (b'\x7f\x7f\xff\xff',1,1)

    # Texture Data
    # All texture maps are stored in a tuple with in this format (bytes of the image:bytes, width:int, height:int)
    albedo_color: np.array
    albedo_map : Tuple[bytes, int, int]
    normal_map : Tuple[bytes, int, int]
    normal_map_intensity: float
    metallic_map : Tuple[bytes, int, int]
    roughness_map : Tuple[bytes, int, int]
    ambient_occlusion_map : Tuple[bytes, int, int]


    def __init__(   self, 
                    name:str=None,
                    albedo_color=np.array([1.0, 1.0, 1.0]), 
                    albedo_map:Tuple[bytes, int, int] = None, # The albedo map to be used in a tuple along with the width and height
                    normal_map:Tuple[bytes, int, int] = None, 
                    normal_map_intensity = 1.0, 
                    metallic_map:Tuple[bytes, int, int] = None, 
                    roughness_map:Tuple[bytes, int, int] = None, 
                    ambient_occlusion_map:Tuple[bytes, int, int] = None):
        super().__init__(name)

        # Init material properties
        self.albedo_color = albedo_color
        self.normal_map_intensity = normal_map_intensity

        # Init texture bytes with default color, if not provided
        self.albedo_map = albedo_map if albedo_map is not None else self.__WHITE
        self.normal_map = normal_map if normal_map is not None else self.__NORMAL
        self.metallic_map = metallic_map if metallic_map is not None else self.__BLACK
        self.roughness_map = roughness_map if roughness_map is not None else self.__BLACK
        self.ambient_occlusion_map = ambient_occlusion_map if ambient_occlusion_map is not None else self.__WHITE

    
    def update_shader_properties(self, shader_decorator_component: ShaderGLDecorator):
        """
        Updates the shader decorator with the properties of this material
        
        Params
        ------
        shader_decorator: ShaderGLDecorator
            The shader decorator with the correct Shader, in which to update the material properties
        """
        
        # Material
        # Albedo
        shader_decorator_component.setUniformVariable(key='albedoColor', value=self.albedo_color, float3=True)
        texture = Texture(img_data=self.albedo_map, texture_channel=0)
        shader_decorator_component.setUniformVariable(key='albedoMap', value=texture, texture=True)
        # Normal map
        shader_decorator_component.setUniformVariable(key='normalMapIntensity', value=1.0, float1=True)
        texture = Texture(img_data=self.normal_map, texture_channel= 1)
        shader_decorator_component.setUniformVariable(key='normalMap', value=texture, texture=True)
        # Metallic map
        texture = Texture(img_data=self.metallic_map, texture_channel=2)
        shader_decorator_component.setUniformVariable(key='metallicMap', value=texture, texture=True)
        # Roughness
        texture = Texture(img_data=self.roughness_map, texture_channel=3)
        shader_decorator_component.setUniformVariable(key='roughnessMap', value=texture, texture=True)
        # Ambient Occlusion
        texture = Texture(img_data=self.ambient_occlusion_map, texture_channel=4)
        shader_decorator_component.setUniformVariable(key='aoMap', value=texture, texture=True)