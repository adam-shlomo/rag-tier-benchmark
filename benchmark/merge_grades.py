#!/usr/bin/env python3
"""De-anonymize blind grades and write grades.jsonl for analyze.py.

Reads the grading workflow task-output + gradebatches/mapping.json + runs.jsonl (for
cost/tier). Maps each anonymized cid back to (model,level,arm,qid), normalizes the
per-part 0-2/0-1 scores to [0,1], attaches the metered cost, and emits one row per cell.

Usage: python merge_grades.py --task ../../tasks/<gradingid>.output [--out grades.jsonl]
"""
import argparse, json, collections
from extract import extract_block


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--mapping", default="gradebatches/mapping.json")
    ap.add_argument("--runs", default="runs.jsonl")
    ap.add_argument("--out", default="grades.jsonl")
    args = ap.parse_args()

    mapping = json.load(open(args.mapping, encoding="utf-8"))
    results = json.load(open(args.task, encoding="utf-8"))["result"]["results"]

    # cost + tier per cell
    meta = {}
    best = {}
    for l in open(args.runs, encoding="utf-8"):
        if not l.strip(): continue
        r = json.loads(l)
        k = (r["model"], r["level"], r["arm"], r["qid"])
        ok = (not r.get("error")) and extract_block(r.get("raw_output", ""))[0]
        if k not in best or (ok and not best[k][1]):
            best[k] = (r, ok)
    for (m, lv, ar, q), (r, ok) in best.items():
        meta[(m, lv, ar, q)] = dict(tier=r.get("tier"), subject=r.get("subject"),
                                    cost=r.get("cost_usd"), via=r.get("via", "openrouter"))

    out = open(args.out, "w", encoding="utf-8")
    n, missing = 0, 0
    for res in results:
        mp = mapping.get(res["path"])
        if not mp:
            continue
        cmap = mp["cmap"]
        for g in res.get("grades", []):
            cid = g.get("cid")
            if cid not in cmap:
                missing += 1; continue
            model, level, arm, qid = cmap[cid]
            parts = g.get("parts", [])
            if not parts:
                continue
            acc = sum(min(p.get("accuracy", 0), 2) for p in parts) / (2 * len(parts))
            rea = sum(min(p.get("reasoning", 0), 2) for p in parts) / (2 * len(parts))
            fmt = sum(min(p.get("format", 0), 1) for p in parts) / len(parts)
            md = meta.get((model, level, arm, qid), {})
            out.write(json.dumps(dict(
                run_key=f"{model}|{level}|{arm}|{qid}",
                model=model, tier=md.get("tier"), level=level, arm=arm,
                subject=md.get("subject"), qid=qid,
                accuracy=round(acc, 4), reasoning=round(rea, 4), format=round(fmt, 4),
                cost_usd=md.get("cost"), via=md.get("via"),
                n_parts=len(parts),
            ), ensure_ascii=False) + "\n")
            n += 1
    out.close()
    print(f"wrote {n} graded cells to {args.out}  (unmapped cids: {missing})")
    by = collections.Counter()
    for l in open(args.out, encoding="utf-8"):
        by[json.loads(l)["model"]] += 1
    print("graded per model:", dict(by))


if __name__ == "__main__":
    main()
