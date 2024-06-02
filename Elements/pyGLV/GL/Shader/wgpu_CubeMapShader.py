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
from Elements.pyGLV.GL.wgpu_texture import Texture, ImportTexture 
from Elements.pyGLV.GL.wgpu_uniform_groups import UniformGroup  
from Elements.pyGLV.GUI.fps_cammera import cammera
from Elements.definitions import SHADER_DIR

class CubeMapShader(Shader):
    def __init__(self, device:wgpu.GPUDevice):  
        super().__init__()

        self.device:wgpu.GPUDevice = device
        self.code = ShaderLoader(SHADER_DIR / "WGPU" / "cubemap_shader.wgsl") 
        self.context = device.create_shader_module(code=self.code)

    def init(self):  
        self.Models = [] 
        self.forward = None;
        self.right = None;
        self.up = None;

        self.attachedMaterial.uniformGroups.update({"frameGroup": UniformGroup(groupName="frameGroup", groupIndex=0)})
        self.attachedMaterial.uniformGroups.update({"materialGroup": UniformGroup(groupName="materialGroup", groupIndex=1)})

        self.addAtribute(name=Buffers.VERTEX, rowLenght=SHADER_TYPES['vec2f'], primitiveType=F32) 

        self.addUniform(
            name="forwards",
            groupName="frameGroup",
            size=SHADER_TYPES['vec4f'] * F32,
            offset=0
        )
        self.addUniform(
            name="right",
            groupName="frameGroup",
            size=SHADER_TYPES['vec4f'] * F32,
            offset=1
        ) 
        self.addUniform(
            name="up",
            groupName="frameGroup",
            size=SHADER_TYPES['vec4f'] * F32,
            offset=2
        )

        self.addTexture(
            name="cubemap", 
            groupName="materialGroup",
            viewDimention=wgpu.TextureViewDimension.cube
        ) 
        self.addSampler(
            name="sampler",
            groupName="materialGroup",
            # sampler=self.device.create_sampler(
            #     address_mode_u=wgpu.AddressMode.repeat,
            #     address_mode_v=wgpu.AddressMode.repeat,
            #     mag_filter=wgpu.FilterMode.linear,
            #     min_filter=wgpu.FilterMode.nearest, 
            #     mipmap_filter=wgpu.FilterMode.nearest,
            #     max_anisotropy=1 
            # ) 
            sampler=self.device.create_sampler()
        ) 

        self.attachedMaterial.uniformGroups["frameGroup"].makeUniformBuffer(device=self.device)

        self.attachedMaterial.uniformGroups["frameGroup"].makeBindGroupLayout(device=self.device) 
        self.attachedMaterial.uniformGroups["materialGroup"].makeBindGroupLayout(device=self.device) 

    def setTexture(self, value:Texture):
        self.attachedMaterial.uniformGroups["materialGroup"].setTexture(name="cubemap", value=value)  

    def update(self, command_encoder:wgpu.GPUCommandBuffer): 
        scene = Scene()  

        dy = -np.tan(np.pi / 8); 
        dx = -dy * (scene._canvasWidth / scene._canvasHeight) 

        forward = scene._cammera.forward 
        right = scene._cammera.right
        up = scene._cammera.up

        self.forward = glm.vec4(forward, 1.0)
        self.right = glm.vec4((dx * right[0]), (dx * right[1]), (dx * right[2]), 1.0) 
        self.up = glm.vec4((dy * up[0]), (dy * up[1]), (dy * up[2]), 1.0)  

        # self.forward = glm.vec4(forward, 1.0) 
        # self.right = glm.vec4(right, 1.0) 
        # self.up = glm.vec4(up, 1.0)

        self.setUniformValues(command_encoder=command_encoder)

    def setUniformValues(self, command_encoder:wgpu.GPUCommandEncoder): 
        self.attachedMaterial.uniformGroups["frameGroup"].setUniform(name="forwards", value=self.forward) 
        self.attachedMaterial.uniformGroups["frameGroup"].setUniform(name="right", value=self.right) 
        self.attachedMaterial.uniformGroups["frameGroup"].setUniform(name="up", value=self.up) 
        self.attachedMaterial.uniformGroups["frameGroup"].update(self.device, command_encoder) 
