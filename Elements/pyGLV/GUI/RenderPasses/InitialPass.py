from __future__ import annotations
import wgpu   
from assertpy import assert_that

from Elements.pyECSS.wgpu_components import Component, RenderExclusiveComponent
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyGLV.GUI.wgpu_cache_manager import GpuCache

class InitialPass(RenderSystem):  
    def on_create(self, entity: Entity, components: Component | list[Component]):   

        assert_that(
            (type(components) == RenderExclusiveComponent), 
            "Render exclusive component not detected in the Renderer initialization"
        ).is_true() 

        GpuCache().canvas_texture = GpuCache().device.create_texture( 
            label="canvas_texture",
            size=[GpuCache().active_canvas_size[0], GpuCache().active_canvas_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        GpuCache().canvas_texture_view = GpuCache().canvas_texture.create_view() 
        GpuCache().canvas_texture_sampler = GpuCache().device.create_sampler()
        

        GpuCache().canvas_texture_depth = GpuCache().device.create_texture(
            label="canvas_depth_texture",
            size=[GpuCache().active_canvas_size[0], GpuCache().active_canvas_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.depth32float,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        GpuCache().canvas_texture_depth_view = GpuCache().canvas_texture_depth.create_view(
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

        if GpuCache().imported_canvas_size[0] != GpuCache().active_canvas_size[0] and GpuCache().imported_canvas_size[1] != GpuCache().active_canvas_size[1]: 
            GpuCache().active_canvas_size = GpuCache().imported_canvas_size 

            GpuCache().canvas_texture = GpuCache().device.create_texture( 
                label="canvas_texture",
                size=[GpuCache().active_canvas_size[0], GpuCache().active_canvas_size[1], 1],
                mip_level_count=1,
                sample_count=1,
                dimension="2d",
                format=wgpu.TextureFormat.rgba8unorm,
                usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
            ) 
            GpuCache().canvas_texture_view = GpuCache().canvas_texture.create_view()  
            GpuCache().canvas_texture_sampler = GpuCache().device.create_sampler()

            GpuCache().canvas_texture_depth = GpuCache().device.create_texture(
                label="canvas_depth_texture",
                size=[GpuCache().active_canvas_size[0], GpuCache().active_canvas_size[1], 1],
                mip_level_count=1,
                sample_count=1,
                dimension="2d",
                format=wgpu.TextureFormat.depth32float,
                usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
            ) 
            GpuCache().canvas_texture_depth_view = GpuCache().canvas_texture_depth.create_view(
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
 
    def on_render(self, entity: Entity, components: Component | list[Component], render_pass): 
        pass