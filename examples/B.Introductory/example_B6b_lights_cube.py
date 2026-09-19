import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

import Elements.utils.normals as norm

from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import SHADER_DIR

example_description = \
"The same cube twice, lit by one point light with the Blinn-Phong shader.\n\
Only the normals differ:\n\n\
  left  FLAT    one normal per face -- flat faces, sharp edges\n\
  right SMOOTH  one normal per corner, averaged over the 3 faces meeting\n\
                there -- the lighting sweeps across the faces, and the cube\n\
                reads as rounded even though the geometry is identical\n\n\
Both are one colour, so the shading is all you see. Lighting also needs the\n\
model matrix on its own (positions and normals in world space) and the camera\n\
position (the specular highlight depends on where you look from).\n\n\
Edit the Light and Material values at the top of the file, or move the camera:\n\
right mouse button to fly, F for wireframe. Hit ESC OR Close the window to quit."

# ---------------- light and material ----------------

#Light
Lposition = util.vec(2.0, 5.5, 2.0) #uniform lightpos
Lambientcolor = util.vec(1.0, 1.0, 1.0) #uniform ambient color
Lambientstr = 0.3 #uniform ambientStr
# the uniform viewPos is NOT a constant: the specular term depends on where the viewer is,
# so it is read back from the camera every frame in the render loop (see gWindow._cameraEye)
Lcolor = util.vec(1.0,1.0,1.0)
Lintensity = 0.8
#Material
Mshininess = 0.4
#: How tight the specular highlight is (Mshininess above is how strong it is).
#: 8 = broad sheen, 32 = plastic, 256+ = mirror glint. See example_B10_specular_grid.py.
MspecularExponent = 32.0
Mcolor = util.vec(0.8, 0.0, 0.8)

winWidth = 1200
winHeight = 800

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
# one colour for the whole cube: per-vertex colours would drown out the shading
colorCube = np.array([[*Mcolor, 1.0]] * 8, dtype=np.float32)
# which corners each triangle joins: 6 faces, 2 triangles per face
indexCube = np.array((1,0,3, 1,3,2,
                  2,3,7, 2,7,6,
                  3,0,4, 3,4,7,
                  6,5,1, 6,1,2,
                  4,5,6, 4,6,7,
                  5,4,0, 5,0,1), np.uint32)

# The same 8 corners and 36 indices, turned into two meshes that differ only in their normals.
# Flat has to split every corner into one copy per face it belongs to (8 -> 36 vertices), because a
# vertex carries a single normal and the three faces at a corner need three different ones. Smooth
# keeps the 8 shared corners and lets each normal be the sum of the faces meeting there.
vertexFlat, indexFlat, colorFlat, normalsFlat = norm.generateFlatNormalsMesh(
    vertexCube.copy(), indexCube.copy(), colorCube.copy())
vertexSmooth, indexSmooth, colorSmooth, normalsSmooth = norm.generateSmoothNormalsMesh(
    vertexCube.copy(), indexCube.copy(), colorCube.copy())

# ---------------- the scene: RooT -> flat cube, smooth cube ----------------

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))

## THE FLAT-SHADED CUBE, on the left ##
cubeFlat = scene.world.createEntity(Entity(name="cube_flat"))
scene.world.addEntityChild(rootEntity, cubeFlat)
cubeFlat_trans = scene.world.addComponent(cubeFlat, BasicTransform(name="cube_flat_trans", trs=util.translate(-0.6,0.3,0) @ util.scale(0.6)))
cubeFlat_mesh = scene.world.addComponent(cubeFlat, RenderMesh(name="cube_flat_mesh"))
cubeFlat_mesh.vertex_attributes.append(vertexFlat)
cubeFlat_mesh.vertex_attributes.append(colorFlat)
cubeFlat_mesh.vertex_attributes.append(normalsFlat)     # attribute 2, the one the lighting needs
cubeFlat_mesh.vertex_index.append(indexFlat)
cubeFlat_vArray = scene.world.addComponent(cubeFlat, VertexArray())
cubeFlat_shader = scene.world.addComponent(cubeFlat, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "Phong.vert", fragment_import_file=SHADER_DIR / "Phong.frag")))

## THE SMOOTH-SHADED CUBE, on the right -- same geometry, same light, same shader ##
cubeSmooth = scene.world.createEntity(Entity(name="cube_smooth"))
scene.world.addEntityChild(rootEntity, cubeSmooth)
cubeSmooth_trans = scene.world.addComponent(cubeSmooth, BasicTransform(name="cube_smooth_trans", trs=util.translate(0.6,0.3,0) @ util.scale(0.6)))
cubeSmooth_mesh = scene.world.addComponent(cubeSmooth, RenderMesh(name="cube_smooth_mesh"))
cubeSmooth_mesh.vertex_attributes.append(vertexSmooth)
cubeSmooth_mesh.vertex_attributes.append(colorSmooth)
cubeSmooth_mesh.vertex_attributes.append(normalsSmooth)
cubeSmooth_mesh.vertex_index.append(indexSmooth)
cubeSmooth_vArray = scene.world.addComponent(cubeSmooth, VertexArray())
cubeSmooth_shader = scene.world.addComponent(cubeSmooth, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "Phong.vert", fragment_import_file=SHADER_DIR / "Phong.frag")))

# ---------------- systems ----------------

initUpdate = scene.world.createSystem(InitGLShaderSystem())
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())

# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight,
           windowTitle = "Elements: Let There Be Light", openGLversion = 4,
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

# both cubes share one light and one shader; only their normals and placement differ
lit_objects = [(cubeFlat_shader, cubeFlat_trans), (cubeSmooth_shader, cubeSmooth_trans)]

while running:
    running = scene.render()
    displayGUI_text(example_description)

    view = gWindow._myCamera    # the mouse and the GUI both write here
    viewPos = gWindow._cameraEye    # world-space camera position, follows the view matrix above

    for shader, trans in lit_objects:
        shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ trans.trs, mat4=True)
        # must be the very same model matrix modelViewProj is built from, otherwise the shader
        # lights a world-space position/normal that does not match the geometry being drawn
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
