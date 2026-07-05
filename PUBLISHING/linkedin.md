# LinkedIn post (primary)

For a while I had a recurring problem that was really a dependency problem in disguise.

Whenever I needed AI to reliably solve hard STEM — calculus, physics, linear algebra, discrete math — the answer was always "use a closed frontier model." Not because I wanted to, but because it was the only tier that got things right often enough.

But defaulting to a closed model has a hidden cost beyond the bill: your reasoning engine lives on someone else's servers, priced and rate-limited by them, and every prompt you send is a data-exposure event.

So I tested a narrower, more useful question: can an open-weight model — small enough to run on a single machine I control — be pushed to match frontier accuracy inside one bounded vertical?

I built a Hebrew STEM benchmark: 5 subjects, 8 models, 3 prompt styles, zero-shot vs RAG, 720 blind-graded answers, $16.50 total.

The number people will quote is cost: a self-hostable open model matched frontier accuracy at ~117× lower cost per correct answer.

But the real finding is deployability. 3 of the 4 models I tested run on hardware you own. The frontier one — the default choice for hard reasoning — can't be self-hosted at all.

And it's not "cheap always wins": one open model (Llama 4 Maverick) was clearly weaker (~0.86). The rule is the cheapest, most deployable model that still clears your accuracy floor.

The prompt engineering I expected to be the hero barely moved accuracy — the models were already near the ceiling. The unlock was the combination: retrieval grounding + a short vertical-specific prompt, running on a model you actually own.

For a bounded vertical, you may not need to rent the frontier at all.

Full independent report, data, code, and DOI in the comments.

#AI #LLM #OpenSource #MachineLearning #EdTech

---

# LinkedIn post (shorter / hook variant)

Everyone's asking which AI model is smartest.

For my product I asked a different question: which model can I run without depending on one I don't own?

I built a Hebrew STEM benchmark — 8 models, 720 blind-graded answers, $16.50.

Accuracy came out basically tied at the top. But 3 of the 4 models are open-weight and self-hostable on a single machine; the frontier one is API-only. A self-hostable open model matched frontier accuracy at ~117× lower cost per correct answer.

The clever prompt I engineered? Barely moved the needle — the models were already near ceiling.

The takeaway: for a bounded vertical, the real question isn't "how smart" — it's "can I run this myself, and does it clear my accuracy floor?"

Full report + data + code + DOI in comments.

---

## Posting notes
- Put the links in the FIRST COMMENT, not the post body (LinkedIn suppresses reach on posts with outbound links). End the post with "links in comments."
- First-comment text: `Full report, data, code: https://github.com/adam-shlomo/rag-tier-benchmark · Archived (DOI): https://doi.org/10.5281/zenodo.21209734`
- Optional carousel (5–6 slides) from the report figures: (1) the dependency problem, (2) the deployability table (open vs closed / self-hostable), (3) "prompt ≈ 0 lift", (4) cost per correct (117×), (5) "cheapest model that clears your floor", (6) links.
- Lead identity: *independent builder publishing reproducible research*, not academic.
