# import sys
# sys.path.append('/Users/mlbeb/Desktop/boo/internship/py_code/pyECSSTree/pyECSS')
from Elements.pyGLV.skinning.skinned_mesh import Skinned_mesh
import os
from turtle import width

import numpy as np
# from sympy import true

import Elements.pyECSS.utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import  Camera, RenderMesh
from Elements.pyECSS.GA.GA_Component import GATransform
from Elements.pyECSS.System import System, TransformSystem, CameraSystem, RenderSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyECSS.ECSSManager import ECSSManager
from Elements.pyGLV.GUI.Viewer import SDL2Window, ImGUIDecorator, RenderGLStateSystem
# sys.path.append('/Users/mlbeb/Desktop/boo/internship/py_code/pyECSSTree/pyECSS/examples')
from Elements.pyECSS.GA.quaternion import Quaternion

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from OpenGL.GL import GL_LINES

import OpenGL.GL as gl




s1 = Scene()
scene = Scene()    

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))
entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)
quat = Quaternion(0,0,0,1)
trans1 = scene.world.addComponent(entityCam1, GATransform(name="trans1", q=quat))

entityCam2 = scene.world.createEntity(Entity(name="entityCam2"))
scene.world.addEntityChild(entityCam1, entityCam2)
trans2 = scene.world.addComponent(entityCam2, GATransform(name="trans2", q=quat))
orthoCam = scene.world.addComponent(entityCam2, Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0), "orthoCam","Camera","500"))

node4 = scene.world.createEntity(Entity(name="node4"))
scene.world.addEntityChild(rootEntity, node4)
trans4 = scene.world.addComponent(node4, GATransform(name="trans4", q=quat))
mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))

node5 = scene.world.createEntity(Entity(name="node5"))
scene.world.addEntityChild(rootEntity, node5)
trans5 = scene.world.addComponent(node5, GATransform(name="trans5", q=quat))
mesh5 = scene.world.addComponent(node5, RenderMesh(name="mesh5"))

axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, GATransform(name="axes_trans", q=quat))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))



# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

####################################################################################################
####################################################################################################
####################################################################################################
################# 
# ADD ENTITIES  #
#################    

dirname = os.path.dirname(__file__)

# NOTICE THAT OBJECTS WITH UVs are currently NOT SUPPORTED
# obj_to_import = os.path.join(dirname, "models", "teapot.obj")
obj_to_import = os.path.join(dirname, "models", "astroBoy_walk.dae")

## ADD FIRST SKINNED MESH ##
# attach a simple skinned mesh in a RenderMesh so that VertexArray can pick it up
# make sure you have changed the filename to the one that corresponds to your file path
a = Skinned_mesh(2,obj_to_import,"dae",True)
# a = Skinned_mesh(0,"/Users/mlbeb/Desktop/boo/internship/py_code/pyECSSTree/pyECSS/examples/cube.dae","dae",False)
# a.coloringvert()


mesh4.vertex_attributes.append(a.oldv)
mesh4.vertex_attributes.append(a.colors)
mesh4.vertex_index.append(a.f)
vArray4 = scene.world.addComponent(node4, VertexArray())
shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))


## ADD SECOND SKINNED MESH ##
# attach a simple skinned mesh in a RenderMesh so that VertexArray can pick it up
# make sure you have changed the filename to the one that corresponds to your file path
obj_to_import2 = os.path.join(dirname, "models", "astroBoy_walk.dae")
b = Skinned_mesh(3,obj_to_import2,"dae",True)
b.coloringvert()


mesh5.vertex_attributes.append(b.oldv)
mesh5.vertex_attributes.append(b.colors)
mesh5.vertex_index.append(b.f)
vArray5 = scene.world.addComponent(node5, VertexArray())
shaderDec5 = scene.world.addComponent(node5, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))


## ADD AXES ##
axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, GATransform(name="axes_trans", q=quat))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=GL_LINES)) # note the primitive change
axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))


# INITIATE SCENE#

scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "pyglGA test_renderAxesTerrainEVENT")
scene.world.traverse_visit(initUpdate, scene.world.root)

################# 
# EVENT MANAGER #
#################

eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext

renderGLEventActuator = RenderGLStateSystem()
eManager._subscribers['OnUpdateWireframe'] = gWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._subscribers['OnUpdateCamera'] = gWindow 
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator  
eManager._subscribers['OnUpdateFrames'] = gWindow   
eManager._actuators['OnUpdateFrames'] = renderGLEventActuator 
eManager._subscribers['OnUpdatePlayButton'] = gWindow   
eManager._actuators['OnUpdatePlayButton'] = renderGLEventActuator    





# CAMERA SETTINGS #

eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
# projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -1.0, 10.0) ## WORKING
# projMat = util.perspective(90.0, 1.33, 0.1, 100) ## WORKING
projMat = util.perspective(50.0, 1.0, 1.0, 10.0) ## WORKING 

model_terrain_axes = util.translate(0.0,0.0,0.0)
model_cube = util.scale(0.3) @ util.translate(0.0,0.5,0.0)

gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update


# MAIN RENDERING LOOP #

running = True

while running:
    a.updateFrames(gWindow._myFrames)
    b.updateFrames(gWindow._myFrames)
    
    if(gWindow._playMode):
        pp = mesh4.vertex_attributes
        print(mesh4.vertex_attributes[0])
        pp[0] = a.applystep(mesh4.vertex_attributes[0]) 
        vArray4.__del__()
        vArray4.attributes = pp
        vArray4.init()
        mesh4.vertex_attributes = pp
        
        pp = mesh5.vertex_attributes
        print(mesh5.vertex_attributes[0])
        pp[0] = b.applystep(mesh5.vertex_attributes[0]) 
        vArray5.__del__()
        vArray5.attributes = pp
        vArray5.init()
        mesh5.vertex_attributes = pp
    
    running = scene.render(running)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    view =  gWindow._myCamera # updates view via the imgui
    mvp_cube = projMat @ view @ model_cube
    mvp_terrain_axes = projMat @ view @ model_terrain_axes
    axes_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
    shaderDec4.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
    # shaderDec5.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
    scene.render_post()
    
scene.shutdown()


####################################################################################################
####################################################################################################
####################################################################################################


