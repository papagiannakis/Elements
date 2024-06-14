import wgpu
import glm
import numpy as np   
from enum import Enum

# from Elements.pyGLV.GL.wgpu_meshes import Buffers 
# from Elements.pyGLV.GUI.RenderPasses.ModelPass import ModelPass 
# from Elements.pyGLV.GUI.RenderPasses.ShadowMapPass import ShadowMapPass 

from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyECSS.wgpu_components import Component
from Elements.pyGLV.GL.wpgu_scene import Scene

class Renderer:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            print('Creating Renderer Singleton Object')
            cls._instance = super(Renderer, cls).__new__(cls)  

            cls.attached_systems:list[RenderSystem] = []

        return cls._instance
    
    def __init__(self):
        None; 

    def add_system(self, system: RenderSystem):  
        self.systems.append(system) 
        system.create(Scene().entities, Scene().entity_componets_relation, Scene().components)  

    def actuate_system(self, system: RenderSystem):
        system.prepare(Scene().entities, Scene().entity_componets_relation, Scene().components) 
        system.render(Scene().entities, Scene().entity_componets_relation, Scene().components)

    def init(self, present_context=None):  
        self._present_context = present_context  
        self._canvasContextFormat = self._present_context.get_preferred_format(self._device.adapter)  

    def render(self):  
        self._canvasContext = self._present_context.get_current_texture();   
        command_encoder = self._device.create_command_encoder()



        self._device.queue.submit([command_encoder.finish()]) 
        self._canvasContext = None;


