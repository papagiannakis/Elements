import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from Elements.utils.terrain import generateTerrain
from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import SHADER_DIR

from OpenGL.GL import GL_LINES

example_description = \
"A cube, a ground grid and the RGB axes. All three are built the same way:\n\
an Entity holding a BasicTransform, a RenderMesh, a VertexArray and a shader.\n\
Only the primitive differs -- triangles for the cube, GL_LINES for the other two.\n\n\
The panel on the left is the scenegraph, read only.\n\n\
Hold the RIGHT mouse button to fly: drag to look, W/A/S/D to move,\n\
Q/E to rise/sink, SPACE to aim back at the origin. Scroll changes the speed.\n\
Hit ESC OR Close the window to quit."

winWidth = 1024
winHeight = 768

# ---------------- geometry ----------------

# the 8 corners of a cube, a colour for each
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
# which corners each triangle joins: 6 faces, 2 triangles per face
indexCube = np.array((1,0,3, 1,3,2,
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32)

# three lines out of the origin, one per axis: x red, y green, z blue
vertexAxes = np.array([
    [0.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
],dtype=np.float32)
colorAxes = np.array([
    [1.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 1.0],
    [0.0, 0.0, 1.0, 1.0]
], dtype=np.float32)
indexAxes = np.array((0,1,2,3,4,5), np.uint32)

# the ground grid: 2*size across, cells 1 unit wide (see Elements.utils.terrain)
vertexTerrain, indexTerrain, colorTerrain = generateTerrain(size=4)

# ---------------- the scene: RooT -> cube, terrain, axes ----------------

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))

## THE CUBE ##
cube = scene.world.createEntity(Entity(name="cube"))
scene.world.addEntityChild(rootEntity, cube)
# translate @ rotate @ scale, applied right-to-left: scaled first, then turned, then moved
cube_trans = scene.world.addComponent(cube, BasicTransform(name="cube_trans",
    trs=util.translate(0,0.5,0) @ util.rotate(axis=(0.0, 1.0, 0.0), angle=45.0) @ util.scale(1.1,1.1,1.1)))
cube_mesh = scene.world.addComponent(cube, RenderMesh(name="cube_mesh"))
cube_mesh.vertex_attributes.append(vertexCube)      # attribute 0, read by the shader as vPosition
cube_mesh.vertex_attributes.append(colorCube)       # attribute 1, read as vColor
cube_mesh.vertex_index.append(indexCube)
cube_vArray = scene.world.addComponent(cube, VertexArray())
cube_shader = scene.world.addComponent(cube, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))

## THE TERRAIN ##
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

## THE AXES ##
axes = scene.world.createEntity(Entity(name="axes"))
scene.world.addEntityChild(rootEntity, axes)
# lifted a hair off the ground, or the x and z axes would fight the grid lines they sit on
axes_trans = scene.world.addComponent(axes, BasicTransform(name="axes_trans", trs=util.translate(0.0, 0.001, 0.0)))
axes_mesh = scene.world.addComponent(axes, RenderMesh(name="axes_mesh"))
axes_mesh.vertex_attributes.append(vertexAxes)
axes_mesh.vertex_attributes.append(colorAxes)
axes_mesh.vertex_index.append(indexAxes)
axes_vArray = scene.world.addComponent(axes, VertexArray(primitive=GL_LINES))
axes_shader = scene.world.addComponent(axes, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))

# ---------------- systems ----------------

initUpdate = scene.world.createSystem(InitGLShaderSystem())
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())

scene.world.print()

# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight,
           windowTitle = "Cube, axes and terrain", customImGUIdecorator = ImGUIecssDecorator2,
           openGLversion = 4)

# pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
# needs an active GL context
scene.world.traverse_visit(initUpdate, scene.world.root)

# ---------------- the window, the GUI and the camera ----------------

gWindow = scene.renderWindow    # the SDL2 window: the pixels, the mouse and the keyboard
gGUI = scene.gContext           # the ImGUI layer wrapped around it, which also owns the camera

# Both are plain objects -- print them, or reach in and change things while the scene runs:
#
#   gWindow._myCamera                    the view matrix; read below, written by the mouse
#   gWindow._cameraEye / _cameraTarget   where the camera is and what it looks at
#   gWindow._windowWidth / _windowHeight kept up to date when the window is resized
#   gWindow._wireframeMode               True draws every triangle as lines (the F key)
#
#   gGUI.createViewMatrix(eye, target, up)   place the camera from code, as below
#   gGUI._eye / _target / _up                where it is right now
#   gGUI.flySpeed                            world units per frame for W/A/S/D and Q/E
#   gGUI.resetTarget()                       aim back at the origin (the SPACE key)
#   gGUI._colorEditor                        background colour, (r, g, b) in 0..1

eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
# createViewMatrix, rather than setting gWindow._myCamera: it also stores eye/target/up, which is
# what the mouse/keyboard camera reads and updates
gGUI.createViewMatrix(eye, target, up)

projMat = util.perspective(50.0, winWidth/winHeight, 0.01, 100.0)

# each object's own placement in the world; the camera supplies the rest of the MVP each frame
model_cube = cube_trans.trs
model_terrain = terrain_trans.trs
model_axes = axes_trans.trs

while running:
    running = scene.render()
    displayGUI_text(example_description)
    scene.world.traverse_visit(renderUpdate, scene.world.root)

    view = gWindow._myCamera   # the mouse and the GUI both write here
    cube_shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ model_cube, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ model_terrain, mat4=True)
    axes_shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ model_axes, mat4=True)

    scene.render_post()

scene.shutdown()
