"""
Central configuration for the Text-to-Scene extension.

Defines all runtime paths, bridge files, model settings, and layout constants
used by the controller, parser, supervisor, and code generator.
"""
import os
import os.path
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (textToScene/.env)
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

# ── Directory layout ──────────────────────────────────────────────────────────
SRC_DIR       = Path(__file__).resolve().parent
EXTENSION_DIR = SRC_DIR.parent          # extensions/textToScene/
DESKTOP_DIR   = Path.home() / "Desktop"

# Runtime state lives in ~/.textToScene/ — inside the user's home directory,
# NOT on the Desktop. This directory is always writable on all platforms.
RUNTIME_DIR     = Path.home() / ".textToScene"
SHARED_DIR      = RUNTIME_DIR / "scene_bridge"
HISTORY_DIR     = SHARED_DIR  / "history"
SAVED_SCENES_DIR= SHARED_DIR  / "saved_scenes"
PREFABS_DIR     = SHARED_DIR  / "prefabs"
CACHE_DIR       = SHARED_DIR  / "cache"
TEXTURES_DIR    = SHARED_DIR  / "textures"
CUSTOM_MODELS_DIR = SHARED_DIR / "custom_models"

# ── File paths ────────────────────────────────────────────────────────────────
PROJECT_SCENE_IR_FILE = SRC_DIR / "scene_ir.json"

SCENE_IR_FILE     = SHARED_DIR  / "scene_ir.json"
PREVIEW_IR_FILE   = SHARED_DIR  / "preview_scene_ir.json"
AI_REQUEST_FILE   = SHARED_DIR  / "ai_request.json"
UI_STATE_FILE     = SHARED_DIR  / "ui_state.json"
SCENE_STATE_FILE  = SHARED_DIR  / "scene_state.json"
HISTORY_STACK_FILE= HISTORY_DIR / "undo_stack.json"
ACTION_CACHE_FILE = CACHE_DIR   / "action_cache.json"

SCENE_OUT_FILE      = RUNTIME_DIR / "scene_out.py"
OFFICIAL_SCENE_FILE = SCENE_OUT_FILE
PREVIEW_SCENE_FILE  = SHARED_DIR  / "preview_scene.py"

# ── API keys & model ──────────────────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ── LLM model selection ───────────────────────────────────────────────────────
# Uncomment the backend you want to use and set the matching API key in .env.
#
# Google Gemini (requires GEMINI_API_KEY):
DEFAULT_MODEL = "gemini-2.5-flash-lite"   # fastest / best accuracy in eval
# DEFAULT_MODEL = "gemini-2.5-flash"      # larger Gemini model — more capable
#
# OpenAI (requires OPENAI_API_KEY):
# DEFAULT_MODEL = "gpt-4o-mini"           # fast and cheap
# DEFAULT_MODEL = "gpt-4.1-mini"          # newer OpenAI mini model

# ── Layout constants ──────────────────────────────────────────────────────────
POLL_INTERVAL  = 0.5
GRID_SPACING   = 1.5
CUBE_Y         = 0.5
CUBE_Z         = 0.0

# ── Texture catalogue ─────────────────────────────────────────────────────────
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


def ensure_runtime_dirs():
    """Create all runtime directories that must exist before the system starts."""
    for path in (
        RUNTIME_DIR, SHARED_DIR, HISTORY_DIR, SAVED_SCENES_DIR, PREFABS_DIR,
        CACHE_DIR, TEXTURES_DIR, CUSTOM_MODELS_DIR,
    ):
        os.makedirs(str(path), exist_ok=True)
