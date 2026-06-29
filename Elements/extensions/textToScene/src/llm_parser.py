import json
import os
import re
import time
from copy import deepcopy
from pathlib import Path

from openai import OpenAI

try:
    from config import ACTION_CACHE_FILE, OPENAI_API_KEY, GEMINI_API_KEY, CACHE_DIR, DEFAULT_MODEL
except ImportError:
    from .config import ACTION_CACHE_FILE, OPENAI_API_KEY, GEMINI_API_KEY, CACHE_DIR, DEFAULT_MODEL

ACTION_SEQUENCE_ALIASES = (
    "action_sequence",
    "steps",
    "sequence",
    "actions",
)

SCENE_DEPENDENT_KEYS = {
    "id",
    "object_id",
    "object_ids",
    "position",
    "new_position",
}


def get_client():
    if not OPENAI_API_KEY:
        raise RuntimeError("Missing OPENAI_API_KEY environment variable")
    return OpenAI(api_key=OPENAI_API_KEY)


# ------------------------------------------------------------------
# Low-level API callers — one per provider
# ------------------------------------------------------------------

def _call_openai(model_name, prompt_text):
    """Call OpenAI Responses API. Returns (text, tokens_in, tokens_out)."""
    client = get_client()
    response = client.responses.create(model=model_name, input=prompt_text)
    text = getattr(response, "output_text", None)
    if not text:
        raise ValueError("OpenAI returned empty response")
    usage = getattr(response, "usage", None)
    tokens_in  = int(getattr(usage, "input_tokens",  0) or 0) if usage else 0
    tokens_out = int(getattr(usage, "output_tokens", 0) or 0) if usage else 0
    return text, tokens_in, tokens_out


def _call_gemini(model_name, prompt_text):
    """Call Google Gemini API. Returns (text, tokens_in, tokens_out).

    Uses the google-genai SDK (pip install google-genai).
    Retries up to 3 times on 429 rate-limit errors with exponential backoff.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set. Add it to your .env file.")
    try:
        from google import genai as google_genai
        from google.genai import errors as genai_errors
    except ImportError:
        raise RuntimeError(
            "Google GenAI package not installed.\nRun: pip install google-genai"
        )

    client = google_genai.Client(api_key=GEMINI_API_KEY)

    max_retries = 3
    wait = 30  # seconds – free tier allows ~15 req/min
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt_text,
            )
            text = response.text
            usage = getattr(response, "usage_metadata", None)
            tokens_in  = int(getattr(usage, "prompt_token_count",     0) or 0) if usage else 0
            tokens_out = int(getattr(usage, "candidates_token_count", 0) or 0) if usage else 0
            return text, tokens_in, tokens_out
        except genai_errors.ClientError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if attempt < max_retries - 1:
                    print(f"\n  [Gemini] Rate limit hit — waiting {wait}s before retry {attempt + 2}/{max_retries}...")
                    time.sleep(wait)
                    wait *= 2  # exponential backoff
                else:
                    raise RuntimeError(
                        f"Gemini quota exhausted after {max_retries} retries.\n"
                        "Options:\n"
                        "  1. Enable billing at https://ai.google.dev\n"
                        "  2. Wait and retry later\n"
                        f"  Original error: {e}"
                    )
            else:
                raise


def _call_llm(model_name, prompt_text):
    """Route to the appropriate provider based on model name prefix."""
    if str(model_name).lower().startswith("gemini"):
        return _call_gemini(model_name, prompt_text)
    return _call_openai(model_name, prompt_text)


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
You are a strict scene-editing parser.

Return exactly one JSON object.
Do not return markdown.
Do not return explanations.
Do not return code fences.
Do not return any extra text.

The top-level JSON object must always contain an "action" field.

Allowed top-level action values:
- add_object
- move_object
- delete_object
- recolor_object
- scale_object
- rotate_object
- new_scene
- save_scene
- load_scene
- add_prefab
- undo
- action_sequence
- generate_pattern
- generate_composite
- apply_texture
- remove_texture
- add_custom_model
- add_light
- delete_light
- move_light
- change_light_color
- change_light_intensity
- animate_object

If the request needs multiple steps (e.g. "add X and move it Y", "create X and make it bigger"), use:
{
  "action": "action_sequence",
  "action_sequence": [
    { "action": "..." },
    { "action": "..." }
  ]
}

Rules:
- Every action inside action_sequence must also contain its own top-level "action".
- Do not nest action_sequence inside another action_sequence.
- If you refer to an existing object, prefer abstract references like "target".
- Avoid scene-specific ids unless the scene context makes them necessary.
- Return valid JSON only.
- For rotate_object: use the canonical schema { "action": "rotate_object", "target": "...", "axis": "x|y|z", "degrees": <number> }.
- For rotate_object: if the user does not specify an axis, default to "y".
- For rotate_object: if the user says only "rotate" without an amount, default to 45 degrees.
- For scale_object: "make it bigger" → factor 1.5, "make it smaller" → factor 0.66, "double" → factor 2.0, "half" → factor 0.5.
- For apply_texture, texture_name must be one of: brick, wood, stone, grass, metal, sand, marble, concrete
- model_path must be a filename (no directories) ending in .usd or .obj
- The file must exist in the custom_models directory
- Bundled 3D models available by name (use add_custom_model with their full keyword as model_path):
  chameleon → chameleon_anim_mtl_variant.usdz
  baseball / ball → ball_baseball_realistic.usdz
  teapot → teapot.usdz
  frank → Frank.usdz
  When the user says "load a chameleon", "add a teapot", etc., use add_custom_model with the keyword as model_path.
- add_prefab vs generate_composite: use add_prefab when the user says "add a/an [object]" or "add prefab [name]" with NO shape specified. Use generate_composite when the user says "make a [object] with [shape]" or "make a [object] using [shape]" — the explicit shape keyword signals procedural generation.

Allowed object_type values:
- cube
- sphere
- cylinder
- cone
- pyramid
- plane

Color: any CSS color name or hex code (e.g. "red", "teal", "#FF5733")
Examples:
{
  "action": "add_object",
  "object_type": "cube",
  "color": "red"
}

Allowed direction values for move_object: right, left, up, down, forward, backward

{
  "action": "move_object",
  "target": "blue cube",
  "direction": "right"
}

{
  "action": "move_object",
  "target": "red sphere",
  "direction": "up"
}

{
  "action": "delete_object",
  "target": "red cube"
}

{
  "action": "scale_object",
  "target": "red cube",
  "factor": 2.0
}

{
  "action": "scale_object",
  "target": "cube_1",
  "scale": [1.0, 2.0, 1.0]
}

Allowed axis values for rotate_object: x, y, z

{
  "action": "rotate_object",
  "target": "cube",
  "axis": "y",
  "degrees": 45
}

{
  "action": "rotate_object",
  "target": "red cube",
  "axis": "y",
  "degrees": 45
}

{
  "action": "rotate_object",
  "target": "cube",
  "axis": "y",
  "degrees": 45
}

{
  "action": "rotate_object",
  "target": "cube",
  "axis": "y",
  "degrees": 90
}

{
  "action": "action_sequence",
  "action_sequence": [
    {
      "action": "add_object",
      "object_type": "cube",
      "color": "purple"
    },
    {
      "action": "move_object",
      "target": "purple cube",
      "direction": "right"
    }
  ]
}

{
  "action": "action_sequence",
  "action_sequence": [
    {
      "action": "add_object",
      "object_type": "sphere",
      "color": "green"
    },
    {
      "action": "scale_object",
      "target": "green sphere",
      "factor": 1.5
    }
  ]
}

{
  "action": "add_object",
  "object_type": "sphere",
  "color": "blue",
  "placement": {
    "relation": "on_top_of",
    "target": "red cube"
  }
}

{
  "action": "action_sequence",
  "action_sequence": [
    {
      "action": "add_object",
      "object_type": "cylinder",
      "color": "white"
    },
    {
      "action": "add_object",
      "object_type": "cube",
      "color": "purple",
      "placement": {
        "relation": "on_top_of",
        "target": "white cylinder"
      }
    }
  ]
}

{
  "action": "save_scene"
}

{
  "action": "save_scene",
  "scene_name": "my_tower"
}

{
  "action": "load_scene",
  "scene_name": "my_tower"
}

Available prefab names: house, tree, chair, bench, bed, table, lamp, street_light, gift_box

{
  "action": "add_prefab",
  "prefab_name": "tree"
}

{
  "action": "add_prefab",
  "prefab_name": "house"
}

{
  "action": "add_prefab",
  "prefab_name": "table"
}

{
  "action": "add_prefab",
  "prefab_name": "lamp"
}

Use generate_pattern for procedural arrangements of identical objects.
Supported pattern values: ring

generate_pattern schema:
{
  "action": "generate_pattern",
  "pattern": "ring",
  "object_type": "<shape>",
  "count": <integer, 2-32>,
  "radius": <float, default 2.5>,
  "color": "<color name>"
}

Examples:
{
  "action": "generate_pattern",
  "pattern": "ring",
  "object_type": "cube",
  "count": 8,
  "radius": 2.5,
  "color": "red"
}

{
  "action": "generate_pattern",
  "pattern": "ring",
  "object_type": "sphere",
  "count": 12,
  "radius": 3.0,
  "color": "blue"
}

Use generate_composite for multi-part procedural structures built from a specified primitive shape.
Supported composite values: tree, table, lamp, house, chair, bed, bench, fence, and any other named real-world object.
Use this action when the user says "make a [object] with [shape]" or "make a [object] using [shape]".

generate_composite schema:
{
  "action": "generate_composite",
  "composite": "<object name>",
  "object_type": "<shape>",
  "color": "<color name>"
}

Examples:
{
  "action": "generate_composite",
  "composite": "tree",
  "object_type": "cylinder",
  "color": "green"
}

{
  "action": "generate_composite",
  "composite": "house",
  "object_type": "cube",
  "color": "white"
}

{
  "action": "generate_composite",
  "composite": "table",
  "object_type": "cube",
  "color": "brown"
}

{
  "action": "generate_composite",
  "composite": "fence",
  "object_type": "cube",
  "color": "gray"
}

{
  "action": "apply_texture",
  "target": "red cube",
  "texture_name": "brick"
}

{
  "action": "remove_texture",
  "target": "cube_1"
}
Light actions:
- add_light: add a point or directional light. light_type defaults to "point".
- delete_light: remove a light by name or target description.
- move_light: move a point light to a new position.
- change_light_color: change the color of a light.
- change_light_intensity: change the brightness of a light (float, e.g. 0.5–2.0).
- For add_light, light_type must be "point" or "directional".
- For directional lights, use "direction": [x, y, z] instead of "position".
- For point lights, "position": [x, y, z] is optional (defaults to [2.0, 5.5, 2.0]).
- color for lights follows the same allowed color names as objects.

{
  "action": "add_light",
  "light_type": "point",
  "color": "white",
  "intensity": 1.2,
  "position": [3.0, 5.0, 3.0]
}

{
  "action": "add_light",
  "light_type": "directional",
  "color": "white",
  "intensity": 1.0,
  "direction": [1.0, -1.0, -1.0]
}

{
  "action": "delete_light",
  "target": "light_1"
}

{
  "action": "move_light",
  "target": "light_1",
  "position": [0.0, 8.0, 0.0]
}

{
  "action": "change_light_color",
  "target": "light_1",
  "color": "orange"
}

{
  "action": "change_light_intensity",
  "target": "light_1",
  "intensity": 0.5
}

User prompt:
%s

Scene context:
%s
""" % (prompt, json.dumps(scene_context, ensure_ascii=False))

_FILLER_WORDS = frozenset({"a", "an", "the", "please"})

def normalize_prompt(prompt):
    text = str(prompt or "").strip().lower()
    # Replace punctuation and underscores with spaces
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"_+", " ", text)
    # Remove filler words (whole-word match via split, no partial removal)
    tokens = [t for t in text.split() if t not in _FILLER_WORDS]
    # Collapse whitespace
    return " ".join(tokens)


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


def _contains_scene_dependent_fields(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in SCENE_DEPENDENT_KEYS:
                return True
            if _contains_scene_dependent_fields(item):
                return True
        return False

    if isinstance(value, list):
        for item in value:
            if _contains_scene_dependent_fields(item):
                return True
        return False

    return False


def is_cacheable_action(action):
    if not isinstance(action, dict):
        return False

    action_name = str(action.get("action", "")).strip().lower()

    if action_name == "action_sequence":
        sequence = action.get("action_sequence")
        if not isinstance(sequence, list) or not sequence:
            return False

        for step in sequence:
            if not is_cacheable_action(step):
                return False

        return True

    _CACHEABLE = {"add_object", "generate_pattern", "generate_composite"}
    if action_name not in _CACHEABLE:
        return False

    if _contains_scene_dependent_fields(action):
        return False

    if action_name == "add_object":
        placement = action.get("placement", {})
        if isinstance(placement, dict):
            if placement.get("target"):
                return False
            relation = str(placement.get("relation", "")).strip().lower()
            if relation and relation != "next_free_slot":
                return False

    return True


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

    if not is_cacheable_action(action):
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


def normalize_parsed_action(action):
    if not isinstance(action, dict):
        raise ValueError("LLM output must be a JSON object")

    normalized = deepcopy(action)

    if "action" not in normalized:
        for alias in ACTION_SEQUENCE_ALIASES:
            value = normalized.get(alias)
            if isinstance(value, list):
                normalized["action"] = "action_sequence"
                normalized["action_sequence"] = value
                break

    if normalized.get("action") == "composite":
        normalized["action"] = "action_sequence"

    if normalized.get("action") == "rotate":
        normalized["action"] = "rotate_object"

    if normalized.get("action") == "rotate_object":
        if "name" in normalized and "target" not in normalized:
            normalized["target"] = normalized.pop("name")
        if "object" in normalized and "target" not in normalized:
            normalized["target"] = normalized.pop("object")
        if "angle" in normalized and "degrees" not in normalized:
            normalized["degrees"] = normalized.pop("angle")

    if "action" not in normalized:
        raise ValueError("LLM output missing 'action' field")

    if normalized.get("action") == "action_sequence":
        sequence = normalized.get("action_sequence")
        if not isinstance(sequence, list) or not sequence:
            raise ValueError("LLM output action_sequence must be a non-empty list")

        for step in sequence:
            if not isinstance(step, dict):
                raise ValueError("Each action_sequence step must be a JSON object")
            if "action" not in step:
                raise ValueError("Each action_sequence step must contain 'action'")

    return normalized


def build_composite_spec_prompt(object_name, primitive_type):
    return """
You are a 3D scene layout designer. Describe a real-world object as a list of non-overlapping 3D primitive parts.

Object to design: {object_name}
Preferred primitive shape: {primitive_type}

Return exactly one JSON object. No markdown, no code fences, no extra text.

Format:
{{
  "parts": [
    {{"name": "part_name", "shape": "cube", "position": [x, y, z], "scale": [sx, sy, sz]}},
    ...
  ]
}}

Spatial rules — CRITICAL, violations will break the scene:
1. Each part occupies the box  [x - sx/2, x + sx/2]  x  [y - sy/2, y + sy/2]  x  [z - sz/2, z + sz/2].
2. No two parts may share interior volume — bounding boxes must NOT intersect.
3. Ground plane is y = 0. Every part must satisfy  y >= sy/2  (bottom edge at or above ground).
4. To stack B directly on top of A:  B_y = A_y + A_sy/2 + B_sy/2.
5. To place B beside A along X:  |B_x - A_x| >= (A_sx + B_sx) / 2.

Work through the layout step by step before writing the JSON:
  a. Place the lowest / largest part first (set its y so the bottom touches y = 0).
  b. Stack or offset each subsequent part so its bounding box clears all previous parts.
  c. Verify every pair is non-overlapping before writing the JSON.

Other rules:
- Use 3 to 8 parts with unique descriptive names.
- Each part must have: "name", "shape" (one of: cube, sphere, cylinder, cone, pyramid, plane), "position" ([x,y,z] floats), "scale" ([sx,sy,sz] positive floats).
- Total footprint: 1–3 units per axis.
- Prefer the specified primitive; other shapes allowed for detail parts.
- Do NOT use "rectangular_prism" — use "cube" for box shapes.
- Return only the JSON object.

Example — a floor lamp (3 parts, stacked vertically, no overlap):
{{
  "parts": [
    {{"name": "base",  "shape": "cylinder", "position": [0.0, 0.10, 0.0], "scale": [0.5, 0.20, 0.5]}},
    {{"name": "pole",  "shape": "cylinder", "position": [0.0, 1.10, 0.0], "scale": [0.1, 2.00, 0.1]}},
    {{"name": "shade", "shape": "cone",     "position": [0.0, 2.30, 0.0], "scale": [0.7, 0.40, 0.7]}}
  ]
}}
base:  y in [0.00, 0.20]
pole:  y in [0.10, 2.10]  — base top = 0.20, pole bottom = 0.10: overlap! FIX: pole_y = 0.10 + 1.00 = 1.10 → y in [0.10, 2.10]. Still wrong. Correct: base_top=0.20, pole_sy=2.0, pole_y = 0.20 + 1.00 = 1.20 → y in [0.20, 2.20]. shade_y = 2.20 + 0.20 = 2.40 → y in [2.20, 2.60]. Use these corrected values.
""".format(object_name=object_name, primitive_type=primitive_type)


def parse_composite_spec_with_llm(object_name, primitive_type, model_name=None):
    """Call the LLM with a focused object-design prompt.

    Returns a validated list of part dicts (name, shape, position, scale).
    Raises ValueError if the response is unusable.
    """
    full_prompt = build_composite_spec_prompt(object_name, primitive_type)
    raw_text, _, _ = _call_llm(model_name or DEFAULT_MODEL, full_prompt)

    if not raw_text:
        raise ValueError("LLM returned empty response for composite spec")

    json_text = extract_json_object(raw_text)
    data = json.loads(json_text)

    if not isinstance(data, dict) or "parts" not in data:
        raise ValueError("LLM composite spec missing 'parts' key")

    parts = data["parts"]
    if not isinstance(parts, list) or len(parts) == 0:
        raise ValueError("LLM composite spec 'parts' must be a non-empty list")

    return parts


def parse_prompt_to_action_with_llm(prompt, scene_ir, model_name=None):
    """Parse a user prompt into a structured action dict using the LLM.

    Attaches _tokens_in / _tokens_out to the returned action dict so the
    evaluation runner can compute cost metrics.
    """
    scene_context = build_scene_context(scene_ir)
    full_prompt = build_prompt(prompt, scene_context)

    raw_text, tokens_in, tokens_out = _call_llm(model_name or DEFAULT_MODEL, full_prompt)

    if not raw_text:
        raise ValueError("LLM returned empty text")

    json_text = extract_json_object(raw_text)
    action = json.loads(json_text)
    action = normalize_parsed_action(action)
    action["_tokens_in"]  = tokens_in
    action["_tokens_out"] = tokens_out

    return action
