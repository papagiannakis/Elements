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
        self.Tangents = None 
        self.Bitangents = None

        self.transforms = []  
        self.attachedMaterial:Material = None
        self.instance_count = instance_count;

    def load_mesh_from_obj(self, path:str):
        self.indices, self.vertices, self.uvs, self.normals, self.Tangents, self.Bitangents = import_mesh(path) 

    def init(self, device:wgpu.GPUDevice):
        self.mesh = Mesh(device) 
        if self.vertices is not None:  
            self.mesh.setVertices(np.ascontiguousarray(np.array(self.vertices, dtype=np.float32)))
        if self.indices is not None:  
            self.mesh.setIndices(np.ascontiguousarray(np.array(self.indices, dtype=np.uint32)))
        if self.uvs is not None:  
            self.mesh.setUVs(np.ascontiguousarray(np.array(self.uvs, dtype=np.float32)))
        if self.normals is not None: 
            self.mesh.setNormals(np.ascontiguousarray(np.array(self.normals, dtype=np.float32)))
        if self.Tangents is not None: 
            self.mesh.setTangent(np.ascontiguousarray(np.array(self.Tangents, dtype=np.float32)))
        if self.Bitangents is not None: 
            self.mesh.setBitangent(np.ascontiguousarray(np.array(self.Bitangents, dtype=np.float32)))


    def onInit(self):
        raise NotImplementedError();

    def onUpdate(self):
        raise NotImplementedError(); 
