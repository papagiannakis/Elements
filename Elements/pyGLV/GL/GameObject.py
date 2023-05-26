from numpy import identity
from Elements.pyECSS import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.Shader import Shader, ShaderGLDecorator
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.pyGLV.utils.normals import generateSmoothNormalsMesh
from Elements.pyGLV.utils.obj_to_mesh import obj_to_mesh

class GameObject:
  
    objectPath = ""

    def __init__(self, name, age):
        self.name = name
        self.age = age
        
        
    def Spawn(_scene, _objectPath, _objectName,  _parent, trs=None, texture=None):
        if trs is None:
            trs = identity()
        #Create entity to the scene 
        entityNode = _scene.world.createEntity(Entity(name = _objectName))
        _scene.world.addEntityChild(_parent, entityNode)
        _scene.world.addComponent(entityNode, BasicTransform(name = _objectName + "_TRS", trs = trs))
        gameObjectMesh = _scene.world.addComponent(entityNode, RenderMesh(name = _objectName + "_Mesh"))
        if texture is None:
            obj_color = [168 / 255, 168 / 255, 210 / 255, 1.0]
            vert, ind, col = obj_to_mesh(_objectPath, color=obj_color)
            vertices, indices, colors, normals = generateSmoothNormalsMesh(vert, ind, col)

            gameObjectMesh.vertex_attributes.append(vertices)
            gameObjectMesh.vertex_attributes.append(colors)
            gameObjectMesh.vertex_attributes.append(normals)
            gameObjectMesh.vertex_index.append(indices)
            _scene.world.addComponent(entityNode, VertexArray())
            shaderDec = _scene.world.addComponent(entityNode, ShaderGLDecorator(
                Shader(vertex_source=Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))
        #else:
        #    vertices, indices, myuvs, normals = TextureMapping.UVMapping(_objectPath,
        #                                                                 normals=True)
        #    gameObjectMesh.vertex_attributes.append(vertices)
        #    gameObjectMesh.vertex_attributes.append(myuvs)
        #    gameObjectMesh.vertex_attributes.append(normals)


        #    gameObjectMesh.vertex_index.append(indices)
        #    vArray = _scene.world.addComponent(entityNode, VertexArray())
        #    shaderDec = _scene.world.addComponent(entityNode, ShaderGLDecorator(
        #        Shader(vertex_source=Shader.SIMPLE_TEXTURE_PHONG_VERT,
        #               fragment_source=Shader.SIMPLE_TEXTURE_PHONG_FRAG)))

        return shaderDec


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

