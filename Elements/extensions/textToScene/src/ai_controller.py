import json
import os
import time
import traceback
from copy import deepcopy
from pathlib import Path

from code_generator import generate_scene_script

PROJECT_DIR = Path(__file__).resolve().parent
SHARED_DIR = Path.home() / "Desktop" / "scene_bridge"
SHARED_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_SCENE_IR_FILE = PROJECT_DIR / "scene_ir.json"
SCENE_IR_FILE = SHARED_DIR / "scene_ir.json"
PREVIEW_IR_FILE = SHARED_DIR / "preview_scene_ir.json"
AI_REQUEST_FILE = SHARED_DIR / "ai_request.json"
UI_STATE_FILE = SHARED_DIR / "ui_state.json"
SCENE_STATE_FILE = SHARED_DIR / "scene_state.json"
SCENE_OUT_FILE = Path.home() / "Desktop" / "scene_out.py"
PREVIEW_SCENE_FILE = SHARED_DIR / "preview_scene.py"

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY environment variable")


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def ensure_shared_scene_ir():
    if SCENE_IR_FILE.exists():
        return
    baseline = read_json(PROJECT_SCENE_IR_FILE, default=None)
    if baseline is None:
        raise FileNotFoundError("Missing baseline project scene_ir.json")
    write_json(SCENE_IR_FILE, baseline)


def load_scene_ir():
    data = read_json(SCENE_IR_FILE, default=None)
    if data is not None:
        return data
    data = read_json(PROJECT_SCENE_IR_FILE, default=None)
    if data is not None:
        return data
    raise FileNotFoundError("Could not find scene_ir.json")


def save_preview_ir(scene_ir):
    write_json(PREVIEW_IR_FILE, scene_ir)


def save_preview_script(scene_ir):
    script = generate_scene_script(scene_ir)
    PREVIEW_SCENE_FILE.write_text(script, encoding="utf-8")


def promote_preview():
    preview_ir = read_json(PREVIEW_IR_FILE, default=None)
    if preview_ir is None:
        raise FileNotFoundError("Missing preview_scene_ir.json")
    if not PREVIEW_SCENE_FILE.exists():
        raise FileNotFoundError("Missing preview_scene.py")

    SCENE_IR_FILE.write_text(
        json.dumps(preview_ir, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    SCENE_OUT_FILE.write_text(
        PREVIEW_SCENE_FILE.read_text(encoding="utf-8"),
        encoding="utf-8"
    )


def clear_preview():
    if PREVIEW_IR_FILE.exists():
        PREVIEW_IR_FILE.unlink()
    if PREVIEW_SCENE_FILE.exists():
        PREVIEW_SCENE_FILE.unlink()


def build_scene_context(scene_ir):
    objects = []

    def walk(node):
        if not isinstance(node, dict):
            return
        if node.get("node_type") == "mesh_object":
            material = node.get("material", {})
            color = material.get("color")
            objects.append({
                "name": node.get("name"),
                "shape": node.get("shape"),
                "color": color,
                "position": node.get("transform", {}).get("position")
            })
        for child in node.get("children", []):
            walk(child)

    walk(scene_ir)
    return {"objects": objects}


def parse_prompt_to_action_with_llm(prompt, scene_ir):
    scene_context = build_scene_context(scene_ir)

    # TODO:
    # εδώ θα μπει η κλήση στο Gemini
    # και θα επιστρέφει strict JSON action
    #
    # προσωρινά κράτα fallback rule-based για να μη σπάει το flow
    action = fallback_rule_based_action(prompt, scene_context)
    validate_action(action)
    return action


def fallback_rule_based_action(prompt, scene_context):
    text = prompt.lower().strip()

    if "red cube" in text:
        return {
            "action": "add_object",
            "object_type": "cube",
            "color": "red",
            "placement": {
                "relation": "next_free_slot"
            }
        }

    if "green cube" in text:
        return {
            "action": "add_object",
            "object_type": "cube",
            "color": "green",
            "placement": {
                "relation": "next_free_slot"
            }
        }

    raise ValueError("Unsupported prompt")


def validate_action(action):
    if not isinstance(action, dict):
        raise ValueError("LLM action must be a dict")
    if "action" not in action:
        raise ValueError("LLM action missing 'action'")


def find_next_free_cube_position(scene_ir):
    used_x = []

    def walk(node):
        if not isinstance(node, dict):
            return
        if node.get("node_type") == "mesh_object" and node.get("shape") == "cube":
            pos = node.get("transform", {}).get("position", [0.0, 0.5, 0.0])
            used_x.append(float(pos[0]))
        for child in node.get("children", []):
            walk(child)

    walk(scene_ir)

    slot = 0
    while True:
        x = 1.5 * slot
        if all(abs(x - u) > 1e-6 for u in used_x):
            return [x, 0.5, 0.0]
        slot += 1


def make_unique_name(scene_ir, prefix="cube"):
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

    i = 1
    while f"{prefix}_{i}" in existing:
        i += 1
    return f"{prefix}_{i}"


def ensure_scene_children(scene_ir):
    if "children" not in scene_ir or not isinstance(scene_ir["children"], list):
        scene_ir["children"] = []
    return scene_ir["children"]


def color_name_to_rgb(name):
    mapping = {
        "red": [1.0, 0.0, 0.0],
        "green": [0.0, 1.0, 0.0],
        "blue": [0.0, 0.0, 1.0],
        "yellow": [1.0, 1.0, 0.0],
        "white": [1.0, 1.0, 1.0],
        "black": [0.0, 0.0, 0.0],
        "purple": [0.8, 0.0, 0.8],
    }
    return mapping.get(name, [0.8, 0.0, 0.8])


def apply_action_to_ir(scene_ir, action):
    new_ir = deepcopy(scene_ir)

    if action["action"] == "add_object":
        if action.get("object_type") != "cube":
            raise ValueError("Only cube supported for now")

        color = color_name_to_rgb(action.get("color", "purple"))
        position = find_next_free_cube_position(new_ir)

        new_node = {
            "node_type": "mesh_object",
            "name": make_unique_name(new_ir, "cube"),
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

        ensure_scene_children(new_ir).append(new_node)
        return new_ir

    raise ValueError("Unsupported action type")


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
        scene_ir = load_scene_ir()
        action = parse_prompt_to_action_with_llm(prompt, scene_ir)
        print("[controller] Parsed action:", action)

        preview_ir = apply_action_to_ir(scene_ir, action)
        save_preview_ir(preview_ir)
        save_preview_script(preview_ir)

        req["status"] = "preview_ready"
        req["message"] = "Preview created"
        req["preview_file"] = PREVIEW_SCENE_FILE.name
        req["preview_ir_file"] = PREVIEW_IR_FILE.name
        req["parsed_action"] = action
        write_json(AI_REQUEST_FILE, req)

        write_json(SCENE_STATE_FILE, {
            "mode": "preview",
            "active_script": str(PREVIEW_SCENE_FILE),
            "request_id": request_id
        })

    except Exception as e:
        req["status"] = "error"
        req["error"] = str(e)
        write_json(AI_REQUEST_FILE, req)
        traceback.print_exc()


def handle_ui_actions():
    ui = read_json(UI_STATE_FILE, default=None)
    if not ui:
        return

    action = ui.get("action")
    if action in (None, "idle", "error"):
        return

    print("[controller] UI action found:", ui)

    if action == "apply":
        try:
            promote_preview()
            clear_preview()

            write_json(UI_STATE_FILE, {"action": "idle"})

            req = read_json(AI_REQUEST_FILE, default={}) or {}
            if req:
                req["status"] = "applied"
                write_json(AI_REQUEST_FILE, req)

            write_json(SCENE_STATE_FILE, {
                "mode": "official",
                "active_script": str(SCENE_OUT_FILE),
                "request_id": ui.get("request_id")
            })

        except Exception as e:
            write_json(UI_STATE_FILE, {
                "action": "error",
                "message": str(e)
            })
            traceback.print_exc()

    elif action == "reject":
        clear_preview()
        write_json(UI_STATE_FILE, {"action": "idle"})

        req = read_json(AI_REQUEST_FILE, default={}) or {}
        if req:
            req["status"] = "rejected"
            write_json(AI_REQUEST_FILE, req)

        write_json(SCENE_STATE_FILE, {
            "mode": "official",
            "active_script": str(SCENE_OUT_FILE),
            "request_id": ui.get("request_id")
        })


def main():
    print("[controller] Started")
    ensure_shared_scene_ir()

    if not SCENE_STATE_FILE.exists():
        write_json(SCENE_STATE_FILE, {
            "mode": "official",
            "active_script": str(SCENE_OUT_FILE)
        })

    while True:
        handle_pending_ai_request()
        handle_ui_actions()
        time.sleep(0.5)


if __name__ == "__main__":
    main()