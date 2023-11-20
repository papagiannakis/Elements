import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem

from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.utils.terrain import generateTerrain
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from OpenGL.GL import GL_LINES

from Elements.features.plotting.plotting_base import FunctionPlotting
from Elements.utils.Shortcuts import displayGUI_text
example_description = \
"This is a scene where you can plot a function either in 2D or 3D \n"

scene = Scene()

# Scenegraph with Entities, Components
rootEntity = scene.world.createEntity(Entity(name="RooT"))
entityCam1 = scene.world.createEntity(Entity(name="entityCam1"))
scene.world.addEntityChild(rootEntity, entityCam1)
trans1 = scene.world.addComponent(entityCam1, BasicTransform(name="trans1", trs=util.identity()))

entityCam2 = scene.world.createEntity(Entity(name="entityCam2"))
scene.world.addEntityChild(entityCam1, entityCam2)
trans2 = scene.world.addComponent(entityCam2, BasicTransform(name="trans2", trs=util.identity()))
# orthoCam = scene.world.addComponent(entityCam2, Camera(util.ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0), "orthoCam","Camera","500"))

node4 = scene.world.createEntity(Entity(name="node4"))
scene.world.addEntityChild(rootEntity, node4)
trans4 = scene.world.addComponent(node4,
                                  BasicTransform(name="trans4", trs=util.translate(0, 0.5, 0)))  # util.identity()
mesh4 = scene.world.addComponent(node4, RenderMesh(name="mesh4"))

axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.identity()))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))

# initialize wrapper for 2d and 3d shaders
shader_2d = []
shader_3d = []

# Colored Axes
vertexAxes = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
], dtype=np.float32)
colorAxes = np.array([
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
], dtype=np.float32)

# index arrays for above vertex Arrays
indexAxes = np.array((0, 1, 2, 3, 4, 5), np.uint32)  # 3 simple colored Axes as R,G,B lines


# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
# camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

# Generate terrain

vertexTerrain, indexTerrain, colorTerrain = generateTerrain(size=4, N=20)
# Add terrain
terrain = scene.world.createEntity(Entity(name="terrain"))
scene.world.addEntityChild(rootEntity, terrain)
terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
terrain_mesh.vertex_attributes.append(vertexTerrain)
terrain_mesh.vertex_attributes.append(colorTerrain)
terrain_mesh.vertex_index.append(indexTerrain)
terrain_vArray = scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(
    Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
shader_2d.append(terrain_shader)

## ADD AXES ##
axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.identity()))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_mesh.vertex_attributes.append(vertexAxes)
axes_mesh.vertex_attributes.append(colorAxes)
axes_mesh.vertex_index.append(indexAxes)
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=GL_LINES))

axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(
    Shader(vertex_source=Shader.COLOR_VERT_MVP, fragment_source=Shader.COLOR_FRAG)))
shader_2d.append(axes_shader)


# entities for 2d and 3d function plotting
function2d_entity = scene.world.createEntity(Entity(name="function2d_entity"))
scene.world.addEntityChild(rootEntity, function2d_entity)
function3d_entity = scene.world.createEntity(Entity(name="function3d_entity"))
scene.world.addEntityChild(rootEntity, function3d_entity)

# initialize function plotting object
function_plotting = FunctionPlotting(function2d_entity, function3d_entity, scene, rootEntity, shader_2d, shader_3d, initUpdate)


# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth=1024, windowHeight=768, windowTitle="Elements: Function Plotting",
           openGLversion=4)

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

projMat = util.perspective(50.0, 1.0, 0.01, 10.0)
gWindow._myCamera = view
model_terrain_axes = terrain.getChild(0).trs


while running:
    running = scene.render()
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    view = gWindow._myCamera  # updates view via the imgui

    mvp_terrain_axes = projMat @ view @ model_terrain_axes

    # trigger actual function plotting and gui
    function_plotting.render_gui_and_plots()

    # set uniform variables for all calssical shaders
    for shader in shader_2d:
        shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)

    displayGUI_text(example_description)
    # set uniform variables for all phong shaders
    for shader in shader_3d:
        Lposition = util.vec(1,3,2)
        Lambientcolor = util.vec(1.0, 1.0, 5.0)  # uniform ambient color
        Lambientstr = 0.1  # uniform ambientStr
        LviewPos = util.vec(2.5, 2.8, 5.0)  # uniform viewpos
        Lcolor = util.vec(1.0, 1.0, 1.0)
        Lintensity = 0.5
        # Material
        Mshininess = 0.0
        Mcolor = util.vec(0.7, 0.35, 0.0)
        
        shader.setUniformVariable(key='modelViewProj', value=mvp_terrain_axes, mat4=True)
        shader.setUniformVariable(key='model', value=mvp_terrain_axes, mat4=True)
        shader.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
        shader.setUniformVariable(key='ambientStr', value=Lambientstr, float1=True)
        shader.setUniformVariable(key='viewPos', value=LviewPos, float3=True)
        shader.setUniformVariable(key='lightPos', value=Lposition, float3=True)
        shader.setUniformVariable(key='lightColor', value=Lcolor, float3=True)
        shader.setUniformVariable(key='lightIntensity', value=Lintensity, float1=True)
        shader.setUniformVariable(key='shininess', value=Mshininess, float1=True)
        shader.setUniformVariable(key='matColor', value=Mcolor, float3=True)

    scene.render_post()

scene.shutdown()