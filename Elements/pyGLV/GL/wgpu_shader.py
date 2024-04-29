
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
from Elements.pyGLV.GL.wgpu_uniform_groups import UniformGroup
import Elements.definitions as definitions 
from Elements.pyGLV.GL.wgpu_shader_types import SHADER_TYPE_BUFFER_STRIDE, SHADER_TYPES, F32, I32


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

class Attribute:
    def __init__(self, rowLength, primitiveType, slot):
        self.rowLength = rowLength
        self.primitiveBytes = primitiveType
        self.slot = slot

        self.layout = self.makeLayout()
 
    def makeLayout(self): 
        return  {
                    "array_stride": self.rowLength * self.primitiveBytes,
                    "step_mode": wgpu.VertexStepMode.vertex,
                    "attributes": [
                        {
                            "format": SHADER_TYPE_BUFFER_STRIDE[self.rowLength],
                            "offset": 0,
                            "shader_location": self.slot,
                        },
                    ],
                } 
    


class Shader:
    def __init__(self): 
        self.context = None 
        self.code = None
        self.attributes = {}
        self.attachedMaterial = None

    def init(self):
        raise NotImplementedError()
    
    def addUniform(self, 
                   name:str,
                   groupName:str, 
                   size:int,
                   offset:int,
                   value:any=None, 
                   usage:any=wgpu.BufferUsage.VERTEX | wgpu.ShaderStage.FRAGMENT, 
                   type:any=wgpu.BufferBindingType.uniform
    ): 
        # if self.attachedMaterial.uniformGroups.get("frameGroup") is None: 
        #     # self.attachedMaterial.uniformGroups["frameGroup"] = UniformGroup("frameGroup", 0)  
        #     self.attachedMaterial.uniformGroups.update({"frameGroup": UniformGroup("frameGroup", 0)})  
        
        self.attachedMaterial.uniformGroups[groupName].addUniform(
            name=name,
            data=value,
            size=size,
            offset=offset,
            usage=usage,
            type=type
        ) 

    def addStorage(self,
                   name:str, 
                   groupName:str,
                   size:int,
                   data:any=None, 
                   usage:any=wgpu.BufferUsage.VERTEX | wgpu.ShaderStage.FRAGMENT, 
                   type:any=wgpu.BufferBindingType.read_only_storage,
    ): 
        # if self.attachedMaterial.uniformGroups.get("frameGroup") is None: 
        #     self.attachedMaterial.uniformGroups["frameGroup"] = UniformGroup("frameGroup", 0) 
        
        self.attachedMaterial.uniformGroups[groupName].addStorage(
            name=name,
            data=data,
            size=size,
            usage=usage,
            type=type
        )

    def addTexture(self,
                    name:str,
                    groupName:str,
                    value:Texture=None,
                    usage:any=wgpu.ShaderStage.FRAGMENT,
                    sampleType:any=wgpu.TextureSampleType.float,
                    dimension:any=wgpu.TextureViewDimension.d2,
    ):
        # if self.attachedMaterial.uniformGroups.get("materialGroup") is None: 
        #     self.attachedMaterial.uniformGroups["materialGroup"] = UniformGroup("materialGroup", 1) 

        self.attachedMaterial.uniformGroups[groupName].addTexture(
            name=name,
            value=value,
            usage=usage, 
            sampleType=sampleType, 
            dimension=dimension
        ) 

    def addSampler(self,
                  name:str, 
                  groupName:str, 
                  sampler:any,
                  usage:any=wgpu.ShaderStage.FRAGMENT,
                  compare=False
    ):
        # if self.attachedMaterial.uniformGroups.get("materialGroup") is None: 
        #     self.attachedMaterial.uniformGroups["materialGroup"] = UniformGroup("materialGroup", 1) 

        self.attachedMaterial.uniformGroups[groupName].addSampler(
            name=name,
            sampler=sampler,
            usage=usage,
            compare=compare
        ) 


    def addAtribute(self, name:str, rowLenght:int, primitiveType):   
        slot = len(self.attributes);
        at = Attribute(rowLenght, primitiveType, slot) 

        # self.attributes[name] = at  
        self.attributes.update({name: at})


    def getVertexBufferLayout(self):
        bufferLayout = [] 

        for key, data in self.attributes.items():
            bufferLayout.append(data.layout) 

        return bufferLayout
    

    def getShader(self):
        return self.context

# class BasicShader:
#     def __init__(self, device:wgpu.GPUDevice):
#         self._code = ShaderLoader(definitions.SHADER_DIR / "WGPU" / "base_shader.wgsl")
#         self._device = device 
#         self._shaderContext = device.create_shader_module(code=self._code);

#         self._uniformBuffer = None
#         self._uniformDiscriptor = np.dtype([
#             ("proj", np.float32, (4, 4)),
#             ("view", np.float32, (4, 4)),        
#         ]) 

#         self._objectBuffer = None
#         self._objectDiscriptor = np.dtype([
#             ("model", np.float32, (4, 4))
#         ])

#     def init(self):
#         self._uniformBuffer = self._device.create_buffer( 
#             size=64 * 2, usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST
#         )

#         self._objectBuffer = self._device.create_buffer(
#             size=64 * 1024, usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST
#         )

#         self.makeFrameGroupLayout()
#         self.makeMaterialGroupLayout()
#         self.makeFrameGroupBinding()


#     def makeFrameGroupBinding(self): 
#         self._frameBindingGroup = self._device.create_bind_group(
#             layout=self._frameGroupLayout,
#             entries=[
#                 {
#                     "binding": 0,
#                     "resource": {
#                         "buffer": self._uniformBuffer,
#                         "offset": 0,
#                         "size": self._uniformBuffer.size,
#                     },
#                 },
#                 { 
#                     "binding": 1,
#                     "resource": {
#                         "buffer": self._objectBuffer,
#                         "offset": 0,
#                         "size": self._objectBuffer.size,
#                     },
#                 }           
#             ])
        

#     def makeFrameGroupLayout(self):
#         self._frameGroupLayout = self._device.create_bind_group_layout(entries=[
#             {
#                 "binding": 0,
#                 "visibility": wgpu.ShaderStage.VERTEX | wgpu.ShaderStage.FRAGMENT,
#                 "buffer": {
#                     "type": wgpu.BufferBindingType.uniform
#                 }
#             },
#             {
#                 "binding": 1,
#                 "visibility": wgpu.ShaderStage.VERTEX | wgpu.ShaderStage.FRAGMENT,
#                 "buffer": {
#                     "type": wgpu.BufferBindingType.read_only_storage,
#                 }
#             }
#         ]) 

#         return self._frameGroupLayout 
    
#     def makeMaterialGroupLayout(self):
#         self._materialGourpLayout = self._device.create_bind_group_layout(entries=[
#             {
#                 "binding": 0,
#                 "visibility": wgpu.ShaderStage.FRAGMENT,
#                 "texture": {  
#                     "sample_type": wgpu.TextureSampleType.float,
#                     "view_dimension": wgpu.TextureViewDimension.d2,
#                 },
#             },
#             {
#                 "binding": 1,
#                 "visibility": wgpu.ShaderStage.FRAGMENT,
#                 "sampler": {"type": wgpu.SamplerBindingType.filtering},
#             }
#         ]) 

#         return self._materialGourpLayout
