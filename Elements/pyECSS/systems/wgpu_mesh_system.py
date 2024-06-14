from __future__ import annotations 

import glm 
import numpy as np 
import trimesh 
import wgpu

from Elements.pyECSS.wgpu_system import System 
from Elements.pyECSS.wgpu_entity import Entity
from Elements.pyECSS.wgpu_components import Component, MeshComponent

from Elements.pyGLV.GUI.wgpu_cache_manager import GpuCache

class TransformSystem(System):  
    def compute_tangent_space(self, vertices, normals, uvs, indices):
        num_verts = len(vertices)
        num_faces = len(indices) // 3
        
        # Initialize tangent and bitangent arrays
        tangents = np.zeros((num_verts, 3))
        bitangents = np.zeros((num_verts, 3))
        
        # Iterate over each face
        for i in range(num_faces):
            i1, i2, i3 = indices[i * 3], indices[i * 3 + 1], indices[i * 3 + 2]
            v1, v2, v3 = vertices[i1], vertices[i2], vertices[i3]
            uv1, uv2, uv3 = uvs[i1], uvs[i2], uvs[i3]
            
            delta_pos1 = v2 - v1
            delta_pos2 = v3 - v1
            delta_uv1 = uv2 - uv1
            delta_uv2 = uv3 - uv1
            
            # Check for zero division
            det = delta_uv1[0] * delta_uv2[1] - delta_uv1[1] * delta_uv2[0]
            if det == 0:
                continue
            
            r = 1.0 / det
            
            # Calculate tangent and bitangent for this face
            tangent = (delta_pos1 * delta_uv2[1] - delta_pos2 * delta_uv1[1]) * r
            bitangent = (delta_pos2 * delta_uv1[0] - delta_pos1 * delta_uv2[0]) * r
            
            # Accumulate tangent and bitangent to each vertex of this face
            tangents[i1] += tangent
            tangents[i2] += tangent
            tangents[i3] += tangent
            bitangents[i1] += bitangent
            bitangents[i2] += bitangent
            bitangents[i3] += bitangent
        
        # Gram-Schmidt orthogonalize and normalize the tangent and bitangent vectors
        for i in range(num_verts):
            normal = normals[i]
            tangent = tangents[i]
            bitangent = bitangents[i]
            
            # Gram-Schmidt orthogonalization
            tangent -= np.dot(normal, tangent) * normal
            bitangent -= np.dot(normal, bitangent) * normal
            bitangent -= np.dot(tangent, bitangent) * tangent
            
            # Normalize
            tangent_norm = np.linalg.norm(tangent)
            bitangent_norm = np.linalg.norm(bitangent)
            
            if tangent_norm != 0:
                tangent /= tangent_norm
            if bitangent_norm != 0:
                bitangent /= bitangent_norm
            
            tangents[i] = tangent
            bitangents[i] = bitangent
        
        return tangents, bitangents


    def import_mesh(self, path:str):
        mesh = trimesh.load(file_obj=path, force='mesh')  

        vertices = np.ascontiguousarray(mesh.vertices, dtype=np.float32) 
        uvs = np.ascontiguousarray(mesh.visual.uv, dtype=np.float32) 
        indices = np.ascontiguousarray(mesh.faces.flatten(), dtype=np.uint32)  
        normals = np.ascontiguousarray(mesh.vertex_normals, dtype=np.float32) 

        tangents, bitangent = self.compute_tangent_space(vertices, normals, uvs, indices)   
        tangents = np.ascontiguousarray(tangents, dtype=np.float32)
        bitangent = np.ascontiguousarray(bitangent, dtype=np.float32)

        return indices, vertices, uvs, normals, tangents, bitangent
    
    def createBuffer(self, data:np.ndarray): 
        buffer = GpuCache().device.create_buffer_with_data(
            data=data, usage=wgpu.BufferUsage.VERTEX
        )  
        return buffer
    
    def createIndexBuffer(self, data:np.ndarray):
        buffer = GpuCache().device.create_buffer_with_data(
            data=data, usage=wgpu.BufferUsage.INDEX
        )   
        return buffer
 
    def on_create(self, entity: Entity, components: Component | list[Component]):
        mesh = components 

        if mesh.type is MeshComponent.Type.IMPORT and mesh.import_path is not None:
            mesh.indices, mesh.vertices, mesh.uvs, mesh.normals, mesh.Tangents, mesh.Bitangents = self.import_mesh(mesh.import_path) 
            
        if mesh.vertices is not None:   
            mesh.vertices_num = len(mesh.vertices)
            mesh.buffer_map.update({MeshComponent.Buffers.VERTEX: self.createBuffer(mesh.vertices)})
        if mesh.indices is not None: 
            mesh.indices_num= len(mesh.indices)
            mesh.buffer_map.update({MeshComponent.Buffers.INDEX: self.createIndexBuffer(mesh.indices)})
        if mesh.uvs is not None:  
            mesh.buffer_map.update({MeshComponent.Buffers.UV: self.createBuffer(mesh.uvs)})
        if mesh.normals is not None: 
            mesh.buffer_map.update({MeshComponent.Buffers.NORMAL: self.createBuffer(mesh.normals)})
        if mesh.Tangents is not None:
            mesh.buffer_map.update({MeshComponent.Buffers.TANGENT: self.createBuffer(mesh.Tangents)})
        if mesh.Bitangents is not None: 
            mesh.buffer_map.update({MeshComponent.Buffers.TANGENT: self.createBuffer(mesh.Bitangents)})  

    def on_update(self, entity: Entity, components: Component | list[Component], event):  
        pass