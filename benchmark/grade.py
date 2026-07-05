#!/usr/bin/env python3
"""Hybrid blind grader (Step 6).

For each run row: strip model identity, extract the ===FINAL=== block, and score
per part on Accuracy / Reasoning / Format vs the exact ground-truth key.

Cost saver: a deterministic NUMERIC fast-path auto-scores Accuracy for parts whose
answer is a plain number matching the key within tolerance — no LLM call. The LLM
grader (Opus 4.8) is used for the rest of Accuracy (symbolic answers) and always for
Reasoning + Format. Add structured per-part numeric keys to corpus.json to push more
parts onto the free path.

Usage:
    export OPENROUTER_API_KEY=sk-or-...
    python grade.py --corpus ../corpus.json --runs runs.jsonl --out grades.jsonl \
        [--no-llm]   # deterministic-only pass (accuracy where numeric, skip reasoning/format)
"""
import argparse, json, os, time
import orclient
import prompts as P
from extract import extract_block, parse_answer, numeric_match
from models import GRADER

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

GRADER_SYSTEM = (
    "You are a strict, impartial grader for hard Hebrew university math/physics answers. "
    "You are given the question, the authoritative worked solution + final answers (ground truth), "
    "and a candidate's answer block. Grade EACH part independently. Accept any algebraically "
    "equivalent form (e.g. 5/\\sqrt{21} = \\sqrt{25/21} = 1.091; unexpanded vs expanded). "
    "Score per part: accuracy 0/1/2 (2=correct final value(s), 1=partially right/right method wrong "
    "number, 0=wrong or missing), reasoning 0/1/2 (is the shown work sound and complete — from the "
    "candidate's full output), format 0/1 (obeyed the contract: right label, LaTeX, units, symbolic+"
    "numeric where asked). Output ONLY JSON."
)

def grade_prompt(q, key, final_answers, full_output, block_answers):
    parts = q["parts"]
    return (
        f"QUESTION (Hebrew):\n{q['question']}\n\n"
        f"GROUND-TRUTH WORKED SOLUTION:\n{key}\n\n"
        f"GROUND-TRUTH FINAL ANSWERS:\n{json.dumps(final_answers, ensure_ascii=False)}\n\n"
        f"CANDIDATE FULL OUTPUT:\n{full_output}\n\n"
        f"CANDIDATE FINAL BLOCK (parsed): {json.dumps(block_answers, ensure_ascii=False)}\n\n"
        f"Parts to grade: {parts}. Return JSON exactly:\n"
        '{\"parts\": [{\"part\": \"א\", \"accuracy\": 0-2, \"reasoning\": 0-2, \"format\": 0-1, '
        '\"note\": \"one line\"}, ...]}'
    )

def call_grader(api_key, system, user, retries=4):
    body = {"model": GRADER["openrouter_id"],
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": 0, "max_tokens": 1500,
            "response_format": {"type": "json_object"}}
    for attempt in range(retries):
        try:
            j = orclient.post_json(OPENROUTER_URL, api_key, body)
            content = j["choices"][0]["message"]["content"]
            usage = j.get("usage", {})
            cost = (usage.get("prompt_tokens", 0) * GRADER["rate_in"]
                    + usage.get("completion_tokens", 0) * GRADER["rate_out"]) / 1e6
            return json.loads(content), cost
        except Exception:
            time.sleep(min(2 ** attempt, 30))
    return None, 0.0


def key_final_for_part(final_answers, part, idx):
    """Best-effort ground-truth string for a part (for the numeric fast-path)."""
    for fa in final_answers:
        if fa.strip().startswith(part) or f"({part})" in fa[:6] or f"חלק {part}" in fa[:12]:
            return fa
    return final_answers[idx] if idx < len(final_answers) else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="../corpus.json")
    ap.add_argument("--runs", default="runs.jsonl")
    ap.add_argument("--out", default="grades.jsonl")
    ap.add_argument("--no-llm", action="store_true")
    args = ap.parse_args()

    corpus = json.load(open(args.corpus, encoding="utf-8"))
    qmap = {q["id"]: (q, subj) for subj in corpus["subjects"] for q in subj["questions"]}
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key and not args.no_llm:
        raise SystemExit("Set OPENROUTER_API_KEY (or use --no-llm)")

    done = set()
    if os.path.exists(args.out):
        for l in open(args.out, encoding="utf-8"):
            if l.strip():
                done.add(json.loads(l)["run_key"])

    out = open(args.out, "a", encoding="utf-8")
    grading_cost, n_llm, n_free = 0.0, 0, 0
    for line in open(args.runs, encoding="utf-8"):
        if not line.strip():
            continue
        run = json.loads(line)
        rk = f"{run['model']}|{run['level']}|{run['arm']}|{run['qid']}"
        if rk in done:
            continue
        q, subj = qmap[run["qid"]]
        ok, block = extract_block(run.get("raw_output", ""))
        parts = q["parts"]

        # deterministic numeric fast-path for accuracy
        free_acc, free_src, need_llm = {}, {}, False
        for i, part in enumerate(parts):
            ans = block.get(part)
            if ans is None:
                free_acc[part] = 0; free_src[part] = "omitted"  # part not answered
                continue
            pa = parse_answer(ans)
            model_val = pa["numeric"] or pa["text"]
            nm = numeric_match(model_val, key_final_for_part(q["finalAnswers"], part, i))
            if nm is True:
                free_acc[part] = 2; free_src[part] = "numeric"
            elif nm is False:
                free_acc[part] = 0; free_src[part] = "numeric"
            else:
                need_llm = True  # symbolic / undecidable -> LLM decides accuracy

        llm = None
        if not args.no_llm and (need_llm or True):  # always LLM for reasoning/format
            user = grade_prompt(q, q["answerKey"], q["finalAnswers"], run.get("raw_output", ""), block)
            llm, cost = call_grader(api_key, GRADER_SYSTEM, user)
            grading_cost += cost
            n_llm += 1
        else:
            n_free += 1

        # merge: prefer deterministic accuracy where available; take reasoning/format from LLM
        merged = []
        llm_by_part = {p["part"]: p for p in (llm or {}).get("parts", [])} if llm else {}
        for part in parts:
            lp = llm_by_part.get(part, {})
            if part in free_acc:
                acc, src = free_acc[part], free_src[part]
            else:
                acc, src = lp.get("accuracy", 0), "llm"
            merged.append(dict(part=part, accuracy=acc,
                               reasoning=lp.get("reasoning"), format=lp.get("format"),
                               note=lp.get("note", ""), acc_source=src))

        # per-question aggregate (normalize: acc/2, reas/2, fmt/1)
        def avg(xs):
            xs = [x for x in xs if x is not None]
            return sum(xs) / len(xs) if xs else None
        q_acc = avg([m["accuracy"] / 2 for m in merged])
        q_rea = avg([m["reasoning"] / 2 for m in merged if m["reasoning"] is not None])
        q_fmt = avg([m["format"] for m in merged if m["format"] is not None])
        row = dict(run_key=rk, model=run["model"], tier=run.get("tier"),
                   level=run["level"], arm=run["arm"], subject=run["subject"],
                   qid=run["qid"], difficulty=run.get("difficulty"),
                   extraction_ok=ok, truncated=run.get("truncated"),
                   cost_usd=run.get("cost_usd"),
                   accuracy=q_acc, reasoning=q_rea, format=q_fmt, parts=merged)
        out.write(json.dumps(row, ensure_ascii=False) + "\n"); out.flush()
    out.close()
    print(f"graded. llm_calls={n_llm} free_calls_skipped={n_free} grading_cost=${grading_cost:.4f}")


if __name__ == "__main__":
    main()
