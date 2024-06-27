from __future__ import annotations 

from Elements.pyECSS.wgpu_system import System 
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyECSS.wgpu_components import Component, CameraComponent

import glm

class CameraSystem(System):
    """
    The system responsible for the cameras.
    """

    def on_create(self, entity: Entity, components: Component | tuple[Component]):
        camera, transform = components
        
        camera.view = glm.inverse(transform.world_matrix)

        if camera.type == CameraComponent.Type.PERSPECTIVE:
            camera.projection = glm.perspective(glm.radians(camera.fov), camera.aspect_ratio, camera.near, camera.far)
        elif camera.type == CameraComponent.Type.ORTHOGRAPHIC:
            camera.projection = glm.ortho(-camera.aspect_ratio * camera.zoom_level, camera.aspect_ratio * camera.zoom_level, -camera.zoom_level, camera.zoom_level, camera.near, camera.far) 
            
        camera.view_projection = camera.projection * camera.view

    def on_update(self, ts, entity: Entity, components: Component | tuple[Component], event):
        camera, transform = components

        if not transform.static:
            camera.view = glm.inverse(transform.world_matrix)
        
            if camera.type == CameraComponent.Type.PERSPECTIVE:
                camera.projection = glm.perspective(glm.radians(camera.fov), camera.aspect_ratio, camera.near, camera.far)
            elif camera.type == CameraComponent.Type.ORTHOGRAPHIC:
                camera.projection = glm.ortho(-camera.aspect_ratio * camera.zoom_level, camera.aspect_ratio * camera.zoom_level, -camera.zoom_level, camera.zoom_level, camera.near, camera.far) 
                
            camera.view_projection = camera.projection * camera.view
