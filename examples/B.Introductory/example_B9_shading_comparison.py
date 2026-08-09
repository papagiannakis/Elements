"""
The same comparison as example_B8_shading_models.py, but one object at a time and interactive.

B8 shows all six combinations at once, which is the better way to *compare* them. This one shows
one at a time, which is the better way to *study* one: orbit around a single object and flip a
single variable while everything else stays put.
"""

import imgui
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
"One object, three shading models, two ways of generating normals.\n\n\
Use the Shading Comparison panel to switch Object, Normals and Shading\n\
independently. The light, the material and the camera never change, so\n\
any difference you see is the shading alone.\n\n\
Worth trying, all on the default low-poly sphere:\n\
  - Smooth normals, then Phong -> Gouraud. The highlight nearly\n\
    vanishes: it is smaller than a triangle, so it lands between the\n\
    vertices where Gouraud sampled the lighting and is never computed.\n\
    Orbit and it flickers as it crosses vertices.\n\
  - Flat + Gouraud (the cheapest pair) against Smooth + Blinn-Phong\n\
    (the most expensive).\n\
  - Then pick Teapot and compare Phong against Gouraud again: at 6320\n\
    triangles the two are indistinguishable. Mesh density, not the\n\
    shading model alone, decides whether Gouraud is good enough.\n\n\
Hold the RIGHT mouse button to fly, F for wireframe.\n\
Hit ESC OR Close the window to quit."

# ---------------- what the panel offers ----------------

#: Flat per-vertex colour: a plain .obj carries no colours. Kept fairly dark on purpose, so the
#: specular highlight has somewhere to go instead of saturating to white.
MODEL_COLOR = (0.55, 0.54, 0.66)


def obj(path):
    """A loader for one Wavefront .obj file."""
    return lambda: obj_to_mesh(path, color=list(MODEL_COLOR) + [1.0])


def sphere(lat, lon):
    """A loader for a generated sphere -- lat x lon rings and segments set the triangle count."""
    return lambda: geometry_factory.create_sphere(
        {"lat": lat, "lon": lon, "scale": [2.0, 2.0, 2.0], "color": list(MODEL_COLOR)})


#: The panel's "Object" dropdown. Every entry is auto-scaled to TARGET_SIZE, so adding one of your
#: own needs no other change.
#:
#: The low-poly sphere is in this list because Gouraud shading only goes visibly wrong when the
#: highlight is about the size of a triangle or smaller -- that is when it falls between the
#: vertices where the lighting was evaluated. Every bundled .obj is far too dense for that.
MODELS = {
    "Sphere (low-poly, 252 tris)": sphere(10, 14),
    "Sphere (dense)":              obj(MODEL_DIR / "sphere.obj"),
    "Teapot":                      obj(MODEL_DIR / "teapot.obj"),
    "Cow":                         obj(MODEL_DIR / "cow.obj"),
    "Teddy":                       obj(MODEL_DIR / "teddy.obj"),
}

#: The object is uniformly scaled so its largest dimension is this many world units.
TARGET_SIZE = 1.2

# ---------------- light and material, identical whatever is selected ----------------

Lposition = util.vec(1.2, 2.8, 2.4)
Lambientcolor = util.vec(1.0, 1.0, 1.0)
Lambientstr = 0.25
Lcolor = util.vec(1.0, 1.0, 1.0)
Lintensity = 0.9
#: How STRONG the highlight is.
Mshininess = 0.9
#: How TIGHT it is. All three shaders get the same value, so switching shading model never
#: secretly changes the highlight's sharpness. Raise it to make Gouraud fail harder.
#: example_B10_specular_grid.py lays out a whole range of these side by side.
MspecularExponent = 32.0

winWidth = 1200
winHeight = 800

# ---------------- the scene: RooT -> one entity per shading model, terrain ----------------
#
# A ShaderGLDecorator belongs to an entity, so "switch the shading model" cannot mean swapping a
# shader on one entity. Instead all three exist all the time, share identical mesh data, and the
# two that are not selected are parked far outside the view frustum. It is a translation rather
# than a zero scale because a zero-scale model matrix is singular, and the shaders invert it to
# build the normal matrix.

scene = Scene()
rootEntity = scene.world.createEntity(Entity(name="RooT"))

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
    trans = scene.world.addComponent(entity, BasicTransform(name=f"{entity_name}_trans", trs=util.identity()))
    mesh = scene.world.addComponent(entity, RenderMesh(name=f"{entity_name}_mesh"))
    scene.world.addComponent(entity, VertexArray())
    shader = scene.world.addComponent(entity, ShaderGLDecorator(
        Shader(vertex_import_file=vert_shader, fragment_import_file=frag_shader)))
    variants[shading_name] = (trans, mesh, shader)

## THE TERRAIN, unlit, to give the object a ground to stand on ##
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

# ---------------- mesh building, cached so revisiting a combination is instant ----------------

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
        build = (geometry_factory.build_smooth_shaded_mesh if normals_name == "Smooth"
                 else geometry_factory.build_flat_shaded_mesh)
        v, i, c, n = build(raw_v, raw_i, raw_c)
        _mesh_cache[key] = (v, i, c, n, scale, base_lift)
    return _mesh_cache[key]


#: Current panel selection.
state = {"model": "Sphere (low-poly, 252 tris)", "normals": "Smooth", "shading": "Phong"}


def apply_mesh():
    """Push the selected Object/Normals combination onto all three variants. The caller must run an
    initUpdate traversal afterwards to actually upload the new arrays to the GPU."""
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
            trans.trs = util.translate(0.0, base_lift, 0.0) @ util.scale(scale)
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
        # No re-upload needed: the geometry is identical, only which entity is on screen changes.
        apply_visibility()

    if mesh_changed:
        apply_mesh()
    return mesh_changed


apply_mesh()

# ---------------- systems ----------------

initUpdate = scene.world.createSystem(InitGLShaderSystem())
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())

# MAIN RENDERING LOOP

running = True
# The plain ImGUIDecorator rather than ImGUIecssDecorator2: this example brings its own panel, and
# the Scenegraph one would only get in its way.
scene.init(imgui=True, windowWidth = winWidth, windowHeight = winHeight,
           windowTitle = "Elements: Shading Comparison", openGLversion = 4,
           customImGUIdecorator = ImGUIDecorator)

# pre-pass scenegraph to initialise all GL context dependent geometry, shader classes
# needs an active GL context
scene.world.traverse_visit(initUpdate, scene.world.root)

# ---------------- the window, the GUI and the camera ----------------

gWindow = scene.renderWindow
gGUI = scene.gContext

eye = util.vec(0.0, 1.4, 2.8)
target = util.vec(0.0, TARGET_SIZE * 0.4, 0.0)
up = util.vec(0.0, 1.0, 0.0)
# also stores eye/target/up, which the mouse camera reads and the shaders need below as viewPos
gGUI.createViewMatrix(eye, target, up)

projMat = util.perspective(50.0, winWidth/winHeight, 0.01, 100.0)

while running:
    running = scene.render()
    displayGUI_text(example_description)

    if draw_panel():
        # new vertex arrays: re-run the init traversal so they reach the GPU
        scene.world.traverse_visit(initUpdate, scene.world.root)

    view = gWindow._myCamera
    viewPos = gWindow._cameraEye

    terrain_shader.setUniformVariable(key='modelViewProj', value=projMat @ view @ terrain_trans.trs, mat4=True)

    # Uniforms go to all three variants, not just the visible one: the hidden two are still
    # traversed by the render system, and a stale modelViewProj would show up the moment one of
    # them is selected.
    for trans, _mesh, shader in variants.values():
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
