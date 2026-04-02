import time 
import json
import os 
import subprocess

# ai key den exwwwww

def process_with_ai(command):
    # pseftiko dummy tha mpei gemini prompt
    print(f"Processing command with ai: {command}")
    print("[AI] Received command, processing...")
    time.sleep(2)  # Simulate processing time
    print("[AI] Command processed successfully.")
    return True

def main_loop():
    print("Starting AI Controller...")
    print(f"working directory: {os.getcwd()}")
    print("Waiting for ai_task.json to appear...")
    while True: 
        if os.path.exists("ai_task.json"):
            try: 
                with open("ai_task.json", "r", encoding="utf-8") as f:
                    data = json.load(f)

                
                if data.get("status") == "pending":
                    command = data.get("command", "")
                    success = process_with_ai(command)
                    if success:
                        print("AI processing completed successfully.")
                        data["status"] = "completed"
                        with open("ai_task.json", "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=4)
                        print("[system] Updated ai_task.json with completed status.")
            except Exception as e:
                print(f"Error processing AI task: {e}")
        time.sleep(1)  # Check every second

if __name__ == "__main__":
    main_loop()
