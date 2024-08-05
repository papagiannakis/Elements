from __future__ import annotations

import glm  
import glfw
import numpy as np

from Elements.pyECSS.wgpu_system import System 
from Elements.pyECSS.wgpu_entity import Entity 
from Elements.pyECSS.wgpu_components import Component 
from Elements.pyGLV.GUI.Input_manager import InputManager 
from Elements.pyGLV.GUI.Viewer import EventTypes, button_map

class CameraControllerSystem(System):
    """
    System responsible for handling camera controls.
    """

    def on_create(self, entity: Entity, components: Component | tuple[Component]): 
        """
        Initialize the camera controller system for the given entity.
        
        :param entity: The entity being created.
        :param components: The components associated with the entity.
        """
        pass

    def on_update(self, ts, entity: Entity, components: Component | tuple[Component], event):
        """
        Update the camera position and orientation based on user input.

        :param ts: Time step for the update.
        :param entity: The entity being updated.
        :param components: The components associated with the entity.
        :param event: The event triggering the update.
        """

        camera_controller, camera, transform = components  

        if InputManager().is_button_pressed(2):
            velocity = camera_controller.movement_speed * ts
            if InputManager().is_key_pressed('W'):
                transform.translation += camera_controller.front * velocity
            if InputManager().is_key_pressed('S'):
                transform.translation -= camera_controller.front * velocity
            if InputManager().is_key_pressed('A'):
                transform.translation -= camera_controller.right * velocity
            if InputManager().is_key_pressed('D'):
                transform.translation += camera_controller.right * velocity 
            if InputManager().is_key_pressed('E'):
                transform.translation -= camera_controller.up * velocity
            if InputManager().is_key_pressed('Q'):
                transform.translation += camera_controller.up * velocity

        if event and event.type == EventTypes.MOUSE_MOTION:     
            if InputManager().is_button_pressed(2):
                x = event.data["x"] 
                y = event.data["y"]   

                dx = x - camera_controller.prev_mouse_x
                dy = y - camera_controller.prev_mouse_y

                camera_controller.prev_mouse_x = x
                camera_controller.prev_mouse_y = y

                if dx > 0:
                    dx = -50.0 * camera_controller.mouse_sensitivity * ts
                elif dx < 0:
                    dx = 50.0 * camera_controller.mouse_sensitivity * ts

                if dy > 0:
                    dy = -50.0 * camera_controller.mouse_sensitivity * ts
                elif dy < 0:
                    dy = 50.0 * camera_controller.mouse_sensitivity * ts

                camera_controller.yaw += dx
                camera_controller.pitch += dy

                if camera_controller.pitch > 89.0:
                    camera_controller.pitch = 89.0
                if camera_controller.pitch < -89.0:
                    camera_controller.pitch = -89.0

                # Update front vector
                front = glm.vec3()
                front.x = glm.cos(glm.radians(camera_controller.yaw)) * glm.cos(glm.radians(camera_controller.pitch))
                front.y = glm.sin(glm.radians(camera_controller.pitch))
                front.z = glm.sin(glm.radians(-camera_controller.yaw)) * glm.cos(glm.radians(camera_controller.pitch))
                camera_controller.front = -1 * glm.normalize(front)

                # Update right and up vectors
                camera_controller.right = -1 * glm.normalize(glm.cross(camera_controller.front, -camera_controller.world_up))
                camera_controller.up = -1 * glm.normalize(glm.cross(camera_controller.right, camera_controller.front))

                transform.rotation += glm.vec3(-dy, dx, 0)