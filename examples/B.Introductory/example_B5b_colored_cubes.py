import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import SHADER_DIR

example_description = \
"The same cube twice, plain colours, no lights: what you see is only the vColor\n\
attribute interpolated across each triangle. Both cubes ask for the very same\n\
thing -- 'paint the front face cyan, the rest grey' -- and only the SPLIT one\n\
can deliver it:\n\n\
  left  SPLIT   36 vertices, one per index: every face owns its 4 corners, so\n\
                the 6 vertices of the front face go cyan and nothing else does\n\
  right SHARED  the 8 cube corners, each used by 3 faces: colouring the 4 front\n\
                corners cyan also colours a corner of the top/bottom/left/right\n\
                faces, and the rasteriser blends it across them\n\n\
Colour lives on the VERTEX, not on the face. A face gets its own colour only if\n\
it gets its own vertices -- the same reason flat shading has to split a mesh to\n\
give each face its own normal.\n\n\
Right mouse button to fly around, F for wireframe. Hit ESC OR Close the window to quit."

winWidth = 1200
winHeight = 800

CYAN = [0.0, 1.0, 1.0, 1.0]
GREY = [0.35, 0.35, 0.38, 1.0]

# ---------------- geometry ----------------

# the 8 corners of a cube
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
# which corners each triangle joins: 6 faces, 2 triangles per face.
# The first 6 indices are the front face (z = +0.5), built from corners 0,1,2,3.
indexCube = np.array((1,0,3, 1,3,2,     # front  <-- the face we want cyan
                  2,3,7, 2,7,6,         # right
                  3,0,4, 3,4,7,         # bottom
                  6,5,1, 6,1,2,         # top
                  4,5,6, 4,6,7,         # back
                  5,4,0, 5,0,1), np.uint32)   # left

## THE SPLIT CUBE: one vertex per index, 8 corners -> 36 vertices ##
# Every triangle now owns its 3 vertices outright, shared with nobody, so the index
# buffer is just 0,1,2,3,... A corner of the cube exists 6 times over (once per
# triangle meeting there) and each copy can carry a different colour.
vertexSplit = vertexCube[indexCube]                      # 36 positions
indexSplit = np.arange(len(vertexSplit), dtype=np.uint32)
colorSplit = np.array([GREY] * len(vertexSplit), dtype=np.float32)
# indices 0..5 are the front face's two triangles: colour exactly those 6 vertices.
# Its neighbours keep their own grey copies of the same corners, so the cyan stops
# dead at the edge -- one crisp cyan side.
colorSplit[0:6] = CYAN
# colorSplit[0:3] = CYAN    ## try this instead: 3 vertices -> a single cyan TRIANGLE

## THE SHARED CUBE: the 8 corners as they are ##
# Corner 2, say, is the top-right of the front face, but it is also a corner of the
# top face and of the right face -- one vertex, one colour, read by all three.
vertexShared = vertexCube.copy()
indexShared = indexCube.copy()
colorShared = np.array([GREY] * 8, dtype=np.float32)
# corners 0,1,2,3 are the front face. Asking for a cyan front face here paints 4 of
# the 8 corners cyan, and every triangle touching them fades from cyan to grey.
colorShared[[0, 1, 2, 3]] = CYAN

# ---------------- the scene: RooT -> split cube, shared cube ----------------

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))

## THE SPLIT CUBE, on the left ##
cubeSplit = scene.world.createEntity(Entity(name="cube_split"))
scene.world.addEntityChild(rootEntity, cubeSplit)
cubeSplit_trans = scene.world.addComponent(cubeSplit, BasicTransform(name="cube_split_trans", trs=util.translate(-0.6,0.3,0) @ util.scale(0.6)))
cubeSplit_mesh = scene.world.addComponent(cubeSplit, RenderMesh(name="cube_split_mesh"))
cubeSplit_mesh.vertex_attributes.append(vertexSplit)    # attribute 0, read by the shader as vPosition
cubeSplit_mesh.vertex_attributes.append(colorSplit)     # attribute 1, read as vColor
cubeSplit_mesh.vertex_index.append(indexSplit)
cubeSplit_vArray = scene.world.addComponent(cubeSplit, VertexArray())
cubeSplit_shader = scene.world.addComponent(cubeSplit, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))

## THE SHARED CUBE, on the right -- same corners, same shader, fewer vertices ##
cubeShared = scene.world.createEntity(Entity(name="cube_shared"))
scene.world.addEntityChild(rootEntity, cubeShared)
cubeShared_trans = scene.world.addComponent(cubeShared, BasicTransform(name="cube_shared_trans", trs=util.translate(0.6,0.3,0) @ util.scale(0.6)))
cubeShared_mesh = scene.world.addComponent(cubeShared, RenderMesh(name="cube_shared_mesh"))
cubeShared_mesh.vertex_attributes.append(vertexShared)
cubeShared_mesh.vertex_attributes.append(colorShared)
cubeShared_mesh.vertex_index.append(indexShared)
cubeShared_vArray = scene.world.addComponent(cubeShared, VertexArray())
cubeShared_shader = scene.world.addComponent(cubeShared, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))

# ---------------- systems ----------------

initUpdate = scene.world.createSystem(InitGLShaderSystem())
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())

# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight,
           windowTitle = "Elements: One Face, One Colour", openGLversion = 4,
           customImGUIdecorator = ImGUIecssDecorator2)

# pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
# needs an active GL context
scene.world.traverse_visit(initUpdate, scene.world.root)

# ---------------- the window, the GUI and the camera ----------------

gWindow = scene.renderWindow
gGUI = scene.gContext

eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
gGUI.createViewMatrix(eye, target, up)

projMat = util.perspective(50.0, winWidth/winHeight, 0.01, 100.0)

# the plain shader needs one uniform only: where the cube ends up on screen
drawn_objects = [(cubeSplit_shader, cubeSplit_trans), (cubeShared_shader, cubeShared_trans)]

while running:
    running = scene.render()
    displayGUI_text(example_description)

    view = gWindow._myCamera    # the mouse and the GUI both write here

    for shader, trans in drawn_objects:
        shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ trans.trs, mat4=True)

    # render after the uniforms are set, so this frame draws with this frame's camera
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()
