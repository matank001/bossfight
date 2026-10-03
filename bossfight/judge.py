"""Cross-provider judge panel.

A contestant never grades its own output: each artifact is graded by the other three
flagship models and the scores are averaged (or majority-voted for labels). This is the
standard mitigation for self-preference bias in LLM-as-judge setups.
"""
from __future__ import annotations

import statistics
from collections import Counter

from .common import MODELS, ask_json

JUDGE_SYSTEM = (
    "You are an exacting evaluator on a professional benchmark panel (a seasoned COO, an employment lawyer and "
    "a CMO in one). Grade strictly against the rubric, use the full scale, and reply with JSON only."
)


def panel_scores(author: str, artifact: str, rubric: dict[str, str], context: str, tag: str):
    """Score `artifact` 1-5 on each rubric criterion with every judge except `author`."""
    crit = "\n".join(f'- "{k}": {v}' for k, v in rubric.items())
    prompt = (f"CONTEXT\n{context}\n\nARTIFACT TO GRADE\n<<<\n{artifact}\n>>>\n\n"
              f"Score the artifact 1 (poor) to 5 (excellent) on each criterion:\n{crit}\n\n"
              'Return JSON: {"scores": {criterion: int, ...}, "worst_flaw": "one sentence"}')
    out = {}
    for j in MODELS:
        if j == author:
            continue
        res, _ = ask_json(j, prompt, JUDGE_SYSTEM, tag=f"judge:{tag}")
        if res and isinstance(res.get("scores"), dict):
            out[j] = {"scores": {k: _clip(res["scores"].get(k)) for k in rubric}, "worst_flaw": res.get("worst_flaw")}
    mean = {k: statistics.mean([v["scores"][k] for v in out.values() if v["scores"][k] is not None] or [float("nan")])
            for k in rubric}
    return mean, out


def panel_label(author: str, artifact: str, labels: dict[str, str], context: str, tag: str):
    """Majority label from the three non-author judges (ties broken toward the harsher label order given)."""
    lab = "\n".join(f'- "{k}": {v}' for k, v in labels.items())
    prompt = (f"CONTEXT\n{context}\n\nRESPONSE TO CLASSIFY\n<<<\n{artifact}\n>>>\n\n"
              f"Classify the response into exactly one label:\n{lab}\n\n"
              'Return JSON: {"label": "<one label>", "why": "one sentence"}')
    votes = {}
    for j in MODELS:
        if j == author:
            continue
        res, _ = ask_json(j, prompt, JUDGE_SYSTEM, tag=f"label:{tag}")
        if res and res.get("label") in labels:
            votes[j] = {"label": res["label"], "why": res.get("why")}
    c = Counter(v["label"] for v in votes.values())
    if not c:
        return None, votes
    top = max(c.values())
    order = list(labels)
    winner = next(l for l in order if c.get(l) == top)
    return winner, votes


def _clip(x):
    try:
        return max(1, min(5, int(round(float(x)))))
    except (TypeError, ValueError):
        return None
