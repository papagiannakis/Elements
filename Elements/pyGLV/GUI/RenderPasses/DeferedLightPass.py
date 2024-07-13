from __future__ import annotations
import wgpu   
from assertpy import assert_that

from Elements.pyECSS.wgpu_components import * 
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController   
from Elements.pyGLV.GL.wpgu_scene import Scene
from Elements.pyGLV.GL.wgpu_texture import Texture, TextureLib

class DeferedLightPass(RenderSystem):

    def make_bind_group(self, shader:DeferedShaderComponent):
        bind_groups_entries = [[]]

        for name in shader.uniform_buffers.keys(): 
            if len(bind_groups_entries) <= shader.uniform_buffers[name]['group']:
                bind_groups_entries.append([]) 

            bind_groups_entries[shader.uniform_buffers[name]['group']].append({
                "binding": shader.uniform_buffers[name]['binding'], 
                "resource": {
                    "buffer": shader.uniform_gpu_buffers[name],
                    "offset": 0,
                    "size": shader.uniform_buffers[name]['size']
                },
            }) 

        for name in shader.read_only_storage_buffers.keys(): 
            if len(bind_groups_entries) <= shader.read_only_storage_buffers[name]['group']:
                bind_groups_entries.append([]) 

            bind_groups_entries[shader.read_only_storage_buffers[name]['group']].append({
                "binding": shader.read_only_storage_buffers[name]['binding'], 
                "resource": {
                    "buffer": shader.read_only_storage_gpu_buffers[name],
                    "offset": 0,
                    "size": shader.read_only_storage_buffers[name]['size']
                },
            })

        for name in shader.other_uniform.keys():
            if len(bind_groups_entries) <= shader.other_uniform[name]['group']:
                bind_groups_entries.append([])

            bind_groups_entries[shader.other_uniform[name]['group']].append({
                "binding": shader.other_uniform[name]['binding'], 
                "resource": shader.other_uniform[name]['other_resource']
            })

        shader.bind_groups.clear()
        for (entries, bind_group_layout) in zip(bind_groups_entries, shader.bind_group_layouts):
            shader.bind_groups.append(
                GpuController().device.create_bind_group(layout=bind_group_layout, entries=entries)
            )

    def make_pipeline(self, material:MaterialComponent, shader:DeferedShaderComponent):   
        material.pipeline = GpuController().device.create_render_pipeline(
            layout=shader.pipeline_layout,
            vertex={
                "module": shader.shader_vertex_module,
                "entry_point": "vs_main", 
                "buffers": []
            },
            primitive=material.primitive,
            depth_stencil=material.depth_stencil,
            multisample=None,
            fragment={
                "module": shader.shader_fragment_module,
                "entry_point": "fs_main",
                "targets": [
                    {
                        "format": wgpu.TextureFormat.rgba8unorm,
                        "blend": None 
                    }
                ]
            }
        )

    def on_create(self, entity: Entity, components: Component | list[Component]): 
        mesh, material, shader = components 

        assert_that(
            (type(mesh) == MeshComponent) and
            (type(material) == MaterialComponent) and
            (type(shader) == DeferedShaderComponent)
        ).is_true()

    def on_prepare(self, entity: Entity, components: Component | list[Component], command_encoder: wgpu.GPUCommandEncoder):   
        mesh, material, shader = components  

        assert_that(
            (type(mesh) == MeshComponent) and
            (type(material) == MaterialComponent) and
            (type(shader) == DeferedShaderComponent)
        ).is_true() 

        GpuController().set_texture_sampler(
            shader_component=shader,
            sampler_name="g_position_sampler",
            texture_name="g_position_texture",
            texture=TextureLib().get_texture(name="g_position_gfx"),
            texture_only=True
        )
        GpuController().set_texture_sampler(
            shader_component=shader,
            sampler_name="g_normal_sampler",
            texture_name="g_normal_texture",
            texture=TextureLib().get_texture(name="g_normal_gfx"),
            texture_only=True
        )
        GpuController().set_texture_sampler(
            shader_component=shader,
            sampler_name="g_color_sampler",
            texture_name="g_color_texture",
            texture=TextureLib().get_texture(name="g_color_gfx"),
            texture_only=True
        )

        light_link: ShadowAffectionComponent = Scene().get_component(entity, ShadowAffectionComponent) 
        if light_link and light_link.light is not None:
            GpuController().set_texture_sampler(
                shader_component=shader,
                sampler_name="shadow_sampler",
                texture_name="shadow_texture",
                texture=TextureLib().get_texture(name="shadow_depth")
            )
        
    def on_render(self, entity: Entity, components: Component | list[Component], render_pass: wgpu.GPURenderPassEncoder | wgpu.GPUComputePassEncoder): 
        mesh, material, shader = components     
        
        self.make_bind_group(shader) 
        self.make_pipeline(material, shader) 
        
        render_pass.set_pipeline(material.pipeline)
        for bind_group_id, bind_group in enumerate(shader.bind_groups):
            render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99) 

        render_pass.draw(6, 1, 0, 0) 
