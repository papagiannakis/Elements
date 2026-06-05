"""
Multi-model evaluation runner for textToScene.
Compares GPT-4o, GPT-4o-mini, and Gemini 2.0 Flash.
Measures: intent accuracy, parse/apply success, latency, tokens, cost.

Usage:
    python evaluation_runner.py                    # all models
    python evaluation_runner.py --models gpt-4o-mini gemini-2.0-flash
    python evaluation_runner.py --independent      # fresh scene per command
"""

import sys
import time
import json
import csv
import argparse
import warnings
from pathlib import Path
from copy import deepcopy

# Suppress FutureWarnings from google-auth on Python 3.9 EOL
warnings.filterwarnings("ignore", category=FutureWarning, module="google")

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mock_ai_contoller import apply_action_to_ir, normalize_action, resolve_composite_overlaps
from llm_parser import parse_prompt_to_action_with_llm, parse_composite_spec_with_llm
from config import OPENAI_API_KEY, GEMINI_API_KEY

# ---------------------------------------------------------------------------
# Model registry  (name, input $/1M tokens, output $/1M tokens)
# ---------------------------------------------------------------------------
ALL_MODELS = {
    "gpt-4o-mini":           {"name": "GPT-4o-mini",            "input_cost": 0.15,  "output_cost":  0.60},
    "gpt-4.1-mini":          {"name": "GPT-4.1-mini",           "input_cost": 0.40,  "output_cost":  1.60},
    "gpt-4o":                {"name": "GPT-4o",                 "input_cost": 2.50,  "output_cost": 10.00},
    "gemini-2.0-flash-lite": {"name": "Gemini-2.0-Flash-Lite",  "input_cost": 0.075, "output_cost":  0.30},
    "gemini-2.0-flash":      {"name": "Gemini-2.0-Flash",       "input_cost": 0.10,  "output_cost":  0.40},
    "gemini-2.5-flash":      {"name": "Gemini-2.5-Flash",       "input_cost": 0.15,  "output_cost":  0.60},
    "gemini-2.5-flash-lite": {"name": "Gemini-2.5-Flash-Lite",  "input_cost": 0.10,  "output_cost":  0.40},
}

DEFAULT_EVAL_MODELS = ["gemini-2.5-flash-lite"]

# ---------------------------------------------------------------------------
# Section → expected action mapping
# ---------------------------------------------------------------------------
_SECTION_ACTION_MAP = {
    "object creation":        "add_object",
    "movement - directional": "move_object",
    "movement - positional":  "move_object",
    "recolor":                "recolor_object",
    "scale - natural":        "scale_object",
    "scale - explicit":       "scale_object",
    "rotation - simple":      "rotate_object",
    "rotation - axis":        "rotate_object",
    "deletion":               "delete_object",
    "prefabs - add":          "add_prefab",
    "prefabs - transform":    None,
    "composite objects":      "generate_composite",
    "scene management":       None,
    "undo/redo":              None,
    "action sequences":       "action_sequence",
    "lighting":               None,
    "texture":                None,
}

_KNOWN_COMPOSITES = {"tree", "table", "lamp"}

# Empty baseline scene
EMPTY_SCENE = {
    "node_type": "scene",
    "name": "root",
    "window": {"width": 800, "height": 600, "title": "Eval"},
    "children": [],
}


def _expected_action_for_section(header_text):
    h = header_text.lower()
    for key, action in _SECTION_ACTION_MAP.items():
        if key in h:
            return action
    return None


# ---------------------------------------------------------------------------
# Test case loading
# ---------------------------------------------------------------------------
def load_test_cases_from_txt(txt_path):
    cases = []
    current_category = "unknown"
    current_expected_action = None
    cmd_id = 0

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                section_title = line.lstrip("#").strip().split("(")[0].strip()
                current_category = section_title
                current_expected_action = _expected_action_for_section(section_title)
                continue
            cmd_id += 1
            cases.append({
                "id": cmd_id,
                "command": line,
                "category": current_category,
                "expected_action": current_expected_action,
            })
    return cases


# ---------------------------------------------------------------------------
# Single test execution
# ---------------------------------------------------------------------------
def run_single_test(command, scene_ir, model_name):
    start = time.time()

    try:
        action = parse_prompt_to_action_with_llm(command, scene_ir, model_name=model_name)
        action = normalize_action(action)

        if (action.get("action") == "generate_composite"
                and action.get("parts") is None
                and action.get("composite") not in _KNOWN_COMPOSITES):
            object_name   = action.get("object_name") or action.get("composite") or "object"
            primitive_type = action.get("object_type") or action.get("primitive_type") or "cube"
            parts = parse_composite_spec_with_llm(object_name, primitive_type, model_name=model_name)
            parts = resolve_composite_overlaps(parts)
            action = dict(action)
            action.update({"composite": "open", "parts": parts,
                           "object_name": object_name, "primitive_type": primitive_type})

    except Exception as e:
        latency = (time.time() - start) * 1000
        return {
            "parse_success": False, "apply_success": False,
            "latency_ms": latency, "error": str(e),
            "action": None, "tokens_in": 0, "tokens_out": 0,
            "new_ir": scene_ir,
        }

    latency    = (time.time() - start) * 1000
    tokens_in  = action.pop("_tokens_in",  0)
    tokens_out = action.pop("_tokens_out", 0)

    try:
        new_ir = apply_action_to_ir(deepcopy(scene_ir), action)
        return {
            "parse_success": True, "apply_success": True,
            "latency_ms": latency, "action": action,
            "tokens_in": tokens_in, "tokens_out": tokens_out,
            "new_ir": new_ir,
        }
    except Exception as e:
        return {
            "parse_success": True, "apply_success": False,
            "latency_ms": latency, "action": action,
            "tokens_in": tokens_in, "tokens_out": tokens_out,
            "error": str(e), "new_ir": scene_ir,
        }


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------
def action_type_matches(result, case):
    expected = case.get("expected_action")
    if expected is None:
        return True
    if not result.get("parse_success") or result.get("action") is None:
        return False
    return result["action"].get("action") == expected


def compute_metrics(results_with_cases, model_config):
    total = len(results_with_cases)
    if total == 0:
        return {}

    parse_ok  = sum(1 for _, r in results_with_cases if r["parse_success"])
    apply_ok  = sum(1 for _, r in results_with_cases if r["apply_success"])
    intent_ok = sum(
        1 for case, r in results_with_cases
        if r["parse_success"] and r["apply_success"] and action_type_matches(r, case)
    )

    latencies = [r["latency_ms"] for _, r in results_with_cases if r["parse_success"]]
    avg_lat   = sum(latencies) / len(latencies) if latencies else 0

    tok_in  = sum(r["tokens_in"]  for _, r in results_with_cases)
    tok_out = sum(r["tokens_out"] for _, r in results_with_cases)

    cost_per_100 = (
        (tok_in  / 1_000_000 * model_config["input_cost"]) +
        (tok_out / 1_000_000 * model_config["output_cost"])
    ) * (100 / total) if total > 0 else 0

    return {
        "total":                  total,
        "parse_success_rate":     parse_ok  / total,
        "apply_success_rate":     apply_ok  / total,
        "intent_accuracy":        intent_ok / total,
        "avg_latency_ms":         avg_lat,
        "total_tokens_in":        tok_in,
        "total_tokens_out":       tok_out,
        "cost_per_100_commands":  cost_per_100,
    }


def compute_per_category_metrics(results_with_cases):
    """Return {category: {intent_ok, total}} for each section."""
    by_cat = {}
    for case, result in results_with_cases:
        cat = case.get("category", "unknown")
        if cat not in by_cat:
            by_cat[cat] = {"intent_ok": 0, "total": 0}
        by_cat[cat]["total"] += 1
        if (result["parse_success"] and result["apply_success"]
                and action_type_matches(result, case)):
            by_cat[cat]["intent_ok"] += 1
    return by_cat


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
def _bar(ratio, width=20):
    filled = int(ratio * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def print_model_summary(model_name, model_config, metrics):
    n = model_config["name"]
    print(f"\n{'='*55}")
    print(f"  {n}  ({model_name})")
    print(f"{'='*55}")
    print(f"  Intent Accuracy : {metrics['intent_accuracy']:6.1%}  {_bar(metrics['intent_accuracy'])}")
    print(f"  Parse Success   : {metrics['parse_success_rate']:6.1%}  {_bar(metrics['parse_success_rate'])}")
    print(f"  Apply Success   : {metrics['apply_success_rate']:6.1%}  {_bar(metrics['apply_success_rate'])}")
    print(f"  Avg Latency     : {metrics['avg_latency_ms']:6.0f} ms")
    print(f"  Tokens In/Out   : {metrics['total_tokens_in']:,} / {metrics['total_tokens_out']:,}")
    print(f"  Cost/100 cmds   : ${metrics['cost_per_100_commands']:.4f}")


def print_per_category(cat_metrics, model_name):
    print(f"\n  Category breakdown  ({model_name})")
    print(f"  {'Category':<32} {'Correct':>7} {'Total':>6} {'Acc':>6}")
    print(f"  {'-'*55}")
    for cat, m in cat_metrics.items():
        acc = m["intent_ok"] / m["total"] if m["total"] > 0 else 0
        print(f"  {cat:<32} {m['intent_ok']:>7} {m['total']:>6} {acc:>6.0%}")


def print_comparison_table(all_metrics, model_cfgs):
    models = list(all_metrics.keys())
    names  = [model_cfgs[m]["name"] for m in models]
    col    = 14

    print(f"\n{'='*70}")
    print("  MODEL COMPARISON SUMMARY")
    print(f"{'='*70}")
    header = f"  {'Metric':<28}" + "".join(f"{n:>{col}}" for n in names)
    print(header)
    print(f"  {'-'*68}")

    rows = [
        ("Intent Accuracy",       "intent_accuracy",       "{:.1%}"),
        ("Parse Success",         "parse_success_rate",    "{:.1%}"),
        ("Apply Success",         "apply_success_rate",    "{:.1%}"),
        ("Avg Latency (ms)",      "avg_latency_ms",        "{:.0f}"),
        ("Cost / 100 commands",   "cost_per_100_commands", "${:.4f}"),
        ("Total Tokens In",       "total_tokens_in",       "{:,}"),
        ("Total Tokens Out",      "total_tokens_out",      "{:,}"),
    ]

    for label, key, fmt in rows:
        vals = [fmt.format(all_metrics[m].get(key, 0)) for m in models]
        row  = f"  {label:<28}" + "".join(f"{v:>{col}}" for v in vals)
        print(row)

    print(f"{'='*70}")


# ---------------------------------------------------------------------------
# CSV / JSON export
# ---------------------------------------------------------------------------
def save_results_csv(all_results, output_path):
    import os, tempfile
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp = tempfile.mkstemp(suffix=".tmp", prefix="eval_")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Model", "ID", "Category", "Command",
                "Expected Action", "Actual Action", "Action Match",
                "Parse OK", "Apply OK", "Intent OK",
                "Latency (ms)", "Tokens In", "Tokens Out", "Error",
            ])
            for model_name, results in all_results.items():
                for case, result in results:
                    expected = case.get("expected_action") or ""
                    actual   = (result["action"].get("action") if result["action"] else "") or ""
                    match    = action_type_matches(result, case)
                    intent   = result["parse_success"] and result["apply_success"] and match
                    writer.writerow([
                        model_name, case["id"], case.get("category", ""),
                        case["command"], expected, actual, match,
                        result["parse_success"], result["apply_success"], intent,
                        f"{result['latency_ms']:.0f}",
                        result["tokens_in"], result["tokens_out"],
                        result.get("error", ""),
                    ])
    except Exception:
        try: os.unlink(tmp)
        except Exception: pass
        raise

    os.replace(tmp, str(output_path))
    print(f"CSV  -> {output_path}")


def save_results_json(all_results, all_metrics, per_cat, model_cfgs, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    export = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "models": {},
    }
    for model_name, results in all_results.items():
        cfg = model_cfgs[model_name]
        export["models"][model_name] = {
            "name":             cfg["name"],
            "metrics":          all_metrics.get(model_name, {}),
            "per_category":     per_cat.get(model_name, {}),
            "commands": [
                {
                    "id":              case["id"],
                    "category":        case.get("category", ""),
                    "command":         case["command"],
                    "expected_action": case.get("expected_action"),
                    "actual_action":   (r["action"].get("action") if r["action"] else None),
                    "intent_ok":       r["parse_success"] and r["apply_success"] and action_type_matches(r, case),
                    "parse_ok":        r["parse_success"],
                    "apply_ok":        r["apply_success"],
                    "latency_ms":      round(r["latency_ms"], 1),
                    "tokens_in":       r["tokens_in"],
                    "tokens_out":      r["tokens_out"],
                    "error":           r.get("error"),
                }
                for case, r in results
            ],
        }

    tmp = output_path.with_suffix(".tmp")
    with open(str(tmp), "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2, ensure_ascii=False)
    tmp.replace(output_path)
    print(f"JSON -> {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="textToScene evaluation runner")
    parser.add_argument(
        "--models", nargs="+",
        choices=list(ALL_MODELS.keys()),
        default=None,
        help="Models to evaluate (default: all that have an API key)",
    )
    parser.add_argument(
        "--independent", action="store_true",
        help="Reset scene to empty before each command (default: cumulative)",
    )
    parser.add_argument(
        "--txt", type=str, default=None,
        help="Path to evaluation_commands.txt (default: docs/evaluation_commands.txt)",
    )
    return parser.parse_args()


def _available_models(requested):
    """Filter to models that have the necessary API key."""
    available = {}
    for key in (requested or DEFAULT_EVAL_MODELS):
        cfg = ALL_MODELS[key]
        if key.startswith("gemini") and not GEMINI_API_KEY:
            print(f"  [skip] {cfg['name']}: GEMINI_API_KEY not set")
            continue
        if not key.startswith("gemini") and not OPENAI_API_KEY:
            print(f"  [skip] {cfg['name']}: OPENAI_API_KEY not set")
            continue
        available[key] = cfg
    return available


if __name__ == "__main__":
    args = parse_args()

    txt_path = Path(args.txt) if args.txt else (
        Path(__file__).parent.parent / "docs" / "evaluation_commands.txt"
    )
    if not txt_path.exists():
        print(f"Error: test file not found: {txt_path}")
        sys.exit(1)

    cases = load_test_cases_from_txt(txt_path)
    print(f"Loaded {len(cases)} test commands from {txt_path.name}")

    models = _available_models(args.models)
    if not models:
        print("No models available. Set OPENAI_API_KEY and/or GEMINI_API_KEY.")
        sys.exit(1)

    print(f"Models: {', '.join(c['name'] for c in models.values())}")
    print(f"Mode  : {'independent (fresh scene per command)' if args.independent else 'cumulative'}\n")

    all_results  = {}
    all_metrics  = {}
    all_per_cat  = {}

    for model_id, model_cfg in models.items():
        print(f"\n{'#'*55}")
        print(f"  Running: {model_cfg['name']}  ({model_id})")
        print(f"{'#'*55}")

        results      = []
        scene_state  = deepcopy(EMPTY_SCENE)

        for i, case in enumerate(cases, 1):
            if args.independent:
                scene_state = deepcopy(EMPTY_SCENE)

            cmd_short = case["command"][:55]
            print(f"  [{i:>3}/{len(cases)}] {cmd_short}", end="", flush=True)

            result = run_single_test(case["command"], scene_state, model_id)
            results.append((case, result))

            ok = result["parse_success"] and result["apply_success"]
            status = "OK  " if ok else "FAIL"
            err = f"  [{result.get('error', '')[:60]}]" if not ok else ""
            print(f"  {status}  {result['latency_ms']:.0f}ms{err}")

            if result["apply_success"] and result.get("new_ir"):
                scene_state = result["new_ir"]

            # Free tier: Gemini ~15 req/min (4s gap), OpenAI is generous
            delay = 4.5 if model_id.startswith("gemini") else 0.4
            time.sleep(delay)

        all_results[model_id] = results
        metrics  = compute_metrics(results, model_cfg)
        cat_met  = compute_per_category_metrics(results)

        all_metrics[model_id] = metrics
        all_per_cat[model_id] = cat_met

        print_model_summary(model_id, model_cfg, metrics)
        print_per_category(cat_met, model_cfg["name"])

    # Overall comparison
    if len(all_results) > 1:
        print_comparison_table(all_metrics, ALL_MODELS)

    # Save outputs — timestamped so multiple runs never overwrite each other
    ts = time.strftime("%Y%m%d_%H%M%S")
    model_tag = "_".join(m.replace("-", "").replace(".", "") for m in all_results)
    stem = f"eval_{ts}_{model_tag}"

    # Try docs/eval_runs/ first, fall back to Desktop
    for candidate_dir in [
        Path(__file__).resolve().parent.parent / "docs" / "eval_runs",
        Path.home() / "Desktop" / "textToScene_eval",
    ]:
        try:
            candidate_dir.mkdir(parents=True, exist_ok=True)
            save_results_csv(all_results, candidate_dir / f"{stem}.csv")
            save_results_json(all_results, all_metrics, all_per_cat, ALL_MODELS, candidate_dir / f"{stem}.json")
            print(f"\nSaved to: {candidate_dir / stem}")
            break
        except Exception as save_err:
            print(f"[save] Could not write to {candidate_dir}: {save_err}")
    else:
        print("[save] WARNING: could not save results to disk — copy the table above manually.")
