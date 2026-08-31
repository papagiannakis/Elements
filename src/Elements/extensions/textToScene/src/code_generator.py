# code_generator.py
import json
import os
import re
import zipfile
from copy import deepcopy
from pathlib import Path
from typing import Optional

import numpy as np

from Elements.extensions.Shapes.geometry_factory import build_render_mesh, create_textured_cube, create_textured_mesh

_SRC_DIR       = Path(os.path.abspath(os.path.dirname(__file__)))
_EXTENSION_DIR = _SRC_DIR.parent
_OUTPUT_DIR    = _SRC_DIR


DEFAULT_WINDOW = {
    "width": 1200,
    "height": 800,
    "title": "Generated Scene"
}

DEFAULT_TRANSFORM = {
    "position": [0.0, 0.5, 0.0],
    "rotation": [0.0, 0.0, 0.0],
    "scale": [1.0, 1.0, 1.0]
}

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
    if "rotation" in transform:
        normalized["rotation"] = ensure_vec3(transform["rotation"], "rotation")
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

        normalized = {
            "node_type": "mesh_object",
            "name": str(node.get("name", "mesh_object_{}".format(idx))),
            "shape": shape,
            "transform": normalize_transform(node.get("transform", {})),
            "material": normalize_material(node.get("material", {}))
        }

        if shape == "custom":
            custom_path = node.get("custom_model_path")
            if not custom_path:
                raise ValueError("mesh_object with shape='custom' requires 'custom_model_path'")
            normalized["custom_model_path"] = str(custom_path)

        if "orbit" in node:
            normalized["orbit"] = node["orbit"]
        if "animation" in node:
            normalized["animation"] = node["animation"]

        return normalized
    
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

        result = {
            "node_type": "light",
            "name": str(node.get("name", "light_{}".format(idx))),
            "light_type": light_type,
            "properties": props
        }

        if "orbit" in node:
            result["orbit"] = node["orbit"]

        return result

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


def make_rotate(rotation):
    rx, ry, rz = rotation

    if rx == ry == rz == 0.0:
        return "util.identity()"

    return "util.eulerAnglesToRotationMatrix(np.radians([{}, {}, {}]))".format(
        float(rx),
        float(ry),
        float(rz)
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

    _elements_root = str(Path(__file__).resolve().parent.parent.parent.parent.parent)
    _path_fix = (
        'import sys as _sys\n'
        '_elements_root = r"{}"\n'
        'if _elements_root not in _sys.path:\n'
        '    _sys.path.insert(0, _elements_root)\n\n'
    ).format(_elements_root)

    return _path_fix + '''import numpy as np

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
from Elements.definitions import TEXTURE_DIR, SHADER_DIR

from Elements.utils.Shortcuts import displayGUI_text

import OpenGL.GL as gl

TEXTURE_VERTEX_SHADER = (SHADER_DIR / "TextToSceneTexture.vert").read_text()
TEXTURE_FRAGMENT_SHADER = (SHADER_DIR / "TextToSceneTexture.frag").read_text()
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

SHARED_DIR = Path(__SHARED_DIR_LITERAL__)
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
        .replace("__SHARED_DIR_LITERAL__", repr(str(_SRC_DIR / "scene_bridge")))
    )

# -----------------------------
# OBJ loader (generation-time)
# -----------------------------
def _parse_obj_for_codegen(obj_path, color_rgb):
    """Parse a Wavefront .obj file and return numpy arrays ready for the renderer.

    Returns (vertices, indices, normals, colors) as numpy arrays.
    Supports triangulated meshes only; quads are split into two triangles.
    Normals are computed per-face (flat shading) if not provided in the file.
    """
    positions = []   # list of [x, y, z]
    face_indices = []  # list of [i0, i1, i2] (0-based)
    obj_normals = {}   # vertex-index -> accumulated normal

    with open(str(obj_path), "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if parts[0] == "v":
                positions.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif parts[0] == "f":
                # Each token is v or v/vt or v/vt/vn  (1-based)
                verts = [int(tok.split("/")[0]) - 1 for tok in parts[1:]]
                # Fan-triangulate
                for k in range(1, len(verts) - 1):
                    face_indices.append([verts[0], verts[k], verts[k + 1]])


def _parse_obj_with_uvs(obj_path):
    """Parse OBJ with UV (vt) coordinates.

    OBJ faces can have different position/UV indices (v/vt or v/vt/vn).
    We expand to a unique-(position, uv) vertex list so that each rendered
    vertex carries both its position and its texture coordinate.

    Returns (vertices, indices, uvs) as float32/uint32 numpy arrays.
    If the file has no vt lines the UVs default to (0, 0).
    """
    positions = []
    uvs_raw = []

    unique_verts = {}   # (pos_idx, uv_idx) -> new flat index
    out_positions = []
    out_uvs = []
    out_tris = []

    with open(str(obj_path), "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if parts[0] == "v":
                positions.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif parts[0] == "vt":
                uvs_raw.append([float(parts[1]), float(parts[2])])
            elif parts[0] == "f":
                face_verts = []
                for tok in parts[1:]:
                    components = tok.split("/")
                    pos_idx = int(components[0]) - 1
                    if len(components) > 1 and components[1]:
                        uv_idx = int(components[1]) - 1
                    else:
                        uv_idx = 0
                    key = (pos_idx, uv_idx)
                    if key not in unique_verts:
                        unique_verts[key] = len(out_positions)
                        out_positions.append(positions[pos_idx])
                        out_uvs.append(uvs_raw[uv_idx] if uvs_raw else [0.0, 0.0])
                    face_verts.append(unique_verts[key])
                for k in range(1, len(face_verts) - 1):
                    out_tris.append([face_verts[0], face_verts[k], face_verts[k + 1]])

    if not out_positions:
        raise ValueError("OBJ file has no vertices: {}".format(obj_path))
    if not out_tris:
        raise ValueError("OBJ file has no faces: {}".format(obj_path))

    verts_array   = np.array([[p[0], p[1], p[2], 1.0] for p in out_positions], dtype=np.float32)
    uvs_array     = np.array(out_uvs, dtype=np.float32)
    indices_array = np.array(out_tris, dtype=np.uint32)
    return verts_array, indices_array, uvs_array

    if not positions:
        raise ValueError("OBJ file has no vertex positions: {}".format(obj_path))
    if not face_indices:
        raise ValueError("OBJ file has no faces: {}".format(obj_path))

    n_verts = len(positions)
    smooth_normals = [[0.0, 0.0, 0.0] for _ in range(n_verts)]

    for tri in face_indices:
        i0, i1, i2 = tri
        p0, p1, p2 = positions[i0], positions[i1], positions[i2]
        # Edge vectors
        e1 = [p1[k] - p0[k] for k in range(3)]
        e2 = [p2[k] - p0[k] for k in range(3)]
        # Cross product
        nx = e1[1]*e2[2] - e1[2]*e2[1]
        ny = e1[2]*e2[0] - e1[0]*e2[2]
        nz = e1[0]*e2[1] - e1[1]*e2[0]
        for vi in (i0, i1, i2):
            smooth_normals[vi][0] += nx
            smooth_normals[vi][1] += ny
            smooth_normals[vi][2] += nz

    # Normalize
    for i, n in enumerate(smooth_normals):
        length = (n[0]**2 + n[1]**2 + n[2]**2) ** 0.5
        if length > 1e-8:
            smooth_normals[i] = [n[k] / length for k in range(3)]
        else:
            smooth_normals[i] = [0.0, 1.0, 0.0]

    r, g, b = float(color_rgb[0]), float(color_rgb[1]), float(color_rgb[2])

    verts_array   = np.array([[p[0], p[1], p[2], 1.0] for p in positions],  dtype=np.float32)
    normals_array = np.array([[n[0], n[1], n[2]]       for n in smooth_normals], dtype=np.float32)
    colors_array  = np.array([[r, g, b, 1.0]            for _ in positions],  dtype=np.float32)
    indices_array = np.array(face_indices, dtype=np.uint32)

    return verts_array, indices_array, normals_array, colors_array


# -----------------------------
# USD loader (generation-time)
# -----------------------------
def _parse_usda_text(usda_path, color_rgb):
    """Parse a USDA (text-format USD) file without requiring the pxr library.

    Extracts the first Mesh prim's points, faceVertexCounts, and
    faceVertexIndices, triangulates, computes smooth normals, and returns
    (vertices, indices, normals, colors) as numpy arrays.
    """
    import re as _re

    text = Path(str(usda_path)).read_text(encoding="utf-8")

    # Match 'point3f[] points = [...]' or 'float3[] points = [...]'
    points_match = _re.search(
        r'(?:point3f|float3|Vec3f)\[\]\s+points\s*=\s*\[(.*?)\]',
        text, _re.DOTALL | _re.IGNORECASE
    )
    if not points_match:
        raise ValueError("No 'points' array found in USDA file: {}".format(usda_path))

    positions = []
    for m in _re.finditer(
        r'\(?\s*(-?\d+\.?\d*(?:e[+-]?\d+)?)\s*,\s*(-?\d+\.?\d*(?:e[+-]?\d+)?)\s*,\s*(-?\d+\.?\d*(?:e[+-]?\d+)?)\s*\)?',
        points_match.group(1)
    ):
        positions.append([float(m.group(1)), float(m.group(2)), float(m.group(3))])

    if not positions:
        raise ValueError("Could not parse vertex positions from USDA file: {}".format(usda_path))

    indices_match = _re.search(
        r'int\[\]\s+faceVertexIndices\s*=\s*\[(.*?)\]', text, _re.DOTALL
    )
    if not indices_match:
        raise ValueError("No 'faceVertexIndices' found in USDA file: {}".format(usda_path))
    raw_indices = [int(x) for x in _re.findall(r'-?\d+', indices_match.group(1))]

    counts_match = _re.search(
        r'int\[\]\s+faceVertexCounts\s*=\s*\[(.*?)\]', text, _re.DOTALL
    )
    if not counts_match:
        raise ValueError("No 'faceVertexCounts' found in USDA file: {}".format(usda_path))
    counts = [int(x) for x in _re.findall(r'\d+', counts_match.group(1))]

    face_indices = []
    offset = 0
    for count in counts:
        verts = raw_indices[offset:offset + count]
        for k in range(1, len(verts) - 1):
            face_indices.append([verts[0], verts[k], verts[k + 1]])
        offset += count

    if not face_indices:
        raise ValueError("No faces found in USDA file: {}".format(usda_path))

    return _build_mesh_arrays(positions, face_indices, color_rgb)


def _parse_usda_with_uvs(usda_path):
    """Parse USDA with primvars:st UV coordinates.

    Handles both indexed (primvars:st:indices) and non-indexed UV layouts.
    Expands to unique-(position, uv) vertices, same as the OBJ UV parser.

    Returns (vertices, indices, uvs) as float32/uint32 numpy arrays.
    """
    import re as _re

    text = Path(str(usda_path)).read_text(encoding="utf-8")

    # Positions
    points_match = _re.search(
        r'(?:point3f|float3|Vec3f)\[\]\s+points\s*=\s*\[(.*?)\]',
        text, _re.DOTALL | _re.IGNORECASE
    )
    if not points_match:
        raise ValueError("No 'points' found in USDA: {}".format(usda_path))
    positions = []
    for m in _re.finditer(
        r'\(?\s*(-?\d+\.?\d*(?:e[+-]?\d+)?)\s*,\s*(-?\d+\.?\d*(?:e[+-]?\d+)?)\s*,\s*(-?\d+\.?\d*(?:e[+-]?\d+)?)\s*\)?',
        points_match.group(1)
    ):
        positions.append([float(m.group(1)), float(m.group(2)), float(m.group(3))])

    # Face topology
    indices_match = _re.search(r'int\[\]\s+faceVertexIndices\s*=\s*\[(.*?)\]', text, _re.DOTALL)
    counts_match  = _re.search(r'int\[\]\s+faceVertexCounts\s*=\s*\[(.*?)\]',  text, _re.DOTALL)
    if not indices_match or not counts_match:
        raise ValueError("No face data found in USDA: {}".format(usda_path))
    pos_face_verts = [int(x) for x in _re.findall(r'-?\d+', indices_match.group(1))]
    counts         = [int(x) for x in _re.findall(r'\d+',   counts_match.group(1))]

    # UVs — try texCoord2f / float2 primvars:st
    uv_match = _re.search(
        r'(?:texCoord2f|float2)\[\]\s+primvars:st\s*=\s*\[(.*?)\]',
        text, _re.DOTALL | _re.IGNORECASE
    )
    uvs_raw = []
    if uv_match:
        for m in _re.finditer(
            r'\(?\s*(-?\d+\.?\d*(?:e[+-]?\d+)?)\s*,\s*(-?\d+\.?\d*(?:e[+-]?\d+)?)\s*\)?',
            uv_match.group(1)
        ):
            uvs_raw.append([float(m.group(1)), float(m.group(2))])

    # UV indices (per-face-vertex, same count as pos_face_verts)
    uv_idx_match = _re.search(r'int\[\]\s+primvars:st:indices\s*=\s*\[(.*?)\]', text, _re.DOTALL)
    if uv_idx_match and uvs_raw:
        uv_face_indices = [int(x) for x in _re.findall(r'-?\d+', uv_idx_match.group(1))]
    elif uvs_raw:
        # Non-indexed: UVs are in face-vertex order directly
        uv_face_indices = list(range(len(pos_face_verts)))
    else:
        uv_face_indices = []

    # Expand to unique (pos_idx, uv_idx) vertices
    unique_verts = {}
    out_positions = []
    out_uvs = []
    out_tris = []

    offset = 0
    for count in counts:
        face_pos  = pos_face_verts[offset:offset + count]
        face_uvidx = uv_face_indices[offset:offset + count] if uv_face_indices else [0] * count
        face_new = []
        for j in range(count):
            pi = face_pos[j]
            ui = face_uvidx[j] if uvs_raw else 0
            key = (pi, ui)
            if key not in unique_verts:
                unique_verts[key] = len(out_positions)
                out_positions.append(positions[pi])
                out_uvs.append(uvs_raw[ui] if uvs_raw else [0.0, 0.0])
            face_new.append(unique_verts[key])
        for k in range(1, len(face_new) - 1):
            out_tris.append([face_new[0], face_new[k], face_new[k + 1]])
        offset += count

    if not out_tris:
        raise ValueError("No faces found in USDA: {}".format(usda_path))

    verts_array   = np.array([[p[0], p[1], p[2], 1.0] for p in out_positions], dtype=np.float32)
    uvs_array     = np.array(out_uvs, dtype=np.float32)
    indices_array = np.array(out_tris, dtype=np.uint32)
    return verts_array, indices_array, uvs_array


def _parse_usd_with_pxr(usd_path, color_rgb):
    """Parse any USD/USDZ format using the pxr library.

    Collects ALL Mesh prims, applies their world transforms, converts to
    meters (metersPerUnit), then normalises the whole model to fit inside
    a 2-unit bounding box so it appears at a sane scale in the scene.
    """
    from pxr import Usd, UsdGeom, Gf  # noqa: PLC0415

    stage = Usd.Stage.Open(str(usd_path))

    # USD may store geometry in centimeters (0.01) or other units.
    meters_per_unit = UsdGeom.GetStageMetersPerUnit(stage)
    if not meters_per_unit or meters_per_unit <= 0:
        meters_per_unit = 0.01  # USD default: centimeters

    all_positions = []
    all_faces = []
    vertex_offset = 0
    time_code = Usd.TimeCode.Default()

    for prim in stage.Traverse():
        if prim.GetTypeName() != "Mesh":
            continue

        mesh = UsdGeom.Mesh(prim)
        pts        = mesh.GetPointsAttr().Get(time_code)
        face_cnts  = mesh.GetFaceVertexCountsAttr().Get(time_code)
        face_idx   = mesh.GetFaceVertexIndicesAttr().Get(time_code)

        if pts is None or face_cnts is None or face_idx is None:
            continue

        # World transform: local → world, then apply unit scale
        try:
            xform_cache = UsdGeom.XformCache(time_code)
            world_xform = xform_cache.GetLocalToWorldTransform(prim)
        except Exception:
            world_xform = Gf.Matrix4d(1.0)

        for p in pts:
            wp = world_xform.Transform(Gf.Vec3d(p[0], p[1], p[2]))
            all_positions.append([
                float(wp[0]) * meters_per_unit,
                float(wp[1]) * meters_per_unit,
                float(wp[2]) * meters_per_unit,
            ])

        raw = list(face_idx)
        off = 0
        for cnt in face_cnts:
            verts = [raw[off + k] + vertex_offset for k in range(cnt)]
            for k in range(1, len(verts) - 1):
                all_faces.append([verts[0], verts[k], verts[k + 1]])
            off += cnt

        vertex_offset += len(pts)

    if not all_positions:
        raise ValueError("No Mesh geometry found in USD file: {}".format(usd_path))
    if not all_faces:
        raise ValueError("No faces found in USD file: {}".format(usd_path))

    # Normalise: centre on XZ, sit on Y=0, scale to 2-unit bounding box
    all_positions = _normalize_positions(all_positions)

    return _build_mesh_arrays(all_positions, all_faces, color_rgb)


def _parse_usd_with_uvs_pxr(usd_path):
    """Parse USD/USDZ with texture UVs using the pxr library.

    Looks for the 'st' primvar on each Mesh prim.
    Expands to unique-(position, uv) vertices.

    Returns (vertices, indices, uvs) as float32/uint32 numpy arrays.
    Falls back to (0,0) UVs if no 'st' primvar is found.
    """
    from pxr import Usd, UsdGeom, Gf  # noqa: PLC0415

    stage        = Usd.Stage.Open(str(usd_path))
    mpu          = UsdGeom.GetStageMetersPerUnit(stage) or 0.01
    time_code    = Usd.TimeCode.Default()

    unique_verts  = {}
    out_positions = []
    out_uvs       = []
    out_tris      = []

    for prim in stage.Traverse():
        if prim.GetTypeName() != "Mesh":
            continue

        mesh      = UsdGeom.Mesh(prim)
        pts       = mesh.GetPointsAttr().Get(time_code)
        face_cnts = mesh.GetFaceVertexCountsAttr().Get(time_code)
        face_idx  = mesh.GetFaceVertexIndicesAttr().Get(time_code)
        if pts is None or face_cnts is None or face_idx is None:
            continue

        try:
            xform_cache = UsdGeom.XformCache(time_code)
            world_xform = xform_cache.GetLocalToWorldTransform(prim)
        except Exception:
            world_xform = Gf.Matrix4d(1.0)

        # World-space positions for this prim
        prim_positions = []
        for p in pts:
            wp = world_xform.Transform(Gf.Vec3d(p[0], p[1], p[2]))
            prim_positions.append([
                float(wp[0]) * mpu, float(wp[1]) * mpu, float(wp[2]) * mpu
            ])

        # UV primvar
        st_pv   = UsdGeom.PrimvarsAPI(mesh).GetPrimvar("st")
        uvs_raw = []
        uv_idxs = []
        if st_pv and st_pv.HasValue():
            uvs_raw = [[float(u), float(v)] for u, v in st_pv.Get(time_code)]
            raw_idx = st_pv.GetIndices(time_code)
            uv_idxs = list(raw_idx) if raw_idx is not None else list(range(len(face_idx)))

        pos_idx_list = list(face_idx)
        offset = 0
        for cnt in face_cnts:
            face_new = []
            for j in range(cnt):
                pi = pos_idx_list[offset + j]
                ui = uv_idxs[offset + j] if uv_idxs else 0
                key = (id(prim), pi, ui)
                if key not in unique_verts:
                    unique_verts[key] = len(out_positions)
                    out_positions.append(prim_positions[pi])
                    out_uvs.append(uvs_raw[ui] if uvs_raw else [0.0, 0.0])
                face_new.append(unique_verts[key])
            for k in range(1, len(face_new) - 1):
                out_tris.append([face_new[0], face_new[k], face_new[k + 1]])
            offset += cnt

    if not out_positions:
        raise ValueError("No Mesh geometry found in USD file: {}".format(usd_path))
    if not out_tris:
        raise ValueError("No faces found in USD file: {}".format(usd_path))

    out_positions = _normalize_positions(out_positions)
    verts_array   = np.array([[p[0], p[1], p[2], 1.0] for p in out_positions], dtype=np.float32)
    uvs_array     = np.array(out_uvs, dtype=np.float32)
    indices_array = np.array(out_tris, dtype=np.uint32)
    return verts_array, indices_array, uvs_array


def _generate_procedural_uvs(verts_array):
    """Cylindrical UV mapping fallback when a model has no embedded UVs.

    u = angle around Y axis normalised to [0, 1]
    v = height normalised to [0, 1]

    Works well for rounded / organic shapes (teapot, vase, character).
    For flat/boxy objects consider box-mapping, but cylindrical is a safe default.
    """
    import math
    xs = verts_array[:, 0]
    ys = verts_array[:, 1]
    zs = verts_array[:, 2]

    ymin, ymax = float(ys.min()), float(ys.max())
    y_span = ymax - ymin if (ymax - ymin) > 1e-6 else 1.0

    uvs = []
    for x, y, z in zip(xs, ys, zs):
        u = (math.atan2(float(z), float(x)) + math.pi) / (2 * math.pi)
        v = (float(y) - ymin) / y_span
        uvs.append([u, v])
    return np.array(uvs, dtype=np.float32)


def _uvs_are_trivial(uvs_array):
    """Return True if every UV is (0,0) — i.e. no real UV data was found."""
    return bool(np.allclose(uvs_array, 0.0))


def _extract_usdz_own_texture(usdz_path):
    """Extract the base-color (_bc / diffuse / basecolor) texture from a USDZ zip.

    Writes the PNG/JPG to output/textures/<stem>/ inside the extension directory and returns its path.
    Returns None if the file is not a USDZ or contains no recognisable color texture.
    """
    usdz_path = Path(usdz_path)
    if not str(usdz_path).lower().endswith(".usdz"):
        return None
    try:
        with zipfile.ZipFile(str(usdz_path)) as z:
            candidates = [
                n for n in z.namelist()
                if re.search(r"(_bc|diffuse|basecolor|base_color|albedo)\.(png|jpg|jpeg)$", n, re.IGNORECASE)
            ]
            if not candidates:
                print("[code_generator] No base-color texture found inside '{}'.".format(usdz_path.name))
                return None
            # Prefer the texture whose filename contains the first word of the USDZ stem.
            # e.g. "chameleon_anim_mtl_variant.usdz" → prefer "chameleon_bc.jpg" over "stick_2_bc.jpg"
            primary_word = usdz_path.stem.lower().split("_")[0]
            preferred = [c for c in candidates if primary_word in Path(c).stem.lower()]
            bc_name = preferred[0] if preferred else candidates[0]
            out_dir = _OUTPUT_DIR / "textures" / usdz_path.stem
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / Path(bc_name).name
            with z.open(bc_name) as src, open(str(out_path), "wb") as dst:
                dst.write(src.read())
            print("[code_generator] Extracted texture '{}' → '{}'.".format(bc_name, out_path))
            return str(out_path)
    except Exception as e:
        print("[code_generator] Could not extract texture from USDZ: {}".format(e))
        return None


def _parse_custom_model_with_uvs(model_path):
    """Dispatch to the correct UV-aware parser based on file extension.

    Falls back to procedural cylindrical UV mapping when the file contains
    no UV data (all-zero after parsing).
    """
    suffix = str(model_path).lower()
    if suffix.endswith(".obj"):
        verts, indices, uvs = _parse_obj_with_uvs(model_path)
    elif suffix.endswith(".usda"):
        verts, indices, uvs = _parse_usda_with_uvs(model_path)
    elif suffix.endswith(".usd") or suffix.endswith(".usdz"):
        try:
            verts, indices, uvs = _parse_usd_with_uvs_pxr(model_path)
        except ImportError:
            verts, indices, uvs = _parse_usda_with_uvs(model_path)
    else:
        raise ValueError(
            "Unsupported format for textured custom model. Supported: .obj, .usd, .usda. File: {}".format(model_path)
        )

    if _uvs_are_trivial(uvs):
        print("[code_generator] No UVs found in '{}' — using procedural cylindrical mapping.".format(model_path))
        uvs = _generate_procedural_uvs(verts)

    return verts, indices, uvs
    raise ValueError(
        "Unsupported format for textured custom model. Supported: .obj, .usd, .usda. File: {}".format(model_path)
    )


def _normalize_positions(positions, target_size=2.0):
    """Centre on XZ plane, sit on Y=0, scale longest axis to target_size."""
    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    zs = [p[2] for p in positions]

    cx = (min(xs) + max(xs)) / 2.0
    cz = (min(zs) + max(zs)) / 2.0
    cy = min(ys)  # sit on ground

    span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    scale = target_size / span if span > 1e-6 else 1.0

    return [
        [(p[0] - cx) * scale, (p[1] - cy) * scale, (p[2] - cz) * scale]
        for p in positions
    ]


def _build_mesh_arrays(positions, face_indices, color_rgb):
    """Shared helper: compute smooth normals and pack into numpy arrays."""
    n_verts = len(positions)
    smooth_normals = [[0.0, 0.0, 0.0] for _ in range(n_verts)]

    for tri in face_indices:
        i0, i1, i2 = tri
        p0, p1, p2 = positions[i0], positions[i1], positions[i2]
        e1 = [p1[k] - p0[k] for k in range(3)]
        e2 = [p2[k] - p0[k] for k in range(3)]
        nx = e1[1]*e2[2] - e1[2]*e2[1]
        ny = e1[2]*e2[0] - e1[0]*e2[2]
        nz = e1[0]*e2[1] - e1[1]*e2[0]
        for vi in (i0, i1, i2):
            smooth_normals[vi][0] += nx
            smooth_normals[vi][1] += ny
            smooth_normals[vi][2] += nz

    for i, n in enumerate(smooth_normals):
        length = (n[0]**2 + n[1]**2 + n[2]**2) ** 0.5
        if length > 1e-8:
            smooth_normals[i] = [n[k] / length for k in range(3)]
        else:
            smooth_normals[i] = [0.0, 1.0, 0.0]

    r, g, b = float(color_rgb[0]), float(color_rgb[1]), float(color_rgb[2])
    verts_array   = np.array([[p[0], p[1], p[2], 1.0] for p in positions],      dtype=np.float32)
    normals_array = np.array([[n[0], n[1], n[2]]       for n in smooth_normals], dtype=np.float32)
    colors_array  = np.array([[r, g, b, 1.0]            for _ in positions],      dtype=np.float32)
    indices_array = np.array(face_indices,                                        dtype=np.uint32)
    return verts_array, indices_array, normals_array, colors_array


def _compute_smooth_normals(verts_array, indices_array):
    """Compute smooth per-vertex normals from triangle geometry.

    verts_array  : (N, 4) float32 — positions with w=1
    indices_array: flat (M*3,) or (M, 3) uint32 — triangle indices
    Returns (N, 3) float32 normal array.
    """
    indices_array = np.asarray(indices_array).reshape(-1, 3)
    n = len(verts_array)
    normals = np.zeros((n, 3), dtype=np.float64)
    for tri in indices_array:
        i0, i1, i2 = int(tri[0]), int(tri[1]), int(tri[2])
        p0 = verts_array[i0, :3].astype(np.float64)
        p1 = verts_array[i1, :3].astype(np.float64)
        p2 = verts_array[i2, :3].astype(np.float64)
        face_n = np.cross(p1 - p0, p2 - p0)
        normals[i0] += face_n
        normals[i1] += face_n
        normals[i2] += face_n
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    lengths = np.where(lengths < 1e-8, 1.0, lengths)
    return (normals / lengths).astype(np.float32)


def _animation_model_code(suffix, animation, position, scale):
    """Return per-frame code for self-animations: bounce, spin, lerp."""
    anim_type = animation.get("type", "")
    x, y, z   = float(position[0]), float(position[1]), float(position[2])
    sx, sy, sz = float(scale[0]),    float(scale[1]),    float(scale[2])

    if anim_type == "bounce":
        amplitude = float(animation.get("amplitude", 0.5))
        speed     = float(animation.get("speed",     2.0))
        return (
            f"_t_{suffix} = time.time()\n"
            f"model_{suffix} = util.translate({x}, {y} + {amplitude} * np.sin(_t_{suffix} * {speed}), {z})"
            f" @ util.scale({sx}, {sy}, {sz})\n"
        )

    if anim_type == "spin":
        speed = float(animation.get("speed", 1.0))   # rad/s
        ax, ay, az = animation.get("axis", [0, 1, 0])
        return (
            f"_t_{suffix} = time.time()\n"
            f"model_{suffix} = util.translate({x}, {y}, {z})"
            f" @ util.rotate(({ax}, {ay}, {az}), _t_{suffix} * {speed})"
            f" @ util.scale({sx}, {sy}, {sz})\n"
        )

    if anim_type == "lerp":
        fx, fy, fz = float(animation.get("from", [x, y, z])[0]), float(animation.get("from", [x, y, z])[1]), float(animation.get("from", [x, y, z])[2])
        tx, ty, tz = float(animation.get("to",   [x, y, z])[0]), float(animation.get("to",   [x, y, z])[1]), float(animation.get("to",   [x, y, z])[2])
        duration   = float(animation.get("duration", 3.0))
        return (
            f"_t_{suffix} = time.time()\n"
            f"_prog_{suffix} = (_t_{suffix} % ({duration} * 2)) / {duration}\n"
            f"_prog_{suffix} = _prog_{suffix} if _prog_{suffix} <= 1.0 else 2.0 - _prog_{suffix}\n"
            f"model_{suffix} = util.translate("
            f"{fx} + _prog_{suffix} * ({tx} - {fx}), "
            f"{fy} + _prog_{suffix} * ({ty} - {fy}), "
            f"{fz} + _prog_{suffix} * ({tz} - {fz})"
            f") @ util.scale({sx}, {sy}, {sz})\n"
        )

    # Fallback: static
    return f"model_{suffix} = util.translate({x}, {y}, {z}) @ util.scale({sx}, {sy}, {sz})\n"


def _orbit_model_code(suffix, orbit, scale):
    """Return per-frame code that computes a dynamic model matrix for an orbiting mesh."""
    cx, cy, cz = orbit.get("center", [0.0, 0.0, 0.0])
    radius = float(orbit.get("radius", 3.0))
    speed  = float(orbit.get("speed",  0.8))
    sx, sy, sz = float(scale[0]), float(scale[1]), float(scale[2])
    return (
        f"_t_orb_{suffix} = time.time()\n"
        f"_ang_orb_{suffix} = _t_orb_{suffix} * {speed}\n"
        f"model_{suffix} = util.translate("
        f"{cx} + np.cos(_ang_orb_{suffix}) * {radius}, "
        f"{cy}, "
        f"{cz} + np.sin(_ang_orb_{suffix}) * {radius}"
        f") @ util.scale({sx}, {sy}, {sz})\n"
    )


def _orbit_light_uniform_code(orbit):
    """Return per-frame code that updates activeLightPos for an orbiting light."""
    cx, cy, cz = orbit.get("center", [0.0, 0.0, 0.0])
    radius = float(orbit.get("radius", 3.0))
    speed  = float(orbit.get("speed",  0.8))
    height = float(orbit.get("height", cy + 2.5))
    return (
        f"_t_orb_light = time.time()\n"
        f"activeLightPos = np.array(["
        f"{cx} + np.cos(_t_orb_light * {speed}) * {radius}, "
        f"{height}, "
        f"{cz} + np.sin(_t_orb_light * {speed}) * {radius}"
        f"], dtype=np.float32)\n"
    )


def _tex_lighting_uniforms(shader_var):
    """Return generated-script code that sets Phong lighting uniforms on a texture shader."""
    return f"""
_t = time.time()
_lpos_orbit = np.array([np.cos(_t * 0.8) * 5.0, 4.0, np.sin(_t * 0.8) * 5.0], dtype=np.float32)
{shader_var}.setUniformVariable(key='Lambientcolor', value=Lambientcolor,        float3=True)
{shader_var}.setUniformVariable(key='Lambientstr',   value=Lambientstr,          float1=True)
{shader_var}.setUniformVariable(key='LviewPos',      value=LviewPos,             float3=True)
{shader_var}.setUniformVariable(key='Lposition',     value=_lpos_orbit,          float3=True)
{shader_var}.setUniformVariable(key='Lcolor',        value=activeLightColor[:3], float3=True)
{shader_var}.setUniformVariable(key='Lintensity',    value=activeLightIntensity, float1=True)
"""


def _extract_asset_from_usdz(usdz_path, asset_rel_path):
    """Extract a specific asset from a USDZ zip by its relative path.

    Handles variants like './0/tex.png', '0/tex.png', '@./0/tex.png@'.
    Returns the local extracted path, or None if not found.
    """
    usdz_path = Path(usdz_path)
    out_dir = _OUTPUT_DIR / "textures" / usdz_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    clean = asset_rel_path.strip("@").lstrip("./").lstrip("/")
    with zipfile.ZipFile(str(usdz_path)) as z:
        names = z.namelist()
        match = next((n for n in names if n.lstrip("./").lstrip("/") == clean), None)
        if not match:
            target = Path(clean).name
            match = next((n for n in names if Path(n).name == target), None)
        if not match:
            return None
        out_path = out_dir / Path(match).name
        with z.open(match) as src, open(str(out_path), "wb") as dst:
            dst.write(src.read())
        return str(out_path)


def _find_usdz_mesh_texture(mesh_prim, usdz_path):
    """Return the extracted base-color texture path bound to a specific USD mesh prim.

    Looks up the bound material then searches for a UsdUVTexture shader under it
    by traversing the stage and filtering by path prefix.
    Returns None if no texture is found.
    """
    try:
        from pxr import UsdShade
    except ImportError:
        return None

    # --- try material binding ---
    try:
        binding_api = UsdShade.MaterialBindingAPI(mesh_prim)
        material, _ = binding_api.ComputeBoundMaterial()
    except Exception:
        material = None

    stage    = mesh_prim.GetStage()
    mat_path = material.GetPrim().GetPath() if (material and material.GetPrim().IsValid()) else None

    # Collect all texture file paths from UsdUVTexture shaders under this material
    texture_paths = []
    for prim in stage.Traverse():
        if mat_path and not prim.GetPath().HasPrefix(mat_path):
            continue
        shader = UsdShade.Shader(prim)
        if not shader:
            continue
        try:
            if shader.GetIdAttr().Get() != "UsdUVTexture":
                continue
        except Exception:
            continue
        file_input = shader.GetInput("file")
        if not file_input:
            continue
        try:
            asset = file_input.Get()
        except Exception:
            continue
        if asset and asset.path:
            texture_paths.append(asset.path)

    if not texture_paths:
        return None

    # Prefer the base-color / diffuse texture over roughness / normal / AO maps
    bc_paths = [p for p in texture_paths
                if re.search(r"(_bc|diffuse|basecolor|base_color|albedo)\.(png|jpg|jpeg)$",
                             p, re.IGNORECASE)]
    best = bc_paths[0] if bc_paths else texture_paths[0]
    return _extract_asset_from_usdz(usdz_path, best)


def _parse_usdz_all_meshes_with_textures(usdz_path):
    """Parse a USDZ and return one (verts, indices, uvs, tex_path) per mesh prim.

    Each mesh is normalised in the same coordinate space so relative positions
    between meshes are preserved. UVs fall back to procedural cylindrical mapping
    when no 'st' primvar is found.
    """
    from pxr import Usd, UsdGeom, Gf

    usdz_path = Path(usdz_path)
    stage = Usd.Stage.Open(str(usdz_path))
    mpu = UsdGeom.GetStageMetersPerUnit(stage) or 0.01
    time_code = Usd.TimeCode.Default()

    raw_meshes = []  # (positions, faces, uvs, tex_path, label)

    for prim in stage.Traverse():
        if prim.GetTypeName() != "Mesh":
            continue
        mesh = UsdGeom.Mesh(prim)
        pts = mesh.GetPointsAttr().Get(time_code)
        face_cnts = mesh.GetFaceVertexCountsAttr().Get(time_code)
        face_idx = mesh.GetFaceVertexIndicesAttr().Get(time_code)
        if pts is None or face_cnts is None or face_idx is None:
            continue

        try:
            world_xform = UsdGeom.XformCache(time_code).GetLocalToWorldTransform(prim)
        except Exception:
            world_xform = Gf.Matrix4d(1.0)

        prim_positions = []
        for p in pts:
            wp = world_xform.Transform(Gf.Vec3d(p[0], p[1], p[2]))
            prim_positions.append([float(wp[0]) * mpu, float(wp[1]) * mpu, float(wp[2]) * mpu])

        st_pv = UsdGeom.PrimvarsAPI(mesh).GetPrimvar("st")
        uvs_raw, uv_idxs = [], []
        if st_pv and st_pv.HasValue():
            uvs_raw = [[float(u), float(v)] for u, v in st_pv.Get(time_code)]
            raw_idx = st_pv.GetIndices(time_code)
            uv_idxs = list(raw_idx) if raw_idx is not None else list(range(len(face_idx)))

        unique_verts = {}
        out_positions, out_uvs, out_tris = [], [], []
        pos_idx_list = list(face_idx)
        offset = 0
        for cnt in face_cnts:
            face_new = []
            for j in range(cnt):
                pi = pos_idx_list[offset + j]
                ui = uv_idxs[offset + j] if uv_idxs else 0
                key = (pi, ui)
                if key not in unique_verts:
                    unique_verts[key] = len(out_positions)
                    out_positions.append(prim_positions[pi])
                    out_uvs.append(uvs_raw[ui] if uvs_raw else [0.0, 0.0])
                face_new.append(unique_verts[key])
            for k in range(1, len(face_new) - 1):
                out_tris.append([face_new[0], face_new[k], face_new[k + 1]])
            offset += cnt

        if not out_positions or not out_tris:
            continue

        tex_path = _find_usdz_mesh_texture(prim, usdz_path)
        raw_meshes.append((out_positions, out_tris, out_uvs, tex_path, str(prim.GetPath())))

    if not raw_meshes:
        raise ValueError("No mesh geometry found in USDZ: {}".format(usdz_path))

    # Compute global normalisation so all meshes share the same scale/origin
    all_pts = [p for positions, _, _, _, _ in raw_meshes for p in positions]
    xs = [p[0] for p in all_pts]; ys = [p[1] for p in all_pts]; zs = [p[2] for p in all_pts]
    cx = (min(xs) + max(xs)) / 2.0
    cz = (min(zs) + max(zs)) / 2.0
    cy = min(ys)
    span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    sc = 2.0 / span if span > 1e-6 else 1.0

    results = []
    for positions, faces, uvs, tex_path, label in raw_meshes:
        norm = [[(p[0] - cx) * sc, (p[1] - cy) * sc, (p[2] - cz) * sc] for p in positions]
        verts_arr = np.array([[p[0], p[1], p[2], 1.0] for p in norm], dtype=np.float32)
        idx_arr   = np.array(faces, dtype=np.uint32)
        uvs_arr   = np.array(uvs,   dtype=np.float32)
        if _uvs_are_trivial(uvs_arr):
            print("[code_generator] Submesh '{}' has no UVs — using procedural mapping.".format(label))
            uvs_arr = _generate_procedural_uvs(verts_arr)
        results.append((verts_arr, idx_arr, uvs_arr, tex_path))

    return results


def _parse_usd_for_codegen(usd_path, color_rgb):
    """Dispatch USD parsing: USDA text without pxr, binary USD/USDZ via pxr."""
    suffix = str(usd_path).lower()
    if suffix.endswith(".usda"):
        return _parse_usda_text(usd_path, color_rgb)
    try:
        return _parse_usd_with_pxr(usd_path, color_rgb)
    except ImportError:
        raise ValueError(
            "Binary USD files require the OpenUSD Python library (pxr).\n"
            "Install with: pip install usd-core\n"
            "Or export your model as .usda (text USD) or .obj instead.\n"
            "File: {}".format(usd_path)
        )


# -----------------------------
# Recursive node emission
# -----------------------------
def emit_mesh_object_node(node, idx, parent_entity_var, parent_trs_expr):
    name = node["name"]
    shape = node["shape"]
    transform = node["transform"]
    material = node["material"]

    # ── custom OBJ / USD model ──────────────────────────────────────────────
    if shape == "custom":
        model_path = node.get("custom_model_path")
        if not model_path:
            raise ValueError("custom shape requires 'custom_model_path'")

        if is_textured_material(material):
            return emit_textured_custom_model_node(node, idx, parent_entity_var, parent_trs_expr)

        # Multi-mesh USDZ: each mesh gets its own texture from the USD material binding
        if str(model_path).lower().endswith(".usdz"):
            try:
                return emit_multi_mesh_usdz_node(node, idx, parent_entity_var, parent_trs_expr)
            except Exception as e:
                print("[code_generator] Multi-mesh USDZ failed ({}), falling back to single mesh.".format(e))

        # Single-mesh fallback: auto-detect best _bc texture from zip
        own_tex = _extract_usdz_own_texture(model_path)
        if own_tex:
            auto_node = deepcopy(node)
            auto_node["material"]["texture"] = {"enabled": True, "path": own_tex}
            return emit_textured_custom_model_node(auto_node, idx, parent_entity_var, parent_trs_expr)

        suffix_lower = str(model_path).lower()
        if suffix_lower.endswith(".usd") or suffix_lower.endswith(".usda") or suffix_lower.endswith(".usdz"):
            vertices, indices, normals, colors = _parse_usd_for_codegen(model_path, material["color"])
        elif suffix_lower.endswith(".obj"):
            vertices, indices, normals, colors = _parse_obj_for_codegen(model_path, material["color"])
        else:
            raise ValueError(
                "Unsupported custom model format. Supported: .obj, .usd, .usda. File: {}".format(model_path)
            )

        position = transform["position"]
        rotation = transform["rotation"]
        suffix = str(idx)
        entity_var = "node_{}".format(suffix)
        trans_var  = "trans_{}".format(suffix)
        mesh_var   = "mesh_{}".format(suffix)
        shader_var = "shader_{}".format(suffix)
        local_trs_expr = "{} @ {}".format(make_translate(position), make_rotate(rotation))
        world_trs_expr = "{} @ ({})".format(parent_trs_expr, local_trs_expr)
        mat_color_expr = vec3_to_util_vec(material["color"])

        vertices_code = ndarray_to_python(vertices, "float32")
        indices_code  = ndarray_to_python(indices,  "uint32")
        colors_code   = ndarray_to_python(colors,   "float32")
        normals_code  = ndarray_to_python(normals,  "float32")

        object_code = """
# ===== mesh_object (custom OBJ/USD): {name} =====
vertices_{suffix} = {vertices_code}
indices_{suffix} = {indices_code}
colors_{suffix} = {colors_code}
normals_{suffix} = {normals_code}

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
    ShaderGLDecorator(Shader(vertex_import_file=SHADER_DIR / "Phong.vert", fragment_import_file=SHADER_DIR / "Phong.frag"))
)
""".format(name=name, suffix=suffix, entity_var=entity_var, parent_entity_var=parent_entity_var,
           trans_var=trans_var, local_trs_expr=local_trs_expr, mesh_var=mesh_var,
           shader_var=shader_var, vertices_code=vertices_code, indices_code=indices_code,
           colors_code=colors_code, normals_code=normals_code)

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
""".format(suffix=suffix, shader_var=shader_var, world_trs_expr=world_trs_expr,
           mat_color_expr=mat_color_expr)

        return object_code, uniform_code, ""

    # ── built-in primitive shapes ───────────────────────────────────────────
    if is_textured_material(material):
        return emit_textured_mesh_object_node(node, idx, parent_entity_var, parent_trs_expr)

    position = transform["position"]
    rotation = transform["rotation"]
    color = material["color"]

    suffix = str(idx)

    entity_var = "node_{}".format(suffix)
    trans_var = "trans_{}".format(suffix)
    mesh_var = "mesh_{}".format(suffix)
    shader_var = "shader_{}".format(suffix)

    local_trs_expr = "{} @ {}".format(make_translate(position), make_rotate(rotation))
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
            vertex_import_file=SHADER_DIR / "Phong.vert",
            fragment_import_file=SHADER_DIR / "Phong.frag"
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

    orbit     = node.get("orbit")
    animation = node.get("animation")
    if orbit:
        model_line = _orbit_model_code(suffix, orbit, transform.get("scale", [1.0, 1.0, 1.0]))
    elif animation:
        model_line = _animation_model_code(suffix, animation, position, transform.get("scale", [1.0, 1.0, 1.0]))
    else:
        model_line = "model_{suffix} = {world_trs_expr}\n".format(
            suffix=suffix, world_trs_expr=world_trs_expr)

    uniform_code = """
{model_line}mvp_{suffix} = projMat @ view @ model_{suffix}
{shader_var}.setUniformVariable(key='modelViewProj', value=mvp_{suffix}, mat4=True)
{shader_var}.setUniformVariable(key='model', value=model_{suffix}, mat4=True)
{shader_var}.setUniformVariable(key='ambientColor', value=Lambientcolor, float3=True)
{shader_var}.setUniformVariable(key='ambientStr', value=Lambientstr, float1=True)
{shader_var}.setUniformVariable(key='viewPos', value=LviewPos, float3=True)
{shader_var}.setUniformVariable(key='lightPos', value=activeLightPos, float3=True)
{shader_var}.setUniformVariable(key='lightColor', value=activeLightColor, float3=True)
{shader_var}.setUniformVariable(key='lightIntensity', value=activeLightIntensity, float1=True)
{shader_var}.setUniformVariable(key='shininess', value=Mshininess, float1=True)
""".format(
        model_line=model_line,
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
    rotation = transform["rotation"]
    scale = transform["scale"]

    suffix = str(idx)
    entity_var = "group_node_{}".format(suffix)
    trans_var = "group_trans_{}".format(suffix)

    trs_expr = "{} @ {} @ {}".format(
        make_translate(position),
        make_rotate(rotation),
        make_scale(scale)
    )
    local_trs_expr = trs_expr
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

def emit_multi_mesh_usdz_node(node, idx, parent_entity_var, parent_trs_expr):
    """Emit one ECS entity per USD mesh prim, each with its own material texture."""
    name       = node["name"]
    transform  = node["transform"]
    model_path = node.get("custom_model_path")
    position   = transform["position"]
    rotation   = transform["rotation"]
    suffix     = str(idx)

    local_trs_expr = "{} @ {}".format(make_translate(position), make_rotate(rotation))
    world_trs_expr = "{} @ ({})".format(parent_trs_expr, local_trs_expr)

    meshes = _parse_usdz_all_meshes_with_textures(model_path)
    print("[code_generator] Multi-mesh USDZ '{}': {} submesh(es).".format(Path(model_path).name, len(meshes)))

    group_var = "node_{}".format(suffix)
    object_code = f"""
# ===== multi-mesh USDZ: {name} ({len(meshes)} submeshes) =====
{group_var} = scene.world.createEntity(Entity(name="{name}"))
scene.world.addEntityChild({parent_entity_var}, {group_var})
scene.world.addComponent({group_var}, BasicTransform(name="{name}_TRS", trs={local_trs_expr}))
"""
    uniform_code       = ""
    texture_setup_code = ""

    for m_idx, (verts, indices, uvs, tex_path) in enumerate(meshes):
        ms          = "{}_{}".format(suffix, m_idx)
        mesh_var    = "node_{}".format(ms)
        normals     = _compute_smooth_normals(verts, indices)
        verts_code  = ndarray_to_python(verts,   "float32")
        idx_code    = ndarray_to_python(indices, "uint32")
        uv_code     = ndarray_to_python(uvs,     "float32")
        normals_code= ndarray_to_python(normals, "float32")

        object_code += f"""
# --- submesh {m_idx} ---
vertices_{ms} = {verts_code}
indices_{ms}  = {idx_code}
uv_{ms}       = {uv_code}
normals_{ms}  = {normals_code}
{mesh_var} = scene.world.createEntity(Entity(name="{name}_m{m_idx}"))
scene.world.addEntityChild({group_var}, {mesh_var})
scene.world.addComponent({mesh_var}, BasicTransform(name="{name}_m{m_idx}_TRS", trs=util.identity()))
mesh_{ms} = scene.world.addComponent({mesh_var}, RenderMesh(name="{name}_m{m_idx}_mesh"))
mesh_{ms}.vertex_attributes.append(vertices_{ms})
mesh_{ms}.vertex_attributes.append(uv_{ms})
mesh_{ms}.vertex_attributes.append(normals_{ms})
mesh_{ms}.vertex_index.append(indices_{ms})
scene.world.addComponent({mesh_var}, VertexArray())
shader_{ms} = scene.world.addComponent(
    {mesh_var},
    ShaderGLDecorator(Shader(vertex_source=TEXTURE_VERTEX_SHADER, fragment_source=TEXTURE_FRAGMENT_SHADER))
)
"""
        uniform_code += f"""
model_{ms} = {world_trs_expr}
shader_{ms}.setUniformVariable(key='model', value=model_{ms}, mat4=True)
shader_{ms}.setUniformVariable(key='view', value=view, mat4=True)
shader_{ms}.setUniformVariable(key='proj', value=projMat, mat4=True)
""" + _tex_lighting_uniforms(f"shader_{ms}")
        if tex_path:
            texture_setup_code += f"""
texture_{ms} = Texture(r"{tex_path}")
shader_{ms}.setUniformVariable(key='texSampler', value=texture_{ms}, texture=True)
"""

    return object_code, uniform_code, texture_setup_code


def emit_textured_custom_model_node(node, idx, parent_entity_var, parent_trs_expr):
    """Emit code for a custom OBJ/USD model with a texture (UV-aware)."""
    name         = node["name"]
    transform    = node["transform"]
    material     = node["material"]
    model_path   = node.get("custom_model_path")
    if not model_path:
        raise ValueError("Textured custom model is missing 'custom_model_path'")
    texture_path = (material.get("texture") or {}).get("path")
    if not texture_path:
        raise ValueError("Textured custom model is missing texture.path")

    position = transform["position"]
    rotation = transform["rotation"]
    suffix   = str(idx)

    entity_var  = "node_{}".format(suffix)
    trans_var   = "trans_{}".format(suffix)
    mesh_var    = "mesh_{}".format(suffix)
    shader_var  = "shader_{}".format(suffix)
    texture_var = "texture_{}".format(suffix)

    local_trs_expr = "{} @ {}".format(make_translate(position), make_rotate(rotation))
    world_trs_expr = "{} @ ({})".format(parent_trs_expr, local_trs_expr)

    raw_vertices, raw_indices, raw_uvs = _parse_custom_model_with_uvs(model_path)
    raw_normals   = _compute_smooth_normals(raw_vertices, raw_indices)
    vertices_code = ndarray_to_python(raw_vertices, "float32")
    indices_code  = ndarray_to_python(raw_indices,  "uint32")
    uv_code       = ndarray_to_python(raw_uvs,      "float32")
    normals_code  = ndarray_to_python(raw_normals,  "float32")

    object_code = f"""
# ===== textured custom model: {name} =====
vertices_{suffix} = {vertices_code}
indices_{suffix}  = {indices_code}
uv_{suffix}       = {uv_code}
normals_{suffix}  = {normals_code}

{entity_var} = scene.world.createEntity(Entity(name="{name}"))
scene.world.addEntityChild({parent_entity_var}, {entity_var})

{trans_var} = scene.world.addComponent(
    {entity_var},
    BasicTransform(name="{name}_TRS", trs={local_trs_expr})
)
{mesh_var} = scene.world.addComponent({entity_var}, RenderMesh(name="{name}_mesh"))
{mesh_var}.vertex_attributes.append(vertices_{suffix})
{mesh_var}.vertex_attributes.append(uv_{suffix})
{mesh_var}.vertex_attributes.append(normals_{suffix})
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
""" + _tex_lighting_uniforms(shader_var)

    texture_set_up_code = f"""
{texture_var} = Texture(r"{texture_path}")
{shader_var}.setUniformVariable(key='texSampler', value={texture_var}, texture=True)
"""
    return object_code, uniform_code, texture_set_up_code


def emit_textured_mesh_object_node(node, idx, parent_entity_var, parent_trs_expr):
    name = node["name"]
    shape = node["shape"]
    transform = node["transform"]
    material = node["material"]

    position = transform["position"]
    rotation = transform["rotation"]
    texture_path = (material.get("texture") or {}).get("path")
    if not texture_path:
        raise ValueError("Textured material is missing texture.path")
    suffix = str(idx)

    entity_var = "node_{}".format(suffix)
    trans_var = "trans_{}".format(suffix)
    mesh_var = "mesh_{}".format(suffix)
    shader_var = "shader_{}".format(suffix)
    texture_var = "texture_{}".format(suffix)

    local_trs_expr = "{} @ {}".format(make_translate(position), make_rotate(rotation))
    world_trs_expr = "{} @ ({})".format(parent_trs_expr, local_trs_expr)

    params = {"scale": transform.get("scale", [1.0, 1.0, 1.0])}
    raw_vertices, raw_indices, raw_uvs = create_textured_mesh(shape, params)
    raw_normals   = _compute_smooth_normals(raw_vertices, raw_indices)
    vertices_code = ndarray_to_python(raw_vertices, "float32")
    indices_code  = ndarray_to_python(raw_indices,  "uint32")
    uv_code       = ndarray_to_python(raw_uvs,      "float32")
    normals_code  = ndarray_to_python(raw_normals,  "float32")

    object_code = f"""
# ===== textured mesh_object: {name} =====
vertices_{suffix} = {vertices_code}
indices_{suffix}  = {indices_code}
uv_{suffix}       = {uv_code}
normals_{suffix}  = {normals_code}

{entity_var} = scene.world.createEntity(Entity(name="{name}"))
scene.world.addEntityChild({parent_entity_var}, {entity_var})

{trans_var} = scene.world.addComponent(
    {entity_var},
    BasicTransform(name="{name}_TRS", trs={local_trs_expr})
)
{mesh_var} = scene.world.addComponent({entity_var}, RenderMesh(name="{name}_mesh"))
{mesh_var}.vertex_attributes.append(vertices_{suffix})
{mesh_var}.vertex_attributes.append(uv_{suffix})
{mesh_var}.vertex_attributes.append(normals_{suffix})
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
""" + _tex_lighting_uniforms(shader_var)

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

    # If the active light has an orbit, prepend per-frame activeLightPos update
    if active_light and active_light.get("orbit"):
        uniform_code = _orbit_light_uniform_code(active_light["orbit"]) + uniform_code

    footer = build_footer(title, uniform_code, post_init_code)

    final_script = header + "\n" + object_code + "\n" + footer
    return final_script


def save_script(script, output_path: Optional[str] = None, scene_ir: Optional[dict] = None):
    if output_path is None:
        output_file = Path(os.path.abspath(os.path.dirname(__file__))) / "scene_out.py"
    else:
        output_file = Path(output_path).resolve()

    with open(str(output_file), "wb") as f:
        f.write(script.encode("utf-8"))

    print("Saved script to:", output_file)

    if scene_ir is not None:
        ir_file = Path(os.path.abspath(os.path.dirname(__file__))) / "scene_bridge" / "scene_ir.json"
        import json as _json
        with open(str(ir_file), "wb") as f:
            f.write(_json.dumps(scene_ir, indent=2, ensure_ascii=False).encode("utf-8"))
        print("Saved scene IR to:", ir_file)

