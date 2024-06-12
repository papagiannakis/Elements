import wgpu
import glm
import numpy as np   
from enum import Enum

from Elements.pyGLV.GL.wgpu_meshes import Buffers 
from Elements.pyGLV.GUI.RenderPasses.ModelPass import ModelPass 
from Elements.pyGLV.GUI.RenderPasses.ShadowMapPass import ShadowMapPass

RENDER_PASSES = []

class Renderer:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            print('Creating Renderer Singleton Object')
            cls._instance = super(Renderer, cls).__new__(cls) 

            cls._scene = None
            cls._device = None
            cls._present_context = None 
            cls._shadowMapDepthTexture = None
            cls._shadowMapDepthTextureView = None

        return cls._instance
    
    def __init__(self):
        None; 

    def init(self, scene=None, device=None, present_context=None):  
        self._scene = scene
        self._device = device
        self._present_context = present_context  
        self._canvasContextFormat = self._present_context.get_preferred_format(self._device.adapter) 

        self._scene.init(device=self._device) 

    def render(self):  
        self._canvasContext = self._present_context.get_current_texture();   
        command_encoder = self._device.create_command_encoder()

        for renderPass in RENDER_PASSES: 
            renderPass.value.onInit(command_encoder)
            renderPass.value.render(command_encoder)  

        self._device.queue.submit([command_encoder.finish()]) 
        self._canvasContext = None;


class PASS(Enum):
    MODEL = ModelPass(renderer=Renderer()) 
    SHADOW = ShadowMapPass(renderer=Renderer())
