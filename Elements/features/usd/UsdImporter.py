"""
USD import utilities, part of the Elements.pyECSS package

Elements.pyECSS (Entity Component Systems in a Scenegraph) package
@Copyright 2021-2022 Dr. George Papagiannakis

The USDImporter file, holds functionality for importing and exporting Elements scenes as .usd files

"""
import os

from numpy.dual import norm
from pxr import Usd, Gf, Sdf
import numpy as np

from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.Entity import Entity
from Elements.pyGLV.GL.Shader import ShaderGLDecorator, Shader
from Elements.pyGLV.GL.VertexArray import VertexArray
import Elements.pyECSS.math_utilities as util

"""
GlobalArray that holds all shaders of loaded objects.

"""

shaderDecs = []

"""
Helper function that creates a generic shader for an object that is loaded.
It is added to the global shaderDecs array.

"""


def InitShaderDec(shaderDec):
    global shaderDecs
    # Light
    Lposition = util.vec(2.0, 5.5, 2.0)  # uniform lightpos
    Lambientcolor = util.vec(1.0, 1.0, 1.0)  # uniform ambient color
    Lambientstr = 0.3  # uniform ambientStr
    LviewPos = util.vec(2.5, 2.8, 5.0)  # uniform viewpos
    Lcolor = util.vec(1.0, 1.0, 1.0)
    Lintensity = 0.8
    # Material
    Mshininess = 0.4
    Mcolor = util.vec(0.8, 0.0, 0.8)

    model_cube = util.scale(0.1) @ util.translate(0.0, 0.5, 0.0)
    projMat = util.perspective(50.0, 1.0, 1.0, 10.0)
    eye = util.vec(1, 0.54, 1.0)
    target = util.vec(0.02, 0.14, 0.217)
    up = util.vec(0.0, 1.0, 0.0)
    view = util.lookat(eye, target, up)
    tabletrs = util.translate(0, 0, 0)
    mvp_cube = projMat @ view @ tabletrs

    shaderDec.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
    shaderDec.setUniformVariable(key='model', value=model_cube, mat4=True)
    shaderDec.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
    shaderDec.setUniformVariable(key='ambientStr', value=Lambientstr, float1=True)
    shaderDec.setUniformVariable(key='viewPos', value=LviewPos, float3=True)
    shaderDec.setUniformVariable(key='lightPos', value=Lposition, float3=True)
    shaderDec.setUniformVariable(key='lightColor', value=Lcolor, float3=True)
    shaderDec.setUniformVariable(key='lightIntensity', value=Lintensity, float1=True)
    shaderDec.setUniformVariable(key='shininess', value=Mshininess, float1=True)
    shaderDec.setUniformVariable(key='matColor', value=Mcolor, float3=True)
    shaderDecs.append(shaderDec)


"""
Loads the .usd file specified in path argument.
Adds the loaded entities and components to the argument scene.
Returns the new scene with all the new entities and components.

"""


def LoadScene(scene, path):
    stage = Usd.Stage.Open(path)
    prim_iter = iter(Usd.PrimRange.PreAndPostVisit(stage.GetPseudoRoot()))
    shaderDecs = []
    for prim in prim_iter:
        if prim_iter.IsPostVisit():
            continue

        parent_entity_name = prim.GetAttribute('parent').Get()
        # Some entities that exist in some demos run with different shaders, as a result we do not load/save them
        if parent_entity_name == 'terrain' or parent_entity_name == 'axes' or parent_entity_name == 'coll' or parent_entity_name == 'LightPos':
            continue

        # Loads the Transform component
        if prim.GetName() == 'TRS':
            l2Cam = np.array(prim.GetAttribute('l2cam').Get())
            l2world = np.array(prim.GetAttribute('l2world').Get())
            rotationEulerAngles = np.array(prim.GetAttribute('rotationEulerAngles').Get())
            translation = np.array(prim.GetAttribute('translation').Get())
            trs = np.array(prim.GetAttribute('trs').Get())
            parent_entity = FindEntity(scene, parent_entity_name)
            scene.world.addComponent(parent_entity, BasicTransform(name=parent_entity_name + "_TRS", trs=trs))

        # Loads the Mesh component
        elif prim.GetName() == 'Mesh':
            points = np.array(prim.GetAttribute('points').Get())
            colors = np.array(prim.GetAttribute('colors').Get())
            if prim.GetAttribute('normals') is not None:
                normals = np.array(prim.GetAttribute('normals').Get())
            indices = np.array(prim.GetAttribute('indices').Get())
            parent_entity_name = prim.GetAttribute('parent').Get()
            parent_entity = FindEntity(scene, parent_entity_name)
            game_object_mesh = scene.world.addComponent(parent_entity, RenderMesh(name=parent_entity_name + "_Mesh"))

            game_object_mesh.vertex_attributes.append(points)
            game_object_mesh.vertex_attributes.append(colors)
            if normals is not None: game_object_mesh.vertex_attributes.append(normals)
            game_object_mesh.vertex_index.append(indices)
            scene.world.addComponent(parent_entity, VertexArray())
            shader_dec = scene.world.addComponent(parent_entity, ShaderGLDecorator(
                    Shader(vertex_import_file=os.path.join(os.path.dirname(__file__), "../../utils/objimporter/default_resources/shaders/Standard.vert"),
                           fragment_import_file=os.path.join(os.path.dirname(__file__),"../../utils/objimporter/default_resources/shaders/Standard.frag"))))
            InitShaderDec(shader_dec)
            shaderDecs.append(shader_dec)

        # Loads the VA component
        elif prim.GetName() == 'VA':
            points = np.array(prim.GetAttribute('points').Get())
            colors = np.array(prim.GetAttribute('colors').Get())
            if prim.GetAttribute('normals') is not None:
                normals = np.array(prim.GetAttribute('normals').Get())
            indices = np.array(prim.GetAttribute('indices').Get())
            parent_entity = prim.GetAttribute('parent').Get()

        # Loads the Entity
        else:
            entity_name = prim.GetName()
            entity_parent_name = prim.GetAttribute('Parent').Get()
            if entity_parent_name is not None:
                entity = scene.world.createEntity(Entity(name=entity_name))
                parent_entity = FindEntity(scene, entity_parent_name)
                scene.world.addEntityChild(parent_entity, entity)
    return shaderDecs


"""
Saves argument scene to the .usd file specified in  argument path.
"""


def SaveScene(scene, path):
    components = scene.world.entities_components
    stage = Usd.Stage.CreateNew(path)
    for k, vs in components.items():
        # Creates entities and handles parenting
        if k.getParent() is None:
            prim = stage.DefinePrim('/' + k.name)
            prim.CreateAttribute('Parent', Sdf.ValueTypeNames.String)
        else:
            pathToParent = FindParentPath(k)
            prim = stage.DefinePrim(pathToParent)
            Parent = prim.CreateAttribute('Parent', Sdf.ValueTypeNames.String)
            Parent.Set(k.getParent().name)

        # Creates and saves components
        ExportComponent(stage, prim, vs)

        ID = prim.CreateAttribute('ID', Sdf.ValueTypeNames.TimeCode)
        ID.Set(k.id)
    stage.Save()


"""
Helper function to find the full path from root
"""


def FindParentPath(entity):
    pathFromRoot = ''
    while entity is not None:
        pathFromRoot = '/' + entity.name + pathFromRoot
        entity = entity.getParent()
    return pathFromRoot


"""
Function used for saving all components of an entity
Stage is the current USD save
EntityPrim is the reference to the USD entity
Components arguments are the components that will be saved.
"""


def ExportComponent(stage, entityPrim, components):
    for comp in components:
        if comp is None:
            continue

        # Saves a transform component
        if comp.type == 'BasicTransform':
            compPrimitive = stage.DefinePrim(str(entityPrim.GetPrimPath()) + '/TRS')
            attr = compPrimitive.CreateAttribute('l2cam', Sdf.ValueTypeNames.Matrix4d)
            attr.Set(Gf.Matrix4d(comp.l2cam))
            attr = compPrimitive.CreateAttribute('l2world', Sdf.ValueTypeNames.Matrix4d)
            attr.Set(Gf.Matrix4d(comp.l2world))
            attr = compPrimitive.CreateAttribute('rotationEulerAngles', Sdf.ValueTypeNames.Vector3d)
            attr.Set(Gf.Vec3d(comp.rotationEulerAngles))
            attr = compPrimitive.CreateAttribute('translation', Sdf.ValueTypeNames.Vector3d)
            attr.Set(Gf.Vec3d(comp.translation.tolist()))
            attr = compPrimitive.CreateAttribute('trs', Sdf.ValueTypeNames.Matrix4d)
            attr.Set(Gf.Matrix4d(comp.trs.astype(float)))
            attr = compPrimitive.CreateAttribute('parent', Sdf.ValueTypeNames.String)
            attr.Set(entityPrim.GetName())

        # Saves a mesh component
        if comp.type == 'RenderMesh':
            compPrimitive = stage.DefinePrim(str(entityPrim.GetPrimPath()) + '/Mesh')
            attr = compPrimitive.CreateAttribute('points', Sdf.ValueTypeNames.Point3dArray)
            attr.Set(ConvertNumpyToGF3D(comp.vertex_attributes[0]))
            attr = compPrimitive.CreateAttribute('colors', Sdf.ValueTypeNames.Point3dArray)
            attr.Set(ConvertNumpyToGF3D(comp.vertex_attributes[1]))
            if len(comp.vertex_attributes) > 2:
                if comp.vertex_attributes[2].shape[1] > 2:
                    attr = compPrimitive.CreateAttribute('normals', Sdf.ValueTypeNames.Point3dArray)
                    attr.Set(ConvertNumpyToGF3D(comp.vertex_attributes[2]))
                else:
                    attr = compPrimitive.CreateAttribute('normals', Sdf.ValueTypeNames.Double2Array)
                    attr.Set(ConvertNumpyToGF2D(comp.vertex_attributes[2]))
            attr = compPrimitive.CreateAttribute('indices', Sdf.ValueTypeNames.IntArray)
            attr.Set(np.asarray((comp.vertex_index)))
            attr = compPrimitive.CreateAttribute('parent', Sdf.ValueTypeNames.String)
            attr.Set(entityPrim.GetName())

        # Saves a VA component
        if comp.type == 'VertexArray':
            compPrimitive = stage.DefinePrim(str(entityPrim.GetPrimPath()) + '/VA')
            attr = compPrimitive.CreateAttribute('points', Sdf.ValueTypeNames.Point3dArray)
            if comp.attributes is None:
                continue
            attr.Set(ConvertNumpyToGF3D(comp.attributes[0]))
            attr = compPrimitive.CreateAttribute('colors', Sdf.ValueTypeNames.Point3dArray)
            attr.Set(ConvertNumpyToGF3D(comp.attributes[1]))
            if len(comp.attributes) > 2:
                if comp.attributes[2].shape[1] > 2:
                    attr = compPrimitive.CreateAttribute('normals', Sdf.ValueTypeNames.Point3dArray)
                    attr.Set(ConvertNumpyToGF3D(comp.attributes[2]))
                else:
                    attr = compPrimitive.CreateAttribute('normals', Sdf.ValueTypeNames.Double2Array)
                    attr.Set(ConvertNumpyToGF2D(comp.attributes[2]))
            attr = compPrimitive.CreateAttribute('indices', Sdf.ValueTypeNames.IntArray)
            attr.Set(np.asarray(comp.index))
            attr = compPrimitive.CreateAttribute('primitive', Sdf.ValueTypeNames.Int)
            attr.Set(comp.primitive)
            attr = compPrimitive.CreateAttribute('usage', Sdf.ValueTypeNames.Int)
            attr.Set(comp.usage)
            attr = compPrimitive.CreateAttribute('parent', Sdf.ValueTypeNames.String)
            attr.Set(entityPrim.GetName())


"""
 Conversion functions from numpy to GF3D which is used in USD.
"""


def ConvertNumpyToGF3D(NPArray):
    gfArray = []
    for point in NPArray:
        gfPoint = Gf.Vec3d(point[0].astype(np.double), point[1].astype(np.double),
                           point[2].astype(np.double))
        gfArray.append(gfPoint)
    return gfArray

def ConvertNumpyToGF2D(NPArray):
    gfArray = []
    for point in NPArray:
        gfPoint = Gf.Vec2d(point[0].astype(np.double), point[1].astype(np.double))
        gfArray.append(gfPoint)
    return gfArray


def ConvertListToGF(List):
    gfArray = []
    for element in List:
        gfInt = Gf.Int(element)
        gfArray.append(gfInt)
    return gfArray


def FindEntity(scene, EntityName):
    components = scene.world.entities_components
    for k, vs in components.items():
        if k.name == EntityName:
            return k


"""
Class used to load a Usd 3D model exported from Maya.
"""


class UsdModel:
    def __init__(self, path, prim):
        stage = Usd.Stage.Open(path)
        self.prim = stage.GetPrimAtPath(prim)
        self.vertexCounts = np.array(self.prim.GetAttribute('faceVertexCounts').Get())
        self.vertexIndices = (np.array(self.prim.GetAttribute('faceVertexIndices').Get()))

        points = np.array(self.prim.GetAttribute('points').Get())
        col = np.ones((points.shape[0], 1))
        self.points = np.c_[points, col]

        color = [168 / 255, 168 / 255, 210 / 255, 1.0]
        colors = [color for _ in range(len(self.points))]
        self.colors = np.array(colors)

    """
    Loads and spawns a USD model in scene.
    Name is the path of the USD model.
    Parent is the name of the entity that the new Entity will be parented.
    """

    def DisplayUSD(self, scene, name, parent):
        entityNode = scene.world.createEntity(Entity(name=name))
        scene.world.addEntityChild(scene, entityNode)
        scene.world.addComponent(entityNode, BasicTransform(name=name + "_TRS", trs=util.scale(1, 1, 1)))

        gameObjectMesh = scene.world.addComponent(entityNode, RenderMesh(name=name + "_Mesh"))
        vertices, indices, colors, normals = norm.generateSmoothNormalsMesh(self.points, self.vertexIndices,
                                                                            self.colors)

        gameObjectMesh.vertex_attributes.append(vertices)
        gameObjectMesh.vertex_attributes.append(colors)
        gameObjectMesh.vertex_attributes.append(normals)
        gameObjectMesh.vertex_index.append(indices)

        scene.world.addComponent(entityNode, VertexArray())
        shaderDec = scene.world.addComponent(entityNode, ShaderGLDecorator(
            Shader(vertex_source=Shader.VERT_PHONG_MVP, fragment_source=Shader.FRAG_PHONG)))

        # Light
        Lposition = util.vec(2.0, 5.5, 2.0)  # uniform lightpos
        Lambientcolor = util.vec(1.0, 1.0, 1.0)  # uniform ambient color
        Lambientstr = 0.3  # uniform ambientStr
        LviewPos = util.vec(2.5, 2.8, 5.0)  # uniform viewpos
        Lcolor = util.vec(1.0, 1.0, 1.0)
        Lintensity = 0.8
        # Material
        Mshininess = 0.4
        Mcolor = util.vec(0.8, 0.0, 0.8)

        model_cube = util.scale(0.1) @ util.translate(0.0, 0.5, 0.0)
        projMat = util.perspective(50.0, 1.0, 1.0, 10.0)
        eye = util.vec(1, 0.54, 1.0)
        target = util.vec(0.02, 0.14, 0.217)
        up = util.vec(0.0, 1.0, 0.0)
        view = util.lookat(eye, target, up)
        tabletrs = util.translate(0, 0, 0)
        mvp_cube = projMat @ view @ tabletrs

        shaderDec.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
        shaderDec.setUniformVariable(key='model', value=model_cube, mat4=True)
        shaderDec.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
        shaderDec.setUniformVariable(key='ambientStr', value=Lambientstr, float1=True)
        shaderDec.setUniformVariable(key='viewPos', value=LviewPos, float3=True)
        shaderDec.setUniformVariable(key='lightPos', value=Lposition, float3=True)
        shaderDec.setUniformVariable(key='lightColor', value=Lcolor, float3=True)
        shaderDec.setUniformVariable(key='lightIntensity', value=Lintensity, float1=True)
        shaderDec.setUniformVariable(key='shininess', value=Mshininess, float1=True)
        shaderDec.setUniformVariable(key='matColor', value=Mcolor, float3=True)
        # self.objectPath = _objectPath

        return shaderDec
