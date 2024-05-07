
import wgpu
from Elements.pyGLV.GL.wgpu_shader import Shader
from Elements.pyGLV.GL.wgpu_uniform_groups import UniformGroup

class Material:
    def __init__(self, tag:str, shader:any): 
        self.tag = tag 
        self.shader = shader
        self.shader.attachedMaterial = self  
        self.uniformGroups = {} 
        self.shader.init()  

        self.pipelineLayout = None 
        self.pipeline = None

    def makePipelineLayout(self, device:wgpu.GPUDevice):
        layouts = []
        for value in self.uniformGroups.values():
            layouts.append(value.bindGroupLayout) 

        self.pipelineLayout = device.create_pipeline_layout(
            bind_group_layouts=layouts
        ) 

    def makePipeline(self, device:wgpu.GPUDevice, renderPass):
        self.makePipelineLayout(device=device) 
        self.pipeline = device.create_render_pipeline(
            layout=self.pipelineLayout,
            vertex={
                "module": self.shader.getShader(),
                "entry_point": "vs_main", 
                "buffers": self.shader.getVertexBufferLayout(),
            },
            primitive=renderPass.primitive,
            depth_stencil=renderPass.depth_stencil,
            multisample=None,
            fragment={
                "module": self.shader.getShader(),
                "entry_point": "fs_main",
                "targets": renderPass.colorBlend
            },
        )

        return self.pipeline

        