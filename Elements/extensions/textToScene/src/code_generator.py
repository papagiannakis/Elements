# code_generator.py
from copy import deepcopy
from pathlib import Path
from typing import Optional

import numpy as np

from geometry_factory import create_geometry


DEFAULT_WINDOW = {
    "width": 1200,
    "height": 800,
    "title": "Generated Scene"
}

DEFAULT_TRANSFORM = {
    "position": [0.0, 0.5, 0.0],
    "scale": [1.0, 1.0, 1.0]
}

DEFAULT_MATERIAL = {
    "color": [0.8, 0.0, 0.8]
}


# -----------------------------
# Validation / normalization
# -----------------------------
def ensure_vec3(value, field_name):
    if value is None:
        raise ValueError("Field '{}' cannot be None".format(field_name))

    if not isinstance(value, (list, tuple)):
        raise TypeError("Field '{}' must be a list/tuple of length 3".format(field_name))

    if len(value) != 3:
        raise ValueError("Field '{}' must have exactly 3 values".format(field_name))

    try:
        return [float(value[0]), float(value[1]), float(value[2])]
    except Exception:
        raise TypeError("Field '{}' must contain numeric values".format(field_name))


def clamp_color(color):
    return [max(0.0, min(1.0, float(c))) for c in color]


def normalize_window(window):
    if window is None:
        window = {}

    if not isinstance(window, dict):
        raise TypeError("'window' must be a dictionary")

    normalized = deepcopy(DEFAULT_WINDOW)

    if "width" in window:
        normalized["width"] = int(window["width"])
    if "height" in window:
        normalized["height"] = int(window["height"])
    if "title" in window:
        normalized["title"] = str(window["title"])

    if normalized["width"] <= 0 or normalized["height"] <= 0:
        raise ValueError("Window width and height must be positive")

    return normalized


def normalize_transform(transform):
    if transform is None:
        transform = {}

    if not isinstance(transform, dict):
        raise TypeError("'transform' must be a dictionary")

    normalized = deepcopy(DEFAULT_TRANSFORM)

    if "position" in transform:
        normalized["position"] = ensure_vec3(transform["position"], "position")
    if "scale" in transform:
        normalized["scale"] = ensure_vec3(transform["scale"], "scale")

    return normalized


def normalize_material(material):
    if material is None:
        material = {}

    if not isinstance(material, dict):
        raise TypeError("'material' must be a dictionary")

    normalized = deepcopy(DEFAULT_MATERIAL)

    if "color" in material:
        normalized["color"] = clamp_color(ensure_vec3(material["color"], "color"))

    return normalized


def normalize_node(node, idx=1):
    if not isinstance(node, dict):
        raise TypeError("Each node must be a dictionary")

    node_type = node.get("node_type")
    if node_type is None:
        raise ValueError("Node is missing 'node_type'")

    if node_type == "scene":
        children = node.get("children", [])
        if not isinstance(children, list):
            raise TypeError("'children' of scene must be a list")

        return {
            "node_type": "scene",
            "name": str(node.get("name", "root")),
            "children": [normalize_node(child, i + 1) for i, child in enumerate(children)]
        }

    elif node_type == "mesh_object":
        shape = node.get("shape")
        if shape is None:
            raise ValueError("mesh_object node is missing 'shape'")

        shape = node.get("shape")
        if shape is None:
            raise ValueError("mesh_object node is missing 'shape'")
        
        return {
            "node_type": "mesh_object",
            "name": str(node.get("name", "mesh_object_{}".format(idx))),
            "shape": shape,
            "transform": normalize_transform(node.get("transform", {})),
            "material": normalize_material(node.get("material", {}))
        }
    
    #add support for group nodes 
    elif node_type == "group":
        children = node.get("children", [])
        if not isinstance(children, list):
            raise TypeError("'children' of group must be a list")

        return {
            "node_type": "group",
            "name": str(node.get("name", "group_{}".format(idx))),
            "transform": normalize_transform(node.get("transform", {})),
            "children": [normalize_node(child, i + 1) for i, child in enumerate(children)]
        }

    else:
        raise ValueError("Unsupported node_type: {}".format(node_type))


def validate_and_normalize_scene_ir(scene_ir):
    if not isinstance(scene_ir, dict):
        raise TypeError("Scene IR must be a dictionary")

    if scene_ir.get("node_type") != "scene":
        raise ValueError("Top-level IR must have node_type='scene'")

    normalized_scene = normalize_node(scene_ir)
    normalized_window = normalize_window(scene_ir.get("window", {}))
    normalized_scene["window"] = normalized_window

    return normalized_scene


# -----------------------------
# Code generation helpers
# -----------------------------
def make_translate(position):
    x, y, z = position
    return "util.translate({}, {}, {})".format(float(x), float(y), float(z))


def make_scale(scale):
    sx, sy, sz = scale

    # Elements snippet σου χρησιμοποιεί util.scale(s)
    # κρατάμε uniform scale αν είναι ίδια.
    if sx == sy == sz:
        return "util.scale({})".format(float(sx))

    # προσωρινό fallback για non-uniform scale
    return "util.scale(1.0)"


def vec3_to_util_vec(v):
    return "util.vec({}, {}, {})".format(float(v[0]), float(v[1]), float(v[2]))


def ndarray_to_python(np_array, dtype_name):
    return "np.array({}, dtype=np.{})".format(np_array.tolist(), dtype_name)


def emit_geometry_data(shape, material, transform, suffix):
    params = {
        "color": material["color"],
        "scale": transform.get("scale", [1.0, 1.0, 1.0])
    }

    raw_vertices, raw_indices, raw_colors = create_geometry(shape, params)

    vertices_code = ndarray_to_python(raw_vertices, "float32")
    indices_code = ndarray_to_python(raw_indices, "uint32")
    colors_code = ndarray_to_python(raw_colors, "float32")

    return """
raw_vertices_{suffix} = {vertices_code}
raw_indices_{suffix} = {indices_code}
raw_colors_{suffix} = {colors_code}

vertices_{suffix}, indices_{suffix}, colors_{suffix}, normals_{suffix} = norm.generateSmoothNormalsMesh(
    raw_vertices_{suffix},
    raw_indices_{suffix},
    raw_colors_{suffix}
)
""".format(
        suffix=suffix,
        vertices_code=vertices_code,
        indices_code=indices_code,
        colors_code=colors_code
    )


def build_header(window):
    width = window["width"]
    height = window["height"]

    return '''import numpy as np

import Elements.pyECSS.math_utilities as util
from Elements.pyECSS.Entity import Entity
from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
from Elements.pyECSS.System import TransformSystem, CameraSystem
from Elements.pyGLV.GL.Scene import Scene
from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
from Elements.pyGLV.GL.VertexArray import VertexArray

import OpenGL.GL as gl
import Elements.utils.normals as norm

example_description = "Generated scene from hierarchical IR"

# Light
Lposition = util.vec(2.0, 5.5, 2.0)
Lambientcolor = util.vec(1.0, 1.0, 1.0)
Lambientstr = 0.3
LviewPos = util.vec(2.5, 2.8, 5.0)
Lcolor = util.vec(1.0, 1.0, 1.0)
Lintensity = 0.8

# Material
Mshininess = 0.4

winWidth = {width}
winHeight = {height}

scene = Scene()

rootEntity = scene.world.createEntity(Entity(name="RooT"))

entityCam1 = scene.world.createEntity(Entity(name="Entity1"))
scene.world.addEntityChild(rootEntity, entityCam1)
scene.world.addComponent(
    entityCam1,
    BasicTransform(name="Entity1_TRS", trs=util.translate(0, 0, -8))
)

eye = util.vec(2.5, 2.5, 2.5)
target = util.vec(0.0, 0.0, 0.0)
up = util.vec(0.0, 1.0, 0.0)
view = util.lookat(eye, target, up)
projMat = util.perspective(50.0, winWidth / winHeight, 0.01, 100.0)

m = np.linalg.inv(projMat @ view)

entityCam2 = scene.world.createEntity(Entity(name="Entity_Camera"))
scene.world.addEntityChild(entityCam1, entityCam2)
scene.world.addComponent(entityCam2, BasicTransform(name="Camera_TRS", trs=util.identity()))
orthoCam = scene.world.addComponent(entityCam2, Camera(m, "orthoCam", "Camera", "500"))

transUpdate = scene.world.createSystem(TransformSystem("transUpdate", "TransformSystem", "001"))
camUpdate = scene.world.createSystem(CameraSystem("camUpdate", "CameraUpdate", "200"))
renderUpdate = scene.world.createSystem(RenderGLShaderSystem())
initUpdate = scene.world.createSystem(InitGLShaderSystem())
'''.format(width=width, height=height)


def build_footer(title, uniform_block):
    indented_uniforms = "\n".join(
        ("    " + line) if line.strip() else line
        for line in uniform_block.splitlines()
    )

    return '''
running = True
scene.init(
    imgui=True,
    windowWidth=winWidth,
    windowHeight=winHeight,
    windowTitle="{title}",
    openGLversion=4,
    customImGUIdecorator=ImGUIecssDecorator2
)

scene.world.traverse_visit(initUpdate, scene.world.root)

eManager = scene.world.eventManager
gWindow = scene.renderWindow
gGUI = scene.gContext

renderGLEventActuator = RenderGLStateSystem()

eManager._subscribers['OnUpdateWireframe'] = gWindow
eManager._actuators['OnUpdateWireframe'] = renderGLEventActuator
eManager._subscribers['OnUpdateCamera'] = gWindow
eManager._actuators['OnUpdateCamera'] = renderGLEventActuator

gWindow._myCamera = view

while running:
    running = scene.render()
    scene.world.traverse_visit(renderUpdate, scene.world.root)
    scene.world.traverse_visit_pre_camera(camUpdate, orthoCam)
    scene.world.traverse_visit(camUpdate, scene.world.root)

    view = gWindow._myCamera
{uniforms}
    scene.render_post()

scene.shutdown()
'''.format(title=title, uniforms=indented_uniforms)


# -----------------------------
# Recursive node emission
# -----------------------------
def emit_mesh_object_node(node, idx, parent_entity_var, parent_trs_expr):
    name = node["name"]
    shape = node["shape"]
    transform = node["transform"]
    material = node["material"]

    position = transform["position"]
    scale = transform["scale"]
    color = material["color"]

    suffix = str(idx)

    entity_var = "node_{}".format(suffix)
    trans_var = "trans_{}".format(suffix)
    mesh_var = "mesh_{}".format(suffix)
    shader_var = "shader_{}".format(suffix)

    local_trs_expr = "util.identity() @ {}".format(make_translate(position))
    world_trs_expr = "{} @ ({})".format(parent_trs_expr, local_trs_expr)

    mat_color_expr = vec3_to_util_vec(color)
    geometry_code = emit_geometry_data(shape, material, transform, suffix)

    object_code = """
# ===== mesh_object: {name} =====
{geometry_code}

{entity_var} = scene.world.createEntity(Entity(name="{name}"))
scene.world.addEntityChild({parent_entity_var}, {entity_var})

{trans_var} = scene.world.addComponent(
    {entity_var},
    BasicTransform(name="{name}_TRS", trs={local_trs_expr})
)

{mesh_var} = scene.world.addComponent({entity_var}, RenderMesh(name="{name}_mesh"))
{mesh_var}.vertex_attributes.append(vertices_{suffix})
{mesh_var}.vertex_attributes.append(colors_{suffix})
{mesh_var}.vertex_attributes.append(normals_{suffix})
{mesh_var}.vertex_index.append(indices_{suffix})

scene.world.addComponent({entity_var}, VertexArray())

{shader_var} = scene.world.addComponent(
    {entity_var},
    ShaderGLDecorator(
        Shader(
            vertex_source=Shader.VERT_PHONG_MVP,
            fragment_source=Shader.FRAG_PHONG
        )
    )
)
""".format(
        name=name,
        geometry_code=geometry_code,
        entity_var=entity_var,
        parent_entity_var=parent_entity_var,
        trans_var=trans_var,
        local_trs_expr=local_trs_expr,
        mesh_var=mesh_var,
        suffix=suffix,
        shader_var=shader_var
    )

    uniform_code = """
model_{suffix} = {world_trs_expr}
mvp_{suffix} = projMat @ view @ model_{suffix}
{shader_var}.setUniformVariable(key='modelViewProj', value=mvp_{suffix}, mat4=True)
{shader_var}.setUniformVariable(key='model', value=model_{suffix}, mat4=True)
{shader_var}.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
{shader_var}.setUniformVariable(key='ambientStr', value=Lambientstr, float1=True)
{shader_var}.setUniformVariable(key='viewPos', value=LviewPos, float3=True)
{shader_var}.setUniformVariable(key='lightPos', value=Lposition, float3=True)
{shader_var}.setUniformVariable(key='lightColor', value=Lcolor, float3=True)
{shader_var}.setUniformVariable(key='lightIntensity', value=Lintensity, float1=True)
{shader_var}.setUniformVariable(key='shininess', value=Mshininess, float1=True)
{shader_var}.setUniformVariable(key='matColor', value={mat_color_expr}, float3=True)
""".format(
        suffix=suffix,
        shader_var=shader_var,
        world_trs_expr=world_trs_expr,
        mat_color_expr=mat_color_expr
    )

    return object_code, uniform_code

#group node emmission. The group must create: 
# - a new entity 
# - BasicTransform component
# - and then emit its children with that entity as the parent_entity_var
def emit_group_node(node, idx, parent_entity_var, parent_trs_expr, state):
    name = node["name"]
    transform = node["transform"]

    position = transform["position"]
    scale = transform["scale"]

    suffix = str(idx)
    entity_var = "group_node_{}".format(suffix)
    trans_var = "group_trans_{}".format(suffix)

    trs_expr = "{} @ {}".format(make_scale(scale), make_translate(position))
    local_trs_expr = "{} @ {}".format(make_scale(scale), make_translate(position))
    world_trs_expr = "{} @ ({})".format(parent_trs_expr, local_trs_expr)
    object_code = """
# ===== group: {name} =====
{entity_var} = scene.world.createEntity(Entity(name="{name}"))
scene.world.addEntityChild({parent_entity_var}, {entity_var})

{trans_var} = scene.world.addComponent(
    {entity_var},
    BasicTransform(name="{name}_TRS", trs={trs_expr})
)
""".format(
        name=name,
        entity_var=entity_var,
        parent_entity_var=parent_entity_var,
        trans_var=trans_var,
        trs_expr=trs_expr
    )

    child_object_blocks = []
    child_uniform_blocks = []

    for child in node.get("children", []):
        child_obj_code, child_uniform_code = emit_node(child, entity_var, world_trs_expr, state)
        child_object_blocks.append(child_obj_code)
        child_uniform_blocks.append(child_uniform_code)

    full_object_code = object_code + "\n" + "\n".join(child_object_blocks)
    full_uniform_code = "\n".join(child_uniform_blocks)

    return full_object_code, full_uniform_code


def emit_node(node, parent_entity_var, parent_trs_expr, state):
    node_type = node["node_type"]

    if node_type == "scene":
        object_blocks = []
        uniform_blocks = []

        for child in node.get("children", []):
            child_obj_code, child_uniform_code = emit_node(
                child,
                "rootEntity",
                "util.identity()",
                state
            )
            object_blocks.append(child_obj_code)
            uniform_blocks.append(child_uniform_code)

        return "\n".join(object_blocks), "\n".join(uniform_blocks)
    elif node_type == "group":
        state["counter"] += 1
        return emit_group_node(node, state["counter"], parent_entity_var, parent_trs_expr, state)

    elif node_type == "mesh_object":
        state["counter"] += 1
        return emit_mesh_object_node(node, state["counter"], parent_entity_var, parent_trs_expr)

    else:
        raise ValueError("Unsupported node_type: {}".format(node_type))

# -----------------------------
# Main public API
# -----------------------------
def generate_scene_script(scene_ir):
    scene_ir = validate_and_normalize_scene_ir(scene_ir)

    window = scene_ir["window"]
    title = window["title"]

    header = build_header(window)

    state = {"counter": 0}
    object_code, uniform_code = emit_node(scene_ir, "rootEntity", "util.identity()", state)

    footer = build_footer(title, uniform_code)

    final_script = header + "\n" + object_code + "\n" + footer
    return final_script

'''
def save_script(script, output_path: Optional[str] = None):
    base_dir = Path(__file__).resolve().parent

    if output_path is None:
        output_file = base_dir / "scene_out.py"
    else:
        output_file = Path(output_path).resolve()

    with open(str(output_file), "w", encoding="utf-8") as f:
        f.write(script)

    print("Saved script to:", output_file)
    ''' #ISSUE WITH PATHS RESTRICTIONS AND SAVING 
def save_script(script, output_path: Optional[str] = None):
    if output_path is None:
        output_file = Path.home() / "Desktop" / "scene_out.py"
    else:
        output_file = Path(output_path).resolve()

    with open(str(output_file), "w", encoding="utf-8") as f:
        f.write(script)

    print("Saved script to:", output_file)

    #keep the old saving method as a fallback in case of issues with desktop path
    # base_dir = Path(__file__).resolve().parent 