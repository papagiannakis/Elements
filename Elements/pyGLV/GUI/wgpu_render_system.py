from __future__ import annotations

import wgpu

from Elements.pyECSS.wgpu_components import Component
from Elements.pyECSS.wgpu_entity import Entity   

class RenderSystem(object):
    """
    Base class for rendering systems. Handles filtering of entities based on required components
    and provides hooks for creating, preparing, and rendering entities.
    """    

    def __init__(self, filters: list[type]): 
        self.filters = filters 

    def filter_entities(self, entities, entity_components): 
        """
        Filter entities based on the required component types.

        :param entities: List of entities to be filtered.
        :param entity_components: Dictionary mapping entity IDs to their components.
        :return: List of entities that have all the required component types.
        """

        filtered_entities = []

        for entity in entities: 
            entity_id = entity.id
            
            # Check if the entity has all the required component types
            if all(comp_type in entity_components.get(entity_id, {}) for comp_type in self.filters):
                filtered_entities.append(entity)

        return filtered_entities
    
    def extract_components(self, entity, entity_component_relation, component_array):
        """
        Extract the required components for an entity.

        :param entity: The entity whose components are to be extracted.
        :param entity_component_relation: Dictionary mapping entity IDs to their component types.
        :param component_array: Dictionary mapping component types to arrays of component instances.
        :return: List of components for the entity.
        """

        components = []
        for comp_type in self.filters:
            components.append(component_array[comp_type][entity_component_relation[entity.id][comp_type]])
        return components 
    
    def create(self, entities, entity_components_relation, components_array): 
        """
        Filter entities and call the on_create method for each filtered entity.

        :param entities: List of all entities.
        :param entity_components_relation: Dictionary mapping entity IDs to their component types.
        :param components_array: Dictionary mapping component types to arrays of component instances.
        """

        self.filtered_entities = self.filter_entities(entities, entity_components_relation) 
        for entity in self.filtered_entities:
            components = self.extract_components(entity, entity_components_relation, components_array)
            if len(components) == 1:
                self.on_create(entity, components[0])
            else:
                self.on_create(entity, components)  

    def prepare(self, entities, entity_components_relation, components_array, command_encoder: wgpu.GPUCommandEncoder): 
        """
        Call the on_prepare method for each filtered entity.

        :param entities: List of all entities.
        :param entity_components_relation: Dictionary mapping entity IDs to their component types.
        :param components_array: Dictionary mapping component types to arrays of component instances.
        :param command_encoder: Command encoder for GPU commands.
        """

        for entity in self.filtered_entities:
            components = self.extract_components(entity, entity_components_relation, components_array)
            if len(components) == 1:
                self.on_prepare(entity, components[0], command_encoder)
            else:
                self.on_prepare(entity, components, command_encoder) 

    def render(self, entities, entity_components_relation, components_array, render_pass): 
        """
        Call the on_render method for each filtered entity.

        :param entities: List of all entities.
        :param entity_components_relation: Dictionary mapping entity IDs to their component types.
        :param components_array: Dictionary mapping component types to arrays of component instances.
        :param render_pass: Render pass encoder for GPU rendering.
        """

        for entity in self.filtered_entities:
            components = self.extract_components(entity, entity_components_relation, components_array) 
            if len(components) == 1:
                self.on_render(entity, components[0], render_pass)
            else: 
                self.on_render(entity, components, render_pass)

    def on_create(self, entity: Entity, components: Component | list[Component]): 
        """
        Hook method called when an entity is created.

        :param entity: The entity being created.
        :param components: The components of the entity.
        """

        pass;  
    
    def on_prepare(self, entity: Entity, components: Component | list[Component], command_encoder: wgpu.GPUCommandEncoder):
        """
        Hook method called when an entity is prepared for rendering.

        :param entity: The entity being prepared.
        :param components: The components of the entity.
        :param command_encoder: Command encoder for GPU commands.
        """

        pass;

    def on_render(self, entity: Entity, components: Component | list[Component], render_pass: wgpu.GPURenderPassEncoder | wgpu.GPUComputePassEncoder): 
        """
        Hook method called when an entity is rendered.

        :param entity: The entity being rendered.
        :param components: The components of the entity.
        :param render_pass: Render pass encoder for GPU rendering.
        """

        pass;