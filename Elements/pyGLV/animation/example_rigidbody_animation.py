import numpy as np

import Elements.pyECSS.utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import  TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem, ImGUIecssDecorator

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from OpenGL.GL import GL_LINES

from Elements.pyGLV.animation.animationCS import *
import imgui

#Simple Cube
vertexCube = np.array([ [-0.5, -0.5, 0.5, 1.0], [-0.5, 0.5, 0.5, 1.0], [0.5, 0.5, 0.5, 1.0], [0.5, -0.5, 0.5, 1.0], [-0.5, -0.5, -0.5, 1.0], [-0.5, 0.5, -0.5, 1.0], [0.5, 0.5, -0.5, 1.0], [0.5, -0.5, -0.5, 1.0] ],dtype=np.float32) 
colorCube = np.array([ [0.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0], [1.0, 1.0, 0.0, 1.0], [0.0, 1.0, 0.0, 1.0], [0.0, 0.0, 1.0, 1.0], [1.0, 0.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [0.0, 1.0, 1.0, 1.0] ], dtype=np.float32)
indexCube = np.array((1,0,3, 1,3,2, 2,3,7, 2,7,6, 3,0,4, 3,4,7, 6,5,1, 6,1,2, 4,5,6, 4,6,7, 5,4,0, 5,0,1), np.uint32) #rhombus out of two triangles

#Colored Axes
vertexAxes = np.array([ [0.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 1.0], [0.0, 1.0, 0.0, 1.0], [0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 1.0, 1.0] ]) 
colorAxes = np.array([ [1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0], [0.0, 1.0, 0.0, 1.0], [0.0, 1.0, 0.0, 1.0], [0.0, 0.0, 1.0, 1.0], [0.0, 0.0, 1.0, 1.0] ])
indexAxes = np.array((0,1,2,3,4,5), np.uint32) #3 simple colored Axes as R,G,B lines

# Generate terrain
from Elements.pyGLV.utils.terrain import generateTerrain
vertexTerrain, indexTerrain, colorTerrain= generateTerrain(size=4,N=20)




scene = Scene()    

# Systems
# transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
# camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())



# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))
entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.identity()))

## ADD CUBE ##
node4 = scene.world.createEntity(Entity(name="node4"))
scene.world.addEntityChild(rootEntity, node4)
# trans4 = scene.world.addComponent(node4, AnimationTransform(name="anim_trans4", first_vec=[0,0,0], next_vec=[6,4,-3]))
# trans4 = scene.world.addComponent(node4, BasicTransform(name="trans4", trs=util.identity()))
trans4 = scene.world.addComponent(node4, AnimationTransform(name="trans4", trs=util.identity(),next_vec=[6,4,-3],method='lerp'))
mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))

mesh4.vertex_attributes.append(vertexCube)
mesh4.vertex_attributes.append(colorCube)
mesh4.vertex_index.append(indexCube)
vArray4 = scene.world.addComponent(node4, VertexArray())
shaderDec4 = scene.world.addComponent(node4, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))

## ADD AXES ##
axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.identity()))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_mesh.vertex_attributes.append(vertexAxes) 
axes_mesh.vertex_attributes.append(colorAxes)
axes_mesh.vertex_index.append(indexAxes)
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=GL_LINES)) 
axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))



# Add terrain
terrain = scene.world.createEntity(Entity(name="terrain"))
scene.world.addEntityChild(rootEntity, terrain)
terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
terrain_mesh.vertex_attributes.append(vertexTerrain) 
terrain_mesh.vertex_attributes.append(colorTerrain)
terrain_mesh.vertex_index.append(indexTerrain)
terrain_vArray = scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(Shader(vertex_source = Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))




model_terrain_axes = terrain.getChild(0).trs # notice that terrain.getChild(0) == terrain_trans

# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = 1024, windowHeight = 768, windowTitle = "Elements: A Working Event Manager", openGLversion = 4, customImGUIdecorator= ImGUIecssDecorator)

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
projMat = util.perspective(50.0, 1.0, 0.01, 10.0) 
gWindow._myCamera = view # otherwise, an imgui slider must be moved to properly update


# model_cube = trans4.current_frame_trs
model_terrain_axes = terrain_trans.trs
## OR
# model_cube = util.scale(0.3) @ util.translate(0.0,0.5,0.0) ## COMPLETELY OVERRIDE OBJECT's TRS
## OR
# model_cube =  trans4.trs @ util.scale(0.3) @ util.translate(0.0,0.5,0.0) ## TAMPER WITH OBJECT's TRS

frame_rate = 0
play_animation = False
bezier_interpolation = True if trans4.method == "bezier" else False
lerp_interpolation = not bezier_interpolation

# init_vec = trans4.trs[:3,3]
def displayGUI():
    # global widgets_basic_str0
    # global latest
    # global n
    # global changed
    global frame_rate
    global trans4
    global play_animation
    global init_vec
    global bezier_interpolation
    global lerp_interpolation

    imgui.begin("frame_rate")
    changed, play_animation = imgui.checkbox("PLAY ANIMATION", play_animation)
    changed, frame_rate = imgui.drag_float("frame_rate", frame_rate, format="%.1f", min_value=0 ,change_speed = 0.01)
    changed, init_vec = imgui.drag_float3("initial position", *trans4.first_vec, format="%.1f",change_speed = 0.01)
    if changed:
        trans4.first_vec = init_vec

    # changed1, lerp_interpolation = imgui.checkbox("Lerp Interpolation", lerp_interpolation)
    # imgui.same_line(spacing=50)
    changed, bezier_interpolation = imgui.checkbox("Bezier Interpolation", bezier_interpolation)
    if changed: 
        if bezier_interpolation: 
            trans4.method = "bezier"
            lerp_interpolation = False

    if play_animation:
        trans4.update_frame(frame_rate)
    imgui.text("Current frame: %.1f" % (trans4._current_frame))
    imgui.end()



while running:
    running = scene.render()
    displayGUI()
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    view =  gWindow._myCamera # updates view via the imgui
    mvp_cube = projMat @ view @ util.scale(0.2) @ trans4.trs
    # if trans4._current_frame <99:
    #     trans4.update_frame(1)
    shaderDec4.setUniformVariable(key='modelViewProj', value=mvp_cube, mat4=True)
    mvp_terrain_axes = projMat @ view @ model_terrain_axes
    axes_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
    scene.render_post()
    # n+=1
    
scene.shutdown()


print(trans4.parent._children[1].name)


# ############




