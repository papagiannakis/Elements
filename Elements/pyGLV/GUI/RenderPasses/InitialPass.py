from __future__ import annotations
import wgpu   
from assertpy import assert_that

from Elements.pyECSS.wgpu_components import Component, RenderExclusiveComponent
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController

class InitialPass(RenderSystem):  
    def on_create(self, entity: Entity, components: Component | list[Component]):   

        assert_that(
            (type(components) == RenderExclusiveComponent), 
            "Render exclusive component not detected in the Renderer initialization"
        ).is_true() 

        GpuController().canvas_texture = GpuController().device.create_texture( 
            label="canvas_texture",
            size=[GpuController().active_canvas_size[0], GpuController().active_canvas_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        GpuController().canvas_texture_view = GpuController().canvas_texture.create_view() 
        GpuController().canvas_texture_sampler = GpuController().device.create_sampler()
        

        GpuController().canvas_texture_depth = GpuController().device.create_texture(
            label="canvas_depth_texture",
            size=[GpuController().active_canvas_size[0], GpuController().active_canvas_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.depth32float,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        GpuController().canvas_texture_depth_view = GpuController().canvas_texture_depth.create_view(
            label="canvas_depth_texture_view",
            format=wgpu.TextureFormat.depth32float,
            dimension="2d",
            aspect=wgpu.TextureAspect.depth_only,
            base_mip_level=0,
            mip_level_count=1,
            base_array_layer=0,
            array_layer_count=1,
        )

    def on_prepare(self, entity: Entity, components: Component | list[Component], command_encoder: wgpu.GPUCommandEncoder): 

        assert_that(
            (type(components) == RenderExclusiveComponent), 
            "Render exclusive component not detected in the Renderer initialization"
        ).is_true()

        if GpuController().imported_canvas_size[0] != GpuController().active_canvas_size[0] and GpuController().imported_canvas_size[1] != GpuController().active_canvas_size[1]: 
            GpuController().active_canvas_size = GpuController().imported_canvas_size   

            print(f"Canvas resized to width: {GpuController().active_canvas_size[0]} and height: {GpuController().active_canvas_size[1]}")

            GpuController().canvas_texture = GpuController().device.create_texture( 
                label="canvas_texture",
                size=[GpuController().active_canvas_size[0], GpuController().active_canvas_size[1], 1],
                mip_level_count=1,
                sample_count=1,
                dimension="2d",
                format=wgpu.TextureFormat.rgba8unorm,
                usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
            ) 
            GpuController().canvas_texture_view = GpuController().canvas_texture.create_view()  
            GpuController().canvas_texture_sampler = GpuController().device.create_sampler()

            GpuController().canvas_texture_depth = GpuController().device.create_texture(
                label="canvas_depth_texture",
                size=[GpuController().active_canvas_size[0], GpuController().active_canvas_size[1], 1],
                mip_level_count=1,
                sample_count=1,
                dimension="2d",
                format=wgpu.TextureFormat.depth32float,
                usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
            ) 
            GpuController().canvas_texture_depth_view = GpuController().canvas_texture_depth.create_view(
                label="canvas_depth_texture_view",
                format=wgpu.TextureFormat.depth32float,
                dimension="2d",
                aspect=wgpu.TextureAspect.depth_only,
                base_mip_level=0,
                mip_level_count=1,
                base_array_layer=0,
                array_layer_count=1,
            )  

        else: 
            return
 
    def on_render(self, entity: Entity, components: Component | list[Component], render_pass:wgpu.GPURenderPassEncoder): 
        pass