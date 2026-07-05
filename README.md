# Distilled Vertical Prompts for Efficient STEM Reasoning

**Cheap models match frontier accuracy on Hebrew RTL STEM problems — at a fraction of the cost.**

An **independent technical research report** and fully reproducible benchmark by **Adam Shlomo**.
*Not peer-reviewed. Not affiliated with any university or model provider.* See the disclaimer below.

📄 Report: [`paper/distilled-vertical-prompts.pdf`](paper/distilled-vertical-prompts.pdf) (with figures) · [editable source (.docx)](paper/distilled-vertical-prompts.docx) · 🔁 Code: [`benchmark/`](benchmark/) · 📊 Data: [`corpus.json`](corpus.json) + grades in [`benchmark/`](benchmark/)
<!-- After Zenodo: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX) -->

---

## TL;DR

I tested whether **cheap models can match frontier models** on hard, Hebrew (right-to-left) university
STEM problems, and whether a **short "distilled vertical" system prompt** — the *juice* of a long
frontier-style prompt (reasoning discipline + a common-error "don'ts" checklist), without the mass —
helps. Setup: **8 models × 3 prompt levels × {zero-shot, RAG} × 15 questions = 720 blind-graded cells**,
temperature 0, total metered cost **$16.50**.

**Two findings:**
1. **The prompt barely mattered.** Accuracy is near-ceiling (mean **0.967**, median **1.000**); prompt
   lift from plain → distilled-vertical is **≈ 0**. The concise prompt didn't *hurt* either — it avoids
   the "over-squeezing" that a huge prompt can cause on small models.
2. **Cost was the whole story.** A Tier-3 open model (**Gemma 4 31B**) reaches the frontier accuracy
   ceiling at **$0.00071 per correct answer — ~117× cheaper than GPT-5.5**. DeepSeek V4 Pro matches
   frontier at ~24× cheaper. Llama 4 Maverick (0.861) is the one clear capability floor.

**Takeaway for builders:** for bounded STEM tutoring, the question isn't "what's the smartest model?"
It's **"what's the cheapest model that clears the accuracy floor for *this* vertical?"** — so benchmark
your vertical.

## Method (one paragraph)

Each of five first-year STEM subjects (mechanics, electromagnetism, linear algebra, calculus, discrete
math) has an **original, self-contained Hebrew passage** stating every definition/theorem its questions
need, plus hard multi-part questions **independently re-solved and adjudicated**. Every model sees the
identical prompt and output contract; only the retrieved passage differs between zero-shot and RAG.
Outputs are graded **blind** (identities stripped) by an LLM rubric (Accuracy/Reasoning/Format per
part; equivalent forms accepted), which was validated by catching a planted error. Accuracy is the
primary metric; the headline is **cost per correct answer**.

## Repository layout

```
rag-tier-benchmark/
  paper/            report — distilled-vertical-prompts.pdf (with figures) + .docx source
  prompts/          L0_plain / L1_reasoning / L2_distilled_vertical (original text)
  corpus.json       full 20-question corpus (passages + questions + answer keys)
  corpus_run.json   the priced 15-question run subset
  benchmark/        code (runner, grader, analysis) + data (runs.jsonl, grades.jsonl, summary.csv)
  PUBLISHING/       blog + LinkedIn drafts
  LICENSE  CITATION.cff  README.md
```

## Reproduce

```bash
export OPENROUTER_API_KEY=...
cd benchmark
python run_benchmark.py --corpus ../corpus_run.json --out runs.jsonl --budget 20
python grade.py         --runs runs.jsonl --out grades.jsonl     # blind rubric
python analyze.py       --grades grades.jsonl                    # cost/correct, Pareto, deltas
```

## How to cite

See [`CITATION.cff`](CITATION.cff). Once archived on Zenodo, cite the DOI.

## Limitations (read before over-generalizing)

Near-ceiling accuracy means this corpus **can't separate the top tier** — a finding *and* a limitation;
harder/adversarial items are needed to rank frontier models. Also: n = 15 priced questions (treat top
models as tied); an LLM judge; synthetic (author-written) corpus; Anthropic models run via a
subscription endpoint (cost **imputed**, latency not endpoint-comparable). Details in the report.

---

> ### Disclaimer
> Independent research by **Adam Shlomo**, in a personal capacity. **Not peer-reviewed; not affiliated
> with, endorsed by, or reviewed by any university or model provider.** All passages and questions are
> **original works** by the author, not reproduced from any institution's materials. Model outputs were
> obtained via public APIs (OpenRouter) and a subscription endpoint at a point in time; versions and
> prices change. **Trademarks** (GPT, Gemini, Claude, Llama, Gemma, DeepSeek, etc.) belong to their
> owners and are used nominatively for factual comparison, without implying affiliation or endorsement.
> Nothing here is professional advice; figures are estimates, not quotes; provided "as is" without
> warranty. **Disclosure:** the author builds StudAI, a study-assistant product informed by this work.
> **License:** report/data CC BY 4.0; code MIT.
