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

SSAO_WORK_GROUP_SIZE = [8, 8]

SSAO_BLUR_SHADER = """ 
struct Uniforms {
    depth_add_mul: vec2<f32>,
};

@group(0) @binding(0)
var<uniform> uniforms: Uniforms;
@group(0) @binding(1)
var r_output_texture: texture_storage_2d<rgba8unorm, write>;
@group(0) @binding(2)
var r_ssao_texture: texture_2d<f32>;
@group(0) @binding(3)
var r_normal_texture: texture_2d<f32>;

const KERNEL_RADIUS: i32 = 5;

fn screen_space_depth_to_view_space_z(d: f32) -> f32 {
    return uniforms.depth_add_mul.y / (uniforms.depth_add_mul.x - d);
}

fn get_view_space_z(p: vec2<i32>) -> f32 {
    let d = textureLoad(r_normal_texture, p, 0).a;
    return screen_space_depth_to_view_space_z(d);
}

fn cross_bilateral_weight(r: f32, z: f32, z0: f32) -> f32 {
    let blur_sigma = (f32(KERNEL_RADIUS) + 1.0) * 0.5;
    let blur_falloff = 1.0 / (2.0 * blur_sigma * blur_sigma);

    // assuming that d and d0 are pre-scaled linear depths
    let dz = z0 - z;
    return exp2(-r*r*blur_falloff - dz*dz);
}

fn process_sample(
    p: vec2<i32>,
    r: f32,
    z0: f32,
    total_ao: ptr<function, f32>,
    total_weight: ptr<function, f32>
) {
    let z = get_view_space_z(p);
    let ao = textureLoad(r_ssao_texture, p, 0).x;

    let weight = cross_bilateral_weight(r, z, z0);
    *total_ao = *total_ao + weight * ao;
    *total_weight = *total_weight + weight;
}

@compute @workgroup_size(8, 8)
fn blur_x(@builtin(global_invocation_id) global_invocation_id: vec3<u32>) {
    let size = vec2<i32>(textureDimensions(r_output_texture));
    let p0 = vec2<i32>(global_invocation_id.xy);

    if (!all(p0 < size)) {
        return;
    }

    let z0: f32 = get_view_space_z(p0);
    var total_ao: f32 = 0.0;
    var total_weight: f32 = 0.0;

    let x1 = max(p0.x - KERNEL_RADIUS, 0);
    let x2 = min(p0.x + KERNEL_RADIUS, size.x - 1);

    for (var x = x1; x <= x2; x = x + 1) {
        let p = vec2<i32>(x, p0.y);
        let r = abs(f32(p0.x - x));
        process_sample(p, r, z0, &total_ao, &total_weight);
    }

    let ao = total_ao / total_weight;
    textureStore(r_output_texture, p0, vec4<f32>(ao, ao, ao, ao));
}

@compute @workgroup_size(8, 8)
fn blur_y(@builtin(global_invocation_id) global_invocation_id: vec3<u32>) {
    let size = vec2<i32>(textureDimensions(r_output_texture));
    let p0 = vec2<i32>(global_invocation_id.xy);

    if (!all(p0 < size)) {
        return;
    }

    let z0: f32 = get_view_space_z(p0);
    var total_ao: f32 = 0.0;
    var total_weight: f32 = 0.0;

    let y1 = max(p0.y - KERNEL_RADIUS, 0);
    let y2 = min(p0.y + KERNEL_RADIUS, size.y - 1);

    for (var y = y1; y <= y2; y = y + 1) {
        let p = vec2<i32>(p0.x, y);
        let r = abs(f32(p0.y - y));
        process_sample(p, r, z0, &total_ao, &total_weight);
    }

    let ao = total_ao / total_weight;
    textureStore(r_output_texture, p0, vec4<f32>(ao, ao, ao, ao));
}
"""

class SSAOBlurPass(RenderSystem):   

    def on_create(self, entity: Entity, components: Component | list[Component]): 
        assert_that(
            (type(components) == RenderExclusiveComponent), 
            f"Only accepted entiy/component in blit stage is {RenderExclusiveComponent}"
        ).is_true()

        self.shader = GpuController().device.create_shader_module(code=SSAO_BLUR_SHADER);  

        self.uniform: wgpu.GPUBuffer = GpuController().device.create_buffer(
            size=((4 * 4)), usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
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
                "storage_texture": {"access": wgpu.StorageTextureAccess.write_only, "format": wgpu.TextureFormat.rgba8unorm},
            }
        ) 
        bind_groups_layout_entries[0].append(
            {
                "binding": 2,
                "visibility": wgpu.ShaderStage.COMPUTE,
                "texture": {  
                    "sample_type": wgpu.TextureSampleType.unfilterable_float,
                    "view_dimension": wgpu.TextureViewDimension.d2,
                },
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
        
        self.bind_group_layouts = [] 
        for layout_entries in bind_groups_layout_entries:
            bind_group_layout = GpuController().device.create_bind_group_layout(entries=layout_entries) 
            self.bind_group_layouts.append(bind_group_layout) 
            
        self.pipeline_layout = GpuController().device.create_pipeline_layout(bind_group_layouts=self.bind_group_layouts)

    def on_prepare(self, entity: Entity, components: Component | list[Component], command_encoder: wgpu.GPUCommandEncoder): 

        cam = Scene().get_primary_cam() 
        cam_comp: CameraComponent = Scene().get_component(cam, CameraComponent) 
        projection = glm.transpose(cam_comp.projection)  

        depth_add_mul = np.ascontiguousarray(glm.vec2(-projection[2][2], projection[3][2]), dtype=np.float32)

        GpuController().device.queue.write_buffer(
            buffer=self.uniform,
            buffer_offset=0,
            data=depth_add_mul,
            data_offset=0,
            size=depth_add_mul.nbytes
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
                "resource": TextureLib().get_texture(name="ssao_blur_gfx").view
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

        # Create the wgou binding objects
        bind_groups = []

        for entries, layouts in zip(bind_groups_entries, self.bind_group_layouts):
            bind_groups.append(
                GpuController().device.create_bind_group(layout=layouts, entries=entries)
            ) 
        self.bind_groups = bind_groups 

        self.blur_x_pipeline = GpuController().device.create_compute_pipeline(
            layout=self.pipeline_layout,
            compute={
                "module": self.shader,
                "entry_point": "blur_x"
            }
        )
        self.blur_y_pipeline = GpuController().device.create_compute_pipeline(
            layout=self.pipeline_layout,
            compute={
                "module": self.shader,
                "entry_point": "blur_y"
            }
        )
    
    def on_render(self, entity: Entity, components: Component | list[Component], render_pass: wgpu.GPURenderPassEncoder | wgpu.GPUComputePassEncoder):   
        
        screen_size = GpuController().render_target_size

        work_group_count_x = np.ceil(screen_size[0] / SSAO_WORK_GROUP_SIZE[0]).astype(int)
        work_group_count_y = np.ceil(screen_size[1] / SSAO_WORK_GROUP_SIZE[1]).astype(int)

        render_pass.set_pipeline(self.blur_x_pipeline) 
        for bind_group_id, bind_group in enumerate(self.bind_groups):
            render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)

        render_pass.dispatch_workgroups(work_group_count_x, work_group_count_y, 1)

        render_pass.set_pipeline(self.blur_y_pipeline) 
        for bind_group_id, bind_group in enumerate(self.bind_groups):
            render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)

        render_pass.dispatch_workgroups(work_group_count_x, work_group_count_y, 1)
