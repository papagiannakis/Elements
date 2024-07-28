from __future__ import annotations 

import wgpu
import glm
import numpy as np   

from Elements.pyECSS.wgpu_components import InfoComponent  
from Elements.pyECSS.wgpu_components import TransformComponent  
from Elements.pyECSS.systems.wgpu_transform_system import TransformSystem

from Elements.pyECSS.wgpu_entity import Entity  
from Elements.pyECSS.wgpu_system import System

class Scene():
    """
    Singleton class to manage entities, components, and systems in a scene.
    """

    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            print('Creating Scene Singleton Object')
            cls._instance = super(Scene, cls).__new__(cls) 

            cls.entity_componets_relation = {}  
            cls.components = {}
            cls.entities:list[Entity] = [] 
            cls.systems:list[System] = [] 
        
            cls.primary_camera = None
        return cls._instance
    
    
    def __init__(self):
        None; 

    def add_entity(self) -> Entity: 
        """
        Adds a new entity to the scene.

        :return: The newly created entity.
        """
                
        entity = Entity() 
        self.entities.append(entity ) 
        return entity  
    
    def get_entities(self) -> list[Entity]:
        """
        Retrieves all entities in the scene.

        :return: List of entities.
        """

        return self.entities
    
    def has_component(self, ent:Entity, component_type:type) -> bool:
        """
        Checks if an entity has a specific component type.

        :param ent: The entity to check.
        :param component_type: The type of the component to check for.
        :return: True if the entity has the component, False otherwise.
        """

        return (ent.id in self.entity_componets_relation and
                component_type in self.entity_componets_relation.get(ent.id) and
                self.entity_componets_relation[ent.id][component_type] != None and
                self.components[component_type][self.entity_componets_relation[ent.id][component_type]] != None) 
    
    def get_component(self, ent:Entity, component_type:type): 
        """
        Retrieves a component of a specific type from an entity.

        :param ent: The entity to get the component from.
        :param component_type: The type of the component to retrieve.
        :return: The component if it exists, None otherwise.
        """

        if self.has_component(ent=ent, component_type=component_type) == False:
            return None; 

        index = self.entity_componets_relation[ent.id][component_type] 
        return self.components[component_type][index]

    def add_component(self, ent:Entity, component):
        """
        Adds a component to an entity.

        :param ent: The entity to add the component to.
        :param component: The component to add.
        :return: The added component.
        """        

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
    
    def add_system(self, system: System):
        """
        Adds a system to the scene.

        :param system: The system to add.
        """  

        self.systems.append(system) 
        system.create(self.entities, self.entity_componets_relation, self.components) 

    def update(self, event, ts):
        """
        Updates all systems in the scene.

        :param event: The event to process.
        :param ts: The timestep for the update.
        """  

        for system in self.systems:
            system.update(ts, self.entities, self.entity_componets_relation, self.components, event) 

    def set_primary_cam(self, ent:Entity):
        """
        Sets the primary camera entity.

        :param ent: The entity to set as the primary camera.
        """

        self.primary_camera = ent 

    def get_primary_cam(self):
        """
        Retrieves the primary camera entity.

        :return: The primary camera entity.
        """

        return self.primary_camera

    def scene_debug_dump(self):
        """
        Dumps the debug information of the scene, printing all entities and their components.
        """
        
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
    info = Scene().add_component(ent2, InfoComponent("component"))
    Scene().add_component(ent1, info) 
    Scene().add_component(ent2, info)

    Scene().add_system(TransformSystem([TransformComponent]))

    if id(s1) == id(s2):
        print("Singleton works, both Scenes contain the same instance.")
    else:
        print("Singleton failed, Scenes contain different instances.")  

    Scene().scene_debug_dump()
    
     