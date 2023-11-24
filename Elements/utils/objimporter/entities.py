
import os
import numpy as np
import Elements.pyECSS.math_utilities as utilities
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from Elements.pyGLV.GL.Textures import Texture
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.utils.objimporter.material import Material, StandardMaterial
from Elements.utils.objimporter.mesh import Mesh
from Elements.utils.objimporter.model import Model
from Elements.definitions import SHADER_DIR


class ModelEntity(Entity):
    def __init__(self, model:Model, name:str=None, _trs=None) -> None:
        """
        Create an entity representation for a Model object
        """
        if name is None:
            name = model.name

        super().__init__(name, type, id)
        self.model:Model = model
        self.transform_component:BasicTransform = BasicTransform(name="Transform", trs = _trs)
        self.mesh_entities:list[MeshEntity] = [] 
            

    def create_entities_and_components(self, scene):
        """
        Creates a new Entity for each Mesh and their Components
        """
        self.transform_component:BasicTransform = scene.world.addComponent(self, self.transform_component)
        for m in range(self.model.mesh_count):
            mesh_entity:MeshEntity = scene.world.createEntity(MeshEntity(self.model.get_mesh(m)))
            self.mesh_entities.append(mesh_entity)
            scene.world.addEntityChild(self, mesh_entity)
            mesh_entity.create_components(scene)


    def initialize_gl(self, light_position, light_color, light_intensity):
        for mesh_entity in self.mesh_entities:
            mesh_entity.initialize_gl(light_position, light_color, light_intensity)



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
        """
        Creates all the ECSS components needed to represent this mesh
        """
        # Generate needed components
        self.transform_component:BasicTransform = scene.world.addComponent(self, BasicTransform(name="Transform", trs=utilities.identity() ))
        self.render_mesh_component:RenderMesh = scene.world.addComponent(self, RenderMesh(name="RenderMesh"))
        
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
        self.shader_decorator_component = scene.world.addComponent(self, ShaderGLDecorator(Shader(vertex_import_file= SHADER_DIR / "Standard.vert", fragment_import_file= SHADER_DIR / "Standard.frag")))


    def initialize_gl(self, light_position, light_color, light_intensity):
        """
        Initializes shader variables, must be called in an active gl context
        """
        # Set object mesh shader static data
        # Light
        self.shader_decorator_component.setUniformVariable(key='lightPos', value=light_position, float3=True)
        self.shader_decorator_component.setUniformVariable(key='lightColor', value=light_color, float3=True)
        self.shader_decorator_component.setUniformVariable(key='lightIntensity', value=light_intensity, float1=True)

        if self.mesh.material is None:
            self.mesh.material = StandardMaterial("new")
        self.mesh.material.update_shader_properties(self.shader_decorator_component)