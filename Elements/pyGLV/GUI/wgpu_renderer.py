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
from Elements.pyGLV.GUI.RenderPasses.SSAOPass import SSAOPass 
from Elements.pyGLV.GUI.RenderPasses.SSAOBlurPass import SSAOBlurPass 
from Elements.pyGLV.GUI.RenderPasses.SkyboxPass import SkyboxPass 
from Elements.pyGLV.GUI.RenderPasses.ShadowMapPass import ShadowMapPass   
from Elements.pyGLV.GUI.RenderPasses.FXAAPass import FXAAPass
from Elements.pyGLV.GUI.wgpu_gpu_controller import GpuController
from Elements.pyGLV.GL.wgpu_texture import Texture, TextureLib 

class RenderPassDescriptor:
    """
    Class to describe the configuration for a render pass, including color and depth attachments.
    """    

    def __init__(self):  
        """
        Initialize the render pass descriptor with default values for color and depth attachments.
        """

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
        """
        Generate the color attachments configuration for the render pass.

        :return: List of dictionaries containing color attachment settings.
        """

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
        """
        Generate the depth attachments configuration for the render pass.

        :return: Dictionary containing depth attachment settings.
        """

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
    """
    Singleton class to manage the rendering process, including initialization and execution of render passes.
    """

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
        """
        Add a rendering system to the renderer and initialize it with the current scene data.

        :param name: Name of the system.
        :param system: Instance of the RenderSystem to add.
        """

        self.attached_systems.update({name: system})
        system.create(Scene().entities, Scene().entity_componets_relation, Scene().components)   

    def actuate_system(self, name:str, command_encoder: wgpu.GPUCommandEncoder, render_pass):
        """
        Actuate the specified system to prepare and render using the given command encoder and render pass.

        :param name: Name of the system to actuate.
        :param command_encoder: The GPU command encoder.
        :param render_pass: The render pass to use for rendering.
        """

        self.attached_systems[name].prepare(Scene().entities, Scene().entity_componets_relation, Scene().components, command_encoder) 
        self.attached_systems[name].render(Scene().entities, Scene().entity_componets_relation, Scene().components, render_pass)

    def init(self, present_context, render_texture_format, SSAO=False):
        """
        Initialize the renderer with the specified context and format, and add default rendering systems.

        :param present_context: The presentation context for rendering.
        :param render_texture_format: The format of the render texture.
        :param SSAO: Boolean to enable or disable Screen Space Ambient Occlusion (SSAO).
        """        

        # settings
        self.SSAO = SSAO

        GpuController().present_context = present_context
        GpuController().render_texture_format = render_texture_format 

        self.add_system("Initial", InitialPass([RenderExclusiveComponent]))  
        self.add_system("Shadows", ShadowMapPass([ShadowAffectionComponent, MeshComponent, TransformComponent]))
        self.add_system("Skybox", SkyboxPass([SkyboxComponent]))
        self.add_system("DeferedGeometry", DeferedGeometryPass([MeshComponent, MaterialComponent, DeferrdGeometryComponent, TransformComponent])) 
        self.add_system("SSAO", SSAOPass([RenderExclusiveComponent]))
        self.add_system("SSAOBlur", SSAOBlurPass([RenderExclusiveComponent]))
        self.add_system("DeferedLight", DeferedLightPass([MaterialComponent, DeferredLightComponent]))
        self.add_system("ForwardPass", ForwardRenderPass([MeshComponent, MaterialComponent, ForwardShaderComponent])) 
        self.add_system("FXAA", FXAAPass([RenderExclusiveComponent]))
        self.add_system("BlitToSurface", BlitSurafacePass([RenderExclusiveComponent]))

    def render(self, size:list[int]):
        """
        Perform the rendering process, executing all attached systems and rendering passes.

        :param size: List of two integers specifying the width and height of the render target.
        """
                
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

        if self.SSAO == True:
            ssao_pass = command_encoder.begin_compute_pass() 
            self.actuate_system("SSAO", command_encoder, ssao_pass)  
            ssao_pass.end()

            ssao_blur_pass = command_encoder.begin_compute_pass() 
            self.actuate_system("SSAOBlur", command_encoder, ssao_blur_pass)  
            ssao_blur_pass.end()

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


