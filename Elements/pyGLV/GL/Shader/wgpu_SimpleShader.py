import wgpu
import numpy as np
from Elements.pyGLV.GL.wgpu_shader import Shader
from Elements.pyGLV.GL.wgpu_shader import ShaderLoader 
from Elements.pyGLV.GL.wgpu_shader import Attribute
from Elements.pyGLV.GL.wgpu_shader import SHADER_TYPE_BUFFER_STRIDE 
from Elements.pyGLV.GL.wgpu_shader import SHADER_TYPES 
from Elements.pyGLV.GL.wgpu_shader import F32, I32 
from Elements.pyGLV.GL.wgpu_texture import Texture, ImprotTexture
from Elements.definitions import SHADER_DIR

class SimpleShader(Shader):
    def __init__(self, device:wgpu.GPUDevice):  
        super().__init__()

        self.device:wgpu.GPUDevice = device
        self.code = ShaderLoader(SHADER_DIR / "WGPU" / "base_shader.wgsl") 
        self.context = device.create_shader_module(code=self.code)

    def init(self):  
        self.tempStorageModels = None
        self.tempProj = None 
        self.tempView = None

        self.addAtribute(name="vertex", rowLenght=SHADER_TYPES['vec3f'], primitiveType=F32)
        self.addAtribute(name="uv", rowLenght=SHADER_TYPES['vec2f'], primitiveType=F32) 

        self.addUniform(
            name="proj",  
            size=SHADER_TYPES['mat4x4'] * F32, 
            offset=0,
        ) 
        self.addUniform(
            name="view",  
            size=SHADER_TYPES['mat4x4'] * F32, 
            offset=1
        )  
        self.addStorage(
            name="models",
            size=(SHADER_TYPES['mat4x4'] * F32) * 1024
        ) 

        self.addTexture(
            name="image",
        ) 
        self.addSampler(
            name="sampler",
            sampler=self.device.create_sampler()
        ) 

        self.attachedMaterial.uniformGroups["frameGroup"].makeUniformBuffer(device=self.device)
        self.attachedMaterial.uniformGroups["frameGroup"].makeStorageBuffers(device=self.device)

        self.attachedMaterial.uniformGroups["frameGroup"].makeBindGroupLayout(device=self.device) 
        # self.attachedMaterial.uniformGroups["frameGroup"].makeBindGroup(device=self.device)
        self.attachedMaterial.uniformGroups["materialGroup"].makeBindGroupLayout(device=self.device) 
        # self.attachedMaterial.uniformGroups["materialGroup"].makeBindGroup(device=self.device)

    def setProj(self, data:np.ndarray): 
        self.tempProj = data

    def setView(self, data:np.ndarray): 
        self.tempView = data

    def setModel(self, data:np.ndarray):
        self.tempStorageModels = data 

    def setTexture(self, value:Texture):
        self.attachedMaterial.uniformGroups["materialGroup"].setTexture(name="image", value=value) 

    def update(self, command_encoder:wgpu.GPUCommandEncoder): 

        self.attachedMaterial.uniformGroups["frameGroup"].setUniform(name="proj", value=self.tempProj) 
        self.attachedMaterial.uniformGroups["frameGroup"].setUniform(name="view", value=self.tempView) 
        self.attachedMaterial.uniformGroups["frameGroup"].setStorage(name="models", value=self.tempStorageModels) 

        self.attachedMaterial.uniformGroups["frameGroup"].update(self.device, command_encoder)

        # self.tempStorageModels = None 
        # self.tempView = None 
        # self.tempProj = None