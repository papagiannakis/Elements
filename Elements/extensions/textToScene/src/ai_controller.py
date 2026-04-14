import time 
import json
import os 
import subprocess

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
