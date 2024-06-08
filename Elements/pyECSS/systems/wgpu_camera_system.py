from __future__ import annotations

import glm 
import numpy as np

from Elements.pyECSS.wgpu_system import System 
from Elements.pyECSS.wgpu_entity import Entity 
from Elements.pyECSS.wgpu_components import Component

class CameraControllerSystem(System):
    """
    The system responsible for the cameras.
    """

    def on_create_entity(self, entity: Entity, components: Component | tuple[Component]):
        pass

    def on_update_entity(self, ts, entity: Entity, components: Component | tuple[Component]):
        camera_controller, camera, transform = components

        if InputManager().get_key_down(glfw.MOUSE_BUTTON_2) and camera.primary:
            velocity = camera_controller.movement_speed * ts
            if InputManager().get_key_down(glfw.KEY_W):
                transform.translation += camera_controller.front * velocity
            if InputManager().get_key_down(glfw.KEY_S):
                transform.translation -= camera_controller.front * velocity
            if InputManager().get_key_down(glfw.KEY_A):
                transform.translation -= camera_controller.right * velocity
            if InputManager().get_key_down(glfw.KEY_D):
                transform.translation += camera_controller.right * velocity
            if InputManager().get_key_down(glfw.KEY_E):
                transform.translation -= camera_controller.up * velocity
            if InputManager().get_key_down(glfw.KEY_Q):
                transform.translation += camera_controller.up * velocity

        def on_mouse_move(x, y, width, height) -> None:
            if InputManager().get_key_down(glfw.MOUSE_BUTTON_2) and camera.primary:
                dx = x - camera_controller.prev_mouse_x
                dy = camera_controller.prev_mouse_y - y # reversed since y-coordinates range from bottom to top

                camera_controller.prev_mouse_x = x
                camera_controller.prev_mouse_y = y

                invert_value = -1.0 if self.invert_controls else 1.0

                if dx > 0:
                    dx = invert_value * 50.0 * camera_controller.mouse_sensitivity * ts
                elif dx < 0:
                    dx = invert_value * -50.0 * camera_controller.mouse_sensitivity * ts

                if dy > 0:
                    dy = invert_value * 50.0 * camera_controller.mouse_sensitivity * ts
                elif dy < 0:
                    dy = invert_value * -50.0 * camera_controller.mouse_sensitivity * ts

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
                camera_controller.front = invert_value * glm.normalize(front)

                # Update right and up vectors
                camera_controller.right = invert_value * glm.normalize(glm.cross(camera_controller.front, -camera_controller.world_up))
                camera_controller.up = invert_value * glm.normalize(glm.cross(camera_controller.right, camera_controller.front))

                transform.rotation += glm.vec3(-dy, dx, 0)