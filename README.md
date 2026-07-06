# Distilled Vertical Prompts for Efficient STEM Reasoning

**The real finding isn't cost — it's that for a bounded vertical you don't need a *closed* frontier
model at all.** On hard Hebrew (right-to-left) university STEM, open-weight models small enough to run
on a single machine **you control** matched a closed frontier model's accuracy — grounded with RAG and
a short, task-specific prompt — at up to **117× lower cost per correct answer**.

Independent research report by **Adam Shlomo**. *Not peer-reviewed. Not affiliated with any university
or model provider.* See the disclaimer below.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21209734.svg)](https://doi.org/10.5281/zenodo.21209734)

📄 Report: [`paper/distilled-vertical-prompts.pdf`](paper/distilled-vertical-prompts.pdf) · 🔁 Code: [`benchmark/`](benchmark/) · 📊 Data: [`corpus.json`](corpus.json) + grades in [`benchmark/`](benchmark/)

---

## TL;DR

People reach for a closed frontier model (GPT-5.5) on hard academic reasoning for one reason:
**reliability**. I tested whether an **open-weight, self-hostable** model — one you can run on a single
node you own, instead of renting through someone else's API — can match that reliability inside one
bounded vertical (first-year STEM). **It can.**

Three of the four models I tested run on hardware you control. The frontier one — the default choice
for hard reasoning — can't be self-hosted at all. Once accuracy is effectively tied, the deciding axis
stops being *capability* and becomes **deployability, control, and cost.**

## What I ruled out first

- **Long, frontier-style system prompts** — closer to a hyped headline than a technique. (I built my
  own prompts from scratch and never used or reconstructed any reported/leaked prompt.) Long prompts
  are expensive, fragile, and can drown a smaller model in instructions it doesn't need.
- **RAG alone** — necessary, not the answer. The real question wasn't "can the model answer with
  context?" but *which* models answer correctly and consistently **on infrastructure you control.**

## The actual unlock: deployability

| Model | Weights | Self-hostable? | Accuracy | Cost / correct answer |
|---|---|---|:--:|:--:|
| **GPT-5.5** | **Closed** | ❌ API-only (OpenAI) | ~0.99 | $0.084 |
| DeepSeek V4 Pro | Open (1.6T / 49B active) | ✅ single 8×H100 server¹ | ~0.99 | $0.0035 (~24× cheaper) |
| Llama 4 Maverick | Open (400B / 17B active) | ✅ single H100 DGX (FP8)² | 0.86 | — (below the floor) |
| **Gemma 4 31B** | **Open, dense 30.7B** | ✅ single consumer GPU (24 GB)³ | ~0.99 | **$0.00071 (~117× cheaper)** |

Deployment specs from vendors' own model cards: ¹ [DeepSeek V4 Pro](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro) ·
² [Llama 4 Maverick FP8](https://huggingface.co/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8) ·
³ [Gemma 4 31B](https://ai.google.dev/gemma/docs/core). *Three of four run on hardware you control — from a
$2k consumer card (Gemma) to a datacenter node (DeepSeek); the one that can't be self-hosted at all is the
one people default to.* For a bounded vertical, **RAG + a short vertical prompt let self-hostable open-weight
models close the gap to the closed frontier model** — and the cost collapse is a *consequence* of that.

## Deployability ≠ clearing the bar

Single-node deployability alone isn't enough: **Llama 4 Maverick is self-hostable but landed at ~0.86**,
clearly behind the other three. So the rule isn't "pick the smallest/cheapest self-hostable model" —
it's **"pick the cheapest, most deployable model that still clears your accuracy floor."** (That Llama
lags also shows the benchmark can still tell a genuinely weaker model apart.)

## The prompt that barely mattered

Going from a plain prompt to a carefully built short "distilled" prompt moved accuracy **≈ 0** (overall
mean **0.967**, median **1.000** — already near the ceiling, so little room to lift). It didn't *hurt*
either, which is the point: a short prompt gives structure without drowning a small model, where a
giant one adds noise. A good wrapper — not the main event.

## Method (one paragraph)

Five first-year STEM subjects (mechanics, electromagnetism, linear algebra, calculus, discrete math);
for each, an **original passage** I wrote containing every definition/theorem its questions need, plus
hard, multi-part questions checked against pre-written worked solutions. Every model saw the identical
prompt and answer contract; only the retrieved passage differed between zero-shot and RAG. **720 answers,
graded blind** (identities stripped) by an LLM rubric (validated by catching a planted error). Accuracy
is primary; the deployment metric is **cost per correct answer**. Total API cost of the run: **$16.50.**

## Repository layout

```
rag-tier-benchmark/
  paper/            report — distilled-vertical-prompts.pdf (with figures) + .docx source
  prompts/          L0_plain / L1_reasoning / L2_distilled_vertical (original text)
  corpus.json       full 20-question corpus (passages + questions + answer keys)
  corpus_run.json   the priced 15-question run subset
  benchmark/        code (runner, grader, analysis) + data (runs.jsonl, grades.jsonl, summary.csv)
  LICENSE  CITATION.cff  README.md
```

## Reproduce

```bash
export OPENROUTER_API_KEY=...
cd benchmark
python run_benchmark.py --corpus ../corpus_run.json --out runs.jsonl --budget 20
python grade.py         --runs runs.jsonl --out grades.jsonl
python analyze.py       --grades grades.jsonl
```

## How to cite

Archived on Zenodo — cite the DOI:

> Adam Shlomo (2026). *Distilled Vertical Prompts for Efficient STEM Reasoning: Cheap Models Match Frontier Accuracy on Hebrew RTL Problems at a Fraction of the Cost.* Zenodo. https://doi.org/10.5281/zenodo.21209734

## Limitations (read before over-generalizing)

The priced run used **15 questions** — treat the top three as effectively tied, not ranked. The
questions are answerable-from-source by design, creating a **ceiling effect**: this can't strongly rank
the strongest models against each other. Grading is by an LLM rubric (spot-validated, still model-based).
The corpus is original and controlled; real academic material is messier. Model versions, prices, and —
especially — open-weight deployment options change fast.

**Read this as:** *for a bounded academic reasoning task, capable open-weight models deployable on a
single machine got close to frontier accuracy at a small fraction of the cost* — not "small models beat
frontier everywhere."

---

> ### Disclaimer
> Independent research by **Adam Shlomo**, in a personal capacity. **Not peer-reviewed; not affiliated
> with, endorsed by, or reviewed by any university or model provider.** All passages and questions are
> **original works** by the author. Model and product names are trademarks of their respective owners,
> used nominatively for factual comparison. Deployment/hardware details are summarized from vendors' own
> model cards and may change. Cost figures are estimates for this experiment's setup, not provider
> quotes. **Disclosure:** the author is the solo builder of **StudAI**, a study-assistant product that
> this research directly informs. **License:** report & data CC BY 4.0; code MIT.
