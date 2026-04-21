import json
import os
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
    return baseline


def ensure_official_scene_script():
    scene_ir = ensure_shared_scene_ir()
    if SCENE_OUT_FILE.exists():
        return

    script = generate_scene_script(scene_ir)
    write_text_atomic(SCENE_OUT_FILE, script)
    print("[controller] Created missing official scene_out.py.")


def normalize_startup_bridge_state():
    ensure_shared_scene_ir()
    ensure_official_scene_script()
    clear_preview_files()

    write_json(UI_STATE_FILE, {
        "action": "idle",
        "created_at": time.time()
    })

    req = read_json(AI_REQUEST_FILE, default=None)
    if isinstance(req, dict):
        status = req.get("status")
        if status in ("pending", "preview_ready"):
            req["status"] = "stale"
            req["message"] = "Cleared by controller startup."
            req["updated_at"] = time.time()
            write_json(AI_REQUEST_FILE, req)

    write_json(SCENE_STATE_FILE, {
        "mode": "official",
        "active_script": str(SCENE_OUT_FILE),
        "updated_at": time.time()
    })


def load_scene_ir():
    return ensure_shared_scene_ir()


def save_preview_ir(scene_ir):
    write_json(PREVIEW_IR_FILE, scene_ir)
    print("[controller] Saved preview IR to:", PREVIEW_IR_FILE)


def save_preview_script(scene_ir):
    script = generate_scene_script(scene_ir)
    write_text_atomic(PREVIEW_SCENE_FILE, script)
    print("[controller] Saved preview script to:", PREVIEW_SCENE_FILE)


def promote_preview():
    if not PREVIEW_IR_FILE.exists():
        raise FileNotFoundError("Missing preview_scene_ir.json")
    if not PREVIEW_SCENE_FILE.exists():
        raise FileNotFoundError("Missing preview_scene.py")

    preview_ir = read_json(PREVIEW_IR_FILE, default=None)
    if not isinstance(preview_ir, dict):
        raise ValueError("Could not read preview_scene_ir.json")

    preview_script = PREVIEW_SCENE_FILE.read_text(encoding="utf-8")

    write_json(SCENE_IR_FILE, preview_ir)
    write_text_atomic(SCENE_OUT_FILE, preview_script)

    print("[controller] Promoted preview successfully.")


def collect_mesh_objects(node, out_list):
    if not isinstance(node, dict):
        return

    if node.get("node_type") == "mesh_object":
        out_list.append(node)

    for child in node.get("children", []):
        collect_mesh_objects(child, out_list)


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

    mentions_cube = "cube" in text or "κύβ" in text
    mentions_on_top = "on top" in text or "πάνω" in text

    if mentions_cube and mentions_on_top:
        target_cube = find_first_cube(new_ir)
        if target_cube is None:
            raise ValueError("No existing cube found to place another cube on top of.")

        target_transform = target_cube.get("transform", {})
        target_pos = target_transform.get("position", [0.0, 0.5, 0.0])
        target_scale = target_transform.get("scale", [1.0, 1.0, 1.0])

        new_pos = [
            float(target_pos[0]),
            float(target_pos[1]) + float(target_scale[1]),
            float(target_pos[2])
        ]

        ensure_scene_children(new_ir).append(make_cube_node(new_ir, new_pos, color))
        return new_ir

    if mentions_cube:
        ensure_scene_children(new_ir).append(make_cube_node(new_ir, [0.0, 1.5, 0.0], color))
        return new_ir

    raise ValueError("This mock controller currently supports cube commands only.")


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

        mark_request_status(
            req,
            "preview_ready",
            message="Preview generated."
        )

        write_scene_state("preview", PREVIEW_SCENE_FILE, request_id=request_id)
        print("[controller] Preview ready for request", request_id)

    except Exception as e:
        mark_request_status(req, "error", error=str(e))
        print("[controller] Error while generating preview:", e)
        traceback.print_exc()


def handle_apply(ui):
    request_id = ui.get("request_id")

    promote_preview()
    clear_preview_files()

    write_json(UI_STATE_FILE, {
        "action": "idle",
        "request_id": request_id,
        "updated_at": time.time()
    })

    req = read_json(AI_REQUEST_FILE, default=None)
    if isinstance(req, dict):
        mark_request_status(req, "applied", message="Preview applied.")

    write_scene_state("official", SCENE_OUT_FILE, request_id=request_id)
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
    print("[controller] SCENE_IR_FILE =", SCENE_IR_FILE)
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
