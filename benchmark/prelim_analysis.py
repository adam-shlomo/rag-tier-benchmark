#!/usr/bin/env python3
"""Preliminary analysis on grades_auto.jsonl (numeric-recall proxy + real metered cost).
Answers the 3 RQs provisionally; to be re-run on the full LLM grades.jsonl later."""
import json, collections

rows = [json.loads(l) for l in open("grades_auto.jsonl", encoding="utf-8")]
cell = collections.defaultdict(list)
for r in rows:
    cell[(r["model"], r.get("tier"), r["level"], r["arm"])].append(r)

def acc(rs): return sum(x["numeric_recall"] for x in rs) / len(rs)
def cost(rs): return sum((x.get("cost_usd") or 0) for x in rs) / len(rs)

summ = {}
for k, rs in cell.items():
    m, tier, lvl, arm = k
    a = acc(rs); c = cost(rs)
    summ[k] = dict(model=m, tier=tier, level=lvl, arm=arm, n=len(rs),
                   acc=a, mean_cost=c, cpc=(c / a if a > 1e-9 else float("inf")))

TIER = {}
for k, v in summ.items():
    TIER[k[0]] = v["tier"]

print("== per (model, level, arm): provisional accuracy | $/call | $/correct ==")
for m in sorted(summ, key=lambda k: (TIER[k[0]], k[0])):
    pass
for m in sorted(set(k[0] for k in summ), key=lambda x: (TIER[x], x)):
    print(f"\n{m}  (tier {TIER[m]})")
    for lvl in ["L0", "L1", "L2"]:
        for arm in ["zeroshot", "rag"]:
            v = summ.get((m, TIER[m], lvl, arm))
            if v:
                cpc = "inf" if v["cpc"] == float("inf") else f"${v['cpc']*1000:.3f}m"
                print(f"   {lvl} {arm:8} acc={v['acc']:.3f}  ${v['mean_cost']*1000:.3f}m/call  {cpc}/correct")

# model-level aggregates (avg over levels+arms) + best-of-ladder
print("\n== model summary: mean acc, best-of-ladder acc, prompt-lift L0->L2, RAG-delta ==")
agg = []
for m in sorted(set(k[0] for k in summ), key=lambda x: (TIER[x], x)):
    rs = [v for k, v in summ.items() if k[0] == m]
    mean_acc = sum(v["acc"] for v in rs) / len(rs)
    best = max(rs, key=lambda v: v["acc"])
    # prompt lift: mean over arms of acc(L2)-acc(L0)
    def acc_lvl(lvl):
        xs=[v["acc"] for v in rs if v["level"]==lvl]; return sum(xs)/len(xs) if xs else None
    lift = (acc_lvl("L2")-acc_lvl("L0")) if acc_lvl("L0") is not None and acc_lvl("L2") is not None else None
    def acc_arm(a):
        xs=[v["acc"] for v in rs if v["arm"]==a]; return sum(xs)/len(xs) if xs else None
    rag = (acc_arm("rag")-acc_arm("zeroshot")) if acc_arm("rag") is not None and acc_arm("zeroshot") is not None else None
    meanc = sum(v["mean_cost"] for v in rs)/len(rs)
    agg.append(dict(model=m, tier=TIER[m], mean_acc=mean_acc, best_acc=best["acc"],
                    best_cell=f"{best['level']}/{best['arm']}", mean_cost=meanc,
                    best_cpc=min(v["cpc"] for v in rs), lift=lift, rag=rag))
    print(f"{m:16} t{TIER[m]}  mean={mean_acc:.3f}  best={best['acc']:.3f}@{best['level']}/{best['arm']:8}  "
          f"lift(L0->L2)={lift:+.3f}  RAG={rag:+.3f}  min$/correct=${min(v['cpc'] for v in rs)*1000:.3f}m")

# RQ answers
print("\n== RQ1 best bang-for-buck (min $/correct across all cells) ==")
allcells = sorted(summ.values(), key=lambda v: v["cpc"])[:6]
for v in allcells:
    print(f"   {v['model']:14} {v['level']}/{v['arm']:8} $/correct=${v['cpc']*1000:.3f}m  acc={v['acc']:.3f}")

print("\n== RQ2 best overall (max accuracy) ==")
for v in sorted(summ.values(), key=lambda v: -v["acc"])[:6]:
    print(f"   {v['model']:14} {v['level']}/{v['arm']:8} acc={v['acc']:.3f}  $/correct=${v['cpc']*1000:.3f}m")

print("\n== RQ3 cheap vs frontier (best-of-ladder) ==")
frontier_best = max((a for a in agg if a["tier"] == 1), key=lambda a: a["best_acc"])
cheap = [a for a in agg if a["tier"] == 3]
print(f"   fair frontier ceiling: {frontier_best['model']} acc={frontier_best['best_acc']:.3f} "
      f"($/correct min ${frontier_best['best_cpc']*1000:.3f}m)")
for a in sorted(cheap, key=lambda a: -a["best_acc"]):
    verdict = "MATCHES/BEATS" if a["best_acc"] >= frontier_best["best_acc"] - 0.02 else "below"
    print(f"   T3 {a['model']:14} best acc={a['best_acc']:.3f} ({verdict} frontier) "
          f"min$/correct=${a['best_cpc']*1000:.3f}m  ({a['best_cpc'] < frontier_best['best_cpc'] and 'cheaper' or 'pricier'})")
