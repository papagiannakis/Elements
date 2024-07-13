from __future__ import annotations

import wgpu

from Elements.pyECSS.wgpu_components import Component
from Elements.pyECSS.wgpu_entity import Entity   

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
        self.filtered_entities = self.filter_entities(entities, entity_components_relation) 
        for entity in self.filtered_entities:
            components = self.extract_components(entity, entity_components_relation, components_array)
            if len(components) == 1:
                self.on_create(entity, components[0])
            else:
                self.on_create(entity, components)  

    def prepare(self, entities, entity_components_relation, components_array, command_encoder: wgpu.GPUCommandEncoder): 
        for entity in self.filtered_entities:
            components = self.extract_components(entity, entity_components_relation, components_array)
            if len(components) == 1:
                self.on_prepare(entity, components[0], command_encoder)
            else:
                self.on_prepare(entity, components, command_encoder) 

    def render(self, entities, entity_components_relation, components_array, render_pass): 
        for entity in self.filtered_entities:
            components = self.extract_components(entity, entity_components_relation, components_array) 
            if len(components) == 1:
                self.on_render(entity, components[0], render_pass)
            else: 
                self.on_render(entity, components, render_pass)

    def on_create(self, entity: Entity, components: Component | list[Component]): 
        pass;  
    
    def on_prepare(self, entity: Entity, components: Component | list[Component], command_encoder: wgpu.GPUCommandEncoder):
        pass;

    def on_render(self, entity: Entity, components: Component | list[Component], render_pass: wgpu.GPURenderPassEncoder | wgpu.GPUComputePassEncoder): 
        pass;