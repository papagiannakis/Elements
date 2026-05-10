import json
import math
import os
import shutil
import time
import traceback
import re
from copy import deepcopy
from pathlib import Path

from code_generator import generate_scene_script
from llm_parser import (
    lookup_cached_action,
    parse_composite_spec_with_llm,
    parse_prompt_to_action_with_llm,
    store_cached_action,
)
from prefabs import build_house, build_tree, build_gift_box, build_street_light



PROJECT_DIR = Path(__file__).resolve().parent
PROJECT_SCENE_IR_FILE = PROJECT_DIR / "scene_ir.json"

SHARED_DIR = Path.home() / "Desktop" / "scene_bridge"
SHARED_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_DIR = SHARED_DIR / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

SAVED_SCENES_DIR = SHARED_DIR / "saved_scenes"
SAVED_SCENES_DIR.mkdir(parents=True, exist_ok=True)

PREFABS_DIR = SHARED_DIR / "prefabs"
PREFABS_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_STACK_FILE = HISTORY_DIR / "undo_stack.json"

SCENE_IR_FILE = SHARED_DIR / "scene_ir.json"
PREVIEW_IR_FILE = SHARED_DIR / "preview_scene_ir.json"
AI_REQUEST_FILE = SHARED_DIR / "ai_request.json"
UI_STATE_FILE = SHARED_DIR / "ui_state.json"
SCENE_STATE_FILE = SHARED_DIR / "scene_state.json"

SCENE_OUT_FILE = Path.home() / "Desktop" / "scene_out.py"
PREVIEW_SCENE_FILE = SHARED_DIR / "preview_scene.py"

POLL_INTERVAL = 0.5
GRID_SPACING = 1.5
CUBE_Y = 0.5
CUBE_Z = 0.0

COLOR_TABLE = {
    "red": [1.0, 0.0, 0.0],
    "green": [0.0, 1.0, 0.0],
    "blue": [0.0, 0.0, 1.0],
    "yellow": [1.0, 1.0, 0.0],
    "white": [1.0, 1.0, 1.0],
    "black": [0.02, 0.02, 0.02],
    "purple": [0.8, 0.0, 0.8],
}

SHAPE_WORDS = [
    "cube",
    "sphere",
    "cylinder",
    "cone",
    "pyramid",
    "plane",
]

DEFAULT_NEW_SCENE_IR = {
    "node_type": "scene",
    "name": "root",
    "window": {
        "width": 1200,
        "height": 800,
        "title": "New Scene"
    },
    "children": [
        {
            "node_type": "mesh_object",
            "name": "cube_1",
            "id": "cube_1",
            "created_order": 1,
            "shape": "cube",
            "transform": {
                "position": [0.0, 0.5, 0.0],
                "scale": [1.0, 1.0, 1.0]
            },
            "material": {
                "color": [0.8, 0.0, 0.8],
                "texture": {
                    "enabled": False,
                    "path": None
                }
            }
        }
    ]
}


def now_timestamp():
    return time.strftime("%Y%m%d_%H%M%S")


def read_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default

    try:
        with open(str(path), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


_WRITE_RETRIES = 8
_WRITE_RETRY_DELAY = 0.15  # seconds between retries; total budget ≈ 5.4 s


def _atomic_replace(tmp_path, dest_path):
    """os.replace with retry loop to handle Windows file-lock races."""
    last_exc = None
    for attempt in range(_WRITE_RETRIES):
        try:
            os.replace(str(tmp_path), str(dest_path))
            return
        except OSError as exc:  # covers PermissionError, WinError 32 (sharing), etc.
            last_exc = exc
            time.sleep(_WRITE_RETRY_DELAY * (attempt + 1))
    try:
        Path(tmp_path).unlink(missing_ok=True)
    except Exception:
        pass
    raise PermissionError(
        f"[controller] atomic replace failed after {_WRITE_RETRIES} retries: {dest_path}"
    ) from last_exc


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(str(tmp_path), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise

    _atomic_replace(tmp_path, path)


def write_text_atomic(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(str(tmp_path), "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise

    _atomic_replace(tmp_path, path)


def copy_file_atomic(source_path, target_path):
    source_path = Path(source_path)
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")
    try:
        shutil.copyfile(str(source_path), str(tmp_path))
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise

    _atomic_replace(tmp_path, target_path)


def clear_preview_files():
    for path in (PREVIEW_IR_FILE, PREVIEW_SCENE_FILE):
        try:
            if path.exists():
                path.unlink()
                print("[controller] Cleared preview file:", path)
        except Exception as e:
            print("[controller] Could not clear preview file:", path, e)


def clear_history_files():
    stack = read_json(HISTORY_STACK_FILE, default=[])
    if isinstance(stack, list):
        for filename in stack:
            try:
                path = HISTORY_DIR / str(filename)
                if path.exists():
                    path.unlink()
            except Exception:
                pass

    write_json(HISTORY_STACK_FILE, [])
    print("[controller] Reset undo history:", HISTORY_STACK_FILE)


def reset_request_and_ui_files(status=None, message=None, request_id=None):
    req = {
        "request_id": request_id,
        "status": status or "idle",
        "message": message or "",
        "updated_at": time.time()
    }

    try:
        write_json(AI_REQUEST_FILE, req)
        print("[controller] Reset request file:", AI_REQUEST_FILE)
    except Exception as exc:
        print(f"[controller] reset_request_and_ui_files: could not write AI_REQUEST_FILE: {exc}")

    try:
        write_json(UI_STATE_FILE, {
            "action": "idle",
            "request_id": request_id,
            "updated_at": time.time()
        })
        print("[controller] Reset UI file:", UI_STATE_FILE)
    except Exception as exc:
        print(f"[controller] reset_request_and_ui_files: could not write UI_STATE_FILE: {exc}")


def write_scene_state(mode, active_script, request_id=None):
    data = {
        "mode": mode,
        "active_script": str(active_script),
        "updated_at": time.time()
    }

    if request_id is not None:
        data["request_id"] = request_id

    write_json(SCENE_STATE_FILE, data)
    print("[controller] scene_state ->", mode, active_script)


def write_status(status, message=None, request_id=None, error=None):
    data = {
        "request_id": request_id,
        "status": status,
        "updated_at": time.time()
    }

    if message is not None:
        data["message"] = message
    if error is not None:
        data["error"] = error

    try:
        write_json(AI_REQUEST_FILE, data)
    except Exception as exc:
        print(f"[controller] write_status failed ({status}): {exc}")


def walk_nodes(node):
    if not isinstance(node, dict):
        return

    yield node

    for child in node.get("children", []):
        for item in walk_nodes(child):
            yield item

def collect_mesh_objects(node, out_list=None):
    if out_list is None:
        out_list = []

    if not isinstance(node, dict):
        return out_list

    if node.get("node_type") == "mesh_object":
        out_list.append(node)

    for child in node.get("children", []):
        collect_mesh_objects(child, out_list)

    return out_list


def delete_nodes_by_ids(scene_ir, object_ids):
    if not object_ids:
        return scene_ir

    object_ids = set(str(x) for x in object_ids)

    def filter_children(children):
        kept = []
        for child in children:
            if not isinstance(child, dict):
                kept.append(child)
                continue

            child_id = str(child.get("id", ""))
            if child.get("node_type") == "mesh_object" and child_id in object_ids:
                continue

            if "children" in child and isinstance(child["children"], list):
                child["children"] = filter_children(child["children"])

            kept.append(child)
        return kept

    if "children" in scene_ir and isinstance(scene_ir["children"], list):
        scene_ir["children"] = filter_children(scene_ir["children"])

    return scene_ir

def collect_groups(scene_ir):
    return [
        node for node in walk_nodes(scene_ir)
        if isinstance(node, dict) and node.get("node_type") == "group"
    ]


def make_unique_name(scene_ir, prefix):
    existing = set()

    for node in walk_nodes(scene_ir):
        name = node.get("name")
        if name:
            existing.add(str(name))

    index = 1
    while prefix + "_" + str(index) in existing or prefix + str(index) in existing:
        index += 1

    return prefix + "_" + str(index)


def next_object_order(scene_ir):
    max_order = 0

    for node in walk_nodes(scene_ir):
        if not isinstance(node, dict):
            continue

        try:
            order = int(node.get("created_order", 0))
        except Exception:
            order = 0

        if order > max_order:
            max_order = order

    return max_order + 1


def ensure_stable_object_ids(scene_ir):
    used_ids = set()
    used_names = set()
    next_order = 1

    for node in walk_nodes(scene_ir):
        if not isinstance(node, dict):
            continue

        node_type = node.get("node_type")
        if node_type not in ("mesh_object", "group"):
            continue

        prefix = str(node.get("shape", node_type))
        name = node.get("name")

        if not name:
            name = make_unique_name(scene_ir, prefix)
            node["name"] = name

        name = str(name)
        if name in used_names:
            name = make_unique_name(scene_ir, prefix)
            node["name"] = name

        used_names.add(name)

        obj_id = node.get("id") or name
        base_id = str(obj_id)
        candidate = base_id
        suffix = 2

        while candidate in used_ids:
            candidate = base_id + "_" + str(suffix)
            suffix += 1

        node["id"] = candidate
        used_ids.add(candidate)

        try:
            order = int(node.get("created_order"))
        except Exception:
            order = next_order

        node["created_order"] = order
        next_order = max(next_order, order + 1)

    return scene_ir


def load_project_baseline_ir():
    data = read_json(PROJECT_SCENE_IR_FILE, default=None)
    if isinstance(data, dict):
        print("[controller] Loaded project baseline IR:", PROJECT_SCENE_IR_FILE)
        return ensure_stable_object_ids(data)

    print("[controller] Project baseline missing; using DEFAULT_NEW_SCENE_IR.")
    return deepcopy(DEFAULT_NEW_SCENE_IR)


def fresh_new_scene_ir():
    print("[controller] New Scene baseline: DEFAULT_NEW_SCENE_IR with one default cube.")
    return ensure_stable_object_ids(deepcopy(DEFAULT_NEW_SCENE_IR))


def ensure_shared_scene_ir():
    data = read_json(SCENE_IR_FILE, default=None)

    if not isinstance(data, dict):
        data = load_project_baseline_ir()
        write_json(SCENE_IR_FILE, data)
        print("[controller] Initialized shared scene_ir.json:", SCENE_IR_FILE)

    data = ensure_stable_object_ids(data)
    write_json(SCENE_IR_FILE, data)
    return data


def ensure_scene_children(scene_ir):
    children = scene_ir.get("children")

    if not isinstance(children, list):
        children = []
        scene_ir["children"] = children

    return children


def ensure_official_scene_script():
    scene_ir = ensure_shared_scene_ir()

    if not SCENE_OUT_FILE.exists():
        write_text_atomic(SCENE_OUT_FILE, generate_scene_script(scene_ir))
        print("[controller] Created official scene script:", SCENE_OUT_FILE)


def initialize_bridge_state():
    print("[controller] Initializing bridge state.")
    ensure_shared_scene_ir()
    ensure_official_scene_script()
    clear_preview_files()
    seed_builtin_prefabs()

    req = read_json(AI_REQUEST_FILE, default=None)
    if isinstance(req, dict) and req.get("status") in ("pending", "preview_ready"):
        write_status("stale", "Cleared stale request on controller startup.", request_id=req.get("request_id"))
    elif not isinstance(req, dict):
        reset_request_and_ui_files(status="idle", message="Controller initialized.", request_id=None)

    write_json(UI_STATE_FILE, {
        "action": "idle",
        "updated_at": time.time()
    })

    write_scene_state("official", SCENE_OUT_FILE)
    print("[controller] Bridge initialization complete.")


def initialize_new_scene(request_id=None):
    print("[controller] Initializing new scene.")
    print("[controller] official scene_ir path:", SCENE_IR_FILE)
    print("[controller] official scene_out path:", SCENE_OUT_FILE)

    clear_preview_files()
    clear_history_files()

    scene_ir = fresh_new_scene_ir()
    write_json(SCENE_IR_FILE, scene_ir)
    write_text_atomic(SCENE_OUT_FILE, generate_scene_script(scene_ir))

    reset_request_and_ui_files(
        status="new_scene_created",
        message="New scene created from default baseline.",
        request_id=request_id
    )

    write_scene_state("official", SCENE_OUT_FILE, request_id=request_id)

    print("[controller] New scene initialized.")
    print("[controller] Baseline used: DEFAULT_NEW_SCENE_IR")
    print("[controller] Official scene path:", SCENE_OUT_FILE)


def color_name_from_text(text):
    text = text.lower()

    for name in COLOR_TABLE:
        if re.search(r"\b" + re.escape(name) + r"\b", text):
            return name

    return None


def color_value(color_name):
    if color_name is None:
        return [0.8, 0.0, 0.8]

    return list(COLOR_TABLE[color_name])


def color_matches(actual, expected):
    if not isinstance(actual, list) or len(actual) != 3:
        return False

    return all(abs(float(actual[i]) - float(expected[i])) < 0.05 for i in range(3))


def shape_from_text(text):
    text = text.lower()

    for shape in SHAPE_WORDS:
        if re.search(r"\b" + re.escape(shape) + r"\b", text):
            return shape

    if "κύβ" in text or "κυβ" in text:
        return "cube"

    return None


_DIRECTION_WORD_MAP = {
    "right":    "right",
    "left":     "left",
    "up":       "up",
    "upward":   "up",
    "upwards":  "up",
    "above":    "up",
    "higher":   "up",
    "down":     "down",
    "downward": "down",
    "downwards":"down",
    "below":    "down",
    "lower":    "down",
    "forward":  "forward",
    "front":    "forward",
    "ahead":    "forward",
    "backward": "backward",
    "back":     "backward",
    "behind":   "backward",
}


def direction_from_text(text):
    text = text.lower()
    for word, canonical in _DIRECTION_WORD_MAP.items():
        if re.search(r"\b" + re.escape(word) + r"\b", text):
            return canonical
    return None


def reference_mode_from_text(text):
    text = text.lower()

    if "most recently added object" in text:
        return "most_recent"
    if "most recent object" in text:
        return "most_recent"
    if "latest object" in text:
        return "most_recent"
    if "last " in text:
        return "last"
    if "first " in text:
        return "first"

    return "default"


def sort_targets_for_reference(nodes, mode):
    def sort_key(node):
        try:
            created_order = int(node.get("created_order", 0))
        except Exception:
            created_order = 0

        return (
            created_order,
            str(node.get("name", "")),
            str(node.get("id", ""))
        )

    ordered = sorted(nodes, key=sort_key)

    if mode in ("last", "most_recent"):
        ordered.reverse()

    return ordered


def get_position(node):
    position = node.get("transform", {}).get("position", [0.0, CUBE_Y, CUBE_Z])
    return [float(position[0]), float(position[1]), float(position[2])]


def get_scale(node):
    scale = node.get("transform", {}).get("scale", [1.0, 1.0, 1.0])
    return [float(scale[0]), float(scale[1]), float(scale[2])]


def set_position(node, position):
    transform = node.setdefault("transform", {})
    transform["position"] = [float(position[0]), float(position[1]), float(position[2])]
    transform.setdefault("scale", [1.0, 1.0, 1.0])


def positions_overlap(a, b):
    return (
        abs(float(a[0]) - float(b[0])) < 0.05 and
        abs(float(a[1]) - float(b[1])) < 0.05 and
        abs(float(a[2]) - float(b[2])) < 0.05
    )


def normalize_group_name(name):
    return str(name).strip().lower().replace(" ", "_")


def group_name_from_text(text):
    text = text.lower().strip()

    patterns = [
        r"\bgroup\s+named\s+([a-zA-Z0-9_ -]+)",
        r"\bin\s+group\s+([a-zA-Z0-9_ -]+)",
        r"\bto\s+group\s+([a-zA-Z0-9_ -]+)",
        r"\bgroup\s+([a-zA-Z0-9_ -]+)",
        r"\bnamed\s+([a-zA-Z0-9_ -]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            raw = match.group(1).strip()
            raw = re.split(r"\b(on top|to the right|right|left|with|and|at)\b", raw)[0].strip()
            if raw:
                return normalize_group_name(raw)

    return None


def find_group(scene_ir, group_name):
    if not group_name:
        return None

    normalized = normalize_group_name(group_name)
    groups = sorted(collect_groups(scene_ir), key=lambda group: str(group.get("name", "")))

    for group in groups:
        if normalize_group_name(group.get("name", "")) == normalized:
            return group

    return None


def ensure_group_children(group_node):
    children = group_node.get("children")

    if not isinstance(children, list):
        children = []
        group_node["children"] = children

    return children


def get_group_world_offset(group_node):
    position = group_node.get("transform", {}).get("position", [0.0, 0.0, 0.0])

    try:
        return [float(position[0]), float(position[1]), float(position[2])]
    except Exception:
        return [0.0, 0.0, 0.0]


def local_to_world_position(local_position, group_node):
    offset = get_group_world_offset(group_node)

    return [
        float(local_position[0]) + offset[0],
        float(local_position[1]) + offset[1],
        float(local_position[2]) + offset[2]
    ]


def world_to_local_position(world_position, group_node):
    offset = get_group_world_offset(group_node)

    return [
        float(world_position[0]) - offset[0],
        float(world_position[1]) - offset[1],
        float(world_position[2]) - offset[2]
    ]


def get_world_position(node, parent_group=None):
    local_position = get_position(node)

    if parent_group is None:
        return local_position

    return local_to_world_position(local_position, parent_group)


def collect_mesh_objects_with_groups(scene_ir):
    result = []

    def walk(node, parent_group=None):
        if not isinstance(node, dict):
            return

        if node.get("node_type") == "mesh_object":
            result.append((node, parent_group))

        next_parent = parent_group
        if node.get("node_type") == "group":
            next_parent = node

        for child in node.get("children", []):
            walk(child, next_parent)

    walk(scene_ir, None)
    return result


def collect_world_positions(scene_ir, exclude_node=None, exclude_object_id=None):
    positions = []

    for node, parent_group in collect_mesh_objects_with_groups(scene_ir):
        if exclude_node is not None and node is exclude_node:
            continue

        node_id = node.get("id")
        if exclude_object_id is not None and str(node_id) == str(exclude_object_id):
            continue
        positions.append(get_world_position(node, parent_group))

    for node in scene_ir.get("children", []):
        if not isinstance(node, dict) or node.get("node_type") != "group":
            continue
        if exclude_node is not None and node is exclude_node:
            continue
        node_id = node.get("id")
        if exclude_object_id is not None and str(node_id) == str(exclude_object_id):
            continue
        positions.append(get_position(node))

    return positions


def is_world_position_free(scene_ir, world_position, exclude_node=None, exclude_object_id=None):
    for used in collect_world_positions(
        scene_ir,
        exclude_node=exclude_node,
        exclude_object_id=exclude_object_id
    ):
        if positions_overlap(used, world_position):
            return False

    return True

def find_nearest_free_world_position(scene_ir, desired_world_position, exclude_object_id=None):
    desired = [
        float(desired_world_position[0]),
        float(desired_world_position[1]),
        float(desired_world_position[2])
    ]

    if is_world_position_free(scene_ir, desired, exclude_object_id=exclude_object_id):
        return desired

    preferred_y = desired[1]
    preferred_z = desired[2]
    base_slot = int(round(desired[0] / GRID_SPACING))

    step = 1
    while True:
        right_candidate = [GRID_SPACING * (base_slot + step), preferred_y, preferred_z]
        if is_world_position_free(scene_ir, right_candidate, exclude_object_id=exclude_object_id):
            return right_candidate

        left_candidate = [GRID_SPACING * (base_slot - step), preferred_y, preferred_z]
        if is_world_position_free(scene_ir, left_candidate, exclude_object_id=exclude_object_id):
            return left_candidate

        step += 1

def find_next_free_world_position(scene_ir, preferred_y=None, preferred_z=None, exclude_object_id=None):
    if preferred_y is None:
        preferred_y = CUBE_Y
    if preferred_z is None:
        preferred_z = CUBE_Z

    slot = 0
    while True:
        world_position = [GRID_SPACING * slot, float(preferred_y), float(preferred_z)]
        if is_world_position_free(scene_ir, world_position, exclude_object_id=exclude_object_id):
            return world_position
        slot += 1


def find_next_free_position_for_group(scene_ir, group_node):
    world_position = find_next_free_world_position(scene_ir)
    return world_to_local_position(world_position, group_node)


def find_first_free_in_direction(scene_ir, start_world_position, delta, exclude_object_id=None, max_steps=50):
    pos = [
        float(start_world_position[0]) + delta[0],
        float(start_world_position[1]) + delta[1],
        float(start_world_position[2]) + delta[2],
    ]
    for _ in range(max_steps):
        if is_world_position_free(scene_ir, pos, exclude_object_id=exclude_object_id):
            return list(pos)
        pos = [pos[0] + delta[0], pos[1] + delta[1], pos[2] + delta[2]]
    # All slots within max_steps are occupied; return the first step as last resort
    return [
        float(start_world_position[0]) + delta[0],
        float(start_world_position[1]) + delta[1],
        float(start_world_position[2]) + delta[2],
    ]


def find_position_right_of_target(scene_ir, target_node, target_group=None, destination_group=None, exclude_object_id=None):
    base = get_world_position(target_node, target_group)
    desired_world_position = [base[0] + GRID_SPACING, base[1], base[2]]

    world_position = find_nearest_free_world_position(
        scene_ir,
        desired_world_position,
        exclude_object_id=exclude_object_id
    )

    if destination_group is not None:
        return world_to_local_position(world_position, destination_group)

    return world_position


def find_position_on_top_of_target(scene_ir, target_node, target_group=None, destination_group=None, exclude_object_id=None):
    base = get_world_position(target_node, target_group)
    scale = get_scale(target_node)
    desired_world_position = [base[0], base[1] + scale[1], base[2]]

    world_position = find_nearest_free_world_position(
        scene_ir,
        desired_world_position,
        exclude_object_id=exclude_object_id
    )

    if destination_group is not None:
        return world_to_local_position(world_position, destination_group)

    return world_position

def make_group_node(scene_ir, group_name):
    normalized = normalize_group_name(group_name)

    if not normalized:
        normalized = make_unique_name(scene_ir, "group")

    existing = set()
    for group in collect_groups(scene_ir):
        existing.add(normalize_group_name(group.get("name", "")))

    name = normalized
    index = 2

    while normalize_group_name(name) in existing:
        name = normalized + "_" + str(index)
        index += 1

    return {
        "node_type": "group",
        "name": name,
        "id": name,
        "created_order": next_object_order(scene_ir),
        "transform": {
            "position": [0.0, 0.0, 0.0],
            "scale": [1.0, 1.0, 1.0]
        },
        "children": []
    }


def make_cube_node(scene_ir, position, color):
    name = make_unique_name(scene_ir, "cube")

    return {
        "node_type": "mesh_object",
        "name": name,
        "id": name,
        "created_order": next_object_order(scene_ir),
        "shape": "cube",
        "transform": {
            "position": position,
            "scale": [1.0, 1.0, 1.0]
        },
        "material": {
            "color": color,
            "texture": {
                "enabled": False,
                "path": None
            }
        }
    }


def strip_group_phrase(text):
    text = text.strip()
    text = re.sub(r"\s+in\s+group\s+[a-zA-Z0-9_ -]+$", "", text).strip()
    text = re.sub(r"\s+to\s+group\s+[a-zA-Z0-9_ -]+$", "", text).strip()
    return text


def target_text_from_add_command(text, placement):
    text = text.lower().strip()

    if placement == "on_top_of":
        marker = "on top of"
        if marker in text:
            return strip_group_phrase(text.split(marker, 1)[1])

    if placement == "right_of":
        for marker in ("to the right of", "right of"):
            if marker in text:
                return strip_group_phrase(text.split(marker, 1)[1])

    return strip_group_phrase(text)


def resolve_target(scene_ir, prompt, prefer_color=None, group_name=None):
    text = prompt.lower()

    items = collect_mesh_objects_with_groups(scene_ir)
    mode = reference_mode_from_text(text)

    target_shape = shape_from_text(text)
    target_color = prefer_color or color_name_from_text(text)

    if group_name is None:
        group_name = group_name_from_text(text)

    if group_name:
        group_node = find_group(scene_ir, group_name)
        if group_node is None:
            print("[controller] Target group not found:", group_name)
            return None, None

        items = [
            (node, parent_group)
            for node, parent_group in items
            if parent_group is group_node
        ]

    if mode == "most_recent":
        target_shape = None
        target_color = None

    candidates = [node for node, parent_group in items]

    if target_shape:
        candidates = [
            node for node in candidates
            if str(node.get("shape", "")).lower() == target_shape
        ]

    if target_color:
        expected = color_value(target_color)
        candidates = [
            node for node in candidates
            if color_matches(node.get("material", {}).get("color"), expected)
        ]

    if not candidates:
        print("[controller] Target resolution failed.")
        print("[controller] prompt:", prompt)
        print("[controller] requested shape:", target_shape)
        print("[controller] requested color:", target_color)
        print("[controller] requested group:", group_name)
        print("[controller] reference mode:", mode)
        return None, None

    ordered = sort_targets_for_reference(candidates, mode)
    chosen = ordered[0]

    parent_group = None
    for node, group in items:
        if node is chosen:
            parent_group = group
            break

    if len(ordered) > 1:
        print("[controller] Multiple targets matched.")
        print("[controller] reference mode:", mode)
        print("[controller] candidates:", [node.get("name") for node in ordered])
        print("[controller] chose:", chosen.get("name"))

    print("[controller] Resolved target object name:", chosen.get("name"))
    print("[controller] Resolved target object id:", chosen.get("id"))
    print("[controller] Resolved target shape:", chosen.get("shape"))

    if parent_group is not None:
        print("[controller] Resolved target group:", parent_group.get("name"))

    return chosen, parent_group


def remove_node_by_id(node, target_id):
    children = node.get("children")

    if not isinstance(children, list):
        return False

    for index, child in enumerate(list(children)):
        if isinstance(child, dict) and child.get("id") == target_id:
            del children[index]
            return True

        if isinstance(child, dict) and remove_node_by_id(child, target_id):
            return True

    return False


# --- Legacy fallback: rule-based parser ---
# Used in handle_pending_ai_request when both cache lookup and LLM call fail.
# Not part of the primary (cache → LLM → validate → apply) execution path.
def parse_command(prompt):
    text = prompt.lower().strip()
    group_name = group_name_from_text(text)

    if "new scene" in text:
        return {"type": "new_scene"}

    if "save" in text and "scene" in text:
        m = re.search(r"\bsave\s+(?:scene\s+)?(?:as\s+)?([a-zA-Z0-9_]+)", text)
        raw = m.group(1) if m else None
        scene_name = raw if raw and raw not in ("scene", "as") else None
        return {"type": "save_scene", "scene_name": scene_name}

    if "load" in text and "scene" in text:
        m = re.search(r"\bload\s+(?:scene\s+)?([a-zA-Z0-9_]+)", text)
        return {"type": "load_scene", "scene_name": m.group(1) if m else None}

    if "create" in text and "group" in text:
        return {
            "type": "create_group",
            "group_name": group_name
        }

    if "delete" in text or "remove" in text:
        return {
            "type": "delete",
            "target_color": color_name_from_text(text),
            "group_name": group_name
        }

    if "move" in text:
        if "group" in text:
            return {
                "type": "move_group",
                "group_name": group_name,
                "direction": direction_from_text(text),
            }

        return {
            "type": "move",
            "direction": direction_from_text(text),
            "target_color": color_name_from_text(text),
            "group_name": group_name
        }

    if "change" in text and "color" in text:
        color = None
        match = re.search(r"\bto\s+([a-z]+)\b", text)

        if match and match.group(1) in COLOR_TABLE:
            color = match.group(1)

        if color is None:
            color = color_name_from_text(text)

        return {
            "type": "change_color",
            "new_color": color,
            "group_name": group_name
        }

    if "ring" in text:
        object_type = shape_from_text(text) or "cube"
        m_n = re.search(r"\b(\d+)\s+(?:objects?|" + object_type + r"s?)\b", text)
        if not m_n:
            m_n = re.search(r"\bof\s+(\d+)\b", text)
        count = int(m_n.group(1)) if m_n else 8
        m_r = re.search(r"\bradius\s*[=:]?\s*(\d+(?:\.\d+)?)\b", text)
        radius = float(m_r.group(1)) if m_r else 2.5
        return {
            "type": "generate_pattern",
            "pattern": "ring",
            "object_type": object_type,
            "count": count,
            "radius": radius,
            "color": color_name_from_text(text) or "purple",
        }

    if "tree" in text and ("with" in text or shape_from_text(text)):
        object_type = shape_from_text(text) or "cube"
        return {
            "type": "generate_composite",
            "composite": "tree",
            "object_type": object_type,
            "color": color_name_from_text(text) or "green",
        }

    if "prefab" in text:
        m = re.search(r"\bprefab\s+([a-zA-Z0-9_]+)", text)
        prefab_name = m.group(1) if m else None
        return {"type": "add_prefab", "prefab_name": prefab_name}

    if "add" in text or "create" in text or "cube" in text:
        placement = "next_free"

        if "on top of" in text or "πάνω" in text or "πανω" in text:
            placement = "on_top_of"
        elif "to the right of" in text or "right of" in text:
            placement = "right_of"

        return {
            "type": "add_cube",
            "color": color_name_from_text(text),
            "placement": placement,
            "group_name": group_name,
            "target_text": target_text_from_add_command(text, placement)
        }

    return {"type": "unknown"}


def command_to_action(command):
    # Converts a parse_command result into the canonical action schema.
    t = command.get("type")
    if t == "new_scene":
        return {"action": "new_scene"}
    if t == "save_scene":
        return {"action": "save_scene", "scene_name": command.get("scene_name")}
    if t == "add_cube":
        placement_str = command.get("placement", "next_free")
        if placement_str == "right_of":
            placement = {"relation": "right_of", "target": command.get("target_text", "")}
        elif placement_str == "on_top_of":
            placement = {"relation": "on_top_of", "target": command.get("target_text", "")}
        else:
            placement = {"relation": "next_free_slot"}
        return {
            "action": "add_object",
            "object_type": "cube",
            "color": command.get("color") or "purple",
            "placement": placement
        }
    if t == "delete":
        return {
            "action": "delete_object",
            "target": command.get("target_color") or "cube"
        }
    if t == "move":
        return {
            "action": "move_object",
            "target": command.get("target_color") or "cube",
            "direction": command.get("direction") or "right",
        }
    if t == "change_color":
        return {
            "action": "recolor_object",
            "target": "cube",
            "color": command.get("new_color") or "purple"
        }
    if t == "create_group":
        return {"action": "create_group", "group_name": command.get("group_name")}
    if t == "load_scene":
        return {"action": "load_scene", "scene_name": command.get("scene_name")}
    if t == "add_prefab":
        return {"action": "add_prefab", "prefab_name": command.get("prefab_name")}
    if t == "generate_pattern":
        return {
            "action": "generate_pattern",
            "pattern": command.get("pattern", "ring"),
            "object_type": command.get("object_type", "cube"),
            "count": command.get("count", 8),
            "radius": command.get("radius", 2.5),
            "color": command.get("color") or "purple",
        }
    if t == "generate_composite":
        return {
            "action": "generate_composite",
            "composite": command.get("composite", "tree"),
            "object_type": command.get("object_type", "cube"),
            "color": command.get("color") or "green",
        }
    raise ValueError("Unknown rule-based command type: " + str(t))

# --- End legacy fallback ---


def find_node_by_id(scene_ir, object_id):
    if not object_id:
        return None

    object_id = str(object_id)

    for node in collect_mesh_objects(scene_ir):
        if str(node.get("id", "")) == object_id:
            return node

    return None



def load_history_stack():
    stack = read_json(HISTORY_STACK_FILE, default=[])

    if isinstance(stack, list):
        return stack

    return []


def save_history_stack(stack):
    write_json(HISTORY_STACK_FILE, stack)


def push_history_state(reason):
    current = read_json(SCENE_IR_FILE, default=None)

    if not isinstance(current, dict):
        return

    filename = "scene_ir_{0}_{1}.json".format(int(time.time() * 1000), reason)
    history_path = HISTORY_DIR / filename

    write_json(history_path, current)

    stack = load_history_stack()
    stack.append(filename)
    save_history_stack(stack)

    print("[controller] Pushed undo history:", history_path)


def pop_history_state():
    stack = load_history_stack()

    while stack:
        filename = stack.pop()
        history_path = HISTORY_DIR / filename

        if history_path.exists():
            save_history_stack(stack)
            return read_json(history_path, default=None)

    save_history_stack(stack)
    return None


def save_preview_ir(scene_ir):
    scene_ir = ensure_stable_object_ids(scene_ir)
    write_json(PREVIEW_IR_FILE, scene_ir)

    print("[controller] official scene_ir path used:", SCENE_IR_FILE)
    print("[controller] preview scene_ir path used:", PREVIEW_IR_FILE)


def save_preview_script(scene_ir):
    write_text_atomic(PREVIEW_SCENE_FILE, generate_scene_script(scene_ir))
    print("[controller] Saved preview script to:", PREVIEW_SCENE_FILE)


def promote_preview_files_exactly():
    if not PREVIEW_IR_FILE.exists():
        raise FileNotFoundError("Missing preview_scene_ir.json")

    if not PREVIEW_SCENE_FILE.exists():
        raise FileNotFoundError("Missing preview_scene.py")

    push_history_state("apply")

    copy_file_atomic(PREVIEW_IR_FILE, SCENE_IR_FILE)
    copy_file_atomic(PREVIEW_SCENE_FILE, SCENE_OUT_FILE)

    print("[controller] Promoted exact preview IR to:", SCENE_IR_FILE)
    print("[controller] Promoted exact preview script to:", SCENE_OUT_FILE)


def backup_official_scene_ir(reason):
    current = read_json(SCENE_IR_FILE, default=None)

    if not isinstance(current, dict):
        raise ValueError("No official scene_ir.json available to save.")

    filename = "scene_ir_{0}_{1}.json".format(now_timestamp(), reason)
    backup_path = SAVED_SCENES_DIR / filename

    write_json(backup_path, current)

    print("[controller] Saved scene backup:", backup_path)
    return backup_path


def save_named_scene(scene_ir, name):
    safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", str(name).strip().lower()).strip("_")
    if not safe_name:
        safe_name = "scene_" + now_timestamp()
    path = SAVED_SCENES_DIR / (safe_name + ".json")
    write_json(path, scene_ir)
    print("[controller] Saved named scene:", path)
    return path, safe_name


def initialize_load_scene(scene_name, request_id=None):
    if not scene_name:
        raise ValueError("No scene name provided for load.")

    safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", str(scene_name).strip().lower()).strip("_")
    if not safe_name:
        raise ValueError("Invalid scene name.")

    path = SAVED_SCENES_DIR / (safe_name + ".json")

    if not path.exists():
        raise FileNotFoundError("Saved scene not found: " + safe_name)

    scene_ir = read_json(path, default=None)
    if not isinstance(scene_ir, dict):
        raise ValueError("Saved scene file is corrupted: " + safe_name)

    scene_ir = ensure_stable_object_ids(scene_ir)

    clear_preview_files()
    clear_history_files()

    write_json(SCENE_IR_FILE, scene_ir)
    write_text_atomic(SCENE_OUT_FILE, generate_scene_script(scene_ir))

    reset_request_and_ui_files(
        status="scene_loaded",
        message="Scene loaded: " + safe_name,
        request_id=request_id
    )

    write_scene_state("official", SCENE_OUT_FILE, request_id=request_id)

    print("[controller] Loaded scene:", safe_name)
    print("[controller] From:", path)


def handle_load_scene(ui):
    scene_name = ui.get("scene_name") or ui.get("name")
    request_id = ui.get("request_id")

    try:
        initialize_load_scene(scene_name, request_id=request_id)
    except FileNotFoundError as e:
        write_status(
            "load_failed",
            "Scene not found: " + str(scene_name or "(none)"),
            request_id=request_id,
            error=str(e)
        )
        write_json(UI_STATE_FILE, {
            "action": "idle",
            "request_id": request_id,
            "updated_at": time.time()
        })
        print("[controller] Load failed:", e)


def find_prefab_by_name(name):
    safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", str(name).strip().lower()).strip("_")
    if not safe_name:
        return None
    path = PREFABS_DIR / (safe_name + ".json")
    return path if path.exists() else None


def load_prefab(name):
    path = find_prefab_by_name(name)
    if path is None:
        raise FileNotFoundError("Prefab not found: " + str(name))
    data = read_json(path, default=None)
    if not isinstance(data, dict):
        raise ValueError("Prefab file is corrupted: " + str(name))
    return data


def instantiate_prefab(scene_ir, prefab_ir, position=None):
    instance = deepcopy(prefab_ir)

    base_name = str(instance.get("name", "prefab"))
    unique_name = make_unique_name(scene_ir, base_name)

    instance["name"] = unique_name
    instance["id"] = unique_name
    instance["created_order"] = next_object_order(scene_ir)

    if position is None:
        position = find_next_free_world_position(scene_ir)
    instance.setdefault("transform", {})["position"] = [
        float(position[0]), float(position[1]), float(position[2])
    ]
    instance["transform"].setdefault("scale", [1.0, 1.0, 1.0])

    def suffix_children(node, prefix):
        for child in node.get("children", []):
            if not isinstance(child, dict):
                continue
            old = str(child.get("name", "node"))
            tail = old[len(base_name) + 1:] if old.startswith(base_name + "_") else old
            child["name"] = prefix + "_" + tail
            child["id"] = child["name"]
            suffix_children(child, prefix)

    suffix_children(instance, unique_name)

    ensure_scene_children(scene_ir).append(instance)
    ensure_stable_object_ids(scene_ir)
    return scene_ir


def seed_builtin_prefabs():
    PREFABS_DIR.mkdir(parents=True, exist_ok=True)

    seeds = {
        "house": build_house("house", [0.0, 0.0, 0.0]),
        "tree": build_tree("tree", [0.0, 0.0, 0.0]),
        "gift_box": build_gift_box("gift_box", [0.0, 0.0, 0.0]),
        "street_light": build_street_light("street_light", [0.0, 0.0, 0.0]),
    }

    for name, ir in seeds.items():
        path = PREFABS_DIR / (name + ".json")
        if not path.exists():
            write_json(path, ir)
            print("[controller] Seeded prefab:", name, "->", path)


_OPEN_COMPOSITE_SKIP = frozenset(SHAPE_WORDS) | {
    "ring", "tree", "table", "lamp", "scene", "prefab", "object", "objects",
}

_MAKE_VERB_RE = re.compile(
    r"\b(?:make|create|build|generate|draw)\s+(?:a|an)\s+(\w+)\b"
)


def detect_procedural_action(prompt):
    """Map explicit procedural / composite prompts to a structured action dict
    without touching the cache or the general LLM action-router.

    Known deterministic composites are returned fully resolved.
    Unknown object names are returned with composite='open' so that
    handle_pending_ai_request can call parse_composite_spec_with_llm to fill
    in the parts array before apply_action_to_ir is called.

    Returns an action dict, or None if the prompt is not a recognised
    procedural pattern.
    """
    text = prompt.lower().strip()

    # ---- ring ----
    if re.search(r"\bring\b", text):
        object_type = shape_from_text(text) or "cube"
        m_n = re.search(r"\bof\s+(\d+)\b", text)
        if not m_n:
            m_n = re.search(r"\b(\d+)\s+(?:objects?|" + re.escape(object_type) + r"s?)\b", text)
        count = int(m_n.group(1)) if m_n else 8
        m_r = re.search(r"\bradius\s*[=:]?\s*(\d+(?:\.\d+)?)\b", text)
        radius = float(m_r.group(1)) if m_r else 2.5
        return {
            "action": "generate_pattern",
            "pattern": "ring",
            "object_type": object_type,
            "count": count,
            "radius": radius,
            "color": color_name_from_text(text) or "purple",
        }

    # ---- deterministic tree ----
    if re.search(r"\btree\b", text) and (
        re.search(r"\bwith\b", text) or
        re.search(r"\bof\b", text) or
        shape_from_text(text)
    ):
        object_type = shape_from_text(text) or "cube"
        return {
            "action": "generate_composite",
            "composite": "tree",
            "object_type": object_type,
            "color": color_name_from_text(text) or "green",
        }

    # ---- deterministic table ----
    if re.search(r"\btable\b", text):
        object_type = shape_from_text(text) or "cube"
        return {
            "action": "generate_composite",
            "composite": "table",
            "object_type": object_type,
            "color": color_name_from_text(text) or "white",
        }

    # ---- deterministic lamp ----
    if re.search(r"\blamp\b", text):
        object_type = shape_from_text(text) or "cube"
        return {
            "action": "generate_composite",
            "composite": "lamp",
            "object_type": object_type,
            "color": color_name_from_text(text) or "yellow",
        }

    # ---- open-ended composite ----
    # Catches "make/create/build/generate a <noun>" where <noun> is not a
    # shape, ring, tree, table, lamp, or other reserved word.
    m = _MAKE_VERB_RE.search(text)
    if m:
        noun = m.group(1)
        if noun not in _OPEN_COMPOSITE_SKIP:
            primitive_type = shape_from_text(text) or "cube"
            return {
                "action": "generate_composite",
                "composite": "open",
                "object_name": noun,
                "primitive_type": primitive_type,
                "color": color_name_from_text(text) or "white",
            }

    return None


def handle_pending_ai_request():
    req = read_json(AI_REQUEST_FILE, default=None)
    if not req:
        return

    if req.get("status") != "pending":
        return

    print("[controller] AI request found:", req)

    request_id = req.get("request_id")
    prompt = req.get("prompt", "").strip()

    if not prompt:
        req["status"] = "error"
        req["error"] = "Empty prompt"
        write_json(AI_REQUEST_FILE, req)
        return

    try:
        scene_ir = ensure_shared_scene_ir()

        action = None
        action_source = None

        procedural_action = detect_procedural_action(prompt)
        if procedural_action is not None:
            try:
                validate_action(procedural_action)
                action = procedural_action
                action_source = "procedural_detector"
                print("[controller] Action source: procedural_detector")
                print("[controller] Procedural action:", action.get("action"))
            except Exception as proc_err:
                print("[controller] Procedural detector produced invalid action:", proc_err)

        if action is None:
            cached_action = lookup_cached_action(prompt)
            if cached_action is not None:
                try:
                    validate_action(cached_action)
                    action = cached_action
                    action_source = "cache"
                    print("[controller] Action source: cache")
                    print("[controller] Cached action:", action.get("action"))
                except Exception as cache_err:
                    print("[controller] Ignoring invalid cached action:", cache_err)

        if action is None:
            try:
                action = parse_prompt_to_action_with_llm(prompt, scene_ir)
                validate_action(action)
                store_cached_action(prompt, action)
                action_source = "llm"
                print("[controller] Action source: LLM")
                print("[controller] LLM action:", action.get("action"))
            except Exception as llm_err:
                print("[controller] LLM failed, using rule-based fallback:", llm_err)
                command = parse_command(prompt)
                action = command_to_action(command)
                validate_action(action)
                action_source = "fallback rule-based parser"
                print("[controller] Action source: fallback rule-based parser")
                print("[controller] Fallback action:", action.get("action"))

        action = normalize_action(action)

        # Resolve open-ended composite: the detector returned composite='open'
        # without a parts list; ask the LLM now with a focused design prompt.
        if (action.get("action") == "generate_composite"
                and action.get("composite") == "open"
                and action.get("parts") is None):
            object_name = action.get("object_name", "object")
            primitive_type = action.get("primitive_type", "cube")
            print("[controller] Resolving open composite '{}' via LLM".format(object_name))
            try:
                parts = parse_composite_spec_with_llm(object_name, primitive_type)
                parts = resolve_composite_overlaps(parts)
                validate_composite_parts(parts)
                action = dict(action)
                action["parts"] = parts
                print("[controller] Composite spec resolved: {} parts".format(len(parts)))
            except Exception as spec_err:
                raise ValueError(
                    "Could not generate composite for '{}': {}".format(object_name, spec_err)
                )

        if action.get("action") == "new_scene":
            initialize_new_scene(request_id=request_id)
            return

        if action.get("action") == "save_scene":
            handle_save_scene({"request_id": request_id, "scene_name": action.get("scene_name")})
            return

        if action.get("action") == "load_scene":
            handle_load_scene({"request_id": request_id, "scene_name": action.get("scene_name")})
            return

        if action.get("action") == "undo":
            handle_undo({"request_id": request_id})
            return

        preview_ir = apply_action_to_ir(scene_ir, action)

        save_preview_ir(preview_ir)
        save_preview_script(preview_ir)

        req["status"] = "preview_ready"
        req["message"] = "Ξ¤ΞΏ preview Ξ΄Ξ·ΞΌΞΉΞΏΟ…ΟΞ³Ξ®ΞΈΞ·ΞΊΞµ."
        req["preview_file"] = PREVIEW_SCENE_FILE.name
        req["preview_ir_file"] = PREVIEW_IR_FILE.name
        req["parsed_action"] = action
        req["action_source"] = action_source
        write_json(AI_REQUEST_FILE, req)

        write_json(SCENE_STATE_FILE, {
            "mode": "preview",
            "active_script": str(PREVIEW_SCENE_FILE),
            "request_id": request_id
        })

        print("[controller] Preview ready for request", request_id)

    except Exception as e:
        clear_preview_files()
        try:
            write_scene_state("official", SCENE_OUT_FILE, request_id=request_id)
        except Exception as _wse:
            print(f"[controller] handle_pending_ai_request: write_scene_state failed: {_wse}")
        try:
            write_json(UI_STATE_FILE, {
                "action": "idle",
                "request_id": request_id,
                "updated_at": time.time()
            })
        except Exception as _uie:
            print(f"[controller] handle_pending_ai_request: UI_STATE_FILE write failed: {_uie}")
        req["status"] = "error"
        req["error"] = str(e)
        try:
            write_json(AI_REQUEST_FILE, req)
        except Exception as _rfe:
            print(f"[controller] handle_pending_ai_request: AI_REQUEST_FILE write failed: {_rfe}")
        print("[controller] Error while handling request:")
        traceback.print_exc()


def handle_apply(ui):
    request_id = ui.get("request_id")

    if not PREVIEW_IR_FILE.exists() or not PREVIEW_SCENE_FILE.exists():
        write_json(UI_STATE_FILE, {
            "action": "error",
            "message": "Preview files missing; cannot apply.",
            "request_id": request_id,
            "updated_at": time.time()
        })
        write_status("error", "Preview files missing; cannot apply.", request_id=request_id)
        print("[controller] Apply aborted: preview files missing.")
        return

    promote_preview_files_exactly()

    write_json(UI_STATE_FILE, {
        "action": "idle",
        "request_id": request_id,
        "updated_at": time.time()
    })

    write_status("applied", "Applied.", request_id=request_id)
    write_scene_state("official", SCENE_OUT_FILE, request_id=request_id)
    clear_preview_files()

    print("[controller] Preview applied.")


def handle_reject(ui):
    request_id = ui.get("request_id")

    clear_preview_files()

    write_json(UI_STATE_FILE, {
        "action": "idle",
        "request_id": request_id,
        "updated_at": time.time()
    })

    write_status("rejected", "Rejected.", request_id=request_id)
    write_scene_state("official", SCENE_OUT_FILE, request_id=request_id)

    print("[controller] Preview rejected.")


def handle_undo(ui):
    request_id = ui.get("request_id")
    previous_ir = pop_history_state()

    if not isinstance(previous_ir, dict):
        raise ValueError("No undo history available.")

    previous_ir = ensure_stable_object_ids(previous_ir)

    write_json(SCENE_IR_FILE, previous_ir)
    write_text_atomic(SCENE_OUT_FILE, generate_scene_script(previous_ir))

    clear_preview_files()

    write_json(UI_STATE_FILE, {
        "action": "idle",
        "request_id": request_id,
        "updated_at": time.time()
    })

    write_status("undone", "Undo restored previous scene.", request_id=request_id)
    write_scene_state("official", SCENE_OUT_FILE, request_id=request_id)

    print("[controller] Undo restored previous official scene.")


def handle_new_scene(ui):
    request_id = ui.get("request_id")
    initialize_new_scene(request_id=request_id)


def handle_save_scene(ui):
    request_id = ui.get("request_id")
    scene_name = ui.get("scene_name") or ui.get("name")
    scene_state = read_json(SCENE_STATE_FILE, default={}) or {}

    if scene_state.get("mode") == "preview":
        write_json(UI_STATE_FILE, {
            "action": "idle",
            "request_id": request_id,
            "updated_at": time.time()
        })

        write_status(
            "save_blocked_preview",
            "Save blocked because preview is active. Apply or Reject first.",
            request_id=request_id
        )

        print("[controller] Save blocked: preview mode is active.")
        return

    scene_ir = ensure_shared_scene_ir()
    write_json(SCENE_IR_FILE, scene_ir)
    write_text_atomic(SCENE_OUT_FILE, generate_scene_script(scene_ir))

    backup_path = backup_official_scene_ir("manual_save")

    named_path = None
    safe_name = None
    if scene_name:
        named_path, safe_name = save_named_scene(scene_ir, scene_name)

    write_json(UI_STATE_FILE, {
        "action": "idle",
        "request_id": request_id,
        "updated_at": time.time()
    })

    if named_path:
        status_message = "Scene saved as '" + safe_name + "'. Backup: " + backup_path.name
    else:
        status_message = "Scene saved. Backup: " + backup_path.name

    write_status("scene_saved", status_message, request_id=request_id)
    write_scene_state("official", SCENE_OUT_FILE, request_id=request_id)

    print("[controller] Scene saved.")
    if named_path:
        print("[controller] Named save:", named_path)
    print("[controller] Current official scene path:", SCENE_OUT_FILE)


def handle_ui_actions():
    ui = read_json(UI_STATE_FILE, default=None)

    if not isinstance(ui, dict):
        return

    action = ui.get("action")

    if action in (None, "idle", "error"):
        return

    print("[controller] UI action found:", ui)

    try:
        if action == "apply":
            handle_apply(ui)
        elif action == "reject":
            handle_reject(ui)
        elif action == "undo":
            handle_undo(ui)
        elif action == "new_scene":
            handle_new_scene(ui)
        elif action == "save_scene":
            handle_save_scene(ui)
        elif action == "load_scene":
            handle_load_scene(ui)
        else:
            write_json(UI_STATE_FILE, {
                "action": "error",
                "message": "Unknown action: " + str(action),
                "updated_at": time.time()
            })

    except Exception as e:
        try:
            write_json(UI_STATE_FILE, {
                "action": "error",
                "message": str(e),
                "updated_at": time.time()
            })
        except Exception as _uie:
            print(f"[controller] handle_ui_actions: UI_STATE_FILE write failed: {_uie}")
        try:
            write_status("error", error=str(e), request_id=ui.get("request_id"))
        except Exception as _wse:
            print(f"[controller] handle_ui_actions: write_status failed: {_wse}")
        try:
            write_scene_state("official", SCENE_OUT_FILE, request_id=ui.get("request_id"))
        except Exception as _sse:
            print(f"[controller] handle_ui_actions: write_scene_state failed: {_sse}")

        print("[controller] UI action error:", e)
        traceback.print_exc()


def validate_action(action):
    if not isinstance(action, dict):
        raise ValueError("Parsed action must be a dictionary")

    if "action" not in action:
        raise ValueError("Parsed action missing 'action'")

    allowed_single = {
        "add_object",
        "move_object",
        "delete_object",
        "recolor_object",
        "scale_object",
        "new_scene",
        "save_scene",
        "load_scene",
        "add_prefab",
        "undo",
        "generate_pattern",
        "generate_composite",
    }

    action_name = action.get("action")

    if action_name in allowed_single:
        return

    if action_name == "action_sequence":
        sequence = action.get("action_sequence")

        if not isinstance(sequence, list) or not sequence:
            raise ValueError("action_sequence must be a non-empty list")

        for step in sequence:
            if not isinstance(step, dict):
                raise ValueError("Each action_sequence step must be a dictionary")

            step_name = step.get("action")
            if step_name == "action_sequence":
                raise ValueError("Nested action_sequence is not supported")

            validate_action(step)

        return

    raise ValueError("Unsupported action: " + str(action_name))


def normalize_action(action):
    if not isinstance(action, dict):
        return action

    action = dict(action)

    # Canonical identity field
    if "object_id" in action and "id" not in action:
        action["id"] = action.pop("object_id")

    # Canonical scene_name field (LLM sometimes returns "name")
    if action.get("action") in ("save_scene", "load_scene"):
        if "name" in action and "scene_name" not in action:
            action["scene_name"] = action.pop("name")

    # Canonical prefab_name field (LLM sometimes returns "name")
    if action.get("action") == "add_prefab":
        if "name" in action and "prefab_name" not in action:
            action["prefab_name"] = action.pop("name")

    # Canonical position field
    if "new_position" in action and "position" not in action:
        action["position"] = action.pop("new_position")

    # Canonical direction for move_object
    if action.get("action") == "move_object" and "direction" in action:
        raw = str(action["direction"]).lower().strip()
        action["direction"] = _DIRECTION_WORD_MAP.get(raw, raw)

    # Recurse into action_sequence steps
    if action.get("action") == "action_sequence" and isinstance(action.get("action_sequence"), list):
        action["action_sequence"] = [normalize_action(step) for step in action["action_sequence"]]

    return action


def describe_node(node):
    material = node.get("material", {})
    color = material.get("color", [0.8, 0.0, 0.8])
    shape = str(node.get("shape", "object"))
    name = str(node.get("name", ""))

    color_name = "unknown"
    for key, value in COLOR_TABLE.items():
        if value == color:
            color_name = key
            break

    return {
        "name": name,
        "shape": shape,
        "color_name": color_name
    }


def _node_created_order(node):
    try:
        return int(node.get("created_order", 0))
    except Exception:
        return 0


def resolve_target_node_with_group(scene_ir, target_text):
    if not target_text:
        return None, None

    target_text = str(target_text).lower().strip()
    all_nodes = collect_mesh_objects_with_groups(scene_ir)

    # Priority 1: exact id match
    for node, parent_group in all_nodes:
        if str(node.get("id", "")).lower() == target_text:
            print("[controller] Resolved target by id:", target_text, "->", node.get("name"))
            return node, parent_group

    # Priority 2: exact name match
    for node, parent_group in all_nodes:
        if str(node.get("name", "")).lower() == target_text:
            print("[controller] Resolved target by name:", target_text, "->", node.get("name"))
            return node, parent_group

    # Determine preferred order from reference words in target_text
    ref_mode = reference_mode_from_text(target_text)
    prefer_last = ref_mode in ("last", "most_recent")

    def pick_best(candidates):
        candidates.sort(key=lambda item: _node_created_order(item[0]), reverse=prefer_last)
        node, pg = candidates[0]
        return node, pg

    # Extract color and shape tokens from target_text
    target_color = None
    for color_name in COLOR_TABLE:
        if re.search(r"\b" + re.escape(color_name) + r"\b", target_text):
            target_color = color_name
            break

    target_shape = None
    for shape in SHAPE_WORDS:
        if re.search(r"\b" + re.escape(shape) + r"\b", target_text):
            target_shape = shape
            break

    # Priority 3: color + shape match
    if target_color and target_shape:
        expected_rgb = COLOR_TABLE[target_color]
        candidates = [
            (node, pg) for node, pg in all_nodes
            if str(node.get("shape", "")).lower() == target_shape
            and color_matches(node.get("material", {}).get("color"), expected_rgb)
        ]
        if candidates:
            node, pg = pick_best(candidates)
            print("[controller] Resolved target by color+shape:", target_text, "->", node.get("name"))
            return node, pg

    # Priority 4: shape-only match
    if target_shape:
        candidates = [
            (node, pg) for node, pg in all_nodes
            if str(node.get("shape", "")).lower() == target_shape
        ]
        if candidates:
            node, pg = pick_best(candidates)
            print("[controller] Resolved target by shape:", target_text, "->", node.get("name"))
            return node, pg

    # Priority 5: color-only match
    if target_color:
        expected_rgb = COLOR_TABLE[target_color]
        candidates = [
            (node, pg) for node, pg in all_nodes
            if color_matches(node.get("material", {}).get("color"), expected_rgb)
        ]
        if candidates:
            node, pg = pick_best(candidates)
            print("[controller] Resolved target by color:", target_text, "->", node.get("name"))
            return node, pg

    print("[controller] Could not resolve target:", target_text)
    return None, None


def resolve_target_node(scene_ir, target_text):
    node, parent_group = resolve_target_node_with_group(scene_ir, target_text)
    return node

def normalize_action_position(value, field_name):
    if value is None:
        return None

    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(field_name + " must be a list/tuple of length 3")

    return [float(value[0]), float(value[1]), float(value[2])]


def normalize_action_scale(value, default_scale=None):
    if value is None:
        if default_scale is None:
            return [1.0, 1.0, 1.0]
        return [
            float(default_scale[0]),
            float(default_scale[1]),
            float(default_scale[2])
        ]

    if isinstance(value, (int, float)):
        factor = float(value)
        return [factor, factor, factor]

    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError("scale must be a number or a list/tuple of length 3")

    return [float(value[0]), float(value[1]), float(value[2])]


def resolve_target_node_by_identity(scene_ir, identity_value):
    if identity_value is None:
        return None, None

    wanted = str(identity_value).strip()
    if not wanted:
        return None, None

    for node, parent_group in collect_mesh_objects_with_groups(scene_ir):
        node_id = str(node.get("id", "")).strip()
        node_name = str(node.get("name", "")).strip()

        if wanted == node_id or wanted == node_name:
            print("[controller] Resolved identity:", wanted, "->", node.get("name"))
            return node, parent_group

    return None, None


def resolve_action_target_node(scene_ir, action):
    object_ids = action.get("object_ids")
    if isinstance(object_ids, list):
        for object_id in object_ids:
            node, parent_group = resolve_target_node_by_identity(scene_ir, object_id)
            if node is not None:
                return node, parent_group

    for key in ("object_id", "id", "name"):
        node, parent_group = resolve_target_node_by_identity(scene_ir, action.get(key))
        if node is not None:
            return node, parent_group

    target_text = action.get("target")
    if target_text:
        return resolve_target_node_with_group(scene_ir, target_text)

    return None, None


def color_name_to_rgb(name):
    return COLOR_TABLE.get(str(name).lower(), [0.8, 0.0, 0.8])


_VALID_COMPOSITE_SHAPES = frozenset(SHAPE_WORDS)


def validate_composite_parts(parts):
    """Raise ValueError if *parts* does not conform to the composite parts schema."""
    if not isinstance(parts, list) or len(parts) == 0:
        raise ValueError("Composite parts must be a non-empty list")
    if len(parts) > 20:
        raise ValueError("Composite parts list too long (max 20, got {})".format(len(parts)))

    seen_names = set()
    for i, part in enumerate(parts):
        if not isinstance(part, dict):
            raise ValueError("Part {} must be a dict, got {}".format(i, type(part).__name__))

        name = part.get("name")
        if not name or not isinstance(name, str):
            raise ValueError("Part {} missing required 'name' field".format(i))
        if name in seen_names:
            raise ValueError("Duplicate part name: '{}'".format(name))
        seen_names.add(name)

        shape = str(part.get("shape", "")).lower()
        if shape not in _VALID_COMPOSITE_SHAPES:
            raise ValueError(
                "Part '{}' has invalid shape '{}'. Allowed: {}".format(
                    name, shape, ", ".join(sorted(_VALID_COMPOSITE_SHAPES))
                )
            )

        pos = part.get("position")
        if not isinstance(pos, list) or len(pos) != 3:
            raise ValueError("Part '{}' position must be [x, y, z], got {}".format(name, pos))
        try:
            [float(v) for v in pos]
        except (TypeError, ValueError):
            raise ValueError("Part '{}' position values must be numbers".format(name))

        scale = part.get("scale")
        if not isinstance(scale, list) or len(scale) != 3:
            raise ValueError("Part '{}' scale must be [sx, sy, sz], got {}".format(name, scale))
        for j, s in enumerate(scale):
            try:
                sv = float(s)
            except (TypeError, ValueError):
                raise ValueError("Part '{}' scale[{}] must be a number".format(name, j))
            if sv <= 0:
                raise ValueError("Part '{}' scale[{}] must be positive, got {}".format(name, j, sv))


def resolve_composite_overlaps(parts, max_iterations=30, min_gap=0.05):
    """Push apart any axis-aligned bounding boxes that overlap.

    Strategy per overlapping pair:
    - Find the axis of minimum penetration depth.
    - On the Y axis, push the higher part upward only (the lower part may be
      ground-resting and cannot go down).
    - On X and Z axes, split the push evenly between the two parts.
    - After moving, clamp every part so its bottom (y - sy/2) stays at y >= 0.

    Returns a new list with adjusted positions; scales are never changed.
    Converges in O(n^2 * max_iterations) steps; in practice one or two
    passes suffice for 3-8 part objects.
    """
    parts = deepcopy(parts)
    n = len(parts)

    for _pass in range(max_iterations):
        any_moved = False

        for i in range(n):
            for j in range(i + 1, n):
                pi = [float(v) for v in parts[i]["position"]]
                si = [float(v) for v in parts[i]["scale"]]
                pj = [float(v) for v in parts[j]["position"]]
                sj = [float(v) for v in parts[j]["scale"]]

                # Per-axis overlap: positive means the boxes intersect on that axis
                ov = []
                for ax in range(3):
                    ov.append(
                        min(pi[ax] + si[ax] / 2.0, pj[ax] + sj[ax] / 2.0)
                        - max(pi[ax] - si[ax] / 2.0, pj[ax] - sj[ax] / 2.0)
                    )

                if not all(o > 1e-6 for o in ov):
                    continue  # no intersection — nothing to do

                # Choose axis of minimum penetration
                min_ax = int(min(range(3), key=lambda a: ov[a]))
                push = ov[min_ax] + min_gap

                if min_ax == 1:
                    # Vertical: push the higher-centre part upward only so the
                    # lower part is not forced below ground.
                    if pj[1] >= pi[1]:
                        pj[1] += push
                    else:
                        pi[1] += push
                else:
                    # Horizontal: split evenly
                    if pj[min_ax] >= pi[min_ax]:
                        pj[min_ax] += push / 2.0
                        pi[min_ax] -= push / 2.0
                    else:
                        pj[min_ax] -= push / 2.0
                        pi[min_ax] += push / 2.0

                # Ground clamp — bottom of each part must stay at or above y=0
                for p, s in ((pi, si), (pj, sj)):
                    floor = s[1] / 2.0
                    if p[1] < floor:
                        p[1] = floor

                parts[i]["position"] = [round(v, 4) for v in pi]
                parts[j]["position"] = [round(v, 4) for v in pj]
                any_moved = True

        if not any_moved:
            break

    return parts


def build_open_composite(scene_ir, object_name, parts, primitive_type, color):
    """Assemble an arbitrary object from a validated *parts* list into a group node.

    Each part specifies its own shape, local position, and scale.  The group
    root is placed at the next free world slot; all part positions are local
    relative to that root.
    """
    group_name = make_unique_name(scene_ir, object_name)
    ref_pos = find_next_free_world_position(scene_ir, preferred_y=0.0)
    base_order = next_object_order(scene_ir)
    rgb = color_name_to_rgb(color)

    children = []
    for idx, part in enumerate(parts):
        child_name = "{}_{}".format(group_name, part["name"])
        pos = [float(v) for v in part["position"]]
        scale = [float(v) for v in part["scale"]]
        shape = str(part.get("shape", primitive_type)).lower()
        children.append({
            "node_type": "mesh_object",
            "name": child_name,
            "id": child_name,
            "created_order": base_order + idx + 1,
            "shape": shape,
            "transform": {"position": pos, "scale": scale},
            "material": {
                "color": list(rgb),
                "texture": {"enabled": False, "path": None},
            },
        })

    group = {
        "node_type": "group",
        "name": group_name,
        "id": group_name,
        "created_order": base_order,
        "transform": {
            "position": [float(ref_pos[0]), 0.0, float(ref_pos[2])],
            "scale": [1.0, 1.0, 1.0],
        },
        "children": children,
    }

    ensure_scene_children(scene_ir).append(group)
    print("[controller] build_open_composite: group={} object={} parts={}".format(
        group_name, object_name, len(parts)))
    return scene_ir


def build_table_composite(scene_ir, object_type, color):
    """Deterministic table: flat top + four legs.

    Dimensions (local): top at y=1.6, scale [2.0, 0.12, 1.2];
    legs at corners, y=0.8, scale [0.12, 1.6, 0.12].
    """
    group_name = make_unique_name(scene_ir, "table_composite")
    ref_pos = find_next_free_world_position(scene_ir, preferred_y=CUBE_Y)
    base_order = next_object_order(scene_ir)
    rgb = color_name_to_rgb(color)
    child_idx = 0

    def _mesh(suffix, pos, scale):
        nonlocal child_idx
        child_idx += 1
        name = "{}_{}".format(group_name, suffix)
        return {
            "node_type": "mesh_object",
            "name": name, "id": name,
            "created_order": base_order + child_idx,
            "shape": str(object_type).lower(),
            "transform": {"position": list(pos), "scale": list(scale)},
            "material": {"color": list(rgb), "texture": {"enabled": False, "path": None}},
        }

    children = [
        _mesh("top",    [0.0,  1.66, 0.0],  [2.0,  0.12, 1.2]),
        _mesh("leg_fl", [-0.88, 0.8, -0.54], [0.12, 1.6,  0.12]),
        _mesh("leg_fr", [ 0.88, 0.8, -0.54], [0.12, 1.6,  0.12]),
        _mesh("leg_bl", [-0.88, 0.8,  0.54], [0.12, 1.6,  0.12]),
        _mesh("leg_br", [ 0.88, 0.8,  0.54], [0.12, 1.6,  0.12]),
    ]

    group = {
        "node_type": "group",
        "name": group_name, "id": group_name,
        "created_order": base_order,
        "transform": {
            "position": [float(ref_pos[0]), 0.0, float(ref_pos[2])],
            "scale": [1.0, 1.0, 1.0],
        },
        "children": children,
    }

    ensure_scene_children(scene_ir).append(group)
    print("[controller] build_table_composite: group={} type={}".format(group_name, object_type))
    return scene_ir


def build_lamp_composite(scene_ir, object_type, color):
    """Deterministic floor lamp: weighted base + tall pole + conical shade.

    Dimensions (local): base at y=0.1 scale [0.5, 0.2, 0.5];
    pole at y=1.0 scale [0.1, 2.0, 0.1]; shade at y=2.15 scale [0.7, 0.4, 0.7].
    """
    group_name = make_unique_name(scene_ir, "lamp_composite")
    ref_pos = find_next_free_world_position(scene_ir, preferred_y=CUBE_Y)
    base_order = next_object_order(scene_ir)
    rgb = color_name_to_rgb(color)
    child_idx = 0

    def _mesh(suffix, pos, scale):
        nonlocal child_idx
        child_idx += 1
        name = "{}_{}".format(group_name, suffix)
        return {
            "node_type": "mesh_object",
            "name": name, "id": name,
            "created_order": base_order + child_idx,
            "shape": str(object_type).lower(),
            "transform": {"position": list(pos), "scale": list(scale)},
            "material": {"color": list(rgb), "texture": {"enabled": False, "path": None}},
        }

    children = [
        _mesh("base",  [0.0, 0.1,  0.0], [0.5, 0.2, 0.5]),
        _mesh("pole",  [0.0, 1.1,  0.0], [0.1, 2.0, 0.1]),
        _mesh("shade", [0.0, 2.15, 0.0], [0.7, 0.4, 0.7]),
    ]

    group = {
        "node_type": "group",
        "name": group_name, "id": group_name,
        "created_order": base_order,
        "transform": {
            "position": [float(ref_pos[0]), 0.0, float(ref_pos[2])],
            "scale": [1.0, 1.0, 1.0],
        },
        "children": children,
    }

    ensure_scene_children(scene_ir).append(group)
    print("[controller] build_lamp_composite: group={} type={}".format(group_name, object_type))
    return scene_ir


def build_ring_pattern(scene_ir, object_type, count, radius, color):
    """Place *count* objects of *object_type* evenly on a circle of *radius*.

    All objects are children of a single group node so the whole pattern
    can be moved / deleted as a unit.  Placement uses the same free-slot
    logic as the rest of the controller so the ring never overlaps existing
    objects.
    """
    count = max(2, min(int(count), 32))
    radius = max(0.5, float(radius))

    group_name = make_unique_name(scene_ir, "ring")
    ref_pos = find_next_free_world_position(scene_ir, preferred_y=CUBE_Y)
    base_order = next_object_order(scene_ir)
    child_idx = 0

    group = {
        "node_type": "group",
        "name": group_name,
        "id": group_name,
        "created_order": base_order,
        "transform": {
            "position": [float(ref_pos[0]), 0.0, float(ref_pos[2])],
            "scale": [1.0, 1.0, 1.0],
        },
        "children": [],
    }

    rgb = color_name_to_rgb(color)

    for i in range(count):
        angle = 2.0 * math.pi * i / count
        x = round(radius * math.cos(angle), 4)
        z = round(radius * math.sin(angle), 4)
        child_idx += 1
        child_name = "{}_obj_{}".format(group_name, child_idx)
        group["children"].append({
            "node_type": "mesh_object",
            "name": child_name,
            "id": child_name,
            "created_order": base_order + child_idx,
            "shape": str(object_type).lower(),
            "transform": {
                "position": [x, CUBE_Y, z],
                "scale": [1.0, 1.0, 1.0],
            },
            "material": {
                "color": list(rgb),
                "texture": {"enabled": False, "path": None},
            },
        })

    ensure_scene_children(scene_ir).append(group)
    print("[controller] build_ring_pattern: group={} count={} radius={} type={}".format(
        group_name, count, radius, object_type))
    return scene_ir


def build_tree_composite(scene_ir, object_type, color):
    """Build a stylised tree entirely from *object_type* mesh objects.

    Structure (all local coords, group root at a free world slot):
      - trunk  : 1 object at [0, 0.75, 0], scale [0.4, 1.5, 0.4]
      - canopy1: 6 objects at y=2.2, r=1.2, scale [1.0, 1.0, 1.0]
      - canopy2: 4 objects at y=3.1, r=0.75, scale [0.9, 0.9, 0.9]  (offset 45°)
      - top    : 1 object at [0, 3.9, 0], scale [0.8, 0.8, 0.8]
    """
    group_name = make_unique_name(scene_ir, "tree_composite")
    ref_pos = find_next_free_world_position(scene_ir, preferred_y=CUBE_Y)
    base_order = next_object_order(scene_ir)
    rgb = color_name_to_rgb(color)
    child_idx = 0

    def _mesh(suffix, pos, scale):
        nonlocal child_idx
        child_idx += 1
        name = "{}_{}".format(group_name, suffix)
        return {
            "node_type": "mesh_object",
            "name": name,
            "id": name,
            "created_order": base_order + child_idx,
            "shape": str(object_type).lower(),
            "transform": {"position": list(pos), "scale": list(scale)},
            "material": {
                "color": list(rgb),
                "texture": {"enabled": False, "path": None},
            },
        }

    children = []

    # trunk — tall and narrow
    children.append(_mesh("trunk", [0.0, 0.75, 0.0], [0.4, 1.5, 0.4]))

    # canopy layer 1 — 6 objects, r=1.2, y=2.2
    for i in range(6):
        a = 2.0 * math.pi * i / 6
        children.append(_mesh(
            "canopy1_{}".format(i + 1),
            [round(1.2 * math.cos(a), 4), 2.2, round(1.2 * math.sin(a), 4)],
            [1.0, 1.0, 1.0],
        ))

    # canopy layer 2 — 4 objects, r=0.75, y=3.1, offset 45°
    for i in range(4):
        a = 2.0 * math.pi * i / 4 + math.pi / 4
        children.append(_mesh(
            "canopy2_{}".format(i + 1),
            [round(0.75 * math.cos(a), 4), 3.1, round(0.75 * math.sin(a), 4)],
            [0.9, 0.9, 0.9],
        ))

    # top — crown apex
    children.append(_mesh("top", [0.0, 3.9, 0.0], [0.8, 0.8, 0.8]))

    group = {
        "node_type": "group",
        "name": group_name,
        "id": group_name,
        "created_order": base_order,
        "transform": {
            "position": [float(ref_pos[0]), 0.0, float(ref_pos[2])],
            "scale": [1.0, 1.0, 1.0],
        },
        "children": children,
    }

    ensure_scene_children(scene_ir).append(group)
    print("[controller] build_tree_composite: group={} type={}".format(group_name, object_type))
    return scene_ir


def apply_action_to_ir(scene_ir, action):
    new_ir = deepcopy(scene_ir)
    action_name = action.get("action")

    print("[controller] Parsed action:", action)

    if action_name == "action_sequence":
        current_ir = new_ir
        sequence = action.get("action_sequence", [])

        for index, step in enumerate(sequence):
            print("[controller] Applying action_sequence step", index + 1, "of", len(sequence))
            validate_action(step)
            current_ir = apply_action_to_ir(current_ir, step)

        return current_ir

    if action_name == "add_object":
        object_type = str(action.get("object_type", "cube")).lower()
        color = color_name_to_rgb(action.get("color", "purple"))
        object_scale = normalize_action_scale(action.get("scale"), default_scale=[1.0, 1.0, 1.0])

        explicit_position = normalize_action_position(action.get("new_position"), "new_position")
        if explicit_position is None:
            explicit_position = normalize_action_position(action.get("position"), "position")

        default_y = max(0.5, 0.5 * float(object_scale[1]))

        if explicit_position is not None:
            desired_world_position = find_nearest_free_world_position(new_ir, explicit_position)
        else:
            desired_world_position = find_next_free_world_position(new_ir, preferred_y=default_y)

        placement = action.get("placement", {})
        relation = placement.get("relation")

        if relation in ("right_of", "on_top_of"):
            target, target_group = resolve_target_node_with_group(new_ir, placement.get("target"))
            if target is not None:
                if relation == "right_of":
                    desired_world_position = find_position_right_of_target(
                        new_ir,
                        target,
                        target_group=target_group
                    )
                elif relation == "on_top_of":
                    desired_world_position = find_position_on_top_of_target(
                        new_ir,
                        target,
                        target_group=target_group
                    )

        position = [
            float(desired_world_position[0]),
            float(desired_world_position[1]),
            float(desired_world_position[2])
        ]

        new_node = {
            "node_type": "mesh_object",
            "name": make_unique_name(new_ir, object_type),
            "id": make_unique_name(new_ir, object_type),
            "created_order": next_object_order(new_ir),
            "shape": object_type,
            "transform": {
                "position": position,
                "scale": object_scale
            },
            "material": {
                "color": color,
                "texture": {
                    "enabled": False,
                    "path": None
                }
            }
        }

        ensure_scene_children(new_ir).append(new_node)
        print("[controller] Added object at position:", position)
        return new_ir

    if action_name == "delete_object":
        object_ids = action.get("object_ids")
        if isinstance(object_ids, list) and object_ids:
            print("[controller] Deleting by object_ids:", object_ids)
            return delete_nodes_by_ids(new_ir, object_ids)

        single_identity = action.get("object_id")
        if single_identity is None:
            single_identity = action.get("id")

        if single_identity is not None:
            print("[controller] Deleting by single object id:", single_identity)
            return delete_nodes_by_ids(new_ir, [single_identity])

        target, target_group = resolve_action_target_node(new_ir, action)
        if target is None:
            raise ValueError("Could not resolve delete target")

        target_id = target.get("id")
        if target_id:
            return delete_nodes_by_ids(new_ir, [target_id])

        children = ensure_scene_children(new_ir)
        children[:] = [c for c in children if c is not target]
        return new_ir

    if action_name == "recolor_object":
        target, target_group = resolve_action_target_node(new_ir, action)
        if target is None:
            raise ValueError("Could not resolve recolor target")

        target.setdefault("material", {})
        target["material"]["color"] = color_name_to_rgb(action.get("color", "purple"))
        target["material"].setdefault("texture", {"enabled": False, "path": None})
        return new_ir

    if action_name == "scale_object":
        target, target_group = resolve_action_target_node(new_ir, action)
        if target is None:
            raise ValueError("Could not resolve scale target")

        transform = target.setdefault("transform", {})
        current_scale = transform.get("scale", [1.0, 1.0, 1.0])

        if "scale" in action:
            new_scale = normalize_action_scale(action.get("scale"), default_scale=current_scale)
        elif "factor" in action:
            factor = float(action.get("factor"))
            new_scale = [
                float(current_scale[0]) * factor,
                float(current_scale[1]) * factor,
                float(current_scale[2]) * factor
            ]
        else:
            raise ValueError("scale_object requires 'scale' or 'factor'")

        transform["scale"] = new_scale
        transform.setdefault("position", [0.0, CUBE_Y, CUBE_Z])
        return new_ir

    if action_name == "move_object":
        target, target_group = resolve_action_target_node(new_ir, action)
        if target is None:
            raise ValueError("Could not resolve move target")

        target_id = target.get("id")
        current_world_position = get_world_position(target, target_group)

        explicit_position = normalize_action_position(action.get("new_position"), "new_position")
        if explicit_position is None:
            explicit_position = normalize_action_position(action.get("position"), "position")

        if explicit_position is not None:
            # Explicit coordinate: snap to nearest free slot around the target point.
            final_world_position = find_nearest_free_world_position(
                new_ir,
                explicit_position,
                exclude_object_id=target_id
            )
        else:
            direction = str(action.get("direction", "")).lower().strip()

            direction_deltas = {
                "right":    [ GRID_SPACING,  0.0,           0.0],
                "left":     [-GRID_SPACING,  0.0,           0.0],
                "up":       [ 0.0,           GRID_SPACING,  0.0],
                "down":     [ 0.0,          -GRID_SPACING,  0.0],
                "forward":  [ 0.0,           0.0,          -GRID_SPACING],
                "backward": [ 0.0,           0.0,           GRID_SPACING],
            }

            if direction not in direction_deltas:
                if not direction:
                    raise ValueError("move_object requires 'direction', 'position', or 'new_position'")
                raise ValueError("Unsupported move direction: " + direction)

            # Walk strictly in the requested direction; never fall back to the
            # opposite side (which would return the object's own current slot).
            delta = direction_deltas[direction]
            final_world_position = find_first_free_in_direction(
                new_ir,
                current_world_position,
                delta,
                exclude_object_id=target_id
            )

        if target_group is not None:
            final_local_position = world_to_local_position(final_world_position, target_group)
            set_position(target, final_local_position)
        else:
            set_position(target, final_world_position)

        print("[controller] Assigned position for moved object:", final_world_position)
        return new_ir

    if action_name == "add_prefab":
        prefab_name = str(action.get("prefab_name") or action.get("name") or "").lower()
        if not prefab_name:
            raise ValueError("add_prefab requires 'prefab_name'")

        builders = {
            "house": build_house,
            "tree": build_tree,
            "gift_box": build_gift_box,
            "street_light": build_street_light,
        }
        builder = builders.get(prefab_name)
        if builder is None:
            raise ValueError("Unknown prefab name: " + prefab_name)

        # Probe at CUBE_Y so existing cubes (all at y=CUBE_Y) are correctly
        # detected as occupying their X/Z slot.  Then set the group root Y to
        # 0.0 so children with local y-offsets sit at natural ground-relative
        # heights (e.g. trunk at world y≈0.22, crown at y≈0.62).
        ref_pos = find_next_free_world_position(new_ir, preferred_y=CUBE_Y)
        position = [ref_pos[0], 0.0, ref_pos[2]]

        unique_name = make_unique_name(new_ir, prefab_name)
        node = builder(name=unique_name, position=position)

        print(f"[controller] add_prefab: name={prefab_name!r}  unique={unique_name!r}")
        print(f"[controller] add_prefab: root node_type={node.get('node_type')!r}")
        print(f"[controller] add_prefab: group root position={position}")
        for _child in node.get("children", []):
            if not isinstance(_child, dict):
                continue
            _local = _child.get("transform", {}).get("position")
            if isinstance(_local, list) and len(_local) == 3:
                _world = [round(position[i] + _local[i], 4) for i in range(3)]
            else:
                _world = "?"
            print(
                f"[controller] add_prefab:   child {_child.get('name')!r}"
                f"  shape={_child.get('shape')!r}"
                f"  local={_local}  world≈{_world}"
            )

        ensure_scene_children(new_ir).append(node)
        print("[controller] Added prefab:", prefab_name)
        return new_ir

    if action_name == "generate_pattern":
        pattern = str(action.get("pattern", "")).lower().strip()
        object_type = str(action.get("object_type", "cube")).lower()
        color = action.get("color") or "purple"
        if pattern == "ring":
            count = action.get("count", 8)
            radius = action.get("radius", 2.5)
            return build_ring_pattern(new_ir, object_type, count, radius, color)
        raise ValueError("Unknown pattern: " + pattern)

    if action_name == "generate_composite":
        composite = str(action.get("composite", "")).lower().strip()
        object_type = str(action.get("object_type", "cube")).lower()
        color = action.get("color") or "green"

        if composite == "tree":
            return build_tree_composite(new_ir, object_type, color)

        if composite == "table":
            return build_table_composite(new_ir, object_type, color)

        if composite == "lamp":
            return build_lamp_composite(new_ir, object_type, color)

        # Open-ended composite: requires a 'parts' list already resolved by
        # handle_pending_ai_request before this function is called.
        parts = action.get("parts")
        if parts is not None:
            object_name = str(action.get("object_name", "object"))
            primitive_type = str(action.get("primitive_type", object_type))
            validate_composite_parts(parts)
            return build_open_composite(new_ir, object_name, parts, primitive_type, color)

        raise ValueError(
            "Unknown composite '{}'. Supported: tree, table, lamp, "
            "or any composite with a 'parts' list.".format(composite)
        )

    raise ValueError("Unsupported action type: " + str(action_name))

def main():
    print("[controller] Mock AI controller started.")
    print("[controller] PROJECT_DIR =", PROJECT_DIR)
    print("[controller] official scene_ir path used:", SCENE_IR_FILE)
    print("[controller] preview scene_ir path used:", PREVIEW_IR_FILE)
    print("[controller] SCENE_OUT_FILE =", SCENE_OUT_FILE)
    print("[controller] PREVIEW_SCENE_FILE =", PREVIEW_SCENE_FILE)
    print("[controller] SAVED_SCENES_DIR =", SAVED_SCENES_DIR)

    initialize_bridge_state()

    while True:
        try:
            handle_pending_ai_request()
        except Exception as e:
            print("[controller] Unhandled error in handle_pending_ai_request:", e)
            traceback.print_exc()
        try:
            handle_ui_actions()
        except Exception as e:
            print("[controller] Unhandled error in handle_ui_actions:", e)
            traceback.print_exc()
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()