from __future__ import annotations

from Elements.pyECSS.wgpu_components import Component
from Elements.pyECSS.wgpu_entity import Entity   

class System(object): 
    """
    Base class for all systems in the ECS framework.
    
    Systems are responsible for processing entities that match specific component filters.
    """

    def __init__(self, filters: list[type]): 
        self.filters = filters 

    def filter_entities(self, entities, entity_components):  
        """
        Filter entities based on the system's component type filters.

        :param entities: List of all entities.
        :param entity_components: Dictionary mapping entity IDs to their components.
        :return: List of entities that match the component filters.
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
        Extract components from an entity based on the system's filters.

        :param entity: The entity from which to extract components.
        :param entity_component_relation: Dictionary mapping entity IDs to their components.
        :param component_array: Dictionary mapping component types to lists of components.
        :return: List of components for the entity.
        """

        components = []
        for comp_type in self.filters:
            components.append(component_array[comp_type][entity_component_relation[entity.id][comp_type]])
        return components
    
    def create(self, entities, entity_components_relation, components_array):
        """
        Filter entities and call the on_create method for each matching entity.

        :param entities: List of all entities.
        :param entity_components_relation: Dictionary mapping entity IDs to their components.
        :param components_array: Dictionary mapping component types to lists of components.
        """

        self.filtered_entities = self.filter_entities(entities, entity_components_relation) 
        for entity in self.filtered_entities:
            components = self.extract_components(entity, entity_components_relation, components_array)
            if len(components) == 1:
                self.on_create(entity, components[0])
            else:
                self.on_create(entity, components)

    def update(self, ts, entities, entity_components_relation, components_array, event):  
        """
        Update matching entities by calling the on_update method for each.

        :param ts: Timestamp of the update.
        :param entities: List of all entities.
        :param entity_components_relation: Dictionary mapping entity IDs to their components.
        :param components_array: Dictionary mapping component types to lists of components.
        :param event: Event to handle during the update.
        """

        for entity in self.filtered_entities:
            components = self.extract_components(entity, entity_components_relation, components_array) 
            if len(components) == 1:
                self.on_update(ts=ts, entity=entity, components=components[0], event=event)
            else: 
                self.on_update(ts=ts, entity=entity, components=components, event=event)

    def on_create(self, entity: Entity, components: Component | list[Component]): 
        """
        Method called when a new entity is created and matches the system's filters.

        This method should be overridden by subclasses to define specific behavior.

        :param entity: The entity being created.
        :param components: The components of the entity.
        """

        pass; 

    def on_update(self, ts, entity: Entity, components: Component | list[Component], event):
        """
        Method called during the update phase for each entity that matches the system's filters.

        This method should be overridden by subclasses to define specific behavior.

        :param ts: Timestamp of the update.
        :param entity: The entity being updated.
        :param components: The components of the entity.
        :param event: The event to handle during the update.
        """

        pass;