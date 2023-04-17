from Elements.pyECSS.System import System
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
import numpy as np

from Elements.pyGLV.GL.Textures import Texture

class Material:
    def __init__(self, name=None):
        self.name = name

    def init(self):
        pass

    def accept(self, system: System):
        system.apply2Material(self)

    def update_shader_properties(self, shader_decorator_component: ShaderGLDecorator):
        pass


# Foreach type of Material also implement its decorator
class StandardMaterial(Material):

    __WHITE = (b'\xff\xff\xff\xff',1,1)
    __BLACK = (b'\x00\x00\x00\x00',1,1)

    # Light Data


    # Texture Data
    __albedo_color: np.array
    __albedo_map : bytes
    __normal_map : bytes
    __normal_map_intensity: float
    __metallic_map : bytes
    __roughness_map : bytes
    __ambient_occlusion_map : bytes

    albedo_map = property(
        fget= lambda self: self.__albedo_map
    )

    def __init__(self, name=None, id=None, light_position=np.array([0.0,0.0,0.0]), light_color=np.array([1.0,1.0,1.0]), light_intensity=1.0 , albedo_color=None, albedo_map=None, normal_map = None, normal_map_intensity = None, metallic_map =None, roughness_map = None, ambient_occlusion_map= None):
        super().__init__(name)

        # Init texture bytes with default color
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
        shader_decorator_component.setUniformVariable(key='albedoColor', value=np.array([1.0, 1.0, 1.0]), float3=True)
        # texturePath = os.path.join(os.path.dirname(__file__), "models/bowel/albedo.png")
        texture = Texture(img_data=self.__WHITE, texture_channel=0)
        shader_decorator_component.setUniformVariable(key='albedoMap', value=texture, texture=True)
        # Normal map
        shader_decorator_component.setUniformVariable(key='normalMapIntensity', value=1.0, float1=True)
        # texturePath = os.path.join(os.path.dirname(__file__), "models/bowel/normal.png")
        texture = Texture(img_data=self.__BLACK, texture_channel= 1)
        shader_decorator_component.setUniformVariable(key='normalMap', value=texture, texture=True)
        # Metallic map
        # texturePath = os.path.join(os.path.dirname(__file__), "models/bowel/metallic.png")
        texture = Texture(img_data=self.__WHITE, texture_channel=2)
        shader_decorator_component.setUniformVariable(key='metallicMap', value=texture, texture=True)
        # Roughness
        # texturePath = os.path.join(os.path.dirname(__file__), "textures/black1x1.png")
        texture = Texture(img_data=self.__WHITE, texture_channel=3)
        shader_decorator_component.setUniformVariable(key='roughnessMap', value=texture, texture=True)
        # Ambient Occlusion
        # texturePath = os.path.join(os.path.dirname(__file__), "textures/black1x1.png")
        texture = Texture(img_data=self.__WHITE, texture_channel=4)
        shader_decorator_component.setUniformVariable(key='aoMap', value=texture, texture=True)
