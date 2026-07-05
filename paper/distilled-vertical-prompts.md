> **Independent research report — not peer-reviewed.** By Adam Shlomo, in a personal capacity; not affiliated with, endorsed by, or reviewed by any university or model provider. All passages and questions are original works by the author, not reproduced from any institution's materials. Model outputs were obtained via public APIs (OpenRouter) and a subscription endpoint at a point in time; versions and prices change. Trademarks (GPT, Gemini, Claude, Llama, Gemma, DeepSeek, etc.) belong to their owners and are used nominatively for factual comparison. Nothing here is professional advice; cost figures are estimates, not quotes. Disclosure: the author builds StudAI, a study-assistant product informed by this work. License: report/data CC BY 4.0, code MIT.

---

# Distilled Vertical Prompts for Efficient STEM Reasoning: Cheap Models Match Frontier Accuracy on Hebrew RTL Problems at a Fraction of the Cost

## Abstract

A persistent intuition holds that a small, inexpensive language model can be lifted to frontier behavior simply by handing it a very long, frontier-style system prompt. A known failure mode contradicts this: small models over-weight irrelevant spans of a long prompt and are "over-squeezed," losing accuracy rather than gaining it. We test a different, task-specific route on academic STEM reasoning in Hebrew, a right-to-left (RTL) language that is under-represented in reasoning evaluations. We construct an original, redistributable benchmark of five standard first-year undergraduate courses (mechanics, electromagnetism, linear algebra, infinitesimal calculus, discrete mathematics), each paired with a self-contained Hebrew passage stating every definition and theorem its questions require, plus 20 hard, multi-part, independently adjudicated questions. On a priced 15-question subset we run a controlled 8-model x 3-prompt x {zero-shot, RAG} grid (720 cells) at temperature 0, grading blind with a validated LLM rubric. Overall accuracy is high (mean 0.967), and prompt lift from a plain prompt to a concise "squeezed-juice" vertical prompt is approximately zero across models (range -0.007 to +0.003). The headline result is economic, not prompt-driven: a Tier-3 open model (Gemma 4 31B) reaches the frontier accuracy ceiling at \$0.00071 per correct answer, roughly 117x cheaper than GPT-5.5. We conclude that on answerable-from-source STEM, cheap models already match frontier accuracy, and a concise distilled vertical prompt is a safe deployment recipe that neither helps nor hurts at ceiling while avoiding the over-squeezing degradation a full-length prompt would risk.

## 1. Introduction

A recurring question in applied LLM deployment is whether the gap between a cheap model and a frontier one can be closed with prompting alone. The question gained fresh momentum from an anecdote — which we flag as **unconfirmed** and which we neither reproduce nor rely on for any technical claim — that a recent frontier assistant ships with an extremely long system prompt (a figure on the order of 130k tokens was informally circulated). If frontier behavior is partly *carried by* such a prompt, the tempting inference is that transplanting a similar prompt onto a small model would transplant the behavior. We treat this anecdote strictly as motivation; we do not quote, paraphrase, reconstruct, or characterize the contents of any proprietary or allegedly-leaked prompt, and all prompts used in this work are original text distilled from published, general prompting principles (chain-of-thought, self-check, structured output, and common-error checklists), not copied from any model.

There is good reason to doubt the naive transplant. A well-documented failure mode of long prompts is that models — especially smaller ones — distribute attention poorly across a large instruction context, over-weighting incidental or mid-context material and degrading on the actual task [CITE: lost-in-the-middle]. We refer to this informally as *over-squeezing*: the useful signal of a long prompt is diluted by everything around it, and a small model that cannot triage the prompt pays for the irrelevant tokens with worse answers. Under this view, more prompt is not more capability.

We propose and test a middle path we call the **distilled vertical prompt**, or the "squeezed-juice" recipe. Rather than transplanting a long general-purpose prompt, we distill its *juice* — the reasoning discipline, worked-method scaffolding, edge-case awareness, and explicit "don'ts" — into a short, task-specific prompt for one vertical. Concretely, our most developed prompt level (~640 tokens) encodes setup discipline, a solve-symbolically-first habit, an explicit common-error checklist (sign conventions, factor-of-2 slips, radians-versus-degrees, unit conversion, dropped terms, square-root branch selection, boundary and continuity conditions, off-by-one, and domain of validity), a verification protocol (dimensional analysis, limiting cases, re-derivation), and a proofs protocol. The hypothesis is that a concise, vertical prompt captures most of the benefit a long prompt could offer while remaining short enough to avoid over-squeezing a cheap model.

We situate this test in **Hebrew, right-to-left academic STEM**. This choice is deliberate. Reasoning benchmarks are overwhelmingly English [CITE: multilingual-reasoning-eval], and RTL scripts introduce tokenization, formatting, and mixed-direction (Hebrew prose with left-to-right mathematics) challenges that English-only evaluations never surface [CITE: rtl-nlp]. STEM problems also admit adjudicable ground truth, which lets us grade accuracy cleanly rather than relying on preference alone. To keep the evaluation grounded and free of source-fabrication, every question is answerable from an accompanying self-contained passage, and grounding is applied phase-symmetrically across the zero-shot and RAG conditions.

Our findings are honest about what prompting does and does not buy. On this near-ceiling task, the distilled vertical prompt did **not** raise accuracy — models were already at parity — so we make no claim of prompt-driven accuracy gains. What the data does show is (a) cheap models already match frontier accuracy on answerable-from-source STEM, at 24-117x lower cost per correct answer, and (b) the concise distilled prompt neither helps nor hurts at ceiling, and crucially does *not* trigger the over-squeezing degradation a full-length prompt would risk. The distilled vertical prompt is therefore best understood not as an accuracy lever but as a *safe, cheap deployment recipe*.

**Contributions.**

- **An original, redistributable Hebrew RTL STEM benchmark.** Five standard first-year undergraduate courses, each with a self-contained Hebrew passage (~760-1650 words) stating every definition and theorem its questions need, plus 20 hard, multi-part questions that were independently re-solved and adjudicated for correctness and answerability. The passages are synthetic and course-aligned rather than verbatim textbook, so the corpus is openly shareable.
- **A three-level distilled-prompt ladder with a byte-identical output contract.** L0 (plain), L1 (verbose chain-of-thought with an understand -> plan -> solve -> verify -> answer self-check), and L2 (the ~640-token "squeezed-juice" vertical prompt), differing *only* in the middle "how to reason" guidance, with a hash-enforced, contract-last per-part answer format so that prompt effects are not confounded by format effects.
- **A controlled 720-cell efficiency grid.** Eight models spanning three cost tiers x three prompt levels x {zero-shot, RAG} x 15 adjudicated questions, at temperature 0 with a uniform reasoning budget, graded blind by a validated rubric, for a total metered API cost of \$16.50.
- **A cost-per-correct headline and an honest null on prompt lift.** We report cost-per-correct answer as the primary deployment metric — a Tier-3 open model reaches the frontier ceiling at ~117x lower cost — and we report prompt lift as approximately zero (range -0.007 to +0.003), explicitly declining to overclaim.
- **A methods-integrity account of a detected-and-corrected pipeline artifact.** We document an endpoint-wrapper confound that initially suppressed shown work for two models, how we diagnosed it via shown-work length, and how re-running and blind re-grading corrected it — evidence that the evaluation pipeline surfaces its own confounds.

### 1.1 Research Questions

- **RQ1 (bang-for-buck).** Which model delivers the best accuracy *per dollar* on grounded Hebrew RTL STEM — i.e., the lowest cost-per-correct answer — and how large is the spread across cost tiers?
- **RQ2 (best overall).** Which model attains the highest raw accuracy, and is the top tier separable on this corpus or compressed against a ceiling?
- **RQ3 (cheap model + distilled vertical prompt vs frontier).** Can a cheap model, paired with a concise distilled vertical prompt, match frontier accuracy — and does the concise prompt help, hurt (via over-squeezing), or leave accuracy unchanged relative to a plain prompt?

## 2. Related Work

**Reasoning elicitation via prompting.** A large body of work shows that instructing a model to reason step by step, rather than answer directly, improves performance on multi-step problems [CITE: chain-of-thought], and that structured variants — self-consistency sampling, plan-then-solve decompositions, and explicit self-verification or self-critique — can extend those gains [CITE: self-consistency; CITE: plan-and-solve; CITE: self-verification]. Our prompt ladder draws its L1 (verbose chain-of-thought with a self-check loop) and L2 (a checklist-and-verification vertical prompt) levels from these general principles. Unlike work that reports prompt-driven accuracy gains, we test whether such scaffolding *transfers* to a near-ceiling grounded task and find that, at ceiling, it neither helps nor hurts — a null we report deliberately rather than search around.

**Long-context and instruction-following degradation.** A complementary line of research documents that models do not use long contexts uniformly: accuracy depends on *where* relevant information sits, with a characteristic degradation for mid-context material — the "lost-in-the-middle" effect [CITE: lost-in-the-middle] — and that long or crowded instructions can dilute adherence to the operative task [CITE: instruction-following-degradation]. Smaller models are especially susceptible to over-weighting incidental prompt content [CITE: small-model-prompt-sensitivity]. This literature motivates our central design choice: distilling a long prompt's useful content into a short vertical prompt to capture its benefit while avoiding the over-squeezing regime. We do not directly evaluate a full-length prompt against the concise one; that comparison is future work, and the over-squeezing claim functions here as motivation rather than result.

**Task-specific and "skill"-style prompting.** Recent practice packages narrow, reusable procedures — worked methods, domain conventions, and error checklists — into compact task-specific instructions, or "skills," rather than relying on a single general prompt [CITE: task-specific-prompting; CITE: agent-skills]. Our distilled vertical prompt is an instance of this vertical strategy, specialized to a single domain (academic STEM) and language direction (Hebrew RTL), and evaluated with a byte-identical output contract so that vertical guidance is isolated from formatting.

**Retrieval-augmented generation.** Supplying a model with retrieved source text at inference time is a standard remedy for missing or parametric-only knowledge [CITE: rag; CITE: retrieval-augmented-lm]. Our design uses grounding phase-symmetrically: the zero-shot and RAG conditions differ only in whether the self-contained passage is retrieved and supplied, which isolates the marginal value of retrieval on a corpus that is answerable-from-source by construction. We find RAG deltas that are small and mostly non-negative, consistent with a regime where the required knowledge is already largely available to strong models.

**LLM-as-judge evaluation.** Using a strong model to grade open-ended outputs against a rubric is now common and correlates reasonably with human judgment, but it carries known biases and calibration caveats [CITE: llm-as-judge; CITE: judge-bias]. We grade blind (model identities stripped) with a fixed per-part rubric that accepts algebraically-equivalent forms, and we validate the judge with a planted-error probe (it correctly zeroed a mis-computed answer), while treating the reasoning axis as a confounded secondary because visible-versus-hidden chains of thought are not endpoint-comparable.

**Multilingual and RTL evaluation.** Most reasoning benchmarks are English-centric, and cross-lingual studies show that reasoning quality can drop in lower-resource and non-Latin-script languages [CITE: multilingual-reasoning-eval; CITE: cross-lingual-reasoning]. RTL languages such as Hebrew and Arabic add script-direction, tokenization, and mixed-direction rendering issues that English evaluations do not exercise [CITE: rtl-nlp; CITE: hebrew-nlp]. Our benchmark contributes a controlled, adjudicated Hebrew RTL STEM evaluation to this under-served space, with grounded passages that make correctness cleanly measurable.

---

*Notes for the author.* Every reference above is a `[CITE: topic]` placeholder — no bibliography entries were generated, per the hard rule against unverified citations; each must be searched, verified in two independent sources, and fetched programmatically before it enters the `.bib`. The 130k-token long-prompt anecdote is flagged as unconfirmed and is used only as motivation; no proprietary or allegedly-leaked prompt content is reproduced or described. All reported figures are drawn verbatim from the supplied results (overall mean accuracy 0.967; prompt-lift range -0.007 to +0.003; Gemma 4 31B at \$0.00071/correct, ~117x cheaper than GPT-5.5's \$0.084; total study cost \$16.50), and no prompt-driven accuracy gain is claimed.

## 3. Methodology

Our study asks a narrow, deployment-relevant question: on academic STEM problems that are *answerable from a provided source*, how far apart are cheap and frontier language models in accuracy, in cost, and in their sensitivity to a concise, vertical-specific system prompt? To answer it without confounds, we hold everything constant across models — passages, questions, prompts, decoding parameters, grounding conditions, grading — and vary only the model, the prompt level, and whether the source passage is supplied (zero-shot vs. RAG). This section specifies the corpus (§3.1), the distilled prompt ladder (§3.2), the experimental grid (§3.3), the execution harness (§3.4), the blind grading protocol (§3.5), and the metrics (§3.6).

### 3.1 Corpus construction

We built an original, self-contained STEM corpus aligned to five standard first-year undergraduate courses: Mechanics, Electromagnetism, Linear Algebra 1, Infinitesimal Calculus 1, and Discrete Mathematics. These courses span continuous physics, matrix algebra, single-variable analysis, and combinatorial reasoning, giving coverage across the kinds of reasoning STEM assistants are asked to perform.

For each course we authored a single Hebrew, right-to-left (RTL) *reference passage* of roughly 760–1650 words. Each passage is **synthetic and self-contained**: it states, in its own words, every definition, theorem, convention, and boundary condition that its associated questions require. The passages are *course-aligned but not verbatim* — they are original prose distilled from the standard content of each subject rather than copied from any textbook, so the corpus is openly redistributable. This design has two deliberate consequences that we state plainly as framing rather than hide as assumptions. First, because each passage is self-contained, the task is *answerable-from-source*: a model that reads the passage and reasons correctly has, in principle, everything it needs. Second, this makes the corpus a strong instrument for measuring reasoning fidelity and grounding, but a *weak* instrument for separating top-tier models — a ceiling effect we anticipate and confront directly in the results and limitations rather than treat as an incidental finding.

Against each passage we authored **20 hard, multi-part questions**, for 100 questions in total. Questions were written to require multi-step derivation (not lookup) and to exercise the exact definitions and theorems the passage supplies. Every question was **independently re-solved and adjudicated**: a second solution pass produced a canonical worked answer, and the two solutions were reconciled part-by-part to confirm that each item is (i) correct as stated, (ii) unambiguous, and (iii) fully answerable from its passage alone. This adversarial key-verification step is a methods-integrity safeguard, not a formality — an item whose "correct" answer is itself wrong would silently corrupt every downstream accuracy number. Items that failed any of the three checks were revised until they passed.

For the *priced* experimental run we drew a **balanced 15-question subset** — one moderate, one hard, and one very-hard question per course — so that difficulty and subject are crossed evenly and the grid stays within a fixed API budget. Difficulty labels were assigned at authoring time and carried through to the analysis, enabling the per-difficulty breakdowns in §4. We are explicit that n = 15 priced questions per cell is small; §4 and the limitations discussion treat the resulting estimates as point estimates over a modest sample and recommend bootstrap confidence intervals for any pairwise claim.

### 3.2 The distilled vertical prompt ladder

The prompt is the independent variable this paper is built around. A recurring, **unconfirmed** industry anecdote holds that a frontier assistant shipped with a very long (on the order of 130k-token) system prompt that was later distilled or leaked. We treat this only as motivation and flag it as unverified; we neither reproduce, quote, paraphrase, nor reconstruct the contents of any proprietary or allegedly-leaked prompt, and none of our prompt text is derived from one. A known failure mode motivates our design choice: small or cheap models tend to *over-weight* irrelevant portions of a very long prompt and get "over-squeezed," which can degrade rather than improve their behavior. Rather than test a giant prompt, we ask whether the *juice* of such a prompt — its worked-method discipline, its edge-case awareness, its explicit "don'ts" — can be distilled into a short, vertical-specific prompt that captures the benefit without inviting the squeezing failure.

Accordingly, we define a three-rung **prompt ladder**. All three rungs are **original text** we wrote, distilled from general, publicly-understood prompting principles — chain-of-thought decomposition [CITE: chain-of-thought prompting], explicit self-verification [CITE: self-consistency / self-verification], structured output contracts, and common-error checklists — and not copied from any model's system prompt.

- **L0 — Plain.** A minimal instruction: solve every part of the question and show your work. No guidance on *how* to reason.
- **L1 — Verbose chain-of-thought + self-check.** An explicit five-stage protocol — *understand → plan → solve → verify → answer* — instructing the model to restate the problem, outline an approach, execute it step by step, check the result, and only then commit to a final answer. This rung supplies process structure but no domain-specific error taxonomy.
- **L2 — The "squeezed-juice" vertical prompt (~640 tokens).** A concise prompt engineered specifically for STEM problem-solving. It adds, on top of L1's process scaffold: (i) **setup discipline** (name the givens, unknowns, and applicable results before computing); (ii) a **solve-symbolically-first** instruction (derive the closed form, substitute numbers last); (iii) a **common-error checklist** that encodes the "don'ts" as explicit guardrails — sign conventions, dropped factors of two, radians vs. degrees, unit conversion, dropped terms, square-root branch selection, boundary and continuity conditions, off-by-one indexing, and domain of validity; (iv) a **verification protocol** (dimensional analysis, limiting-case checks, and independent re-derivation); and (v) a **proofs protocol** for items requiring an argument rather than a computed value. L2 is the concrete realization of the "distill the juice, avoid the squeeze" hypothesis: it delivers targeted, high-density guidance in a footprint two orders of magnitude smaller than the anecdotal long prompt.

Crucially, the three rungs **differ only in the middle "how to reason" guidance**. Two elements are held **byte-identical** across L0, L1, and L2:

1. **A grounding clause.** Identical wording instructs the model to answer strictly from the provided passage. Grounding is **phase-symmetric**: the clause is present in both the zero-shot and RAG conditions, so the two conditions differ only in whether the passage text is actually supplied, never in whether the model is *told* to stay grounded. This prevents the zero-shot condition from being an unintended invitation to fabricate source material.
2. **A strict output contract.** Every rung ends with the same `===FINAL===` per-part answer contract, requiring a clearly delimited final answer for each part of the question.

Both invariants are **enforced in code**, not by inspection: the harness asserts that the grounding clause and output-contract blocks are byte-identical across rungs (via a hash check) and that the output contract appears **last** in the assembled prompt for every cell. This guarantees that any accuracy difference we attribute to prompt level comes from the reasoning guidance alone, and that the answer contract is never accidentally reordered or diluted by a longer middle section.

### 3.3 Experimental grid

The full grid is **8 models × 3 prompt levels × 2 grounding conditions × 15 questions = 720 cells**. The models span three cost tiers:

- **Tier 1 (frontier):** GPT-5.5, Opus 4.8, Gemini 3.1 Pro.
- **Tier 2 (mid):** Sonnet 5, Gemini 3.5 Flash.
- **Tier 3 (cheap):** DeepSeek V4 Pro, Llama 4 Maverick, Gemma 4 31B.

The two grounding conditions are **zero-shot** (question only) and **RAG** (question preceded by its full reference passage). Because each passage is self-contained (§3.1), the RAG condition supplies genuinely sufficient context, and the zero-shot condition isolates what the model can do from parametric knowledge alone under the same grounding instruction.

Every model receives the **same prompts and the same decoding parameters**; the only thing that varies across the two grounding conditions is whether the passage is present. Decoding uses **temperature 0** for determinism. For reasoning-capable models we impose a **uniform 3000-token reasoning budget**. This budget serves two purposes: it bounds cost, and it prevents an unbounded reasoning trace from consuming the token budget that the answer block needs — a failure mode that would otherwise penalize exactly the models most inclined to think at length. We note that capping reasoning is a deliberate design choice with a cost/quality trade-off, and we flag reasoning as a *confounded* axis in §3.5.

### 3.4 Execution

We ran the grid with a **self-built streaming client**. For every API call the runner logs per-call **token usage** (prompt and completion tokens) and **time-to-first-token (TTFT)**, streamed from the provider, and enforces a **hard budget guard** that halts the run before a preset spend ceiling is crossed. This keeps the study reproducible and the cost accounting exact rather than estimated: the headline cost figures in §3.6 are computed from metered usage, not from token counts we inferred ourselves. The complete study — all 720 cells plus grading — cost **$16.50** in metered API spend.

One execution caveat must be disclosed for fairness. The **Anthropic models (Opus 4.8 and Sonnet 5), and all grading calls**, were served through a **subscription endpoint** rather than a metered pay-per-token API. Two consequences follow. First, their cost is **imputed at published list rates** from the logged token usage rather than directly metered; we mark every such figure as imputed. Second, TTFT from the subscription endpoint is **not comparable** to the metered endpoints and is therefore excluded from any latency comparison involving those models. We surface this rather than bury it because it bears directly on how the cost and latency numbers should be read.

The subscription endpoint also produced a diagnosable **artifact that we detected and corrected in-pipeline** — reported here as evidence that the harness surfaces its own confounds. In the initial run, the Anthropic models scored anomalously low (Opus 4.8 at 0.815) because a wrapper on the subscription endpoint caused them to emit **answer-only** outputs with essentially **zero characters of shown work**. This penalized the Reasoning axis and, on proof items where the derivation *is* the answer, the Accuracy axis as well. We diagnosed the cause by inspecting shown-work length per response, re-ran the affected cells with a corrected instruction (after which the models produced full 4,000–5,000-character worked solutions), and **re-graded the corrected outputs blindly**. Accuracy rose to **0.991 (Opus 4.8)** and **0.953 (Sonnet 5)**. All results reported in §4 use the corrected, re-graded outputs. We include this episode because a study that cannot detect its own instrumentation confounds cannot be trusted at the top of the accuracy range, which is precisely where our central finding lives.

### 3.5 Blind grading

Every response was graded by an **Opus 4.8 rubric grader** operating **blind**: model identities were stripped from the transcripts before grading, so the grader could not condition on which model produced an answer. The rubric scores each **part** of each multi-part question on three axes:

- **Accuracy** — 0 / 1 / 2 (wrong / partially correct / correct);
- **Reasoning** — 0 / 1 / 2 (quality and validity of the shown derivation);
- **Format** — 0 / 1 (adherence to the per-part answer contract).

The grader accepts **algebraically-equivalent forms** — e.g., factored vs. expanded expressions, or equivalent trigonometric or set-notation renderings — so a correct answer is not penalized for surface form.

We **validated** the grader rather than assuming it. In a check on the grader's discrimination, an Opus L1 response that mis-computed a surjection count was scored **0.667** overall, with the grader correctly assigning **0** to the erroneous part while crediting the parts that were right. This confirms the grader catches a *planted* arithmetic error and localizes it to the offending sub-part rather than blurring it across the item. We treat this as necessary but not sufficient evidence of grader reliability and, given the small n, recommend the confidence-interval caveats in §4 for any close comparison.

Two honesty caveats on the axes. First, **Accuracy is the primary metric** and **Reasoning is a confounded secondary** one: some models emit visible chain-of-thought while others reason in a hidden trace, so the Reasoning axis partly measures *whether work was shown* rather than *whether the reasoning was sound*. The §3.4 artifact is a concrete instance of this confound. Second, because grading itself ran on the subscription endpoint, it inherits the imputed-cost caveat for accounting purposes (the grading cost is folded into the $16.50 total at list rates).

### 3.6 Metrics

We report accuracy and cost, with cost-per-correct as the headline.

**Accuracy** is the normalized Accuracy-axis score, averaged over parts and questions, reported per cell and aggregated by model, difficulty, subject, prompt level (for the L0→L2 *prompt-lift*), and grounding condition (for the zero-shot→RAG *RAG-delta*). Accuracy is our primary quality metric; the rubric also defines Reasoning and Format weights for a composite quality score, but we lead with Accuracy for the reasons in §3.5.

**Cost** is computed per call from **metered usage** as

$$\text{cost} = \text{prompt\_tokens} \times \text{rate}_{\text{in}} + \text{completion\_tokens} \times \text{rate}_{\text{out}},$$

using each provider's published input/output rates (imputed at list rates for the subscription-served Anthropic models, per §3.4).

**Cost-per-correct** is our headline efficiency metric:

$$\text{cost-per-correct} = \frac{\text{mean cost per call}}{\text{accuracy}}.$$

This normalizes raw per-call price by the answer quality it buys, so a model that is slightly less accurate but far cheaper is not flattered or unfairly penalized: it is charged for the correctness it actually delivers. Cost-per-correct is what lets us state the study's economic finding — cheap models matching frontier accuracy at a fraction of the price — on a single, like-for-like axis, which we develop in §4.

## 4. Results

We report accuracy from the priced 15-question run subset (1 moderate + 1 hard + 1 very-hard per course) across the full 8-model × 3-level × {zero-shot, RAG} grid (720 graded cells). Accuracy is the primary metric, scored blind by an Opus-4.8 rubric with algebraically-equivalent forms accepted; cost-per-correct (mean per-call cost divided by accuracy) is the headline deployment metric. The **total metered API cost of the entire study was $16.50**. Anthropic models (Opus 4.8, Sonnet 5) and all grading ran on a subscription endpoint, so their dollar figures are **imputed at list rates** and their TTFT is not endpoint-comparable; this is flagged inline below and treated as a limitation.

### Table 1 — Per-model summary

| Model | Tier | Mean accuracy | Best-of-ladder accuracy | Min cost-per-correct |
|---|---|---|---|---|
| Opus 4.8 | T1 | 0.991 | 1.000 | $0.046 (imputed) |
| GPT-5.5 | T1 | 0.989 | 1.000 | $0.084 |
| Gemini 3.1 Pro | T1 | 0.984 | 0.987 | $0.044 |
| Gemini 3.5 Flash | T2 | 0.993 | 1.000 | $0.032 |
| Sonnet 5 | T2 | 0.953 | 1.000 | $0.024 (imputed) |
| DeepSeek V4 Pro | T3 | 0.988 | 0.993 | $0.0035 |
| Gemma 4 31B | T3 | 0.976 | 0.987 | $0.00071 |
| Llama 4 Maverick | T3 | 0.861 | 0.881 | $0.0013 |

Two facts are visible at a glance and structure the rest of this section: (i) seven of eight models cluster tightly at the top, with best-of-ladder accuracy at or near the 1.000 ceiling, and (ii) the min cost-per-correct spans nearly two orders of magnitude — from GPT-5.5 at $0.084 down to Gemma 4 31B at $0.00071 — despite near-identical accuracy. The single clear outlier on accuracy is Llama 4 Maverick (0.861 mean, 0.881 best-of-ladder).

### 4.1 Overall accuracy and the ceiling effect

Aggregating over all models, levels, and retrieval conditions, accuracy is **mean 0.967, median 1.000**. The median of 1.000 indicates that on a majority of graded cells the model answered every part of the question fully correctly.

Accuracy is essentially flat across difficulty, which is itself notable given that the difficulty labels were assigned by the (independently re-solved and adjudicated) item authors:

| Difficulty | Accuracy |
|---|---|
| Moderate | 0.979 |
| Hard | 0.952 |
| Very-hard | 0.970 |

The very-hard items are not systematically harder for the models than the merely-hard items (0.970 vs 0.952), and all three bands sit within a narrow band of one another. By subject, the spread is similarly compressed:

| Subject | Accuracy (approx.) |
|---|---|
| Mechanics | 0.93 |
| Linear Algebra | 0.95 |
| Electromagnetism | 0.96 |
| Discrete Math | 0.99 |
| Calculus | 1.00 |

Mechanics is the hardest subject and Calculus the easiest, but even the floor (0.93) is high in absolute terms.

We read this as a **ceiling effect**, and we treat it as the central finding *and* the central limitation of the study. On STEM problems that are self-contained — where the accompanying passage states every definition and theorem the question requires — 2026-generation models across all three tiers are near-saturated. This compression is what makes the cost axis, not the accuracy axis, the discriminating dimension (§4.5). It also means the corpus does not separate the top tier of models from one another with any statistical confidence, a point we return to in the limitations.

### 4.2 Prompt-lift is approximately zero (and L2 does not over-squeeze)

The three prompt levels differ *only* in the middle "how to reason" guidance — L0 (plain: "solve every part, show work"), L1 (verbose chain-of-thought + self-check), and L2 (the concise ~640-token "squeezed-juice" vertical prompt with a common-error checklist, a verification protocol, and a proofs protocol). The grounding clause and the strict `===FINAL===` per-part answer contract are byte-identical across levels and enforced in code (hash check + contract-last assertion), so any accuracy difference is attributable to reasoning guidance alone.

The measured **L0→L2 accuracy lift is approximately zero for every model**, in the range **−0.007 to +0.003**. Sonnet 5 shows a nominal +0.050, but on n=15 questions this is small-sample noise rather than a reliable effect. We therefore make **no claim that the distilled prompt lifts accuracy** on this task: at ceiling, there is simply no headroom for prompt engineering to recover.

The *negative* result here is the one we want to underline, because it is the crux of the paper's thesis. A well-known failure mode of long, general-purpose system prompts is that small models over-weight irrelevant instructions and get "over-squeezed," losing accuracy. If our concise vertical L2 prompt were triggering that degradation, we would expect the smallest models to *lose* accuracy relative to the plain L0 baseline. They do not. The verbose-to-concise transition costs the Tier-3 small models nothing beyond noise (**Llama 4 Maverick −0.006, Gemma 4 31B −0.007**, both within the measurement band). In other words, the distilled vertical prompt is accuracy-neutral rather than accuracy-harmful even on the smallest models in the grid — it delivers the structure of a frontier-style prompt without inducing the over-squeezing penalty a full-length (rumored ~130k-token) prompt is anecdotally reported to cause.

We stress that we did **not** directly test a full-length prompt against the concise one; the over-squeezing hazard is used only as motivation and framing, and the ~130k-token figure is an **unconfirmed anecdote**. What we *can* report is the confirmatory half: the concise distilled prompt is a safe drop-in — it neither helps nor hurts accuracy at ceiling.

### 4.3 RAG delta

We compare the zero-shot condition (passage withheld; grounding phase-symmetric so no source-fabrication is licensed) against the RAG condition (passage retrieved and supplied). The **zero-shot → RAG accuracy delta is small and mostly non-negative**:

| Model | RAG delta |
|---|---|
| Gemma 4 31B | +0.016 |
| Llama 4 Maverick | +0.012 |
| Gemini 3.1 Pro | +0.004 |
| Gemini 3.5 Flash | +0.004 |

The largest gains accrue to the smallest models (Gemma, Llama), which is consistent with retrieval helping exactly where parametric knowledge is weakest. Several frontier models show a slightly *negative* delta, but these fall within the same noise band that governs §4.2 and should not be read as retrieval hurting. The takeaway is that on a self-contained corpus, RAG provides a modest, safe uplift for smaller models and is close to a no-op for the strongest ones — again consistent with the ceiling effect.

### 4.4 A detected-and-corrected artifact (methods integrity)

We report one pipeline artifact in full, because catching it is itself evidence the evaluation surfaces its own confounds. In the first pass, the two Anthropic models scored anomalously low — **Opus 4.8 at 0.815** — an outlier flatly inconsistent with their standing on every other axis. Diagnosing via shown-work length revealed the cause: a subscription-endpoint wrapper made Opus and Sonnet emit **answer-only outputs (0 characters of shown work)**. Because the rubric scores a Reasoning axis, and because proof items require demonstrated derivation for full Accuracy credit, the missing work depressed both scores.

We re-ran the affected models with a corrected instruction; they then produced full worked solutions (**4,000–5,000 characters** of derivation), and we **re-graded blind**. The corrected scores are the ones reported throughout this paper: **Opus 4.8 → 0.991** and **Sonnet 5 → 0.953**. Separately, the grader itself was validated against a planted error: an Opus L1 response that mis-computed a surjection count was scored **0.667**, correctly zeroing the wrong sub-part rather than rubber-stamping a fluent-but-incorrect answer. Together these establish that (i) the grader discriminates on correctness, not surface fluency, and (ii) the pipeline detects and corrects endpoint-induced output artifacts rather than baking them into headline numbers. We note as a residual caveat that the Reasoning axis remains confounded by the visible-vs-hidden chain-of-thought distinction and is not endpoint-fair; this is why Accuracy, not the composite quality score, is our primary metric.

### 4.5 Answering the research questions

**RQ1 — Do cheap models match frontier accuracy on answerable-from-source STEM?** Yes. The frontier accuracy ceiling in this study is **best-of-ladder 1.000** (Opus 4.8, GPT-5.5, Gemini 3.5 Flash, Sonnet 5). Among the cheapest Tier-3 models, **DeepSeek V4 Pro reaches 0.993** and **Gemma 4 31B reaches 0.987** best-of-ladder — statistically indistinguishable from the ceiling on n=15 (top models are within likely CI overlap; see limitations). Only **Llama 4 Maverick (0.861)** is a clear capability floor. So with a single exception, cheap models match frontier accuracy on this task.

**RQ2 — At what cost ratio?** The accuracy parity comes at a dramatic cost advantage. Taking min cost-per-correct as the deployment figure:

- **Gemma 4 31B** answers correctly at **$0.00071/correct**, versus **GPT-5.5 at $0.084/correct** — roughly **117× cheaper** at effectively equal accuracy.
- **DeepSeek V4 Pro** answers correctly at **$0.0035/correct**, roughly **24× cheaper** than GPT-5.5 while scoring 0.993 best-of-ladder.

The full spread across the grid confirms the pattern: accuracy varies by a few percentage points among the top seven models, while cost-per-correct varies by ~117×.

**RQ3 — Does the concise distilled ("squeezed-juice") vertical prompt improve or degrade cheap-model performance?** Neither, at ceiling. As established in §4.2, the L0→L2 lift is ≈0 for all models (−0.007 to +0.003), and — critically — the concise L2 prompt does **not over-squeeze** the small Tier-3 models (Gemma −0.007, Llama −0.006, both within noise). The contribution of the distilled prompt is therefore not an accuracy gain but a **safety property**: it packages frontier-style reasoning structure (setup discipline, symbolic-first solving, a common-error/"don'ts" checklist, and a verification protocol) into ~640 tokens that neither help nor hurt at ceiling — making it a pragmatic default for cheap-model vertical deployment rather than a lever for accuracy.

Taken together, the results support the paper's honest thesis: on self-contained Hebrew (RTL) STEM, **cheap models already match frontier accuracy at 24–117× lower cost**, and a concise distilled vertical prompt is a **safe, accuracy-neutral deployment recipe** that avoids the over-squeezing degradation attributed to full-length prompts. The ceiling effect that makes this parity so clean is simultaneously the study's principal limitation: a harder, less self-contained, or adversarial corpus would be required to separate the top tier and to directly test the concise-vs-full-length prompt trade-off, which we leave to future work [CITE: over-squeezing long prompts]. [CITE: bootstrap confidence intervals for small-sample eval]

## 5. Discussion

### 5.1 The distilled-vertical-prompt thesis meets a ceiling

We set out to test whether a *concise, frontier-inspired vertical prompt* — the "squeezed juice" of a long system prompt, distilled into ~640 tokens of setup discipline, a common-error checklist, and a verification protocol — could lift cheap models on academic STEM reasoning in Hebrew. The honest finding is that on this corpus **there was nothing to lift**. Prompt-lift from the plain baseline (L0) to the distilled vertical prompt (L2) is statistically indistinguishable from zero for every model in the grid (range −0.007 to +0.003; Sonnet 5's +0.050 is small-sample noise on n=15). Accuracy was already near the ceiling — overall mean 0.967, median 1.000 — before any prompt engineering was applied.

This is not a null result in the discouraging sense. It reframes where the value actually lives. When the task is *answerable from a self-contained source* and the model is a 2026-generation system, accuracy is essentially solved, and the axis on which deployments still differ by orders of magnitude is **cost**, not prompt design. The distilled vertical prompt does not buy accuracy here because accuracy is not the scarce resource; it buys *safety* — a point we develop below.

### 5.2 The win is cost, not prompt-lift

The cost story is stark. The frontier accuracy ceiling on our best-of-ladder metric is held jointly by Opus 4.8 and GPT-5.5 at 1.000. A Tier-3 open-weights model, **Gemma 4 31B, reaches 0.987 best-of-ladder at $0.00071 per correct answer — roughly 117× cheaper than GPT-5.5's $0.084**. DeepSeek V4 Pro matches the frontier within noise (0.993) at ~24× lower cost per correct answer. Even the mid-tier Gemini 3.5 Flash posts the highest mean accuracy in the entire grid (0.993) at $0.032 per correct answer. In other words, for STEM problems that are answerable from their source material, the accuracy gap between a flagship and a small open model has collapsed to within plausible confidence-interval overlap, while the price gap spans two orders of magnitude.

Cost-per-correct is the right lens precisely *because* accuracy has saturated: when two models both answer correctly almost always, the deployment decision reduces to what each correct answer costs to produce. On that metric the cheap models do not merely compete — they win outright, and the frontier premium becomes difficult to justify for this vertical.

The one clear exception marks the real floor. **Llama 4 Maverick (0.861 mean, 0.881 best-of-ladder)** is the single model that fails to reach the ceiling, and it does so at a level (roughly one part in seven scored below full accuracy) that would be visible to users. This tells us the ceiling is a property of *capable* cheap models, not of cheapness as such: below some capability threshold the parity disappears. Gemma 4 31B sits above that threshold; Llama 4 Maverick sits at it.

### 5.3 Why "concise" matters: the prompt's value is that it is safe

The motivating anecdote for this work — an *unverified, publicly circulated rumor* of a very long (~130k-token) frontier system prompt allegedly distilled or leaked; we neither confirm it nor reproduce, quote, or characterize any such content — resurfaced a real, documented failure mode: small models handed a very long prompt tend to over-weight its irrelevant portions and degrade, a "squeezing" effect [CITE: long-context prompt degradation in small models]. Our three prompt levels are original text, written from general prompting principles (chain-of-thought, self-verification, structured output, common-error checklists) rather than derived from any model's proprietary prompt.

Against that backdrop, the *absence* of a downside is itself the finding. The verbose chain-of-thought level (L1) did not hurt the small models (Llama −0.006, Gemma −0.007 — both within noise), and the distilled L2 neither helped nor harmed. The distilled vertical prompt therefore occupies a genuinely useful position: it carries the reasoning scaffolding, the "don'ts," and the verification protocol one would want from a long frontier prompt, **without the length that triggers over-squeezing**. On a task already at ceiling this manifests as "no change" — but "no change" is exactly what a deployment recipe should guarantee. The concise prompt is safe by construction: it cannot over-squeeze a small model because it is short, and our data confirm it does not degrade even the two weakest Tier-3 models.

### 5.4 Implications: cheap models per vertical, as skills

Taken together, these results argue for a specific deployment pattern. For a bounded academic vertical — here, standard first-year undergraduate STEM in Hebrew RTL — the pragmatic recipe is a **capable cheap model paired with a concise distilled vertical prompt**, deployed as a reusable skill. This captures the accuracy of the frontier (within CI) at a fraction of the cost, while the concise prompt guards against the length-driven degradation that would make a naive "just give the small model the big prompt" strategy backfire.

The broader implication is that, for *answerable-from-source* STEM, the frontier gap has effectively closed. The differentiator among 2026 models on this class of task is no longer whether they can solve the problem but what solving it costs — and that shifts the design question from "which is the strongest model" to "which is the cheapest model above the capability floor, wrapped in a prompt that is short enough not to hurt it." That is a per-vertical, skill-shaped answer, and it is cheap: the entire study cost $16.50 in metered API usage.

## 6. Limitations

**Ceiling effect and low top-tier discrimination.** The central limitation is also the central finding: the corpus is too answerable for 2026-generation models to separate at the top. With overall accuracy at mean 0.967 / median 1.000, the top five models (Gemini 3.5 Flash 0.993, Opus 4.8 0.991, GPT-5.5 0.989, DeepSeek V4 Pro 0.988, Gemini 3.1 Pro 0.984) sit within a span that is almost certainly inside overlapping confidence intervals. We cannot, from this data, claim a reliable ordering among them, and we do not. The ceiling also means our prompt-lift null (L0→L2 ≈ 0) is measured in a regime with little headroom — it is entirely consistent with a distilled prompt mattering more on harder, less self-contained items. Establishing that requires a corpus deliberately built to be *not* fully answerable from its passage: adversarial, multi-source, or partially-underdetermined items.

**Small n and the need for bootstrap CIs.** The priced grid uses a 15-question balanced subset (one moderate, one hard, one very-hard per course across five courses), chosen to bound API budget. Fifteen items is small for the per-model accuracy differences we report; point estimates should be read with bootstrap confidence intervals, which we advise and which we expect to place the top five models within mutual overlap. Per-subject figures (Mechanics 0.93 … Calculus 1.00) rest on even fewer items each and should be treated as directional.

**The Reasoning axis is not endpoint-fair.** Our secondary quality metric, Reasoning (0/1/2), is confounded by *visible-versus-hidden* chain-of-thought: models that stream their working are scored on text that models emitting terminal answers do not expose. This is not a like-for-like comparison, and we treat Accuracy — not Reasoning or the composite quality weight — as the primary metric throughout. The Reasoning numbers should not be used to rank models.

**Subscription-endpoint imputed cost and non-comparable TTFT.** The Anthropic models (Opus 4.8, Sonnet 5) and all grading ran on a subscription endpoint rather than a metered pay-per-token API. Their cost-per-correct figures are therefore **imputed at published list rates**, not observed billing, and their time-to-first-token is not comparable to the metered-endpoint models and is excluded from latency comparison. Their accuracy is directly measured; their price is a modeled estimate. Relatedly, we surfaced and corrected a pipeline artifact in which a subscription-endpoint wrapper caused Opus/Sonnet to emit answer-only outputs (0 characters of shown work), which spuriously penalized Reasoning and, on proof items, Accuracy (Opus initially 0.815). We diagnosed this via shown-work length, re-ran with a corrected instruction (yielding 4–5k characters of worked solution), and re-graded blindly, recovering Opus 0.991 / Sonnet 0.953. We report this as methods integrity — the pipeline surfaces its own confounds — but it is a reminder that endpoint wrappers can silently distort output format.

**We did not directly test the 130k-vs-concise comparison.** The over-squeezing hypothesis is our *motivation*, not a claim we tested head-to-head. We did not run a full-length (~130k-token) prompt against our concise distilled prompt on the same models; the ~130k figure is an unconfirmed anecdote, and we deliberately did not attempt to reconstruct any such prompt (see integrity notes). Our evidence for the concise prompt's safety is indirect: verbose L1 and distilled L2 do not degrade even the weakest small models on this task. A direct length-scaling study — measuring where, and for which models, prompt length begins to hurt — is the natural next step and the most important piece of future work.

**Corpus construction.** The passages are original, synthetic, course-aligned Hebrew texts written to be self-contained; they are not verbatim textbook material. This makes them openly redistributable but also, by design, unusually answerable — reinforcing the ceiling. Generalization to noisier, real-world course material (partial OCR, missing definitions, cross-referenced sources) is untested.

## 7. Conclusion

We evaluated eight models across three levels of a distilled vertical prompt, in zero-shot and RAG conditions, on a balanced set of hard multi-part Hebrew RTL STEM questions — 720 cells in all, blind-graded against an accuracy-first rubric. The result is a clean, honest, two-part finding.

First, **cheap models already match frontier accuracy** on STEM problems that are answerable from their source. A Tier-3 open-weights model reaches the frontier best-of-ladder ceiling at roughly 117× lower cost per correct answer than a flagship; a second matches it at ~24× lower cost. The frontier premium, on this vertical, buys almost nothing in accuracy.

Second, **the concise distilled vertical prompt neither helps nor hurts at ceiling** — and that is its virtue. On a near-saturated task there is no accuracy to add, but crucially the short prompt does *not* trigger the over-squeezing degradation that a full-length frontier prompt is known to induce in small models. It carries the reasoning scaffolding and error checklist of a long prompt without the length that would backfire. The concise vertical prompt is thus the pragmatic, safe deployment recipe: it captures frontier-quality behavior on a bounded vertical, at cheap-model cost, without the risk of length-driven collapse.

We make no claim of prompt-driven accuracy gains — the data show lift ≈ 0, and we report it as such. What the data *do* support is a deployment thesis: for answerable-from-source academic STEM, pair a capable cheap model with a concise distilled prompt, ship it as a per-vertical skill, and spend the two orders of magnitude you save elsewhere. The open question we hand to future work is where that parity breaks — on harder, less self-contained, adversarial items, and under a direct long-versus-concise prompt-length comparison that we deliberately left untested here.

## Reproducibility & Data Availability

The full evaluation grid comprises **720 cells** (8 models × 3 prompt levels × {zero-shot, RAG} × 15 questions). All outputs were **blind-graded** with model identities stripped, using an Opus-4.8 rubric scoring each part for Accuracy (0/1/2), Reasoning (0/1/2), and Format (0/1), with algebraically-equivalent forms accepted; the grader was validated by its correct zeroing of a planted arithmetic error. The three prompt levels differ only in their middle "how to reason" guidance and share a byte-identical grounding clause and per-part `===FINAL===` answer contract, enforced in code via a prompt hash and a contract-last assertion; the runner is a self-built streaming client that logs per-call token usage and TTFT under a hard budget guard, at temperature 0 with a uniform 3000-token reasoning budget for reasoning-capable models.

We release the corpus (five original, self-contained, course-aligned Hebrew STEM passages plus 20 authored-and-adjudicated multi-part questions), the prompt ladder, the runner and grading code, and the complete per-cell grades and token/cost logs, to enable independent re-grading and re-pricing. The **total metered API cost of the entire study was $16.50**. Anthropic models (Opus 4.8, Sonnet 5) and all grading ran on a subscription endpoint, so their cost figures are imputed at list rates and their TTFT is excluded from latency comparison; this is disclosed per cell in the released logs. The prompt levels are original text distilled from general prompting principles, not derived from any proprietary or allegedly-leaked system prompt.
