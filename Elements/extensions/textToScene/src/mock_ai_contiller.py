import json
import os
import shutil
import time
import traceback
import re
from copy import deepcopy
from pathlib import Path

from code_generator import generate_scene_script
from llm_parser import parse_prompt_to_action_with_llm


PROJECT_DIR = Path(__file__).resolve().parent
PROJECT_SCENE_IR_FILE = PROJECT_DIR / "scene_ir.json"

SHARED_DIR = Path.home() / "Desktop" / "scene_bridge"
SHARED_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_DIR = SHARED_DIR / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

SAVED_SCENES_DIR = SHARED_DIR / "saved_scenes"
SAVED_SCENES_DIR.mkdir(parents=True, exist_ok=True)

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


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(str(tmp_path), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    os.replace(str(tmp_path), str(path))


def write_text_atomic(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(str(tmp_path), "w", encoding="utf-8") as f:
        f.write(text)

    os.replace(str(tmp_path), str(path))


def copy_file_atomic(source_path, target_path):
    source_path = Path(source_path)
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")
    shutil.copyfile(str(source_path), str(tmp_path))
    os.replace(str(tmp_path), str(target_path))


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

    write_json(AI_REQUEST_FILE, req)

    write_json(UI_STATE_FILE, {
        "action": "idle",
        "request_id": request_id,
        "updated_at": time.time()
    })

    print("[controller] Reset request file:", AI_REQUEST_FILE)
    print("[controller] Reset UI file:", UI_STATE_FILE)


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

    write_json(AI_REQUEST_FILE, data)


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


def collect_world_positions(scene_ir, exclude_node=None):
    positions = []

    for node, parent_group in collect_mesh_objects_with_groups(scene_ir):
        if exclude_node is not None and node is exclude_node:
            continue

        positions.append(get_world_position(node, parent_group))

    return positions


def is_world_position_free(scene_ir, world_position, exclude_node=None):
    for used in collect_world_positions(scene_ir, exclude_node=exclude_node):
        if positions_overlap(used, world_position):
            return False

    return True


def find_next_free_world_position(scene_ir):
    used_x = []
    for node in collect_mesh_objects(scene_ir):
        pos= node.get("transform", {}).get("position", [0.0, CUBE_Y, CUBE_Z])   
        try: 
            used_x.append(float(pos[0]))
        except Exception:
            pass
    
    slot = 0    
    while True:
        x = GRID_SPACING * slot
        if all(abs(x - u) > 1e-6 for u in used_x):
            return [x, CUBE_Y, CUBE_Z]
        slot += 1


def find_next_free_position_for_group(scene_ir, group_node):
    world_position = find_next_free_world_position(scene_ir)
    return world_to_local_position(world_position, group_node)


def find_position_right_of_target(scene_ir, target_node, target_group=None, destination_group=None, exclude_node=None):
    base = get_world_position(target_node, target_group)
    step = 1

    while True:
        world_position = [base[0] + GRID_SPACING * step, base[1], base[2]]

        if is_world_position_free(scene_ir, world_position, exclude_node=exclude_node):
            if destination_group is not None:
                return world_to_local_position(world_position, destination_group)

            return world_position

        step += 1


def find_position_on_top_of_target(scene_ir, target_node, target_group=None, destination_group=None, exclude_node=None):
    base = get_world_position(target_node, target_group)
    scale = get_scale(target_node)
    world_position = [base[0], base[1] + scale[1], base[2]]

    if is_world_position_free(scene_ir, world_position, exclude_node=exclude_node):
        if destination_group is not None:
            return world_to_local_position(world_position, destination_group)

        return world_position

    return find_position_right_of_target(
        scene_ir,
        target_node,
        target_group=target_group,
        destination_group=destination_group,
        exclude_node=exclude_node
    )


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


def parse_command(prompt):
    text = prompt.lower().strip()
    group_name = group_name_from_text(text)

    if "new scene" in text:
        return {"type": "new_scene"}

    if "save scene" in text:
        return {"type": "save_scene"}

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
            direction = "right" if "right" in text else None

            return {
                "type": "move_group",
                "group_name": group_name,
                "direction": direction
            }

        direction = "right" if "right" in text else None

        return {
            "type": "move",
            "direction": direction,
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
    t = command.get("type")
    if t == "new_scene":
        return {"action": "new_scene"}
    if t == "save_scene":
        return {"action": "save_scene"}
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
            "direction": command.get("direction") or "right"
        }
    if t == "change_color":
        return {
            "action": "recolor_object",
            "target": "cube",
            "color": command.get("new_color") or "purple"
        }
    if t == "create_group":
        return {"action": "create_group", "group_name": command.get("group_name")}
    raise ValueError("Unknown rule-based command type: " + str(t))
############################ change for llm parser ############################
def apply_mock_ai_prompt(scene_ir, prompt):
    new_ir = ensure_stable_object_ids(deepcopy(scene_ir))
    command = parse_command(prompt)

    print("[controller] Parsed command type:", command.get("type"))

    command_type = command.get("type")
    group_name = command.get("group_name")

    if command_type == "create_group":
        if not group_name:
            raise ValueError("Missing group name.")

        existing = find_group(new_ir, group_name)
        if existing is not None:
            print("[controller] Group already exists:", existing.get("name"))
            return new_ir

        group_node = make_group_node(new_ir, group_name)
        ensure_scene_children(new_ir).append(group_node)

        print("[controller] Created group:", group_node.get("name"))
        print("[controller] Group position:", group_node.get("transform", {}).get("position"))
        return new_ir

    if command_type == "add_cube":
        placement = command.get("placement")
        color = color_value(command.get("color"))
        target_text = command.get("target_text") or prompt

        destination_group = None

        if group_name:
            destination_group = find_group(new_ir, group_name)
            if destination_group is None:
                raise ValueError("Group not found: " + str(group_name))

        if placement == "right_of":
            target, target_group = resolve_target(
                new_ir,
                target_text,
                prefer_color=None,
                group_name=group_name
            )

            if target is None:
                raise ValueError("Could not resolve target for right-of placement.")

            position = find_position_right_of_target(
                new_ir,
                target,
                target_group=target_group,
                destination_group=destination_group
            )

        elif placement == "on_top_of":
            target, target_group = resolve_target(
                new_ir,
                target_text,
                prefer_color=None,
                group_name=group_name
            )

            if target is None:
                raise ValueError("Could not resolve target for on-top placement.")

            position = find_position_on_top_of_target(
                new_ir,
                target,
                target_group=target_group,
                destination_group=destination_group
            )

        else:
            if destination_group is not None:
                position = find_next_free_position_for_group(new_ir, destination_group)
            else:
                position = find_next_free_world_position(new_ir)

        cube = make_cube_node(new_ir, position, color)

        if destination_group is not None:
            ensure_group_children(destination_group).append(cube)
            print("[controller] Added object to group:", destination_group.get("name"))
        else:
            ensure_scene_children(new_ir).append(cube)

        print("[controller] Target text for placement:", target_text)
        print("[controller] Assigned position for new object:", position)
        print("[controller] Added object name:", cube["name"])
        return new_ir

    if command_type == "move_group":
        if not group_name:
            raise ValueError("Missing group name.")

        group_node = find_group(new_ir, group_name)
        if group_node is None:
            raise ValueError("Group not found: " + str(group_name))

        direction = command.get("direction")
        if direction != "right":
            raise ValueError("Only moving groups to the right is supported for now.")

        current_position = get_group_world_offset(group_node)
        new_position = [
            current_position[0] + GRID_SPACING,
            current_position[1],
            current_position[2]
        ]

        group_node.setdefault("transform", {})["position"] = new_position
        group_node.setdefault("transform", {}).setdefault("scale", [1.0, 1.0, 1.0])

        print("[controller] Moved group:", group_node.get("name"))
        print("[controller] New group position:", new_position)
        return new_ir

    if command_type == "move":
        target, target_group = resolve_target(
            new_ir,
            prompt,
            prefer_color=command.get("target_color"),
            group_name=group_name
        )

        if target is None:
            raise ValueError("Could not resolve target for move command.")

        direction = command.get("direction")
        if direction != "right":
            raise ValueError("Only moving to the right is supported for now.")

        position = find_position_right_of_target(
            new_ir,
            target,
            target_group=target_group,
            destination_group=target_group,
            exclude_node=target
        )

        set_position(target, position)

        print("[controller] Assigned position for moved object:", position)
        return new_ir

    if command_type == "change_color":
        new_color_name = command.get("new_color")
        if new_color_name is None:
            raise ValueError("No supported target color found.")

        target, target_group = resolve_target(new_ir, prompt, group_name=group_name)
        if target is None:
            raise ValueError("Could not resolve target for color change.")

        material = target.setdefault("material", {})
        material["color"] = color_value(new_color_name)
        material.setdefault("texture", {"enabled": False, "path": None})

        print("[controller] Changed object color:", target.get("name"), "->", new_color_name)
        return new_ir

    if command_type == "delete":
        target, target_group = resolve_target(
            new_ir,
            prompt,
            prefer_color=command.get("target_color"),
            group_name=group_name
        )

        if target is None:
            raise ValueError("Could not resolve target for delete command.")

        target_id = target.get("id")
        target_name = target.get("name")

        if not remove_node_by_id(new_ir, target_id):
            raise ValueError("Could not delete target object: " + str(target_name))

        print("[controller] Deleted object name:", target_name)
        return new_ir

    raise ValueError("Unsupported command.")


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

        try:
            action = parse_prompt_to_action_with_llm(prompt, scene_ir)
            print("[controller] LLM action:", action.get("action"))
        except Exception as llm_err:
            print("[controller] LLM failed, using rule-based fallback:", llm_err)
            command = parse_command(prompt)
            action = command_to_action(command)
            print("[controller] Fallback action:", action.get("action"))

        validate_action(action)

        if action.get("action") == "new_scene":
            initialize_new_scene(request_id=request_id)
            return

        if action.get("action") == "save_scene":
            handle_save_scene({"request_id": request_id})
            return

        preview_ir = apply_action_to_ir(scene_ir, action)

        save_preview_ir(preview_ir)
        save_preview_script(preview_ir)

        req["status"] = "preview_ready"
        req["message"] = "Το preview δημιουργήθηκε."
        req["preview_file"] = PREVIEW_SCENE_FILE.name
        req["preview_ir_file"] = PREVIEW_IR_FILE.name
        req["parsed_action"] = action
        write_json(AI_REQUEST_FILE, req)

        write_json(SCENE_STATE_FILE, {
            "mode": "preview",
            "active_script": str(PREVIEW_SCENE_FILE),
            "request_id": request_id
        })

        print("[controller] Preview ready for request", request_id)

    except Exception as e:
        req["status"] = "error"
        req["error"] = str(e)
        write_json(AI_REQUEST_FILE, req)
        print("[controller] Error while handling request:")
        traceback.print_exc()

def handle_apply(ui):
    request_id = ui.get("request_id")

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

    write_json(UI_STATE_FILE, {
        "action": "idle",
        "request_id": request_id,
        "updated_at": time.time()
    })

    write_status(
        "scene_saved",
        "Scene saved. Backup: " + backup_path.name,
        request_id=request_id
    )

    write_scene_state("official", SCENE_OUT_FILE, request_id=request_id)

    print("[controller] Scene saved.")
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
        else:
            write_json(UI_STATE_FILE, {
                "action": "error",
                "message": "Unknown action: " + str(action),
                "updated_at": time.time()
            })

    except Exception as e:
        write_json(UI_STATE_FILE, {
            "action": "error",
            "message": str(e),
            "updated_at": time.time()
        })

        write_status("error", error=str(e), request_id=ui.get("request_id"))
        write_scene_state("official", SCENE_OUT_FILE, request_id=ui.get("request_id"))

        print("[controller] UI action error:", e)
        traceback.print_exc()


######## new helper functions for llm parser ########
def validate_action(action):
    if not isinstance(action, dict):
        raise ValueError("Parsed action must be a dictionary")

    if "action" not in action:
        raise ValueError("Parsed action missing 'action'")

    allowed = {
        "add_object",
        "move_object",
        "delete_object",
        "recolor_object",
        "scale_object",
        "new_scene",
        "save_scene",
        "undo"
    }

    if action["action"] not in allowed:
        raise ValueError("Unsupported action: " + str(action["action"]))


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


def resolve_target_node(scene_ir, target_text):
    if not target_text:
        return None

    target_text = str(target_text).lower().strip()
    candidates = []

    for node in collect_mesh_objects(scene_ir):
        info = describe_node(node)
        tokens = [info["name"].lower(), info["shape"].lower(), info["color_name"].lower()]
        joined = " ".join(tokens)

        if target_text in joined:
            candidates.append(node)

    if not candidates:
        return None

    candidates = sorted(candidates, key=lambda n: str(n.get("name", "")))
    chosen = candidates[0]
    print("[controller] Resolved target:", target_text, "->", chosen.get("name"))
    return chosen

def color_name_to_rgb(name):
    return COLOR_TABLE.get(str(name).lower(), [0.8, 0.0, 0.8])


def apply_action_to_ir(scene_ir, action):
    new_ir = deepcopy(scene_ir)
    action_name = action.get("action")

    print("[controller] Parsed action:", action)

    if action_name == "add_object":
        object_type = str(action.get("object_type", "cube")).lower()
        color = color_name_to_rgb(action.get("color", "purple"))

        position = find_next_free_world_position(new_ir)
        placement = action.get("placement", {})
        relation = placement.get("relation")

        if relation in ("right_of", "on_top_of"):
            target = resolve_target_node(new_ir, placement.get("target"))
            if target is not None:
                target_pos = target.get("transform", {}).get("position", [0.0, CUBE_Y, CUBE_Z])
                target_scale = target.get("transform", {}).get("scale", [1.0, 1.0, 1.0])

                if relation == "right_of":
                    position = [
                        float(target_pos[0]) + GRID_SPACING,
                        float(target_pos[1]),
                        float(target_pos[2])
                    ]
                elif relation == "on_top_of":
                    position = [
                        float(target_pos[0]),
                        float(target_pos[1]) + float(target_scale[1]),
                        float(target_pos[2])
                    ]

        new_node = {
            "node_type": "mesh_object",
            "name": make_unique_name(new_ir, object_type),
            "id": make_unique_name(new_ir, object_type),
            "created_order": next_object_order(new_ir),
            "shape": object_type,
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

        ensure_scene_children(new_ir).append(new_node)
        print("[controller] Added object at position:", position)
        return new_ir

    if action_name == "delete_object":
        object_ids = action.get("object_ids")
        if object_ids:
            print("[controller] Deleting by object_ids:", object_ids)
            return delete_nodes_by_ids(new_ir, object_ids)

        target = resolve_target_node(new_ir, action.get("target"))
        if target is None:
            raise ValueError("Could not resolve delete target")

        target_id = target.get("id")
        if target_id:
            return delete_nodes_by_ids(new_ir, [target_id])

        children = ensure_scene_children(new_ir)
        children[:] = [c for c in children if c is not target]
        return new_ir

    if action_name == "recolor_object":
        target = resolve_target_node(new_ir, action.get("target"))
        if target is None:
            raise ValueError("Could not resolve recolor target")

        target.setdefault("material", {})
        target["material"]["color"] = color_name_to_rgb(action.get("color", "purple"))
        target["material"].setdefault("texture", {"enabled": False, "path": None})
        return new_ir

    if action_name == "move_object":
        target = resolve_target_node(new_ir, action.get("target"))
        if target is None:
            raise ValueError("Could not resolve move target")

        direction = str(action.get("direction", "")).lower().strip()
        pos = target.setdefault("transform", {}).setdefault("position", [0.0, CUBE_Y, CUBE_Z])

        if direction == "right":
            pos[0] = float(pos[0]) + GRID_SPACING
        elif direction == "left":
            pos[0] = float(pos[0]) - GRID_SPACING
        elif direction == "forward":
            pos[2] = float(pos[2]) - GRID_SPACING
        elif direction == "backward":
            pos[2] = float(pos[2]) + GRID_SPACING
        else:
            raise ValueError("Unsupported move direction: " + direction)

        return new_ir

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
        handle_pending_ai_request()
        handle_ui_actions()
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()