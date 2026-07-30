"""
Consolidate multiple evaluation runs into one comparison report.

Usage:
    python consolidate_results.py                  # reads all JSON in docs/eval_runs/
    python consolidate_results.py --out report.csv # custom output name
"""

import json
import csv
import sys
import argparse
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "docs"
RUNS_DIR = DOCS_DIR / "eval_runs"

# Pretty names override (for any model id found in the files)
MODEL_NAMES = {
    "gpt-4o":                "GPT-4o",
    "gpt-4o-mini":           "GPT-4o-mini",
    "gpt-4.1-mini":          "GPT-4.1-mini",
    "gemini-2.0-flash":      "Gemini-2.0-Flash",
    "gemini-2.0-flash-lite": "Gemini-2.0-Flash-Lite",
    "gemini-2.5-flash":      "Gemini-2.5-Flash",
    "gemini-2.5-flash-lite": "Gemini-2.5-Flash-Lite",
}


def load_runs(runs_dir):
    """Load all JSON run files. Returns {model_id: metrics_dict}."""
    combined = {}
    files = sorted(runs_dir.glob("eval_*.json"))
    if not files:
        print(f"No eval_*.json files found in {runs_dir}")
        sys.exit(1)

    print(f"Found {len(files)} run file(s):")
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        print(f"  {f.name}  ({', '.join(data.get('models', {}).keys())})")
        for model_id, model_data in data.get("models", {}).items():
            # Later runs overwrite earlier ones for the same model
            combined[model_id] = model_data

    return combined


def _pct(v):
    return f"{v:.1%}" if isinstance(v, float) else str(v)


def print_comparison(combined):
    models = list(combined.keys())
    names  = [MODEL_NAMES.get(m, m) for m in models]
    col    = 20

    print(f"\n{'='*75}")
    print("  CONSOLIDATED COMPARISON")
    print(f"{'='*75}")
    header = f"  {'Metric':<28}" + "".join(f"{n:>{col}}" for n in names)
    print(header)
    print(f"  {'-'*73}")

    rows = [
        ("Intent Accuracy",      "intent_accuracy",       _pct),
        ("Parse Success",        "parse_success_rate",    _pct),
        ("Apply Success",        "apply_success_rate",    _pct),
        ("Avg Latency (ms)",     "avg_latency_ms",        lambda v: f"{v:.0f}"),
        ("Cost / 100 cmds",      "cost_per_100_commands", lambda v: f"${v:.4f}"),
        ("Total Tokens In",      "total_tokens_in",       lambda v: f"{int(v):,}"),
        ("Total Tokens Out",     "total_tokens_out",      lambda v: f"{int(v):,}"),
        ("Total Commands",       "total",                 lambda v: str(int(v))),
    ]

    for label, key, fmt in rows:
        vals = [fmt(combined[m]["metrics"].get(key, 0)) for m in models]
        print(f"  {label:<28}" + "".join(f"{v:>{col}}" for v in vals))

    print(f"{'='*75}")


def print_per_category(combined):
    # Collect all categories across all models
    all_cats = []
    for model_data in combined.values():
        for cat in model_data.get("per_category", {}).keys():
            if cat not in all_cats:
                all_cats.append(cat)

    models = list(combined.keys())
    names  = [MODEL_NAMES.get(m, m) for m in models]
    col    = 16

    print(f"\n{'='*75}")
    print("  PER-CATEGORY ACCURACY")
    print(f"{'='*75}")
    header = f"  {'Category':<32}" + "".join(f"{n:>{col}}" for n in names)
    print(header)
    print(f"  {'-'*73}")

    for cat in all_cats:
        vals = []
        for m in models:
            cat_data = combined[m].get("per_category", {}).get(cat)
            if cat_data:
                acc = cat_data["intent_ok"] / cat_data["total"] if cat_data["total"] > 0 else 0
                vals.append(f"{acc:.0%} ({cat_data['intent_ok']}/{cat_data['total']})")
            else:
                vals.append("-")
        print(f"  {cat:<32}" + "".join(f"{v:>{col}}" for v in vals))

    print(f"{'='*75}")


def save_csv(combined, output_path):
    models = list(combined.keys())
    rows = []

    # Collect all categories
    all_cats = []
    for m in models:
        for cat in combined[m].get("per_category", {}).keys():
            if cat not in all_cats:
                all_cats.append(cat)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(["Metric"] + [MODEL_NAMES.get(m, m) for m in models])

        # Overall metrics
        metrics_rows = [
            ("Intent Accuracy",  "intent_accuracy",       lambda v: f"{v:.1%}"),
            ("Parse Success",    "parse_success_rate",    lambda v: f"{v:.1%}"),
            ("Apply Success",    "apply_success_rate",    lambda v: f"{v:.1%}"),
            ("Avg Latency (ms)", "avg_latency_ms",        lambda v: f"{v:.0f}"),
            ("Cost/100 cmds",    "cost_per_100_commands", lambda v: f"${v:.4f}"),
            ("Total Cmds",       "total",                 lambda v: str(int(v))),
        ]
        for label, key, fmt in metrics_rows:
            writer.writerow([label] + [fmt(combined[m]["metrics"].get(key, 0)) for m in models])

        writer.writerow([])
        writer.writerow(["Category Accuracy"] + [MODEL_NAMES.get(m, m) for m in models])

        for cat in all_cats:
            row = [cat]
            for m in models:
                cat_data = combined[m].get("per_category", {}).get(cat)
                if cat_data and cat_data["total"] > 0:
                    acc = cat_data["intent_ok"] / cat_data["total"]
                    row.append(f"{acc:.1%}")
                else:
                    row.append("-")
            writer.writerow(row)

    print(f"\nCSV saved: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None, help="Output CSV filename")
    parser.add_argument("--dir", default=None, help="Directory with eval JSON files")
    args = parser.parse_args()

    runs_dir = Path(args.dir) if args.dir else RUNS_DIR
    combined = load_runs(runs_dir)

    print_comparison(combined)
    print_per_category(combined)

    out_name = args.out or (DOCS_DIR / "consolidated_results.csv")
    save_csv(combined, out_name)
