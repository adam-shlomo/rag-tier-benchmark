"""Deterministic extraction of the ===FINAL=== answer block, and numeric compare.

Mirrors the grader-side regex spec from Step 2. Used by both the runner
(extraction_ok flag) and the grader (per-part answers + numeric fast-path).
"""
import re

_BLOCK = re.compile(r"===FINAL===\s*(.*?)\s*===END===", re.DOTALL)
_LINE = re.compile(r"^\s*([^\s:]+)\s*:\s*(.+?)\s*$")
_SYMNUM = re.compile(r"\$(.+?)\$\s*=>\s*\$(.+?)\$")
_NUM = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def _parse_lines(body):
    answers = {}
    for line in body.splitlines():
        if not line.strip():
            continue
        m = _LINE.match(line)
        if m:
            answers[m.group(1).strip()] = m.group(2).strip()
    return answers


def extract_block(text):
    """Return (ok, {label: raw_answer}). Uses the LAST ===FINAL===...===END=== block;
    ignores anything after ===END===. ok=False if no answers are recovered.

    Fallback (applied uniformly to every model): if the opening ===FINAL=== fence is
    missing but ===END=== is present, recover the trailing contiguous run of 'label:
    answer' lines just before it. This rescues the answer content when a (usually smaller)
    model drops the opening fence — a FORMAT violation the grader still penalizes from the
    raw output, but not an Accuracy/Reasoning loss."""
    text = text or ""
    matches = _BLOCK.findall(text)
    if matches:
        a = _parse_lines(matches[-1])
        return (len(a) > 0), a
    # fallback: dropped opening fence
    if "===END===" in text:
        before = text.rsplit("===END===", 1)[0]
        run = []
        for line in reversed(before.splitlines()):
            if _LINE.match(line):
                run.append(line)
            elif line.strip() == "" and run:
                continue
            elif run:
                break
        if run:
            a = _parse_lines("\n".join(reversed(run)))
            if a:
                return True, a
    return False, {}


def parse_answer(raw):
    """Split one answer line into structured pieces:
       {unsure, symbolic, numeric, text} — symbolic/numeric set if '=> ' form."""
    unsure = False
    a = raw
    if a.startswith("UNSURE:"):
        unsure = True
        a = a[len("UNSURE:"):].strip()
    sn = _SYMNUM.search(a)
    if sn:
        return {"unsure": unsure, "symbolic": sn.group(1).strip(),
                "numeric": sn.group(2).strip(), "text": a}
    return {"unsure": unsure, "symbolic": None, "numeric": None, "text": a}


def last_number(s):
    """Best-effort: the last numeric literal in a string (usually the answer value)."""
    if not s:
        return None
    nums = _NUM.findall(s.replace(",", ""))
    return float(nums[-1]) if nums else None


def numeric_match(model_ans, key_ans, rel_tol=0.02, abs_tol=1e-9):
    """True/False/None. None => can't decide numerically (symbolic-only), defer to LLM."""
    m = last_number(model_ans)
    k = last_number(key_ans)
    if m is None or k is None:
        return None
    denom = max(abs(k), abs(m), abs_tol)
    return abs(m - k) <= max(abs_tol, rel_tol * denom)
