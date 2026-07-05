#!/usr/bin/env python3
"""Merge Max-side (Opus/Sonnet) inference outputs into runs.jsonl.

Reads a workflow task-output JSON ({result:{results:[{model,level,arm,qid,raw_output}]}}),
re-derives subject/difficulty/parts from corpus_run.json, parses the answer block, and
imputes token counts + cost at LIST rates (these ran on Max, so cost is imputed for the
Pareto analysis, not money spent). TTFT is null (subscription-sourced, not API-comparable).

Usage: python merge_max.py --task ../../tasks/<id>.output [--corpus ../corpus_run.json --out runs.jsonl]
"""
import argparse, json, os
from extract import extract_block
from models import BY_KEY

CHARS_PER_TOK = 3.3  # blended estimate for Hebrew+LaTeX+English on the Claude tokenizer (imputed)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, help="workflow task .output JSON")
    ap.add_argument("--corpus", default="../corpus_run.json")
    ap.add_argument("--out", default="runs.jsonl")
    ap.add_argument("--promptdir", default="maxprompts")
    args = ap.parse_args()

    corpus = json.load(open(args.corpus, encoding="utf-8"))
    qmeta = {q["id"]: (s["code"], q["difficulty"], q["parts"])
             for s in corpus["subjects"] for q in s["questions"]}

    payload = json.load(open(args.task, encoding="utf-8"))
    results = payload["result"]["results"]

    # avoid dup rows: keys already in runs.jsonl
    done = set()
    if os.path.exists(args.out):
        for l in open(args.out, encoding="utf-8"):
            if l.strip():
                r = json.loads(l)
                done.add(f"{r['model']}|{r['level']}|{r['arm']}|{r['qid']}")

    out = open(args.out, "a", encoding="utf-8")
    n_add, n_ok = 0, 0
    for r in results:
        key = f"{r['model']}|{r['level']}|{r['arm']}|{r['qid']}"
        if key in done:
            continue
        raw = r.get("raw_output", "")
        if not raw.strip():
            continue  # failed/throttled cell — skip so it can be retried and merged later
        code, diff, parts = qmeta[r["qid"]]
        ok, block = extract_block(raw)
        m = BY_KEY[r["model"]]
        # impute tokens/cost
        ppath = os.path.join(args.promptdir, f"{r['model']}_{r['level']}_{r['arm']}_{r['qid']}.txt")
        prompt_chars = os.path.getsize(ppath) if os.path.exists(ppath) else 0
        ptok = int(prompt_chars / CHARS_PER_TOK)
        ctok = int(len(raw) / CHARS_PER_TOK)
        cost = ptok * m["rate_in"] / 1e6 + ctok * m["rate_out"] / 1e6
        row = dict(
            model=r["model"], tier=m["tier"], level=r["level"], arm=r["arm"],
            subject=code, qid=r["qid"], difficulty=diff,
            prompt_tokens=ptok, completion_tokens=ctok,
            ttft_ms=None, latency_ms=None,
            cost_usd=round(cost, 6), cost_imputed=True, via="max",
            extraction_ok=ok, truncated=(not ok), finish_reason="max_agent",
            parts_expected=parts, parts_returned=list(block.keys()),
            raw_output=raw, error=(r.get("error")),
        )
        out.write(json.dumps(row, ensure_ascii=False) + "\n")
        n_add += 1
        n_ok += 1 if ok else 0
    out.close()
    print(f"merged {n_add} Max rows ({n_ok} with a parseable block) into {args.out}")


if __name__ == "__main__":
    main()
