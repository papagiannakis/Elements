import re
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
 
        group_ids = self.extract_group_id() 
        if not group_ids:
            raise Exception("No groups found")  
        
        for group in group_ids:
            name = f"({group})" 
            self.attachedMaterial.uniformGroups.update({name: UniformGroup(groupName=name, groupIndex=int(group))})

        attributes = self.extract_attributes() 
        if not attributes:
            raise Exception("No attributes present") 
        
        for attr in attributes:
            self.addAtribute(name=self.attribute_dispatch(attr[1]), rowLenght=SHADER_TYPES[attr[2]], primitiveType=self.separate_type_and_precision(attr[2]))

        uniformContents = self.extract_struct("Uniforms") 
        if not uniformContents: 
            raise Exception("No content")  

        offset = 0
        for pair in uniformContents: 
            shader_precision = self.separate_type_and_precision(pair[1])
            self.addUniform(
                name=pair[0],
                groupName="(0)", 
                size=SHADER_TYPES[pair[1]] * shader_precision,
                offset=offset
            ) 
            offset += 1 

        storage_content = self.extract_storage_read_variables()
        if not storage_content:
            raise Exception("No content") 
        
        for pair in storage_content: 
            shader_precision = self.separate_type_and_precision(pair[1]) 
            self.addStorage(
                name=pair[0],
                groupName="(0)",
                size=SHADER_TYPES[pair[1]] * shader_precision * 1024
            )

        textures = self.extract_textures() 
        if not storage_content:
            raise Exception("No textures")  
        
        for text in textures:
            name = text[0] 
            text_type = wgpu.TextureSampleType.float 

            if text[1] == "texture_depth_2d":
                text_type = wgpu.TextureSampleType.depth
            elif text[1] == "texture_cube<f32>": 
                text_type = wgpu.TextureSampleType.cube

            self.addTexture(
                name=name, 
                groupName="(1)",
                sampleType=text_type
            )

        samplers = self.extract_samplers() 
        if not samplers: 
            raise Exception("vre malaka") 

        for smpler in samplers:
            name = smpler[0] 
            compare = False 
            compare_function = None 

            if smpler[1] == "sampler_comparison":  
                compare = True;
                compare_function = wgpu.CompareFunction.less_equal                  

            self.addSampler(
                name=smpler[0],
                groupName="(1)",
                compare=compare,
                sampler=self.device.create_sampler(compare=compare_function)
            ) 

        self.attachedMaterial.uniformGroups["(0)"].makeUniformBuffer(device=self.device)
        self.attachedMaterial.uniformGroups["(0)"].makeStorageBuffers(device=self.device)

        for bind_group_layouts in self.attachedMaterial.uniformGroups.values(): 
            bind_group_layouts.makeBindGroupLayout(device=self.device)

    def setShadowMap(self, value:Texture):
        self.attachedMaterial.uniformGroups["(1)"].setTexture(name="shadowMap", value=value)

    def setTexture(self, value:Texture):
        self.attachedMaterial.uniformGroups["(1)"].setTexture(name="myTexture", value=value)

    def update(self, command_encoder:wgpu.GPUCommandBuffer):
        scene = Scene()

        light_pos = scene._light;

        view = scene._cammera.getView();
        # view = glm.transpose(glm.lookAtLH(light_pos.xyz, [0.0, 0.0, 0.0], [0.0, 0.0, 1.0]))
        # view = glm.rotate(glm.radians(-90), glm.vec3(1, 0, 0)) * view

        light_view = glm.transpose(glm.lookAtLH(light_pos.xyz, [0.0, 0.0, 0.0], [0.0, 0.0, 1.0]))
        light_view = glm.rotate(glm.radians(-90), glm.vec3(1, 0, 0)) * light_view
        # light_view = glm.rotate(np.deg2rad(-90), glm.vec3(0, 0, 1)) * light_view

        ratio = scene._canvasWidth / scene._canvasHeight
        near = 0.1
        far = 500.0
        light_proj = glm.transpose(glm.perspectiveLH(glm.radians(60), ratio, near, far))
        # light_proj = (glm.orthoLH(-light_pos.x, light_pos.x, -light_pos.y, -light_pos.y, -400, 400))
        # light_proj = glm.transpose(glm.orthoLH(-50.0, 50.0, -50.0, 50.0, near, far))

        ratio = scene._canvasWidth / scene._canvasHeight
        near = 0.01
        far = 500.0
        proj = glm.transpose(glm.perspectiveLH(glm.radians(60), ratio, near, far)) 
        # proj = (glm.orthoLH(-light_pos.x, light_pos.x, -light_pos.y, -light_pos.y, -400, 400))


        self.Proj = np.asarray(proj, dtype=np.float32)
        self.View = np.asarray(view, dtype=np.float32)
        self.Models = np.asarray(self.Models, dtype=np.float32)
        self.Models_ti = np.asarray(self.Models_ti, dtype=np.float32)

        self.light_view = np.asarray(light_view, dtype=np.float32)
        self.light_proj = np.asarray(light_proj, dtype=np.float32)

        self.light_pos = np.asarray(light_pos, dtype=np.float32)
        # self.cam_pos = np.asarray(light_pos, dtype=np.float32)
        self.cam_pos = np.asarray(glm.vec4(scene._cammera.getPos(), 1.0), dtype=np.float32)

        self.setUniformValues(command_encoder=command_encoder)

    def setUniformValues(self, command_encoder:wgpu.GPUCommandEncoder):
        self.attachedMaterial.uniformGroups["(0)"].setUniform(name="proj", value=self.Proj)
        self.attachedMaterial.uniformGroups["(0)"].setUniform(name="view", value=self.View)
        self.attachedMaterial.uniformGroups["(0)"].setUniform(name="light_view", value=self.light_view)
        self.attachedMaterial.uniformGroups["(0)"].setUniform(name="light_proj", value=self.light_proj)
        self.attachedMaterial.uniformGroups["(0)"].setUniform(name="light_pos", value=self.light_pos)
        self.attachedMaterial.uniformGroups["(0)"].setUniform(name="cam_pos", value=self.cam_pos)
        self.attachedMaterial.uniformGroups["(0)"].setStorage(name="models", value=self.Models)
        self.attachedMaterial.uniformGroups["(0)"].setStorage(name="models_ti", value=self.Models_ti)
        self.attachedMaterial.uniformGroups["(0)"].update(self.device, command_encoder)
