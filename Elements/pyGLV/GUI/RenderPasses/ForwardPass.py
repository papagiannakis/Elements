from __future__ import annotations
import wgpu   
from assertpy import assert_that

from Elements.pyECSS.wgpu_components import * 
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController   
from Elements.pyGLV.GL.wpgu_scene import Scene
from Elements.pyGLV.GL.wgpu_texture import Texture, TextureLib

class ForwardRenderPass(RenderSystem):
    """
    Render system for performing a forward rendering pass, which involves rendering
    geometry and shading in a single pass.
    """    

    def make_bind_group(self, shader:ForwardShaderComponent):
        """
        Creates bind groups for the shader based on its uniform buffers, read-only
        storage buffers, and other uniform resources.

        :param shader: The shader component containing the buffers and layouts.
        """

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

    def make_pipeline(self, material:MaterialComponent, shader:ForwardShaderComponent):
        """
        Creates a render pipeline for the material using the given shader.

        :param material: The material component containing pipeline configuration.
        :param shader: The shader component containing the shader modules and layouts.
        """        

        material.pipeline = GpuController().device.create_render_pipeline(
            layout=shader.pipeline_layout,
            vertex={
                "module": shader.shader_module,
                "entry_point": "vs_main", 
                "buffers": shader.attributes_layout 
            },
            primitive=material.primitive,
            depth_stencil=material.depth_stencil,
            multisample=None,
            fragment={
                "module": shader.shader_module,
                "entry_point": "fs_main",
                "targets": [
                    {
                        "format": wgpu.TextureFormat.rgba8unorm,
                        "blend": material.color_blend 
                    }
                ]
            }
        )

    def on_create(self, entity: Entity, components: Component | list[Component]):
        """
        Called when the render system is created. Ensures the correct components are provided.

        :param entity: The entity associated with this render system.
        :param components: The components associated with this render system.
        """

        mesh, material, shader = components 

        assert_that(
            (type(mesh) == MeshComponent) and
            (type(material) == MaterialComponent) and
            (type(shader) == ForwardShaderComponent)
        ).is_true()

    def on_prepare(self, entity: Entity, components: Component | list[Component], command_encoder: wgpu.GPUCommandEncoder):   
        """
        Called before rendering to prepare the resources and pipeline state.

        :param entity: The entity associated with this render system.
        :param components: The components associated with this render system.
        :param command_encoder: The command encoder to record commands.
        """

        mesh, material, shader = components  

        assert_that(
            (type(mesh) == MeshComponent) and
            (type(material) == MaterialComponent) and
            (type(shader) == ForwardShaderComponent)
        ).is_true() 

        light_link: ShadowAffectionComponent = Scene().get_component(entity, ShadowAffectionComponent) 

        if light_link and light_link.light is not None:
            GpuController().set_texture_sampler(
                shader_component=shader,
                sampler_name="shadow_sampler",
                texture_name="shadow_texture",
                texture=TextureLib().get_texture(name="shadow_depth")
            )
        
    def on_render(self, entity: Entity, components: Component | list[Component], render_pass: wgpu.GPURenderPassEncoder | wgpu.GPUComputePassEncoder): 
        """
        Called during rendering to execute the forward rendering pass.

        :param entity: The entity associated with this render system.
        :param components: The components associated with this render system.
        :param render_pass: The render pass encoder to record rendering commands.
        """

        mesh, material, shader = components   

        self.make_bind_group(shader) 
        self.make_pipeline(material, shader) 

        # print("stage: forward pass")

        render_pass.set_pipeline(material.pipeline)
        render_pass.set_index_buffer(mesh.buffer_map[MeshComponent.Buffers.INDEX.value], wgpu.IndexFormat.uint32) 
        for name, attr in shader.attributes.items():
            render_pass.set_vertex_buffer(slot=attr['slot'], buffer=mesh.buffer_map[name])
        for bind_group_id, bind_group in enumerate(shader.bind_groups):
            render_pass.set_bind_group(bind_group_id, bind_group, [], 0, 99)
        render_pass.draw_indexed(mesh.indices_num, 1, 0, 0, 0) 
