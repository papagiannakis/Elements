import sys 
import glm
import json
import numpy as np 
import Elements.utils.normals as norm
from Elements.definitions import MODEL_DIR

meshes = []

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
                # for vertex_data in face:
                #     v_idx, uv_idx, n_idx = map(int, vertex_data.split('/'))
                #     # OBJ indices start from 1, so subtract 1 to convert to 0-based indexing
                #     face_vertices.append(vertices[v_idx - 1])
                #     if uv_idx != 0:
                #         face_uvs.append(uvs[uv_idx - 1])
                #     if n_idx != 0:
                #         face_normals.append(normals[n_idx - 1])

                for vertex_data in face:
                    v_vt_vn = list(map(int, vertex_data.split('/')))

                    face_vertices.append(vertices[v_vt_vn[0] - 1])
                    face_uvs.append(uvs[v_vt_vn[1] - 1])
                    
    return face_vertices, face_uvs


class mesh: 
    def __init__(self, file, modelMat=None):  
        self.data = json.loads(json_laoder(file))   
        
        if modelMat is None: 
            modelMat = glm.mat4x4(1)  
            
        for i, vertex in enumerate(self.data["vertices"]): 
            v = glm.vec4(x=vertex[0], y=vertex[1], z=vertex[2], w=1)
            v = modelMat @ v;  
            self.data["vertices"][i] = [v[0], v[1], v[2]] 
            
        self.verices = np.array(self.data["vertices"], dtype=np.float32)
        self.color = np.array(self.data["colors"], dtype=np.float32)
        self.indices = np.array(self.data["indices"], dtype=np.uint32)  
        
        self.verices, self.indices, self.color = norm.generateUniqueVertices(vertices=self.verices, indices=self.indices, color=self.color)  
        self.normals = norm.generateNormals(vertices=self.verices, indices=self.indices)
            
        meshes.append(self) 
        
        
def GenerateSceneMeshData(): 
    vertices = []  
    colors = [] 
    normals = [] 
    indices = []  
    indexOffset = 0
    
    for m in meshes:
        for vertex in m.verices:
            vertices.append(vertex)
        for color in m.color:
            colors.append(color) 
        for normal in m.normals:
            normals.append(normal)  
        
        for index in m.indices:
            indices.append(index + indexOffset)  
        indexOffset = indexOffset + len(m.indices)  
        
    vertices = np.array(vertices, dtype=np.float32)
    colors = np.array(colors, dtype=np.float32)
    normals = np.array(normals, dtype=np.float32) 
    indices = np.array(indices, dtype=np.uint32) 
    
    return vertices, indices, colors, normal


if __name__ == "__main__":
    obj_to_import = MODEL_DIR / "cube" / "cube.obj"
    v, vt = obj_loader(obj_to_import)
    print(v)