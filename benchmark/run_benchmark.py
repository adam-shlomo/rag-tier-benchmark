#!/usr/bin/env python3
"""Self-contained benchmark runner (replaces the n8n pipeline).

Grid = models x levels x arms(zero-shot,RAG) x questions. For each cell it assembles
the prompt (with byte-invariance + contract-last assertions), calls OpenRouter with
streaming (to capture TTFT), retries with backoff, and appends one JSONL row with the
real token usage + cost. Resumable: cells already in the log are skipped.

Usage:
    export OPENROUTER_API_KEY=sk-or-...
    python run_benchmark.py --corpus ../corpus.json --out runs.jsonl \
        [--levels L0 L1 L2] [--arms zeroshot rag] [--models opus-4.8 llama3-8b ...] \
        [--max-tokens 4096] [--concurrency 6] [--limit N]

Dry run (no API calls; validates assembly + invariants over the whole grid):
    python run_benchmark.py --corpus ../corpus.json --dry-run
"""
import argparse, json, os, sys, time, threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

import prompts as P
import orclient
from models import MODELS, BY_KEY, OPENROUTER_MODELS
from extract import extract_block

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_log_lock = threading.Lock()


def load_corpus(path):
    data = json.load(open(path, encoding="utf-8"))
    cells = []  # flat work-list
    for subj in data["subjects"]:
        for q in subj["questions"]:
            cells.append(dict(subject=subj["code"], chunk=subj["chunk"],
                              qid=q["id"], parts=q["parts"],
                              question=q["question"], difficulty=q["difficulty"]))
    return cells


def cell_key(model_key, level, arm, qid):
    return f"{model_key}|{level}|{arm}|{qid}"


def load_done(out_path):
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            done.add(cell_key(r["model"], r["level"], r["arm"], r["qid"]))
    return done


def compute_cost(usage, model):
    pt = usage.get("prompt_tokens", 0) or 0
    ct = usage.get("completion_tokens", 0) or 0
    return pt * model["rate_in"] / 1e6 + ct * model["rate_out"] / 1e6


def call_openrouter(api_key, model, system, user, max_tokens, reasoning_budget=0, timeout=180):
    """Streamed call. Returns dict(text, usage, ttft_ms, latency_ms, finish_reason)."""
    body = {
        "model": model["openrouter_id"],
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    # uniform, disclosed thinking budget for reasoning-capable models (bounds cost + avoids
    # reasoning eating the whole max_tokens before the answer block is emitted)
    if model.get("reasoning") and reasoning_budget > 0:
        body["reasoning"] = {"max_tokens": reasoning_budget}
    t0 = time.time()
    ttft = None
    chunks, usage, finish = [], {}, None
    for raw in orclient.stream_lines(OPENROUTER_URL, api_key, body, timeout=timeout):
        if not raw or not raw.startswith("data: "):
            continue
        payload = raw[len("data: "):]
        if payload == "[DONE]":
            break
        obj = json.loads(payload)
        if obj.get("usage"):
            usage = obj["usage"]
        for ch in obj.get("choices", []):
            delta = ch.get("delta", {}).get("content")
            if delta:
                if ttft is None:
                    ttft = (time.time() - t0) * 1000.0
                chunks.append(delta)
            if ch.get("finish_reason"):
                finish = ch["finish_reason"]
    return dict(text="".join(chunks), usage=usage,
                ttft_ms=ttft, latency_ms=(time.time() - t0) * 1000.0,
                finish_reason=finish)


def run_cell(api_key, model, level, arm, cell, max_tokens, reasoning_budget=0, retries=4):
    chunk = cell["chunk"] if arm == "rag" else None
    system, user = P.assemble(level, cell["question"], cell["parts"], chunk=chunk)
    err = None
    for attempt in range(retries):
        try:
            res = call_openrouter(api_key, model, system, user, max_tokens, reasoning_budget)
            ok, answers = extract_block(res["text"])
            truncated = (res["finish_reason"] == "length") or (not ok)
            return dict(
                model=model["key"], tier=model["tier"], level=level, arm=arm,
                subject=cell["subject"], qid=cell["qid"], difficulty=cell["difficulty"],
                prompt_tokens=res["usage"].get("prompt_tokens"),
                completion_tokens=res["usage"].get("completion_tokens"),
                ttft_ms=round(res["ttft_ms"], 1) if res["ttft_ms"] else None,
                latency_ms=round(res["latency_ms"], 1),
                cost_usd=round(compute_cost(res["usage"], model), 6),
                extraction_ok=ok, truncated=truncated,
                finish_reason=res["finish_reason"],
                parts_expected=cell["parts"], parts_returned=list(answers.keys()),
                raw_output=res["text"], error=None,
            )
        except Exception as e:  # noqa
            err = f"{type(e).__name__}: {e}"
            time.sleep(min(2 ** attempt, 30))
    return dict(model=model["key"], tier=model["tier"], level=level, arm=arm,
                subject=cell["subject"], qid=cell["qid"], difficulty=cell["difficulty"],
                error=err, extraction_ok=False, truncated=True, raw_output="")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="../corpus.json")
    ap.add_argument("--out", default="runs.jsonl")
    ap.add_argument("--levels", nargs="+", default=P.LEVELS)
    ap.add_argument("--arms", nargs="+", default=["zeroshot", "rag"])
    ap.add_argument("--models", nargs="+", default=[m["key"] for m in OPENROUTER_MODELS],
                    help="default = OpenRouter-billed models only (Anthropic run on Max)")
    ap.add_argument("--max-tokens", type=int, default=5000)
    ap.add_argument("--reasoning-budget", type=int, default=3000,
                    help="uniform thinking-token budget for reasoning models (0=off). "
                         "Bounds cost and stops reasoning from eating the answer block.")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0, help="cap number of cells (smoke test)")
    ap.add_argument("--budget", type=float, default=0.0,
                    help="hard USD cap; stop launching new calls once spend hits 95%% of this. "
                         "0 = no cap. Uses models.py rates x actual usage, so set real rates first.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cells = load_corpus(args.corpus)
    models = [BY_KEY[k] for k in args.models]

    # build work-list
    work = []
    for m in models:
        for level in args.levels:
            for arm in args.arms:
                for c in cells:
                    work.append((m, level, arm, c))

    if args.dry_run:
        n_ok = 0
        for m, level, arm, c in work:
            chunk = c["chunk"] if arm == "rag" else None
            P.assemble(level, c["question"], c["parts"], chunk=chunk)  # asserts invariants
            n_ok += 1
        print(f"DRY RUN OK: assembled + invariant-checked {n_ok} prompts "
              f"({len(models)} models x {len(args.levels)} levels x {len(args.arms)} arms x {len(cells)} questions).")
        return

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("Set OPENROUTER_API_KEY")

    done = load_done(args.out)
    todo = [w for w in work if cell_key(w[0]["key"], w[1], w[2], w[3]["qid"]) not in done]
    # cheapest models first, so if a budget cap bites we've fully covered the cheap grid
    todo.sort(key=lambda w: w[0]["rate_in"] + w[0]["rate_out"])
    if args.limit:
        todo = todo[:args.limit]
    cap = args.budget * 0.95 if args.budget > 0 else float("inf")
    print(f"grid={len(work)}  done={len(done)}  todo={len(todo)}  "
          f"budget={'$%.2f (halt at $%.2f)' % (args.budget, cap) if args.budget > 0 else 'none'}")

    out = open(args.out, "a", encoding="utf-8")
    q = deque(todo)
    inflight, fmap = set(), {}
    n, spent, halted = 0, 0.0, False

    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        def submit_next():
            if q and spent < cap:
                item = q.popleft()
                fut = ex.submit(run_cell, api_key, item[0], item[1], item[2], item[3],
                                args.max_tokens, args.reasoning_budget)
                inflight.add(fut); fmap[fut] = item
                return True
            return False

        while len(inflight) < args.concurrency and submit_next():
            pass
        while inflight:
            finished, _ = wait(inflight, return_when=FIRST_COMPLETED)
            for fut in finished:
                inflight.discard(fut); fmap.pop(fut, None)
                row = fut.result()
                with _log_lock:
                    out.write(json.dumps(row, ensure_ascii=False) + "\n"); out.flush()
                n += 1
                spent += row.get("cost_usd") or 0.0
                flag = "ERR" if row.get("error") else ("TRUNC" if row.get("truncated") else "ok")
                print(f"[{n}] {row['model']:14} {row['level']} {row['arm']:8} "
                      f"{row['qid']:10} {flag:5} spent=${spent:.4f}")
            if spent >= cap and not halted:
                halted = True
                print(f"** BUDGET HALT: spent ${spent:.4f} >= 95%% of ${args.budget:.2f}. "
                      f"Draining {len(inflight)} in-flight, launching no more. {len(q)} cells left unrun (rerun to resume).**")
            while len(inflight) < args.concurrency and submit_next():
                pass
    out.close()
    tag = " (BUDGET-HALTED — rerun to finish remaining cells)" if halted else ""
    print(f"done. approx spend this run: ${spent:.4f}{tag}. Recompute exact cost from usage for the paper.")


if __name__ == "__main__":
    main()
