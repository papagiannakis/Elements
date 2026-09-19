import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2

from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from Elements.extensions.Shapes import geometry_factory

from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import SHADER_DIR

example_description = \
"The same sphere twice, sharp and smooth, with no geometry written out at all:\n\
geometry_factory builds the vertices, the indices and both sets of normals.\n\n\
  left  SHARP   every triangle gets its own 3 vertices and one face normal, so\n\
                the tessellation shows -- you can count the facets\n\
  right SMOOTH  the vertices stay shared and each normal is the average of the\n\
                faces meeting there, which nearly points straight out of the\n\
                centre, so the facets disappear and the ball looks round\n\n\
This is the opposite lesson to the cube in B6b. A cube's faces really are flat,\n\
so smoothing it is wrong; a sphere's facets only exist because a curved surface\n\
had to be chopped into triangles, so smoothing is what hides the approximation.\n\
Raise LAT and LON to make the sharp one converge on the smooth one.\n\n\
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

# ---------------- the geometry, from geometry_factory ----------------
#
# Deliberately coarse, so the sharp sphere's facets are countable. lat x lon is how many rings and
# segments the ball is cut into -- the whole point of a sphere primitive is that this is a parameter
# rather than a vertex list.
LAT = 16
LON = 24

# One set of vertices and triangles, shared by both spheres.
vertices, indices, colors = geometry_factory.create_geometry(
    "sphere", {"lat": LAT, "lon": LON, "color": Mcolor})

# ...and two ways of putting normals on it, which is the only difference between the two objects.
# Flat has to split every triangle off on its own (362 -> 2160 vertices here, 6x the memory) because
# its 3 corners carry that one face's normal and cannot be reused by the neighbouring face.
vertexSharp, indexSharp, colorSharp, normalsSharp = geometry_factory.build_flat_shaded_mesh(
    vertices, indices, colors)

# Smooth keeps the 362 shared vertices and averages the faces at each one. On a sphere that average
# lands within about a degree of the true radial direction -- close enough that the surface reads as
# genuinely curved, from geometry that is still flat triangles.
vertexSmooth, indexSmooth, colorSmooth, normalsSmooth = geometry_factory.build_smooth_shaded_mesh(
    vertices, indices, colors)

# ---------------- the scene: RooT -> sharp sphere, smooth sphere ----------------

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))

## THE SHARP SPHERE, on the left ##
sharp = scene.world.createEntity(Entity(name="sphere_sharp"))
scene.world.addEntityChild(rootEntity, sharp)
sharp_trans = scene.world.addComponent(sharp, BasicTransform(name="sphere_sharp_trans", trs=util.translate(-0.7,0.3,0) @ util.scale(0.6)))
sharp_mesh = scene.world.addComponent(sharp, RenderMesh(name="sphere_sharp_mesh"))
sharp_mesh.vertex_attributes.append(vertexSharp)
sharp_mesh.vertex_attributes.append(colorSharp)
sharp_mesh.vertex_attributes.append(normalsSharp)
sharp_mesh.vertex_index.append(indexSharp)
sharp_vArray = scene.world.addComponent(sharp, VertexArray())
sharp_shader = scene.world.addComponent(sharp, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "Phong.vert", fragment_import_file=SHADER_DIR / "Phong.frag")))

## THE SMOOTH SPHERE, on the right ##
smooth = scene.world.createEntity(Entity(name="sphere_smooth"))
scene.world.addEntityChild(rootEntity, smooth)
smooth_trans = scene.world.addComponent(smooth, BasicTransform(name="sphere_smooth_trans", trs=util.translate(0.7,0.3,0) @ util.scale(0.6)))
smooth_mesh = scene.world.addComponent(smooth, RenderMesh(name="sphere_smooth_mesh"))
smooth_mesh.vertex_attributes.append(vertexSmooth)
smooth_mesh.vertex_attributes.append(colorSmooth)
smooth_mesh.vertex_attributes.append(normalsSmooth)
smooth_mesh.vertex_index.append(indexSmooth)
smooth_vArray = scene.world.addComponent(smooth, VertexArray())
smooth_shader = scene.world.addComponent(smooth, ShaderGLDecorator(
    Shader(vertex_import_file=SHADER_DIR / "Phong.vert", fragment_import_file=SHADER_DIR / "Phong.frag")))

print("sphere: %d vertices / %d triangles from the factory" % (len(vertices), len(indices) // 3))
print("  sharp  needs %d vertices (one per triangle corner)" % len(vertexSharp))
print("  smooth needs %d (the originals, shared)" % len(vertexSmooth))

# ---------------- systems ----------------

initUpdate = scene.world.createSystem(InitGLShaderSystem())
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())

# MAIN RENDERING LOOP

running = True
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight,
           windowTitle = "Elements: sharp and smooth sphere", openGLversion = 4,
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

# both spheres share one light and one shader; only their normals and placement differ
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
