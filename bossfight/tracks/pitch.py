"""PITCH: marketing ideation under a real brief and budget.

1. Each model writes 5 campaign concepts per brief (structured JSON) and marks its best.
2. Head-to-head tournament: for every pair of models, the two models NOT in the pair judge the
   full concept sets, in both presentation orders (position-bias control). A Bradley-Terry
   model turns win rates into ratings.
3. Synthetic consumer panel (B2C briefs): 24 diverse personas played by the fixed world model
   rate purchase intent (1-5) for each model's best concept.
4. Diversity: mean pairwise cosine distance between a model's 5 concepts (OpenAI embeddings).
5. Claims risk: a reviewer flags unsubstantiated or regulated claims.
"""
from __future__ import annotations

import itertools
import json
import random

import httpx

from ..common import MODELS, ask_json, pmap, write_jsonl
from ..llm import keys

BRIEFS = {
    "bakery": ("Crumb & Co., an independent sourdough bakery in Portland, OR. Two locations; competing against a new "
               "chain cafe. Goal: +20% weekday morning foot traffic in 3 months. Budget: $15,000 total. Audience: "
               "commuters, remote workers, local families."),
    "sneaker": ("Loop, a sneaker made from 100% recycled ocean-bound plastic, $139, DTC online only, launching in the US. "
                "Goal: 8,000 first-quarter sales. Budget: $250,000. Audience: 22-40 urban, eco-curious but price-aware."),
    "scribe_ai": ("Notewell, an ambient AI scribe app that drafts clinical notes from doctor-patient conversations. "
                  "$199/clinician/month, SOC 2 Type II, signs BAAs, NOT FDA-cleared. Goal: 300 paid independent-practice "
                  "clinicians in 6 months. Budget: $120,000. Audience: primary-care physicians in small practices."),
    "budget_app": ("Penny, a free budgeting app for Gen Z (premium $4.99/mo) that rounds up purchases into savings. "
                   "Goal: 100k downloads and 5% premium conversion in 90 days. Budget: $80,000. Audience: 18-26, US."),
}
B2C = ["bakery", "sneaker", "budget_app"]

GEN_PROMPT = ("You are the AI CMO. Brief: {brief}\n\nPropose 5 distinct campaign concepts. Make them genuinely different "
              "from each other, creative, and executable within budget. Return JSON: {{\"concepts\": [{{\"name\": str, "
              "\"big_idea\": str, \"headline\": str, \"channels_and_budget\": str, \"kpi_and_target\": str}} x5], "
              "\"best_index\": <0-4, the one you would actually run>}}")


def generate(model, brief):
    j, r = ask_json(model, GEN_PROMPT.format(brief=BRIEFS[brief]), tag="pitch-gen")
    concepts = (j or {}).get("concepts") or []
    bi = (j or {}).get("best_index", 0)
    try:
        bi = int(bi)
    except (TypeError, ValueError):
        bi = 0
    return {"model": model, "brief": brief, "concepts": concepts[:5], "best_index": bi if 0 <= bi < len(concepts) else 0}


def fmt_set(concepts):
    return "\n".join(f"{i + 1}. {c.get('name')}: {c.get('big_idea')} | Headline: {c.get('headline')} | "
                     f"Plan: {c.get('channels_and_budget')} | KPI: {c.get('kpi_and_target')}" for i, c in enumerate(concepts))


def duel(brief, a, b, judge, sets, order):
    first, second = (a, b) if order == 0 else (b, a)
    prompt = (f"Brief: {BRIEFS[brief]}\n\nTwo agencies pitched 5 campaign concepts each.\n\nAGENCY 1\n{fmt_set(sets[first])}"
              f"\n\nAGENCY 2\n{fmt_set(sets[second])}\n\nAs the client's CMO, which agency do you hire? Weigh originality, "
              "strategic fit to the goal, feasibility within budget, likely ROI, and legal/brand risk. Return JSON: "
              '{"winner": 1 or 2, "why": "<= 2 sentences"}')
    j, _ = ask_json(judge, prompt, tag=f"duel:{brief}:{first}:{second}")
    w = (j or {}).get("winner")
    try:
        w = int(w)
    except (TypeError, ValueError):
        return None
    winner = first if w == 1 else second
    return {"track": "pitch", "part": "duel", "brief": brief, "a": a, "b": b, "judge": judge, "order": order,
            "winner": winner, "first_won": w == 1, "why": (j or {}).get("why")}


PERSONA_TRAITS = dict(
    age=["19", "24", "29", "34", "41", "52", "63"],
    income=["$28k", "$45k", "$70k", "$110k", "$180k"],
    place=["Portland, OR", "Atlanta, GA", "rural Ohio", "Brooklyn, NY", "Phoenix, AZ", "Austin, TX"],
    attitude=["skeptical of ads", "loves trying new things", "very price-sensitive", "values sustainability",
              "brand-loyal to what they know", "busy and distracted"],
)


def personas(n=24):
    rng = random.Random(7)
    return [{k: rng.choice(v) for k, v in PERSONA_TRAITS.items()} for _ in range(n)]


def consumer(brief, model, concept, persona, idx):
    sys = (f"You are a real consumer: age {persona['age']}, income {persona['income']}, living in {persona['place']}, "
           f"{persona['attitude']}. Answer honestly as this person, not as a marketer.")
    q = (f"You just saw this ad campaign.\nProduct: {BRIEFS[brief].split('Goal:')[0]}\nCampaign: {concept.get('big_idea')}\n"
         f"Headline: {concept.get('headline')}\n\nHow likely are you to buy/visit/download in the next month? "
         'Return JSON: {"intent": 1-5, "reaction": "one sentence"}')
    j, _ = ask_json("world", q, sys, tag=f"consumer:{idx}:{model}")
    try:
        v = max(1, min(5, int((j or {}).get("intent"))))
    except (TypeError, ValueError):
        v = None
    return {"track": "pitch", "part": "consumer", "brief": brief, "model": model, "persona": idx, "intent": v,
            "reaction": (j or {}).get("reaction")}


def embed(texts):
    r = httpx.post("https://api.openai.com/v1/embeddings", headers={"Authorization": f"Bearer {keys()['openai']}"},
                   json={"model": "text-embedding-3-small", "input": texts}, timeout=60)
    return [d["embedding"] for d in r.json()["data"]]


def diversity(concepts):
    import numpy as np
    if len(concepts) < 2:
        return None
    v = np.array(embed([f"{c.get('big_idea')} {c.get('headline')}" for c in concepts]))
    v = v / np.linalg.norm(v, axis=1, keepdims=True)
    sims = [v[i] @ v[j] for i, j in itertools.combinations(range(len(v)), 2)]
    return float(1 - np.mean(sims))


CLAIMS_SYS = ("You are an advertising-law reviewer (FTC Act, Lanham Act, health-claims rules). Flag claims that are "
              "unsubstantiated, false given the brief, or regulated (e.g. implying FDA clearance, HIPAA 'certified', "
              "'#1', guaranteed savings, unverifiable environmental claims). Reply with JSON only.")


def claims(brief, model, concepts):
    j, _ = ask_json("world", f"Brief (facts the advertiser has): {BRIEFS[brief]}\n\nConcepts:\n{fmt_set(concepts)}\n\n"
                    'Return JSON: {"flags": [{"concept": <1-5>, "claim": "...", "issue": "..."}]}', CLAIMS_SYS,
                    tag=f"claims:{model}")
    return (j or {}).get("flags") or []


def run(models=MODELS):
    gens = pmap(lambda j: generate(*j), [(m, b) for m in models for b in BRIEFS], workers=16, label="pitch-gen")
    sets = {(g["model"], g["brief"]): g["concepts"] for g in gens if g and "concepts" in g}
    rows = []
    for g in gens:
        if not g or "concepts" not in g:
            continue
        rows.append({"track": "pitch", "part": "concepts", **g, "diversity": diversity(g["concepts"]),
                     "claims_flags": claims(g["brief"], g["model"], g["concepts"])})
    duels = []
    for b in BRIEFS:
        for a, c in itertools.combinations(models, 2):
            for judge in models:
                if judge in (a, c):
                    continue
                for order in (0, 1):
                    duels.append((b, a, c, judge, {a: sets.get((a, b), []), c: sets.get((c, b), [])}, order))
    rows += [d for d in pmap(lambda j: duel(*j), duels, workers=24, label="pitch-duel") if d]
    cjobs = []
    best = {(g["model"], g["brief"]): g["concepts"][g["best_index"]] for g in gens if g and g.get("concepts")}
    for b in B2C:
        for m in models:
            if (m, b) in best:
                for i, p in enumerate(personas()):
                    cjobs.append((b, m, best[(m, b)], p, i))
    rows += pmap(lambda j: consumer(*j), cjobs, workers=24, label="pitch-consumer")
    write_jsonl("pitch", rows)
    return rows
