import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray
from Elements.definitions import MODEL_DIR, SHADER_DIR

from OpenGL.GL import GL_LINES

import Elements.utils.normals as norm
from Elements.utils.terrain import generateTerrain
from Elements.utils.obj_to_mesh import obj_to_mesh

from Elements.utils.Shortcuts import displayGUI_text

example_description = \
"The Newell teapot, loaded from a .obj file instead of typed in by hand.\n\n\
Two lines do the work:\n\
  obj_to_mesh              positions and triangles out of the file\n\
  generateSmoothNormalsMesh a normal per vertex, which the Phong shader needs\n\n\
A .obj carries no colours, so obj_to_mesh paints every vertex the same, and no\n\
normals either that Elements uses -- they are computed from the geometry.\n\n\
Swap MODEL below for any other file in Elements/assets/models. Unlike the\n\
positions of a cube, none of this scales with how complex the model is.\n\n\
Hold the RIGHT mouse button to fly: drag to look, W/A/S/D to move, Q/E to\n\
rise/sink, SPACE to aim at the origin, scroll or +/- for speed.\n\
Hit ESC OR Close the window to quit."

# ---------------- what to load ----------------

#: any .obj under Elements/assets/models -- cow.obj, teddy.obj, bunny.obj, sphere.obj,
#: LivingRoom/Chair/Chair.obj ... obj_to_mesh reads v, v/vt, v//vn and v/vt/vn face formats and
#: triangulates quads, so files with uv coordinates load too (their uvs are simply not used here)
MODEL = MODEL_DIR / "teapot.obj"
# MODEL = MODEL_DIR / "cow.obj"
# MODEL = MODEL_DIR / "teddy.obj" # too big model, use MODEL_SCALE = 0.05
# MODEL = MODEL_DIR / "sphere.obj"
# MODEL = MODEL_DIR / "bunny.obj"
# MODEL = MODEL_DIR / "Hand" /"Hand.obj" # too small model, use MODEL_SCALE = 3.4
MODEL_COLOR = [168/255, 168/255, 210/255, 1.0]
MODEL_SCALE = 0.4

# ---------------- light and material ----------------

Lposition = util.vec(2.0, 5.5, 2.0)
Lambientcolor = util.vec(1.0, 1.0, 1.0)
Lambientstr = 0.3
Lcolor = util.vec(1.0, 1.0, 1.0)
Lintensity = 0.8
Mshininess = 0.4
MspecularExponent = 32.0

winWidth = 1200
winHeight = 800

# ---------------- geometry ----------------

# positions + triangles from the file, then a normal per vertex from the geometry
vert, ind, col = obj_to_mesh(MODEL, color=MODEL_COLOR)
vertices, indices, colors, normals = norm.generateSmoothNormalsMesh(vert, ind, col)
print("%s: %d vertices, %d triangles" % (MODEL.name, len(vertices), len(indices) // 3))

vertexTerrain, indexTerrain, colorTerrain = generateTerrain(size=4)

# ---------------- the scene: RooT -> teapot, terrain ----------------

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))

## THE LOADED OBJECT, lit ##
teapot = scene.world.createEntity(Entity(name="teapot"))
scene.world.addEntityChild(rootEntity, teapot)
teapot_trans = scene.world.addComponent(teapot, BasicTransform(name="teapot_trans", trs=util.scale(MODEL_SCALE)))
teapot_mesh = scene.world.addComponent(teapot, RenderMesh(name="teapot_mesh"))
teapot_mesh.vertex_attributes.append(vertices)
teapot_mesh.vertex_attributes.append(colors)
teapot_mesh.vertex_attributes.append(normals)     # attribute 2, the one the lighting needs
teapot_mesh.vertex_index.append(indices)
teapot_vArray = scene.world.addComponent(teapot, VertexArray())
teapot_shader = scene.world.addComponent(teapot, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "Phong.vert", fragment_import_file=SHADER_DIR / "Phong.frag")))

## THE TERRAIN, unlit ##
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

# ---------------- systems ----------------

# TransformSystem is what turns each BasicTransform's own trs into the l2world used below. The other
# examples multiply trs in directly, which works only while nothing is parented to anything else.
transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
initUpdate = scene.world.createSystem(InitGLShaderSystem())
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())

# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight,
           windowTitle = "Elements: Tea anyone?", openGLversion = 4,
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
# also stores eye/target/up, which the mouse camera reads and the shader needs below as viewPos
gGUI.createViewMatrix(eye, target, up)

projMat = util.perspective(50.0, winWidth/winHeight, 0.01, 100.0)

while running:
    running = scene.render()
    displayGUI_text(example_description)
    scene.world.traverse_visit(transUpdate, scene.world.root)

    view = gWindow._myCamera        # the mouse and the GUI both write here
    viewPos = gWindow._cameraEye    # world-space camera position, follows the view matrix above

    terrain_shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ terrain_trans.l2world, mat4=True)

    teapot_shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ teapot_trans.l2world, mat4=True)
    # must be the very same model matrix modelViewProj is built from, otherwise the shader lights a
    # world-space position/normal that does not match the geometry being drawn
    teapot_shader.setUniformVariable(key='model',value=teapot_trans.l2world,mat4=True)
    teapot_shader.setUniformVariable(key='ambientColor',value=Lambientcolor,float3=True)
    teapot_shader.setUniformVariable(key='ambientStr',value=Lambientstr,float1=True)
    teapot_shader.setUniformVariable(key='viewPos',value=viewPos,float3=True)
    teapot_shader.setUniformVariable(key='lightPos',value=Lposition,float3=True)
    teapot_shader.setUniformVariable(key='lightColor',value=Lcolor,float3=True)
    teapot_shader.setUniformVariable(key='lightIntensity',value=Lintensity,float1=True)
    teapot_shader.setUniformVariable(key='shininess',value=Mshininess,float1=True)
    teapot_shader.setUniformVariable(key='specularExponent',value=MspecularExponent,float1=True)

    # render after the uniforms are set, so this frame draws with this frame's camera
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()
