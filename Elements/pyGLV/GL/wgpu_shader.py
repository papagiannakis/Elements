
from __future__         import annotations
from abc                import ABC, abstractmethod
import sys
from typing             import List
import os   
import re

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
                    viewDimention:any=wgpu.TextureViewDimension.d2
    ):

        self.attachedMaterial.uniformGroups[groupName].addTexture(
            name=name,
            value=value,
            usage=usage, 
            sampleType=sampleType, 
            dimension=dimension,
            viewDimention=viewDimention
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
    
    def extract_group_id(self):
        # Match the @group annotation and capture the group ID
        group_pattern = re.compile(r'@group\((\d+)\)')
        groups = group_pattern.findall(self.code)
        
        # Use a set to store unique group IDs
        unique_group_ids = set(groups) 
        unique_group_ids = sorted(unique_group_ids)
        
        return unique_group_ids

    def attribute_dispatch(self, attr):
        if attr == "a_pos": 
            return Buffers.VERTEX
        elif attr == "a_uv": 
            return Buffers.UV
        elif attr == "a_normal": 
            return Buffers.NORMAL
        elif attr == "a_tangent": 
            return Buffers.TANGENT
        elif attr == "a_bitangent": 
            return Buffers.BITANGENT 
        else: 
            return None

    def extract_attributes(self):
        # Match the entire function definition
        function_pattern = re.compile(r'@vertex\s*fn\s*vs_main\s*\((.*?)\)\s*->\s*Fragment', re.DOTALL)
        match = function_pattern.search(self.code)
        if not match:
            return []

        # Extract the attributes part
        attributes_part = match.group(1)

        # Match each attribute inside the function definition
        attribute_pattern = re.compile(r'@location\((\d+)\)\s+([\w_]+):\s+([\w_]+)')
        attributes = attribute_pattern.findall(attributes_part)
        
        return attributes 

    def extract_struct(self, struct_name):
        # Regex pattern to match the struct with colon-separated attributes and comma at the end
        struct_pattern = rf"struct {struct_name} {{(.*?)}};"
        
        # Use re.DOTALL to match newlines
        match = re.search(struct_pattern, self.code, re.DOTALL)
        
        if match:
            # Extract the content inside the struct
            content = match.group(1).strip()
            # Remove colons and commas from the content and split by whitespace
            attributes_and_types = re.split(r'[:,]\s*', content)
            # Remove any empty strings from the list
            attributes_and_types = [item for item in attributes_and_types if item.strip()]
            # Group attributes and types
            attribute_type_pairs = [attributes_and_types[i:i+2] for i in range(0, len(attributes_and_types), 2)]
            return attribute_type_pairs
        else:
            return None
        
    def separate_type_and_precision(self, type_str):
        match = re.match(r'([a-zA-Z0-9]+)([fi])', type_str)
        if match:  
            precision = None
            if match.group(2) == "i": 
                precision = I32 
            else: 
                precision = F32

            return precision
        else:
            return None
        
    def extract_storage_read_variables(self):
        variable_pattern = r'@binding\(\d+\) @group\(\d+\) var<storage, read> ([\w\d_]+): array<(\w+)>;'
        variables = re.findall(variable_pattern, self.code)
        return variables

    def extract_samplers(self):
        # Define a regex pattern to match the sampler declarations
        sampler_pattern = re.compile(r'@binding\(\d+\) @group\(\d+\) var ([\w_]+): (sampler.*);')
        samplers = sampler_pattern.findall(self.code)
        return samplers

    def extract_textures(self):
        # Define a regex pattern to match the texture declarations
        texture_pattern = re.compile(r'@binding\(\d+\) @group\(\d+\) var ([\w_]+): (texture_.*);')
        textures = texture_pattern.findall(self.code)
        return textures