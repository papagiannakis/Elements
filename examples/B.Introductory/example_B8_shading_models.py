"""
Phong vs Blinn-Phong vs Gouraud, side by side.

Six copies of the same model in a 2 x 3 grid:

                      Phong          Blinn-Phong        Gouraud
    back  row  |   smooth normals   smooth normals   smooth normals
    front row  |    flat normals     flat normals     flat normals

Each column isolates one shading model, each row isolates how the normals were built. Geometry,
light, material and camera are identical everywhere, which is what makes the comparison mean
anything: whatever difference you see is caused by the one variable that changed.
"""

from OpenGL.GL import GL_LINES

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIDecorator
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from Elements.extensions.Shapes import geometry_factory
from Elements.utils.obj_to_mesh import obj_to_mesh
from Elements.utils.terrain import generateTerrain
from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import MODEL_DIR, SHADER_DIR

example_description = \
"Six copies of one model: three shading models x two kinds of normals.\n\n\
Columns, left to right:  Phong | Blinn-Phong | Gouraud\n\
Front row: flat normals.  Back row: smooth normals.\n\n\
Phong and Blinn-Phong both light every FRAGMENT and differ in a single\n\
line of the fragment shader; Blinn-Phong's highlight is the wider of\n\
the two at the same exponent.\n\n\
Gouraud lights every VERTEX and lets the rasteriser interpolate the\n\
finished colour. On the coarse sphere its highlight nearly disappears:\n\
the highlight is smaller than a triangle, so it falls between the\n\
vertices where the lighting was sampled and is never computed at all.\n\
Orbit the camera and watch it flicker in and out.\n\n\
Hold the RIGHT mouse button to fly, F for wireframe.\n\
Hit ESC OR Close the window to quit."

# ---------------- what to show ----------------

#: Flat per-vertex colour: a plain .obj carries no colours.
MODEL_COLOR = (0.55, 0.54, 0.66)


def obj(path):
    """A loader for one Wavefront .obj file."""
    return lambda: obj_to_mesh(path, color=list(MODEL_COLOR) + [1.0])


def sphere(lat, lon):
    """A loader for a generated sphere -- lat x lon rings and segments set the triangle count."""
    return lambda: geometry_factory.create_sphere(
        {"lat": lat, "lon": lon, "scale": [2.0, 2.0, 2.0], "color": list(MODEL_COLOR)})


#: Which model fills all six slots. The default is a deliberately coarse 252-triangle sphere,
#: because a dense mesh cannot show what the Gouraud column is here to show: Gouraud only breaks
#: when the highlight is about the size of a triangle or smaller. Every bundled .obj is far too
#: fine for that (teapot.obj is 6320 triangles, roughly 3 pixels each at this scale, and its
#: Gouraud rendering comes out identical to its Phong one). Load the teapot to compare Phong
#: against Blinn-Phong, keep the coarse sphere to see Gouraud fail.
MODEL = sphere(10, 14)
# MODEL = obj(MODEL_DIR / "teapot.obj")
# MODEL = obj(MODEL_DIR / "cow.obj")
# MODEL = obj(MODEL_DIR / "teddy.obj")

#: Each copy is uniformly scaled so its largest dimension is this many world units.
TARGET_SIZE = 0.8

# ---------------- light and material, shared by all six ----------------

Lposition = util.vec(0.9, 2.6, 2.2)
Lambientcolor = util.vec(1.0, 1.0, 1.0)
Lambientstr = 0.25
Lcolor = util.vec(1.0, 1.0, 1.0)
Lintensity = 0.9
#: How STRONG the highlight is -- turned up from the 0.4 of the other examples, since highlights
#: are the whole point here.
Mshininess = 0.9
#: How TIGHT the highlight is. All three shaders get the same value, so the shading model stays
#: the only variable. Raise it and Gouraud loses the highlight even more dramatically.
MspecularExponent = 32.0

# viewPos is missing on purpose: the specular term depends on where the camera is, so it is read
# back from the camera every frame in the render loop below.

winWidth = 1200
winHeight = 800

# ---------------- the geometry, built once and shared ----------------

vertices, indices, colors = MODEL()

# One scale for every copy, from the model's own bounding box, so any .obj lands at a sensible
# size. [:, :3] drops the homogeneous w component.
extent = vertices[:, :3].max(axis=0) - vertices[:, :3].min(axis=0)
model_scale = TARGET_SIZE / float(extent.max())
# How far the model's lowest point sits below its own origin, scaled: lift each copy by this so it
# stands on the terrain instead of sinking through it.
base_lift = -float(vertices[:, 1].min()) * model_scale

#   flat   -> one normal per triangle, so the mesh has to be split into unshared vertices
#   smooth -> one normal per vertex, averaged over the triangles meeting there
v_flat, i_flat, c_flat, n_flat = geometry_factory.build_flat_shaded_mesh(vertices, indices, colors)
v_smooth, i_smooth, c_smooth, n_smooth = geometry_factory.build_smooth_shaded_mesh(vertices, indices, colors)

# ---------------- the scene: RooT -> six copies, terrain ----------------

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))

#: The columns. Blinn-Phong reuses Phong.vert verbatim: the two models are identical right up to
#: the fragment stage, where a single line differs.
LIGHTING_MODELS = [
    ("Phong",      SHADER_DIR / "Phong.vert",   SHADER_DIR / "Phong.frag"),
    ("BlinnPhong", SHADER_DIR / "Phong.vert",   SHADER_DIR / "BlinnPhong.frag"),
    ("Gouraud",    SHADER_DIR / "Gouraud.vert", SHADER_DIR / "Gouraud.frag"),
]

#: The rows: (label, mesh, z offset). Flat in front, smooth behind, from the default camera.
NORMAL_STYLES = [
    ("Flat",   (v_flat, i_flat, c_flat, n_flat),         TARGET_SIZE * 1.05),
    ("Smooth", (v_smooth, i_smooth, c_smooth, n_smooth), -TARGET_SIZE * 1.05),
]

column_spacing = TARGET_SIZE * 1.6

#: (name, BasicTransform, ShaderGLDecorator) per copy, so the render loop can push the same
#: uniforms to all six without caring which shader each one uses.
objects = []

for column, (model_name, vert_shader, frag_shader) in enumerate(LIGHTING_MODELS):
    x = (column - 1) * column_spacing
    for style_name, (v, i, c, n), z in NORMAL_STYLES:
        name = f"{model_name}_{style_name}"
        entity = scene.world.createEntity(Entity(name=name))
        scene.world.addEntityChild(rootEntity, entity)

        trans = scene.world.addComponent(entity, BasicTransform(
            name=f"{name}_trans",
            trs=util.translate(x, base_lift, z) @ util.scale(model_scale)))
        mesh = scene.world.addComponent(entity, RenderMesh(name=f"{name}_mesh"))
        # Attribute order must match the shaders' layout(location=...): 0 position, 1 colour,
        # 2 normal. Both Phong.vert and Gouraud.vert declare them in that order.
        mesh.vertex_attributes.append(v)
        mesh.vertex_attributes.append(c)
        mesh.vertex_attributes.append(n)
        mesh.vertex_index.append(i)
        scene.world.addComponent(entity, VertexArray())
        shader = scene.world.addComponent(entity, ShaderGLDecorator(
            Shader(vertex_import_file=vert_shader, fragment_import_file=frag_shader)))

        objects.append((name, trans, shader))

## THE TERRAIN, unlit, to give the objects a ground to stand on ##
vertexTerrain, indexTerrain, colorTerrain = generateTerrain(size=4, N=20)
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

# ---------------- systems ----------------

initUpdate = scene.world.createSystem(InitGLShaderSystem())
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())

# MAIN RENDERING LOOP

running = True
# The plain ImGUIDecorator rather than ImGUIecssDecorator2: the Scenegraph panel would sit on top
# of the leftmost column, and there is nothing to inspect anyway -- the six objects differ only in
# their shader.
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight,
           windowTitle = "Elements: Phong vs Blinn-Phong vs Gouraud", openGLversion = 4,
           customImGUIdecorator = ImGUIDecorator)

# pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
# needs an active GL context
scene.world.traverse_visit(initUpdate, scene.world.root)

# ---------------- the window, the GUI and the camera ----------------

gWindow = scene.renderWindow
gGUI = scene.gContext

eye = util.vec(0.0, 2.3, 3.9)
target = util.vec(0.0, TARGET_SIZE * 0.3, 0.0)
up = util.vec(0.0, 1.0, 0.0)
# also stores eye/target/up, which the mouse camera reads and the shaders need below as viewPos
gGUI.createViewMatrix(eye, target, up)

projMat = util.perspective(50.0, winWidth/winHeight, 0.01, 100.0)

while running:
    running = scene.render()
    displayGUI_text(example_description)

    view = gWindow._myCamera
    viewPos = gWindow._cameraEye

    terrain_shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ terrain_trans.trs, mat4=True)

    # Every copy gets exactly the same uniforms; the three shaders declare the same set, so the
    # only thing that varies across the grid is the shader code itself.
    for name, trans, shader in objects:
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
