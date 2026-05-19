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

import openpyxl
from mock_ai_contoller import apply_action_to_ir, normalize_action
from llm_parser import parse_prompt_to_action_with_llm
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

def load_test_cases(xlsx_path):
    """Load test cases from Excel."""
    wb = openpyxl.load_workbook(xlsx_path)
    
    # Try to find the sheet with test cases (usually first sheet with "Command" header)
    ws = None
    for sheet in wb.worksheets:
        # Check if first row has "Command" column
        first_row = [cell.value for cell in sheet[1]]
        if "Command" in first_row or "command" in [str(v).lower() for v in first_row if v]:
            ws = sheet
            break
    
    if not ws:
        ws = wb.worksheets[1] if len(wb.worksheets) > 1 else wb.active
    
    cases = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0] or not row[1]:
            continue
        # Skip summary rows (Total, formulas, etc)
        if str(row[1]).startswith("=") or str(row[0]).lower() == "total":
            continue
        cases.append({
            "id": row[0],
            "command": str(row[1]),
            "category": str(row[2]) if row[2] else "",
            "expected_action": str(row[3]) if row[3] else "",
            "expected_target": str(row[4]) if row[4] else "",
        })
    return cases

def run_single_test(command, scene_ir, model_name):
    """Run one test with specified model and return metrics."""
    start = time.time()
    
    try:
        action = parse_prompt_to_action_with_llm(command, scene_ir, model_name=model_name)
        parse_success = True
        action = normalize_action(action)
    except Exception as e:
        latency = (time.time() - start) * 1000
        print(f"  ❌ Parse failed: {e}")  # DEBUG
        return {
            "parse_success": False,
            "apply_success": False,
            "latency_ms": latency,
            "error": str(e),
            "action": None,
            "tokens_in": 0,
            "tokens_out": 0,
            "new_ir": new_ir,
        }
    
    print(f"  ✓ Parsed: {action.get('action', 'unknown')}")  # DEBUG
    latency = (time.time() - start) * 1000
    
    # Extract token counts if available
    tokens_in = getattr(action, '_tokens_in', 0)
    tokens_out = getattr(action, '_tokens_out', 0)
    
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
        }
    
    return {
        "parse_success": True,
        "apply_success": True,
        "latency_ms": latency,
        "action": action,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
    }

def compute_metrics(results, expected_cases, model_config):
    """Compute aggregate metrics for a model."""
    total = len(results)
    parse_success = sum(1 for r in results if r["parse_success"])
    apply_success = sum(1 for r in results if r["apply_success"])
    
    # Intent accuracy: action matches expected
    intent_correct = 0
    for r, e in zip(results, expected_cases):
        if r["action"] and r["action"].get("action") == e["expected_action"]:
            intent_correct += 1
    
    # Latency
    latencies = [r["latency_ms"] for r in results if r["parse_success"]]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    
    # Tokens and cost
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
    """Save detailed results to CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Model", "ID", "Command", "Category", "Expected Action",
            "Actual Action", "Parse Success", "Apply Success",
            "Latency (ms)", "Tokens In", "Tokens Out", "Error"
        ])
        
        for model_name, model_config in MODELS.items():
            print(f"=== Running {model_config['name']} ===")
            results = []
            
            # Keep scene state across commands (stateful evaluation)
            current_scene = deepcopy(EMPTY_SCENE)
            
            for i, case in enumerate(cases, 1):
                cmd_preview = str(case['command'])[:50] if case['command'] else "(empty)"
                print(f"[{i}/{len(cases)}] {cmd_preview}")
                result = run_single_test(case["command"], current_scene, model_name)
                results.append((case, result))
                
                # Update scene with result if successful
                if result["apply_success"] and result.get("new_ir"):
                    current_scene = result["new_ir"]
                
                time.sleep(0.5)
    
    all_results[model_name] = results

if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)
    
    xlsx_path = Path(__file__).parent.parent / "docs" / "textToScene_evaluation.xlsx"
    cases = load_test_cases(xlsx_path)
    
    print(f"Loaded {len(cases)} test cases")
    print(f"Testing {len(MODELS)} models: {', '.join(MODELS.keys())}\n")
    
    all_results = {}
    
    for model_name, model_config in MODELS.items():
        print(f"=== Running {model_config['name']} ===")
        results = []
        
        for i, case in enumerate(cases, 1):
            cmd_preview = str(case['command'])[:50] if case['command'] else "(empty)"
            print(f"[{i}/{len(cases)}] {cmd_preview}")            
            result = run_single_test(case["command"], deepcopy(EMPTY_SCENE), model_name)
            results.append((case, result))
            time.sleep(0.5)  # Rate limiting
        
        all_results[model_name] = results
        metrics = compute_metrics([r for _, r in results], cases, model_config)
        
        print(f"\n{model_config['name']} Results:")
        print(f"  Intent Accuracy:  {metrics['intent_accuracy']:.1%}")
        print(f"  Parse Success:    {metrics['parse_success_rate']:.1%}")
        print(f"  Apply Success:    {metrics['apply_success_rate']:.1%}")
        print(f"  Avg Latency:      {metrics['avg_latency_ms']:.0f}ms")
        print(f"  Cost/100 cmds:    ${metrics['cost_per_100_commands']:.3f}")
        print()
    
    # Save detailed CSV
    output_csv = Path("evaluation_results.csv")
    save_results_csv(all_results, output_csv)
    print(f"Saved detailed results to {output_csv.absolute()}")

# python tests/evaluation_runner.py