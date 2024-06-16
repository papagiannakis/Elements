from __future__ import annotations
import wgpu   
from assertpy import assert_that

from Elements.pyECSS.wgpu_components import Component, RenderExclusiveComponent
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyGLV.GUI.wgpu_cache_manager import GpuCache 


BLIT_SHADER_CODE = """  
@group(0) @binding(0) var tex: texture_2d<f32>;
@group(0) @binding(1) var samp: sampler; 

@vertex
fn vs_main(@builtin(vertex_index) vertex_index: u32) -> @builtin(position) vec4<f32> {
    var positions = array<vec2<f32>, 3>(
        vec2<f32>(-1.0, -1.0),
        vec2<f32>(3.0, -1.0),
        vec2<f32>(-1.0, 3.0)
    );

    var position = positions[vertex_index];
    return vec4<f32>(position, 0.0, 1.0);
} 

@fragment
fn fs_main(@builtin(position) fragCoord: vec4<f32>) -> @location(0) vec4<f32> {
    let uv = fragCoord.xy * 0.5 + vec2<f32>(0.5, 0.5);
    return textureSample(tex, samp, uv);
}
"""


class BlitSurafacePass(RenderSystem): 

    def on_create(self, entity: Entity, components: Component | list[Component]): 
        self.shader = GpuCache().device.create_shader_module(code=BLIT_SHADER_CODE);

    def on_prepare(self, entity: Entity, components: Component | list[Component], command_encoder: wgpu.GPUCommandEncoder): 
        # We always have two bind groups, so we can play distributing our
        # resources over these two groups in different configurations.
        bind_groups_entries = [[]]
        bind_groups_layout_entries = [[]]

        bind_groups_entries[0].append(
            {
                "binding": 0,
                "resource": GpuCache().canvas_texture_view
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
                "resource": GpuCache().canvas_texture_sampler
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
            bind_group_layout = GpuCache().device.create_bind_group_layout(entries=layout_entries)
            bind_group_layouts.append(bind_group_layout)
            bind_groups.append(
                GpuCache().device.create_bind_group(layout=bind_group_layout, entries=entries)
            ) 
        self.bind_groups = bind_groups

        pipeline_layout = GpuCache().device.create_pipeline_layout(bind_group_layouts=bind_group_layouts)

        self.render_pipeline = GpuCache().device.create_render_pipeline(
            layout=pipeline_layout,
            vertex={
                "module": self.shader,
                "entry_point": "vs_main", 
                "buffers": [], 
            },
            primitive={
                "topology": wgpu.PrimitiveTopology.triangle_list,
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
                        "format": GpuCache().render_texture_format,
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
    
    def on_render(self, entity: Entity, components: Component | list[Component], render_pass):   
        assert_that(
            (type(components) == RenderExclusiveComponent), 
            f"Only accepted entiy/component in blit stage is {RenderExclusiveComponent}"
        ).is_true()

        render_pass.set_pipeline(self.render_pipeline) 
        for bind_group_id, bind_group in enumerate(self.bind_groups):
            render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)

        render_pass.draw(3, 1, 0, 0) 

