"""
Multi-model evaluation runner for textToScene.
Compares GPT-4o, GPT-4o-mini, and optionally Claude 3.5 Sonnet.
Measures: intent accuracy, latency, tokens, cost per command.
"""

import sys
import time
import json
import csv
from pathlib import Path
from copy import deepcopy
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mock_ai_contoller import apply_action_to_ir, normalize_action, resolve_composite_overlaps
from llm_parser import parse_prompt_to_action_with_llm, parse_composite_spec_with_llm
from config import OPENAI_API_KEY

# Empty test scene
EMPTY_SCENE = {
    "node_type": "scene",
    "name": "root",
    "window": {"width": 800, "height": 600, "title": "Eval"},
    "children": [],
}

# Model configurations
MODELS = {
    "gpt-4o": {"name": "GPT-4o", "input_cost": 2.50, "output_cost": 10.0},
    "gpt-4o-mini": {"name": "GPT-4o-mini", "input_cost": 0.15, "output_cost": 0.60},
}

# Maps section header keywords (lowercase) to expected action type.
# None means "mixed" — action type check is skipped for those commands.
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
}

def _expected_action_for_section(header_text):
    """Return expected action string for a section header, or None for mixed."""
    h = header_text.lower()
    for key, action in _SECTION_ACTION_MAP.items():
        if key in h:
            return action
    return None


def load_test_cases_from_txt(txt_path):
    """Load test commands from text file, one per line.

    Section headers (lines starting with #) determine the expected_action for
    all commands that follow, enabling per-command intent verification.
    """
    cases = []
    current_category = "unknown"
    current_expected_action = None
    cmd_id = 0

    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                # Strip leading # and whitespace to get the section title
                section_title = line.lstrip('#').strip()
                # Remove parenthetical counts like "(10 commands)"
                section_title = section_title.split('(')[0].strip()
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

def run_single_test(command, scene_ir, model_name):
    """Run one test with specified model and return metrics."""
    start = time.time()
    
    try:
        action = parse_prompt_to_action_with_llm(command, scene_ir, model_name=model_name)
        parse_success = True
        action = normalize_action(action)

        # Resolve open/unknown composites that need a second LLM design pass
        _KNOWN_COMPOSITES = {"tree", "table", "lamp"}
        if (action.get("action") == "generate_composite"
                and action.get("parts") is None
                and action.get("composite") not in _KNOWN_COMPOSITES):
            object_name = action.get("object_name") or action.get("composite") or "object"
            primitive_type = action.get("object_type") or action.get("primitive_type") or "cube"
            parts = parse_composite_spec_with_llm(object_name, primitive_type, model_name=model_name)
            parts = resolve_composite_overlaps(parts)
            action = dict(action)
            action["composite"] = "open"
            action["parts"] = parts
            action["object_name"] = object_name
            action["primitive_type"] = primitive_type
    except Exception as e:
        latency = (time.time() - start) * 1000
        return {
            "parse_success": False,
            "apply_success": False,
            "latency_ms": latency,
            "error": str(e),
            "action": None,
            "tokens_in": 0,
            "tokens_out": 0,
            "new_ir": scene_ir,
        }
    
    latency = (time.time() - start) * 1000
    tokens_in = action.get('_tokens_in', 0)
    tokens_out = action.get('_tokens_out', 0)
    
    try:
        new_ir = apply_action_to_ir(deepcopy(scene_ir), action)
        apply_success = True
    except Exception as e:
        return {
            "parse_success": True,
            "apply_success": False,
            "latency_ms": latency,
            "action": action,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "error": str(e),
            "new_ir": scene_ir,
        }
    
    return {
        "parse_success": True,
        "apply_success": True,
        "latency_ms": latency,
        "action": action,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "new_ir": new_ir,
    }

def action_type_matches(result, case):
    """Return True if the parsed action type matches the expected action for this case.

    Cases with expected_action=None are 'mixed' sections — always pass this check.
    """
    expected = case.get("expected_action")
    if expected is None:
        return True  # mixed section, skip action-type check
    if not result.get("parse_success") or result.get("action") is None:
        return False
    return result["action"].get("action") == expected


def compute_metrics(results_with_cases, model_config):
    """Compute aggregate metrics for a model.

    results_with_cases: list of (case, result) tuples.
    """
    total = len(results_with_cases)
    parse_success = sum(1 for _, r in results_with_cases if r["parse_success"])
    apply_success = sum(1 for _, r in results_with_cases if r["apply_success"])

    # Intent = parsed correct action type AND apply succeeded
    intent_correct = sum(
        1 for case, r in results_with_cases
        if r["parse_success"] and r["apply_success"] and action_type_matches(r, case)
    )

    latencies = [r["latency_ms"] for _, r in results_with_cases if r["parse_success"]]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    total_tokens_in  = sum(r["tokens_in"]  for _, r in results_with_cases)
    total_tokens_out = sum(r["tokens_out"] for _, r in results_with_cases)

    cost_per_100 = (
        (total_tokens_in / 1_000_000 * model_config["input_cost"]) +
        (total_tokens_out / 1_000_000 * model_config["output_cost"])
    ) * (100 / total) if total > 0 else 0

    return {
        "total": total,
        "parse_success_rate": parse_success / total if total > 0 else 0,
        "apply_success_rate": apply_success / total if total > 0 else 0,
        "intent_accuracy": intent_correct / total if total > 0 else 0,
        "avg_latency_ms": avg_latency,
        "total_tokens_in": total_tokens_in,
        "total_tokens_out": total_tokens_out,
        "cost_per_100_commands": cost_per_100,
    }

def save_results_csv(all_results, output_path):
    """Save detailed results to CSV.

    Writes to a temp file in the system temp directory first, then moves it
    atomically to the final location. This avoids Windows file-lock issues and
    never fails because of missing intermediate directories.
    """
    import os, tempfile
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_fd, tmp_path_str = tempfile.mkstemp(suffix='.tmp', prefix='eval_results_')
    try:
        with os.fdopen(tmp_fd, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Model", "ID", "Category", "Command",
                "Expected Action", "Actual Action", "Action Match",
                "Parse Success", "Apply Success", "Intent Correct",
                "Latency (ms)", "Tokens In", "Tokens Out", "Error"
            ])
            for model_name, results in all_results.items():
                for case, result in results:
                    expected = case.get("expected_action") or ""
                    actual   = result["action"].get("action") if result["action"] else ""
                    match    = action_type_matches(result, case)
                    intent   = result["parse_success"] and result["apply_success"] and match
                    writer.writerow([
                        model_name,
                        case["id"],
                        case.get("category", ""),
                        case["command"],
                        expected,
                        actual,
                        match,
                        result["parse_success"],
                        result["apply_success"],
                        intent,
                        f"{result['latency_ms']:.0f}",
                        result["tokens_in"],
                        result["tokens_out"],
                        result.get("error", ""),
                    ])
    except Exception:
        try:
            os.unlink(tmp_path_str)
        except Exception:
            pass
        raise
    os.replace(tmp_path_str, str(output_path))

if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)
    
    txt_path = Path(__file__).parent.parent / "docs" / "evaluation_commands.txt"
    cases = load_test_cases_from_txt(txt_path)
    print(f"Loaded {len(cases)} commands\n")
    
    all_results = {}
    
    for model_name, model_config in MODELS.items():
        print(f"=== Running {model_config['name']} ===")
        results = []
        current_scene = deepcopy(EMPTY_SCENE)
        
        for i, case in enumerate(cases, 1):
            print(f"[{i}/{len(cases)}] {case['command'][:50]}")
            result = run_single_test(case["command"], current_scene, model_name)
            results.append((case, result))
            
            if result["apply_success"] and result.get("new_ir"):
                current_scene = result["new_ir"]
            
            time.sleep(0.5)
        
        all_results[model_name] = results
        metrics = compute_metrics(results, model_config)
        
        print(f"\n{model_config['name']} Results:")
        print(f"  Success Rate:     {metrics['intent_accuracy']:.1%}")
        print(f"  Parse Success:    {metrics['parse_success_rate']:.1%}")
        print(f"  Apply Success:    {metrics['apply_success_rate']:.1%}")
        print(f"  Avg Latency:      {metrics['avg_latency_ms']:.0f}ms")
        print(f"  Cost/100 cmds:    ${metrics['cost_per_100_commands']:.3f}\n")
    

    output_csv = Path(__file__).parent.parent / "docs" / "evaluation_results.csv"
    save_results_csv(all_results, output_csv)
    print(f"Saved to {output_csv}")