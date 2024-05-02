import wgpu
import glm
import numpy as np  
from Elements.pyGLV.GL.wpgu_scene import Scene
from Elements.pyGLV.GL.wgpu_meshes import Buffers
from Elements.pyGLV.GL.wgpu_shader import Shader
from Elements.pyGLV.GL.wgpu_shader import ShaderLoader 
from Elements.pyGLV.GL.wgpu_shader import Attribute
from Elements.pyGLV.GL.wgpu_shader import SHADER_TYPE_BUFFER_STRIDE 
from Elements.pyGLV.GL.wgpu_shader import SHADER_TYPES 
from Elements.pyGLV.GL.wgpu_shader import F32, I32 
from Elements.pyGLV.GL.wgpu_texture import Texture, ImprotTexture 
from Elements.pyGLV.GL.wgpu_uniform_groups import UniformGroup  
from Elements.pyGLV.GUI.fps_cammera import cammera
from Elements.definitions import SHADER_DIR

class BlinPhongShader(Shader):
    def __init__(self, device:wgpu.GPUDevice):  
        super().__init__()

        self.device:wgpu.GPUDevice = device
        self.code = ShaderLoader(SHADER_DIR / "WGPU" / "blin_phong_shader.wgsl") 
        self.context = device.create_shader_module(code=self.code)

    def init(self):    
        self.Models = [];
        self.View = None;
        self.Proj = None; 

        self.lightColor = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32) 
        self.lightPos = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32) 
        self.camPos = None

        self.attachedMaterial.uniformGroups.update({"frameGroup": UniformGroup(groupName="frameGroup", groupIndex=0)})
        self.attachedMaterial.uniformGroups.update({"materialGroup": UniformGroup(groupName="materialGroup", groupIndex=1)})

        self.addAtribute(name=Buffers.VERTEX, rowLenght=SHADER_TYPES['vec3f'], primitiveType=F32)
        self.addAtribute(name=Buffers.UV, rowLenght=SHADER_TYPES['vec2f'], primitiveType=F32)  
        self.addAtribute(name=Buffers.NORMAL, rowLenght=SHADER_TYPES['vec3f'], primitiveType=F32)

        self.addUniform(
            name="proj", 
            groupName="frameGroup",
            size=SHADER_TYPES['mat4x4'] * F32, 
            offset=0,
        ) 
        self.addUniform(
            name="view",   
            groupName="frameGroup",
            size=SHADER_TYPES['mat4x4'] * F32, 
            offset=1
        )    
        self.addUniform( 
            name="lightColor",
            groupName="frameGroup",
            size=SHADER_TYPES['vec4f'] * F32, 
            offset=2
        )
        self.addUniform( 
            name="lightPos",
            groupName="frameGroup",
            size=SHADER_TYPES['vec4f'] * F32, 
            offset=3
        ) 
        self.addUniform( 
            name="camPos",
            groupName="frameGroup",
            size=SHADER_TYPES['vec4f'] * F32, 
            offset=4
        ) 

        self.addStorage(
            name="models", 
            groupName="frameGroup",
            size=(SHADER_TYPES['mat4x4'] * F32) * 1024
        )  

        self.addTexture(
            name="texture", 
            groupName="materialGroup"
        ) 
        self.addSampler(
            name="sampler",
            groupName="materialGroup",
            sampler=self.device.create_sampler()
        ) 

        self.makeUniformBuffer("frameGroup") 
        self.makeStorageBuffers("frameGroup") 
        self.makeBindGroupLayout("frameGroup") 
        self.makeBindGroupLayout("materialGroup")

    def makeUniformBuffer(self, tag:str):
        self.attachedMaterial.uniformGroups[tag].makeUniformBuffer(device=self.device) 
    
    def makeStorageBuffers(self, tag:str):
        self.attachedMaterial.uniformGroups[tag].makeStorageBuffers(device=self.device)

    def makeBindGroupLayout(self, tag:str): 
        self.attachedMaterial.uniformGroups[tag].makeBindGroupLayout(device=self.device) 

    def setTexture(self, value:Texture):
        self.attachedMaterial.uniformGroups["materialGroup"].setTexture(name="texture", value=value)  

    def update(self, command_encoder:wgpu.GPUCommandBuffer): 
        scene = Scene()

        view = scene._cammera.view;

        ratio = scene._canvasWidth / scene._canvasHeight
        near = 0.001
        far = 1000.0 
        proj = glm.transpose(glm.perspectiveLH(glm.radians(60), ratio, near, far)) 
        
        self.Proj = proj 
        self.View = view
        self.Models = np.asarray(self.Models, dtype=np.float32) 
        camPos = glm.vec4(scene._cammera.position, 1.0) 
        self.camPos = np.array(camPos, dtype=np.float32); 

        self.setUniformValues(command_encoder=command_encoder)

    def setUniformValues(self, command_encoder:wgpu.GPUCommandEncoder): 
        self.attachedMaterial.uniformGroups["frameGroup"].setUniform(name="proj", value=self.Proj) 
        self.attachedMaterial.uniformGroups["frameGroup"].setUniform(name="view", value=self.View) 
        self.attachedMaterial.uniformGroups["frameGroup"].setStorage(name="models", value=self.Models)    

        self.attachedMaterial.uniformGroups["frameGroup"].setUniform(name="lightColor", value=self.lightColor) 
        self.attachedMaterial.uniformGroups["frameGroup"].setUniform(name="lightPos", value=self.lightPos) 
        self.attachedMaterial.uniformGroups["frameGroup"].setUniform(name="camPos", value=self.camPos) 

        self.attachedMaterial.uniformGroups["frameGroup"].update(self.device, command_encoder) 