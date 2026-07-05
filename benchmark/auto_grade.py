#!/usr/bin/env python3
"""Deterministic numeric accuracy (no LLM). Provisional signal + free fast-path.

Per cell: re-extract the answer block, pull the ground-truth numeric values from the
question's key, and score numeric recall = (# key values matched in the model block) /
(# key values). Questions whose key has < MIN_NUMS distinct numeric values are 'symbolic'
and marked not-auto-gradable (deferred to the LLM grader). Cost $0.

Usage: python auto_grade.py --corpus ../corpus_run.json --runs runs.jsonl --out grades_auto.jsonl
"""
import argparse, json, re, collections
from extract import extract_block

MIN_NUMS = 3          # a question needs >= this many key numbers to be numeric-auto-gradable
REL_TOL = 0.03

_SUP = str.maketrans("⁻⁺⁰¹²³⁴⁵⁶⁷⁸⁹", "-+0123456789")

def _norm(s):
    if not s: return ""
    s = s.translate(_SUP)
    # scientific: \times 10^{k}, ×10^{k}, ·10^{k}, x10^k  -> e{k}
    s = re.sub(r"\s*(?:\\times|×|·|\\cdot|x)\s*10\s*\^?\s*\{?\s*([-+]?\d+)\s*\}?", r"e\1", s)
    s = re.sub(r"\bd?frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"(\1/\2)", s)   # \dfrac{a}{b}->(a/b)
    s = re.sub(r"\\[a-zA-Z]+", " ", s)   # strip remaining latex commands
    return s

_NUM = re.compile(r"[-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?")

def _sig(v):
    # 4 significant figures — preserves magnitude (9.42e-9 stays 9.42e-9, unlike round(,6))
    if v == 0: return 0.0
    return float("%.4g" % v)

def numbers(s):
    """Set of float values in a (LaTeX/unicode) string, incl. simple fractions a/b."""
    s = _norm(s)
    vals = set()
    # fractions a/b (after normalisation)
    for a, b in re.findall(r"(-?\d+(?:\.\d+)?)\s*/\s*(-?\d+(?:\.\d+)?)", s):
        try:
            fb = float(b)
            if fb: vals.add(_sig(float(a) / fb))
        except Exception: pass
    for m in _NUM.findall(s):
        try:
            vals.add(_sig(float(m)))
        except Exception: pass
    return vals

def match(target, pool):
    for p in pool:
        d = max(abs(target), abs(p), 1e-9)
        if abs(target - p) <= REL_TOL * d: return True
    return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="../corpus_run.json")
    ap.add_argument("--runs", default="runs.jsonl")
    ap.add_argument("--out", default="grades_auto.jsonl")
    args = ap.parse_args()

    corpus = json.load(open(args.corpus, encoding="utf-8"))
    keynums, gradable = {}, {}
    for s in corpus["subjects"]:
        for q in s["questions"]:
            kv = set()
            for fa in q["finalAnswers"]:
                kv |= numbers(fa)
            keynums[q["id"]] = kv
            gradable[q["id"]] = len(kv) >= MIN_NUMS

    out = open(args.out, "w", encoding="utf-8")
    per = collections.defaultdict(lambda: [0.0, 0])   # (model,level,arm) -> [sum_acc, n]
    seen = set()
    for line in open(args.runs, encoding="utf-8"):
        if not line.strip(): continue
        r = json.loads(line)
        k = (r["model"], r["level"], r["arm"], r["qid"])
        if k in seen or r.get("error"): continue
        seen.add(k)
        if not gradable.get(r["qid"]): continue
        ok, block = extract_block(r.get("raw_output", ""))
        model_pool = set()
        for v in block.values():
            model_pool |= numbers(v)
        kv = keynums[r["qid"]]
        hit = sum(1 for t in kv if match(t, model_pool))
        acc = hit / len(kv) if kv else 0.0
        per[(r["model"], r["level"], r["arm"])][0] += acc
        per[(r["model"], r["level"], r["arm"])][1] += 1
        out.write(json.dumps(dict(model=r["model"], tier=r.get("tier"), level=r["level"],
                                  arm=r["arm"], qid=r["qid"], subject=r["subject"],
                                  numeric_recall=round(acc, 3), key_n=len(kv), hit=hit,
                                  extraction_ok=ok, cost_usd=r.get("cost_usd"),
                                  via=r.get("via", "openrouter")), ensure_ascii=False) + "\n")
    out.close()

    ng = sum(1 for q in gradable.values() if q)
    print(f"auto-graded numeric-recall on {ng}/{len(gradable)} questions "
          f"(symbolic questions deferred to LLM).")
    print(f"\n{'model':16} {'level':4} {'zs':>6} {'rag':>6}   (numeric-recall accuracy)")
    models = sorted(set(m for m, l, a in per))
    for m in models:
        for lvl in ["L0", "L1", "L2"]:
            zs = per.get((m, lvl, "zeroshot")); rg = per.get((m, lvl, "rag"))
            zsv = f"{zs[0]/zs[1]:.2f}" if zs and zs[1] else "  -"
            rgv = f"{rg[0]/rg[1]:.2f}" if rg and rg[1] else "  -"
            print(f"{m:16} {lvl:4} {zsv:>6} {rgv:>6}")

if __name__ == "__main__":
    main()
