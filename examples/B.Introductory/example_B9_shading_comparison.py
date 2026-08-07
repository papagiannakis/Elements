"""
The same comparison as example_B8_shading_models.py, but interactive: one object at a time, with
an ImGui panel to switch the model, the normals and the shading model independently.

B8 shows all six combinations at once, which is the better way to *compare* them. This one shows
one at a time, which is the better way to *study* one -- you can orbit around a single object and
flip a single variable while everything else stays put.

Panel controls:

  Object    -- which model to show. Add your own .obj to MODELS below; every model is auto-scaled
               to TARGET_SIZE, so no hand-tuning is needed.
  Normals   -- Smooth (normals averaged over the triangles meeting at each vertex, so the surface
               reads as curved) or Flat (one normal per triangle, so it reads as faceted). The
               triangles are the same either way; only the normals change.
  Shading   -- Phong, Blinn-Phong or Gouraud. Phong and Blinn-Phong both light every fragment and
               differ in exactly one line of the fragment shader. Gouraud lights every vertex
               instead and interpolates the resulting colour, which is much cheaper but loses
               highlights that fall between vertices.

Things worth trying, all on the default low-poly sphere:

  * Smooth normals, then flip Phong -> Gouraud. The specular highlight all but vanishes: it is
    smaller than a triangle, so it lands between the vertices where Gouraud sampled the lighting
    and is never computed. Orbit and it flickers as it crosses vertices.
  * Flat normals + Gouraud, the cheapest combination of both axes, against Smooth + Blinn-Phong,
    the most expensive.
  * Then switch Object to Teapot and try Phong vs Gouraud again -- at 6320 triangles the two are
    indistinguishable. Mesh density, not the shading model alone, decides whether Gouraud is good
    enough; that is exactly why it was worth using when vertices were expensive.

Hit ESC or close the window to quit.
"""

import imgui
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

# The same tolerant OBJ reader the Showcase example's object gallery uses -- see the note in
# example_B8_shading_models.py.
from Elements.extensions.showcase.showcase_helpers import load_obj_mesh

# NOT Elements.utils.normals -- its generateFlatNormalsMesh silently produces smooth-looking
# normals for teapot.obj and cow.obj. See the longer note in example_B8_shading_models.py.
import Elements.extensions.Normals_USDimporter_BSP.normals as norm

# A sphere generated at a chosen triangle count, rather than loaded from a file. The low-poly
# entry in MODELS below is the only object here coarse enough to actually show Gouraud shading
# failing -- see the "Why a low-poly sphere" note under MODELS.
from Elements.extensions.Shapes.geometry_factory import create_sphere


# ================================================================================================
# Change these
# ================================================================================================

def obj(path):
    """A loader for one Wavefront .obj. Add your own model to MODELS with, for example:
           "My model": obj(Path("/somewhere/mine.obj")),"""
    return lambda: load_obj_mesh(path, MODEL_COLOR)


def sphere(lat, lon):
    """A loader for a procedurally generated sphere -- lat/lon control the triangle count."""
    return lambda: create_sphere({"lat": lat, "lon": lon, "scale": [2.0, 2.0, 2.0],
                                  "color": list(MODEL_COLOR)})


#: Everything offered in the panel's "Object" dropdown. Every entry is auto-scaled to TARGET_SIZE,
#: so adding one needs no other change.
#:
#: Why a low-poly sphere is in this list: Gouraud shading only goes visibly wrong when a specular
#: highlight is about the size of a triangle or smaller, because that is when the highlight falls
#: between the vertices where the lighting was evaluated. Every .obj bundled with Elements is far
#: too dense for that -- teapot.obj alone is 6320 triangles, which at this scale is roughly 3
#: pixels each, so its Gouraud rendering is indistinguishable from its Phong one. The 252-triangle
#: sphere is coarse enough to show the real difference. Pick it, choose Gouraud, and orbit.
MODELS = {
    "Sphere (low-poly, 252 tris)": sphere(10, 14),
    "Sphere (dense)":              obj(MODEL_DIR / "sphere.obj"),
    "Teapot":                      obj(MODEL_DIR / "teapot.obj"),
    "Cow":                         obj(MODEL_DIR / "cow.obj"),
    "Teddy":                       obj(MODEL_DIR / "teddy.obj"),
}

#: The object is uniformly scaled so its largest dimension is this many world units.
TARGET_SIZE = 1.2

#: Flat per-vertex colour -- plain .obj files do not carry one. Kept fairly dark on purpose so the
#: specular highlight has somewhere to go instead of saturating to white.
MODEL_COLOR = (0.55, 0.54, 0.66)


# ================================================================================================
# Light and material -- identical whichever shading model is selected, so the panel really is
# changing only the shading
# ================================================================================================

Lposition = util.vec(1.2, 2.8, 2.4)
Lambientcolor = util.vec(1.0, 1.0, 1.0)
Lambientstr = 0.25
Lcolor = util.vec(1.0, 1.0, 1.0)
Lintensity = 0.9
#: How *strong* the specular highlight is.
Mshininess = 0.9
#: How *tight* it is. All three shaders are given the same value, so switching shading model
#: never secretly changes the highlight's sharpness. Raise it to make Gouraud fail harder: the
#: tighter the highlight, the more likely it lands between vertices and is never computed.
#: example_B10_specular_grid.py lays out a whole range of these side by side.
MspecularExponent = 32.0

winWidth = 1200
winHeight = 800

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))


# ================================================================================================
# One entity per shading model
# ================================================================================================
#
# A ShaderGLDecorator is attached to an entity, so "switch the shading model" cannot mean swapping
# a shader on one entity -- instead all three exist all the time, share identical mesh data, and
# the two that are not selected get parked far outside the view frustum. That is the standard
# "hide an entity" trick in Elements (see _HIDDEN_OFFSET in extensions/showcase/showcase_helpers.py);
# it is a translation rather than a zero scale because a zero-scale model matrix is singular and
# the shaders invert it to build the normal matrix.

SHADING_MODELS = [
    ("Phong",       SHADER_DIR / "Phong.vert",   SHADER_DIR / "Phong.frag"),
    ("Blinn-Phong", SHADER_DIR / "Phong.vert",   SHADER_DIR / "BlinnPhong.frag"),
    ("Gouraud",     SHADER_DIR / "Gouraud.vert", SHADER_DIR / "Gouraud.frag"),
]
NORMAL_STYLES = ["Smooth", "Flat"]

HIDDEN_OFFSET = (100000.0, 100000.0, 100000.0)

#: shading model name -> (BasicTransform, RenderMesh, ShaderGLDecorator)
variants = {}

for shading_name, vert_shader, frag_shader in SHADING_MODELS:
    entity_name = shading_name.replace("-", "")
    entity = scene.world.createEntity(Entity(name=entity_name))
    scene.world.addEntityChild(rootEntity, entity)
    trans = scene.world.addComponent(entity, BasicTransform(name=f"{entity_name}_TRS", trs=util.identity()))
    mesh = scene.world.addComponent(entity, RenderMesh(name=f"{entity_name}_mesh"))
    scene.world.addComponent(entity, VertexArray())
    shader = scene.world.addComponent(entity, ShaderGLDecorator(
        Shader(vertex_import_file=vert_shader, fragment_import_file=frag_shader)))
    variants[shading_name] = (trans, mesh, shader)


# ================================================================================================
# Mesh building, cached so flipping back to a combination you already picked is instant
# ================================================================================================

_mesh_cache = {}


def mesh_for(model_name, normals_name):
    """(vertices, indices, colors, normals, scale, base_lift) for one Object/Normals combination."""
    key = (model_name, normals_name)
    if key not in _mesh_cache:
        raw_v, raw_i, raw_c = MODELS[model_name]()
        # Scale and lift come from the *raw* model, so both normal styles of a model agree.
        extent = raw_v[:, :3].max(axis=0) - raw_v[:, :3].min(axis=0)
        scale = TARGET_SIZE / float(extent.max())
        base_lift = -float(raw_v[:, 1].min()) * scale
        generate = norm.generateSmoothNormalsMesh if normals_name == "Smooth" else norm.generateFlatNormalsMesh
        v, i, c, n = generate(raw_v, raw_i, raw_c)
        _mesh_cache[key] = (v, i, c, n, scale, base_lift)
    return _mesh_cache[key]


#: Current panel selection.
state = {"model": "Sphere (low-poly, 252 tris)", "normals": "Smooth", "shading": "Phong"}


def apply_mesh():
    """Push the selected Object/Normals combination onto all three variants. The caller must run
    an initUpdate traversal afterwards to actually upload the new arrays to the GPU."""
    v, i, c, n, scale, base_lift = mesh_for(state["model"], state["normals"])
    for trans, mesh, _shader in variants.values():
        # Attribute order must match the shaders' layout(location=...): 0 position, 1 colour,
        # 2 normal. Both Phong.vert and Gouraud.vert declare them in that order.
        mesh.vertex_attributes = [v, c, n]
        mesh.vertex_index = [i]
    apply_visibility()


def apply_visibility():
    """Selected variant to the origin, the other two parked outside the frustum."""
    _v, _i, _c, _n, scale, base_lift = mesh_for(state["model"], state["normals"])
    for shading_name, (trans, _mesh, _shader) in variants.items():
        if shading_name == state["shading"]:
            trans.trs = util.translate(0.0, base_lift, 0.0) @ util.scale(scale, scale, scale)
        else:
            trans.trs = util.translate(*HIDDEN_OFFSET)


def draw_panel():
    """The one ImGui window this example adds. Returns True when the *mesh* changed (Object or
    Normals), which is what forces a re-upload; a Shading change only moves transforms."""
    imgui.begin("Shading Comparison", True)

    model_names = list(MODELS.keys())
    changed_model, model_idx = imgui.combo("Object", model_names.index(state["model"]), model_names)
    changed_normals, normals_idx = imgui.combo(
        "Normals", NORMAL_STYLES.index(state["normals"]), NORMAL_STYLES)
    shading_names = [name for name, _v, _f in SHADING_MODELS]
    changed_shading, shading_idx = imgui.combo(
        "Shading", shading_names.index(state["shading"]), shading_names)

    imgui.separator()
    imgui.text_wrapped(
        "Phong and Blinn-Phong shade per fragment and differ in one "
        "line of the fragment shader. Gouraud shades per vertex and "
        "interpolates, so highlights between vertices are lost.")
    imgui.end()

    mesh_changed = False
    if changed_model and model_names[model_idx] != state["model"]:
        state["model"] = model_names[model_idx]
        mesh_changed = True
    if changed_normals and NORMAL_STYLES[normals_idx] != state["normals"]:
        state["normals"] = NORMAL_STYLES[normals_idx]
        mesh_changed = True
    if changed_shading and shading_names[shading_idx] != state["shading"]:
        state["shading"] = shading_names[shading_idx]
        # No re-upload needed -- the geometry is identical, only which entity is on screen changes.
        apply_visibility()

    if mesh_changed:
        apply_mesh()
    return mesh_changed


apply_mesh()


# ================================================================================================
# Terrain, to give the object a ground to stand on
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
# The plain ImGUIDecorator, not an ImGUIecssDecorator: this example brings its own panel, and the
# Scenegraph one would only get in its way.
scene.init(imgui=True, windowWidth=winWidth, windowHeight=winHeight,
           windowTitle="Elements: Shading Comparison",
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

eye = util.vec(0.0, 1.4, 2.8)
target = util.vec(0.0, TARGET_SIZE * 0.4, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
projMat = util.perspective(50.0, winWidth / winHeight, 0.01, 100.0)

gWindow._myCamera = view  # otherwise, an imgui slider must be moved to properly update
gWindow._cameraEye = eye  # seed the world-space eye, so viewPos is correct before the first camera move

example_description = (
    "One object, three shading models, two ways of generating normals.\n\n"
    "Use the Shading Comparison panel to switch Object, Normals and\n"
    "Shading independently. The light, material and camera never\n"
    "change, so any difference you see is the shading alone.\n\n"
    "On the low-poly sphere, switch Phong -> Gouraud: the highlight\n"
    "nearly vanishes, because it is smaller than a triangle and so\n"
    "falls between the vertices Gouraud sampled. On the Teapot, at\n"
    "6320 triangles, the two look identical.\n\n"
    "Move the camera with the mouse or the GUI. Hit ESC to quit."
)

while running:
    running = scene.render()
    displayGUI_text(example_description)

    if draw_panel():
        # New vertex arrays -- re-run the init traversal so they reach the GPU, exactly as the
        # Showcase example does after its own object gallery changes.
        scene.world.traverse_visit(initUpdate, scene.world.root)

    scene.world.traverse_visit(transUpdate, scene.world.root)

    view = gWindow._myCamera      # updated by the mouse / the imgui camera sliders
    viewPos = gWindow._cameraEye  # world-space camera position, follows the view matrix above

    terrain_shader.setUniformVariable(
        key='modelViewProj', value=projMat @ view @ terrain_trans.l2world, mat4=True)

    # Uniforms go to all three variants, not just the visible one: the hidden two are still
    # traversed by the render system, and leaving them with a stale modelViewProj would be a
    # latent bug the moment one of them is selected.
    for trans, _mesh, shader in variants.values():
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
