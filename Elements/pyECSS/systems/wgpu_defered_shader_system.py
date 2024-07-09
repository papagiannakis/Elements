from __future__ import annotations 

from Elements.pyECSS.wgpu_system import System 
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyECSS.wgpu_components import * 
from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController 
from Elements.pyGLV.GL.wgpu_shader_types import *

import glm  
import re 
import wgpu 
import sys  
from assertpy import assert_that

VERTEX_SHADER_CODE = """ 
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
""" 

class ForwardShaderSystem(System): 

    def ShaderLoader(self, file):
        try:
            f = open(file, 'r')
        except OSError:
            print ("Could not open/read fragment shader file:", file)
            sys.exit()
        with f:
            return f.read() 

    # add the length of each member
    def parse_buffer(self, buffer_type: str, shader_code):
        pattern = re.compile(r"@group\((\d+)\) @binding\((\d+)\) var" + re.escape(buffer_type) + r" (\w+):\s*(\w+(?:\<.*?\>)?);")
        matches = pattern.findall(shader_code)

        buffers = {}
        buffer_members = {}
        member_offset = 0
        for match in matches:
            group, binding, name, type = match
            struct_pattern = r"struct " + re.escape(type) + r" \{([^}]*)\}"
            struct_match = re.search(struct_pattern, shader_code)
            if struct_match: 
                member_offset = 0
                buffer_members.clear()
                struct_body = struct_match.group(1)
                member_pattern = r"(\w+)\s*:\s*(\w+(?:\<.*?\>)?)"
                members = re.findall(member_pattern, struct_body)
                for member in members:  
                    buffer_members.update({member[0]: {
                            'type': member[1], 
                            'slot': member_offset
                        }
                    })  
                    member_offset += SHADER_TYPES[member[1]]

            buffers.update({ name: {
                    'group': int(group),
                    'binding': int(binding),
                    'type': type, 
                    'size': member_offset,
                    'members': buffer_members,
                    'other_resource': None
                }
            })

        return buffers

    def make_gpu_uniform_buffers(self, gpu_buffer_map:dict, buffer_map:dict):
        for key, buffer in buffer_map.items(): 
            gpu_buffer_map.update({
                key: GpuController().device.create_buffer(
                    size=buffer['size'], usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
                )
            }) 

    def make_gpu_read_only_storage_buffers(self, gpu_buffer_map:dict, buffer_map:dict):
        for key, buffer in buffer_map.items(): 
            gpu_buffer_map.update({
                key: GpuController().device.create_buffer(
                    size=buffer['size'], usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST
                )
            })
 
    def on_create(self, entity: Entity, components: Component | list[Component]): 
        shader = components 

        assert_that(type(shader) == DeferedShaderComponent).is_true()

        shader.shader_fragment_code = self.ShaderLoader(shader.shader_fragment_code)
        shader.shader_fragment_module = GpuController().device.create_shader_module(code=shader.shader_fragment_code) 
        shader.shader_vertex_module = GpuController().device.create_shader_module(code=VERTEX_SHADER_CODE)

        shader.uniform_buffers = self.parse_buffer('<uniform>', shader.shader_fragment_code) 
        shader.read_only_storage_buffers = self.parse_buffer('<storage, read>', shader.shader_fragment_code) 
        shader.other_uniform = self.parse_buffer('', shader.shader_fragment_code) 

        self.make_gpu_uniform_buffers(shader.uniform_gpu_buffers, shader.uniform_buffers)
        self.make_gpu_read_only_storage_buffers(shader.read_only_storage_gpu_buffers, shader.read_only_storage_buffers)

        bind_groups_layout_entries = [[]]
        for name in shader.uniform_buffers.keys(): 
            if len(bind_groups_layout_entries) <= shader.uniform_buffers[name]['group']:
                bind_groups_layout_entries.append([]) 

            bind_groups_layout_entries[shader.uniform_buffers[name]['group']].append({
                "binding": shader.uniform_buffers[name]['binding'],
                "visibility": wgpu.ShaderStage.VERTEX | wgpu.ShaderStage.FRAGMENT,
                "buffer": {
                    "type": wgpu.BufferBindingType.uniform
                },
            }) 

        for name in shader.read_only_storage_buffers.keys(): 
            if len(bind_groups_layout_entries) <= shader.read_only_storage_buffers[name]['group']:
                bind_groups_layout_entries.append([]) 

            bind_groups_layout_entries[shader.read_only_storage_buffers[name]['group']].append({
                "binding": shader.read_only_storage_buffers[name]['binding'],
                "visibility": wgpu.ShaderStage.VERTEX | wgpu.ShaderStage.FRAGMENT,
                "buffer": {
                    "type": wgpu.BufferBindingType.read_only_storage
                },
            })

        for name in shader.other_uniform.keys():
            if len(bind_groups_layout_entries) <= shader.other_uniform[name]['group']:
                bind_groups_layout_entries.append([])

            if shader.other_uniform[name]['type'] == 'texture_2d<f32>':
                bind_groups_layout_entries[shader.other_uniform[name]['group']].append({
                    "binding": shader.other_uniform[name]['binding'],
                    "visibility": wgpu.ShaderStage.FRAGMENT,
                    "texture": {  
                        "sample_type": wgpu.TextureSampleType.float,
                        "view_dimension": wgpu.TextureViewDimension.d2,
                    }
                }) 

            elif shader.other_uniform[name]['type'] == 'texture_depth_2d':
                bind_groups_layout_entries[shader.other_uniform[name]['group']].append({
                    "binding": shader.other_uniform[name]['binding'],
                    "visibility": wgpu.ShaderStage.FRAGMENT,
                    "texture": {  
                        "sample_type": wgpu.TextureSampleType.depth,
                        "view_dimension": wgpu.TextureViewDimension.d2,
                    }
                })

            elif shader.other_uniform[name]['type'] == 'texture_cube<f32>':
                bind_groups_layout_entries[shader.other_uniform[name]['group']].append({
                    "binding": shader.other_uniform[name]['binding'],
                    "visibility": wgpu.ShaderStage.FRAGMENT,
                    "texture": {  
                        "sample_type": wgpu.TextureSampleType.cube,
                        "view_dimension": wgpu.TextureViewDimension.d2,
                    }
                })

            elif shader.other_uniform[name]['type'] == 'sampler':
                bind_groups_layout_entries[shader.other_uniform[name]['group']].append({
                        "binding": shader.other_uniform[name]['binding'],
                        "visibility": wgpu.ShaderStage.FRAGMENT,
                        "sampler": {
                            "type": wgpu.SamplerBindingType.filtering
                        },
                }) 

            elif shader.other_uniform[name]['type'] == 'sampler_comparison':
                bind_groups_layout_entries[shader.other_uniform[name]['group']].append({
                        "binding": shader.other_uniform[name]['binding'],
                        "visibility": wgpu.ShaderStage.FRAGMENT,
                        "sampler": {
                            "type": wgpu.SamplerBindingType.comparison
                        },
                }) 
        
        shader.bind_group_layouts = []
        for layout_entries in bind_groups_layout_entries:
            shader.bind_group_layouts.append(GpuController().device.create_bind_group_layout(entries=layout_entries)) 

        shader.pipeline_layout = GpuController().device.create_pipeline_layout(
            bind_group_layouts=shader.bind_group_layouts
        )
 
    def on_update(self, ts, entity: Entity, components: Component | list[Component], event): 
        pass;