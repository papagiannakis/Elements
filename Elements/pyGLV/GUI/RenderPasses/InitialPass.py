from __future__ import annotations 

from Elements.pyECSS.wgpu_components import Component
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyGLV.GUI.wgpu_render_system import RenderSystem 
from Elements.pyGLV.GUI.wgpu_cache_manager import GpuCache

class InitialPass(RenderSystem):  
    def __init__(self, filters: list[type]):
        super().__init__(filters) 

        

    def on_create(self, entity: Entity, components: Component | list[Component]): 
        pass 

    def on_prepare(self, entity: Entity, components: Component | list[Component]): 
        pass 
 
    def on_render(self, entity: Entity, components: Component | list[Component]): 
        pass