"""
Generate evaluation charts for the thesis presentation.
Outputs to ~/Desktop/textToScene_figures/ at 300 DPI.

Run from the textToScene folder:
    python tests/generate_charts.py
"""
import json
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Paths ─────────────────────────────────────────────────────────────────────
DOCS   = Path(__file__).resolve().parent.parent / "docs"
DATA   = DOCS / "all_results.json"
OUTDIR = Path.home() / "Desktop" / "textToScene_figures"
OUTDIR.mkdir(exist_ok=True)

data   = json.loads(DATA.read_text(encoding="utf-8"))
models = data["models"]
ids    = list(models.keys())
names  = [m["name"] for m in models.values()]

# ── Global style ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":        "DejaVu Sans",
    "font.size":          17,
    "axes.titlesize":     21,
    "axes.labelsize":     18,
    "xtick.labelsize":    15,
    "ytick.labelsize":    15,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.grid":          True,
    "grid.color":         "#DDDDDD",
    "grid.linestyle":     "--",
    "grid.linewidth":     0.8,
    "figure.facecolor":   "white",
    "axes.facecolor":     "#FAFAFA",
})

# ── Colour palette ─────────────────────────────────────────────────────────────
COLORS = {
    "rule_based":            "#AAAAAA",
    "gpt-4o-mini":           "#4C9BE8",
    "gpt-4.1-mini":          "#1A5FAD",
    "gemini-2.5-flash-lite": "#34A853",
    "gemini-2.5-flash":      "#0F6B2F",
}
colors = [COLORS.get(i, "#BBBBBB") for i in ids]


# ════════════════════════════════════════════════════════════════════════════════
# FIG 1 — Overall intent accuracy  (horizontal bar)
# ════════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 5.5))
acc   = [models[i]["metrics"]["intent_accuracy"] * 100 for i in ids]
y_pos = np.arange(len(names))

bars = ax.barh(y_pos, acc, color=colors, height=0.58,
               edgecolor="white", linewidth=1.5)

for bar, v in zip(bars, acc):
    x_label = v - 2.2 if v > 30 else v + 1.0
    ha_label = "right" if v > 30 else "left"
    col = "white" if v > 30 else "#333333"
    ax.text(x_label, bar.get_y() + bar.get_height() / 2,
            f"{v:.1f}%", va="center", ha=ha_label,
            color=col, fontweight="bold", fontsize=17)

ax.set_yticks(y_pos)
ax.set_yticklabels(names, fontsize=16)
ax.set_xlabel("Intent Accuracy (%)", fontsize=18)
ax.set_title(
    "Overall Intent Accuracy per Model\n(125 evaluation prompts · 15 categories)",
    fontsize=21, fontweight="bold", pad=14,
)
ax.set_xlim(0, 114)
ax.axvline(100, color="#888888", linestyle="--", linewidth=1.0, alpha=0.7)
ax.set_axisbelow(True)
ax.yaxis.grid(False)

legend_handles = [
    mpatches.Patch(color="#AAAAAA", label="Rule-Based (baseline)"),
    mpatches.Patch(color="#4C9BE8", label="OpenAI models"),
    mpatches.Patch(color="#34A853", label="Google Gemini models"),
]
ax.legend(handles=legend_handles, loc="upper center",
          bbox_to_anchor=(0.5, -0.22), ncol=3,
          fontsize=15, framealpha=0.92)

plt.tight_layout()
plt.subplots_adjust(bottom=0.22)
fig.savefig(OUTDIR / "fig1_overall_accuracy.png", dpi=300, bbox_inches="tight")
plt.close()
print("Saved: fig1_overall_accuracy.png")


# ════════════════════════════════════════════════════════════════════════════════
# FIG 2 — Per-category accuracy (split 2-panel, LLM models only)
# ════════════════════════════════════════════════════════════════════════════════
categories = list(models[ids[0]]["per_category"].keys())
short_cats = [
    c.replace("Movement - Directional",    "Movement\nDirectional")
     .replace("Movement - Positional",     "Movement\nPositional")
     .replace("Scale - Natural Language",  "Scale\nNatural Lang.")
     .replace("Scale - Explicit",          "Scale Explicit")
     .replace("Rotation - Simple",         "Rotation\nSimple")
     .replace("Rotation - Axis Specified", "Rotation\nAxis Spec.")
     .replace("Prefabs - Add",             "Prefabs Add")
     .replace("Prefabs - Transform",       "Prefabs\nTransform")
     .replace("Composite Objects",         "Composite")
     .replace("Scene Management",          "Scene Mgmt")
     .replace("Undo/Redo Tests",           "Undo/Redo")
     .replace("Action Sequences",          "Action Seq.")
    for c in categories
]

llm_ids    = [i for i in ids if i != "rule_based"]
llm_names  = [models[i]["name"] for i in llm_ids]
llm_colors = [COLORS.get(i, "#BBBBBB") for i in llm_ids]
n_llm      = len(llm_ids)     # 4

SPLIT = 8    # first 8 categories on top row, last 7 on bottom
cat_groups = [list(range(0, SPLIT)), list(range(SPLIT, len(categories)))]

fig, axes = plt.subplots(2, 1, figsize=(17, 12), sharey=True)
fig.suptitle(
    "Per-Category Intent Accuracy  (LLM models only, 4 backends)",
    fontsize=21, fontweight="bold", y=0.99,
)

for ax, cat_idx in zip(axes, cat_groups):
    x     = np.arange(len(cat_idx))
    width = 0.21
    for j, mid in enumerate(llm_ids):
        cat_data = models[mid]["per_category"]
        vals = [
            cat_data[categories[c]]["intent_ok"] / cat_data[categories[c]]["total"] * 100
            for c in cat_idx
        ]
        offset = (j - n_llm / 2 + 0.5) * width
        bars = ax.bar(
            x + offset, vals, width,
            label=models[mid]["name"],
            color=llm_colors[j], edgecolor="white", linewidth=0.8,
        )
        for bar, v in zip(bars, vals):
            if v > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 1.5,
                    f"{int(v)}",
                    ha="center", va="bottom", fontsize=12, color="#333333",
                )

    ax.set_xticks(x)
    ax.set_xticklabels([short_cats[c] for c in cat_idx], fontsize=14)
    ax.set_ylabel("Accuracy (%)", fontsize=18)
    ax.set_ylim(0, 127)
    ax.axhline(100, color="#888888", linestyle="--", linewidth=0.9, alpha=0.7)
    ax.set_axisbelow(True)

axes[0].legend(loc="lower left", fontsize=15, ncol=2, framealpha=0.92)
plt.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig(OUTDIR / "fig2_per_category.png", dpi=300, bbox_inches="tight")
plt.close()
print("Saved: fig2_per_category.png")


# ════════════════════════════════════════════════════════════════════════════════
# FIG 3 — Latency vs Cost  (bubble = accuracy)
# ════════════════════════════════════════════════════════════════════════════════
# Annotation offsets chosen to avoid overlap given the data layout:
#   rule_based  : far left (2.8 ms, $0)  — annotate below
#   flash-lite  : fast+cheap cluster      — annotate above-right
#   gpt-4o-mini : ~same latency as 4.1-mini, cheaper
#   gpt-4.1-mini: similar latency, more expensive
#   flash       : slowest
OFFSETS = {
    "rule_based":            (-10, -28),
    "gpt-4o-mini":           ( 12,   8),
    "gpt-4.1-mini":          ( 12, -18),
    "gemini-2.5-flash-lite": ( 12,  10),
    "gemini-2.5-flash":      ( 12,   8),
}

fig, ax = plt.subplots(figsize=(11, 7))

for mid, color in zip(ids, colors):
    m    = models[mid]["metrics"]
    lat  = m["avg_latency_ms"]
    cost = m["cost_per_100_commands"]
    acc  = m["intent_accuracy"] * 100
    size = max(120, acc * 4.5)

    ax.scatter(lat, cost, s=size, color=color, alpha=0.88,
               edgecolors="white", linewidth=2.5, zorder=4)

    ox, oy = OFFSETS.get(mid, (12, 6))
    use_arrow = (mid == "rule_based")
    ax.annotate(
        f"{models[mid]['name']}\n{acc:.1f}% accuracy",
        xy=(lat, cost),
        xytext=(ox, oy),
        textcoords="offset points",
        fontsize=14, fontweight="bold", color="#222222",
        arrowprops=dict(arrowstyle="-", color="#BBBBBB", lw=1.2)
        if use_arrow else None,
    )

# Star annotation for best model
best_lat  = models["gemini-2.5-flash-lite"]["metrics"]["avg_latency_ms"]
best_cost = models["gemini-2.5-flash-lite"]["metrics"]["cost_per_100_commands"]
ax.annotate(
    "★ Best: fastest + cheapest\n    + highest accuracy",
    xy=(best_lat, best_cost),
    xytext=(best_lat - 900, best_cost + 0.055),
    fontsize=14, color="#0F6B2F", fontweight="bold",
    arrowprops=dict(arrowstyle="->", color="#0F6B2F", lw=1.6),
)

ax.set_xlabel("Average Latency (ms)", fontsize=18)
ax.set_ylabel("Cost per 100 Commands (USD)", fontsize=18)
ax.set_title(
    "Latency vs Cost per 100 Commands\n(bubble size proportional to intent accuracy)",
    fontsize=21, fontweight="bold",
)
ax.set_axisbelow(True)
plt.tight_layout()
fig.savefig(OUTDIR / "fig3_latency_cost.png", dpi=300, bbox_inches="tight")
plt.close()
print("Saved: fig3_latency_cost.png")


# ════════════════════════════════════════════════════════════════════════════════
# FIG 4 — Challenging categories (all 5 models incl. baseline)
# ════════════════════════════════════════════════════════════════════════════════
weak_cats   = ["Prefabs - Transform", "Action Sequences", "Recolor", "Object Creation"]
weak_labels = ["Prefabs\n(Transform)", "Action\nSequences", "Recolor", "Object\nCreation"]

n_all = len(ids)   # 5  ← FIXED: was using n_models=4 (LLMs only) causing bar misalignment
width = 0.155

fig, ax = plt.subplots(figsize=(12, 6.5))
x2 = np.arange(len(weak_cats))

for j, mid in enumerate(ids):
    cat_data = models[mid]["per_category"]
    vals = [
        cat_data[c]["intent_ok"] / cat_data[c]["total"] * 100
        for c in weak_cats
    ]
    offset = (j - n_all / 2 + 0.5) * width
    bars = ax.bar(
        x2 + offset, vals, width,
        label=models[mid]["name"],
        color=colors[j], edgecolor="white", linewidth=0.9,
    )
    for bar, v in zip(bars, vals):
        if v > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1.5,
                f"{int(v)}",
                ha="center", va="bottom", fontsize=13, color="#333333",
            )

ax.set_xticks(x2)
ax.set_xticklabels(weak_labels, fontsize=16)
ax.set_ylabel("Accuracy (%)", fontsize=18)
ax.set_ylim(0, 128)
ax.set_title(
    "Accuracy in Challenging Categories\n(all models including rule-based baseline)",
    fontsize=14, fontweight="bold",
)
ax.axhline(100, color="#888888", linestyle="--", linewidth=1.0, alpha=0.7)
ax.legend(fontsize=14, loc="lower right", ncol=2, framealpha=0.92)
ax.set_axisbelow(True)
plt.tight_layout()
fig.savefig(OUTDIR / "fig4_challenging_categories.png", dpi=300, bbox_inches="tight")
plt.close()
print("Saved: fig4_challenging_categories.png")


# ════════════════════════════════════════════════════════════════════════════════
# CSV — full evaluation table (Excel-ready with BOM for correct encoding)
# ════════════════════════════════════════════════════════════════════════════════
csv_path = OUTDIR / "evaluation_table.csv"
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow([""] + names)
    for label, fn in [
        ("Intent Accuracy (%)",   lambda m: f"{m['intent_accuracy']*100:.1f}"),
        ("Parse Success (%)",     lambda m: f"{m['parse_success_rate']*100:.1f}"),
        ("Apply Success (%)",     lambda m: f"{m['apply_success_rate']*100:.1f}"),
        ("Avg Latency (ms)",      lambda m: f"{m['avg_latency_ms']:.0f}"),
        ("Cost / 100 cmds (USD)", lambda m: f"${m['cost_per_100_commands']:.4f}"),
        ("Total Tokens In",       lambda m: str(m["total_tokens_in"])),
        ("Total Tokens Out",      lambda m: str(m["total_tokens_out"])),
    ]:
        writer.writerow([label] + [fn(models[i]["metrics"]) for i in ids])

    writer.writerow([])
    writer.writerow(["Category"] + names)
    for cat in categories:
        row = [cat]
        for mid in ids:
            d = models[mid]["per_category"][cat]
            acc = d["intent_ok"] / d["total"] * 100
            row.append(f"{acc:.0f}%  ({d['intent_ok']}/{d['total']})")
        writer.writerow(row)

print("Saved: evaluation_table.csv")
print(f"\nAll files saved to: {OUTDIR}")
print("  fig1_overall_accuracy.png")
print("  fig2_per_category.png")
print("  fig3_latency_cost.png")
print("  fig4_challenging_categories.png")
print("  evaluation_table.csv")
