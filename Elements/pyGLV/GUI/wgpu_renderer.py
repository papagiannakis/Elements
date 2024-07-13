from __future__ import annotations

import wgpu
import glm
import numpy as np   
from enum import Enum

from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyECSS.wgpu_components import *
from Elements.pyGLV.GL.wpgu_scene import Scene       
from Elements.pyGLV.GUI.RenderPasses.InitialPass import InitialPass 
from Elements.pyGLV.GUI.RenderPasses.BlitToSurfacePass import BlitSurafacePass 
from Elements.pyGLV.GUI.RenderPasses.ForwardPass import ForwardRenderPass
from Elements.pyGLV.GUI.RenderPasses.DeferedGeometryPass import DeferedGeometryPass 
from Elements.pyGLV.GUI.RenderPasses.DeferedLightPass import DeferedLightPass 
from Elements.pyGLV.GUI.RenderPasses.SSAONoisePass import SSAONoisePass 
from Elements.pyGLV.GUI.RenderPasses.SkyboxPass import SkyboxPass 
from Elements.pyGLV.GUI.RenderPasses.ShadowMapPass import ShadowMapPass   
from Elements.pyGLV.GUI.RenderPasses.FXAAPass import FXAAPass
from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController
from Elements.pyGLV.GL.wgpu_texture import Texture, TextureLib 

class RenderPassDescriptor: 
    def __init__(self):  
        # color attachments
        self.view = None
        self.resolve_target = None 
        self.clear_value = (0.0, 0.0, 0.0, 1.0)
        self.load_op = wgpu.LoadOp.clear 
        self.store_op = wgpu.StoreOp.store 

        #depth attachments 
        self.depth_view = None
        self.depth_clear_value = 1.0
        self.depth_load_op = wgpu.LoadOp.clear
        self.depth_store_op = wgpu.StoreOp.store
        self.depth_read_only = False
        self.stencil_clear_value = 0
        self.stencil_load_op = wgpu.LoadOp.clear
        self.stencil_store_op = wgpu.StoreOp.store
        self.stencil_read_only = True

    def generate_color_attachments(self): 
        return [
            {
                "view": self.view,
                "resolve_target": self.resolve_target,
                "clear_value": self.clear_value, 
                "load_op": self.load_op,
                "store_op": self.store_op,
            }
        ]

    def generate_depth_attachments(self): 
        return {
            "view": self.depth_view,
            "depth_clear_value": self.depth_clear_value,
            "depth_load_op": self.depth_load_op,
            "depth_store_op": self.depth_store_op,
            "depth_read_only": self.depth_read_only,
            "stencil_clear_value": self.stencil_clear_value,
            "stencil_load_op": self.stencil_load_op,
            "stencil_store_op": self.stencil_store_op,
            "stencil_read_only": self.stencil_read_only,
        }

class Renderer:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            print('Creating Renderer Singleton Object')
            cls._instance = super(Renderer, cls).__new__(cls)  

            cls.attached_systems = {}

            RenderEntity = Scene().add_entity()
            Scene().add_component(RenderEntity, RenderExclusiveComponent()) 

        return cls._instance
    
    def __init__(self):
        None; 

    def add_system(self, name:str, system: RenderSystem):  
        self.attached_systems.update({name: system})
        system.create(Scene().entities, Scene().entity_componets_relation, Scene().components)   

    def actuate_system(self, name:str, command_encoder: wgpu.GPUCommandEncoder, render_pass):
        self.attached_systems[name].prepare(Scene().entities, Scene().entity_componets_relation, Scene().components, command_encoder) 
        self.attached_systems[name].render(Scene().entities, Scene().entity_componets_relation, Scene().components, render_pass)

    def init(self, present_context, render_texture_format):  
        GpuController().present_context = present_context
        GpuController().render_texture_format = render_texture_format 

        self.add_system("Initial", InitialPass([RenderExclusiveComponent]))  
        self.add_system("Shadows", ShadowMapPass([ShadowAffectionComponent, MeshComponent, TransformComponent]))
        self.add_system("Skybox", SkyboxPass([SkyboxComponent]))
        self.add_system("DeferedGeometry", DeferedGeometryPass([DeferedShaderComponent, MeshComponent, TransformComponent])) 
        self.add_system("SSAONoise", SSAONoisePass([RenderExclusiveComponent]))
        self.add_system("DeferedLight", DeferedLightPass([MeshComponent, MaterialComponent, DeferedShaderComponent]))
        self.add_system("ForwardPass", ForwardRenderPass([MeshComponent, MaterialComponent, ForwardShaderComponent])) 
        self.add_system("FXAA", FXAAPass([RenderExclusiveComponent]))
        self.add_system("BlitToSurface", BlitSurafacePass([RenderExclusiveComponent]))

    def render(self, size:list[int]):    
        # resize if needed 
        GpuController().render_target_size = size
        command_encoder : wgpu.GPUCommandEncoder = GpuController().device.create_command_encoder()

        self.actuate_system("Initial", command_encoder, None) 
        
        shadowDescriptor = RenderPassDescriptor()  
        shadowDescriptor.view = TextureLib().get_texture(name="shadow_gfx").view
        shadowDescriptor.depth_view = TextureLib().get_texture(name="shadow_depth").view  
        shadowDescriptor.clear_value = (1.0, 1.0, 1.0, 1.0)
        shadow_render_pass = command_encoder.begin_render_pass(
            color_attachments=shadowDescriptor.generate_color_attachments(),
            depth_stencil_attachment=shadowDescriptor.generate_depth_attachments()
        )
        self.actuate_system("Shadows", command_encoder, shadow_render_pass)
        shadow_render_pass.end()

        deferedGeomDescriptor = RenderPassDescriptor() 
        deferedGeomDescriptor.depth_view = TextureLib().get_texture(name="world_depth").view
        geometry_render_pass = command_encoder.begin_render_pass(
            color_attachments=[
                {
                    "view": TextureLib().get_texture(name="g_position_gfx").view,
                    "resolve_target": None,
                    "clear_value": (0.0, 0.0, 0.0, 1.0), 
                    "load_op": wgpu.LoadOp.clear,
                    "store_op": wgpu.StoreOp.store,
                },
                {
                    "view": TextureLib().get_texture(name="g_normal_gfx").view,
                    "resolve_target": None,
                    "clear_value": (0.0, 0.0, 0.0, 1.0), 
                    "load_op": wgpu.LoadOp.clear,
                    "store_op": wgpu.StoreOp.store,
                },
                {
                    "view": TextureLib().get_texture(name="g_color_gfx").view,
                    "resolve_target": None,
                    "clear_value": (0.0, 0.0, 0.0, 1.0), 
                    "load_op": wgpu.LoadOp.clear,
                    "store_op": wgpu.StoreOp.store,
                }, 
            ],
            depth_stencil_attachment=deferedGeomDescriptor.generate_depth_attachments()
        )  
        self.actuate_system("DeferedGeometry", command_encoder, geometry_render_pass)
        geometry_render_pass.end() 

        ssao_noise_pass = command_encoder.begin_compute_pass() 
        self.actuate_system("SSAONoise", command_encoder, ssao_noise_pass)
        ssao_noise_pass.end()

        worldDescriptor = RenderPassDescriptor() 
        worldDescriptor.view = TextureLib().get_texture(name="world_gfx").view
        worldDescriptor.depth_view = TextureLib().get_texture(name="world_depth").view
        world_render_pass = command_encoder.begin_render_pass(
            color_attachments=worldDescriptor.generate_color_attachments(),
            depth_stencil_attachment=worldDescriptor.generate_depth_attachments()
        )   
        # completing the pass of the deferred elemenets and fill the depth buffer
        self.actuate_system("DeferedLight", command_encoder, world_render_pass)   
        # baised on the filled depth buffer start drawing the forward rendered elements
        self.actuate_system("ForwardPass", command_encoder, world_render_pass) 
        # complete the pass with the skybox
        self.actuate_system("Skybox", command_encoder, world_render_pass)
        world_render_pass.end()

        fxaaDescriptor = RenderPassDescriptor() 
        fxaaDescriptor.view = TextureLib().get_texture(name="fxaa_gfx").view
        fxaa_render_pass = command_encoder.begin_render_pass(
            color_attachments=fxaaDescriptor.generate_color_attachments()
        ) 
        self.actuate_system("FXAA", command_encoder, fxaa_render_pass)
        fxaa_render_pass.end()

        blitDescriptor = RenderPassDescriptor()
        blitDescriptor.view = GpuController().present_context.get_current_texture().create_view() 
        blit_render_pass = command_encoder.begin_render_pass(
            color_attachments=blitDescriptor.generate_color_attachments()
        ) 
        self.actuate_system("BlitToSurface", command_encoder, blit_render_pass) 
        blit_render_pass.end()

        GpuController().device.queue.submit([command_encoder.finish()]) 


