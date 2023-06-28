from numpy import identity
from Elements.pyECSS import Entity
from Elements.pyGLV.GL.Scene import Scene
from Elements.utils.normals import generateSmoothNormalsMesh
from Elements.utils.obj_to_mesh import obj_to_mesh
from Elements.utils.objimporter.entities import ModelEntity
from Elements.utils.objimporter.mesh import Mesh
from Elements.utils.objimporter.model import Model
from Elements.utils.objimporter.wavefront import Wavefront
from PIL import Image
from Elements.utils.objimporter.material import StandardMaterial


class GameObject:
    objectPath = ""

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def Spawn(_scene, _objectPath, _objectName, _parent, _trs=None):
        if _trs is None:
            _trs = identity()

        imported_obj: Model = Wavefront(_objectPath, calculate_smooth_normals=False)
        model_entity: ModelEntity = _scene.world.createEntity(ModelEntity(imported_obj, _objectName, _trs))

        _scene.world.addEntityChild(_parent, model_entity)
        model_entity.create_entities_and_components(_scene)
        model_entity.transform_component.trs = _trs
        return model_entity

    def Find(searchName: str) -> Entity:
        returnEntity = None
        scene = Scene()
        scene.world.entities_components

        for entity in scene.world.entities:
            if (entity.name == searchName):
                returnEntity = entity

        if (returnEntity is None):
            print("Entity ", str(searchName), " not found!")

        return returnEntity
