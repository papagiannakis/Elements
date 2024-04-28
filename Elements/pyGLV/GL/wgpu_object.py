import wgpu 
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
            self.mesh.setVertices(self.vertices)
        if self.indices.any():  
            self.mesh.setIndices(self.indices) 
        if self.uvs.any():  
            self.mesh.setUVs(self.uvs) 
        if self.normals.any():  
            self.mesh.setNormals(self.normals) 


    def onInit(self):
        raise NotImplementedError();

    def onUpdate(self):
        raise NotImplementedError(); 

    # def set_renderer_attributes(self, device:wgpu.GPUDevice, materialBindGroupLayout:wgpu.GPUBindGroupLayout=None):
    #     vertices = np.array(self.vertices, dtype=np.float32)
    #     uvs = np.array(self.uvs, dtype=np.float32)

    #     if materialBindGroupLayout:
    #         self.material = wgpu_material(device=device, filepath=self.material_info["file"], bindGroupLayout=materialBindGroupLayout);
    #         self.bindGroup = self.material.bindGroup;
    #     else:
    #         self.material = None
    #         self.bindGroup = None

    #     self.vertex_buffer = device.create_buffer_with_data(
    #         data=vertices, usage=wgpu.BufferUsage.VERTEX
    #     )

    #     self.uvs_buffer = device.create_buffer_with_data(
    #         data=uvs, usage=wgpu.BufferUsage.VERTEX
    #     )