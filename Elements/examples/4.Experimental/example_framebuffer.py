import numpy as np
import os
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import  TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import IMGUIecssDecoratorBundle, ImGUIecssDecorator

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
import Elements.utils.normals as norm
from Elements.pyGLV.GL.Textures import get_texture_faces
from Elements.pyGLV.GL.Textures import get_single_texture_faces

from Elements.definitions import TEXTURE_DIR

from Elements.utils.Shortcuts import displayGUI_text


example_description = \
"This example demonstrates the cube map texture, i.e., \n\
we encapsulate the scene into a huge cube and apply texture to them\n\
creating the illusion of a scenery. \n\
You may move the camera using the mouse or the GUI. \n\
You may see the ECS Scenegraph showing Entities & Components of the scene and \n\
various information about them. Hit ESC OR Close the window to quit." 


winWidth = 1024
winHeight = 768

eye = util.vec(1, 0.54, 1.0)
target = util.vec(0.02, 0.14, 0.217)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
projMat = util.perspective(50.0, 1.0, 1.0, 10.0)   

# Scenegraph with Entities, Components
scene = Scene()    
rootEntity = scene.world.createEntity(Entity(name="Root"))

node4 = scene.world.createEntity(Entity(name="node4"))
scene.world.addEntityChild(rootEntity, node4)
trans4 = scene.world.addComponent(node4, BasicTransform(name="trans4", trs=util.identity())) #util.identity()
mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))

#Simple Cube
vertexCube = np.array([
    [-0.5, -0.5, 0.5, 1.0],
    [-0.5, 0.5, 0.5, 1.0],
    [0.5, 0.5, 0.5, 1.0],
    [0.5, -0.5, 0.5, 1.0], 
    [-0.5, -0.5, -0.5, 1.0], 
    [-0.5, 0.5, -0.5, 1.0], 
    [0.5, 0.5, -0.5, 1.0], 
    [0.5, -0.5, -0.5, 1.0]
],dtype=np.float32) 

colorCube = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [1.0, 0.0, 1.0, 1.0],
    [1.0, 1.0, 1.0, 1.0],
    [0.0, 1.0, 1.0, 1.0]
], dtype=np.float32)

indexCube = np.array((1,0,3, 1,3,2, 
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32) 

## ADD CUBE ##
# attach a simple cube in a RenderMesh so that VertexArray can pick it up
mesh4.vertex_attributes.append(vertexCube)
mesh4.vertex_attributes.append(colorCube)
mesh4.vertex_index.append(indexCube)
vArray4 = scene.world.addComponent(node4, VertexArray())

model = util.translate(0.0,0.0,0.5)@util.scale(3)
eye = util.vec(1.0, 1.0, 1.0)
target = util.vec(0,0.0,0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)

# projMat = util.perspective(120.0, 1.33, 0.1, 100.0)
projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -10, 10.0)

mvpMat =  projMat @ view @ model


shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
shaderDec4.setUniformVariable(key='modelViewProj', value=mvpMat, mat4=True)


# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

vertexCube, indexCube, _ = norm.generateUniqueVertices(vertexCube,indexCube)

# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight, windowTitle = "Elements: Cube Mapping Example", customImGUIdecorator = IMGUIecssDecoratorBundle, openGLversion = 4)


# pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
# needs an active GL context
scene.world.traverse_visit(initUpdate, scene.world.root)


################### EVENT MANAGER ###################

eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext

renderGLEventActuator = RenderGLStateSystem()


eManager._subscribers['OnUpdateWireframe'] = gWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._subscribers['OnUpdateCamera'] = gWindow 
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator


eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
projMat = util.perspective(50.0, 1.0, 0.01, 100.0)   

gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update


while running:
    running = scene.render()
    displayGUI_text(example_description)
    scene.world.traverse_visit(transUpdate, scene.world.root)    
    
    view =  gWindow._myCamera # updates view via the imgui

    shaderDec4.setUniformVariable(key='Proj', value=projMat, mat4=True)
    shaderDec4.setUniformVariable(key='View', value=view, mat4=True)
    shaderDec4.setUniformVariable(key='model', value=trans4.l2world, mat4=True)
   
    scene.world.traverse_visit(renderUpdate, scene.world.root) 
    
    scene.render_post()

scene.shutdown()