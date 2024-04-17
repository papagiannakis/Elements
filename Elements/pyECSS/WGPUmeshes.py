import sys 
import glm
import json
import numpy as np 
import Elements.utils.normals as norm

meshes = []

def MeshLoader(file):
    try:
        f = open(file, 'r')
    except OSError:
        print ("Could not open/read mesh file:", file)
        sys.exit()
    with f:
        return f.read() 

class mesh: 
    def __init__(self, file, modelMat=None):  
        self.data = json.loads(MeshLoader(file))   
        
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