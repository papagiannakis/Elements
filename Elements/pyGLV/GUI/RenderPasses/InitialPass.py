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

        self.render_size = GpuController().render_target_size

        g_position_gfx: wgpu.GPUTexture = GpuController().device.create_texture( 
            label="canvas_texture",
            size=[self.render_size[0], self.render_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        g_position_gfx_view: wgpu.GPUTextureView = g_position_gfx.create_view() 
        g_position_gfx_sampler: wgpu.GPUSampler = GpuController().device.create_sampler(
            min_filter=wgpu.FilterMode.linear,
            mag_filter=wgpu.FilterMode.linear,
            mipmap_filter=wgpu.FilterMode.nearest
        )

        g_normal_gfx: wgpu.GPUTexture = GpuController().device.create_texture( 
            label="canvas_texture",
            size=[self.render_size[0], self.render_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        g_normal_gfx_view: wgpu.GPUTextureView = g_normal_gfx.create_view() 
        g_normal_gfx_sampler: wgpu.GPUSampler = GpuController().device.create_sampler(
            min_filter=wgpu.FilterMode.linear,
            mag_filter=wgpu.FilterMode.linear,
            mipmap_filter=wgpu.FilterMode.nearest
        )

        g_color_gfx: wgpu.GPUTexture = GpuController().device.create_texture( 
            label="canvas_texture",
            size=[self.render_size[0], self.render_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        g_color_gfx_view: wgpu.GPUTextureView = g_color_gfx.create_view() 
        g_color_gfx_sampler: wgpu.GPUSampler = GpuController().device.create_sampler(
            min_filter=wgpu.FilterMode.linear,
            mag_filter=wgpu.FilterMode.linear,
            mipmap_filter=wgpu.FilterMode.nearest
        )

        fxaa_gfx: wgpu.GPUTexture = GpuController().device.create_texture( 
            label="canvas_texture",
            size=[self.render_size[0], self.render_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        fxaa_gfx_view: wgpu.GPUTextureView = fxaa_gfx.create_view() 
        fxaa_gfx_sampler: wgpu.GPUSampler = GpuController().device.create_sampler()

        world_gfx: wgpu.GPUTexture = GpuController().device.create_texture( 
            label="canvas_texture",
            size=[self.render_size[0], self.render_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        world_gfx_view: wgpu.GPUTextureView = world_gfx.create_view() 
        world_gfx_sampler: wgpu.GPUSampler = GpuController().device.create_sampler(
            min_filter=wgpu.FilterMode.linear,
            mag_filter=wgpu.FilterMode.linear,
            mipmap_filter=wgpu.FilterMode.linear
        )

        world_depth: wgpu.GPUTexture = GpuController().device.create_texture(
            label="canvas_depth_texture",
            size=[self.render_size[0], self.render_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.depth32float,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        world_depth_view: wgpu.GPUTextureView = world_depth.create_view(
            label="canvas_depth_texture_view",
            format=wgpu.TextureFormat.depth32float,
            dimension="2d",
            aspect=wgpu.TextureAspect.depth_only,
            base_mip_level=0,
            mip_level_count=1,
            base_array_layer=0,
            array_layer_count=1,
        ) 
        world_depth_sampler: wgpu.GPUSampler = GpuController().device.create_sampler()
       
        shadow_gfx: wgpu.GPUTexture = GpuController().device.create_texture(
            label="shadow_texture",
            size=[2048, 2048, 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        shadow_gfx_view: wgpu.GPUTextureView = shadow_gfx.create_view() 
        shadow_gfx_sampler: wgpu.GPUSampler = GpuController().device.create_sampler()
        
        shadow_depth: wgpu.GPUTexture = GpuController().device.create_texture(
            label="shadow_texture",
            size=[2048, 2048, 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.depth32float,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        )
        shadow_depth_view: wgpu.GPUTextureView = shadow_depth.create_view(
            label="shadow_depth_texture_view",
            format=wgpu.TextureFormat.depth32float,
            dimension="2d",
            aspect=wgpu.TextureAspect.depth_only,
            base_mip_level=0,
            mip_level_count=1,
            base_array_layer=0,
            array_layer_count=1,
        )  
        shadow_depth_sampler: wgpu.GPUSampler = GpuController().device.create_sampler()


        # Appengind the Generated textures To the Texture lib
        TextureLib().append_texture(name="fxaa_gfx", texture=Texture(
            texture=fxaa_gfx,
            view=fxaa_gfx_view,
            sampler=fxaa_gfx_sampler,
            width=self.render_size[0],
            height=self.render_size[1]
        ))
        TextureLib().append_texture(name="g_position_gfx", texture=Texture(
            texture=g_position_gfx,
            view=g_position_gfx_view,
            sampler=g_position_gfx_sampler,
            width=self.render_size[0],
            height=self.render_size[1]
        )) 
        TextureLib().append_texture(name="g_normal_gfx", texture=Texture(
            texture=g_normal_gfx,
            view=g_normal_gfx_view,
            sampler=g_normal_gfx_sampler,
            width=self.render_size[0],
            height=self.render_size[1]
        ))
        TextureLib().append_texture(name="g_color_gfx", texture=Texture(
            texture=g_color_gfx,
            view=g_color_gfx_view,
            sampler=g_color_gfx_sampler,
            width=self.render_size[0],
            height=self.render_size[1]
        ))
        TextureLib().append_texture(name="world_gfx", texture=Texture(
            texture=world_gfx,
            view=world_gfx_view,
            sampler=world_gfx_sampler,
            width=self.render_size[0],
            height=self.render_size[1]
        )) 
        TextureLib().append_texture(name="world_depth", texture=Texture(
            texture=world_depth,
            view=world_depth_view,
            sampler=world_depth_sampler,
            width=self.render_size[0],
            height=self.render_size[1]
        ))  
        TextureLib().append_texture(name="shadow_gfx", texture=Texture(
            texture=shadow_gfx, 
            view=shadow_gfx_view,
            sampler=shadow_gfx_sampler,
            width=2048,
            height=2048
        ))
        TextureLib().append_texture(name="shadow_depth", texture=Texture(
            texture=shadow_depth, 
            view=shadow_depth_view,
            sampler=shadow_depth_sampler, 
            width=2048,
            height=2048
        ))

    def on_prepare(self, entity: Entity, components: Component | list[Component], command_encoder: wgpu.GPUCommandEncoder): 

        assert_that(
            (type(components) == RenderExclusiveComponent), 
            "Render exclusive component not detected in the Renderer initialization"
        ).is_true()

        if GpuController().render_target_size[0] == self.render_size[0] and GpuController().render_target_size[1] == self.render_size[1]:  
            return 

        print(f"Render target resized to width: {self.render_size[0]} -> {GpuController().render_target_size[0]} and height: {self.render_size[1]} -> {GpuController().render_target_size[1]}")    
        self.render_size = GpuController().render_target_size

        fxaa_gfx: wgpu.GPUTexture = GpuController().device.create_texture( 
            label="canvas_texture",
            size=[self.render_size[0], self.render_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        fxaa_gfx_view: wgpu.GPUTextureView = fxaa_gfx.create_view() 
        fxaa_gfx_sampler: wgpu.GPUSampler = GpuController().device.create_sampler()

        g_position_gfx: wgpu.GPUTexture = GpuController().device.create_texture( 
            label="canvas_texture",
            size=[self.render_size[0], self.render_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        g_position_gfx_view: wgpu.GPUTextureView = g_position_gfx.create_view() 
        g_position_gfx_sampler: wgpu.GPUSampler = GpuController().device.create_sampler(
            min_filter=wgpu.FilterMode.linear,
            mag_filter=wgpu.FilterMode.linear,
            mipmap_filter=wgpu.FilterMode.nearest
        )

        g_normal_gfx: wgpu.GPUTexture = GpuController().device.create_texture( 
            label="canvas_texture",
            size=[self.render_size[0], self.render_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        g_normal_gfx_view: wgpu.GPUTextureView = g_normal_gfx.create_view() 
        g_normal_gfx_sampler: wgpu.GPUSampler = GpuController().device.create_sampler(
            min_filter=wgpu.FilterMode.linear,
            mag_filter=wgpu.FilterMode.linear,
            mipmap_filter=wgpu.FilterMode.nearest
        )

        g_color_gfx: wgpu.GPUTexture = GpuController().device.create_texture( 
            label="canvas_texture",
            size=[self.render_size[0], self.render_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        g_color_gfx_view: wgpu.GPUTextureView = g_color_gfx.create_view() 
        g_color_gfx_sampler: wgpu.GPUSampler = GpuController().device.create_sampler(
            min_filter=wgpu.FilterMode.linear,
            mag_filter=wgpu.FilterMode.linear,
            mipmap_filter=wgpu.FilterMode.nearest
        )

        world_gfx: wgpu.GPUTexture = GpuController().device.create_texture( 
            label="canvas_texture",
            size=[self.render_size[0], self.render_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        world_gfx_view: wgpu.GPUTextureView = world_gfx.create_view() 
        world_gfx_sampler: wgpu.GPUSampler = GpuController().device.create_sampler(
            min_filter=wgpu.FilterMode.linear,
            mag_filter=wgpu.FilterMode.linear,
            mipmap_filter=wgpu.FilterMode.linear
        )

        world_depth: wgpu.GPUTexture = GpuController().device.create_texture(
            label="canvas_depth_texture",
            size=[self.render_size[0], self.render_size[1], 1],
            mip_level_count=1,
            sample_count=1,
            dimension="2d",
            format=wgpu.TextureFormat.depth32float,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING
        ) 
        world_depth_view: wgpu.GPUTextureView = world_depth.create_view(
            label="canvas_depth_texture_view",
            format=wgpu.TextureFormat.depth32float,
            dimension="2d",
            aspect=wgpu.TextureAspect.depth_only,
            base_mip_level=0,
            mip_level_count=1,
            base_array_layer=0,
            array_layer_count=1,
        ) 
        world_depth_sampler: wgpu.GPUSampler = GpuController().device.create_sampler() 

        TextureLib().append_texture(name="fxaa_gfx", texture=Texture(
            texture=fxaa_gfx,
            view=fxaa_gfx_view,
            sampler=fxaa_gfx_sampler,
            width=self.render_size[0],
            height=self.render_size[1]
        ))
        TextureLib().append_texture(name="g_position_gfx", texture=Texture(
            texture=g_position_gfx,
            view=g_position_gfx_view,
            sampler=g_position_gfx_sampler,
            width=self.render_size[0],
            height=self.render_size[1]
        )) 
        TextureLib().append_texture(name="g_normal_gfx", texture=Texture(
            texture=g_normal_gfx,
            view=g_normal_gfx_view,
            sampler=g_normal_gfx_sampler,
            width=self.render_size[0],
            height=self.render_size[1]
        ))
        TextureLib().append_texture(name="g_color_gfx", texture=Texture(
            texture=g_color_gfx,
            view=g_color_gfx_view,
            sampler=g_color_gfx_sampler,
            width=self.render_size[0],
            height=self.render_size[1]
        ))
        TextureLib().append_texture(name="world_gfx", texture=Texture(
            texture=world_gfx,
            view=world_gfx_view,
            sampler=world_gfx_sampler, 
            width=self.render_size[0],
            height=self.render_size[1]
        ))
        TextureLib().append_texture(name="world_depth", texture=Texture(
            texture=world_depth,
            view=world_depth_view,
            sampler=world_depth_sampler, 
            width=self.render_size[0],
            height=self.render_size[1]
        )) 
 
    def on_render(self, entity: Entity, components: Component | list[Component], render_pass:wgpu.GPURenderPassEncoder): 
        pass