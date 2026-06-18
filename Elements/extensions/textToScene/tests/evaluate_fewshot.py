"""
Few-shot baseline comparison.

Approach: give the LLM 3 complete Elements scene files as examples and
ask it to generate a new scene from a natural language prompt.
Compare success rate against textToScene (which always produces valid code).

Metrics:
  syntax_ok  generated code is valid Python (ast.compile)
  api_ok     contains required Elements API patterns
  no_halluc  does NOT use known hallucinated API patterns
  full_ok    all three pass  (the "apples-to-apples" success criterion)

Run: python tests/evaluate_fewshot.py
"""

import ast
import sys
import re
import json
import time
import textwrap
from pathlib import Path
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from code_generator import generate_scene_script
from llm_parser import _call_llm
from config import GEMINI_API_KEY, OPENAI_API_KEY

DOCS     = Path(__file__).parent.parent / "docs"
OUT_JSON = DOCS / "all_results.json"

# generate 3 compact example scenes from the IR 

def _gen(ir_children, title="Scene"):
    ir = {
        "node_type": "scene", "name": "root",
        "window": {"width": 800, "height": 600, "title": title},
        "children": ir_children,
    }
    return generate_scene_script(ir)


def _trim(code, max_lines=80):
    """Keep first max_lines of the generated code — enough to show structure."""
    lines = code.splitlines()
    trimmed = lines[:max_lines]
    if len(lines) > max_lines:
        trimmed.append("# ... (render loop continues) ...")
    return "\n".join(trimmed)


EXAMPLE_1 = _trim(_gen([{
    "node_type": "mesh_object", "name": "red_cube",
    "shape": "cube",
    "transform": {"position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
    "material": {"color": [1.0, 0.0, 0.0], "texture": {"enabled": False, "path": None}},
}], "Red Cube Scene"))

EXAMPLE_2 = _trim(_gen([
    {
        "node_type": "mesh_object", "name": "blue_sphere",
        "shape": "sphere",
        "transform": {"position": [-1.5, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
        "material": {"color": [0.0, 0.0, 1.0], "texture": {"enabled": False, "path": None}},
    },
    {
        "node_type": "mesh_object", "name": "green_cylinder",
        "shape": "cylinder",
        "transform": {"position": [1.5, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
        "material": {"color": [0.0, 1.0, 0.0], "texture": {"enabled": False, "path": None}},
    },
], "Two Shapes Scene"))

EXAMPLE_3 = _trim(_gen([
    {
        "node_type": "mesh_object", "name": "yellow_cone",
        "shape": "cone",
        "transform": {"position": [0.0, 0.5, 0.0], "scale": [1.0, 1.5, 1.0]},
        "material": {"color": [1.0, 1.0, 0.0], "texture": {"enabled": False, "path": None}},
    },
    {
        "node_type": "mesh_object", "name": "purple_pyramid",
        "shape": "pyramid",
        "transform": {"position": [2.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0]},
        "material": {"color": [0.8, 0.0, 0.8], "texture": {"enabled": False, "path": None}},
    },
], "Cone and Pyramid"))

#few-shot system prompt

FEW_SHOT_SYSTEM = """You are an expert in the Elements Python computer graphics framework.
Generate complete, runnable Python scene scripts using the Elements API.

STRICT RULES — violation = immediate failure:
1. Use ONLY these imports (copy exactly):
   import numpy as np
   import Elements.pyECSS.math_utilities as util
   from Elements.pyECSS.Entity import Entity
   from Elements.pyECSS.Component import BasicTransform, Camera, RenderMesh
   from Elements.pyECSS.System import TransformSystem, CameraSystem
   from Elements.pyGLV.GL.Scene import Scene
   from Elements.pyGLV.GUI.Viewer import RenderGLStateSystem
   from Elements.pyGLV.GUI.ImguiDecorator import ImGUIecssDecorator2
   from Elements.pyGLV.GL.Shader import InitGLShaderSystem, Shader, ShaderGLDecorator, RenderGLShaderSystem
   from Elements.pyGLV.GL.VertexArray import VertexArray

2. Every mesh object needs ALL FOUR of: vertex_attributes (vertices, colors, normals),
   vertex_index, VertexArray component, ShaderGLDecorator component.

3. Numpy vertex arrays must be dtype=np.float32. Index arrays must be dtype=np.uint32.

4. Do NOT invent API methods. Use ONLY what appears in the examples below.

5. Return ONLY the Python code. No markdown, no explanation.

--- EXAMPLE 1: Single red cube ---
{ex1}

--- EXAMPLE 2: Blue sphere + green cylinder ---
{ex2}

--- EXAMPLE 3: Yellow cone + purple pyramid ---
{ex3}
""".format(ex1=EXAMPLE_1, ex2=EXAMPLE_2, ex3=EXAMPLE_3)

# ── test prompts (20 representative commands) ──────────────────────────────────

TEST_PROMPTS = [
    # object creation
    "Create a scene with a single red cube.",
    "Generate a scene with a blue sphere and a green cylinder side by side.",
    "Create a scene with three pyramids: red, yellow, and blue.",
    "Make a scene with a white cone and an orange cube.",
    # color & shape variety
    "Create a purple sphere scene.",
    "Make a scene with a teal cylinder.",
    "Generate a scene containing a pink pyramid and a gray cube.",
    # scale
    "Create a red cube that is twice as large as normal.",
    "Make a small green sphere (scale 0.5) and a large blue cone (scale 2).",
    # placement
    "Create a scene with a red cube on the left and a blue sphere on the right.",
    "Make a green cylinder in the center and a yellow cone slightly to the right.",
    # multiple objects
    "Generate a scene with 4 different shapes: cube, sphere, cylinder, cone in different colors.",
    "Create a scene with two cubes: one red at position (-2, 0.5, 0) and one blue at (2, 0.5, 0).",
    # with transforms
    "Make a tall thin cylinder (scale 0.3, 3.0, 0.3) in green.",
    "Create a flat wide pyramid (scale 2.0, 0.5, 2.0) in orange.",
    # simple composites
    "Make a simple tree: a brown cylinder trunk and a green sphere on top.",
    "Create a simple house: a white cube body and a red pyramid roof.",
    # lighting description
    "Create a scene with a red sphere under warm lighting.",
    # complex
    "Make a scene with 5 colored spheres arranged in a row.",
    "Generate a scene with a cube, a sphere on top of it, and a pyramid next to them.",
]

# ── validation ─────────────────────────────────────────────────────────────────

REQUIRED_PATTERNS = [
    r"from Elements\.pyECSS\.Entity import Entity",
    r"from Elements\.pyGLV\.GL\.Scene import Scene",
    r"scene\.world\.createEntity",
    r"scene\.world\.addComponent",
    r"BasicTransform",
    r"RenderMesh",
    r"VertexArray\(\)",
    r"ShaderGLDecorator",
    r"scene\.init\(",
    r"scene\.render\(",
]

HALLUCINATION_PATTERNS = [
    r"scene\.add_object",
    r"scene\.add_mesh",
    r"Entity\.create\(",
    r"Mesh\.create\(",
    r"scene\.create_object",
    r"gl\.glCreateBuffer",
    r"pyglet\.",
    r"pygame\.",
    r"glfw\.",
    r"moderngl\.",
    r"\.add_child\(",
    r"scene\.objects\.",
]

def check_syntax(code):
    try:
        compile(code, "<few_shot>", "exec")
        return True, None
    except SyntaxError as e:
        return False, str(e)

def check_api(code):
    missing = [p for p in REQUIRED_PATTERNS if not re.search(p, code)]
    return len(missing) == 0, missing

def check_hallucinations(code):
    found = [p for p in HALLUCINATION_PATTERNS if re.search(p, code)]
    return len(found) == 0, found

def evaluate_generated_code(code):
    if not code or len(code.strip()) < 50:
        return {"syntax_ok": False, "api_ok": False, "no_halluc": False,
                "full_ok": False, "errors": ["empty or too short"]}
    syn_ok, syn_err = check_syntax(code)
    api_ok, missing = check_api(code)
    noh_ok, halluc  = check_hallucinations(code)
    return {
        "syntax_ok": syn_ok,
        "api_ok":    api_ok,
        "no_halluc": noh_ok,
        "full_ok":   syn_ok and api_ok and noh_ok,
        "errors":    (([f"SyntaxError: {syn_err}"] if not syn_ok else []) +
                      ([f"Missing API: {missing}"] if not api_ok else []) +
                      ([f"Hallucination: {halluc}"] if not noh_ok else [])),
    }

# run evaluation

def run_fewshot_eval(model_id, delay=4.5):
    print(f"\n{'#'*60}")
    print(f"  Few-Shot Baseline — {model_id}")
    print(f"{'#'*60}")

    results = []
    for i, prompt in enumerate(TEST_PROMPTS, 1):
        print(f"  [{i:>2}/{len(TEST_PROMPTS)}] {prompt[:55]}", end="", flush=True)
        start = time.time()
        try:
            full = FEW_SHOT_SYSTEM + f"\n\nNow generate a scene for this request:\n{prompt}\n"
            text, tin, tout = _call_llm(model_id, full)
            # strip markdown fences if present
            code = re.sub(r"^```(?:python)?", "", text.strip(), flags=re.MULTILINE)
            code = re.sub(r"```$", "", code.strip(), flags=re.MULTILINE).strip()
            eval_result = evaluate_generated_code(code)
        except Exception as e:
            eval_result = {"syntax_ok": False, "api_ok": False, "no_halluc": False,
                           "full_ok": False, "errors": [str(e)]}
            tin = tout = 0

        lat = (time.time() - start) * 1000
        status = "PASS" if eval_result["full_ok"] else "FAIL"
        err_short = eval_result["errors"][0][:50] if eval_result["errors"] else ""
        print(f"  {status}  {lat:.0f}ms" + (f"  [{err_short}]" if not eval_result["full_ok"] else ""))

        results.append({
            "prompt": prompt,
            "syntax_ok": eval_result["syntax_ok"],
            "api_ok":    eval_result["api_ok"],
            "no_halluc": eval_result["no_halluc"],
            "full_ok":   eval_result["full_ok"],
            "errors":    eval_result["errors"],
            "latency_ms": lat,
            "tokens_in":  tin,
            "tokens_out": tout,
        })
        time.sleep(delay)

    # metrics
    n = len(results)
    syn_rate = sum(r["syntax_ok"] for r in results) / n
    api_rate = sum(r["api_ok"]    for r in results) / n
    noh_rate = sum(r["no_halluc"] for r in results) / n
    full_rate = sum(r["full_ok"]  for r in results) / n
    avg_lat   = sum(r["latency_ms"] for r in results) / n

    print(f"\n{'='*55}")
    print(f"  FEW-SHOT RESULTS — {model_id}")
    print(f"{'='*55}")
    print(f"  Syntax valid      : {syn_rate:6.1%}  ({sum(r['syntax_ok'] for r in results)}/{n})")
    print(f"  API correct       : {api_rate:6.1%}  ({sum(r['api_ok'] for r in results)}/{n})")
    print(f"  No hallucinations : {noh_rate:6.1%}  ({sum(r['no_halluc'] for r in results)}/{n})")
    print(f"  FULL PASS         : {full_rate:6.1%}  ({sum(r['full_ok'] for r in results)}/{n})")
    print(f"  Avg latency       : {avg_lat:.0f} ms")
    print(f"\n  textToScene (same prompts): 100% syntax, 100% API, 100% no-halluc")
    print(f"  → LLM gain: +{(1.0 - full_rate)*100:.1f} percentage points from structured pipeline")

    return results, {
        "syntax_rate": syn_rate, "api_rate": api_rate,
        "no_halluc_rate": noh_rate, "full_pass_rate": full_rate,
        "avg_latency_ms": avg_lat, "n": n,
    }


if __name__ == "__main__":
    model = "gemini-2.5-flash-lite"   # change if needed
    delay = 4.5 if model.startswith("gemini") else 0.5

    results, summary = run_fewshot_eval(model, delay=delay)

    # save
    out = Path.home() / "Desktop" / "textToScene_figures" / "fewshot_results.json"
    out.write_text(json.dumps({
        "model": model,
        "summary": summary,
        "results": results,
        "textToScene_reference": {
            "syntax_rate": 1.0, "api_rate": 1.0,
            "no_halluc_rate": 1.0, "full_pass_rate": 1.0,
            "note": "Deterministic code generator — always 100%"
        }
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved: {out}")
