import wgpu
import glm

import sys 
import glm
import json
import numpy as np 
import Elements.utils.normals as norm
from Elements.definitions import MODEL_DIR
from Elements.pyGLV.GL.wgpu_material import wgpu_material
from Elements.pyGLV.GL.wgpu_shader import BasicShader 
from Elements.pyGLV.GUI import fps_cammera, static_cammera



def json_laoder(file):
    try:
        f = open(file, 'r')
    except OSError:
        print ("Could not open/read mesh file:", file)
        sys.exit()
    with f:
        return f.read() 


def obj_loader(file_path):
    vertices = []
    uvs = []
    normals = []
    
    face_vertices = []
    face_uvs = []
    face_normals = []

    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('v '):
                vertex = list(map(float, line.strip().split()[1:]))
                vertices.append(vertex)
            elif line.startswith('vt '):
                uv = list(map(float, line.strip().split()[1:]))
                uvs.append(uv)
            elif line.startswith('vn '):
                normal = list(map(float, line.strip().split()[1:]))
                normals.append(normal)
            elif line.startswith('f '):
                face = line.strip().split()[1:]
                for vertex_data in face:
                    v_vt_vn = list(map(int, vertex_data.split('/')))

                    face_vertices.append(vertices[v_vt_vn[0] - 1])
                    face_uvs.append(uvs[v_vt_vn[1] - 1])
                    
    return face_vertices, face_uvs


class Object:
    def __init__(self):
        self.vertices = None
        self.uvs = None
        self.normals = None

        self.transform = glm.mat4x4(1)

        self.material_info = {}

        self.updateFunc = None

    def load_mesh_from_obj(self, file_path):
        self.vertices, self.uvs = obj_loader(file_path=file_path) 

        self.vertices = np.array(self.vertices, dtype=np.float32)
        self.uvs = np.array(self.uvs, dtype=np.float32)

    def load_materila(self, file_path:str):
        self.material_info["file"] = file_path

    def update(self):
        raise NotImplementedError();

    def _internal_init(self, device:wgpu.GPUDevice, materialBindGroupLayout:wgpu.GPUBindGroupLayout=None):
        vertices = np.array(self.vertices, dtype=np.float32)
        uvs = np.array(self.uvs, dtype=np.float32)

        if materialBindGroupLayout:
            self.material = wgpu_material(device=device, filepath=self.material_info["file"], bindGroupLayout=materialBindGroupLayout);
            self.bindGroup = self.material.bindGroup;
        else:
            self.material = None
            self.bindGroup = None

        self.vertex_buffer = device.create_buffer_with_data(
            data=vertices, usage=wgpu.BufferUsage.VERTEX
        )

        self.uvs_buffer = device.create_buffer_with_data(
            data=uvs, usage=wgpu.BufferUsage.VERTEX
        )

        self.bufferDiscriptor = [
            {
                "array_stride": 3 * 4,
                "step_mode": wgpu.VertexStepMode.vertex,
                "attributes": [
                    {
                        "format": wgpu.VertexFormat.float32x3,
                        "offset": 0,
                        "shader_location": 0,
                    },
                ],
            },
            {
                "array_stride": 2 * 4,
                "step_mode": wgpu.VertexStepMode.vertex,
                "attributes": [
                    {
                        "format": wgpu.VertexFormat.float32x2,
                        "offset": 0,
                        "shader_location": 1,
                    },
                ],
            },
        ]





class Scene():
    """
    Singleton Scene that assembles ECSSManager and Viewer classes together for Scene authoring
    in pyglGA. It also brings together the new extensions to pyglGA: Shader, VertexArray and 
    RenderMeshDecorators
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            print('Creating Scene Singleton Object')
            cls._instance = super(Scene, cls).__new__(cls)

            cls._cammera = None
            cls._objects: Object = []
        return cls._instance
    
    
    def __init__(self):
        None;

    def set_cammera(self, cam: fps_cammera.cammera):
        self._cammera = cam

    def append_object(self, obj: Object):
        self._objects.append(obj)

    def init(self, device:wgpu.GPUDevice, materialBindGroupLayout:wgpu.GPUBindGroupLayout=None):
        for obj in self._objects:
            obj._internal_init(device=device, materialBindGroupLayout=materialBindGroupLayout)

    def update(self, canvas, event):
        self._cammera.update(canvas=canvas, event=event)

        for obj in self._objects:
            obj.update()


if __name__ == "__main__":
    # The client singleton code.

    s1 = Scene()
    s2 = Scene()

    if id(s1) == id(s2):
        print("Singleton works, both Scenes contain the same instance.")
    else:
        print("Singleton failed, Scenes contain different instances.")
     