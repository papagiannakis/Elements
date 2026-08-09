import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import RenderMesh
from Elements.pyGLV.GL.Scene import Scene

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import SHADER_DIR

example_description = \
"One coloured cube, placed on screen by a single Model-View-Projection matrix:\n\n\
  model   where the cube sits in the world\n\
  view    where the camera is  (util.lookat, from eye / target / up)\n\
  projMat how the world is flattened onto the screen\n\n\
The MVP is sent to the shader once, before the loop, so the camera cannot move.\n\
Hit ESC OR Close the window to quit."

winWidth = 1024
winHeight = 768

# ---------------- geometry: the 8 corners of a cube, a colour for each ----------------

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

# ---------------- the scene: RooT -> cube ----------------

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))

cube = scene.world.createEntity(Entity(name="cube"))
scene.world.addEntityChild(rootEntity, cube)

# RenderMesh holds the data, VertexArray uploads it to the GPU, ShaderGLDecorator draws it
cube_mesh = scene.world.addComponent(cube, RenderMesh(name="cube_mesh"))
cube_mesh.vertex_attributes.append(vertexCube)      # attribute 0, read by the shader as vPosition
cube_mesh.vertex_attributes.append(colorCube)       # attribute 1, read as vColor
cube_mesh.vertex_index.append(indexCube)
cube_vArray = scene.world.addComponent(cube, VertexArray())
cube_shader = scene.world.addComponent(cube, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))

# ---------------- the MVP matrix ----------------

model = util.translate(0.0,0.0,0.5) @ util.scale(3)

eye = util.vec(3.0, 3.0, 3.0)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)

projMat = util.ortho(-10.0, 10.0, -10.0, 10.0, -10.0, 10.0)
# projMat = util.perspective(120.0, 1.33, 0.1, 100.0)   ## try this instead

# right-to-left: the cube is placed, then seen from the camera, then projected
cube_shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ model, mat4=True)

# ---------------- systems ----------------

initUpdate = scene.world.createSystem(InitGLShaderSystem())
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())

scene.world.print()

# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight, windowTitle = "A Cube Scene via ECSS")

# pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
# needs an active GL context
scene.world.traverse_visit(initUpdate, scene.world.root)

while running:
    running = scene.render()
    displayGUI_text(example_description)
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()
