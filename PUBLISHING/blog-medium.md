# I Tested 8 AI Models on Hebrew STEM Problems. The Cheapest Good Model Was 117× Cheaper per Correct Answer.

*An independent research report. Full data, code, and the technical write-up are linked at the bottom.*

---

There's a popular bet in AI right now: take a cheap model, hand it a long, frontier-style system
prompt, and it'll start behaving like a frontier model.

I wanted to test a more practical version of that bet — for one specific job. I build a study
assistant for STEM students, and most of that studying happens in **Hebrew**, a right-to-left language
where the model has to juggle Hebrew prose *and* left-to-right math in the same line. Almost every
public LLM benchmark is in English. So I ran my own.

## The question

**Do Hebrew STEM students actually need frontier AI models — or is a cheaper model already good enough?**

And a second one I cared about as a builder: does a **short, task-specific "distilled" prompt** — the
*juice* of a big frontier prompt (the reasoning discipline and the list of common mistakes to avoid),
without the bulk — actually help a small model?

## What I built

A small but careful benchmark:

- **5 first-year STEM subjects** — mechanics, electromagnetism, linear algebra, calculus, discrete math.
- For each, an **original Hebrew passage** I wrote that contains every definition and theorem its
  questions need (so the answer is always derivable from the text — no hidden knowledge required).
- **Hard, multi-part questions**, each independently solved and checked against a worked answer key.
- **8 models** across three price tiers, from frontier down to small open models.
- **3 prompt styles** (plain → verbose reasoning → a concise "distilled vertical" prompt).
- **Two modes:** zero-shot (no passage) and RAG (passage supplied).

That's **720 model answers**, all graded **blind** (the grader never sees which model wrote what) on a
fixed rubric. Total API cost to run the whole thing: **$16.50**.

## The surprising result

**The prompt barely mattered.**

Going from a plain prompt to my carefully-built "distilled" prompt moved accuracy by **about zero**
(within noise). Why? Because on these problems the models were already **near the ceiling** — mean
accuracy **0.967**, median a perfect **1.000**. There wasn't much room to lift.

Importantly, the concise prompt didn't *hurt* either. That's the quiet win: a huge prompt can actually
*degrade* a small model by drowning it in irrelevant instructions. A short, focused one doesn't.

## The real result: cost, not smarts

If accuracy is basically tied, the deciding factor becomes **cost per correct answer**. And there the
gap is enormous:

| Model (tier) | Accuracy | Cost per correct answer |
|---|:--:|:--:|
| GPT-5.5 (frontier) | ~0.99 | **$0.084** |
| DeepSeek V4 Pro (cheap) | 0.99 | **$0.0035** (~24× cheaper) |
| **Gemma 4 31B (cheap, open)** | **0.99** | **$0.00071** (~117× cheaper) |
| Llama 4 Maverick (cheap) | 0.86 | — (the one real floor) |

A **31-billion-parameter open model matched the frontier's accuracy at roughly one-hundredth of the
cost per correct answer.** One model (Llama 4 Maverick) was clearly weaker — proof the benchmark can
still tell good from bad — but the rest clustered at the top.

## What this means for builders

For a **bounded** task like STEM tutoring, the right question isn't *"what's the smartest model?"* It's:

> **"What's the cheapest model that clears the accuracy floor for *this specific* vertical?"**

So: **benchmark your vertical.** You may be paying 100× for accuracy you already had. The distilled
prompt still earns its place — it packages the right reasoning discipline cleanly — but treat it as a
safe deployment default, not a magic accuracy lever.

## Honest limitations

I'm publishing this as an **independent research report, not a peer-reviewed paper**, and I want to be
straight about what it does and doesn't show:

- **Ceiling effect.** These questions are answerable-from-source and the models are strong, so nearly
  all of them ace it. That means the benchmark **can't rank the very top models** — it needs harder,
  more adversarial questions to do that. This is the biggest caveat.
- **Small sample.** 15 priced questions. Treat the top models as effectively tied.
- **LLM judge.** Grading is by a model rubric (validated by catching a planted error, but still a model).
- **Synthetic corpus.** I wrote the passages; they're realistic but not drawn from any real course.
- **One config, one point in time.** Prices and model versions change.

## Links

- **Full report + data + code (GitHub):** https://github.com/adam-shlomo/rag-tier-benchmark
- **Archived version (DOI):** https://doi.org/10.5281/zenodo.21209734

*Independent research by Adam Shlomo, in a personal capacity — not affiliated with, endorsed by, or
reviewed by any university or model provider. All passages and questions are original works by the
author. Model and product names are trademarks of their respective owners, used here nominatively for
factual comparison. Nothing here is professional advice; cost figures are estimates, not quotes.
Disclosure: I build StudAI, a study-assistant product informed by this work.*
