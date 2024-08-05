from __future__ import annotations 

from Elements.pyECSS.wgpu_system import System 
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyECSS.wgpu_components import Component, CameraComponent

import glm

class CameraSystem(System):
    """
    The system responsible for managing camera components and updating their view and projection matrices.
    """

    def on_create(self, entity: Entity, components: Component | tuple[Component]): 
        """
        Initialize the camera component when the entity is created.
        
        This sets up the initial view and projection matrices for the camera.

        :param entity: The entity being created.
        :param components: The components associated with the entity, expected to include a camera and transform component.
        """

        camera, transform = components
        
        camera.view = glm.inverse(transform.world_matrix)

        if camera.type == CameraComponent.Type.PERSPECTIVE:
            camera.projection = glm.perspective(glm.radians(camera.fov), camera.aspect_ratio, camera.near, camera.far)
        elif camera.type == CameraComponent.Type.ORTHOGRAPHIC:
            camera.projection = glm.ortho(-camera.aspect_ratio * camera.zoom_level, camera.aspect_ratio * camera.zoom_level, -camera.zoom_level, camera.zoom_level, camera.near, camera.far) 
            
        camera.view_projection = camera.projection * camera.view

    def on_update(self, ts, entity: Entity, components: Component | tuple[Component], event):
        """
        Update the camera's view and projection matrices based on the entity's transform.

        This recalculates the view and projection matrices if the transform is not static.

        :param ts: Time step for the update.
        :param entity: The entity being updated.
        :param components: The components associated with the entity, expected to include a camera and transform component.
        :param event: The event triggering the update (unused in this method).
        """
        
        camera, transform = components

        if not transform.static:
            camera.view = glm.inverse(transform.world_matrix)
        
            if camera.type == CameraComponent.Type.PERSPECTIVE:
                camera.projection = glm.perspective(glm.radians(camera.fov), camera.aspect_ratio, camera.near, camera.far)
            elif camera.type == CameraComponent.Type.ORTHOGRAPHIC:
                camera.projection = glm.ortho(-camera.aspect_ratio * camera.zoom_level, camera.aspect_ratio * camera.zoom_level, -camera.zoom_level, camera.zoom_level, camera.near, camera.far) 
                
            camera.view_projection = camera.projection * camera.view
