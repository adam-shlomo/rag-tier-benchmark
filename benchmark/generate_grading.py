#!/usr/bin/env python3
"""Generate blind grading batches for the Max/Opus grader.

Per question, collect all usable candidate outputs, STRIP model identity (candidates
labeled c000..), pseudo-shuffle by content hash (decouples order from model), and batch.
Each batch -> a task file (question + full answer key + anonymized candidate solutions).
A mapping.json records cid -> (model,level,arm,qid) so grades map back after the blind pass.

Usage: python generate_grading.py [--batch 10 --outdir gradebatches]
"""
import argparse, json, os, hashlib, collections
from extract import extract_block


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="../corpus_run.json")
    ap.add_argument("--runs", default="runs.jsonl")
    ap.add_argument("--outdir", default="gradebatches")
    ap.add_argument("--batch", type=int, default=10)
    ap.add_argument("--models", nargs="+", default=None, help="only grade these models")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    corpus = json.load(open(args.corpus, encoding="utf-8"))
    qinfo = {q["id"]: (s["code"], q) for s in corpus["subjects"] for q in s["questions"]}

    # dedup runs, keep usable
    best = {}
    for l in open(args.runs, encoding="utf-8"):
        if not l.strip(): continue
        r = json.loads(l)
        k = (r["model"], r["level"], r["arm"], r["qid"])
        ok = (not r.get("error")) and extract_block(r.get("raw_output", ""))[0]
        r["_u"] = ok
        if k not in best or (ok and not best[k]["_u"]): best[k] = r
    usable = [r for r in best.values() if r["_u"]]
    if args.models:
        usable = [r for r in usable if r["model"] in args.models]

    by_q = collections.defaultdict(list)
    for r in usable:
        by_q[r["qid"]].append(r)

    mapping = {}
    n_batches = 0
    cid_counter = 0
    for qid, cands in by_q.items():
        cands.sort(key=lambda r: hashlib.md5(r["raw_output"].encode()).hexdigest())  # blind order
        code, q = qinfo[qid]
        for i in range(0, len(cands), args.batch):
            grp = cands[i:i + args.batch]
            bfile = os.path.join(args.outdir, f"{qid}_b{i//args.batch}.txt")
            cmap = {}
            lines = [
                f"QUESTION ({code}, Hebrew):\n{q['question']}\n",
                f"\nGROUND-TRUTH ANSWER KEY (authoritative, worked solution + final answers):\n{q['answerKey']}\n",
                f"\nGROUND-TRUTH FINAL ANSWERS: {json.dumps(q['finalAnswers'], ensure_ascii=False)}\n",
                f"\nPARTS TO GRADE: {q['parts']}\n",
                "\n" + "=" * 60 + "\nCANDIDATE ANSWERS TO GRADE (identities hidden):\n",
            ]
            for r in grp:
                cid = f"c{cid_counter:03d}"; cid_counter += 1
                cmap[cid] = [r["model"], r["level"], r["arm"], r["qid"]]
                lines.append(f"\n### {cid}\n{r.get('raw_output','')}\n")
            open(bfile, "w", encoding="utf-8").write("".join(lines))
            mapping[os.path.abspath(bfile)] = dict(qid=qid, parts=q["parts"], cmap=cmap)
            n_batches += 1

    json.dump(mapping, open(os.path.join(args.outdir, "mapping.json"), "w"), ensure_ascii=False)
    print(f"wrote {n_batches} grading batches ({cid_counter} candidates) to {args.outdir}/")
    print(f"batches by question: {collections.Counter(m['qid'] for m in mapping.values())}")


if __name__ == "__main__":
    main()
