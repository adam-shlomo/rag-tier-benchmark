# I Tested 8 AI Models on Multi-Part STEM Problems. The Real Finding Wasn't Cost — It Was That You Don't Need a Closed Frontier Model At All.

*Independent research report. Full data, code, and the technical write-up are linked at the bottom.*

---

For a while, I had a recurring problem that was really a dependency problem in disguise.

Whenever I needed an AI system to reliably solve calculus, physics, linear algebra, or discrete math problems, I kept landing on the same answer: use a closed-weight frontier model. Not because I preferred it, but because it was the only tier that got things right often enough — and even then, not always.

With cheaper models, the workflow usually looked like this: ask the question, get a shaky answer, correct the model, correct it again, maybe end up with something usable. At that point "cheap" stops being cheap. The real cost is retries, manual checking, and not trusting the output.

But there's a second cost to always reaching for a closed frontier model that's easy to miss: it means the reasoning engine behind anything you build sits entirely on someone else's infrastructure, priced and rate-limited by someone else, with no way to run it yourself — and every prompt you send is also a data exposure event, since that data now lives on the model provider's servers instead of yours.

So I set out to test something narrower and more useful than "which model is smartest":

**Can an open-weight model — small enough to deploy on a single machine you control, rather than a closed model reachable only through someone else's API — be pushed far enough to match frontier accuracy inside one specific, bounded academic vertical?**

## What I Ruled Out First

The first approach I tried was long, frontier-style system prompts — the idea that if you hand a smaller model a huge, detailed prompt (inspired by the general shape of the large system prompts that have been reported, though to be clear I built my own from scratch and never used or reconstructed any leaked prompt), it starts behaving like a much stronger model. I tested this directly. It turned out to be closer to a hyped-up headline than a real technique: long prompts are expensive, fragile, and can drown a smaller model in instructions it doesn't need.

The second approach was retrieval — giving the model the source material it needs instead of asking it to know everything. That part is reasonable on its own, but RAG alone doesn't answer the real question, because I wasn't just asking "can the model answer with context?" I was asking which models can answer correctly, consistently, and on infrastructure that doesn't require a closed frontier model. That's a different question, so I built a benchmark.

## What I Actually Tested

I built a small, careful STEM benchmark covering five first-year subjects: mechanics, electromagnetism, linear algebra, calculus, and discrete math.

For each subject, I wrote an original passage containing every definition, formula, and theorem needed to answer the questions, then wrote hard, multi-part questions against those passages and graded them against pre-written worked solutions.

The setup covered:

- 8 different models
- 3 prompt styles
- 2 modes: zero-shot and RAG
- 15 priced questions across the five subjects
- 720 total model answers

All answers were graded blind — the grader didn't know which model produced which answer. Total API cost for the full run: **$16.50**.

## The Prompt That Barely Mattered

I had one specific idea I wanted to test: could I compress the useful parts of a long reasoning prompt into a short, task-specific checklist instead — the discipline that prevents careless mistakes (identify what's given, solve symbolically before plugging in numbers, check units, watch for sign errors and missing factors, check edge cases, don't skip the final answer) without the bulk of a massive prompt?

The result: the prompt barely moved the needle. Going from a plain prompt to the carefully built short prompt changed accuracy very little, even for smaller models. Overall accuracy across the run was already high — **mean 0.967, median 1.000** — which meant there wasn't much room left for any prompt to improve things.

That doesn't mean the short prompt was pointless. It didn't hurt performance, which matters more than it sounds: a giant prompt can add noise and pull a smaller model's attention toward the wrong things, while a short one gives structure without drowning the answer. It was a good wrapper — just not the main event.

## The Real Finding: Deployability, Not Just Cost

Once accuracy is close to tied, the more useful question isn't "which model is smartest" — it's "which of these models can I actually run without depending on a closed model I don't control?"

Here's where the four models tested actually sit:

- **GPT-5.5** — closed-weight. Available only through OpenAI's API. Cannot be self-hosted at any scale, on any number of machines.
- **DeepSeek V4 Pro** — open-weight (MIT), 1.6T total / 49B active parameters. Self-hostable on a single **8× H100 server** — a datacenter-class node, but one you can own and run air-gapped, not an API you rent. (DeepSeek also ships a smaller V4-Flash that fits on a single 80 GB GPU.)
- **Llama 4 Maverick** — open-weight, 400B total / 17B active parameters. Meta's own model card states the **FP8 weights fit on a single H100 DGX host**.
- **Gemma 4 31B** — open-weight (Apache 2.0), dense 30.7B, built for **consumer GPUs** — it runs on a single 24 GB card like an RTX 4090. The most single-node-friendly of the four.

Three of the four models tested can run entirely on hardware you control — from a consumer GPU (Gemma) to a single datacenter server (DeepSeek) — with no dependency on a hyperscale provider. The fourth — the one usually treated as the default choice for hard academic reasoning — can't be deployed that way at all.

That's the actual unlock in this data: for a bounded vertical like STEM reasoning, retrieval grounding plus a short, domain-specific prompt let self-hostable, open-weight models close the gap to a closed-weight frontier model. The cost collapse below is a consequence of that, not the headline by itself.

## Cost Is the Downstream Effect

Here are the per-model numbers:

- **GPT-5.5** — accuracy ≈ 0.99, cost per correct answer: **$0.084**
- **DeepSeek V4 Pro** — accuracy ≈ 0.99, cost per correct answer: **$0.0035** (about 24× cheaper than GPT-5.5)
- **Gemma 4 31B** — accuracy ≈ 0.99, cost per correct answer: **$0.00071** (about 117× cheaper than GPT-5.5)

A gap that size isn't a rounding error in an API bill. It's the difference between "expensive at scale" and "actually viable to build a product on" — and it exists specifically because the cheaper models aren't paying frontier-provider margins or running on infrastructure priced for hyperscale serving.

## Not Every Small Model Clears the Bar

One important caveat: single-node deployability alone isn't sufficient. Llama 4 Maverick — itself an open-weight, single-node-capable model — landed around 0.86 accuracy, clearly behind the other three. That's useful information in its own right: it means this benchmark can still tell a genuinely weaker model apart from the pack, rather than being too easy to discriminate anything.

So the lesson isn't "always pick the smallest, cheapest, most self-hostable model." It's: find the cheapest, most deployable model that still clears your accuracy floor — because deployability alone doesn't guarantee that.

## Why This Extends Beyond One Benchmark

This isn't just a benchmarking curiosity. On CNBC's *Squawk Box* on July 1, 2026, Palantir CEO Alex Karp argued that AI companies are imposing a "wealth tax" on businesses — charging heavily for tokens while harvesting the proprietary data those businesses feed in, using it to improve the labs' own models ([CNBC](https://www.cnbc.com/2026/07/01/palantir-karp-open-ai-anthropic-tokens.html)).

Karp was talking about large enterprises, not specifically about smaller products built as thin layers on top of frontier APIs — but the underlying concern is the same one that's been circulating in startup and VC circles for a while: if a product's entire value sits on a closed model you don't own, the company that owns that model has both visibility into your usage and the incentive to eventually build your differentiating feature directly into the base model. A moat built entirely on a rented, closed foundation isn't a moat you actually control.

That's the same argument this benchmark supports, at a much smaller scale. For a specific, well-defined vertical, an open-weight model plus retrieval grounding plus a short domain-specific prompt can close most of the gap to a closed frontier model — without handing your data, your prompts, or your product's differentiation to whichever lab is ahead this particular quarter. My own view, based on this data but not proven by it alone, is that the durable long-term position for vertical AI products isn't defaulting to the biggest general-purpose model available — it's a smaller, task-specific, vertical-optimized model you actually own.

## The Takeaway

For a bounded academic reasoning task, the biggest lever wasn't prompt size, and it wasn't RAG by itself. It was combining the two — retrieval grounding plus a short, vertical-specific prompt — on top of an open-weight model you can actually run yourself, instead of defaulting to a closed frontier model because that's the tier everyone assumes you need.

The working pattern:

- Build a benchmark for the actual task, not a generic one
- Test across model tiers, including ones you could self-host
- Ground answers in source material where it matters
- Use a short, task-specific prompt instead of a massive one
- Measure correctness and cost per correct answer together
- Pick the cheapest, most deployable model that still clears your reliability floor

## Honest Limitations

This is independent research, not a peer-reviewed paper, and a few things matter for how much weight to put on it:

- The priced run used 15 questions, so close differences between the top three models should be read as effectively tied, not ranked.
- The questions were designed to be answerable from the supplied material, which creates a ceiling effect. That was partly the point, but it also means this benchmark can't strongly rank the strongest models against each other.
- Grading was done with an LLM rubric. I validated it with spot checks, but it's still model-based grading.
- The corpus was original and controlled. Real-world academic material — inconsistent formatting, ambiguous phrasing, incomplete context — is messier than this.
- Model versions and prices change quickly, and open-weight model deployment options are the fastest-changing part of this data.

I'd read this as: for a bounded academic reasoning task, capable open-weight models that can be deployed on a single machine got close to frontier accuracy at a small fraction of the cost — not as "small models beat frontier models everywhere."

## Disclosure

I'm the solo builder of StudAI, a study assistant for university students. This research directly informed decisions I'm making for that product, which is part of why I cared about testing deployability and not just accuracy.

## Sources (deployment specs + quotes)

- DeepSeek V4 Pro — [Hugging Face model card](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro) (1.6T/49B active, MIT)
- Llama 4 Maverick — [Meta model card](https://github.com/meta-llama/llama-models/blob/main/models/llama4/MODEL_CARD.md) · [FP8 weights on Hugging Face](https://huggingface.co/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8) ("fits on a single H100 DGX host")
- Gemma 4 31B — [Google AI docs](https://ai.google.dev/gemma/docs/core) · [model card](https://huggingface.co/google/gemma-4-31B) (30.7B dense, Apache 2.0, consumer-GPU)
- Alex Karp "wealth tax" — [CNBC, July 1 2026](https://www.cnbc.com/2026/07/01/palantir-karp-open-ai-anthropic-tokens.html)

## Links

- **Full report, data, and code:** https://github.com/adam-shlomo/rag-tier-benchmark
- **Archived version (DOI):** https://doi.org/10.5281/zenodo.21209734

*Independent research by Adam Shlomo, in a personal capacity. Not peer-reviewed. Not affiliated with, endorsed by, or reviewed by any university or model provider. All passages and questions are original works by the author. Model and product names are trademarks of their respective owners, used here for factual comparison. Deployment and hardware details are summarized from vendors' own model cards and may change. Cost figures are based on this experiment's setup and shouldn't be treated as provider quotes.*
