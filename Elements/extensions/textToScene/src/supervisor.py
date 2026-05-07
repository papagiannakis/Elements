import json
import subprocess
import sys
import time
from pathlib import Path

try:
    from config import (
        OFFICIAL_SCENE_FILE,
        POLL_INTERVAL,
        PREVIEW_SCENE_FILE,
        SCENE_STATE_FILE,
        SHARED_DIR,
        ensure_runtime_dirs,
    )
except ImportError:
    from .config import (
        OFFICIAL_SCENE_FILE,
        POLL_INTERVAL,
        PREVIEW_SCENE_FILE,
        SCENE_STATE_FILE,
        SHARED_DIR,
        ensure_runtime_dirs,
    )


ensure_runtime_dirs()


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

    tmp_path.replace(path)


def ensure_initial_state():
    if not SCENE_STATE_FILE.exists():
        write_json(SCENE_STATE_FILE, {
            "mode": "official",
            "active_script": str(OFFICIAL_SCENE_FILE),
            "updated_at": time.time()
        })


def normalize_script_path(scene_state):
    if not isinstance(scene_state, dict):
        return OFFICIAL_SCENE_FILE

    mode = scene_state.get("mode", "official")
    active_script = scene_state.get("active_script")

    if active_script:
        path = Path(active_script)
        if not path.is_absolute():
            path = SHARED_DIR / path

        if mode == "preview" and path.exists():
            return path

        if mode == "official":
            return path

    if mode == "preview" and PREVIEW_SCENE_FILE.exists():
        return PREVIEW_SCENE_FILE

    return OFFICIAL_SCENE_FILE


def scene_state_key(scene_state, script_path):
    if not isinstance(scene_state, dict):
        return (str(script_path), None)

    return (
        str(script_path),
        scene_state.get("mode"),
        scene_state.get("request_id"),
        scene_state.get("updated_at")
    )


def launch_scene(script_path):
    script_path = Path(script_path)

    if not script_path.exists():
        raise FileNotFoundError("Scene script not found: " + str(script_path))

    print("[supervisor] Launching:", script_path)

    return subprocess.Popen(
        [sys.executable, str(script_path)],
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
    print("[supervisor] Starting.")
    print("[supervisor] SHARED_DIR =", SHARED_DIR)
    print("[supervisor] SCENE_STATE_FILE =", SCENE_STATE_FILE)
    print("[supervisor] OFFICIAL_SCENE_FILE =", OFFICIAL_SCENE_FILE)
    print("[supervisor] PREVIEW_SCENE_FILE =", PREVIEW_SCENE_FILE)

    ensure_initial_state()

    current_proc = None
    current_key = None

    try:
        while True:
            scene_state = read_json(SCENE_STATE_FILE, default={}) or {}
            desired_script = normalize_script_path(scene_state)
            desired_key = scene_state_key(scene_state, desired_script)

            if current_proc is not None and current_proc.poll() is not None:
                print("[supervisor] Scene process exited.")
                current_proc = None
                current_key = None

            if current_proc is None or current_key != desired_key:
                stop_scene(current_proc)
                current_proc = launch_scene(desired_script)
                current_key = desired_key

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("")
        print("[supervisor] Stopping.")
        stop_scene(current_proc)


if __name__ == "__main__":
    main()
