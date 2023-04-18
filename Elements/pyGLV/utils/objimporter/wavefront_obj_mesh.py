from Elements.pyGLV.utils.objimporter.mesh import Mesh
import Elements.pyGLV.utils.normals as norm
import numpy as np

from Elements.pyGLV.utils.objimporter.wavefront_obj_face import WavefrontObjectFace

class WavefrontObjectMesh(Mesh):
    """
    Helper class to store information of a mesh contained in a Wavefront .obj file.
    Derives from Mesh class
    """
    def __init__(self, name: str)-> None:
        super().__init__(name)
        self.faces = []
    
    class _VertexData:
        def __init__(self) -> None:
            self.vertexIndex = 0
            self.vertex = np.array([0.0,0.0,0.0])

            self.normalIndex = 0
            self.normal = np.array([0.0,1.0,0.0])

            self.uvIndex = 0
            self.uv = np.array([0.0,0.0])
    
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
        new_vertices = []
        new_normals = []
        new_uv = []

        new_indices = []



        has_normals = False

        face:WavefrontObjectFace
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
                new_indices.append(len(new_vertices))

                new_vertices.append(self.vertices[face.vertex_indices[i]-1])

                # Did obj have normal information?
                if face.has_normals:
                    new_normals.append(self.normals[face.normal_indices[i]-1])
                    has_normals = True # At least one face has normals then this object must have normals imported
                
                # Did obj have uv information?
                if face.has_texture_coords:
                    new_uv.append([self.uv[face.texture_coords_indices[i]-1][0], self.uv[face.texture_coords_indices[i]-1][1]]) # Only pass the u,v and not w values
                    self.has_uv = True # At least one face has uv texture data, then this object must have uvs as a whole


        self.vertices = np.array(new_vertices)
        self.indices = np.array(new_indices)
        
        # Apply uvs to mesh
        if self.has_uv:
            self.uv = np.array(new_uv)
        else:
            self.uv = None

        # Apply (and Calculate if needed) normals
        if calculate_smooth_normals:
            # Calculate Smooth shaded normals
            # mesh.vertices, mesh.indices, uv, mesh.normals = norm.generateSmoothNormalsMeshNew(mesh.vertices, mesh.indices, color= (uv if mesh.has_uv else None))
            self.normals = norm.generateSmoothNormalsMeshNew(self.vertices, self.indices, 60.0)
        else:
            if has_normals:
                self.normals = np.array(new_normals)
            else:
                # Calculate Flat shaded normals
                self.vertices, self.indices, new_uv, self.normals = norm.generateFlatNormalsMesh(self.vertices, self.indices, color= (self.uv if self.has_uv else None))

        self.__optimize()

    def __optimize():
        """
        Optimizes vertices, indices, uv arrays in order to remove duplicates
        """
        # TODO: Optimize vertices by removing duplicate
        pass