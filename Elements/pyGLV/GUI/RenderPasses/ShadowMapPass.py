from __future__ import annotations
import wgpu
import glm 
import numpy as np
from assertpy import assert_that

from Elements.pyECSS.wgpu_components import Component, LightComponent, MeshComponent, LightAffectionComponent, CameraComponent, TransformComponent, InfoComponent
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController 
from Elements.pyGLV.GL.wgpu_texture import TextureLib, Texture
from Elements.pyGLV.GL.wpgu_scene import Scene

SHADER_CODE = """ 
struct uniforms {
    projection: mat4x4f, 
    view: mat4x4f,
    model: mat4x4f
};

@group(0) @binding(0) var<uniform> ubuffer: uniforms; 

struct VertexInput {
    @location(0) a_vertices: vec3f, 
}
struct VertexOutput {
    @builtin(position) Position: vec4<f32>,
}; 
struct FragmentOutput { 
    @builtin(frag_depth) depth: f32,
    @location(0) color: vec4f,
};

@vertex
fn vs_main( 
    in: VertexInput
) -> VertexOutput {

    var model = transpose(ubuffer.model);
    var view = transpose(ubuffer.view); 
    var projection = transpose(ubuffer.projection);

    var out: VertexOutput; 
    out.Position = projection * view * model * vec4<f32>(in.a_vertices, 1.0);  
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
) -> FragmentOutput { 
    var out: FragmentOutput; 

    out.depth = LinearizeDepth(in.Position.z, 0.01, 500.0); 
    out.color = vec4f(out.depth, out.depth, out.depth, 1.0);
    return out;
}
"""

class ShadowMapPass(RenderSystem):
    def __init__(self, filters: list[type]):
        super().__init__(filters) 
        self.shader = None
    
    def on_create(self, entity: Entity, components: Component | list[Component]):
        # assert_that(type(components) == SkyboxComponent).is_true()
        # skybox: SkyboxComponent = components  
        assert_that(
            type(components[0]) == LightAffectionComponent and
            type(components[1]) == MeshComponent and 
            type(components[2]) == TransformComponent 
        ).is_true() 

        light_cache: LightAffectionComponent = components[0]
         
        # WGSL example   
        if self.shader is None:
            self.shader = GpuController().device.create_shader_module(code=SHADER_CODE);
        
        light_cache.uniform_gpu_buffer = GpuController().device.create_buffer(
            size=((16 * 4) + (16 * 4) + (16 * 4)), usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
        )
        
        bind_groups_layout_entries = [[]]
        bind_groups_layout_entries[0].append(
            {
                "binding": 0,
                "visibility": wgpu.ShaderStage.VERTEX | wgpu.ShaderStage.FRAGMENT,
                "buffer": {"type": wgpu.BufferBindingType.uniform},
            }
        )  
        
        self.bind_group_layouts = [] 
        for layout_entries in bind_groups_layout_entries:
            bind_group_layout = GpuController().device.create_bind_group_layout(entries=layout_entries) 
            self.bind_group_layouts.append(bind_group_layout) 
            
        self.pipeline_layout = GpuController().device.create_pipeline_layout(bind_group_layouts=self.bind_group_layouts)

    def on_prepare(self, entity: Entity, components: Component | list[Component], command_encoder: wgpu.GPUCommandEncoder):
        assert_that(
            type(components[0]) == LightAffectionComponent and
            type(components[1]) == MeshComponent and 
            type(components[2]) == TransformComponent 
        ).is_true()    
        cam:Entity = Scene().get_primary_cam()
        
        lightAffected: LightAffectionComponent = components[0] 
        mesh: MeshComponent = components[1] 
        transform: TransformComponent = components[2] 
        
        light: Entity = lightAffected.light
        light_comp:LightComponent = Scene().get_component(light, LightComponent)  
        light_cam:CameraComponent = Scene().get_component(light, CameraComponent)
        
        light_view = light_cam.view 
        light_proj = light_cam.projection 
        model = transform.world_matrix 
        
        light_view_data = np.ascontiguousarray(light_view, dtype=np.float32) 
        light_proj_data = np.ascontiguousarray(light_proj, dtype=np.float32) 
        model_data = np.ascontiguousarray(model, dtype=np.float32)
        
        GpuController().device.queue.write_buffer(
            buffer=lightAffected.uniform_gpu_buffer,
            buffer_offset=0,
            data=light_proj_data,
            data_offset=0,
            size=light_proj_data.nbytes
        )
        GpuController().device.queue.write_buffer(
            buffer=lightAffected.uniform_gpu_buffer,
            buffer_offset=64,
            data=light_view_data,
            data_offset=0,
            size=light_view_data.nbytes
        ) 
        GpuController().device.queue.write_buffer(
            buffer=lightAffected.uniform_gpu_buffer,
            buffer_offset=128,
            data=model_data,
            data_offset=0,
            size=model_data.nbytes
        )  

        bind_groups_entries = [[]]
        bind_groups_entries[0].append(
            {
                "binding": 0,
                "resource": {
                    "buffer": lightAffected.uniform_gpu_buffer,
                    "offset": 0,
                    "size": lightAffected.uniform_gpu_buffer.size,
                },
            }
        )

        # Create the wgou binding objects
        bind_groups = []

        for entries, layouts in zip(bind_groups_entries, self.bind_group_layouts):
            bind_groups.append(
                GpuController().device.create_bind_group(layout=layouts, entries=entries)
            ) 

        lightAffected.bind_groups = bind_groups
        lightAffected.render_pipeline = GpuController().device.create_render_pipeline(
            layout=self.pipeline_layout,
            vertex={
                "module": self.shader,
                "entry_point": "vs_main", 
                "buffers": [ 
                    {
                        "array_stride": 4 * 3, 
                        "step_mode": wgpu.VertexStepMode.vertex,
                        "attributes": [
                            {
                                "format": wgpu.VertexFormat.float32x3,
                                "offset": 0,
                                "shader_location": 0 
                            },
                        ],
                    } 
                ], 
            },
            primitive={
                "topology": wgpu.PrimitiveTopology.triangle_list,
                "front_face": wgpu.FrontFace.ccw,
                "cull_mode": wgpu.CullMode.front,
            },
            depth_stencil={ 
                "format": wgpu.TextureFormat.depth32float,
                "depth_write_enabled": True,
                "depth_compare": wgpu.CompareFunction.less,
            },            
            multisample=None,
            fragment={
                "module": self.shader,
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
    
    def on_render(self, entity: Entity, components: Component | list[Component], render_pass: wgpu.GPURenderPassEncoder): 
        assert_that(
            type(components[0]) == LightAffectionComponent and
            type(components[1]) == MeshComponent and 
            type(components[2]) == TransformComponent 
        ).is_true()   

        lightAffected: LightAffectionComponent = components[0] 
        mesh: MeshComponent = components[1] 
        
        render_pass.set_pipeline(lightAffected.render_pipeline) 
        render_pass.set_index_buffer(mesh.buffer_map[MeshComponent.Buffers.INDEX.value], wgpu.IndexFormat.uint32) 
        render_pass.set_vertex_buffer(slot=0, buffer=mesh.buffer_map[MeshComponent.Buffers.VERTEX.value])
        for bind_group_id, bind_group in enumerate(lightAffected.bind_groups):
            render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)

        render_pass.draw_indexed(mesh.indices_num, 1, 0, 0) 