import time 
import json
import os 
import subprocess
from copy import deepcopy

# ai key den exwwwww
DESKTOP_PATH = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
TASK_FILE = os.path.join(DESKTOP_PATH, "ai_task.json")

def process_with_ai(command):
    # pseftiko dummy tha mpei gemini prompt
    print(f"Processing command with ai: {command}")
    print("[AI] Received command, processing...")
    time.sleep(2)  # Simulate processing time
    print("[AI] Command processed successfully.")
    return True

def main_loop():
    print("--- AI Controller (Desktop Monitor) Started ---")
    print(f"Watching file: {TASK_FILE}")
    
    while True:
        if os.path.exists(TASK_FILE):
            try:
                with open(TASK_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                if data.get("status") == "pending":
                    command = data.get("command")
                    if process_with_ai(command):
                        data["status"] = "completed"
                        with open(TASK_FILE, "w", encoding="utf-8") as f:
                            json.dump(data, f)
                        print("[System] Task completed and updated on Desktop.")
            except Exception as e:
                print(f"Error processing AI task: {e}")
        time.sleep(1)  # Check every second

if __name__ == "__main__":
    main_loop()

def apply_prompt_to_ir(scene_ir, prompt: str):
    text = prompt.lower().strip()
    new_ir = deepcopy(scene_ir)

    if "κόκκινο κύβο" in text or "red cube" in text:
        new_ir["children"].append({
            "node_type": "mesh_object",
            "name": "cube_preview_1",
            "shape": "cube",
            "transform": {
                "position": [0.0, 1.5, 0.0],
                "scale": [1.0, 1.0, 1.0]
            },
            "material": {
                "color": [1.0, 0.0, 0.0],
                "texture": {
                    "enabled": False,
                    "path": None
                }
            }
        })
        return new_ir

    if "red cube" in text or "cube" in text:
        new_ir["children"].append({
            "node_type": "mesh_object",
            "name": "cube_preview_1",
            "shape": "cube",
            "transform": {
                "position": [0.0, 1.5, 0.0],
                "scale": [1.0, 1.0, 1.0]
            },
            "material": {
                "color": [0.8, 0.0, 0.8],
                "texture": {
                    "enabled": False,
                    "path": None
                }
            }
        })
        return new_ir

    raise ValueError("Δεν υποστηρίζεται ακόμα αυτό το prompt")