"""
Evaluates the rule-based parser (no LLM) as a reference/baseline.
Compares against the LLM results already in docs/all_results.json.

Run: python tests/evaluate_baseline.py
"""

import sys
import json
import time
from pathlib import Path
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mock_ai_contoller import (
    parse_command, command_to_action, apply_action_to_ir,
    normalize_action, validate_action, detect_procedural_action
)

DOCS     = Path(__file__).parent.parent / "docs"
TXT_PATH = DOCS / "evaluation_commands.txt"
OUT_JSON = DOCS / "all_results.json"

EMPTY_SCENE = {
    "node_type": "scene", "name": "root",
    "window": {"width": 800, "height": 600, "title": "Eval"},
    "children": [],
}

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
    "animation":              "animate_object",
    "orbit - object":         "add_object",
    "orbit - light":          "add_light",
    "custom model loading":   "add_custom_model",
    "scene management":       None,
    "undo/redo":              None,
    "action sequences":       "action_sequence",
}

def expected_action_for_section(header):
    h = header.lower()
    for key, action in _SECTION_ACTION_MAP.items():
        if key in h:
            return action
    return None

def load_cases(txt_path):
    cases, cat, exp_action, cmd_id = [], "unknown", None, 0
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            if line.startswith("#"):
                title = line.lstrip("#").strip().split("(")[0].strip()
                cat, exp_action = title, expected_action_for_section(title)
                continue
            cmd_id += 1
            cases.append({"id": cmd_id, "command": line,
                          "category": cat, "expected_action": exp_action})
    return cases

def action_matches(result, case):
    expected = case.get("expected_action")
    if expected is None:
        return True
    if not result.get("parse_success") or not result.get("action"):
        return False
    return result["action"].get("action") == expected

def run_rule_based(command, scene_ir):
    start = time.time()
    try:
        # Try procedural/animation/orbit detection first (no LLM required)
        action = detect_procedural_action(command)
        if action is None:
            command_dict = parse_command(command)
            action = command_to_action(command_dict)
        action = normalize_action(action)
        validate_action(action)
    except Exception as e:
        return {"parse_success": False, "apply_success": False,
                "action": None, "latency_ms": (time.time()-start)*1000,
                "error": str(e), "new_ir": scene_ir}

    try:
        new_ir = apply_action_to_ir(deepcopy(scene_ir), action)
        return {"parse_success": True, "apply_success": True,
                "action": action, "latency_ms": (time.time()-start)*1000,
                "new_ir": new_ir}
    except Exception as e:
        return {"parse_success": True, "apply_success": False,
                "action": action, "latency_ms": (time.time()-start)*1000,
                "error": str(e), "new_ir": scene_ir}


if __name__ == "__main__":
    if not TXT_PATH.exists():
        print(f"ERROR: {TXT_PATH} not found"); sys.exit(1)

    cases = load_cases(TXT_PATH)
    print(f"Loaded {len(cases)} commands\n")
    print("Running rule-based parser (no LLM)...")

    results = []
    scene   = deepcopy(EMPTY_SCENE)

    for i, case in enumerate(cases, 1):
        result = run_rule_based(case["command"], scene)
        results.append((case, result))
        ok = result["parse_success"] and result["apply_success"]
        if result["apply_success"] and result.get("new_ir"):
            scene = result["new_ir"]
        status = "OK  " if ok else "FAIL"
        err = f"  [{result.get('error','')[:55]}]" if not ok else ""
        print(f"  [{i:>3}/{len(cases)}] {status}  {case['command'][:50]}{err}")

    # ── metrics ───────────────────────────────────────────────────────────────
    total     = len(results)
    parse_ok  = sum(1 for _, r in results if r["parse_success"])
    apply_ok  = sum(1 for _, r in results if r["apply_success"])
    intent_ok = sum(1 for c, r in results
                    if r["parse_success"] and r["apply_success"] and action_matches(r, c))
    lats      = [r["latency_ms"] for _, r in results if r["parse_success"]]
    avg_lat   = sum(lats)/len(lats) if lats else 0

    # per-category
    per_cat = {}
    for case, result in results:
        cat = case.get("category", "unknown")
        per_cat.setdefault(cat, {"intent_ok": 0, "total": 0})
        per_cat[cat]["total"] += 1
        if result["parse_success"] and result["apply_success"] and action_matches(result, case):
            per_cat[cat]["intent_ok"] += 1

    metrics = {
        "total": total,
        "intent_accuracy":    intent_ok / total,
        "parse_success_rate": parse_ok  / total,
        "apply_success_rate": apply_ok  / total,
        "avg_latency_ms":     avg_lat,
        "total_tokens_in":    0,
        "total_tokens_out":   0,
        "cost_per_100_commands": 0.0,
    }

    # ── print summary ─────────────────────────────────────────────────────────
    print(f"\n{'='*55}")
    print("  RULE-BASED PARSER (Baseline / Reference Point)")
    print(f"{'='*55}")
    print(f"  Intent Accuracy : {metrics['intent_accuracy']:6.1%}")
    print(f"  Parse Success   : {metrics['parse_success_rate']:6.1%}")
    print(f"  Apply Success   : {metrics['apply_success_rate']:6.1%}")
    print(f"  Avg Latency     : {metrics['avg_latency_ms']:6.1f} ms  (no API call)")
    print(f"  Cost            : $0.0000  (no LLM)")
    print()
    print(f"  {'Category':<32} {'OK':>4} {'Total':>6} {'Acc':>6}")
    print(f"  {'-'*52}")
    for cat, m in per_cat.items():
        acc = m["intent_ok"] / m["total"] if m["total"] > 0 else 0
        print(f"  {cat:<32} {m['intent_ok']:>4} {m['total']:>6} {acc:>6.0%}")

    # ── save into all_results.json ────────────────────────────────────────────
    if OUT_JSON.exists():
        data = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    else:
        data = {"generated_at": time.strftime("%Y-%m-%d"), "models": {}}

    data["models"]["rule_based"] = {
        "name":         "Rule-Based (no LLM)",
        "provider":     "Baseline",
        "tier":         "baseline",
        "metrics":      metrics,
        "per_category": per_cat,
    }

    OUT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to: {OUT_JSON}")
    print("Now re-run:  python tests/generate_charts.py")
