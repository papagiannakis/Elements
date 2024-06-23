from __future__ import annotations 

import glm 
import numpy as np 
import trimesh 
import wgpu

from Elements.pyECSS.wgpu_system import System 
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyECSS.wgpu_components import Component, MeshComponent 
from Elements.pyECSS.math_utilities import compute_tangent_space

from Elements.pyGLV.GUI.wgpu_cache_manager import GpuController

class MeshSystem(System):  

    def import_mesh(self, path:str):
        mesh = trimesh.load(file_obj=path, force='mesh')  

        vertices = np.ascontiguousarray(mesh.vertices, dtype=np.float32) 
        uvs = np.ascontiguousarray(mesh.visual.uv, dtype=np.float32) 
        indices = np.ascontiguousarray(mesh.faces.flatten(), dtype=np.uint32)  
        normals = np.ascontiguousarray(mesh.vertex_normals, dtype=np.float32) 

        tangents, bitangent = compute_tangent_space(vertices, normals, uvs, indices)   
        tangents = np.ascontiguousarray(tangents, dtype=np.float32)
        bitangent = np.ascontiguousarray(bitangent, dtype=np.float32)

        return indices, vertices, uvs, normals, tangents, bitangent
    
    def createBuffer(self, data:np.ndarray): 
        buffer = GpuController().device.create_buffer_with_data(
            data=data, usage=wgpu.BufferUsage.VERTEX
        )  
        return buffer
    
    def createIndexBuffer(self, data:np.ndarray):
        buffer = GpuController().device.create_buffer_with_data(
            data=data, usage=wgpu.BufferUsage.INDEX
        )   
        return buffer
 
    def on_create(self, entity: Entity, components: Component | list[Component]):
        mesh = components 

        if mesh.type is MeshComponent.Type.IMPORT and mesh.import_path is not None:
            mesh.indices, mesh.vertices, mesh.uvs, mesh.normals, mesh.Tangents, mesh.Bitangents = self.import_mesh(mesh.import_path) 
            
        if mesh.vertices is not None:   
            mesh.vertices_num = len(mesh.vertices)
            mesh.buffer_map.update({MeshComponent.Buffers.VERTEX.value: self.createBuffer(mesh.vertices)})
        if mesh.indices is not None: 
            mesh.indices_num= len(mesh.indices)
            mesh.buffer_map.update({MeshComponent.Buffers.INDEX.value: self.createIndexBuffer(mesh.indices)})
        if mesh.uvs is not None:  
            mesh.buffer_map.update({MeshComponent.Buffers.UV.value: self.createBuffer(mesh.uvs)})
        if mesh.normals is not None: 
            mesh.buffer_map.update({MeshComponent.Buffers.NORMAL.value: self.createBuffer(mesh.normals)})
        if mesh.Tangents is not None:
            mesh.buffer_map.update({MeshComponent.Buffers.TANGENT.value: self.createBuffer(mesh.Tangents)})
        if mesh.Bitangents is not None: 
            mesh.buffer_map.update({MeshComponent.Buffers.TANGENT.value: self.createBuffer(mesh.Bitangents)})  

    def on_update(self, ts, entity: Entity, components: Component | list[Component], event):  
        pass 


if __name__ == "__main__": 
    print(MeshComponent.Buffers.VERTEX == "a_vertices") 