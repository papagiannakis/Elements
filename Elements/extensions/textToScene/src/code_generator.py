# code_generator.py
import json
from copy import deepcopy
from pathlib import Path
from typing import Optional

import numpy as np

from geometry_factory import build_render_mesh, create_textured_cube


DEFAULT_WINDOW = {
    "width": 1200,
    "height": 800,
    "title": "Generated Scene"
}

DEFAULT_TRANSFORM = {
    "position": [0.0, 0.5, 0.0],
    "scale": [1.0, 1.0, 1.0]
}

#Add support for texture in material normalization

DEFAULT_MATERIAL = {
    "color": [0.8, 0.0, 0.8],
    "texture":{
        "enabled": False,
        "path": None
    }
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

    if "texture" in material:
        texture = material["texture"]
        if not isinstance(texture, dict):
            raise TypeError("'texture' must be a dictionary")
        normalized["texture"]["enabled"] = bool(texture.get("enabled", False))  
        normalized["texture"]["path"]=texture.get("path", None)
    return normalized

def is_textured_material(material):
    tex = material.get("texture") or {}
    return bool(tex.get("enabled", False)) and bool(tex.get("path"))

#-----------------------------
#texture loading and emitting code generation for textured materials


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
    elif node_type == "light":
        light_type = node.get("light_type")
        if light_type is None:
            raise ValueError("light node is missing 'light_type'")

        if light_type not in ["point", "directional"]:
            raise ValueError("Unsupported light_type: {}".format(light_type))

        input_props = node.get("properties", {})
        if not isinstance(input_props, dict):
            raise TypeError("'properties' of light must be a dictionary")

        props = {
            "position": [2.0, 5.5, 2.0],
            "direction": [1.0, -1.0, -1.0],
            "color": [1.0, 1.0, 1.0],
            "intensity": 1.2
        }

        if "position" in input_props:
            props["position"] = ensure_vec3(input_props["position"], "light.position")
        if "direction" in input_props:
            props["direction"] = ensure_vec3(input_props["direction"], "light.direction")
        if "color" in input_props:
            props["color"] = clamp_color(ensure_vec3(input_props["color"], "light.color"))
        if "intensity" in input_props:
            props["intensity"] = float(input_props["intensity"])

        return {
            "node_type": "light",
            "name": str(node.get("name", "light_{}".format(idx))),
            "light_type": light_type,
            "properties": props
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

#----------------------------
# LIGHTS 
# ---------------------------

def collect_lights(node, lights):
    if node is None: return 
    if not isinstance(node, dict): return

    if node.get("node_type") == "light":
        lights.append(node)

    children = node.get("children", [])
    if children is None:
        children = []

    for child in children:
        if child is not None:
            collect_lights(child, lights)

def build_light_setup_code(active_light):
    if active_light is None:
        return """
activeLightPos = util.vec(2.0, 5.5, 2.0)
activeLightColor = util.vec(1.0, 1.0, 1.0)
activeLightIntensity = 0.8
"""


    props = active_light["properties"]
    color = props["color"]
    intensity = props["intensity"]

    color_expr = "util.vec({}, {}, {})".format(
        float(color[0]), float(color[1]), float(color[2])
    )

    if active_light["light_type"] == "point":
        pos = props["position"]
        pos_expr = "util.vec({}, {}, {})".format(
            float(pos[0]), float(pos[1]), float(pos[2])
        )

        return """
activeLightPos = {pos_expr}
activeLightColor = {color_expr}
activeLightIntensity = {intensity}
""".format(
            pos_expr=pos_expr,
            color_expr=color_expr,
            intensity=float(intensity)
        )

    elif active_light["light_type"] == "directional":
        direction = props["direction"]

        # Μετατρέπουμε direction -> pseudo-position μακριά από τη σκηνή
        pseudo_pos = [
            -10.0 * float(direction[0]),
            -10.0 * float(direction[1]),
            -10.0 * float(direction[2])
        ]

        pseudo_pos_expr = "util.vec({}, {}, {})".format(
            pseudo_pos[0], pseudo_pos[1], pseudo_pos[2]
        )

        return """
activeLightPos = {pseudo_pos_expr}
activeLightColor = {color_expr}
activeLightIntensity = {intensity}
""".format(
            pseudo_pos_expr=pseudo_pos_expr,
            color_expr=color_expr,
            intensity=float(intensity)
        )

    return """
activeLightPos = util.vec(2.0, 5.5, 2.0)
activeLightColor = util.vec(1.0, 1.0, 1.0)
activeLightIntensity = 0.8
"""
# -----------------------------
# Code generation helpers
# -----------------------------
def make_translate(position):
    x, y, z = position
    return "util.translate({}, {}, {})".format(float(x), float(y), float(z))


def make_scale(scale):
    sx, sy, sz = scale

    if sx == sy == sz:
        return "util.scale({})".format(float(sx))

    return (
        "np.array([[{sx}, 0.0, 0.0, 0.0], "
        "[0.0, {sy}, 0.0, 0.0], "
        "[0.0, 0.0, {sz}, 0.0], "
        "[0.0, 0.0, 0.0, 1.0]], dtype=np.float32)"
    ).format(
        sx=float(sx),
        sy=float(sy),
        sz=float(sz)
    )


def vec3_to_util_vec(v):
    return "util.vec({}, {}, {})".format(float(v[0]), float(v[1]), float(v[2]))


def ndarray_to_python(np_array, dtype_name):
    return "np.array({}, dtype=np.{})".format(np_array.tolist(), dtype_name)


def emit_geometry_data(shape, material, transform, suffix):
    params = {
        "color": material["color"],
        "scale": transform.get("scale", [1.0, 1.0, 1.0])
    }

    raw_vertices, raw_indices, raw_colors, raw_normals = build_render_mesh(shape, params)

    vertices_code = ndarray_to_python(raw_vertices, "float32")
    indices_code = ndarray_to_python(raw_indices, "uint32")
    colors_code = ndarray_to_python(raw_colors, "float32")
    normals_code = ndarray_to_python(raw_normals, "float32")

    return """
vertices_{suffix} = {vertices_code}
indices_{suffix} = {indices_code}
colors_{suffix} = {colors_code}
normals_{suffix} = {normals_code}
""".format(
        suffix=suffix,
        vertices_code=vertices_code,
        indices_code=indices_code,
        colors_code=colors_code,
        normals_code=normals_code
    )


def build_header(window, light_setup_code):
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
from Elements.pyGLV.GL.Textures import Texture 
import Elements.utils.normals as norm

from Elements.utils.terrain import generateTerrain
from Elements.definitions import TEXTURE_DIR

from Elements.utils.Shortcuts import displayGUI_text

import OpenGL.GL as gl
import Elements.utils.normals as norm

TEXTURE_VERTEX_SHADER = """
#version 410
layout (location=0) in vec4 vPos;
layout (location=1) in vec2 vTexCoord;

out vec2 fragmentTexCoord;

uniform mat4 model;
uniform mat4 view;
uniform mat4 proj;

void main()
{{
    gl_Position = proj * view * model * vPos;
    fragmentTexCoord = vTexCoord;
}}
"""
TEXTURE_FRAGMENT_SHADER = """
#version 410
out vec4 outputColor;
in vec2 fragmentTexCoord;
uniform sampler2D texSampler;

void main()
{{
    outputColor = texture(texSampler, fragmentTexCoord);
}}
"""
example_description = "Generated scene from hierarchical IR"

# Ambient / view defaults
Lambientcolor = util.vec(1.0, 1.0, 1.0)
Lambientstr = 0.3
LviewPos = util.vec(2.5, 2.8, 5.0)

# Material
Mshininess = 0.4

# Active light
{light_setup_code}

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
'''.format(
        width=width,
        height=height,
        light_setup_code=light_setup_code
    )

def build_footer(title, uniform_block, texture_set_up_block):
    indented_uniforms = "\n".join(
        ("    " + line) if line.strip() else line
        for line in uniform_block.splitlines()
    )

    footer_template = r'''
import imgui
import json
import time
from pathlib import Path

SHARED_DIR = Path.home() / "Desktop" / "scene_bridge"
SHARED_DIR.mkdir(parents=True, exist_ok=True)

AI_REQUEST_FILE = SHARED_DIR / "ai_request.json"
UI_STATE_FILE = SHARED_DIR / "ui_state.json"
SCENE_STATE_FILE = SHARED_DIR / "scene_state.json"

command_text = ""
status_message = "Ready for input."
show_editor_panel = True
request_counter = 0
current_request_id = None
current_mode = "official"
current_active_script = ""


def read_json_file(path):
    try:
        if not path.exists():
            return None
        with open(str(path), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def write_json_file(path, data):
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(str(tmp_path), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp_path.replace(path)


def load_bridge_state():
    global request_counter
    global current_request_id
    global current_mode
    global current_active_script

    req = read_json_file(AI_REQUEST_FILE)
    if isinstance(req, dict):
        try:
            req_id = int(req.get("request_id", 0))
            if req_id > 0:
                request_counter = max(request_counter, req_id)
                current_request_id = req_id
        except Exception:
            pass

    scene_state = read_json_file(SCENE_STATE_FILE)
    if isinstance(scene_state, dict):
        current_mode = str(scene_state.get("mode", "official"))
        current_active_script = str(scene_state.get("active_script", ""))


def poll_backend_state():
    global status_message
    global request_counter
    global current_request_id
    global current_mode
    global current_active_script

    req = read_json_file(AI_REQUEST_FILE)
    ui = read_json_file(UI_STATE_FILE)
    scene_state = read_json_file(SCENE_STATE_FILE)

    if isinstance(scene_state, dict):
        current_mode = str(scene_state.get("mode", "official"))
        current_active_script = str(scene_state.get("active_script", ""))

    if isinstance(req, dict):
        try:
            req_id = int(req.get("request_id", 0))
            if req_id > 0:
                request_counter = max(request_counter, req_id)
                current_request_id = req_id
        except Exception:
            pass

        req_status = req.get("status")

        if req_status == "pending":
            status_message = "Request sent. Waiting for preview."
        elif req_status == "preview_ready":
            status_message = "Preview ready."
        elif req_status == "applied":
            status_message = "Applied."
        elif req_status == "rejected":
            status_message = "Rejected."
        elif req_status == "undone":
            status_message = "Undo restored previous scene."
        elif req_status == "new_scene_created":
            status_message = "New scene created."
        elif req_status == "scene_saved":
            status_message = str(req.get("message", "Scene saved."))
        elif req_status == "save_blocked_preview":
            status_message = "Save blocked. Apply or Reject preview first."
        elif req_status == "stale":
            status_message = "Previous stale request was cleared."
        elif req_status == "error":
            status_message = "Error: " + str(req.get("error", "unknown error"))

    if isinstance(ui, dict) and ui.get("action") == "error":
        status_message = "Controller error: " + str(ui.get("message", "unknown"))


def write_ai_request(prompt_text):
    global request_counter
    global current_request_id

    load_bridge_state()
    request_counter += 1
    current_request_id = request_counter

    data = {
        "request_id": request_counter,
        "status": "pending",
        "prompt": prompt_text,
        "created_at": time.time()
    }

    write_json_file(AI_REQUEST_FILE, data)
    return request_counter


def write_ui_action(action_name):
    data = {
        "action": action_name,
        "created_at": time.time()
    }

    if current_request_id is not None:
        data["request_id"] = current_request_id

    write_json_file(UI_STATE_FILE, data)


def display_active_script():
    if not current_active_script:
        return "(unknown)"

    try:
        return Path(current_active_script).name
    except Exception:
        return current_active_script


def draw_editor_panel():
    global command_text
    global status_message
    global show_editor_panel

    if not show_editor_panel:
        return

    imgui.begin("Scene Editor", True)

    imgui.text("Mode: " + str(current_mode))
    imgui.text("Request ID: " + (str(current_request_id) if current_request_id is not None else "(none)"))
    imgui.text_wrapped("Active script: " + display_active_script())

    imgui.spacing()
    imgui.separator()
    imgui.spacing()

    imgui.text("Command:")
    changed, command_text = imgui.input_text_multiline(
        "##scene_command",
        command_text,
        1024,
        width=420,
        height=100
    )

    imgui.spacing()

    if imgui.button("Send to AI", width=120):
        if command_text.strip():
            try:
                req_id = write_ai_request(command_text)
                status_message = "Request sent. request_id = " + str(req_id)
            except Exception as e:
                status_message = "Failed to send request: " + str(e)
        else:
            status_message = "Please type a command first."

    imgui.same_line()

    if imgui.button("Apply", width=80):
        try:
            write_ui_action("apply")
            status_message = "Apply sent."
        except Exception as e:
            status_message = "Apply failed: " + str(e)

    imgui.same_line()

    if imgui.button("Reject", width=80):
        try:
            write_ui_action("reject")
            status_message = "Reject sent."
        except Exception as e:
            status_message = "Reject failed: " + str(e)

    imgui.same_line()

    if imgui.button("Undo", width=80):
        try:
            write_ui_action("undo")
            status_message = "Undo sent."
        except Exception as e:
            status_message = "Undo failed: " + str(e)

    imgui.spacing()

    if imgui.button("New Scene", width=120):
        try:
            write_ui_action("new_scene")
            status_message = "New scene requested."
        except Exception as e:
            status_message = "New scene failed: " + str(e)

    imgui.same_line()

    if imgui.button("Save", width=80):
        try:
            write_ui_action("save_scene")
            status_message = "Save requested."
        except Exception as e:
            status_message = "Save failed: " + str(e)

    imgui.spacing()
    imgui.separator()
    imgui.text("Status:")
    imgui.text_wrapped(status_message)

    imgui.end()


running = True
load_bridge_state()

scene.init(
    imgui=True,
    windowWidth=winWidth,
    windowHeight=winHeight,
    windowTitle=__WINDOW_TITLE_LITERAL__,
    openGLversion=4,
    customImGUIdecorator=ImGUIecssDecorator2
)

scene.world.traverse_visit(initUpdate, scene.world.root)
__POST_INIT_BLOCK__

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
__UNIFORMS__
    poll_backend_state()
    draw_editor_panel()
    scene.render_post()

scene.shutdown()
'''

    return (
        footer_template
        .replace("__WINDOW_TITLE_LITERAL__", json.dumps(title))
        .replace("__POST_INIT_BLOCK__", texture_set_up_block)
        .replace("__UNIFORMS__", indented_uniforms)
    )

# -----------------------------
# Recursive node emission
# -----------------------------
def emit_mesh_object_node(node, idx, parent_entity_var, parent_trs_expr):
    name = node["name"]
    shape = node["shape"]
    transform = node["transform"]
    material = node["material"]

    if is_textured_material(material):
        return emit_textured_mesh_object_node(node, idx, parent_entity_var, parent_trs_expr)    

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
{shader_var}.setUniformVariable(key='lightPos', value=activeLightPos, float3=True)
{shader_var}.setUniformVariable(key='lightColor', value=activeLightColor, float3=True)
{shader_var}.setUniformVariable(key='lightIntensity', value=activeLightIntensity, float1=True)
{shader_var}.setUniformVariable(key='shininess', value=Mshininess, float1=True)
{shader_var}.setUniformVariable(key='matColor', value={mat_color_expr}, float3=True)
""".format(
        suffix=suffix,
        shader_var=shader_var,
        world_trs_expr=world_trs_expr,
        mat_color_expr=mat_color_expr
    )

    return object_code, uniform_code, ""

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

    trs_expr = make_translate(position)
    local_trs_expr = make_translate(position)
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
    child_post_init_blocks = []

    for child in node.get("children", []):
        child_obj_code, child_uniform_code, child_post_init_code = emit_node(child, entity_var, world_trs_expr, state)
        child_object_blocks.append(child_obj_code)
        child_uniform_blocks.append(child_uniform_code)
        child_post_init_blocks.append(child_post_init_code)


    full_object_code = object_code + "\n" + "\n".join(child_object_blocks)
    full_uniform_code = "\n".join(child_uniform_blocks)
    full_post_init_code = "\n".join(child_post_init_blocks)

    return full_object_code, full_uniform_code, full_post_init_code


def emit_node(node, parent_entity_var, parent_trs_expr, state):
    if node is None:
        # Decide if you want to return empty strings or raise a clearer error
        return "", "", ""
    node_type = node.get("node_type")

    if node_type == "scene":
        object_blocks = []
        uniform_blocks = []
        post_init_blocks = []

        for child in node.get("children", []):
            child_obj_code, child_uniform_code, child_post_init_code = emit_node(
                child,
                "rootEntity",
                "util.identity()",
                state
            )
            object_blocks.append(child_obj_code)
            uniform_blocks.append(child_uniform_code)
            post_init_blocks.append(child_post_init_code)

        return "\n".join(object_blocks), "\n".join(uniform_blocks), "\n".join(post_init_blocks)
    elif node_type == "group":
        state["counter"] += 1
        return emit_group_node(node, state["counter"], parent_entity_var, parent_trs_expr, state)

    elif node_type == "mesh_object":
        state["counter"] += 1
        return emit_mesh_object_node(node, state["counter"], parent_entity_var, parent_trs_expr)
    elif node_type == "light":
        
        return "", "", ""
        
    else:
        raise ValueError("Unsupported node_type: {}".format(node_type))

def emit_textured_mesh_object_node(node, idx, parent_entity_var, parent_trs_expr):
    name = node["name"]
    shape = node["shape"]
    transform = node["transform"]
    material = node["material"]

    position = transform["position"]
    texture_path = (material.get("texture") or {}).get("path")
    if not texture_path:
        raise ValueError("Textured material is missing texture.path")
    suffix = str(idx)

    entity_var = "node_{}".format(suffix)
    trans_var = "trans_{}".format(suffix)
    mesh_var = "mesh_{}".format(suffix)
    shader_var = "shader_{}".format(suffix)
    texture_var = "texture_{}".format(suffix)

    local_trs_expr = "{} ".format( make_translate(position))
    world_trs_expr = "{} @ ({})".format(parent_trs_expr, local_trs_expr)
    if shape != "cube":
        raise ValueError("Currently only 'cube' shape is supported for textured mesh_object nodes")
    
    raw_vertices, raw_indices, raw_uvs = create_textured_cube()
    vertices_code = ndarray_to_python(raw_vertices, "float32")
    indices_code = ndarray_to_python(raw_indices, "uint32")
    uv_code = ndarray_to_python(raw_uvs, "float32")

    object_code = f"""
# ===== textured mesh_object: {name} =====
vertices_{suffix} = {vertices_code}
indices_{suffix} = {indices_code}
uv_{suffix} = {uv_code}

{entity_var} = scene.world.createEntity(Entity(name="{name}"))
scene.world.addEntityChild({parent_entity_var}, {entity_var})

{trans_var} = scene.world.addComponent(
    {entity_var},
    BasicTransform(name="{name}_TRS", trs={local_trs_expr})
)
{mesh_var} = scene.world.addComponent({entity_var}, RenderMesh(name="{name}_mesh"))
{mesh_var}.vertex_attributes.append(vertices_{suffix})
{mesh_var}.vertex_attributes.append(uv_{suffix})
{mesh_var}.vertex_index.append(indices_{suffix})

scene.world.addComponent({entity_var}, VertexArray())
{shader_var} = scene.world.addComponent(
    {entity_var},
    ShaderGLDecorator(
        Shader(
            vertex_source=TEXTURE_VERTEX_SHADER,
            fragment_source=TEXTURE_FRAGMENT_SHADER
        )
    )
)
""" 

    uniform_code = f"""
model_{suffix} = {world_trs_expr}
{shader_var}.setUniformVariable(key='model', value=model_{suffix}, mat4=True)
{shader_var}.setUniformVariable(key='view', value=view, mat4=True)
{shader_var}.setUniformVariable(key='proj', value=projMat, mat4=True)
"""
    texture_set_up_code = f"""
{texture_var} = Texture(r"{texture_path}")
{shader_var}.setUniformVariable(key='texSampler', value={texture_var}, texture=True)
"""
    
    return object_code, uniform_code, texture_set_up_code

def check_ir_textures(node):
    if not isinstance(node, dict):
        return

    if node.get("node_type") == "mesh_object":
        material = node.setdefault("material", {})
        texture = material.setdefault("texture", {})
        texture.setdefault("enabled", False)
        texture.setdefault("path", None)

    for child in node.get("children", []):
        check_ir_textures(child)
# -----------------------------
# Main public API
# -----------------------------
def generate_scene_script(scene_ir):
    scene_ir = deepcopy(scene_ir)
    check_ir_textures(scene_ir)
    scene_ir = validate_and_normalize_scene_ir(scene_ir)

    window = scene_ir["window"]
    title = window["title"]


    ## LIGHTS 
    lights = []
    collect_lights(scene_ir, lights)

    active_light = lights[0] if len(lights) > 0 else None

    light_setup_code = build_light_setup_code(active_light)
    #end lights
    header = build_header(window, light_setup_code)

    state = {"counter": 0}
    object_code, uniform_code, post_init_code = emit_node(scene_ir, "rootEntity", "util.identity()", state)

    footer = build_footer(title, uniform_code, post_init_code)

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

