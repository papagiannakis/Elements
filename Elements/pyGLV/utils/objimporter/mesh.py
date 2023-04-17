import os
import numpy as np
from Elements.pyECSS import utilities
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import System
import Elements.pyECSS.utilities as util
from Elements.pyGLV.GL.Textures import Texture
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.GL import Shader
from Elements.pyGLV.GL.Shader import ShaderGLDecorator, Shader
from Elements.pyGLV.utils.objimporter.material import Material
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
    material : str
        the material name to be used for this mesh
    
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
        self.vertices = np.array([]) # Array with float4 with (x, y, z, w) like [[1.0, 1.0, 1.0, 1.0], [2.0, 1.5, 2.65, 1.0], ...]
        self.normals = np.array([])
        self.has_uv = False
        self.uv = np.array([])
        self.indices = np.array([], dtype=np.uint32)
        self.material = None

    # def add_to_ecss_scene(self, scene, parent):
    #     """
    #     Adds an entity, for the mesh, with all the components needed

    #     Parameters
    #     ----------
    #     scene : Scene
    #         The ECSS scene to add this mesh to.
    #     parent : Entity
    #         The ECSS Entity to be the parent of this mesh.
        
    #     Returns
    #     -------
    #     Entity
    #     The entity, added in the scene
    #     """

    #     node = scene.world.createEntity(Entity(name=self.name))
    #     scene.world.addEntityChild(parent, node)


    #     transform = scene.world.addComponent(node, BasicTransform(name=self.name+"_Transform", type="BasicTransform"))
    #     mesh_renderer = scene.world.addComponent(node, RenderMesh(name=self.name+"_RenderMesh", type="RenderMesh"))

    #     mesh_renderer.vertex_attributes.append(self.vertices)
    #     mesh_renderer.vertex_attributes.append(self.normals)
    #     # If imported object has uv data, pass them or create all zeros array
    #     if self.has_uv: 
    #         mesh_renderer.vertex_attributes.append(self.uv)
    #     else:
    #         object_uvs = np.array([[1.0, 1.0]] * len(self.vertices))
    #         mesh_renderer.vertex_attributes.append(object_uvs)

    #     mesh_renderer.vertex_index.append(self.indices)


    #     vertex_array = scene.world.addComponent(node, VertexArray())
    #     shader = Shader(vertex_import_file=os.path.join(os.path.dirname(__file__), "default_resources/shaders/Lit.vert"), fragment_import_file= os.path.join(os.path.dirname(__file__), "default_resources/shaders/Lit.frag"))
    #     shader_decorator = scene.world.addComponent(node, ShaderGLDecorator(shader, type="ShaderGLDecorator"))

    #     # print(len(self.vertices), len(self.normals), len(self.uv))
    #     # exit()

    #     # # ---- Configure Shader -----

    #     # # Set object mesh shader static data
    #     # # Light
    #     # Lposition = utilities.vec(0, 1.1, 1.0) #uniform lightpos
    #     # Lcolor = utilities.vec(1.0,1.0,1.0)
    #     # Lintensity = 10.0

    #     # shader_decorator.setUniformVariable(key='lightPos', value=Lposition, float3=True)
    #     # shader_decorator.setUniformVariable(key='lightColor', value=Lcolor, float3=True)
    #     # shader_decorator.setUniformVariable(key='lightIntensity', value=Lintensity, float1=True)
    #     # # Material
    #     # # Albedo
    #     # shader_decorator.setUniformVariable(key='albedoColor', value=np.array([1.0, 0.0, 0.0]), float3=True)
    #     # texturePath = os.path.join(os.path.dirname(__file__), "default_resources/textures/white1x1.png")
    #     # texture = Texture(texturePath, texture_channel=0)
    #     # shader_decorator.setUniformVariable(key='albedoMap', value=texture, texture=True)
    #     # exit()
    #     # # Normal map
    #     # shader_decorator.setUniformVariable(key='normalMapIntensity', value=1.0, float1=True)
    #     # texturePath = os.path.join(os.path.dirname(__file__), "default_resources/textures/normal1x1.png")
    #     # texture = Texture(texturePath, texture_channel=1)
    #     # shader_decorator.setUniformVariable(key='normalMap', value=texture, texture=True)
    #     # # Metallic map
    #     # texturePath = os.path.join(os.path.dirname(__file__), "default_resources/textures/white1x1.png")
    #     # texture = Texture(texturePath, texture_channel=2)
    #     # shader_decorator.setUniformVariable(key='metallicMap', value=texture, texture=True)
    #     # # Roughness
    #     # texturePath = os.path.join(os.path.dirname(__file__), "default_resources/textures/black1x1.png")
    #     # texture = Texture(texturePath, texture_channel=3)
    #     # shader_decorator.setUniformVariable(key='roughnessMap', value=texture, texture=True)
    #     # # Ambient Occlusion
    #     # texturePath = os.path.join(os.path.dirname(__file__), "default_resources/textures/white1x1.png")
    #     # texture = Texture(texturePath, texture_channel=4)
    #     # shader_decorator.setUniformVariable(key='aoMap', value=texture, texture=True)

    #     return node