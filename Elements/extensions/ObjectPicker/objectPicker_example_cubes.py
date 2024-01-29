import numpy as np
import os
import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import  TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.features.ObjectPicker.Gizmos import Gizmos
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray


from Elements.utils.Shortcuts import displayGUI_text
from Elements.features.ObjectPicker.AABoundingBox import AABoundingBox
from OpenGL.GL import GL_LINES

from Elements.features.BasicShapes.BasicShapes import CubeSpawn

example_description = """
This is a scene that contains multiple cubes at random places.
is possible via the mouse or the GUI

Gizmos Instructions:
Click on the scene to select an object. You can then manipulate
it by alt+clicking on the gizmos that appear, by pressing the 
respective key:

T: translation
R: Rotation
S: Scaling
D: Make the Gizmo Disappear

You can reset an object to its original position by pressing '0'

To use the Gizmos hover over them, press and hold the Left-alt-key + Left-mouse-button and 
move the cursor to see the result
"""

#Light
Lposition = util.vec(0.0, 2.5, 1.2) #uniform lightpos
Lambientcolor = util.vec(1.0, 1.0, 1.0) #uniform ambient color
Lambientstr = 0.3 #uniform ambientStr
LviewPos = util.vec(2.5, 2.8, 5.0) #uniform viewpos
Lcolor = util.vec(1.0,1.0,1.0)
Lintensity = 0.9
#Material
Mshininess = 0.4 
Mcolor = util.vec(1.0, 0.0, 0.8)


scene = Scene()    

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))
entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.translate(2.5, 2.5, 2.5)))



# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

# Add ground


cubes = scene.world.createEntity(Entity(name="cubes"))
scene.world.addEntityChild(rootEntity, cubes)

for i in range(125):
    cube = CubeSpawn("cube"+str(i))
    scene.world.addEntityChild(cubes, cube)
    cube.trans.trs = util.translate(np.random.uniform(-1,1,3), 3+np.random.uniform(-1,1,3), np.random.uniform(-1,1,3))@util.scale(0.1)
    bounding_box = scene.world.addComponent(cube, AABoundingBox(name="AABoundingBox", vertices = cube.mesh.vertex_attributes[0]))
    cube.shaderDec.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True);
    cube.shaderDec.setUniformVariable(key='ambientStr', value=Lambientstr, float1=True);
    cube.shaderDec.setUniformVariable(key='viewPos', value=LviewPos, float3=True);
    cube.shaderDec.setUniformVariable(key='lightPos', value=Lposition, float3=True);
    cube.shaderDec.setUniformVariable(key='lightColor', value=Lcolor, float3=True);
    cube.shaderDec.setUniformVariable(key='lightIntensity', value=Lintensity, float1=True);
    cube.shaderDec.setUniformVariable(key='shininess',value=Mshininess,float1=True)
    cube.shaderDec.setUniformVariable(key='matColor',value=Mcolor,float3=True)


eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
width = 1024.0
height = 768.0
fov = 50.0
aspect_ratio = width/height
near = 0.01
far = 60.0
projMat = util.perspective(fov, aspect_ratio, near, far)

gizmos = Gizmos(rootEntity)
gizmos.set_camera_in_use("entityCam1")
gizmos.update_projection(projMat)
gizmos.update_view(view)
gizmos.update_screen_dimensions(window_width=width,window_height=height)

# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements: Multiple Cubes ObjectPicker", openGLversion = 4)

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

gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update


while running:
    running = scene.render()
    scene.world.traverse_visit(transUpdate, scene.world.root) 
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    displayGUI_text(example_description)
    view =  gWindow._myCamera # updates view via the imgui
    height = scene.renderWindow._windowHeight
    width = scene.renderWindow._windowWidth
    
    gizmos.update_screen_dimensions(window_width=width,window_height=height)
    gizmos.update_view(view)
    gizmos.update_ray_start()
    gizmos.get_Event()
    gizmos.update_imgui()
    

    for i in range(125):
        cubes.getChild(i).shaderDec.setUniformVariable(key='modelViewProj', value=projMat @ view @ cubes.getChild(i).trans.l2world, mat4=True);
        cubes.getChild(i).shaderDec.setUniformVariable(key='model',value=cubes.getChild(i).trans.l2world ,mat4=True)


    scene.render_post()
    
scene.shutdown()