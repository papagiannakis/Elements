import wgpu 
import numpy as np
from Elements.pyGLV.GL.wgpu_meshes import Mesh, import_mesh 
from Elements.pyGLV.GL.wgpu_material import Material

class Object:
    def __init__(self, instance_count:int=1):
        self.vertices = None 
        self.indices = None
        self.uvs = None
        self.normals = None

        self.transforms = []  
        self.attachedMaterial:Material = None
        self.instance_count = instance_count;

    def load_mesh_from_obj(self, path:str):
        self.indices, self.vertices, self.uvs, self.normals = import_mesh(path) 

    def init(self, device:wgpu.GPUDevice):
        self.mesh = Mesh(device) 
        if self.vertices.any():  
            self.mesh.setVertices(np.ascontiguousarray(np.array(self.vertices, dtype=np.float32)))
            # self.mesh.setVertices(self.vertices)
        if self.indices.any():  
            self.mesh.setIndices(np.ascontiguousarray(np.array(self.indices, dtype=np.uint32)))
            # self.mesh.setIndices(self.indices)
        if self.uvs.any():  
            self.mesh.setUVs(np.ascontiguousarray(np.array(self.uvs, dtype=np.float32)))
            # self.mesh.setUVs(self.uvs)
        if self.normals.any(): 
            self.mesh.setNormals(np.ascontiguousarray(np.array(self.normals, dtype=np.float32)))
            # self.mesh.setNormals(self.normals)


    def onInit(self):
        raise NotImplementedError();

    def onUpdate(self):
        raise NotImplementedError(); 
