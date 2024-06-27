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
    def on_create(self, entity: Entity, components: Component | list[Component]):  
        skybox:SkyboxComponent = components
        
        TextureLib().make_skybox(skybox.gpu_texture_name, skybox.paths)

    def on_update(self, ts, entity: Entity, components: Component | list[Component], event): 
        pass