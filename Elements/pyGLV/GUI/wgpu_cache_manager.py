import wgpu
import glm
import numpy as np   
from enum import Enum

from Elements.pyGLV.GL.wgpu_meshes import Buffers 
from Elements.pyGLV.GUI.RenderPasses.ModelPass import ModelPass 
from Elements.pyGLV.GUI.RenderPasses.ShadowMapPass import ShadowMapPass


class GpuCache:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            print('Creating Gpu cache Singleton Object')
            cls._instance = super(GpuCache, cls).__new__(cls) 

            cls.device: wgpu.GPUDevice = None 
            cls.adapter: wgpu.GPUAdapter = None

            cls.present_context = None
            cls.render_texture_format = None

            cls.imported_canvas_size: list[int] = None 
            cls.active_canvas_size: list[int] = None 
            cls.canvas_texture: wgpu.GPUTexture = None 
            cls.canvas_texture_view: wgpu.GPUTextureView = None 
            cls.canvas_texture_sampler: wgpu.GPUSampler = None
            cls.canvas_texture_depth: wgpu.GPUTexture = None 
            cls.canvas_texture_depth_view: wgpu.GPUTextureView = None 
            cls.canvas_texture_depht_sampler: wgpu.GPUSampler = None

            cls.shadow_depth_texture: wgpu.GPUTexture  = None  
            cls.shadow_depth_texture_view: wgpu.GPUTextureView = None
            cls.shadow_depth_texture_sampler: wgpu.GPUTextureView = None

        return cls._instance
    
    def __init__(self):
        None;  

    def set_adapter_device(self, adapter, device):
        self.device = device
        self.adapter = adapter
