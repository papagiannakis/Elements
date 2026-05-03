import json
import os
import re

from openai import OpenAI

API_KEY_ENV = "OPENAI_API_KEY"
DEFAULT_MODEL = "gpt-5.5"


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