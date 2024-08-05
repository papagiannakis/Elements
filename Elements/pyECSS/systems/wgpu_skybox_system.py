from __future__ import annotations

from Elements.pyECSS.wgpu_system import System 
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyECSS.wgpu_components import Component, SkyboxComponent
from Elements.pyGLV.GL.wgpu_shader_types import * 
from Elements.pyGLV.GL.wgpu_texture import Texture, TextureLib

import glm  
import re 
import wgpu 
import sys

class SkyboxSystem(System): 
    """
    The system responsible for managing skybox components.
    """

    def on_create(self, entity: Entity, components: Component | list[Component]):
        """
        Initializes the skybox component for an entity.

        :param entity: The entity being created.
        :param components: The components associated with the entity, expected to include a skybox component.
        """

        skybox:SkyboxComponent = components
        
        TextureLib().make_skybox(skybox.gpu_texture_name, skybox.paths)

    def on_update(self, ts, entity: Entity, components: Component | list[Component], event):
        """
        Updates the skybox component for an entity. This method currently does nothing and is a placeholder for future updates.

        :param ts: Time step for the update.
        :param entity: The entity being updated.
        :param components: The components associated with the entity.
        :param event: The event triggering the update.
        """
        pass