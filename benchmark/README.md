# Hebrew-STEM RAG benchmark — runner (no n8n)

Self-contained pipeline for the prompt-as-equalizer study: run 8 models × 3 prompt
levels × {zero-shot, RAG} × 20 questions, grade the outputs, and produce the
cost/quality analysis. Everything is plain Python + the OpenRouter HTTP API.

## Files
| file | role |
|------|------|
| `prompts.py` | invariant blocks + L0/L1/L2 ladder + `assemble()` (contract-last, byte-invariance assertions) |
| `extract.py` | deterministic `===FINAL===` block parser + numeric compare |
| `models.py` | 8-model registry (OpenRouter IDs + **estimated** pricing) + grader model |
| `run_benchmark.py` | the runner: streams calls, captures usage/TTFT, retries, JSONL log, **resumable** |
| `grade.py` | hybrid blind grader: free numeric Accuracy fast-path + Opus for Reasoning/Format |
| `analyze.py` | cost-per-correct, Pareto frontier, prompt-lift, RAG delta, best-of-ladder ceiling |
| `../corpus.json` | 20 questions + 5 chunks + exact verified keys (part labels detected) |

## Prereqs
```
pip install requests
export OPENROUTER_API_KEY=sk-or-...
```
Then **edit `models.py`**: confirm each `openrouter_id` exists at https://openrouter.ai/models
(some planned IDs — gpt-5.5, gemini-3.1-pro, deepseek-v4, gemma-3-9b — may need the nearest
real slug) and repull `rate_in`/`rate_out`. Pricing there is for budgeting only; **actual cost
is recomputed from each call's returned `usage`.**

## Run sequence
```bash
# 0. validate assembly + invariants over the whole grid, spend $0
python run_benchmark.py --corpus ../corpus.json --dry-run

# 1. smoke test: a few real cells on the cheapest models first
python run_benchmark.py --models llama3-8b gemma3-9b --limit 6 --out runs.jsonl

# 2. full grid (resumable — safe to Ctrl-C and rerun; done cells are skipped)
python run_benchmark.py --corpus ../corpus.json --out runs.jsonl --concurrency 6

# 3. grade (hybrid; --no-llm does a free deterministic-only pass first if you want)
python grade.py --corpus ../corpus.json --runs runs.jsonl --out grades.jsonl

# 4. analysis → summary.csv + printed headline tables
python analyze.py --grades grades.jsonl --out summary.csv
```

## Budget-fitting config (≤ $20 API, grading + Anthropic models on Claude Max)

Grading and the two Anthropic benchmark models (Opus 4.8, Sonnet 5) run on your **Max
subscription** (off the API meter). Only the 6 non-Anthropic models go through OpenRouter:

```bash
# ~$11 of OpenRouter spend; --budget is a hard safety net (halts new launches at 95% of $20)
python run_benchmark.py --corpus ../corpus.json --out runs.jsonl --budget 20 \
    --models gpt-5.5 gemini-3.1-pro gemini-flash deepseek-v4 llama3-8b gemma3-9b
```
- Opus 4.8 + Sonnet 5 answer cells + **all grading** are produced via Max (spawned Claude
  agents / the Claude app), not `grade.py`'s OpenRouter path — so they cost $0 in API terms.
- Their **cost is imputed** at list rates for the Pareto analysis; their **TTFT** is flagged as
  subscription-sourced (not directly comparable to API TTFT). Disclose in Limitations.
- The `--budget` guard halts *new* launches at 95% of the cap and drains in-flight calls, so
  final spend can exceed the cap only by ~(concurrency × per-cell cost) ≈ cents for these cheap
  models. Keep any expensive model off the OpenRouter path (or run it at `--concurrency 1`).
- Set real `rate_in`/`rate_out` in `models.py` first so the guard counts accurately.

## Design guarantees (from the Step-2 stress panel)
- **Contract is strictly last.** `assemble()` puts guidance in the *system* message and the
  question + `===FINAL===` contract in the *user* message, so the contract sits in the model's
  recency window. Course-pack fragments (if you add any) must go in the guidance region only.
- **Byte-invariance enforced in code.** `assemble()` asserts the GROUNDING block is present and
  hash-stable and the contract is the last thing in the prompt — a drifted cell fails fast
  instead of silently mis-grading.
- **Part labels templated per question** (`corpus.json` → `parts`), so a small model can't stop
  at part ב on a 4-part item. Same rendered labels across all models/levels for a given question.
- **Zero-shot vs RAG differ only by the passage.** Same system prompt, same params.

## Knobs
- `--levels L0 L1 L2`, `--arms zeroshot rag`, `--models <keys>` to run slices (e.g. the diagonal).
- `--max-tokens 4096` (raise if frontier reasoning models truncate; runner flags `truncated`).
- Temperature is fixed at 0 (reproducibility). For variance bars, duplicate the run with a
  different `--out` at a patched temperature and average — keep the headline at T=0.

## Logging schema (one JSONL row per cell)
`model, tier, level, arm, subject, qid, difficulty, prompt_tokens, completion_tokens,
ttft_ms, latency_ms, cost_usd, extraction_ok, truncated, finish_reason,
parts_expected, parts_returned, raw_output, error`

## Cost control
- Grade Accuracy for free where the answer is numeric (the fast-path); reserve Opus for
  Reasoning/Format + symbolic Accuracy. Adding structured per-part numeric keys to `corpus.json`
  pushes more parts onto the free path.
- `truncated` rows are prompt-length artifacts, not wrong answers — `analyze.py` reports
  `trunc_rate`; exclude them from Accuracy if they cluster on the small-model×L2 cells.
- See `../rag-benchmark-cost-estimate.md`: expect **~$100–260** for the full 20-question grid + grading.
