import json
import time
import shutil
from copy import deepcopy
from pathlib import Path

from code_generator import generate_scene_script
PROJECT_DIR = Path(__file__).resolve().parent
SHARED_DIR = Path.home() / "Desktop" / "scene_bridge"
SHARED_DIR.mkdir(parents=True, exist_ok=True)

SCENE_IR_FILE = PROJECT_DIR / "scene_ir.json"
PREVIEW_IR_FILE = SHARED_DIR / "preview_scene_ir.json"
AI_REQUEST_FILE = SHARED_DIR / "ai_request.json"
UI_STATE_FILE = SHARED_DIR / "ui_state.json"
SCENE_OUT_FILE = Path.home() / "Desktop" / "scene_out.py"
PREVIEW_SCENE_FILE = SHARED_DIR / "preview_scene.py"
def read_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def write_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_text(path: Path, text: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def load_scene_ir():
    data = read_json(SCENE_IR_FILE, default=None)
    if data is None:
        raise FileNotFoundError(f"Δεν βρέθηκε το {SCENE_IR_FILE.name}")
    return data


def save_preview_ir(scene_ir):
    write_json(PREVIEW_IR_FILE, scene_ir)


def save_preview_script(scene_ir):
    script = generate_scene_script(scene_ir)
    save_text(PREVIEW_SCENE_FILE, script)


def promote_preview():
    if not PREVIEW_IR_FILE.exists():
        raise FileNotFoundError("Δεν υπάρχει preview_scene_ir.json")
    if not PREVIEW_SCENE_FILE.exists():
        raise FileNotFoundError("Δεν υπάρχει preview_scene.py")

    shutil.copy2(PREVIEW_IR_FILE, SCENE_IR_FILE)
    shutil.copy2(PREVIEW_SCENE_FILE, SCENE_OUT_FILE)


def clear_preview():
    if PREVIEW_IR_FILE.exists():
        PREVIEW_IR_FILE.unlink()
    if PREVIEW_SCENE_FILE.exists():
        PREVIEW_SCENE_FILE.unlink()


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


def detect_color_from_text(text):
    if "κόκκινο" in text or "red" in text:
        return [1.0, 0.0, 0.0]
    if "μπλε" in text or "blue" in text:
        return [0.0, 0.0, 1.0]
    if "πράσινο" in text or "green" in text:
        return [0.0, 1.0, 0.0]

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


def apply_mock_ai_prompt(scene_ir, prompt: str):
    """
    Rule-based 'fake AI' για δοκιμές χωρίς API key.
    """
    text = prompt.lower().strip()
    new_ir = deepcopy(scene_ir)
    color = detect_color_from_text(text)

    # περίπτωση: "βάλε έναν ... κύβο πάνω στον κύβο"
    if ("κύβο" in text or "cube" in text) and ("πάνω" in text or "on top" in text):
        target_cube = find_first_cube(new_ir)
        if target_cube is None:
            raise ValueError("Δεν βρήκα υπάρχοντα κύβο για να βάλω άλλον πάνω του.")

        target_pos = target_cube.get("transform", {}).get("position", [0.0, 0.5, 0.0])
        target_scale = target_cube.get("transform", {}).get("scale", [1.0, 1.0, 1.0])

        new_pos = [
            float(target_pos[0]),
            float(target_pos[1]) + float(target_scale[1]),
            float(target_pos[2])
        ]

        new_cube = make_cube_node(new_ir, new_pos, color)
        ensure_scene_children(new_ir).append(new_cube)
        return new_ir

    # περίπτωση: "βάλε έναν ... κύβο"
    if "κύβο" in text or "cube" in text:
        new_cube = make_cube_node(new_ir, [0.0, 1.5, 0.0], color)
        ensure_scene_children(new_ir).append(new_cube)
        return new_ir

    raise ValueError("Δεν υποστηρίζεται ακόμα αυτή η εντολή.")


def handle_pending_ai_request():
    req = read_json(AI_REQUEST_FILE, default=None)
    if not req:
        return
    print("[controller] AI request found:", req)

    if req.get("status") != "pending":
        return

    request_id = req.get("request_id")
    prompt = req.get("prompt", "").strip()

    if not prompt:
        req["status"] = "error"
        req["error"] = "Empty prompt"
        write_json(AI_REQUEST_FILE, req)
        return

    try:
        scene_ir = load_scene_ir()
        preview_ir = apply_mock_ai_prompt(scene_ir, prompt)

        save_preview_ir(preview_ir)
        save_preview_script(preview_ir)

        req["status"] = "preview_ready"
        req["message"] = "Το preview δημιουργήθηκε."
        req["preview_file"] = PREVIEW_SCENE_FILE.name
        req["preview_ir_file"] = PREVIEW_IR_FILE.name
        write_json(AI_REQUEST_FILE, req)

        write_json(UI_STATE_FILE, {
            "action": "preview_ready",
            "request_id": request_id,
            "message": "Preview is ready"
        })

        print(f"[controller] Preview ready for request {request_id}")

    except Exception as e:
        req["status"] = "error"
        req["error"] = str(e)
        write_json(AI_REQUEST_FILE, req)
        print(f"[controller] Error: {e}")


def handle_ui_actions():
    ui = read_json(UI_STATE_FILE, default=None)
    if not ui:
        return
    print("[controller] UI action found:", ui)
    action = ui.get("action")

    if action == "apply":
        try:
            promote_preview()
            write_json(UI_STATE_FILE, {
                "action": "applied",
                "message": "Το preview έγινε επίσημη σκηνή."
            })
            print("[controller] Preview applied")
        except Exception as e:
            write_json(UI_STATE_FILE, {
                "action": "error",
                "message": str(e)
            })
            print(f"[controller] Apply error: {e}")

    elif action == "reject":
        clear_preview()
        write_json(UI_STATE_FILE, {
            "action": "rejected",
            "message": "Το preview απορρίφθηκε."
        })
        print("[controller] Preview rejected")


def main():
    print("[controller] Mock AI controller started.")
    print("[controller] Mock AI controller started.")
    print("[controller] PROJECT_DIR =", PROJECT_DIR)
    print("[controller] SHARED_DIR  =", SHARED_DIR)
    print("[controller] AI_REQUEST_FILE =", AI_REQUEST_FILE)
    print("[controller] UI_STATE_FILE   =", UI_STATE_FILE)
    print("[controller] SCENE_IR_FILE   =", SCENE_IR_FILE)
    print("[controller] SCENE_OUT_FILE  =", SCENE_OUT_FILE)
    while True:
        handle_pending_ai_request()
        handle_ui_actions()
        time.sleep(0.5)


if __name__ == "__main__":
    main()