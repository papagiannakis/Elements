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

def load_test_cases_from_txt(txt_path):
    """Load test commands from text file, one per line."""
    cases = []
    with open(txt_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            cases.append({
                "id": i,
                "command": line,
                "category": "auto",
                "expected_action": "auto",
                "expected_target": "",
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

def compute_metrics(results, expected_cases, model_config):
    """Compute aggregate metrics for a model."""
    total = len(results)
    parse_success = sum(1 for r in results if r["parse_success"])
    apply_success = sum(1 for r in results if r["apply_success"])
    
    # For auto tests: success = parse AND apply both worked
    intent_correct = sum(1 for r in results if r["parse_success"] and r["apply_success"])
    
    latencies = [r["latency_ms"] for r in results if r["parse_success"]]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    
    total_tokens_in = sum(r["tokens_in"] for r in results)
    total_tokens_out = sum(r["tokens_out"] for r in results)
    
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
    """Save detailed results to CSV using atomic write to avoid file-lock errors."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(".csv.tmp")
    try:
        with open(tmp_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Model", "ID", "Command", "Actual Action", "Parse Success",
                "Apply Success", "Latency (ms)", "Tokens In", "Tokens Out", "Error"
            ])
            for model_name, results in all_results.items():
                for case, result in results:
                    writer.writerow([
                        model_name,
                        case["id"],
                        case["command"],
                        result["action"].get("action") if result["action"] else "",
                        result["parse_success"],
                        result["apply_success"],
                        f"{result['latency_ms']:.0f}",
                        result["tokens_in"],
                        result["tokens_out"],
                        result.get("error", ""),
                    ])
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise
    import os
    os.replace(str(tmp_path), str(output_path))

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
        metrics = compute_metrics([r for _, r in results], cases, model_config)
        
        print(f"\n{model_config['name']} Results:")
        print(f"  Success Rate:     {metrics['intent_accuracy']:.1%}")
        print(f"  Parse Success:    {metrics['parse_success_rate']:.1%}")
        print(f"  Apply Success:    {metrics['apply_success_rate']:.1%}")
        print(f"  Avg Latency:      {metrics['avg_latency_ms']:.0f}ms")
        print(f"  Cost/100 cmds:    ${metrics['cost_per_100_commands']:.3f}\n")
    

    output_csv = Path(__file__).parent.parent / "docs" / "evaluation_results.csv"
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    save_results_csv(all_results, output_csv)
    print(f"Saved to {output_csv}")