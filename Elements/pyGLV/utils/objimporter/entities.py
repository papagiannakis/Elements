
import os
import numpy as np
from Elements.pyECSS import utilities
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from Elements.pyGLV.GL.Textures import Texture
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.utils.objimporter.material import Material, StandardMaterial
from Elements.pyGLV.utils.objimporter.mesh import Mesh


class ModelEntity(Entity):
    def __init__(self, name=None, type=None, id=None) -> None:
        super().__init__(name, type, id)

    def init(self):
        """
        Initializes GL variables.
        Must be called in an active OpenGL Context
        """
        print("Init")
        exit()
        pass
        # return super().init()


class MeshEntity(Entity):
    """
    A ECSS entity representation for a Mesh object
    """

    transform_component : BasicTransform
    render_mesh_component : RenderMesh
    vertex_array_component : VertexArray
    shader_decorator_component : ShaderGLDecorator

    def __init__(self, mesh:Mesh, name:str=None, type=None, id=None) -> None:
        """
        Create an entity representation for a Mesh object
        """
        if name is None:
            name = mesh.name

        super().__init__(name, type, id)
        self.mesh = mesh
        self.transform_component = None
        self.render_mesh_component = None
        self.vertex_array_component = None

    def create_components(self, scene):
        # Generate needed components
        self.transform_component = scene.world.addComponent(self, BasicTransform(name="Transform", trs=utilities.identity() ))
        self.render_mesh_component = scene.world.addComponent(self, RenderMesh(name="RenderMesh"))
        
        self.render_mesh_component.vertex_attributes.append(self.mesh.vertices)
        self.render_mesh_component.vertex_attributes.append(self.mesh.normals)
        # If imported object has uv data, pass them or create all zeros array
        if self.mesh.has_uv: 
            self.render_mesh_component.vertex_attributes.append(self.mesh.uv)
        else:
            object_uvs = np.array([[1.0, 1.0]] * len(self.mesh.vertices))
            self.render_mesh_component.vertex_attributes.append(object_uvs)

        self.render_mesh_component.vertex_index.append(self.mesh.indices)
        self.vertex_array_component = scene.world.addComponent(self, VertexArray())
        self.shader_decorator_component = scene.world.addComponent(self, ShaderGLDecorator(Shader(vertex_import_file=os.path.join(os.path.dirname(__file__), "default_resources/shaders/Standard.vert"), fragment_import_file= os.path.join(os.path.dirname(__file__), "default_resources/shaders/Standard.frag"))))


    def initialize_gl(self, light_position, light_color, light_intensity):
        # Set object mesh shader static data
        # Light
        self.shader_decorator_component.setUniformVariable(key='lightPos', value=light_position, float3=True)
        self.shader_decorator_component.setUniformVariable(key='lightColor', value=light_color, float3=True)
        self.shader_decorator_component.setUniformVariable(key='lightIntensity', value=light_intensity, float1=True)


        # self.mesh.material = StandardMaterial("new")
        self.mesh.material.update_shader_properties(self.shader_decorator_component)