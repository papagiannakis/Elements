import glm 

from enum import Enum
from Elements.pyECSS.wgpu_entity import Entity 

class Component(object):  
    def __init__(self):
        self.is_active = True;

class InfoComponent(Component):
    def __init__(self, tag:str): 
        self.tag = tag

class TransformComponent(Component):
    def __init__(self, translation: glm.vec3, rotation: glm.vec3, scale: glm.vec3):
        self.translation = translation
        self.rotation = rotation
        self.scale = scale

        self.local_matrix = glm.mat4(1.0)
        self.world_matrix = glm.mat4(1.0)
        self.quaternion = glm.quat()

        self.static = False
    
    def get_world_position(self) -> glm.vec3:
        return (self.world_matrix * glm.vec4(self.translation, 1.0)).xyz 
    
class CameraComponent(Component):
    class Type(Enum):
        PERSPECTIVE = 1
        ORTHOGRAPHIC = 2

    def __init__(self, fov, aspect_ratio, near, far, zoom_level, type: Type, primary = True):
        self.zoom_level = zoom_level
        self.fov = fov
        self.near = near
        self.far = far
        self.aspect_ratio = aspect_ratio
        self.type: CameraComponent.Type = type

        self.view = glm.mat4(1.0)
        if type is CameraComponent.Type.ORTHOGRAPHIC:
            self.projection = glm.ortho(-self.aspect_ratio * self.zoom_level, self.aspect_ratio * self.zoom_level, -self.zoom_level, self.zoom_level, self.near, self.far)
        elif type is CameraComponent.Type.PERSPECTIVE:
            self.projection = glm.perspective(glm.radians(self.fov), self.aspect_ratio, self.near, self.far)
        self.view_projection = glm.mat4(1.0)

class CameraControllerComponent(Component):
    def __init__(self, movement_speed = 3.5, mouse_sensitivity = 1.25):
        self.front = glm.vec3(0.0, 0.0, 1.0)
        self.right = glm.vec3(1.0, 0.0, 0.0)
        self.up = glm.vec3(0.0, 1.0, 0.0)
        self.world_up = glm.vec3(0.0, 1.0, 0.0)
        self.yaw = -90.0
        self.pitch = 0.0
        self.movement_speed = movement_speed
        self.mouse_sensitivity = mouse_sensitivity
        self.zoom = 45.0
        self.prev_mouse_x = 0.0
        self.prev_mouse_y = 0.0