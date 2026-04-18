import json
import subprocess
import time
from pathlib import Path


SHARED_DIR = Path.home() / "Desktop" / "scene_bridge"
SHARED_DIR.mkdir(parents=True, exist_ok=True)

SCENE_STATE_FILE = SHARED_DIR / "scene_state.json"
OFFICIAL_SCENE_FILE = Path.home() / "Desktop" / "scene_out.py"
PREVIEW_SCENE_FILE = SHARED_DIR / "preview_scene.py"

POLL_INTERVAL = 0.5


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


def ensure_initial_state():
    if not SCENE_STATE_FILE.exists():
        write_json(SCENE_STATE_FILE, {
            "mode": "official",
            "active_script": str(OFFICIAL_SCENE_FILE)
        })


def normalize_script_path(scene_state: dict) -> Path:
    mode = scene_state.get("mode", "official")
    active_script = scene_state.get("active_script")

    if active_script:
        p = Path(active_script)
        if not p.is_absolute():
            p = SHARED_DIR / p
        return p

    if mode == "preview":
        return PREVIEW_SCENE_FILE

    return OFFICIAL_SCENE_FILE


def launch_scene(script_path: Path):
    if not script_path.exists():
        raise FileNotFoundError(f"Scene script not found: {script_path}")

    print(f"[supervisor] Launching: {script_path}")
    return subprocess.Popen(
        ["python", str(script_path)],
        cwd=str(script_path.parent)
    )


def stop_scene(proc):
    if proc is None:
        return

    if proc.poll() is not None:
        return

    print("[supervisor] Stopping current scene process...")
    proc.terminate()

    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        print("[supervisor] Force killing scene process...")
        proc.kill()
        proc.wait(timeout=5)


def main():
    print("[supervisor] Starting...")
    print("[supervisor] SHARED_DIR =", SHARED_DIR)
    print("[supervisor] SCENE_STATE_FILE =", SCENE_STATE_FILE)
    print("[supervisor] OFFICIAL_SCENE_FILE =", OFFICIAL_SCENE_FILE)
    print("[supervisor] PREVIEW_SCENE_FILE =", PREVIEW_SCENE_FILE)

    ensure_initial_state()

    current_proc = None
    current_script = None

    try:
        while True:
            scene_state = read_json(SCENE_STATE_FILE, default={}) or {}
            desired_script = normalize_script_path(scene_state)

            # Αν το process έκλεισε μόνο του, ξέχνα το handle
            if current_proc is not None and current_proc.poll() is not None:
                print("[supervisor] Scene process exited.")
                current_proc = None
                current_script = None

            # Αν θέλουμε άλλο script ή δεν υπάρχει process, κάνε launch/relaunch
            if current_proc is None or current_script != desired_script:
                stop_scene(current_proc)
                current_proc = launch_scene(desired_script)
                current_script = desired_script

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n[supervisor] Stopping...")
        stop_scene(current_proc)


if __name__ == "__main__":
    main()