import json
import os
import shutil
import time
import traceback
from copy import deepcopy
from pathlib import Path

from code_generator import generate_scene_script


PROJECT_DIR = Path(__file__).resolve().parent
PROJECT_SCENE_IR_FILE = PROJECT_DIR / "scene_ir.json"

SHARED_DIR = Path.home() / "Desktop" / "scene_bridge"
SHARED_DIR.mkdir(parents=True, exist_ok=True)

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

DEFAULT_SCENE_IR = {
    "node_type": "scene",
    "name": "root",
    "window": {
        "width": 1200,
        "height": 800,
        "title": "Hierarchical Cube Scene"
    },
    "children": [
        {
            "node_type": "mesh_object",
            "name": "cube1",
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

    if not source_path.exists():
        raise FileNotFoundError("Missing source file: " + str(source_path))

    tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")
    shutil.copyfile(str(source_path), str(tmp_path))
    os.replace(str(tmp_path), str(target_path))


def clear_preview_files():
    for path in (PREVIEW_IR_FILE, PREVIEW_SCENE_FILE):
        try:
            if path.exists():
                path.unlink()
        except Exception:
            pass


def load_project_baseline_ir():
    data = read_json(PROJECT_SCENE_IR_FILE, default=None)
    if isinstance(data, dict):
        return data

    print("[controller] Project baseline scene_ir.json missing or invalid; using built-in fallback.")
    return deepcopy(DEFAULT_SCENE_IR)


def ensure_shared_scene_ir():
    data = read_json(SCENE_IR_FILE, default=None)
    if isinstance(data, dict):
        return data

    baseline = load_project_baseline_ir()
    write_json(SCENE_IR_FILE, baseline)
    print("[controller] Initialized shared scene_ir.json from project baseline.")
    print("[controller] official scene_ir path used:", SCENE_IR_FILE)
    return baseline


def ensure_official_scene_script():
    scene_ir = ensure_shared_scene_ir()
    if SCENE_OUT_FILE.exists():
        return

    script = generate_scene_script(scene_ir)
    write_text_atomic(SCENE_OUT_FILE, script)
    print("[controller] Created missing official scene_out.py:", SCENE_OUT_FILE)


def normalize_startup_bridge_state():
    ensure_shared_scene_ir()
    ensure_official_scene_script()
    clear_preview_files()

    write_json(UI_STATE_FILE, {
        "action": "idle",
        "created_at": time.time()
    })

    req = read_json(AI_REQUEST_FILE, default=None)
    if isinstance(req, dict) and req.get("status") in ("pending", "preview_ready"):
        req["status"] = "stale"
        req["message"] = "Cleared by controller startup."
        req["updated_at"] = time.time()
        write_json(AI_REQUEST_FILE, req)

    write_scene_state("official", SCENE_OUT_FILE)


def load_scene_ir():
    print("[controller] official scene_ir path used:", SCENE_IR_FILE)
    return ensure_shared_scene_ir()


def save_preview_ir(scene_ir):
    write_json(PREVIEW_IR_FILE, scene_ir)
    print("[controller] preview scene_ir path used:", PREVIEW_IR_FILE)


def save_preview_script(scene_ir):
    script = generate_scene_script(scene_ir)
    write_text_atomic(PREVIEW_SCENE_FILE, script)
    print("[controller] Saved preview script to:", PREVIEW_SCENE_FILE)


def promote_preview_files_exactly():
    if not PREVIEW_IR_FILE.exists():
        raise FileNotFoundError("Missing preview_scene_ir.json")
    if not PREVIEW_SCENE_FILE.exists():
        raise FileNotFoundError("Missing preview_scene.py")

    preview_ir = read_json(PREVIEW_IR_FILE, default=None)
    if not isinstance(preview_ir, dict):
        raise ValueError("Could not read preview_scene_ir.json")

    print("[controller] Applying exact preview IR:", PREVIEW_IR_FILE)
    print("[controller] Applying exact preview script:", PREVIEW_SCENE_FILE)

    copy_file_atomic(PREVIEW_IR_FILE, SCENE_IR_FILE)
    copy_file_atomic(PREVIEW_SCENE_FILE, SCENE_OUT_FILE)

    print("[controller] Promoted preview IR to:", SCENE_IR_FILE)
    print("[controller] Promoted preview script to:", SCENE_OUT_FILE)


def collect_mesh_objects(node, out_list):
    if not isinstance(node, dict):
        return

    if node.get("node_type") == "mesh_object":
        out_list.append(node)

    for child in node.get("children", []):
        collect_mesh_objects(child, out_list)


def collect_cube_positions(scene_ir):
    meshes = []
    positions = []
    collect_mesh_objects(scene_ir, meshes)

    for node in meshes:
        if node.get("shape") != "cube":
            continue

        transform = node.get("transform", {})
        position = transform.get("position")
        if not isinstance(position, list) or len(position) != 3:
            continue

        try:
            positions.append([
                float(position[0]),
                float(position[1]),
                float(position[2])
            ])
        except Exception:
            pass

    return positions


def find_next_free_cube_position(scene_ir):
    used_slots = set()

    for position in collect_cube_positions(scene_ir):
        x = position[0]
        y = position[1]
        z = position[2]

        if abs(y - CUBE_Y) > 0.01:
            continue
        if abs(z - CUBE_Z) > 0.01:
            continue

        slot = int(round(x / GRID_SPACING))
        if abs(x - (slot * GRID_SPACING)) < 0.01 and slot >= 0:
            used_slots.add(slot)

    slot = 0
    while slot in used_slots:
        slot += 1

    return [slot * GRID_SPACING, CUBE_Y, CUBE_Z]


def find_first_cube(scene_ir):
    meshes = []
    collect_mesh_objects(scene_ir, meshes)

    for node in meshes:
        if node.get("shape") == "cube":
            return node

    return None


def make_unique_name(scene_ir, prefix):
    existing = set()

    def walk(node):
        if not isinstance(node, dict):
            return

        name = node.get("name")
        if name:
            existing.add(name)

        for child in node.get("children", []):
            walk(child)

    walk(scene_ir)

    index = 1
    while prefix + "_" + str(index) in existing:
        index += 1

    return prefix + "_" + str(index)


def ensure_scene_children(scene_ir):
    children = scene_ir.get("children")
    if not isinstance(children, list):
        children = []
        scene_ir["children"] = children
    return children


def detect_color_from_text(text):
    text = text.lower()

    if "red" in text:
        return [1.0, 0.0, 0.0]
    if "blue" in text:
        return [0.0, 0.0, 1.0]
    if "green" in text:
        return [0.0, 1.0, 0.0]
    if "yellow" in text:
        return [1.0, 1.0, 0.0]
    if "white" in text:
        return [1.0, 1.0, 1.0]
    if "black" in text:
        return [0.02, 0.02, 0.02]

    return [0.8, 0.0, 0.8]


def make_cube_node(scene_ir, position, color):
    return {
        "node_type": "mesh_object",
        "name": make_unique_name(scene_ir, "cube"),
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


def apply_mock_ai_prompt(scene_ir, prompt):
    text = prompt.lower().strip()
    new_ir = deepcopy(scene_ir)
    color = detect_color_from_text(text)

    mentions_cube = "cube" in text or "κύβ" in text or "κυβ" in text
    mentions_on_top = "on top" in text or "πάνω" in text or "πανω" in text

    if mentions_cube and mentions_on_top:
        target_cube = find_first_cube(new_ir)
        if target_cube is None:
            raise ValueError("No existing cube found to place another cube on top of.")

        target_transform = target_cube.get("transform", {})
        target_pos = target_transform.get("position", [0.0, 0.5, 0.0])
        target_scale = target_transform.get("scale", [1.0, 1.0, 1.0])

        position = [
            float(target_pos[0]),
            float(target_pos[1]) + float(target_scale[1]),
            float(target_pos[2])
        ]
    elif mentions_cube:
        position = find_next_free_cube_position(new_ir)
    else:
        raise ValueError("This mock controller currently supports cube commands only.")

    cube = make_cube_node(new_ir, position, color)
    ensure_scene_children(new_ir).append(cube)

    print("[controller] Added cube:", cube["name"])
    print("[controller] Added cube position:", position)

    return new_ir


def write_scene_state(mode, active_script, request_id=None):
    data = {
        "mode": mode,
        "active_script": str(active_script),
        "updated_at": time.time()
    }

    if request_id is not None:
        data["request_id"] = request_id

    write_json(SCENE_STATE_FILE, data)


def mark_request_status(req, status, message=None, error=None):
    req["status"] = status
    req["updated_at"] = time.time()

    if message is not None:
        req["message"] = message
    if error is not None:
        req["error"] = error

    write_json(AI_REQUEST_FILE, req)


def handle_pending_ai_request():
    req = read_json(AI_REQUEST_FILE, default=None)
    if not isinstance(req, dict):
        return

    if req.get("status") != "pending":
        return

    request_id = req.get("request_id")
    prompt = str(req.get("prompt", "")).strip()

    print("[controller] AI request found:", req)

    if not prompt:
        mark_request_status(req, "error", error="Empty prompt")
        return

    try:
        scene_ir = load_scene_ir()
        preview_ir = apply_mock_ai_prompt(scene_ir, prompt)

        save_preview_ir(preview_ir)
        save_preview_script(preview_ir)

        mark_request_status(req, "preview_ready", message="Preview generated.")

        write_scene_state("preview", PREVIEW_SCENE_FILE, request_id=request_id)
        print("[controller] Preview ready for request", request_id)

    except Exception as e:
        mark_request_status(req, "error", error=str(e))
        print("[controller] Error while generating preview:", e)
        traceback.print_exc()


def handle_apply(ui):
    request_id = ui.get("request_id")

    promote_preview_files_exactly()

    write_json(UI_STATE_FILE, {
        "action": "idle",
        "request_id": request_id,
        "updated_at": time.time()
    })

    req = read_json(AI_REQUEST_FILE, default=None)
    if isinstance(req, dict):
        mark_request_status(req, "applied", message="Preview applied.")

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

    req = read_json(AI_REQUEST_FILE, default=None)
    if isinstance(req, dict):
        mark_request_status(req, "rejected", message="Preview rejected.")

    write_scene_state("official", SCENE_OUT_FILE, request_id=request_id)
    print("[controller] Preview rejected.")


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

        write_scene_state("official", SCENE_OUT_FILE, request_id=ui.get("request_id"))

        print("[controller] UI action error:", e)
        traceback.print_exc()


def main():
    print("[controller] Mock AI controller started.")
    print("[controller] PROJECT_DIR =", PROJECT_DIR)
    print("[controller] PROJECT_SCENE_IR_FILE =", PROJECT_SCENE_IR_FILE)
    print("[controller] SHARED_DIR =", SHARED_DIR)
    print("[controller] official scene_ir path used:", SCENE_IR_FILE)
    print("[controller] preview scene_ir path used:", PREVIEW_IR_FILE)
    print("[controller] SCENE_OUT_FILE =", SCENE_OUT_FILE)
    print("[controller] PREVIEW_SCENE_FILE =", PREVIEW_SCENE_FILE)
    print("[controller] SCENE_STATE_FILE =", SCENE_STATE_FILE)

    normalize_startup_bridge_state()

    while True:
        handle_pending_ai_request()
        handle_ui_actions()
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
