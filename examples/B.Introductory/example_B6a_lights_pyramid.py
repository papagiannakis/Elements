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
"Two square-based pyramids, sharp and smooth. Every vertex, index and normal in\n\
this file is written out by hand -- Elements.utils.normals is not used at all.\n\n\
Same 5 faces and the same silhouette, from opposite extremes of sharing:\n\n\
  left  SHARP   18 vertices, nothing shared. One vertex per triangle corner,\n\
                so the index list is just 0,1,2,...,17 and each face carries\n\
                its own normal.\n\
  right SMOOTH   5 vertices, each appearing exactly once. Every face reads its\n\
                corners from the same 5, so a vertex normal has to be the\n\
                average of every face that meets there.\n\n\
Read the geometry section: 5 face normals from cross products, then averages per\n\
vertex, and the orientation of every triangle to keep straight. For a shape with\n\
5 faces. This is what generateFlatNormalsMesh / generateSmoothNormalsMesh do for\n\
you in B6.\n\n\
Right mouse button to fly, F for wireframe. Hit ESC OR Close the window to quit."

# ---------------- light and material ----------------

Lposition = util.vec(2.0, 5.5, 2.0)
Lambientcolor = util.vec(1.0, 1.0, 1.0)
Lambientstr = 0.3
Lcolor = util.vec(1.0, 1.0, 1.0)
Lintensity = 0.8
Mshininess = 0.4
MspecularExponent = 32.0
Mcolor = util.vec(0.0, 0.6, 0.9)

winWidth = 1200
winHeight = 800

# ---------------- the pyramid, by hand ----------------
#
# Square base of side 1 on y=-0.5, apex 1.0 above its centre:
#
#         A (0, 0.5, 0)                 B0 (-0.5,-0.5, 0.5)   front-left
#        /|\                            B1 ( 0.5,-0.5, 0.5)   front-right
#       / | \                           B2 ( 0.5,-0.5,-0.5)   back-right
#      /  |  \                          B3 (-0.5,-0.5,-0.5)   back-left
#     B3--+---B2
#    /        /                         5 faces: 4 triangular sides + a square base
#   B0------B1                          6 triangles, since the base takes two
#
# A face normal is perpendicular to the face and points outwards. Each side rises 1.0 while stepping
# 0.5 outwards, so in (outwards, up) terms its normal is (1.0, 0.5) -> (2, 1)/sqrt(5). Equivalently
# normalise(cross(second - first, third - first)) for the windings below -- and winding is the thing
# to watch: swap two corners of a triangle and its normal flips to face inwards.

S5 = np.sqrt(5.0)

APEX = [0.0, 0.5, 0.0, 1.0]
B0 = [-0.5, -0.5, 0.5, 1.0]
B1 = [0.5, -0.5, 0.5, 1.0]
B2 = [0.5, -0.5, -0.5, 1.0]
B3 = [-0.5, -0.5, -0.5, 1.0]

N_FRONT = [0.0, 1 / S5, 2 / S5]      # the +z side
N_RIGHT = [2 / S5, 1 / S5, 0.0]      # the +x side
N_BACK = [0.0, 1 / S5, -2 / S5]      # the -z side
N_LEFT = [-2 / S5, 1 / S5, 0.0]      # the -x side
N_DOWN = [0.0, -1.0, 0.0]            # the base

# ---- SHARP: one normal per face, so nothing can be shared ----
# Every triangle brings its own three corners, the base included: 6 triangles x 3 = 18 vertices,
# with the winding baked into the order they are listed in.
vertexSharp = np.array([
    B0, B1, APEX,        # front side   (B0, B1, apex)
    B1, B2, APEX,        # right side   (B1, B2, apex)
    B2, B3, APEX,        # back side    (B2, B3, apex)
    B3, B0, APEX,        # left side    (B3, B0, apex)
    B0, B2, B1,          # base, half 1 (B0, B2, B1 -- not B0, B1, B2, which would face up)
    B0, B3, B2,          # base, half 2 (B0, B3, B2 -- reversed for the same reason)
], dtype=np.float32)

normalsSharp = np.array([
    N_FRONT, N_FRONT, N_FRONT,           # all 3 corners of a face carry that face's normal
    N_RIGHT, N_RIGHT, N_RIGHT,
    N_BACK, N_BACK, N_BACK,
    N_LEFT, N_LEFT, N_LEFT,
    N_DOWN, N_DOWN, N_DOWN,              # base, half 1
    N_DOWN, N_DOWN, N_DOWN,              # base, half 2
], dtype=np.float32)

# nothing is shared, so the indices are simply the order the vertices are in
indexSharp = np.arange(len(vertexSharp), dtype=np.uint32)

# ---- SMOOTH: 5 vertices, each appearing exactly once ----
# The apex is shared by the 4 sides. Their outward parts cancel in pairs, so the average is exactly
# straight up -- the one tidy result here.
#
# Every base corner is now shared by two sides *and* the base, so all three go into its average.
# For B1, that is front + right + base:
#     (0,1,2)/S5 + (2,1,0)/S5 + (0,-1,0)  =  (2/S5,  2/S5 - 1,  2/S5)
# and the length of that is nothing tidy:
CORNER_LEN = np.sqrt(2 * (2 / S5) ** 2 + (2 / S5 - 1) ** 2)   # 1.26931...
CORNER_X = (2 / S5) / CORNER_LEN                              # 0.70466
CORNER_Y = (2 / S5 - 1) / CORNER_LEN                          # -0.08317, i.e. below horizontal
# That negative y is the price of sharing the rim: the base pulls the corner normals under the
# horizon, and the bottom edge shades slightly dark. Keeping the rim crisp means duplicating those
# 4 vertices, which is what the sharp pyramid does with all 18 of its.

vertexSmooth = np.array([
    APEX,               # 0
    B0,                 # 1
    B1,                 # 2
    B2,                 # 3
    B3,                 # 4
], dtype=np.float32)

normalsSmooth = np.array([
    [0.0, 1.0, 0.0],                            # apex: front + right + back + left
    [-CORNER_X, CORNER_Y, CORNER_X],            # B0:   left  + front + base
    [CORNER_X, CORNER_Y, CORNER_X],             # B1:   front + right + base
    [CORNER_X, CORNER_Y, -CORNER_X],            # B2:   right + back  + base
    [-CORNER_X, CORNER_Y, -CORNER_X],           # B3:   back  + left  + base
], dtype=np.float32)

indexSmooth = np.array((
    1, 2, 0,        # front side   (B0, B1, apex)
    2, 3, 0,        # right side   (B1, B2, apex)
    3, 4, 0,        # back side    (B2, B3, apex)
    4, 1, 0,        # left side    (B3, B0, apex)
    1, 3, 2,        # base, half 1 (B0, B2, B1 -- watch the orientation: B0, B1, B2 would face up)
    1, 4, 3,        # base, half 2 (B0, B3, B2 -- reversed for the same reason)
), np.uint32)

# one colour throughout: per-vertex colours would drown out the shading
colorSharp = np.array([[*Mcolor, 1.0]] * len(vertexSharp), dtype=np.float32)
colorSmooth = np.array([[*Mcolor, 1.0]] * len(vertexSmooth), dtype=np.float32)

# ---------------- the scene: RooT -> sharp pyramid, smooth pyramid ----------------

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))

## THE SHARP PYRAMID, on the left ##
sharp = scene.world.createEntity(Entity(name="pyramid_sharp"))
scene.world.addEntityChild(rootEntity, sharp)
sharp_trans = scene.world.addComponent(sharp, BasicTransform(name="pyramid_sharp_trans", trs=util.translate(-0.7,0.3,0) @ util.scale(0.6)))
sharp_mesh = scene.world.addComponent(sharp, RenderMesh(name="pyramid_sharp_mesh"))
sharp_mesh.vertex_attributes.append(vertexSharp)
sharp_mesh.vertex_attributes.append(colorSharp)
sharp_mesh.vertex_attributes.append(normalsSharp)
sharp_mesh.vertex_index.append(indexSharp)
sharp_vArray = scene.world.addComponent(sharp, VertexArray())
sharp_shader = scene.world.addComponent(sharp, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "Phong.vert", fragment_import_file=SHADER_DIR / "Phong.frag")))

## THE SMOOTH PYRAMID, on the right ##
smooth = scene.world.createEntity(Entity(name="pyramid_smooth"))
scene.world.addEntityChild(rootEntity, smooth)
smooth_trans = scene.world.addComponent(smooth, BasicTransform(name="pyramid_smooth_trans", trs=util.translate(0.7,0.3,0) @ util.scale(0.6)))
smooth_mesh = scene.world.addComponent(smooth, RenderMesh(name="pyramid_smooth_mesh"))
smooth_mesh.vertex_attributes.append(vertexSmooth)
smooth_mesh.vertex_attributes.append(colorSmooth)
smooth_mesh.vertex_attributes.append(normalsSmooth)
smooth_mesh.vertex_index.append(indexSmooth)
smooth_vArray = scene.world.addComponent(smooth, VertexArray())
smooth_shader = scene.world.addComponent(smooth, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "Phong.vert", fragment_import_file=SHADER_DIR / "Phong.frag")))

# ---------------- systems ----------------

initUpdate = scene.world.createSystem(InitGLShaderSystem())
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())

# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight,
           windowTitle = "Elements: normals by hand", openGLversion = 4,
           customImGUIdecorator = ImGUIecssDecorator2)

# pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
# needs an active GL context
scene.world.traverse_visit(initUpdate, scene.world.root)

# ---------------- the window, the GUI and the camera ----------------

gWindow = scene.renderWindow
gGUI = scene.gContext

eye = util.vec(2.5, 2.0, 2.5)
target = util.vec(0.0, 0.3, 0.0)
up = util.vec(0.0, 1.0, 0.0)
# also stores eye/target/up, which the mouse camera reads and the shader needs below as viewPos
gGUI.createViewMatrix(eye, target, up)

projMat = util.perspective(50.0, winWidth/winHeight, 0.01, 100.0)

# both pyramids share one light and one shader; only their normals and placement differ
lit_objects = [(sharp_shader, sharp_trans), (smooth_shader, smooth_trans)]

while running:
    running = scene.render()
    displayGUI_text(example_description)

    view = gWindow._myCamera
    viewPos = gWindow._cameraEye

    for shader, trans in lit_objects:
        shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ trans.trs, mat4=True)
        shader.setUniformVariable(key='model',value=trans.trs,mat4=True)
        shader.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
        shader.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
        shader.setUniformVariable(key='viewPos',value=viewPos,float3=True)
        shader.setUniformVariable(key='lightPos',value=Lposition,float3=True)
        shader.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
        shader.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
        shader.setUniformVariable(key='shininess',value=Mshininess,float1=True)
        shader.setUniformVariable(key='specularExponent',value=MspecularExponent,float1=True)

    # render after the uniforms are set, so this frame draws with this frame's camera
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()
