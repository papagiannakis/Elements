from __future__ import annotations
import wgpu 
import glm   
import numpy as np
from assertpy import assert_that

from Elements.pyECSS.wgpu_components import Component, RenderExclusiveComponent
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyECSS.wgpu_components import *
from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController
from Elements.pyGLV.GL.wgpu_texture import Texture, TextureLib 
from Elements.pyGLV.GL.wpgu_scene import Scene

SSAO_NOISE_SHADER = """ 
struct Uniforms {  
    projection: mat4x4f,
    screen_size: vec2f,
    near_far: vec2f
}; 

@group(0) @binding(0) var<uniform> ubuffer: Uniforms;
@group(0) @binding(1) var<storage, read> kernel: array<vec4f>;
@group(0) @binding(2) var gPosition: texture_2d<f32>;
@group(0) @binding(3) var gNormal: texture_2d<f32>;
@group(0) @binding(4) var noise: texture_2d<f32>;
@group(0) @binding(5) var noise_sampler: sampler; 

struct VertexOutput { 
    @builtin(position) Position: vec4<f32>,
    @location(0) uv: vec2<f32>
}

@vertex
fn vs_main(
    @builtin(vertex_index) vertex_index: u32
) -> VertexOutput {  

    var POSITIONS = array<vec2<f32>, 6>(
        vec2<f32>(-1.0, -1.0), // bottom-left
        vec2<f32>( 1.0, -1.0), // bottom-right
        vec2<f32>(-1.0,  1.0), // top-left
        vec2<f32>(-1.0,  1.0), // top-left
        vec2<f32>( 1.0, -1.0), // bottom-right
        vec2<f32>( 1.0,  1.0)  // top-right
    );

    var UVS = array<vec2<f32>, 6>(
        vec2<f32>(0.0, 1.0), // bottom-left
        vec2<f32>(1.0, 1.0), // bottom-right
        vec2<f32>(0.0, 0.0), // top-left
        vec2<f32>(0.0, 0.0), // top-left
        vec2<f32>(1.0, 1.0), // bottom-right
        vec2<f32>(1.0, 0.0)  // top-right
    );

    var out: VertexOutput;
    let pos = POSITIONS[vertex_index];
    let vUV = UVS[vertex_index]; 

    out.uv = vUV;
    out.Position = vec4f(pos, 0.0, 1.0);
    return out;
}  

fn LinearizeDepth( 
    depth: f32,
    near: f32,
    far: f32
) -> f32 {  

    let zNdc = 2 * depth - 1; 
    let zEye = (2 * far * near) / ((far + near) - zNdc * (far - near)); 
    let linearDepth = (zEye - near) / (far - near);
    return linearDepth;
}

@fragment
fn fs_main(
    in: VertexOutput
) -> @location(0) vec4f { 

    var pos_coord = in.uv * ubuffer.screen_size; 
    var pos_texel = vec2u(u32(pos_coord.x), u32(pos_coord.y));

    var noise_scale = vec2f(ubuffer.screen_size.x / 4.0, ubuffer.screen_size.y / 4.0);

    var frag_pos = textureLoad(gPosition, pos_texel, 0).xyz;
    var frag_normal = normalize(textureLoad(gNormal, pos_texel, 0).xyz);
    var random_vec = textureSample(noise, noise_sampler, in.uv * noise_scale).xyz;

    var tangent = normalize(random_vec - frag_normal * dot(random_vec, frag_normal));
    var bitangent = cross(frag_normal, tangent);
    var TBN = mat3x3f(tangent, bitangent, frag_normal);

    var occlusion = 0.0; 
    var radius = 0.5;

    for (var i = 0; i < 128; i++) { 
        var sample_pos = TBN * kernel[i].xyz;
        sample_pos = frag_pos + sample_pos * radius; 

        var offset = vec4f(sample_pos, 1.0);
        offset = transpose(ubuffer.projection) * offset; 
        var offset_ndc = offset.xyz;
        var offset_zero_one = offset_ndc.xyz * 0.5 + 0.5;

        var smaple_depth = textureLoad(gPosition, vec2u(u32(offset_zero_one.x), u32(offset_zero_one.y)), 0).z; 
        var range_check = smoothstep(0.0, 1.0, radius / abs(frag_pos.z - smaple_depth));
        var depth_check: bool = (smaple_depth >= sample_pos.z + 0.025);
        occlusion = occlusion + (select(1.0, 0.0, depth_check) * range_check);
    }

    occlusion = 1.0 - (occlusion / 128.0);
    return vec4f(occlusion, occlusion, occlusion, occlusion);
}
"""

class SSAOPass(RenderSystem): 

    # def lerp(self, a, b, f):
    #     return a + f * (b - a)

    def on_create(self, entity: Entity, components: Component | list[Component]): 
        self.shader = GpuController().device.create_shader_module(code=SSAO_NOISE_SHADER);  

        self.storage: wgpu.GPUBuffer = GpuController().device.create_buffer(
            size=(4 * 4) * 128, usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST
        )
        self.uniform: wgpu.GPUBuffer = GpuController().device.create_buffer(
            size=((16 * 4) + (4 * 4) + (4 * 4)), usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
        )
        
        bind_groups_layout_entries = [[]]   
        bind_groups_layout_entries[0].append(
            {
                "binding": 0,
                "visibility": wgpu.ShaderStage.VERTEX | wgpu.ShaderStage.FRAGMENT,
                "buffer": {"type": wgpu.BufferBindingType.uniform},
            }
        ) 
        bind_groups_layout_entries[0].append(
            {
                "binding": 1,
                "visibility": wgpu.ShaderStage.VERTEX | wgpu.ShaderStage.FRAGMENT,
                "buffer": {"type": wgpu.BufferBindingType.read_only_storage},
            }
        ) 
        bind_groups_layout_entries[0].append(
            {
                "binding": 2,
                "visibility": wgpu.ShaderStage.FRAGMENT,
                "texture": {  
                    "sample_type": wgpu.TextureSampleType.unfilterable_float,
                    "view_dimension": wgpu.TextureViewDimension.d2,
                },
            }
        )
        bind_groups_layout_entries[0].append(
            {
                "binding": 3,
                "visibility": wgpu.ShaderStage.FRAGMENT,
                "texture": {  
                    "sample_type": wgpu.TextureSampleType.unfilterable_float,
                    "view_dimension": wgpu.TextureViewDimension.d2,
                },
            }
        )
        bind_groups_layout_entries[0].append(
            {
                "binding": 4,
                "visibility": wgpu.ShaderStage.FRAGMENT,
                "texture": {  
                    "sample_type": wgpu.TextureSampleType.float,
                    "view_dimension": wgpu.TextureViewDimension.d2,
                },
            }
        )
        bind_groups_layout_entries[0].append(
            {
                "binding": 5,
                "visibility": wgpu.ShaderStage.FRAGMENT,
                "sampler": {"type": wgpu.SamplerBindingType.filtering},
            }
        )
        
        self.bind_group_layouts = [] 
        for layout_entries in bind_groups_layout_entries:
            bind_group_layout = GpuController().device.create_bind_group_layout(entries=layout_entries) 
            self.bind_group_layouts.append(bind_group_layout) 
            
        self.pipeline_layout = GpuController().device.create_pipeline_layout(bind_group_layouts=self.bind_group_layouts)

    def on_prepare(self, entity: Entity, components: Component | list[Component], command_encoder: wgpu.GPUCommandEncoder): 

        ssao_kernel_samples = [] 
        for i in range(1, 128):
            sample = glm.vec3(
                np.random.random() * 2.0 - 1.0,
                np.random.random() * 2.0 - 1.0,
                np.random.random() 
            )  
            sample = glm.normalize(sample) 
            sample *= np.random.random() 
            scale = float(i) / 64.0
            # scale = self.lerp(0.1, 1.0, scale * scale)  
            scale = 0.1 + (scale * scale) * (1.0 - 0.1)
            sample *= scale
            sample = glm.vec4(sample, 1.0)

            ssao_kernel_samples.append(np.ascontiguousarray(sample, dtype=np.float32))  

        ssao_kernel_samples_data = np.vstack(ssao_kernel_samples, dtype=np.float32)  

        GpuController().device.queue.write_buffer(
            buffer=self.storage,
            buffer_offset=0,
            data=ssao_kernel_samples_data,
            data_offset=0,
            size=ssao_kernel_samples_data.nbytes
        ) 

        screen_size = np.ascontiguousarray(glm.vec2(GpuController().render_target_size), dtype=np.float32)

        cam = Scene().get_primary_cam() 
        cam_comp: CameraComponent = Scene().get_component(cam, CameraComponent)
        projection = np.ascontiguousarray(cam_comp.projection, dtype=np.float32)
        near_far = np.ascontiguousarray(glm.vec2(cam_comp.near, cam_comp.far), dtype=np.float32)

        GpuController().device.queue.write_buffer(
            buffer=self.uniform,
            buffer_offset=0,
            data=projection,
            data_offset=0,
            size=projection.nbytes
        ) 
        GpuController().device.queue.write_buffer(
            buffer=self.uniform,
            buffer_offset=64,
            data=screen_size,
            data_offset=0,
            size=screen_size.nbytes
        )
        GpuController().device.queue.write_buffer(
            buffer=self.uniform,
            buffer_offset=80,
            data=near_far,
            data_offset=0,
            size=near_far.nbytes
        )

        # We always have two bind groups, so we can play distributing our
        # resources over these two groups in different configurations.
        bind_groups_entries = [[]]
        bind_groups_entries[0].append(
            {
                "binding": 0,
                "resource": {
                    "buffer": self.uniform,
                    "offset": 0,
                    "size": self.uniform.size,
                },
            }
        )
        bind_groups_entries[0].append(
            {
                "binding": 1,
                "resource": {
                    "buffer": self.storage,
                    "offset": 0,
                    "size": self.storage.size,
                },
            }
        )
        bind_groups_entries[0].append(
            {
                "binding": 2,
                "resource": TextureLib().get_texture(name="g_position_gfx").view
            } 
        ) 

        bind_groups_entries[0].append(
            {
                "binding": 3, 
                "resource": TextureLib().get_texture(name="g_normal_gfx").view
            }
        )
        bind_groups_entries[0].append(
            {
                "binding": 4, 
                "resource": TextureLib().get_texture(name="ssao_noise_gfx").view
            }
        ) 
        bind_groups_entries[0].append(
            {
                "binding": 5, 
                "resource": TextureLib().get_texture(name="ssao_noise_gfx").sampler
            }
        )

        # Create the wgou binding objects
        bind_groups = []

        for entries, layouts in zip(bind_groups_entries, self.bind_group_layouts):
            bind_groups.append(
                GpuController().device.create_bind_group(layout=layouts, entries=entries)
            ) 
        self.bind_groups = bind_groups 

        self.render_pipeline = GpuController().device.create_render_pipeline(
            layout=self.pipeline_layout,
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
                        "format": wgpu.TextureFormat.rgba32float,
                        "blend": None 
                    }
                ],
            },
        )
    
    def on_render(self, entity: Entity, components: Component | list[Component], render_pass: wgpu.GPURenderPassEncoder | wgpu.GPUComputePassEncoder):   
        assert_that(
            (type(components) == RenderExclusiveComponent), 
            f"Only accepted entiy/component in blit stage is {RenderExclusiveComponent}"
        ).is_true()

        render_pass.set_pipeline(self.render_pipeline) 
        for bind_group_id, bind_group in enumerate(self.bind_groups):
            render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)

        render_pass.draw(6, 1, 0, 0) 
