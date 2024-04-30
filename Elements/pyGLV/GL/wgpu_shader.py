
from __future__         import annotations
from abc                import ABC, abstractmethod
import sys
from typing             import List
import os  

import OpenGL.GL as gl

import wgpu
import numpy as np

from Elements.pyGLV.GL.wgpu_meshes import Buffers
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


class Attribute:
    def __init__(self, name:Buffers, rowLength, primitiveType, slot): 
        self.name = name
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

        self.attachedMaterial.uniformGroups[groupName].addSampler(
            name=name,
            sampler=sampler,
            usage=usage,
            compare=compare
        ) 


    def addAtribute(self, name:Buffers, rowLenght:int, primitiveType):   
        slot = len(self.attributes);
        at = Attribute(name, rowLenght, primitiveType, slot) 

        self.attributes.update({name: at})


    def getVertexBufferLayout(self):
        bufferLayout = [] 

        for data in self.attributes.values():
            bufferLayout.append(data.layout) 

        return bufferLayout
    

    def getShader(self):
        return self.context
