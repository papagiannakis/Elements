from numpy import identity
from Elements.pyECSS import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.utils.normals import generateSmoothNormalsMesh
from Elements.pyGLV.utils.obj_to_mesh import obj_to_mesh
from Elements.pyGLV.utils.objimporter.entities import ModelEntity
from Elements.pyGLV.utils.objimporter.model import Model
from Elements.pyGLV.utils.objimporter.wavefront import Wavefront

class GameObject:
  
    objectPath = ""

    def __init__(self, name, age):
        self.name = name
        self.age = age
        
        
    def Spawn(_scene, _objectPath, _objectName,  _parent, trs=None, texture=None):
        if trs is None:
            trs = identity()

        imported_obj:Model = Wavefront(_objectPath, calculate_smooth_normals=False)

        model_entity:ModelEntity = _scene.world.createEntity(ModelEntity(imported_obj,_objectName))
        _scene.world.addEntityChild(_parent, model_entity)
        model_entity.create_entities_and_components(_scene)

        return model_entity


    def Find(searchName: str) -> Entity:
        returnEntity = None
        scene = Scene.Scene()
        scene.world.entities_components


        for entity in scene.world.entities:
            if(entity.name == searchName):
                returnEntity = entity

        if(returnEntity is None):
            print("Entity ",str(searchName)," not found!")

        return returnEntity

