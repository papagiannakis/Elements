from dotenv import load_dotenv
import os

load_dotenv()
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Debug - check if key is loaded
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    print(f"WARNING: OPENAI_API_KEY not found. Checked {env_path}")
    print(f".env exists: {env_path.exists()}")
else:
    print(f"[config] API key loaded (length: {len(OPENAI_API_KEY)})")
"""
Central configuration for the Text-to-Scene extension.

This module defines all runtime paths, generated files, bridge files,
model settings, and layout constants used by the controller, parser,
supervisor, and code generator.
"""
import os 
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent
EXTENSION_DIR = SRC_DIR.parent
DESKTOP_DIR = Path.home() / "Desktop"

SHARED_DIR = DESKTOP_DIR / "scene_bridge"
HISTORY_DIR = SHARED_DIR / "history"
SAVED_SCENES_DIR = SHARED_DIR / "saved_scenes"
PREFABS_DIR = SHARED_DIR / "prefabs"
CACHE_DIR = SHARED_DIR / "cache"

TEXTURES_DIR = SHARED_DIR / "textures"

TEXTURE_CATALOGUE = {
    "brick":    "brick.jpg",
    "wood":     "wood.jpg",
    "stone":    "stone.jpg",
    "grass":    "grass.jpg",
    "metal":    "metal.jpg",
    "sand":     "sand.jpg",
    "marble":   "marble.jpg",
    "concrete": "concrete.jpg",
}

CUSTOM_MODELS_DIR = SHARED_DIR / "custom_models"

PROJECT_SCENE_IR_FILE = SRC_DIR / "scene_ir.json"
SCENE_IR_FILE = SHARED_DIR / "scene_ir.json"
PREVIEW_IR_FILE = SHARED_DIR / "preview_scene_ir.json"
AI_REQUEST_FILE = SHARED_DIR / "ai_request.json"
UI_STATE_FILE = SHARED_DIR / "ui_state.json"
SCENE_STATE_FILE = SHARED_DIR / "scene_state.json"
HISTORY_STACK_FILE = HISTORY_DIR / "undo_stack.json"
ACTION_CACHE_FILE = CACHE_DIR / "action_cache.json"

SCENE_OUT_FILE = DESKTOP_DIR / "scene_out.py"
OFFICIAL_SCENE_FILE = SCENE_OUT_FILE
PREVIEW_SCENE_FILE = SHARED_DIR / "preview_scene.py"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
DEFAULT_MODEL = "gpt-4.1-mini"

POLL_INTERVAL = 0.5
GRID_SPACING = 1.5
CUBE_Y = 0.5
CUBE_Z = 0.0


def ensure_runtime_dirs():
    for path in (SHARED_DIR, HISTORY_DIR, SAVED_SCENES_DIR, PREFABS_DIR, CACHE_DIR, TEXTURES_DIR, CUSTOM_MODELS_DIR):
        path.mkdir(parents=True, exist_ok=True)