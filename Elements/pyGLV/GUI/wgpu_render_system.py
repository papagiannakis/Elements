from __future__ import annotations

from Elements.pyECSS.wgpu_components import Component
from Elements.pyECSS.wgpu_components import Entity   

class RenderSystem(object): 
    def __init__(self, filters: list[type]): 
        self.filters = filters 

    def filter_entities(self, entities, entity_components): 
        filtered_entities = []

        for entity in entities: 
            entity_id = entity.id
            
            # Check if the entity has all the required component types
            if all(comp_type in entity_components.get(entity_id, {}) for comp_type in self.filters):
                filtered_entities.append(entity)

        return filtered_entities
    
    def extract_components(self, entity, entity_component_relation, component_array):
        components = []
        for comp_type in self.filters:
            components.append(component_array[comp_type][entity_component_relation[entity.id][comp_type]])
        return components 
    
    def create(self, entities, entity_components_relation, components_array): 
        filtered_entities = self.filter_entities(entities, entity_components_relation) 
        for entity in filtered_entities:
            components = self.extract_components(entity, entity_components_relation, components_array)
            if len(components) == 1:
                self.on_create(entity, components[0])
            else:
                self.on_create(entity, components)  

    def prepare(self, entities, entity_components_relation, components_array): 
        filtered_entities = self.filter_entities(entities, entity_components_relation) 
        for entity in filtered_entities:
            components = self.extract_components(entity, entity_components_relation, components_array)
            if len(components) == 1:
                self.on_prepare(entity, components[0])
            else:
                self.on_prepare(entity, components) 

    def render(self, entities, entity_components_relation, components_array): 
        filtered_entities = self.filter_entities(entities, entity_components_relation)
        for entity in filtered_entities:
            components = self.extract_components(entity, entity_components_relation, components_array) 
            if len(components) == 1:
                self.on_render(entity=entity, components=components[0])
            else: 
                self.on_render(entity=entity, components=components)

    def on_create(self, entity: Entity, components: Component | list[Component]): 
        pass;  
    
    def on_prepare(self, entity: Entity, components: Component | list[Component]):
        pass;

    def on_render(self, entity: Entity, components: Component | list[Component]): 
        pass;