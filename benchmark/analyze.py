#!/usr/bin/env python3
"""Analysis: turns grades.jsonl into the paper's headline numbers.

Computes per (model, level, arm):
  - quality Q (weighted Accuracy/Reasoning/Format), accuracy
  - mean cost/call, cost-per-correct = mean_cost / accuracy
  - RAG delta (rag - zeroshot) per model x level
  - prompt-lift curve (L0->L1->L2) per model
  - Pareto frontier in (cost_per_correct, quality) and best-of-ladder fair ceiling

Answers: #best-overall (max Q), #best-bang-for-buck (Pareto knee / min $/correct),
#cheap>=frontier (Tier-3 cell dominating a frontier cell).

Usage: python analyze.py --grades grades.jsonl [--out summary.csv] [--w 0.6 0.3 0.1]
"""
import argparse, json, csv
from collections import defaultdict

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grades", default="grades.jsonl")
    ap.add_argument("--out", default="summary.csv")
    ap.add_argument("--w", nargs=3, type=float, default=[0.6, 0.3, 0.1],
                    help="weights for accuracy reasoning format")
    args = ap.parse_args()
    wa, wr, wf = args.w

    cells = defaultdict(list)          # (model,tier,level,arm) -> [rows]
    for line in open(args.grades, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        cells[(r["model"], r.get("tier"), r["level"], r["arm"])].append(r)

    def q_of(r):
        a = r.get("accuracy") or 0
        rr = r.get("reasoning"); f = r.get("format")
        rr = a if rr is None else rr   # if no LLM reasoning, fall back to accuracy
        f = 1.0 if f is None else f
        return wa * a + wr * rr + wf * f

    summary = {}
    for key, rows in cells.items():
        model, tier, level, arm = key
        n = len(rows)
        acc = sum(r.get("accuracy") or 0 for r in rows) / n
        Q = sum(q_of(r) for r in rows) / n
        mean_cost = sum(r.get("cost_usd") or 0 for r in rows) / n
        # cost-per-correct: cost of a fully-correct answer's worth; guard acc=0
        cpc = (mean_cost / acc) if acc > 1e-9 else float("inf")
        trunc = sum(1 for r in rows if r.get("truncated")) / n
        summary[key] = dict(model=model, tier=tier, level=level, arm=arm, n=n,
                            accuracy=round(acc, 3), Q=round(Q, 3),
                            mean_cost=round(mean_cost, 6),
                            cost_per_correct=(round(cpc, 6) if cpc != float("inf") else None),
                            trunc_rate=round(trunc, 3))

    rows = list(summary.values())
    # --- write CSV ---
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    # --- headline readouts ---
    def show(title, rs):
        print(f"\n== {title} ==")
        for r in rs:
            print(f"  {r['model']:14} {r['level']} {r['arm']:8} "
                  f"Q={r['Q']:.3f} acc={r['accuracy']:.3f} "
                  f"$/call={r['mean_cost']:.5f} $/correct={r['cost_per_correct']} trunc={r['trunc_rate']}")

    # best overall (max Q, any config)
    show("BEST OVERALL (top 5 by Q)", sorted(rows, key=lambda r: -r["Q"])[:5])

    # best bang-for-buck (min cost-per-correct among acc>0)
    payable = [r for r in rows if r["cost_per_correct"] is not None]
    show("BEST BANG-FOR-BUCK (top 5 by $/correct)", sorted(payable, key=lambda r: r["cost_per_correct"])[:5])

    # Pareto frontier in (cost_per_correct asc, Q desc): keep non-dominated
    pts = sorted(payable, key=lambda r: (r["cost_per_correct"], -r["Q"]))
    frontier, best_q = [], -1
    for r in pts:
        if r["Q"] > best_q:
            frontier.append(r); best_q = r["Q"]
    show("PARETO FRONTIER (cost_per_correct vs Q)", frontier)

    # per-model best-of-ladder (fair ceiling) + prompt lift
    by_model = defaultdict(list)
    for r in rows:
        by_model[r["model"]].append(r)
    print("\n== FAIR CEILING (best-of-ladder Q per model) + prompt lift L0->L2 ==")
    for model, rs in sorted(by_model.items(), key=lambda kv: -max(x["Q"] for x in kv[1])):
        best = max(rs, key=lambda r: r["Q"])
        l0 = min((r["Q"] for r in rs if r["level"] == "L0"), default=None)
        l2 = max((r["Q"] for r in rs if r["level"] == "L2"), default=None)
        lift = (round(l2 - l0, 3) if (l0 is not None and l2 is not None) else None)
        print(f"  {model:14} bestQ={best['Q']:.3f} @ {best['level']}/{best['arm']}  "
              f"prompt-lift(L0->L2)={lift}")

    # RAG delta per (model, level)
    print("\n== RAG DELTA (Q_rag - Q_zeroshot) ==")
    byml = {(r["model"], r["level"], r["arm"]): r for r in rows}
    for (model, tier, level, arm) in sorted(cells):
        if arm != "rag":
            continue
        z = byml.get((model, level, "zeroshot"))
        g = byml.get((model, level, "rag"))
        if z and g:
            print(f"  {model:14} {level}: delta={g['Q']-z['Q']:+.3f}  (zs={z['Q']:.3f} -> rag={g['Q']:.3f})")

    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
