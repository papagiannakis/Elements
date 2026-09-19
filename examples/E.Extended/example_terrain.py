"""
The reference grids from Elements.utils.terrain.generateTerrain, on their own.

Nothing is in this scene except the grids and the coloured axes, so it is the place to check what
generateTerrain actually produces and to fly around it: the ground grid on y=0, plus the two
optional upright planes on x=0 and z=0 that sizeX/sizeZ switch on.

Together the three planes answer "where am I?" while navigating -- the ground gives position on the
floor, and the upright pair gives height, which a single ground grid cannot.
"""

import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.utils.terrain import generateTerrain
from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import SHADER_DIR

from OpenGL.GL import GL_LINES

#: half-width of the ground grid: it spans [-TERRAIN_SIZE, TERRAIN_SIZE] in both x and z
TERRAIN_SIZE = 5
#: 0 lets generateTerrain pick the line count, which it does so the cells come out 1 unit across
TERRAIN_N = 0
#: vertical extent of the two upright planes; [0, 0] would leave them out
PLANE_HEIGHT = [0.0, 2.0]

example_description = \
"The reference grids from Elements.utils.terrain, on their own.\n\n\
Ground grid on y=0, spanning " + str(2 * TERRAIN_SIZE) + " x " + str(2 * TERRAIN_SIZE) + " units,\n\
plus the upright planes on x=0 and z=0 rising to y=" + str(PLANE_HEIGHT[1]) + ".\n\
All three share their grid spacing, so they line up where they meet.\n\
The coloured axes mark the origin: R=x, G=y, B=z.\n\n\
Hold the RIGHT mouse button to fly:\n\
  drag to look, W/A/S/D to move, Q/E to rise/sink,\n\
  SPACE to aim back at the origin.\n\
Scroll to change the fly speed (printed on the terminal).\n\
Hit ESC OR Close the window to quit."

winWidth = 1024
winHeight = 768

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))

## ADD THE TERRAIN ##
# sizeX/sizeZ each give a *vertical* range: the horizontal extent comes from size, which is what
# makes the upright planes meet the ground grid line-for-line.
vertexTerrain, indexTerrain, colorTerrain = generateTerrain(
    size=TERRAIN_SIZE,
    N=TERRAIN_N,
    sizeX=PLANE_HEIGHT,
    sizeZ=PLANE_HEIGHT,
)
terrain = scene.world.createEntity(Entity(name="terrain"))
scene.world.addEntityChild(rootEntity, terrain)
terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
terrain_mesh.vertex_attributes.append(vertexTerrain)
terrain_mesh.vertex_attributes.append(colorTerrain)
terrain_mesh.vertex_index.append(indexTerrain)
terrain_vArray = scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))

## ADD THE AXES ##
# Scaled to the grid so they read across the whole thing rather than sitting in one cell.
vertexAxes = np.array([
    [0.0, 0.0, 0.0, 1.0], [TERRAIN_SIZE, 0.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0], [0.0, PLANE_HEIGHT[1], 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0], [0.0, 0.0, TERRAIN_SIZE, 1.0],
], dtype=np.float32)
colorAxes = np.array([
    [1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0], [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0], [0.0, 0.0, 1.0, 1.0],
], dtype=np.float32)
indexAxes = np.array((0, 1, 2, 3, 4, 5), np.uint32)

axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
# Nudged off the planes: the x and z axes would otherwise be exactly coincident with the grid's own
# centre lines, and which one wins the depth test per pixel is arbitrary (z-fighting).
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.translate(0.0, 0.002, 0.0)))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_mesh.vertex_attributes.append(vertexAxes)
axes_mesh.vertex_attributes.append(colorAxes)
axes_mesh.vertex_index.append(indexAxes)
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=GL_LINES))
axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))

# Systems
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

# MAIN RENDERING LOOP
running = True
scene.init(imgui=True, windowWidth=winWidth, windowHeight=winHeight,
           windowTitle="Elements: terrain reference grids", customImGUIdecorator=ImGUIecssDecorator2,
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

eye = util.vec(6.0, 4.0, 8.0)
target = util.vec(0.0, 0.5, 0.0)
up = util.vec(0.0, 1.0, 0.0)

# Set the camera through the decorator, not by assigning gWindow._myCamera: createViewMatrix also
# stores eye/target/up, which is what the right-button look/fly controls read and update. Assigning
# the view matrix alone would leave them at their defaults, and the first drag would jump the camera.
gGUI.createViewMatrix(eye, target, up)

projMat = util.perspective(50.0, winWidth / winHeight, 0.01, 100.0)

model_terrain = terrain_trans.trs
model_axes = axes_trans.trs

while running:
    running = scene.render()
    displayGUI_text(example_description)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.world.traverse_visit(transUpdate, scene.world.root)

    view = gWindow._myCamera
    terrain_shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ model_terrain, mat4=True)
    axes_shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ model_axes, mat4=True)

    scene.render_post()

scene.shutdown()
