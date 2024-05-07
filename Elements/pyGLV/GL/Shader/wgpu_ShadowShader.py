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

class ShadowShader(Shader):
    def __init__(self, device:wgpu.GPUDevice):  
        super().__init__()

        self.device:wgpu.GPUDevice = device
        self.code = ShaderLoader(SHADER_DIR / "WGPU" / "shadow_shader.wgsl") 
        self.context = device.create_shader_module(code=self.code)

    def init(self):  
        self.Models = [] 
        self.Models_ti = []
        self.Proj = None 
        self.View = None  

        self.light_view = None
        self.light_proj = None

        self.light_pos = None
        self.cam_pos = None

        self.attachedMaterial.uniformGroups.update({"frameGroup": UniformGroup(groupName="frameGroup", groupIndex=0)})
        self.attachedMaterial.uniformGroups.update({"materialGroup": UniformGroup(groupName="materialGroup", groupIndex=1)})

        self.addAtribute(name=Buffers.VERTEX, rowLenght=SHADER_TYPES['vec3f'], primitiveType=F32)
        self.addAtribute(name=Buffers.NORMAL, rowLenght=SHADER_TYPES['vec3f'], primitiveType=F32) 
        self.addAtribute(name=Buffers.UV, rowLenght=SHADER_TYPES['vec2f'], primitiveType=F32) 

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
            name="light_proj", 
            groupName="frameGroup",
            size=SHADER_TYPES['mat4x4'] * F32, 
            offset=2,
        ) 
        self.addUniform(
            name="light_view",   
            groupName="frameGroup",
            size=SHADER_TYPES['mat4x4'] * F32, 
            offset=3
        )  
        self.addUniform(
            name="light_pos",   
            groupName="frameGroup",
            size=SHADER_TYPES['vec4f'] * F32, 
            offset=4
        )  
        self.addUniform(
            name="cam_pos",   
            groupName="frameGroup",
            size=SHADER_TYPES['vec4f'] * F32, 
            offset=5
        )  

        self.addStorage(
            name="models", 
            groupName="frameGroup",
            size=(SHADER_TYPES['mat4x4'] * F32) * 1024
        )   
        self.addStorage( 
            name="models_ti",
            groupName="frameGroup",
            size=(SHADER_TYPES['mat4x4'] * F32) * 1024
        ) 

        self.addTexture( 
            name="texture",
            groupName="materialGroup",
        )
        self.addTexture(
            name="shadowMap",
            groupName="materialGroup", 
            sampleType=wgpu.TextureSampleType.depth
        )
        self.addSampler(
            name="shadowSampler",
            groupName="materialGroup",
            compare=True,
            sampler=self.device.create_sampler(compare=wgpu.CompareFunction.less_equal)
        ) 
        self.addSampler(
            name="textureSampler",
            groupName="materialGroup",
            sampler=self.device.create_sampler()
        )

        self.attachedMaterial.uniformGroups["frameGroup"].makeUniformBuffer(device=self.device)
        self.attachedMaterial.uniformGroups["frameGroup"].makeStorageBuffers(device=self.device)
        self.attachedMaterial.uniformGroups["frameGroup"].makeBindGroupLayout(device=self.device) 
        self.attachedMaterial.uniformGroups["materialGroup"].makeBindGroupLayout(device=self.device) 

    def setShadowMap(self, value:Texture):
        self.attachedMaterial.uniformGroups["materialGroup"].setTexture(name="shadowMap", value=value)  

    def setTexture(self, value:Texture):
        self.attachedMaterial.uniformGroups["materialGroup"].setTexture(name="texture", value=value)

    def update(self, command_encoder:wgpu.GPUCommandBuffer): 
        scene = Scene() 

        light_pos = scene._light;

        view = scene._cammera.view; 
        light_view = glm.transpose(glm.lookAtLH(light_pos.xyz, [0.0, 0.0, 0.0], [0.0, 0.0, 1.0]))
        # light_view = glm.rotate(np.deg2rad(-90), glm.vec3(0, 0, 1)) * light_view 

        ratio = scene._canvasWidth / scene._canvasHeight
        near = 0.1
        far = 1000.0
        light_proj = glm.transpose(glm.perspectiveLH(glm.radians(90), ratio, near, far))
        # light_proj = glm.transpose(glm.orthoLH(-100, 100, -100, 100, -400, 400))
        # light_proj = glm.transpose(glm.orthoLH(-50.0, 50.0, -50.0, 50.0, near, far))

        ratio = scene._canvasWidth / scene._canvasHeight
        near = 0.01
        far = 500.0 
        proj = glm.transpose(glm.perspectiveLH(glm.radians(60), ratio, near, far))  

        
        self.Proj = np.asarray(proj, dtype=np.float32) 
        self.View = np.asarray(view, dtype=np.float32)
        self.Models = np.asarray(self.Models, dtype=np.float32)   
        self.Models_ti = np.asarray(self.Models_ti, dtype=np.float32)

        self.light_view = np.asarray(light_view, dtype=np.float32)
        self.light_proj = np.asarray(light_proj, dtype=np.float32)  

        self.light_pos = np.asarray(light_pos, dtype=np.float32) 
        self.cam_pos = np.asarray(glm.vec4(scene._cammera.position, 1.0), dtype=np.float32) 

        self.setUniformValues(command_encoder=command_encoder)

    def setUniformValues(self, command_encoder:wgpu.GPUCommandEncoder): 
        self.attachedMaterial.uniformGroups["frameGroup"].setUniform(name="proj", value=self.Proj) 
        self.attachedMaterial.uniformGroups["frameGroup"].setUniform(name="view", value=self.View) 
        self.attachedMaterial.uniformGroups["frameGroup"].setUniform(name="light_view", value=self.light_view) 
        self.attachedMaterial.uniformGroups["frameGroup"].setUniform(name="light_proj", value=self.light_proj) 
        self.attachedMaterial.uniformGroups["frameGroup"].setUniform(name="light_pos", value=self.light_pos) 
        self.attachedMaterial.uniformGroups["frameGroup"].setUniform(name="cam_pos", value=self.cam_pos) 
        self.attachedMaterial.uniformGroups["frameGroup"].setStorage(name="models", value=self.Models) 
        self.attachedMaterial.uniformGroups["frameGroup"].setStorage(name="models_ti", value=self.Models_ti) 
        self.attachedMaterial.uniformGroups["frameGroup"].update(self.device, command_encoder) 
