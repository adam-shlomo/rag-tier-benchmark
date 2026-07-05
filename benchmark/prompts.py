"""Prompt ladder + assembly for the Hebrew-STEM RAG benchmark.

Invariants (byte-identical across levels): PERSONA, GROUNDING, and the CONTRACT
rules text. Only the MIDDLE guidance scales (L0/L1/L2). The contract's part-label
lines are templated per question so an 8B never stops early on a 4-part item.

Assembly (contract is strictly LAST — it sits in the model's recency window):
  system = PERSONA + GROUNDING + MIDDLE[level]
  user   = [RAG passage]? + QUESTION + CONTRACT(parts)
"""
import hashlib

PERSONA = ("You solve hard university-level math and physics problems. "
           "The question is in Hebrew. Respond in Hebrew, with all math in LaTeX using $...$.")

GROUNDING = ("If a source passage appears before the question, base your solution on it and "
             "prefer its definitions, notation, and given values where they differ from your own. "
             "If no passage appears, solve from your own knowledge — do not mention or invent a "
             "source that is not there.")

# ---- MIDDLE guidance per level (this is the only thing that scales) ----
MIDDLE = {
    "L0": "Solve every part of the question and show your work.",

    "L1": (
        "Before the final block, reason through these steps as short bullets (not paragraphs). "
        "This checklist guides your thinking; in your written answer include only the Hebrew "
        "solution and then the block.\n"
        "1. Understand — restate what is given (values, units, conditions) and what each part (א, ב, ...) asks.\n"
        "2. Plan — choose the principle or equation for each part before computing.\n"
        "3. Solve — do each part step by step; keep it symbolic first, substitute numbers last; carry units throughout.\n"
        "4. Check — verify units, recompute one critical number, and sanity-check magnitude and sign "
        "(a limiting case if possible). Fix anything wrong before finalizing.\n"
        "5. Answer — only now write the block, and nothing after ===END===.\n"
        "Solve every part."
    ),

    "L2": (
        "Follow the checklist below to reason. It guides your thinking only — in your written answer "
        "include the Hebrew solution and then the block, nothing else.\n\n"
        "1. SET UP\n"
        "- List the parts to solve (א, ב, ...) and what each asks for.\n"
        "- Write every given quantity with its unit; name the unknowns.\n"
        "- State the law/definition/formula before using it; fix axes, sign convention, and reference/zero point.\n\n"
        "2. SOLVE SYMBOLICALLY FIRST\n"
        "- Stay in symbols; isolate the target variable; substitute numbers only at the last step.\n"
        "- Convert all inputs to one consistent unit system before substituting; carry units through every line.\n\n"
        "3. WATCH FOR COMMON ERRORS\n"
        "- Sign conventions; stray factor of 2; radians vs degrees; unit conversions; dropped terms when "
        "expanding/integrating; sqrt-of-square branch; boundary/continuity conditions; off-by-one in sums; domain of validity.\n\n"
        "4. VERIFY BEFORE COMMITTING\n"
        "- Dimensional check on the final expression.\n"
        "- Limiting-case and magnitude/sanity check.\n"
        "- Re-derive one key step a second way, or substitute the answer back.\n"
        "- If a check fails, find the error and redo — never report a value you could not confirm.\n\n"
        "5. FOR PROOFS / DERIVATIONS\n"
        "- State the target claim; name each theorem/definition you invoke; justify every step.\n"
        "- Induction: check the base case AND the inductive step separately; end by confirming you reached the target.\n\n"
        "6. THEN ANSWER\n"
        "- One clean final result per part. If a part resists verification, keep your best attempt and mark it UNSURE.\n"
        "- Always end with the ===FINAL=== block below, and write nothing after ===END===.\n\n"
        "Solve every part."
    ),
}
LEVELS = ["L0", "L1", "L2"]

# ---- CONTRACT (rules text is invariant; the label lines are templated per question) ----
_CONTRACT_RULES = (
    r"""Rules for the block:
- One line per part, in order, for ALL parts the question has (__ALLPARTS__). Never stop early.
- Start the line with the part's label, then ": ", then only the final result.
- Put every expression and number in $...$, with units inside, e.g.  א: $3.2\,\text{m/s}$.
- Symbolic-then-numeric part: give both as  $symbolic$ => $numeric with units$ , e.g.  ב: $v=\sqrt{2gh}$ => $6.3\,\text{m/s}$.
- If unsure of a part, prefix that line's answer with UNSURE: (keep your best attempt after it).
- No commentary and no extra lines inside the block."""
)

def contract_block(parts):
    """Templated contract; identical across models/levels for a given question's parts."""
    label_lines = "\n".join(f"{p}: <final answer>" for p in parts)
    rules = _CONTRACT_RULES.replace("__ALLPARTS__", ", ".join(parts))
    return (
        "End your response with EXACTLY this block, and write NOTHING after the ===END=== line:\n\n"
        "===FINAL===\n"
        f"{label_lines}\n"
        "===END===\n\n"
        f"{rules}"
    )

# ---- invariance references (assert these never drift across assembled prompts) ----
GROUNDING_SHA = hashlib.sha256(GROUNDING.encode()).hexdigest()
CONTRACT_RULES_SHA = hashlib.sha256(_CONTRACT_RULES.encode()).hexdigest()

def assemble(level, question_text, parts, chunk=None):
    """Return (system, user). chunk=None -> zero-shot; chunk set -> RAG arm."""
    system = f"{PERSONA}\n\n{GROUNDING}\n\n{MIDDLE[level]}"
    passage = f'מקור (קטע לימוד):\n"""\n{chunk}\n"""\n\n' if chunk else ""
    user = f'{passage}שאלה:\n{question_text}\n\n{contract_block(parts)}'
    _assert_invariants(system, user)
    return system, user

def _assert_invariants(system, user):
    # grounding present and byte-identical
    assert GROUNDING in system, "GROUNDING missing from system prompt"
    assert hashlib.sha256(GROUNDING.encode()).hexdigest() == GROUNDING_SHA
    # contract rules byte-identical (find the rules substring inside user)
    assert "Rules for the block:" in user, "contract rules missing from user prompt"
    # contract is strictly LAST: nothing after the closing fence
    assert user.rstrip().endswith("No commentary and no extra lines inside the block."), \
        "contract must be the last thing in the user prompt"
    # ===FINAL=== is the unique fence anchor; ===END=== appears twice by design
    # (once in the 'write NOTHING after the ===END=== line' instruction, once as the fence).
    assert user.count("===FINAL===") == 1, "expected exactly one ===FINAL=== fence"

APPROX_SYS_TOKENS = {  # rough, for pre-run budgeting only; real cost comes from usage
    "L0": 280, "L1": 460, "L2": 730,
}
