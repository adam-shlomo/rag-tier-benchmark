# LinkedIn post (primary)

I spent the last few weeks testing one question:

Do Hebrew STEM students actually need frontier AI models — or are cheaper models already good enough?

Almost every LLM benchmark is in English. So I built my own for Hebrew (right-to-left), across five
first-year subjects: mechanics, electromagnetism, calculus, linear algebra, and discrete math.

Then I ran 8 models × 3 prompt styles × 2 grounding modes (zero-shot and RAG) → 720 blind-graded
answers. Total cost to run the whole thing: $16.50.

The surprising result: the prompt barely mattered.

I built a careful "distilled" system prompt — the reasoning discipline and common-mistake checklists of
a big frontier prompt, squeezed into a short one. Accuracy lift over a plain prompt? ≈ 0. The models
were already near the ceiling.

The real result: cost.

A 31B open model (Gemma 4 31B) matched the frontier's accuracy at ~$0.0007 per correct answer —
roughly 117× cheaper than GPT-5.5. Another cheap model (DeepSeek V4) matched it at ~24× cheaper. Only
one small model was clearly weaker, so the test still separates good from bad.

My takeaway as a builder:

For a bounded job like STEM tutoring, the right question isn't "what's the smartest model?"

It's: "what's the cheapest model that clears the accuracy floor for THIS vertical?"

If you're shipping an AI feature, benchmark your vertical. You might be paying 100× for accuracy you
already had.

I'm publishing the full independent research report — data, prompts, code, and blind grades — here: [link]

(Independent research, not peer-reviewed; original benchmark I wrote myself. Honest caveat: the task is
near-ceiling, so this ranks cost, not the very top of capability — the report says so plainly.)

#AI #LLM #MachineLearning #EdTech #PromptEngineering

---

# LinkedIn post (shorter alt / hook variant)

Everyone's asking which AI model is smartest.

For my product (STEM tutoring in Hebrew) I asked a cheaper question: which is the cheapest model that's
*good enough*?

So I built a Hebrew RTL STEM benchmark — 8 models, 720 blind-graded answers, $16.50 total.

Result: accuracy was basically tied at the top. A 31B open model matched a frontier model's accuracy at
~117× lower cost per correct answer. The fancy prompt I engineered? Barely moved the needle.

Lesson: benchmark your vertical. You may be paying 100× for accuracy you already had.

Full independent report + data + code: [link]

---

## Posting notes
- Post as text (LinkedIn suppresses reach on posts with outbound links) — OR put the link in the first
  comment and say "link in comments."
- Optional carousel (5–6 slides) from the report figures: (1) the question, (2) the setup, (3) "prompt
  ≈ 0 lift", (4) the cost table, (5) "benchmark your vertical", (6) link.
- Keep the honest caveat in — it reads as credible, not weak.
