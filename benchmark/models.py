"""Model registry for the 8-model benchmark.

via="openrouter" -> billed API call (counts against the $20 cap).
via="max"        -> run on the Claude Max subscription (Anthropic models + grading);
                    rate_in/out are IMPUTED list prices for the Pareto analysis only,
                    NOT money spent here.

Prices are USD per 1M tokens.  Verified from OpenRouter (2026-07) where marked ✓.
"""

MODELS = [
    # ---- Tier 1 ----   (reasoning=True -> gets the uniform thinking budget)
    dict(key="gpt-5.5",        tier=1, via="openrouter", reasoning=True,
         openrouter_id="openai/gpt-5.5",                rate_in=5.00,  rate_out=30.0),   # ✓ $5 / $30
    dict(key="gemini-3.1-pro", tier=1, via="openrouter", reasoning=True,
         openrouter_id="google/gemini-3.1-pro-preview", rate_in=2.00,  rate_out=12.0),   # ✓ $2 / $12
    dict(key="opus-4.8",       tier=1, via="max", reasoning=True,
         openrouter_id="anthropic/claude-opus-4.8",     rate_in=5.00,  rate_out=25.0),   # imputed (Max)

    # ---- Tier 2 ----
    dict(key="sonnet-5",       tier=2, via="max", reasoning=True,
         openrouter_id="anthropic/claude-sonnet-5",     rate_in=3.00,  rate_out=15.0),   # imputed (Max)
    dict(key="gemini-flash",   tier=2, via="openrouter", reasoning=True,
         openrouter_id="google/gemini-3.5-flash",       rate_in=1.50,  rate_out=9.00),   # ✓ Gemini 3.5 Flash $1.50 / $9

    # ---- Tier 3 ----
    dict(key="deepseek-v4",    tier=3, via="openrouter", reasoning=True,
         openrouter_id="deepseek/deepseek-v4-pro",      rate_in=0.435, rate_out=0.87),   # ✓ $0.435 / $0.87
    dict(key="llama4-mav",     tier=3, via="openrouter", reasoning=False,
         openrouter_id="meta-llama/llama-4-maverick",   rate_in=0.15,  rate_out=0.60),   # ✓ Llama 4 Maverick $0.15 / $0.60
    dict(key="gemma4-31b",     tier=3, via="openrouter", reasoning=False,
         openrouter_id="google/gemma-4-31b-it",         rate_in=0.12,  rate_out=0.35),   # ✓ $0.12 / $0.35
    # (free alt: google/gemma-4-31b-it:free — $0 but rate-limited; use for a $0 smoke test)
]

BY_KEY = {m["key"]: m for m in MODELS}
OPENROUTER_MODELS = [m for m in MODELS if m["via"] == "openrouter"]
MAX_MODELS = [m for m in MODELS if m["via"] == "max"]

# Grader runs on Max (off the API meter). Imputed price for any accounting only.
GRADER = dict(key="opus-4.8-grader", openrouter_id="anthropic/claude-opus-4.8",
              via="max", rate_in=5.00, rate_out=25.0)
