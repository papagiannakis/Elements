from __future__ import annotations
import wgpu 
import glm   
import numpy as np
from assertpy import assert_that

from Elements.pyECSS.wgpu_components import *
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController 
from Elements.pyGLV.GL.wgpu_texture import TextureLib, Texture
from Elements.pyGLV.GL.wpgu_scene import Scene

GEOMETRY_SHADER = """
struct Uniforms {
    projection: mat4x4f, 
    view: mat4x4f,
    model: mat4x4f,
    near_far: vec2f
};
struct VertexInput {
    @location(0) a_vertices: vec3f,
    @location(1) a_normals: vec3f,
    @location(2) a_uvs: vec2f
};
struct VertexOutput {
    @builtin(position) Position: vec4f,
    @location(0) pos:   vec4f,
    @location(1) uv:    vec2f,
    @location(2) normal: vec3f
};
struct FragOutput { 
    @builtin(frag_depth) depth: f32,
    @location(0) gPosition: vec4f,
    @location(1) gNornal: vec4f,
    @location(2) gColor: vec4f
}; 

@group(0) @binding(0) var<uniform> ubuffer: Uniforms;
@group(0) @binding(1) var diffuse_texture: texture_2d<f32>;
@group(0) @binding(2) var diffuse_sampler: sampler;

fn LinearizeDepth( 
    depth: f32,
    near: f32,
    far: f32,
) -> f32 {   

    let zNdc = 2 * depth - 1; 
    let zEye = (2 * far * near) / ((far + near) - zNdc * (far - near)); 
    let linearDepth = (zEye - near) / (far - near);
    return linearDepth;
}

@vertex 
fn vs_main( 
    in: VertexInput
) -> VertexOutput { 
    let projection = transpose(ubuffer.projection);
    let view = transpose(ubuffer.view);
    let model = transpose(ubuffer.model);

    var out: VertexOutput;
    out.Position = projection * view * model * vec4f(in.a_vertices, 1.0);
    out.pos = model * vec4f(in.a_vertices, 1.0);
    out.uv = in.a_uvs;
    out.normal = in.a_normals;
    return out;
}

@fragment
fn fs_main(
    in: VertexOutput 
) -> FragOutput {    
    var near = ubuffer.near_far.x;
    var far = ubuffer.near_far.y;

    var out: FragOutput;
    
    out.depth = in.Position.z; 
    out.gPosition = vec4f(in.pos);
    out.gNornal = vec4f(in.normal.xyz, LinearizeDepth(in.Position.z, near, far));
    out.gColor = vec4f(textureSample(diffuse_texture, diffuse_sampler, in.uv).rgb, 1.0);
    return out;
}
"""

class DeferedGeometryPass(RenderSystem): 

    def on_create(self, entity: Entity, components: Component | list[Component]):
        shader, mesh, transform = components 

        assert_that( 
            type(shader) == DeferedShaderComponent and
            type(mesh) == MeshComponent and
            type(transform) == TransformComponent
        ).is_true()

        self.shader_module = GpuController().device.create_shader_module(code=GEOMETRY_SHADER);  

        shader.g_uniform_buffer = GpuController().device.create_buffer(
            size=((16 * 4) + (16 * 4) + (16 * 4) + (4 * 4)), usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
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
                "visibility": wgpu.ShaderStage.FRAGMENT,
                "texture": {  
                    "sample_type": wgpu.TextureSampleType.float,
                    "view_dimension": wgpu.TextureViewDimension.d2,
                },
            }
        )
        bind_groups_layout_entries[0].append(
            {
                "binding": 2,
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
        shader, mesh, transform = components 

        assert_that( 
            type(shader) == DeferedShaderComponent and
            type(mesh) == MeshComponent and
            type(transform) == TransformComponent
        ).is_true() 

        cam: Entity = Scene().get_primary_cam() 
        cam_comp: CameraComponent = Scene().get_component(cam, CameraComponent)
        mesh_trans: TransformComponent = Scene().get_component(entity, TransformComponent)
        diffuse = TextureLib().get_texture(name=shader.diffuse_texture) 

        projection = np.ascontiguousarray(cam_comp.projection, dtype=np.float32) 
        view = np.ascontiguousarray(cam_comp.view, dtype=np.float32) 
        model = np.ascontiguousarray(mesh_trans.world_matrix, dtype=np.float32) 
        near_far = glm.vec2(cam_comp.near, cam_comp.far) 
        near_far_data = np.ascontiguousarray(near_far, dtype=np.float32)

        GpuController().device.queue.write_buffer(
            buffer=shader.g_uniform_buffer,
            buffer_offset=0,
            data=projection,
            data_offset=0,
            size=projection.nbytes
        )
        GpuController().device.queue.write_buffer(
            buffer=shader.g_uniform_buffer,
            buffer_offset=64,
            data=view,
            data_offset=0,
            size=view.nbytes
        )
        GpuController().device.queue.write_buffer(
            buffer=shader.g_uniform_buffer,
            buffer_offset=128,
            data=model,
            data_offset=0,
            size=model.nbytes
        )
        GpuController().device.queue.write_buffer(
            buffer=shader.g_uniform_buffer,
            buffer_offset=192,
            data=near_far_data,
            data_offset=0,
            size=near_far_data.nbytes
        )

        # We always have two bind groups, so we can play distributing our
        # resources over these two groups in different configurations.
        bind_groups_entries = [[]]
        bind_groups_entries[0].append(
            {
                "binding": 0,
                "resource": {
                    "buffer": shader.g_uniform_buffer,
                    "offset": 0,
                    "size": shader.g_uniform_buffer.size,
                },
            }
        )
        bind_groups_entries[0].append(
            {
                "binding": 1,
                "resource": diffuse.view
            } 
        ) 

        bind_groups_entries[0].append(
            {
                "binding": 2, 
                "resource": diffuse.sampler
            }
        )

        # Create the wgou binding objects
        bind_groups = []

        for entries, layouts in zip(bind_groups_entries, self.bind_group_layouts):
            bind_groups.append(
                GpuController().device.create_bind_group(layout=layouts, entries=entries)
            ) 
        shader.g_bind_group = bind_groups

        shader.g_pipeline = GpuController().device.create_render_pipeline(
            layout=self.pipeline_layout,
            vertex={
                "module": self.shader_module,
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
                    },
                    {
                        "array_stride": 4 * 3, 
                        "step_mode": wgpu.VertexStepMode.vertex,
                        "attributes": [
                            {
                                "format": wgpu.VertexFormat.float32x3,
                                "offset": 0,
                                "shader_location": 1 
                            },
                        ],
                    },
                    {
                        "array_stride": 4 * 2,
                        "step_mode": wgpu.VertexStepMode.vertex,
                        "attributes": [
                            {
                                "format": wgpu.VertexFormat.float32x2,
                                "offset": 0,
                                "shader_location": 2
                            },
                        ],
                    } 
                ], 
            },
            primitive={
                "topology": wgpu.PrimitiveTopology.triangle_list,
                "front_face": wgpu.FrontFace.ccw,
                "cull_mode": wgpu.CullMode.none,
            },
            depth_stencil={
                "format": wgpu.TextureFormat.depth32float,
                "depth_write_enabled": True,
                "depth_compare": wgpu.CompareFunction.less,
            },            
            multisample=None,
            fragment={
                "module": self.shader_module,
                "entry_point": "fs_main",
                "targets": [
                    {
                        "format": wgpu.TextureFormat.rgba32float,
                        "blend": None
                    },
                    {
                        "format": wgpu.TextureFormat.rgba32float,
                        "blend": None
                    },
                    {
                        "format": wgpu.TextureFormat.rgba32float,
                        "blend": None
                    }
                ],
            },
        )
    
    def on_render(self, entity: Entity, components: Component | list[Component], render_pass:wgpu.GPURenderPassEncoder):   
        shader, mesh, transform = components 

        assert_that( 
            type(shader) == DeferedShaderComponent and
            type(mesh) == MeshComponent and
            type(transform) == TransformComponent
        ).is_true()

        render_pass.set_pipeline(shader.g_pipeline) 
        render_pass.set_index_buffer(mesh.buffer_map[MeshComponent.Buffers.INDEX.value], wgpu.IndexFormat.uint32) 
        render_pass.set_vertex_buffer(slot=0, buffer=mesh.buffer_map[MeshComponent.Buffers.VERTEX.value]) 
        render_pass.set_vertex_buffer(slot=1, buffer=mesh.buffer_map[MeshComponent.Buffers.NORMAL.value]) 
        render_pass.set_vertex_buffer(slot=2, buffer=mesh.buffer_map[MeshComponent.Buffers.UV.value]) 
        for bind_group_id, bind_group in enumerate(shader.g_bind_group):
            render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)

        render_pass.draw_indexed(mesh.indices_num, 1, 0, 0, 0) 

