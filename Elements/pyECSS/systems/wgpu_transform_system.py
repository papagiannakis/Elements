from __future__ import annotations 

import glm

from Elements.pyECSS.wgpu_system import System 
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyECSS.wgpu_components import Component

class TransformSystem(System): 
 
    def on_create(self, entity: Entity, components: Component | list[Component]): 
        transform = components

        T = glm.translate(glm.mat4(1.0), glm.vec3(transform.translation.x, transform.translation.y, transform.translation.z))
        R = glm.quat(glm.vec3(glm.radians(transform.rotation.x), glm.radians(transform.rotation.y), glm.radians(transform.rotation.z)))
        S = glm.scale(glm.mat4(1.0), glm.vec3(transform.scale.x, transform.scale.y, transform.scale.z))

        transform.quaternion = R        
        transform.local_matrix = T * glm.mat4(R) * S
        transform.world_matrix = transform.local_matrix

    def on_update(self, entity: Entity, components: Component | list[Component]): 
        transform = components

        if not transform.static:
            T = glm.translate(glm.mat4(1.0), glm.vec3(transform.translation.x, transform.translation.y, transform.translation.z))
            R = glm.quat(glm.vec3(glm.radians(transform.rotation.x), glm.radians(transform.rotation.y), glm.radians(transform.rotation.z)))
            S = glm.scale(glm.mat4(1.0), glm.vec3(transform.scale.x, transform.scale.y, transform.scale.z))
            
            transform.quaternion = R
            transform.local_matrix = T * glm.mat4(R) * S
            transform.world_matrix = transform.local_matrix        