import wgpu
import trimesh
import numpy as np  
from enum import Enum

from Elements.definitions import MODEL_DIR 

class Buffers(Enum):
    VERTEX = 1
    INDEX = 2
    UV = 3
    NORMAL = 4 
    COLOR = 5 
    TANGENT = 6
    BITANGENT = 7

def compute_tangent_space(vertices, normals, uvs, indices):
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


def import_mesh(path:str):
    mesh = trimesh.load(file_obj=path, force='mesh')  

    vertices = np.array(mesh.vertices, dtype=np.float32) 
    uvs = np.array(mesh.visual.uv, dtype=np.float32) 
    indices = np.array(mesh.faces.flatten(), dtype=np.uint32)  
    normals = np.array(mesh.vertex_normals, dtype=np.float32) 

    tangents, bitangent = compute_tangent_space(vertices, normals, uvs, indices)   
    tangents = np.array(tangents, dtype=np.float32)
    bitangent = np.array(bitangent, dtype=np.float32)

    return indices, vertices, uvs, normals, tangents, bitangent


class Mesh:
    def __init__(self, device:wgpu.GPUDevice):
        self.device = device 
        self.numVertices = any
        self.numIndices = any
        self.hasIndices: bool = False; 

        self.bufferMap = {}

    def setVertices(self, vertices:np.ndarray):
        self.numVertices = len(vertices)   
        self.createBuffer(vertices, Buffers.VERTEX)

    def setIndices(self, indices:np.ndarray):
        self.numIndices = len(indices)  
        self.hasIndices = True 
        self.createIndexBuffer(indices, Buffers.INDEX) 

    def setNormals(self, normals:np.ndarray): 
        self.createBuffer(normals, Buffers.NORMAL)  

    def setColors(self, colors:np.ndarray):
        self.createBuffer(colors, Buffers.COLOR)   

    def setUVs(self, uvs:np.ndarray):
        self.createBuffer(uvs, Buffers.UV) 

    def setTangent(self, tan:np.ndarray):
        self.createBuffer(tan, Buffers.TANGENT)

    def setBitangent(self, tan:np.ndarray):
        self.createBuffer(tan, Buffers.BITANGENT) 

    def createBuffer(self, data:np.ndarray, name:Buffers): 
        buffer = self.device.create_buffer_with_data(
            data=data, usage=wgpu.BufferUsage.VERTEX
        ) 
        self.bufferMap.update({name: buffer})  
    
    def createIndexBuffer(self, data:np.ndarray, name:Buffers):
        buffer = self.device.create_buffer_with_data(
            data=data, usage=wgpu.BufferUsage.INDEX
        ) 
        self.bufferMap.update({name: buffer})   

    def getBufferByName(self, name:Buffers):
        return self.bufferMap.get(name)

    def updateBuffer(self, name:Buffers, data:np.ndarray): 
        buffer = self.getBufferByName(name) 
        buffer.destroy()
        del self.bufferMap[name] 
        self.createBuffer(name, data)


if __name__ == "__main__":
    indices, vertices, uvs, normals, tangents, bitangent = import_mesh(MODEL_DIR / "stronghold" / "source" / "Stronghold.obj")
    print(len(indices))
    print(len(vertices))
    print(len(uvs))
    print(len(normals))
    print(len(tangents))
    print(len(bitangent))
