import wgpu
import trimesh
import numpy as np

from Elements.definitions import MODEL_DIR

def import_mesh(path:str):
    mesh = trimesh.load(file_obj=path, force='mesh') 

    vertices = np.array(mesh.vertices, dtype=np.float32) 
    uvs = np.array(mesh.visual.uv, dtype=np.float32) 
    indices = np.array(mesh.faces.flatten(), dtype=np.uint32)  
    normals = np.array(mesh.vertex_normals, dtype=np.float32)

    return indices, vertices, uvs, normals

class Mesh:
    def __init__(self, device:wgpu.GPUDevice):
        self.device = device 
        self.numVertices = any
        self.numIndices = any
        self.hasIndices: bool = True; 

        self.bufferMap = {}

    def setVertices(self, vertices:np.ndarray):
        self.numVertices = len(vertices)   
        self.createBuffer(vertices, "vertices") 

    def setIndices(self, indices:np.ndarray):
        self.numIndices = len(indices)  
        self.hasIndices = True 
        self.createIndexBuffer(indices, "indices") 

    def setNormals(self, normals:np.ndarray): 
        self.createBuffer(normals, "normals")  

    def setColors(self, colors:np.ndarray):
        self.createBuffer(colors, "normals")   

    def setUVs(self, uvs:np.ndarray):
        self.createBuffer(uvs, "uvs")

    def createBuffer(self, data:np.ndarray, name:str):
        buffer = self.device.create_buffer_with_data(
            data=data, usage=wgpu.BufferUsage.VERTEX
        ) 
        self.bufferMap.update({name: buffer})  
    
    def createIndexBuffer(self, data:np.ndarray, name:str):
        buffer = self.device.create_buffer_with_data(
            data=data, usage=wgpu.BufferUsage.INDEX
        ) 
        self.bufferMap.update({name: buffer})   

    def getBufferByName(self, name:str):
        return self.bufferMap.get(name)

    def updateBuffer(self, name:str, data:np.ndarray): 
        buffer = self.getBufferByName(name) 
        buffer.destroy()
        del self.bufferMap[name] 
        self.createBuffer(name, data)


if __name__ == "__main__":
    m = import_mesh(MODEL_DIR / "Scalpel" / "Scalpel.obj")

    print(m)
