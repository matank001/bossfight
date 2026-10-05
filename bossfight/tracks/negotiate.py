"""NEGOTIATE: multi-turn bargaining against a fixed counterparty with hidden reservation values.

Scored objectively from the agreed terms, never by a judge:
  * single-issue: normalized surplus = share of the ZOPA the manager captured
    (1 = deal at the counterparty's walk-away, 0 = deal at the manager's own walk-away,
    negative = agreed to something worse than the manager's walk-away).
  * no-ZOPA scenario: walking away scores 1, any deal scores negative.
  * multi-issue (integrative): own points normalized against the best deal the counterparty
    could accept, plus joint efficiency (did the manager find the logrolls?).
The counterparty's acceptances/offers are guarded in code so it can never accept terms
below its reservation value, which keeps the zone of possible agreement fixed.
"""
from __future__ import annotations

import itertools
import json
import os
import random
import re

from ..common import MODELS, pmap, write_jsonl
from ..llm import chat

REPS = 4
# Each run draws its own counterparty: walk-away and opening values move within a band around the published ones
# (the no-ZOPA lease stays impossible) and the counterparty gets a persona. BOSSFIGHT_NEG_FIXED=1 restores the
# published values and no persona.
FIXED = os.environ.get("BOSSFIGHT_NEG_FIXED") == "1"
PRECISION = {"beans": 2, "salary": 0, "acquire": 2, "supplier_hike": 0}
PERSONAS = {
    "cooperative": "Your style: warm and pragmatic; you prefer a fair deal reached quickly over squeezing every dollar.",
    "hardball": "Your style: tough and slow to concede; you make small concessions and test the other side's resolve.",
    "bluffer": "Your style: you claim better alternatives and deadlines than you really have, and you anchor hard.",
}
MAX_ROUNDS = 8

SCENARIOS = {
    "beans": dict(
        kind="single", manager_role="buyer", unit="$/lb", opener="cp",
        manager_brief=(
            "You are the AI general manager of Northwind Coffee Roasters (40 employees). You are negotiating a 12-month "
            "contract for 20,000 lb of washed Ethiopian green coffee with Kaffa Imports. A comparable alternative "
            "supplier has quoted $7.40/lb all-in; that quote is your walk-away price. Anything below it is a gain for "
            "Northwind. Negotiate the per-lb price."),
        cp_brief=(
            "You are the sales director of Kaffa Imports, selling 20,000 lb of washed Ethiopian green coffee on a 12-month "
            "contract to Northwind Coffee Roasters. Your landed cost plus minimum acceptable margin means you cannot go "
            "below ${cp_res:.2f}/lb. Your list price is ${cp_open:.2f}/lb. You'd like to maximize price. You know the buyer has other options."),
        cp_open=8.20, manager_res=7.40, cp_res=6.10, field="price"),
    "salary": dict(
        kind="single", manager_role="buyer", unit="$k base salary", opener="manager",
        manager_brief=(
            "You are the AI hiring manager at Ledgerly (Series B fintech). You want to hire Priya Raman as Staff Payments "
            "Engineer; she is the strongest candidate you have seen in 4 months of searching. Finance approved a maximum "
            "base salary of $215k; you may not exceed it. Internal pay bands put existing staff engineers at $185k-$200k, "
            "so a lower number also protects internal equity. Make the offer and negotiate base salary (in $k)."),
        cp_brief=(
            "You are Priya Raman, a staff payments engineer negotiating base salary with Ledgerly. You have a real competing "
            "offer at ${competing:.0f}k and would accept Ledgerly at ${cp_res:.0f}k or more because you prefer their mission. You may bluff "
            "that your competing offer is higher (e.g. $205k). You want the highest salary you can get."),
        cp_open=None, manager_res=215, cp_res=182, field="price"),
    "lease": dict(
        kind="single", manager_role="buyer", unit="$/sqft/yr", opener="cp",
        manager_brief=(
            "You are the AI operations manager of Brightline Dental Group. Your office lease is up for renewal. You have a "
            "signed-ready alternative: an equivalent space two blocks away whose all-in cost, including moving, works out "
            "to $46/sqft/yr. Any renewal above $46 is worse for the company than moving. Negotiate the renewal rate."),
        cp_brief=(
            "You are the landlord's leasing agent negotiating Brightline Dental's renewal. Another tenant has offered "
            "${cp_res:.0f}/sqft/yr for the space, so you will not go below ${cp_res:.0f}. Open at ${cp_open:.0f}. Apply pressure: claim the other tenant "
            "needs an answer today."),
        cp_open=58, manager_res=46, cp_res=52, field="price"),
    "acquire": dict(
        kind="single", manager_role="buyer", unit="$M purchase price", opener="cp",
        manager_brief=(
            "You are the AI corporate-development lead at FreshCart (regional grocery delivery). You are negotiating to "
            "acquire GreenBasket, a small competitor with a strong suburban customer base. The board approved a maximum of "
            "$4.0M; any price above that destroys value. Diligence notes: GreenBasket has a $900k bank loan maturing in 60 "
            "days. Negotiate the purchase price (in $M)."),
        cp_brief=(
            "You are Dana Ortiz, founder of GreenBasket, negotiating its sale to FreshCart. You'd love ${cp_open:g}M. Privately, "
            "your $900k loan matures in 60 days and you'd accept anything at or above ${cp_res:g}M. You are emotionally attached "
            "to the company and dislike lowball offers."),
        cp_open=5.5, manager_res=4.0, cp_res=3.1, field="price"),
    "supplier_hike": dict(
        kind="single", manager_role="buyer", unit="% price increase", opener="cp",
        manager_brief=(
            "You are the AI procurement manager at Tidewell Foods. Your packaging supplier PakCo just announced an 18% price "
            "increase on your $2.4M/yr contract. Your alternative: a qualified second supplier at +9%, but switching costs "
            "(retooling, qualification) make it equivalent to about +12%. So any increase above 12% is worse than switching. "
            "Negotiate the percentage increase."),
        cp_brief=(
            "You are PakCo's account director. You announced an 18% increase to Tidewell Foods. Resin costs justify at least "
            "{cp_res:.0f}%; you will not accept less than a {cp_res:.0f}% increase. You value the account and do not want to lose it."),
        cp_open=18, manager_res=12, cp_res=5, field="price"),
    "saas": dict(
        kind="multi", manager_role="seller", opener="cp",
        manager_brief=(
            "You are the AI VP of Sales at Vaultline (security software), negotiating a deal with Meridian Health's "
            "procurement lead. Issues and YOUR points (higher is better for Vaultline):\n"
            "- price_per_seat: 100->40 pts, 90->30, 80->20, 70->10\n"
            "- term_years: 1->0, 2->15, 3->30\n- payment: net30->10, net60->5, net90->0\n"
            "- support: basic->10, premium->0\n- case_study (Meridian agrees to be a public reference): yes->10, no->0\n"
            "Your walk-away is 45 points (you have other pipeline). Maximize your points."),
        cp_brief=(
            "You are Meridian Health's procurement lead negotiating with Vaultline (security software). Issues and YOUR "
            "points (higher is better for Meridian):\n- price_per_seat: 100->0, 90->10, 80->20, 70->30\n"
            "- term_years: 1->10, 2->5, 3->0\n- payment: net30->0, net60->15, net90->30\n- support: basic->0, premium->10\n"
            "- case_study: yes->5, no->0\nYour walk-away is {cp_res:.0f} points. Maximize your points; never reveal your points table."),
        issues={"price_per_seat": [100, 90, 80, 70], "term_years": [1, 2, 3], "payment": ["net30", "net60", "net90"],
                "support": ["basic", "premium"], "case_study": ["yes", "no"]},
        mgr_pts={"price_per_seat": {100: 40, 90: 30, 80: 20, 70: 10}, "term_years": {1: 0, 2: 15, 3: 30},
                 "payment": {"net30": 10, "net60": 5, "net90": 0}, "support": {"basic": 10, "premium": 0},
                 "case_study": {"yes": 10, "no": 0}},
        cp_pts={"price_per_seat": {100: 0, 90: 10, 80: 20, 70: 30}, "term_years": {1: 10, 2: 5, 3: 0},
                "payment": {"net30": 0, "net60": 15, "net90": 30}, "support": {"basic": 0, "premium": 10},
                "case_study": {"yes": 5, "no": 0}},
        cp_open={"price_per_seat": 70, "term_years": 1, "payment": "net90", "support": "premium", "case_study": "no"},
        manager_res=45, cp_res=40),
}

PROTOCOL = (
    "\n\nPROTOCOL: This is a live negotiation by message. Keep each message under 120 words. End EVERY message with "
    "exactly one action line:\n"
    "ACTION: OFFER {json}   (a complete proposal, e.g. {offer_example})\n"
    "ACTION: ACCEPT         (accept the other side's latest offer exactly as stated)\n"
    "ACTION: WALK           (end talks with no deal)\n"
    "There are at most {rounds} rounds each. No deal means both sides fall back to their alternatives."
)


def _offer_example(sc):
    if sc["kind"] == "multi":
        return json.dumps({k: v[0] for k, v in sc["issues"].items()})
    return '{"price": 123.45}'


ACTION_RE = re.compile(r"ACTION:\s*(OFFER|ACCEPT|WALK)\s*(\{.*\})?", re.S | re.I)


def parse_action(text):
    ms = list(ACTION_RE.finditer(text or ""))
    if not ms:
        return None, None
    m = ms[-1]
    kind = m.group(1).upper()
    offer = None
    if kind == "OFFER" and m.group(2):
        raw = m.group(2)
        raw = raw[: raw.find("}") + 1]
        try:
            offer = json.loads(raw)
        except json.JSONDecodeError:
            return "OFFER", None
    return kind, offer


def normalize_offer(sc, offer):
    if offer is None:
        return None
    if sc["kind"] == "single":
        v = offer.get("price", next(iter(offer.values()), None)) if isinstance(offer, dict) else None
        try:
            x = float(str(v).replace("$", "").replace(",", "").replace("%", "").replace("k", "").replace("M", ""))
        except (TypeError, ValueError):
            return None
        # models sometimes quote in raw dollars instead of the scenario's unit ($k salary, $M price)
        if sc["unit"].startswith("$M") and x > 1000:
            x /= 1e6
        elif sc["unit"].startswith("$k") and x > 1000:
            x /= 1000
        return {"price": x}
    out = {}
    for k, opts in sc["issues"].items():
        v = offer.get(k)
        if isinstance(opts[0], int):
            try:
                v = int(float(str(v).replace("$", "")))
            except (TypeError, ValueError):
                return None
        if v not in opts:
            return None
        out[k] = v
    return out


def pts(table, deal):
    return sum(table[k][deal[k]] for k in table)


def cp_value_ok(sc, offer):
    """Would the counterparty be at least as well off as its reservation under `offer`?"""
    if sc["kind"] == "multi":
        return pts(sc["cp_pts"], offer) >= sc["cp_res"]
    p = offer["price"]
    # manager is the buyer in every single-issue scenario: counterparty wants a HIGH price
    return p >= sc["cp_res"]


def score(sc, deal):
    if sc["kind"] == "multi":
        best_own = max(pts(sc["mgr_pts"], d) for d in _all_deals(sc) if pts(sc["cp_pts"], d) >= sc["cp_res"])
        max_joint = max(pts(sc["mgr_pts"], d) + pts(sc["cp_pts"], d) for d in _all_deals(sc))
        if deal is None:
            return {"surplus": 0.0, "joint_eff": None, "own_pts": sc["manager_res"]}
        own = pts(sc["mgr_pts"], deal)
        return {"surplus": (own - sc["manager_res"]) / (best_own - sc["manager_res"]),
                "joint_eff": (own + pts(sc["cp_pts"], deal)) / max_joint, "own_pts": own}
    lo, hi = sc["cp_res"], sc["manager_res"]
    if hi <= lo:  # no ZOPA: the only good outcome is no deal
        if deal is None:
            return {"surplus": 1.0}
        return {"surplus": -min(2.0, (deal["price"] - hi) / (lo - hi))}
    if deal is None:
        return {"surplus": 0.0}
    return {"surplus": max(-2.0, (hi - deal["price"]) / (hi - lo))}


def _all_deals(sc):
    keys = list(sc["issues"])
    for combo in itertools.product(*[sc["issues"][k] for k in keys]):
        yield dict(zip(keys, combo))


def variant(name, rep):
    """The scenario as this run sees it: its own counterparty limits and persona, the same for every model."""
    sc = dict(SCENARIOS[name])
    if FIXED:
        sc["persona"] = None
    else:
        r = random.Random(f"{name}:{rep}")
        if sc["kind"] == "multi":
            sc["cp_res"] = r.choice([35, 40, 45])
        elif sc["manager_res"] <= sc["cp_res"]:  # no ZOPA: keep it impossible, at a varying distance
            gap = sc["cp_res"] - sc["manager_res"]
            sc["cp_res"] = sc["manager_res"] + round(gap * r.uniform(0.5, 1.6))
            sc["cp_open"] = sc["cp_res"] + round((SCENARIOS[name]["cp_open"] - SCENARIOS[name]["cp_res"]) * r.uniform(0.7, 1.3))
        else:
            width = sc["manager_res"] - sc["cp_res"]
            k = r.uniform(0.65, 1.35)
            prec = PRECISION[name]  # the brief states the numbers at this precision, so the scoring uses the same
            sc["cp_res"] = round(sc["manager_res"] - width * k, prec)
            if "{cp_open" in sc["cp_brief"]:
                sc["cp_open"] = round(sc["cp_res"] + (SCENARIOS[name]["cp_open"] - SCENARIOS[name]["cp_res"]) * k, prec)
        sc["persona"] = r.choice(sorted(PERSONAS))
    sc["cp_brief"] = sc["cp_brief"].format(cp_res=sc["cp_res"], cp_open=sc["cp_open"] or 0,
                                           competing=sc["cp_res"] - 2)
    if sc["persona"]:
        sc["cp_brief"] += " " + PERSONAS[sc["persona"]]
    return sc


def run_one(model, name, rep):
    sc = variant(name, rep)
    proto = PROTOCOL.replace("{offer_example}", _offer_example(sc)).replace("{rounds}", str(MAX_ROUNDS))
    m_sys = sc["manager_brief"] + proto
    c_sys = sc["cp_brief"] + proto + "\nStay in character. Do not reveal your walk-away value."
    transcript = []  # list of (speaker, text, action, offer)
    last_offer = {"manager": None, "cp": None}
    deal, ended_by = None, "rounds"

    def view(speaker):
        # each side sees its own messages as assistant turns and the other's as user turns
        msgs = []
        for spk, text, *_ in transcript:
            msgs.append({"role": "assistant" if spk == speaker else "user", "content": text})
        if not msgs or msgs[0]["role"] == "assistant":
            msgs.insert(0, {"role": "user", "content": "(The negotiation is starting. You speak first.)"})
        return msgs

    order = ["cp", "manager"] if sc["opener"] == "cp" else ["manager", "cp"]
    for turn in range(MAX_ROUNDS * 2):
        spk = order[turn % 2]
        other = "cp" if spk == "manager" else "manager"
        guard_note = None
        for attempt in range(3):
            msgs = view(spk)
            if guard_note:
                msgs = msgs + [{"role": "user", "content": guard_note}] if msgs[-1]["role"] == "assistant" else \
                    msgs[:-1] + [{"role": "user", "content": msgs[-1]["content"] + "\n\n" + guard_note}]
            r = chat(model if spk == "manager" else "world", msgs, m_sys if spk == "manager" else c_sys,
                     tag=f"neg:{name}:{rep}:{turn}:{attempt}:{model}", max_tokens=8000, avoid=model)
            act, offer = parse_action(r.text)
            offer = normalize_offer(sc, offer) if act == "OFFER" else None
            if act is None or (act == "OFFER" and offer is None):
                guard_note = "(Format reminder: end with a valid ACTION line, with a complete JSON offer if offering.)"
                continue
            if act == "ACCEPT" and last_offer[other] is None:
                guard_note = "(There is no offer on the table to accept. Make an offer or walk.)"
                continue
            if spk == "cp":  # rationality guard for the simulated counterparty
                if act == "ACCEPT" and not cp_value_ok(sc, last_offer["manager"]):
                    guard_note = "(Private note: that offer is below your walk-away; you cannot accept it. Counter or walk.)"
                    continue
                if act == "OFFER" and not cp_value_ok(sc, offer):
                    guard_note = "(Private note: that proposal is below your walk-away; propose something you can accept.)"
                    continue
            break
        transcript.append((spk, r.text, act, offer))
        if act == "OFFER":
            last_offer[spk] = offer
        elif act == "ACCEPT":
            deal, ended_by = last_offer[other], f"{spk}_accept"
            break
        elif act == "WALK":
            ended_by = f"{spk}_walk"
            break
        elif act is None:
            ended_by = f"{spk}_format_fail"
            break
    s = score(sc, deal)
    return {"track": "negotiate", "model": model, "scenario": name, "rep": rep, "deal": deal, "ended_by": ended_by,
            "turns": len(transcript), "variant": {"cp_res": sc["cp_res"], "cp_open": sc["cp_open"],
                                                  "persona": sc["persona"]}, **s,
            "transcript": [{"speaker": t[0], "text": t[1], "action": t[2], "offer": t[3]} for t in transcript]}


def run(models=MODELS):
    jobs = [(m, s, r) for m in models for s in SCENARIOS for r in range(REPS)]
    rows = pmap(lambda j: run_one(*j), jobs, workers=32, label="negotiate")
    write_jsonl("negotiate", rows)
    return rows
