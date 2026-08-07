"""
Phong vs Blinn-Phong vs Gouraud, side by side.

Six copies of the same imported model are laid out in a 2 x 3 grid:

                      Phong          Blinn-Phong        Gouraud
    back  row  |   smooth normals   smooth normals   smooth normals
    front row  |    flat normals     flat normals     flat normals

So each *column* isolates one shading model, and each *row* isolates how the mesh normals were
generated. Everything else -- geometry, light, material, camera -- is identical across all six,
which is the only way the comparison means anything.

What to look for:

  * Phong (left) vs Blinn-Phong (middle): both compute the lighting once per *fragment*, and
    differ in exactly one line of the fragment shader. Phong reflects the light ray about the
    normal and compares it to the viewer; Blinn-Phong compares the normal to the vector halfway
    between light and viewer. At the same exponent Blinn-Phong's highlight is the wider of the
    two -- raise MspecularExponent below and watch both tighten; see BlinnPhong.frag for why,
    and what exponent makes them match.

  * Gouraud (right): computes the lighting once per *vertex* and lets the rasteriser interpolate
    the finished colour. Far cheaper -- and on the smooth row you will notice the highlight has
    almost entirely disappeared. That is Gouraud's characteristic failure: the highlight is
    smaller than a triangle, so it falls between the vertices where the lighting was sampled and
    is never computed at all. Orbit the camera and it flickers in and out.

    This only shows up on a coarse mesh, which is why the default model is a 252-triangle sphere
    rather than one of the bundled .obj files -- see the note on MODEL below.

  * front row vs back row: flat normals give every triangle a single normal, so the surface reads
    as faceted; smooth normals average across the triangles meeting at each vertex, so it reads as
    curved. Same triangles either way -- only the normals differ.

Hit ESC or close the window to quit.
"""

from OpenGL.GL import GL_LINES

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, RenderMesh
from Elements.pyECSS.System import TransformSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIDecorator
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

from Elements.utils.terrain import generateTerrain
from Elements.utils.Shortcuts import displayGUI_text
from Elements.definitions import MODEL_DIR, SHADER_DIR

# The same OBJ reader the Showcase example's object gallery uses. It is more tolerant than
# Elements.utils.obj_to_mesh: it accepts v, v/vt and v/vt/vn face formats and fan-triangulates
# quads and n-gons, so most .obj files found in the wild just load.
from Elements.extensions.showcase.showcase_helpers import load_obj_mesh

# NOT Elements.utils.normals. That module's generateFlatNormalsMesh decides whether to split the
# mesh into per-triangle vertices by looking for duplicate vertex *positions*, and quietly falls
# back to smooth-looking normals if the model happens to contain any (teapot.obj and cow.obj both
# do). This version checks the *index* array, which is what actually decides whether triangles
# share vertices -- so the "flat" row below really is flat.
import Elements.extensions.Normals_USDimporter_BSP.normals as norm

# A sphere generated at a chosen triangle count, rather than loaded from a file -- the default
# model below. See the note on MODEL for why a coarse mesh is what this comparison needs.
from Elements.extensions.Shapes.geometry_factory import create_sphere


# ================================================================================================
# Change these
# ================================================================================================

def obj(path):
    """A loader for one Wavefront .obj file."""
    return lambda: load_obj_mesh(path, MODEL_COLOR)


def sphere(lat, lon):
    """A loader for a procedurally generated sphere -- lat/lon control the triangle count."""
    return lambda: create_sphere({"lat": lat, "lon": lon, "scale": [2.0, 2.0, 2.0],
                                  "color": list(MODEL_COLOR)})


#: Which model to show in all six slots. Swap in any .obj with, for example:
#:     MODEL = obj(MODEL_DIR / "teapot.obj")
#: (cow.obj, teddy.obj and sphere.obj are also bundled), or point obj() at a file of your own.
#: Whatever you pick is auto-scaled and auto-spaced by TARGET_SIZE below.
#:
#: The default is a deliberately coarse 252-triangle sphere, because a dense mesh cannot show what
#: the Gouraud column is here to show. Gouraud only goes visibly wrong when a specular highlight
#: is roughly the size of a triangle or smaller -- that is when the highlight lands between the
#: vertices where the lighting was evaluated and is simply missed. Every .obj bundled with
#: Elements is far too fine for that: teapot.obj is 6320 triangles, about 3 pixels each at this
#: scale, and its Gouraud rendering comes out pixel-identical to its Phong one. Load the teapot to
#: compare Phong against Blinn-Phong, but keep the coarse sphere to see Gouraud break.
MODEL = sphere(10, 14)
# MODEL_PATH = MODEL_DIR / "cow.obj"
# MODEL_PATH = MODEL_DIR / "teapot.obj"

#: Each copy is uniformly scaled so its largest dimension is this many world units.
TARGET_SIZE = 0.8

#: Flat per-vertex colour of the models -- plain .obj files do not carry one.
MODEL_COLOR = (0.55, 0.54, 0.66)


# ================================================================================================
# Light and material -- shared by all six objects, so only the shading model varies
# ================================================================================================

Lposition = util.vec(0.9, 2.6, 2.2)
Lambientcolor = util.vec(1.0, 1.0, 1.0)
Lambientstr = 0.25
Lcolor = util.vec(1.0, 1.0, 1.0)
Lintensity = 0.9
# How *strong* the highlight is. Turned up from the 0.4 the other examples use, to make the
# highlights -- the whole point here -- easy to see.
Mshininess = 0.9
#: How *tight* the highlight is. All three shaders get the same value, so the comparison stays
#: fair and the shading model is the only thing that varies. Worth raising: the tighter the
#: highlight, the more dramatically Gouraud (right column) loses it between vertices.
#: Note Blinn-Phong needs roughly 4x Phong's exponent to produce a highlight of the same size,
#: which is exactly why the middle column looks wider at an equal value.
MspecularExponent = 32.0

# The viewer position (uniform viewPos) is deliberately absent here: the specular term depends on
# where the camera is, so it is read back from the camera every frame in the render loop.

winWidth = 1200
winHeight = 800

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))


# ================================================================================================
# The 2 x 3 grid
# ================================================================================================

#: (column label, vertex shader, fragment shader). Note that Blinn-Phong reuses Phong.vert
#: verbatim: the two models are identical right up to the fragment stage.
LIGHTING_MODELS = [
    ("Phong",      SHADER_DIR / "Phong.vert",   SHADER_DIR / "Phong.frag"),
    ("BlinnPhong", SHADER_DIR / "Phong.vert",   SHADER_DIR / "BlinnPhong.frag"),
    ("Gouraud",    SHADER_DIR / "Gouraud.vert", SHADER_DIR / "Gouraud.frag"),
]

vertices, indices, colors = MODEL()

# One scale for every copy, derived from the model's own bounding box, so any .obj lands at a
# sensible size. extent[:3] drops the homogeneous w component.
extent = vertices[:, :3].max(axis=0) - vertices[:, :3].min(axis=0)
model_scale = TARGET_SIZE / float(extent.max())
# How far the model's lowest point sits below its own origin, scaled -- lift each copy by this so
# it stands on the terrain instead of sinking through it.
base_lift = -float(vertices[:, 1].min()) * model_scale

# Build both meshes once and share the arrays across the three columns: the columns differ only in
# which shader they hand them to, never in the geometry.
#   flat   -> one normal per triangle (the mesh is split so no vertex is shared)
#   smooth -> one normal per vertex, averaged over the triangles meeting there
v_flat, i_flat, c_flat, n_flat = norm.generateFlatNormalsMesh(vertices, indices, colors)
v_smooth, i_smooth, c_smooth, n_smooth = norm.generateSmoothNormalsMesh(vertices, indices, colors)

#: (row label, mesh, z offset). Flat in front, smooth behind, as seen from the default camera.
NORMAL_STYLES = [
    ("Flat",   (v_flat, i_flat, c_flat, n_flat),         TARGET_SIZE * 1.05),
    ("Smooth", (v_smooth, i_smooth, c_smooth, n_smooth), -TARGET_SIZE * 1.05),
]

column_spacing = TARGET_SIZE * 1.6

#: Filled in below as (entity name, BasicTransform, ShaderGLDecorator) so the render loop can push
#: the same uniforms to every object without caring which shader it is.
objects = []

for column, (model_name, vert_shader, frag_shader) in enumerate(LIGHTING_MODELS):
    x = (column - 1) * column_spacing
    for style_name, (v, i, c, n), z in NORMAL_STYLES:
        name = f"{model_name}_{style_name}"
        entity = scene.world.createEntity(Entity(name=name))
        scene.world.addEntityChild(rootEntity, entity)

        trans = scene.world.addComponent(entity, BasicTransform(
            name=f"{name}_TRS",
            trs=util.translate(x, base_lift, z) @ util.scale(model_scale, model_scale, model_scale),
        ))
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


# ================================================================================================
# Terrain, to give the objects a ground to stand on
# ================================================================================================

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


# ================================================================================================
# Systems and main loop
# ================================================================================================

transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())

running = True
# The plain ImGUIDecorator, not one of the ImGUIecssDecorator variants the neighbouring examples
# use: the Scenegraph panel those add is wide enough to sit on top of the leftmost column, and
# there is nothing to inspect here anyway -- the six objects differ only in their shader.
scene.init(imgui=True, windowWidth=winWidth, windowHeight=winHeight,
           windowTitle="Elements: Phong vs Blinn-Phong vs Gouraud",
           openGLversion=4, customImGUIdecorator=ImGUIDecorator)

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

eye = util.vec(0.0, 2.3, 3.9)
target = util.vec(0.0, TARGET_SIZE * 0.3, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
projMat = util.perspective(50.0, winWidth / winHeight, 0.01, 100.0)

gWindow._myCamera = view  # otherwise, an imgui slider must be moved to properly update
gWindow._cameraEye = eye  # seed the world-space eye, so viewPos is correct before the first camera move

example_description = (
    "Six copies of one model, comparing three shading models.\n\n"
    "Columns, left to right:  Phong | Blinn-Phong | Gouraud\n"
    "Front row: flat (sharp) normals.  Back row: smooth normals.\n\n"
    "Phong and Blinn-Phong both light every fragment and differ in\n"
    "only one line of the fragment shader. Gouraud lights every\n"
    "vertex instead and interpolates the result, so its highlights\n"
    "look faceted and can fall between vertices and vanish.\n\n"
    "Edit MODEL_PATH near the top of the file to try another .obj.\n"
    "Move the camera with the mouse or the GUI. Hit ESC to quit."
)

while running:
    running = scene.render()
    displayGUI_text(example_description)
    scene.world.traverse_visit(transUpdate, scene.world.root)

    view = gWindow._myCamera    # updated by the mouse / the imgui camera sliders
    viewPos = gWindow._cameraEye  # world-space camera position, follows the view matrix above

    terrain_shader.setUniformVariable(
        key='modelViewProj', value=projMat @ view @ terrain_trans.l2world, mat4=True)

    # Every object gets exactly the same uniforms. The three shaders declare the same set, so the
    # only thing that varies across the grid is the shader code itself.
    for name, trans, shader in objects:
        shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ trans.l2world, mat4=True)
        shader.setUniformVariable(key='model', value=trans.l2world, mat4=True)
        shader.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
        shader.setUniformVariable(key='ambientStr', value=Lambientstr, float1=True)
        shader.setUniformVariable(key='viewPos', value=viewPos, float3=True)
        shader.setUniformVariable(key='lightPos', value=Lposition, float3=True)
        shader.setUniformVariable(key='lightColor', value=Lcolor, float3=True)
        shader.setUniformVariable(key='lightIntensity', value=Lintensity, float1=True)
        shader.setUniformVariable(key='shininess', value=Mshininess, float1=True)
        shader.setUniformVariable(key='specularExponent', value=MspecularExponent, float1=True)

    # Render after the uniforms are set, so this frame draws with this frame's camera.
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.render_post()

scene.shutdown()
