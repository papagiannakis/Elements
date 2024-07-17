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

SSAO_NOISE_TEXTURE_SIZE = 64 
SSAO_SAMPLE_COUNT = 64
SSAO_WORK_GROUP_SIZE = [8, 8]

SSAO_SHADER = """ 
const SAMPLE_COUNT:u32 = 64; 
const RADIUS:f32 = 1.0; 
const BIAS:f32 = 0.01;

struct Uniforms {
    view_matrix: mat4x4<f32>,
    projection: mat4x4<f32>,
    uv_to_view_space_add: vec2<f32>,
    uv_to_view_space_mul: vec2<f32>,
    depth_add_mul: vec2<f32>,
    noise_offset: vec2<u32>,
};

struct Samples {
    data: array<vec4<f32>>,
};

@group(0) @binding(0) var<uniform> uniforms: Uniforms;
@group(0) @binding(1) var<storage, read> samples: Samples;
@group(0) @binding(2) var r_output_texture: texture_storage_2d<rgba32float, write>;
@group(0) @binding(3) var r_normal_texture: texture_2d<f32>;
@group(0) @binding(4) var r_noise_texture: texture_2d<f32>;

fn screen_space_depth_to_view_space_z(d: f32) -> f32 {
    return uniforms.depth_add_mul.y / (uniforms.depth_add_mul.x - d);
}

fn uv_to_view_space_position(uv: vec2<f32>, depth: f32) -> vec3<f32> {
    let z = screen_space_depth_to_view_space_z(depth);
    return vec3<f32>((uv * uniforms.uv_to_view_space_mul + uniforms.uv_to_view_space_add) * -z, z);
}

fn load_random_vec(frag_coord: vec2<u32>) -> vec3<f32> {
    let p = (frag_coord + uniforms.noise_offset) % vec2<u32>(textureDimensions(r_noise_texture));
    return vec3<f32>(textureLoad(r_noise_texture, vec2<i32>(p), 0).xy, 0.0);
}

@compute @workgroup_size(8, 8)
fn main(@builtin(global_invocation_id) global_invocation_id: vec3<u32>) {
    let size = vec2<u32>(textureDimensions(r_output_texture));
    let frag_coord = global_invocation_id.xy;

    if (!all(frag_coord < size)) {
        return;
    }

    let depth = textureLoad(r_normal_texture, vec2<i32>(frag_coord), 0).a;
    if (depth == 1.0) {
        textureStore(r_output_texture, vec2<i32>(frag_coord), vec4<f32>(1.0, 1.0, 1.0, 1.0));
        return;
    }

    let frag_uv = (vec2<f32>(frag_coord) + 0.5) / vec2<f32>(size);
    let view_pos = uv_to_view_space_position(frag_uv, depth);
    let normal = mat3x3<f32>(uniforms.view_matrix[0].xyz, uniforms.view_matrix[1].xyz, uniforms.view_matrix[2].xyz)
        * textureLoad(r_normal_texture, vec2<i32>(frag_coord), 0).xyz;
    let random_vec = load_random_vec(frag_coord);

    let tangent = normalize(random_vec - normal * dot(random_vec, normal));
    let bitangent = cross(normal, tangent);
    let tbn = mat3x3<f32>(tangent, bitangent, normal);

    var occlusion = 0.0;
    for (var i = 0u; i < SAMPLE_COUNT; i = i + 1u) {
        let sample_vec = RADIUS * (tbn * samples.data[i].xyz);
        let sample_pos = view_pos + sample_vec;

        let sample_clip_pos = uniforms.projection * vec4<f32>(sample_pos, 1.0);
        let sample_ndc = sample_clip_pos.xy / sample_clip_pos.w;
        let sample_uv = sample_ndc * vec2<f32>(0.5, -0.5) + 0.5;
        var sample_coords = vec2<i32>(floor(sample_uv * vec2<f32>(size)));
        sample_coords = clamp(sample_coords, vec2<i32>(0), vec2<i32>(size) - 1);

        let sample_depth = textureLoad(r_normal_texture, sample_coords, 0).a;
        if (sample_depth == 1.0) {
            continue;
        }

        let z = screen_space_depth_to_view_space_z(sample_depth);
        let range_check = smoothstep(0.0, 1.0, RADIUS / abs(view_pos.z - z));
        occlusion = occlusion + select(0.0, 1.0, z >= sample_pos.z + BIAS) * range_check;
    }

    occlusion = 1.0 - (occlusion / f32(SAMPLE_COUNT));
    textureStore(
        r_output_texture,
        vec2<i32>(frag_coord),
        vec4<f32>(occlusion, occlusion, occlusion, occlusion)
    );
}
"""

class SSAOPass(RenderSystem):   

    def get_sample_vectors(self, count: int) -> np.ndarray:
        vectors = []
        for i in range(count):
            lng = np.random.uniform(0.0, 2.0 * np.pi)
            lat = np.arccos(np.random.uniform(0.0, 1.0))
            r = np.sqrt((i + 1) / count)
            
            vector = [
                r * np.cos(lng) * np.sin(lat),
                r * np.sin(lng) * np.sin(lat),
                r * np.cos(lat),
                0.0
            ]
            vectors.append(vector)
        
        return np.array(vectors, dtype=np.float32)

    def on_create(self, entity: Entity, components: Component | list[Component]): 
        assert_that(
            (type(components) == RenderExclusiveComponent), 
            f"Only accepted entiy/component in blit stage is {RenderExclusiveComponent}"
        ).is_true()

        TextureLib().create_noise_texture(name="ssao_noise_gfx", config={
            "width": SSAO_NOISE_TEXTURE_SIZE,
            "height": SSAO_NOISE_TEXTURE_SIZE,
            "depth_or_array_layers": 1
        })

        self.shader = GpuController().device.create_shader_module(code=SSAO_SHADER);  

        self.uniform: wgpu.GPUBuffer = GpuController().device.create_buffer(
            size=((16 * 4) + (16 * 4) + (4 * 4) + (4 * 4) + (4 * 4) + (4 * 4)), usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
        ) 

        # sample kernel
        self.sample_storage: wgpu.GPUBuffer = GpuController().device.create_buffer(
            size=(4 * 4) * SSAO_SAMPLE_COUNT, usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST
        )
        kernel_samples = self.get_sample_vectors(SSAO_SAMPLE_COUNT)
        GpuController().device.queue.write_buffer(
            buffer=self.sample_storage,
            buffer_offset=0,
            data=kernel_samples,
            data_offset=0,
            size=kernel_samples.nbytes
        )  
        
        bind_groups_layout_entries = [[]]   
        bind_groups_layout_entries[0].append(
            {
                "binding": 0,
                "visibility": wgpu.ShaderStage.COMPUTE,
                "buffer": {"type": wgpu.BufferBindingType.uniform},
            }
        ) 
        bind_groups_layout_entries[0].append(
            {
                "binding": 1,
                "visibility": wgpu.ShaderStage.COMPUTE,
                "buffer": {"type": wgpu.BufferBindingType.read_only_storage},
            }
        ) 
        bind_groups_layout_entries[0].append(
            {
                "binding": 2,
                "visibility": wgpu.ShaderStage.COMPUTE,
                "storage_texture": {"access": wgpu.StorageTextureAccess.write_only, "format": wgpu.TextureFormat.rgba32float},
            }
        ) 
        bind_groups_layout_entries[0].append(
            {
                "binding": 3,
                "visibility": wgpu.ShaderStage.COMPUTE,
                "texture": {  
                    "sample_type": wgpu.TextureSampleType.unfilterable_float,
                    "view_dimension": wgpu.TextureViewDimension.d2,
                },
            }
        )
        bind_groups_layout_entries[0].append(
            {
                "binding": 4,
                "visibility": wgpu.ShaderStage.COMPUTE,
                "texture": {  
                    "sample_type": wgpu.TextureSampleType.unfilterable_float,
                    "view_dimension": wgpu.TextureViewDimension.d2,
                },
            }
        )
        
        self.bind_group_layouts = [] 
        for layout_entries in bind_groups_layout_entries:
            bind_group_layout = GpuController().device.create_bind_group_layout(entries=layout_entries) 
            self.bind_group_layouts.append(bind_group_layout) 
            
        self.pipeline_layout = GpuController().device.create_pipeline_layout(bind_group_layouts=self.bind_group_layouts)

    def on_prepare(self, entity: Entity, components: Component | list[Component], command_encoder: wgpu.GPUCommandEncoder): 

        cam = Scene().get_primary_cam() 
        cam_comp: CameraComponent = Scene().get_component(cam, CameraComponent) 
        view = glm.transpose(cam_comp.view)
        projection = glm.transpose(cam_comp.projection)  
        
        noise_offset = np.ascontiguousarray(glm.vec2(0, 0), dtype=np.uint32)  

        tan_half_fov_x = 1.0 / projection[0][0]
        tan_half_fov_y = 1.0 / projection[1][1]
 
        uv_to_view_space_mul = np.ascontiguousarray(glm.vec2(tan_half_fov_x * 2.0, tan_half_fov_y * -2.0), dtype=np.float32)
        uv_to_view_space_add = np.ascontiguousarray(glm.vec2(tan_half_fov_x * -1.0, tan_half_fov_y), dtype=np.float32)

        # depth_add = np.float32(-projection[2][2])
        # depth_mul = np.float32(projection[3][2]) 

        depth_add_mul = np.ascontiguousarray(glm.vec2(-projection[2][2], projection[3][2]), dtype=np.float32)

        view = np.ascontiguousarray(view, dtype=np.float32)
        projection = np.ascontiguousarray(projection, dtype=np.float32) 

        GpuController().device.queue.write_buffer(
            buffer=self.uniform,
            buffer_offset=0,
            data=view,
            data_offset=0,
            size=view.nbytes
        ) 
        GpuController().device.queue.write_buffer(
            buffer=self.uniform,
            buffer_offset=64,
            data=projection,
            data_offset=0,
            size=projection.nbytes
        )
        GpuController().device.queue.write_buffer(
            buffer=self.uniform,
            buffer_offset=128,
            data=uv_to_view_space_add,
            data_offset=0,
            size=uv_to_view_space_add.nbytes
        )
        GpuController().device.queue.write_buffer(
            buffer=self.uniform,
            buffer_offset=144,
            data=uv_to_view_space_mul,
            data_offset=0,
            size=uv_to_view_space_mul.nbytes
        )
        GpuController().device.queue.write_buffer(
            buffer=self.uniform,
            buffer_offset=160,
            data=depth_add_mul,
            data_offset=0,
            size=depth_add_mul.nbytes
        )
        GpuController().device.queue.write_buffer(
            buffer=self.uniform,
            buffer_offset=176,
            data=noise_offset,
            data_offset=0,
            size=noise_offset.nbytes
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
                    "buffer": self.sample_storage,
                    "offset": 0,
                    "size": self.sample_storage.size,
                },
            }
        )
        bind_groups_entries[0].append(
            {
                "binding": 2,
                "resource": TextureLib().get_texture(name="ssao_gfx").view
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

        # Create the wgou binding objects
        bind_groups = []

        for entries, layouts in zip(bind_groups_entries, self.bind_group_layouts):
            bind_groups.append(
                GpuController().device.create_bind_group(layout=layouts, entries=entries)
            ) 
        self.bind_groups = bind_groups 

        self.render_pipeline = GpuController().device.create_compute_pipeline(
            layout=self.pipeline_layout,
            compute={
                "module": self.shader,
                "entry_point": "main"
            }
        )
    
    def on_render(self, entity: Entity, components: Component | list[Component], render_pass: wgpu.GPURenderPassEncoder | wgpu.GPUComputePassEncoder):   

        screen_size = GpuController().render_target_size

        work_group_count_x = np.ceil(screen_size[0] / SSAO_WORK_GROUP_SIZE[0]).astype(int)
        work_group_count_y = np.ceil(screen_size[1] / SSAO_WORK_GROUP_SIZE[1]).astype(int)

        render_pass.set_pipeline(self.render_pipeline) 
        for bind_group_id, bind_group in enumerate(self.bind_groups):
            render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)

        render_pass.dispatch_workgroups(work_group_count_x, work_group_count_y, 1)
