
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
        for key, value in self.uniformGroups.items():
            layouts.append(value.bindGroupLayout) 

        self.pipelineLayout = device.create_pipeline_layout(
            bind_group_layouts=layouts
        ) 

    def makePipeline(self, device:wgpu.GPUDevice, renderTextureFormat):
        self.makePipelineLayout(device=device) 
        self.pipeline = device.create_render_pipeline(
            layout=self.pipelineLayout,
            vertex={
                "module": self.shader.getShader(),
                "entry_point": "vs_main", 
                "buffers": self.shader.getVertexBufferLayout(),
            },
            primitive={
                "topology": wgpu.PrimitiveTopology.triangle_list,
                "front_face": wgpu.FrontFace.ccw,
                "cull_mode": wgpu.CullMode.none,
            },
            depth_stencil={
                "format": wgpu.TextureFormat.depth24plus,
                "depth_write_enabled": True,
                "depth_compare": wgpu.CompareFunction.less,
            },
            multisample=None,
            fragment={
                "module": self.shader.getShader(),
                "entry_point": "fs_main",
                "targets": [
                    {
                        "format": renderTextureFormat,
                        "blend": {
                            "alpha": (
                                wgpu.BlendFactor.one,
                                wgpu.BlendFactor.zero,
                                wgpu.BlendOperation.add,
                            ),
                            "color": (
                                wgpu.BlendFactor.one,
                                wgpu.BlendFactor.zero,
                                wgpu.BlendOperation.add,
                            ),
                        },
                    }
                ],
            },
        )

        return self.pipeline

        