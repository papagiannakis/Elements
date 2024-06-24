from __future__ import annotations

import wgpu
import glm
import numpy as np   
from enum import Enum

# from Elements.pyGLV.GL.wgpu_meshes import Buffers 
# from Elements.pyGLV.GUI.RenderPasses.ModelPass import ModelPass 
# from Elements.pyGLV.GUI.RenderPasses.ShadowMapPass import ShadowMapPass 

from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyECSS.wgpu_components import Component, RenderExclusiveComponent, MeshComponent, ShaderComponent, MaterialComponent
from Elements.pyGLV.GL.wpgu_scene import Scene       
from Elements.pyGLV.GUI.RenderPasses.InitialPass import InitialPass 
from Elements.pyGLV.GUI.RenderPasses.BlitToSurfacePass import BlitSurafacePass 
from Elements.pyGLV.GUI.RenderPasses.ModelPass import MeshRenderPass 
from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController 

class RenderPassDescriptor: 
    def __init__(self):  
        # color attachments
        self.view = None
        self.resolve_target = None 
        self.clear_value = (0.0, 0.0, 0.0, 0.0)
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

    def init(self, present_context, render_texture_format, canvas_size):  
        GpuController().present_context = present_context
        GpuController().render_texture_format = render_texture_format 

        GpuController().imported_canvas_size = canvas_size
        GpuController().active_canvas_size = canvas_size 

        self.add_system("Initial", InitialPass([RenderExclusiveComponent])) 
        self.add_system("MeshPass", MeshRenderPass([MeshComponent, MaterialComponent, ShaderComponent]))
        self.add_system("BlitToSurface", BlitSurafacePass([RenderExclusiveComponent]))

    def render(self, size:list[int]):    
        # resize if needed 
        GpuController().imported_canvas_size = size

        command_encoder : wgpu.GPUCommandEncoder = GpuController().device.create_command_encoder()

        self.actuate_system("Initial", command_encoder, None)  

        meshDescriptor = RenderPassDescriptor() 
        meshDescriptor.view = GpuController().canvas_texture_view
        meshDescriptor.depth_view = GpuController().canvas_texture_depth_view 
        mesh_render_pass = command_encoder.begin_render_pass(
            color_attachments=meshDescriptor.generate_color_attachments(),
            depth_stencil_attachment=meshDescriptor.generate_depth_attachments()
        ) 
        self.actuate_system("MeshPass", command_encoder, mesh_render_pass) 
        mesh_render_pass.end()

        blitDescriptor = RenderPassDescriptor()
        blitDescriptor.view = GpuController().present_context.get_current_texture().create_view() 
        blit_render_pass = command_encoder.begin_render_pass(
            color_attachments=blitDescriptor.generate_color_attachments()
        ) 
        self.actuate_system("BlitToSurface", command_encoder, blit_render_pass) 
        blit_render_pass.end()

        GpuController().device.queue.submit([command_encoder.finish()]) 


