import json
import os
import re
import time
from copy import deepcopy
from pathlib import Path

from openai import OpenAI

API_KEY_ENV = "OPENAI_API_KEY"
DEFAULT_MODEL = "gpt-4.1-mini"

SHARED_DIR = Path.home() / "Desktop" / "scene_bridge"
CACHE_DIR = SHARED_DIR / "cache"
ACTION_CACHE_FILE = CACHE_DIR / "action_cache.json"

def get_client():
    api_key = os.getenv(API_KEY_ENV)
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY environment variable")
    return OpenAI()


def build_scene_context(scene_ir):
    objects = []

    def walk(node):
        if not isinstance(node, dict):
            return
        if node.get("node_type") == "mesh_object":
            material = node.get("material", {})
            transform = node.get("transform", {})
            objects.append({
                "name": node.get("name"),
                "id": node.get("id"),
                "shape": node.get("shape"),
                "color": material.get("color"),
                "position": transform.get("position"),
                "scale": transform.get("scale"),
                "created_order": node.get("created_order")
            })
        for child in node.get("children", []):
            walk(child)

    walk(scene_ir)
    return {"objects": objects}


def build_prompt(prompt, scene_context):
    return """
You are a scene-editing parser.

Convert the user request into strict JSON only.
Do not return markdown.
Do not return explanations.
Do not return code fences.

Allowed actions:
- add_object
- move_object
- delete_object
- recolor_object
- scale_object
- new_scene
- save_scene
- undo

Allowed object_type values:
- cube
- sphere
- cylinder
- cone
- pyramid
- plane

Allowed color names:
- red
- green
- blue
- yellow
- white
- black
- purple

Return only one valid JSON object.

User prompt:
%s

Scene context:
%s
""" % (prompt, json.dumps(scene_context, ensure_ascii=False))


def normalize_prompt(prompt):
    text = str(prompt or "").strip().lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"[_\s]+", " ", text, flags=re.UNICODE)
    return text.strip()


def load_action_cache():
    if not ACTION_CACHE_FILE.exists():
        return {}

    try:
        with open(str(ACTION_CACHE_FILE), "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}

    if isinstance(data, dict):
        entries = data.get("entries")
        if isinstance(entries, dict):
            return entries
        return data

    return {}


def save_action_cache(cache):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "version": 1,
        "updated_at": time.time(),
        "entries": cache
    }

    tmp_path = ACTION_CACHE_FILE.with_suffix(ACTION_CACHE_FILE.suffix + ".tmp")
    with open(str(tmp_path), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    os.replace(str(tmp_path), str(ACTION_CACHE_FILE))


def lookup_cached_action(prompt):
    normalized = normalize_prompt(prompt)
    if not normalized:
        return None

    cache = load_action_cache()
    entry = cache.get(normalized)

    if isinstance(entry, dict) and "action" in entry:
        return deepcopy(entry.get("action"))

    if isinstance(entry, dict):
        return deepcopy(entry)

    return None


def store_cached_action(prompt, action):
    normalized = normalize_prompt(prompt)
    if not normalized or not isinstance(action, dict):
        return

    cache = load_action_cache()
    cache[normalized] = {
        "prompt": str(prompt or ""),
        "normalized_prompt": normalized,
        "action": deepcopy(action),
        "updated_at": time.time()
    }
    save_action_cache(cache)


def extract_json_object(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")

    return text[start:end + 1]


def parse_prompt_to_action_with_llm(prompt, scene_ir, model_name=None):
    client = get_client()
    scene_context = build_scene_context(scene_ir)
    full_prompt = build_prompt(prompt, scene_context)

    response = client.responses.create(
        model=model_name or DEFAULT_MODEL,
        input=full_prompt
    )

    raw_text = getattr(response, "output_text", None)
    if not raw_text:
        raise ValueError("OpenAI returned empty text")

    json_text = extract_json_object(raw_text)
    action = json.loads(json_text)

    if not isinstance(action, dict):
        raise ValueError("LLM output must be a JSON object")

    if "action" not in action:
        raise ValueError("LLM output missing 'action' field")

    return action