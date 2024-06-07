from Elements.pyECSS.wgpu_entity import Entity 

import glm

class Component(object):  
    def __init__(self):
        self.is_active = True;

class InfoComponent(Component):
    def __init__(self, tag:str): 
        self.tag = tag

class TransformComponent(Component):
    def __init__(self, translation: glm.vec3, rotation: glm.vec3, scale: glm.vec3): 
        self.T = translation
        self.R = rotation 
        self.S = scale 

        self.world = glm.mat4(1) 

    def get_world_position(self) -> glm.vec3: 
        return (self.world * glm.vec4(self.T, 1.0)).xyz;