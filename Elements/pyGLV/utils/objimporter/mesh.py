import numpy as np
import Elements.pyGLV.utils.normals as norm

from Elements.pyGLV.utils.objimporter.wavefront_obj_mesh import WavefrontObjectMesh

class Mesh:
    """
    A class that stores meshes.

    Meshes contain vertices, normals, uvs and indices arrays
    The indices array is indexing into the vertex array; three indices for each triangle of the mesh
    For every vertex at the i-th position, the normal and uv information of it will be at position i of the normals and uv arrays.

    Attributes
    ----------
    name : str
        the name of the mesh
    vertices : np.array
        The vertices of the mesh
    normals : np.array
        The normals of the mesh
    uv : np.array
        The UVs of the mesh
    indices : np.array
        the indices list containing the triangle indices for the vertex list
    material : str
        the material name to be used for this mesh
    
    Methods
    -------
    from_objmesh(vertices, normals, texture_coords, obj_mesh)
        Creates a Mesh instance from a mesh of a WavefrontObjectMesh
    """

    def __init__(self, name=""):
        self.name = name
        self.vertices = np.array([]) # Array with float4 with (x, y, z, w) like [[1.0, 1.0, 1.0, 1.0], [2.0, 1.5, 2.65, 1.0], ...]
        self.normals = np.array([])
        self.has_uv = False
        self.uv = np.array([])
        self.indices = np.array([], dtype=np.uint32)
        self.material = ""
    
    @staticmethod
    def from_objmesh(vertices, normals, texture_coords, obj_mesh: WavefrontObjectMesh, calculate_smooth_normals:bool = False) -> None:
        """
        Creates a Mesh from a WavefrontObjectMesh

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
        
        mesh = Mesh(name=obj_mesh.name)
        mesh.material = obj_mesh.material
        
        # init normals and texture_coords with 0
        new_normals = [[0.0, 1.0, 0.0]] * len(vertices)
        uv = [[0.0, 0.0]] * len(vertices)

        indices = []

        has_normals = False
        for face in obj_mesh.faces:
            # Check face is valid?
            face_valid = True
            for index in face.vertex_indices:
                if index > len(vertices): # Indexes in .obj start from 1, not 0 apparently
                    face_valid = False
                    print("Found invalid face, ignoring... %d %d" %(index, len(vertices)))
            
            if not face_valid:
                continue

            for i in range(3):
                index = face.vertex_indices[i]-1
                indices.append(index)

                # Did obj have normal information?
                if face.has_normals:
                    new_normals[index] = normals[face.normal_indices[i]-1]
                    has_normals = True # At least one face has normals then this object must have normals imported
                
                # Did obj have uv information?
                if face.has_texture_coords:
                    uv[index] = [texture_coords[face.texture_coords_indices[i]-1][0], texture_coords[face.texture_coords_indices[i]-1][1]] # Only pass the u,v and not w values
                    mesh.has_uv = True # At least one face has uv texture data, then this object must have uvs as a whole

        mesh.vertices = np.array(vertices)
        print(len(mesh.vertices))
        print(len(np.unique(mesh.vertices)))
        mesh.indices = np.array(indices, dtype=np.uint32)
        
        uv = np.array(uv)

        if calculate_smooth_normals:
            # Calculate Flat shaded normals
            mesh.vertices, mesh.indices, uv, mesh.normals = norm.generateSmoothNormalsMesh(mesh.vertices, mesh.indices, colors= (uv if mesh.has_uv else None))
            pass
        else:
            if has_normals:
                mesh.normals = np.array(new_normals)
            else:
                # Calculate Flat shaded normals
                mesh.vertices, mesh.indices, uv, mesh.normals = norm.generateFlatNormalsMesh(mesh.vertices, mesh.indices, color= (uv if mesh.has_uv else None))

        # Apply uvs to mesh
        if mesh.has_uv:
            mesh.uv = uv

        return mesh




