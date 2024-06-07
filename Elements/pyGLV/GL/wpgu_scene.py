import wgpu
import glm
import numpy as np   

from __future__ import annotations
from Elements.pyECSS.wgpu_components import Component 
from Elements.pyECSS.wgpu_components import TransformComponent 
from Elements.pyECSS.wgpu_components import InfoComponent 
from Elements.pyECSS.wgpu_entity import Entity

class Scene():
    """
    Singleton Scene that assembles ECSSManager and Viewer classes together for Scene authoring
    in pyglGA. It also brings together the new extensions to pyglGA: Shader, VertexArray and 
    RenderMeshDecorators
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            print('Creating Scene Singleton Object')
            cls._instance = super(Scene, cls).__new__(cls)

            # cls._cammera = None
            # cls._objects = [] 
            # cls._canvasWidth = 0 
            # cls._canvasHeight = 0 
            # cls._light = None 

            cls.entity_componets_relation = {}  
            cls.components = {}
            cls.entities = []
            cls.systemns = [] 

            cls.canvas_width = 0;
            cls.canvas_height = 0;
        return cls._instance
    
    
    def __init__(self):
        None; 

    def add_entity(self) -> Entity: 
        
        entity = Entity()
        self.entities.append(Entity) 
        return entity  
    
    def get_entities(self) -> list[Entity]: 
        return self.entities
    
    def has_component(self, ent:Entity, component_type:type) -> bool:

        return (ent.id in self.entity_componets_relation and
                component_type in self.entity_componets_relation.get(ent.id) and
                self.entity_componets_relation[ent.id][component_type] != None and
                self.components[component_type][self.entity_componets_relation[ent.id][component_type]] != None) 
    
    def get_component(self, ent:Entity, component_type:type):

        if self.has_component(ent=ent, component_type=component_type) == False:
            return None; 

        index = self.entity_componets_relation[ent.id][component_type] 
        return self.components[component_type][index]

    def add_component(self, ent:Entity, component):

        if ent.id not in self.entity_componets_relation:
            self.entity_componets_relation[ent.id] = {} 

        component_type = type(component) 

        if self.has_component(ent=ent, component_type=component_type) is True:
            print(f'Entity {ent} has already component with type: {component_type}') 
            return self.get_component(ent=ent, component_type=component_type)
        
        if component_type not in self.components:
            self.components[component_type] = [] 

        c_array = self.components[component_type] 
        c_index = len(c_array) 

        self.entity_componets_relation[ent.id][component_type] = c_index 

        self.components[component_type].append(component) 

        return component
    
    def add_system(self, system):
        pass

    # def set_cammera(self, cam: fps_cammera.cammera):
    #     self._cammera = cam

    # def append_object(self, obj: Object): 
    #     self._objects.append(obj) 

    # def set_light(self, pos:any):
    #     self._light = pos;

    # def init(self, device:wgpu.GPUDevice):
    #     for obj in self._objects: 
    #         obj.onInit()  

    #     for obj in self._objects: 
    #         obj.init(device=device) 

    # def update(self, canvas, event):
    #     self._canvasWidth = canvas._windowWidth
    #     self._canvasHeight = canvas._windowHeight

    #     self._cammera.update(canvas=canvas, event=event)

    #     for obj in self._objects:
    #         obj.onUpdate()

    def scene_debug_dump(self):
        
        for id in self.entity_componets_relation.keys():
            for c_type in self.entity_componets_relation[id].keys(): 
                index = self.entity_componets_relation[id][c_type] 
                component = self.components[c_type][index] 

                print(f'Entity id:{id} component:{component}')

if __name__ == "__main__":
    # The client singleton code.

    s1 = Scene()
    s2 = Scene() 

    ent1 = s1.add_entity() 
    ent2 = s2.add_entity() 

    trs = Scene().add_component(ent1, TransformComponent(glm.vec3(1), glm.vec3(1), glm.vec3(1)))
    info = Scene().add_component(ent2, InfoComponent("SIAROP"))
    Scene().add_component(ent1, info) 
    Scene().add_component(ent2, info)

    if id(s1) == id(s2):
        print("Singleton works, both Scenes contain the same instance.")
    else:
        print("Singleton failed, Scenes contain different instances.")  

    Scene().scene_debug_dump()
    
     