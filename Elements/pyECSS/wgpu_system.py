from __future__ import annotations

from Elements.pyECSS.wgpu_components import Component
from Elements.pyECSS.wgpu_components import Entity   
from Elements.pyGLV.GL.wpgu_scene   import Scene 

class System(object): 
    def __init__(self, filters: list[type]): 
        self.filters = filters 
        self.filtered_entities = None

    # def filter(self):  

    #     entities = Scene().get_entities()

    #     for filter, entity in zip(self.filters, entities):
            