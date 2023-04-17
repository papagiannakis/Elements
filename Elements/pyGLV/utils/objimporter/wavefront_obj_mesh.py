from Elements.pyGLV.utils.objimporter.mesh import Mesh
import Elements.pyGLV.utils.normals as norm
import numpy as np

class WavefrontObjectMesh(Mesh):
    """
    Helper class to store information of a mesh contained in a Wavefront .obj file.
    Derives from Mesh class
    """
    def __init__(self, name: str)-> None:
        super().__init__(name)
        self.faces = []
    
    
    def convert_to_mesh(self, calculate_smooth_normals:bool = False):
        """
        Parses the faces array into the vertices,uvs,normals,indices arrays

        Parameters
        ----------
        vertices : List
            The common vertices of the WavefrontObjectMesh, same across all meshes in it
        normals : List
            The common normals of the WavefrontObjectMesh, same across all meshes in it
        texture_coords : str
            The common texture coordinates of the WavefrontObjectMesh, same across all meshes in it
        obj_mesh : WavefrontObjectMesh
            The specific mesh of the WavefrontObjectMesh to source from
        """
                
        # init normals and texture_coords with 0
        new_normals = [[0.0, 1.0, 0.0]] * len(self.vertices)
        uv = [[0.0, 0.0]] * len(self.vertices)

        indices = []

        has_normals = False
        for face in self.faces:
            # Check face is valid?
            face_valid = True
            for index in face.vertex_indices:
                if index > len(self.vertices): # Indexes in .obj start from 1, not 0 apparently
                    face_valid = False
                    print("Found invalid face, ignoring... %d %d" %(index, len(self.vertices)))
            
            if not face_valid:
                continue

            for i in range(3):
                index = face.vertex_indices[i]-1
                indices.append(index)

                # Did obj have normal information?
                if face.has_normals:
                    new_normals[index] = self.normals[face.normal_indices[i]-1]
                    has_normals = True # At least one face has normals then this object must have normals imported
                
                # Did obj have uv information?
                if face.has_texture_coords:
                    uv[index] = [self.uv[face.texture_coords_indices[i]-1][0], self.uv[face.texture_coords_indices[i]-1][1]] # Only pass the u,v and not w values
                    self.has_uv = True # At least one face has uv texture data, then this object must have uvs as a whole

        self.vertices = np.array(self.vertices)
        self.indices = np.array(indices, dtype=np.uint32)
        
        uv = np.array(uv)

        if calculate_smooth_normals:
            # Calculate Smooth shaded normals
            # mesh.vertices, mesh.indices, uv, mesh.normals = norm.generateSmoothNormalsMeshNew(mesh.vertices, mesh.indices, color= (uv if mesh.has_uv else None))
            self.normals = norm.generateSmoothNormalsMeshNew(self.vertices, self.indices, 60.0)
        
        else:
            if has_normals:
                self.normals = np.array(new_normals)
            else:
                # Calculate Flat shaded normals
                self.vertices, self.indices, uv, self.normals = norm.generateFlatNormalsMesh(self.vertices, self.indices, color= (uv if self.has_uv else None))

        # Apply uvs to mesh
        if self.has_uv:
            self.uv = uv
        else:
            self.uv = None