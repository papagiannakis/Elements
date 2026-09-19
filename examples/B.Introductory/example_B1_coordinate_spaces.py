"""
Everything between a vertex array and a pixel, printed one space at a time.

Three objects -- a set of points, a pair of lines and a triangle -- sit on the ground grid. Pick one
in the "Pipeline spaces" panel and it shows that object's own vertices as they are handed from one
space to the next, using the very same matrices the shader is given below:

    object --(model)--> world --(view)--> eye --(projMat)--> clip --(/w)--> NDC --(viewport)--> window

Fly the camera around and the world-space column stays put while everything downstream of the view
matrix moves -- which is the whole point: `model` is a property of the object, `view` and `projMat`
are properties of the camera looking at it.

Elements.pyGLV (Computer Graphics for Deep Learning and Scientific Visualization)
"""

import numpy as np

import OpenGL.GL as gl
from OpenGL.GL import GL_LINES, GL_POINTS, GL_TRIANGLES

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from Elements.utils.terrain import generateTerrain
from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import SHADER_DIR

import imgui

example_description = \
"Three objects on a ground grid: points, lines and a triangle.\n\n\
Pick one in the 'Pipeline spaces' panel and it prints that object's vertices in\n\
every space they pass through on the way to the screen -- one column per vertex:\n\n\
  object  the numbers in the vertex array, as typed in this file\n\
  world   x model     where this object sits in the scene\n\
  eye     x view      the same scene, seen from the camera\n\
  clip    x projMat   the viewing frustum squared off into a cube\n\
  NDC     / w         the perspective divide; inside the screen means -1..1\n\
  window  x viewport  pixels, y counted up from the bottom left\n\n\
Only `model` belongs to the object: hold the RIGHT mouse button and fly, and the\n\
world row stays put while every row below it changes.\n\n\
projMat here keeps 1 to 20 units in front of the camera and throws the rest away,\n\
so flying far enough back clips the whole scene out of existence.\n\n\
Hit ESC OR Close the window to quit."

winWidth = 1280
winHeight = 800

# ---------------- geometry, in each object's own object space ----------------

#: plain [x, y, z] triples; addObject() appends the w=1 that makes them homogeneous points
POINT_COORDS = [[1.0, 0.0, 0.0], [1.5, 1.5, 0.0], [1.5, 0.0, 0.0]]
#: GL_LINES takes vertices two at a time, so these four are two separate segments, not a strip
LINE_COORDS = [[2.0, 0.0, 0.0], [0.5, 2.5, 1.0], [1.5, 0.0, 1.0], [1.5, 1.0, 1.5]]
TRIANGLE_COORDS = [[-2.0, 0.0, 0.0], [0.5, 2.5, -2.0], [1.5, 0.0, -2.0]]

# ---------------- the scene: RooT -> terrain, points, lines, triangle ----------------

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))


def addObject(name, coords, color, primitive, trs):
    """One Entity carrying a transform, a mesh, a vertex array and the plain colour shader.

    Returns the homogeneous vertices next to the transform and the shader, because the panel below
    needs the very same numbers that were handed to the GPU.
    """
    vertices = np.array([xyz + [1.0] for xyz in coords], dtype=np.float32)
    colors = np.array([color] * len(vertices), dtype=np.float32)
    # no shared corners here: every vertex is drawn once, in the order it was written
    indices = np.arange(len(vertices), dtype=np.uint32)

    entity = scene.world.createEntity(Entity(name=name))
    scene.world.addEntityChild(rootEntity, entity)
    trans = scene.world.addComponent(entity, BasicTransform(name=name + "_trans", trs=trs))
    mesh = scene.world.addComponent(entity, RenderMesh(name=name + "_mesh"))
    mesh.vertex_attributes.append(vertices)     # attribute 0, read by the shader as vPosition
    mesh.vertex_attributes.append(colors)       # attribute 1, read as vColor
    mesh.vertex_index.append(indices)
    scene.world.addComponent(entity, VertexArray(primitive=primitive))
    shader = scene.world.addComponent(entity, ShaderGLDecorator(
        Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))
    return vertices, trans, shader


## THE GROUND GRID ##
# 2*size across with 1-unit cells, so it doubles as a ruler for the world-space numbers
vertexTerrain, indexTerrain, colorTerrain = generateTerrain(size=4)
terrain = scene.world.createEntity(Entity(name="terrain"))
scene.world.addEntityChild(rootEntity, terrain)
terrain_trans = scene.world.addComponent(terrain, BasicTransform(name="terrain_trans", trs=util.identity()))
terrain_mesh = scene.world.addComponent(terrain, RenderMesh(name="terrain_mesh"))
terrain_mesh.vertex_attributes.append(vertexTerrain)
terrain_mesh.vertex_attributes.append(colorTerrain)
terrain_mesh.vertex_index.append(indexTerrain)
scene.world.addComponent(terrain, VertexArray(primitive=GL_LINES))
terrain_shader = scene.world.addComponent(terrain, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "ColorMVP.vert", fragment_import_file=SHADER_DIR / "Color.frag")))

## THE THREE OBJECTS ##
# A different model matrix each, and none of them the identity: with identity transforms the
# object -> world step would print the same numbers twice and teach nothing.
pointsVertices, points_trans, points_shader = addObject(
    "points", POINT_COORDS, [0.5, 0.5, 1.0, 1.0], GL_POINTS,
    util.translate(-2.0, 1.0, 0.0))                                     # moved left, lifted a unit
lineVertices, lines_trans, lines_shader = addObject(
    "lines", LINE_COORDS, [0.5, 1.0, 1.0, 1.0], GL_LINES,
    util.rotate(axis=(0.0, 1.0, 0.0), angle=90.0))                      # a quarter turn about y
triangleVertices, triangle_trans, triangle_shader = addObject(
    "triangle", TRIANGLE_COORDS, [1.0, 0.5, 1.0, 1.0], GL_TRIANGLES,
    util.translate(1.0, 0.0, 1.0) @ util.scale(0.5, 0.5, 0.5))          # halved, then moved

#: what the panel offers, and what the loop draws. The transform is kept rather than its .trs so
#: that editing the TRS elsewhere would be picked up here too.
objects = [
    ("Points", pointsVertices, points_trans, points_shader),
    ("Lines", lineVertices, lines_trans, lines_shader),
    ("Triangle", triangleVertices, triangle_trans, triangle_shader),
]

# ---------------- the panel ----------------

#: index into `objects`, or -1 for "None". Module level: ImGui panels are redrawn from scratch every
#: frame, so anything the user picked has to be remembered outside the function that draws it.
selected_object = 0


def matrixText(matrix):
    """A 4xN matrix as text, one column per vertex.

    Fixed to two decimals: the numbers are here to be compared from one space to the next, and
    float32's full 8 digits of noise make that harder, not more accurate.
    """
    return np.array2string(np.asarray(matrix, dtype=np.float64), precision=2,
                           suppress_small=True, floatmode="fixed", max_line_width=200)


def pipelineGUI(objects, view, projMat, windowWidth, windowHeight):
    """Walk the selected object's vertices through the pipeline, printing each space on the way."""
    global selected_object

    # off to the right, clear of the three objects and of the description panel on the left
    imgui.set_next_window_position(720, 40, imgui.FIRST_USE_EVER)
    imgui.set_next_window_size(545, 730, imgui.FIRST_USE_EVER)
    imgui.begin("Pipeline spaces")

    # positional args, not keyword: pyimgui calls the second one `selected` and imgui_bundle calls
    # it `p_selected`, so only positional works on both backends
    if imgui.selectable("None", selected_object == -1)[0]:
        selected_object = -1
    for index, (name, _, _, _) in enumerate(objects):
        if imgui.selectable(name, selected_object == index)[0]:
            selected_object = index
    imgui.separator()

    if selected_object < 0:
        imgui.text("Nothing selected.")
        imgui.end()
        return

    name, vertices, trans, _ = objects[selected_object]
    # one column per vertex, so the matrices multiply from the left the way they are written
    inObject = vertices.transpose()
    model = trans.trs

    imgui.text(name + ": " + str(inObject.shape[1]) + " vertices, rows are x / y / z / w")
    imgui.separator()

    imgui.text("Object space\n" + matrixText(inObject))

    inWorld = model @ inObject
    imgui.text("\nx model  ->  World space\n" + matrixText(inWorld))

    inEye = view @ inWorld
    imgui.text("\nx view  ->  Eye space\n" + matrixText(inEye))

    # projMat is the last thing the vertex shader does; everything below happens in fixed-function
    # hardware, which is why the shader only ever receives projMat @ view @ model
    inClip = projMat @ inEye
    imgui.text("\nx projMat  ->  Clip space\n" + matrixText(inClip))

    # the perspective divide: w carries the distance from the camera, so dividing by it is what
    # makes far things small. Everything inside the frustum lands in -1..1 on all three axes.
    inNDC = inClip[:-1, :] / inClip[3, None]
    imgui.text("\n/ w  ->  Normalized Device Coordinates\n" + matrixText(inNDC))

    # the viewport transform: -1..1 stretched over the drawable, y counted up from the bottom left
    # (which is the opposite of the way the mouse position is reported)
    inWindow = np.empty_like(inNDC)
    inWindow[0, :] = (inNDC[0, :] + 1.0) * windowWidth / 2.0
    inWindow[1, :] = (inNDC[1, :] + 1.0) * windowHeight / 2.0
    # depth: 0 at the near plane, 1 at the far one -- but not linearly. The divide by w already
    # happened, so most of the 0..1 range is spent just in front of the camera, which is why these
    # numbers all sit up near the far end and barely move.
    inWindow[2, :] = (inNDC[2, :] + 1.0) / 2.0
    imgui.text("\nx viewport  ->  Window space, " + str(windowWidth) + " x " + str(windowHeight)
               + " px\nrows are x / y / depth\n" + matrixText(inWindow))

    imgui.end()


# ---------------- systems ----------------

initUpdate = scene.world.createSystem(InitGLShaderSystem())
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())

scene.world.print()

# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth=winWidth, windowHeight=winHeight,
           windowTitle="From object space to window space", openGLversion=4)

# pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
# needs an active GL context
scene.world.traverse_visit(initUpdate, scene.world.root)

gl.glPointSize(10)                  # GL_POINTS are a single pixel otherwise, and a point you cannot
                                    # see is a poor advertisement for a pipeline that placed it
gl.glDisable(gl.GL_CULL_FACE)       # the triangle should stay visible from behind as well
gl.glEnable(gl.GL_DEPTH_TEST)
gl.glDepthFunc(gl.GL_LESS)

# ---------------- the window, the GUI and the camera ----------------

gWindow = scene.renderWindow    # the SDL2 window: the pixels, the mouse and the keyboard
gGUI = scene.gContext           # the ImGUI layer wrapped around it, which also owns the camera

eye = util.vec(4.5, 3.5, 7.0)
target = util.vec(2.0, 1.0, 0.0)    # aimed right of the objects, so they sit clear of the panel
up = util.vec(0.0, 1.0, 0.0)
# createViewMatrix, rather than setting gWindow._myCamera: it also stores eye/target/up, which is
# what the mouse/keyboard camera reads and updates
gGUI.createViewMatrix(eye, target, up)

# a near plane at 1 and a far plane at 20: everything nearer or further than that is clipped away,
# which is easy to see by flying backwards until the grid disappears
projMat = util.perspective(50.0, winWidth / winHeight, 1.0, 20.0)

while running:
    running = scene.render()

    # read after scene.render(), which is where the mouse gets to move the camera: the panel and
    # the shaders then agree on the numbers within a single frame
    view = gWindow._myCamera

    for _, _, trans, shader in objects:
        shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ trans.trs, mat4=True)
    terrain_shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ terrain_trans.trs, mat4=True)

    displayGUI_text(example_description)
    pipelineGUI(objects, view, projMat, gWindow._windowWidth, gWindow._windowHeight)

    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()
