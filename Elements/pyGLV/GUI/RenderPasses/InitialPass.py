from __future__ import annotations
import wgpu   
from assertpy import assert_that

from Elements.pyECSS.wgpu_components import Component, RenderExclusiveComponent
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController
from Elements.pyGLV.GL.wgpu_texture import Texture, TextureLib

class InitialPass(RenderSystem):  
    def on_create(self, entity: Entity, components: Component | list[Component]):   

        assert_that(
            (type(components) == RenderExclusiveComponent), 
            "Render exclusive component not detected in the Renderer initialization"
        ).is_true() 

        canvas_texture: wgpu.GPUTexture = GpuController().device.create_texture( 
            label="canvas_texture",
            size=[GpuController().render_target_size[0], GpuController().render_target_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        canvas_texture_view: wgpu.GPUTextureView = canvas_texture.create_view() 
        canvas_texture_sampler: wgpu.GPUSampler = GpuController().device.create_sampler()
        

        canvas_texture_depth: wgpu.GPUTexture = GpuController().device.create_texture(
            label="canvas_depth_texture",
            size=[GpuController().render_target_size[0], GpuController().render_target_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.depth32float,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        canvas_texture_depth_view: wgpu.GPUTextureView = canvas_texture_depth.create_view(
            label="canvas_depth_texture_view",
            format=wgpu.TextureFormat.depth32float,
            dimension="2d",
            aspect=wgpu.TextureAspect.depth_only,
            base_mip_level=0,
            mip_level_count=1,
            base_array_layer=0,
            array_layer_count=1,
        ) 
        canvas_texture_depth_sampler: wgpu.GPUSampler = GpuController().device.create_sampler() 

        TextureLib().append_texture(name="render_target", texture=Texture(
            texture=canvas_texture,
            view=canvas_texture_view,
            sampler=canvas_texture_sampler,
            width=GpuController().render_target_size[0],
            height=GpuController().render_target_size[1]
        )) 
        TextureLib().append_texture(name="render_target_depth", texture=Texture(
            texture=canvas_texture_depth,
            view=canvas_texture_depth_view,
            sampler=canvas_texture_depth_sampler,
            width=GpuController().render_target_size[0],
            height=GpuController().render_target_size[1]
        )) 

    def on_prepare(self, entity: Entity, components: Component | list[Component], command_encoder: wgpu.GPUCommandEncoder): 

        assert_that(
            (type(components) == RenderExclusiveComponent), 
            "Render exclusive component not detected in the Renderer initialization"
        ).is_true()

        target: Texture = TextureLib().get_texture(name="render_target") 
        target_depth: Texture = TextureLib().get_texture(name="render_target_depth")

        if GpuController().render_target_size[0] != target.width and GpuController().render_target_size[1] != target.height:
            print(f"Render target resized to width: {target.width} -> {GpuController().render_target_size[0]} and height: {target.height} -> {GpuController().render_target_size[1]}")

            target.texture = GpuController().device.create_texture( 
                label="canvas_texture",
                size=[GpuController().render_target_size[0], GpuController().render_target_size[1], 1],
                mip_level_count=1,
                sample_count=1,
                dimension="2d",
                format=wgpu.TextureFormat.rgba8unorm,
                usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
            ) 
            target.view = target.texture.create_view()
            TextureLib().append_texture(name="render_target", texture=Texture(
                texture=target.texture,
                view=target.view,
                sampler=target.sampler, 
                width=GpuController().render_target_size[0],
                height=GpuController().render_target_size[1]
            ))

            target_depth.texture = GpuController().device.create_texture(
                label="canvas_depth_texture",
                size=[GpuController().render_target_size[0], GpuController().render_target_size[1], 1],
                mip_level_count=1,
                sample_count=1,
                dimension="2d",
                format=wgpu.TextureFormat.depth32float,
                usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
            ) 
            target_depth.view = target_depth.texture.create_view(
                label="canvas_depth_texture_view",
                format=wgpu.TextureFormat.depth32float,
                dimension="2d",
                aspect=wgpu.TextureAspect.depth_only,
                base_mip_level=0,
                mip_level_count=1,
                base_array_layer=0,
                array_layer_count=1,
            )
            TextureLib().append_texture(name="render_target_depth", texture=Texture(
                texture=target_depth.texture,
                view=target_depth.view,
                sampler=target_depth.sampler, 
                width=GpuController().render_target_size[0],
                height=GpuController().render_target_size[1]
            )) 

        else: 
            return
 
    def on_render(self, entity: Entity, components: Component | list[Component], render_pass:wgpu.GPURenderPassEncoder): 
        pass