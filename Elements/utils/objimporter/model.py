from __future__ import annotations
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.utils.objimporter.mesh import Mesh

class Model:
    """
    Stores a 3D model, containing multiple meshes, Textures and Materials, as an Entity
    
    """
    name: str # The name of this Model
    __meshes : dict[str, Mesh] = {} # The named meshes of the imported object in a dict with their names as keys, each containing its vertices/normals/uvs
    __mesh_list : list[Mesh] = [] # All the meshes of the imported object in a list, each containing its vertices/normals/uvs

    def __init__(self, name:str):
        self.name = name
        self.__mesh_list = []
        self.__meshes = {}

    def add_mesh(self, mesh: Mesh):
        """
        Adds a mesh to the model

        Parameters
        ----------
        mesh : Mesh
            The mesh to add to this model.
        """
        self.__mesh_list.append(mesh)
        if mesh.name != "":
            self.__meshes[mesh.name] = mesh

    def get_mesh(self, id)-> Mesh:
        """
        Gets a mesh in the model

        Parameters
        ----------
        id : str or number
            The name of the mesh or the id of it.
        """
        if type(id) is str:
            return self.__meshes[id]
        elif type(id) is int:
            return self.__mesh_list[id]
        else:
            return None

    def add_to_ecss_scene(self, scene, parent):
        """
        Adds the root entity and a 
        child entity, for each mesh, with all the components needed

        Parameters
        ----------
        scene : Scene
            The ECSS scene to add this model to.
        parent : Entity
            The ECSS Entity to be the parent of this model.
        
        Returns
        -------
        Entity
        The entity, added in the scene
        """

        node = scene.world.createEntity(Entity(name=self.name))
        scene.world.addEntityChild(parent, node)

        for mesh in self.__mesh_list:
            mesh.add_to_ecss_scene(scene, node)

        return node
    
    def __get_mesh_count(self) -> int:
        return len(self.__mesh_list) if self.__mesh_list is not None else 0

    mesh_count = property(__get_mesh_count)
