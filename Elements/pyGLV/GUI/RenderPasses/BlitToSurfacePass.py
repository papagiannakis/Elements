from __future__ import annotations
import wgpu   
from assertpy import assert_that

from Elements.pyECSS.wgpu_components import Component, RenderExclusiveComponent
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController 
from Elements.pyGLV.GL.wgpu_texture import TextureLib, Texture


BLIT_SHADER_CODE = """  
@group(0) @binding(0) var tex: texture_2d<f32>;
@group(0) @binding(1) var samp: sampler; 

struct VertexOutput { 
    @builtin(position) Position: vec4<f32>,
    @location(0) fragCoord: vec2<f32>
}

@vertex
fn vs_main(@builtin(vertex_index) vertex_index: u32) -> VertexOutput {
    var POSITIONS: array<vec2<f32>, 4> = array<vec2<f32>, 4>(
        vec2<f32>(-1.0, -1.0),
        vec2<f32>( 1.0, -1.0),
        vec2<f32>(-1.0,  1.0),
        vec2<f32>( 1.0,  1.0)
    );

    var UVS: array<vec2<f32>, 4> = array<vec2<f32>, 4>(
        vec2<f32>(0.0, 0.0),
        vec2<f32>(1.0, 0.0),
        vec2<f32>(0.0, 1.0),
        vec2<f32>(1.0, 1.0)
    );

    var out: VertexOutput;
    let pos = POSITIONS[vertex_index];
    let vUV = UVS[vertex_index]; 

    out.fragCoord = vUV;
    out.Position = vec4f(pos, 0.0, 1.0);
    return out;
} 

@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
    return textureSample(tex, samp, in.fragCoord);
}
"""


class BlitSurafacePass(RenderSystem): 

    def on_create(self, entity: Entity, components: Component | list[Component]): 
        self.shader = GpuController().device.create_shader_module(code=BLIT_SHADER_CODE);

    def on_prepare(self, entity: Entity, components: Component | list[Component], command_encoder: wgpu.GPUCommandEncoder): 
        # We always have two bind groups, so we can play distributing our
        # resources over these two groups in different configurations.
        bind_groups_entries = [[]]
        bind_groups_layout_entries = [[]]

        bind_groups_entries[0].append(
            {
                "binding": 0,
                "resource": TextureLib().get_texture(name="render_target").view
            } 
        ) 
        bind_groups_layout_entries[0].append(
            {
                "binding": 0,
                "visibility": wgpu.ShaderStage.FRAGMENT,
                "texture": {  
                    "sample_type": wgpu.TextureSampleType.float,
                    "view_dimension": wgpu.TextureViewDimension.d2,
                },
            }
        )

        bind_groups_entries[0].append(
            {
                "binding": 1, 
                "resource": TextureLib().get_texture(name="render_target").sampler
            }
        )
        bind_groups_layout_entries[0].append(
            {
                "binding": 1,
                "visibility": wgpu.ShaderStage.FRAGMENT,
                "sampler": {"type": wgpu.SamplerBindingType.filtering},
            }
        )

        # Create the wgou binding objects
        bind_group_layouts = []
        bind_groups = []

        for entries, layout_entries in zip(bind_groups_entries, bind_groups_layout_entries):
            bind_group_layout = GpuController().device.create_bind_group_layout(entries=layout_entries)
            bind_group_layouts.append(bind_group_layout)
            bind_groups.append(
                GpuController().device.create_bind_group(layout=bind_group_layout, entries=entries)
            ) 
        self.bind_groups = bind_groups

        pipeline_layout = GpuController().device.create_pipeline_layout(bind_group_layouts=bind_group_layouts)

        self.render_pipeline = GpuController().device.create_render_pipeline(
            layout=pipeline_layout,
            vertex={
                "module": self.shader,
                "entry_point": "vs_main", 
                "buffers": [], 
            },
            primitive={
                "topology": wgpu.PrimitiveTopology.triangle_strip,
                "front_face": wgpu.FrontFace.ccw,
                "cull_mode": wgpu.CullMode.none,
            },
            depth_stencil=None,            
            multisample=None,
            fragment={
                "module": self.shader,
                "entry_point": "fs_main",
                "targets": [
                    {
                        "format": GpuController().render_texture_format,
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
    
    def on_render(self, entity: Entity, components: Component | list[Component], render_pass:wgpu.GPURenderPassEncoder):   
        assert_that(
            (type(components) == RenderExclusiveComponent), 
            f"Only accepted entiy/component in blit stage is {RenderExclusiveComponent}"
        ).is_true()

        render_pass.set_pipeline(self.render_pipeline) 
        for bind_group_id, bind_group in enumerate(self.bind_groups):
            render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)

        render_pass.draw(4, 1, 0, 0) 

