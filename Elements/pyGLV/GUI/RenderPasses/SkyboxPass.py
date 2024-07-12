from __future__ import annotations
import wgpu
import glm 
import numpy as np
from assertpy import assert_that

from Elements.pyECSS.wgpu_components import Component, RenderExclusiveComponent, SkyboxComponent, CameraComponent
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController 
from Elements.pyGLV.GL.wgpu_texture import TextureLib, Texture
from Elements.pyGLV.GL.wpgu_scene import Scene

SHADER_CODE = """ 
struct Uniforms {
  viewDirectionProjectionInverse: mat4x4f,
};
 
struct VSOutput {
  @builtin(position) position: vec4f,
  @location(0) pos: vec4f,
};
struct FragOutput { 
    @builtin(frag_depth) depth: f32,
    @location(0) color: vec4f
};
 
@group(0) @binding(0) var<uniform> uni: Uniforms;
@group(0) @binding(1) var ourTexture: texture_cube<f32>;
@group(0) @binding(2) var ourSampler: sampler;
 
@vertex fn vs_main(@builtin(vertex_index) vNdx: u32) -> VSOutput {
  var pos = array(
    vec2f(-1, 3),
    vec2f(-1,-1),
    vec2f( 3,-1),
  );
  var vsOut: VSOutput;
  vsOut.position = vec4f(pos[vNdx], 1, 1);
  vsOut.pos = vsOut.position;
  return vsOut;
}

@fragment fn fs_main(vsOut: VSOutput) -> FragOutput {
  var out: FragOutput;
  let t = transpose(uni.viewDirectionProjectionInverse) * vsOut.pos;
  var color = textureSample(ourTexture, ourSampler, normalize(t.xyz / t.w) * vec3f(-1, 1, 1)); 

  out.depth = 1.0;
  out.color = color;
  return out;
}
"""

class SkyboxPass(RenderSystem):
    
    def on_create(self, entity: Entity, components: Component | list[Component]):
        assert_that(type(components) == SkyboxComponent).is_true()
        skybox: SkyboxComponent = components 
         
        # WGSL example
        shader = GpuController().device.create_shader_module(code=SHADER_CODE);
        
        self.uniform_buffer: wgpu.GPUBuffer = GpuController().device.create_buffer(
            size=16 * 4, usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
        )

        # We always have two bind groups, so we can play distributing our
        # resources over these two groups in different configurations.
        bind_groups_entries = [[]]
        bind_groups_layout_entries = [[]]

        bind_groups_entries[0].append(
            {
                "binding": 0,
                "resource": {
                    "buffer": self.uniform_buffer,
                    "offset": 0,
                    "size": self.uniform_buffer.size,
                },
            }
        )
        bind_groups_layout_entries[0].append(
            {
                "binding": 0,
                "visibility": wgpu.ShaderStage.VERTEX | wgpu.ShaderStage.FRAGMENT,
                "buffer": {"type": wgpu.BufferBindingType.uniform},
            }
        ) 

        bind_groups_entries[0].append(
            {
                "binding": 1,
                "resource": TextureLib().get_skybox(name=skybox.gpu_texture_name).view
            } 
        ) 
        bind_groups_layout_entries[0].append(
            {
                "binding": 1,
                "visibility": wgpu.ShaderStage.FRAGMENT,
                "texture": {  
                    "sample_type": wgpu.TextureSampleType.float,
                    "view_dimension": wgpu.TextureViewDimension.cube,
                },
            }
        )

        bind_groups_entries[0].append(
            {
                "binding": 2, 
                "resource": TextureLib().get_skybox(name=skybox.gpu_texture_name).sampler
            }
        )
        bind_groups_layout_entries[0].append(
            {
                "binding": 2,
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

        pipeline_layout = GpuController().device.create_pipeline_layout(bind_group_layouts=bind_group_layouts)
        
        self.bind_groups = bind_groups
        self.render_pipeline = GpuController().device.create_render_pipeline(
            layout=pipeline_layout,
            vertex={
                "module": shader,
                "entry_point": "vs_main", 
                "buffers": [], 
            },
            primitive={
                "topology": wgpu.PrimitiveTopology.triangle_strip,
                "front_face": wgpu.FrontFace.ccw,
                "cull_mode": wgpu.CullMode.none,
            },
            depth_stencil={ 
                "format": wgpu.TextureFormat.depth32float,
                "depth_write_enabled": True,
                "depth_compare": wgpu.CompareFunction.less_equal,
            },            
            multisample=None,
            fragment={
                "module": shader,
                "entry_point": "fs_main",
                "targets": [
                    {
                        "format": wgpu.TextureFormat.rgba8unorm,
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
    
    def on_prepare(self, entity: Entity, components: Component | list[Component], command_encoder: wgpu.GPUCommandEncoder):
        cam:Entity = Scene().get_primary_cam()
        
        camera:CameraComponent = Scene().get_component(cam, CameraComponent)
        view = camera.view     
        view[3].x = 0
        view[3].y = 0
        view[3].z = 0 
        view_proj = camera.projection * view
        inv_view_proj = glm.inverse(view_proj)
        inv_view_proj_data = np.ascontiguousarray(inv_view_proj, dtype=np.float32)
        
        GpuController().device.queue.write_buffer(
            buffer=self.uniform_buffer,
            buffer_offset=0,
            data=inv_view_proj_data,
            data_offset=0,
            size=inv_view_proj_data.nbytes
        )
    
    def on_render(self, entity: Entity, components: Component | list[Component], render_pass: wgpu.GPURenderPassEncoder):
        render_pass.set_pipeline(self.render_pipeline) 
        for bind_group_id, bind_group in enumerate(self.bind_groups):
            render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)

        render_pass.draw(3, 1, 0, 0) 