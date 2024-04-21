
from __future__         import annotations
from abc                import ABC, abstractmethod
import sys
from typing             import List
import os  

import OpenGL.GL as gl

import wgpu
import numpy as np


from Elements.pyECSS.System import System
from Elements.pyECSS.Component import Component, ComponentDecorator, RenderMesh, CompNullIterator
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL.Textures import Texture, Texture3D
import Elements.definitions as definitions


def ShaderLoader(file):
    try:
        f = open(file, 'r')
    except OSError:
        print ("Could not open/read fragment shader file:", file)
        sys.exit()
    with f:
        return f.read() 

# shader_code = ShaderLoader(definitions.SHADER_DIR / "SIGGRAPH" / "Textures" / "simple_texture2.wgsl");
# shader = device.create_shader_module(code=shader_code);

class BasicShader:
    def __init__(self, device:wgpu.GPUDevice):
        self._code = ShaderLoader(definitions.SHADER_DIR / "WGPU" / "base_shader.wgsl")
        self._device = device 
        self._shaderContext = device.create_shader_module(code=self._code);

        self._uniformBuffer = None
        self._uniformDiscriptor = np.dtype([
            ("proj", np.float32, (4, 4)),
            ("view", np.float32, (4, 4)),        
        ]) 

        self._objectBuffer = None
        self._objectDiscriptor = np.dtype([
            ("model", np.float32, (4, 4))
        ])

    def init(self):
        self._uniformBuffer = self._device.create_buffer( 
            size=64 * 2, usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
        )

        self._objectBuffer = self._device.create_buffer(
            size=64 * 1024, usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST
        )

        self.makeFrameGroupLayout()
        self.makeMaterialGroupLayout()
        self.makeFrameGroupBinding()


    def makeFrameGroupBinding(self): 
        self._frameBindingGroup = self._device.create_bind_group(
            layout=self._frameGroupLayout,
            entries=[
                {
                    "binding": 0,
                    "resource": {
                        "buffer": self._uniformBuffer,
                        "offset": 0,
                        "size": self._uniformBuffer.size,
                    },
                },
                { 
                    "binding": 1,
                    "resource": {
                        "buffer": self._objectBuffer,
                        "offset": 0,
                        "size": self._objectBuffer.size,
                    },
                }           
            ])
        

    def makeFrameGroupLayout(self):
        self._frameGroupLayout = self._device.create_bind_group_layout(entries=[
            {
                "binding": 0,
                "visibility": wgpu.ShaderStage.VERTEX | wgpu.ShaderStage.FRAGMENT,
                "buffer": {
                    "type": wgpu.BufferBindingType.uniform
                }
            },
            {
                "binding": 1,
                "visibility": wgpu.ShaderStage.VERTEX | wgpu.ShaderStage.FRAGMENT,
                "buffer": {
                    "type": wgpu.BufferBindingType.read_only_storage,
                }
            }
        ]) 

        return self._frameGroupLayout 
    
    def makeMaterialGroupLayout(self):
        self._materialGourpLayout = self._device.create_bind_group_layout(entries=[
            {
                "binding": 0,
                "visibility": wgpu.ShaderStage.FRAGMENT,
                "texture": {  
                    "sample_type": wgpu.TextureSampleType.float,
                    "view_dimension": wgpu.TextureViewDimension.d2,
                },
            },
            {
                "binding": 1,
                "visibility": wgpu.ShaderStage.FRAGMENT,
                "sampler": {"type": wgpu.SamplerBindingType.filtering},
            }
        ]) 

        return self._materialGourpLayout
