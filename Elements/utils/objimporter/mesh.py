import os
import numpy as np
from Elements.pyECSS import utilities
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import System
import Elements.pyECSS.math_utilities as util
from Elements.pyGLV.GL.Textures import Texture
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL import Shader
from Elements.pyGLV.GL.Shader import ShaderGLDecorator, Shader
from Elements.utils.objimporter.material import Material
from Elements.pyECSS.Entity import Entity

from Elements.pyECSS.Component import Component


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
    material : Material
        the material to be used for this mesh
    
    Methods
    -------
    from_objmesh(vertices, normals, texture_coords, obj_mesh)
        Creates a Mesh instance from a mesh of a WavefrontObjectMesh
    """

    name : str
    vertices: np.array
    normals: np.array
    has_uv: bool
    uv: np.array
    indices: np.array
    material: Material

    def __init__(self, name=""):
        self.name = name
        self.vertices = np.array([]) # Array with float3 with (x, y, z) like [[1.0, 1.0, 1.0], [2.0, 1.5, 2.65], ...]
        self.normals = np.array([])
        self.has_uv = False
        self.uv = np.array([])
        self.indices = np.array([], dtype=np.uint32)
        self.material = None