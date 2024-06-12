import wgpu
import glm
import numpy as np   
from enum import Enum

from Elements.pyGLV.GL.wgpu_meshes import Buffers 
from Elements.pyGLV.GUI.RenderPasses.ModelPass import ModelPass 
from Elements.pyGLV.GUI.RenderPasses.ShadowMapPass import ShadowMapPass


class GpuCache:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            print('Creating Gpu cache Singleton Object')
            cls._instance = super(GpuCache, cls).__new__(cls) 

            cls.canvas_texture = None
            cls.canvas_texture_depth = None
            cls.shadow_texture = None

        return cls._instance
    
    def __init__(self):
        None; 
