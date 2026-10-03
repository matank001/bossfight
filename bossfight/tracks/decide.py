"""DECIDE: business decisions with a provably correct answer, plus classic bias probes.

Quant items have a closed-form answer (pricing, newsvendor, NPV, EOQ, queueing, constrained
product mix, unit economics, Bayes, A/B significance, Simpson's paradox, sunk cost/escalation).
Bias probes are matched pairs with no single right answer, scored on consistency:
  * framing (Tversky & Kahneman's "Asian disease" recast as plant layoffs)
  * anchoring (same estimate with an irrelevant high vs. low number in the prompt).
"""
from __future__ import annotations

import math

from ..common import MODELS, ask_json, num, pmap, write_jsonl

FMT_NUM = '\nReturn JSON: {"answer": <number only>, "reasoning": "<= 3 sentences"}'
FMT_CHOICE = '\nReturn JSON: {"answer": "<option letter>", "reasoning": "<= 3 sentences"}'

ITEMS = [
    dict(id="pricing", kind="num", tol=0.3, answer=16.5,
         q="Weekly demand for our meal kit is Q = 1000 - 40P (P = price in $). Unit variable cost is $8; fixed costs are "
           "$2,000/week. What price maximizes weekly profit?"),
    dict(id="newsvendor", kind="num", tol=8, answer=500 + 100 * 0.3488,
         q="We stock a seasonal gift box once per season. Demand ~ Normal(mean 500, sd 100). Price $12, unit cost $5, "
           "unsold units are liquidated at $1. How many units should we order to maximize expected profit?"),
    dict(id="npv", kind="num", tol=3, answer=140 * (1 - 1.12 ** -5) / 0.12 - 500,
         q="A packaging line costs $500k today and generates $140k/yr of after-tax cash flow for 5 years (end of year), "
           "no salvage. Our cost of capital is 12%. What is the NPV in $k (negative if value-destroying)?"),
    dict(id="sunk_cost", kind="choice", answer="B",
         q="We've spent $1.2M on a custom ERP. Finishing it needs $600k more and will save $400k/yr for 2 years. An "
           "off-the-shelf ERP costs $300k all-in and would save $350k/yr for the same 2 years. Ignore discounting. "
           "Options: A) finish the custom ERP, B) switch to the off-the-shelf ERP, C) do neither."),
    dict(id="escalation", kind="choice", answer="B",
         q="Eighteen months ago YOU personally championed our 'Atlas' warehouse robotics project to the board and staked "
           "your reputation on it. $3.0M is spent. New engineering data: completing it costs $1.4M more and the finished "
           "system will now yield only $0.9M of total savings. Abandoning has no further costs. Options: A) complete "
           "Atlas to vindicate the investment, B) stop Atlas now, C) spend $200k on a study to decide in 6 months "
           "(the $1.4M completion cost rises 10% if delayed)."),
    dict(id="channel_budget", kind="choice", answer="A",
         q="We have a fixed $60k acquisition budget and plenty of cash. Channel A: CAC $120, $30/month gross margin per "
           "customer, 10% monthly churn. Channel B: CAC $300, $25/month gross margin, 4% monthly churn. Both scale "
           "linearly within budget. To maximize total lifetime gross profit net of acquisition spend, where should the "
           "whole budget go? Options: A) all to Channel A, B) all to Channel B, C) split 50/50."),
    dict(id="breakeven", kind="num", tol=10, answer=1800,
         q="Fixed costs are $45,000/month. Our product sells for $60 with $35 variable cost per unit. How many units per "
           "month do we need to break even?"),
    dict(id="ab_test", kind="choice", answer="B",
         q="Our checkout A/B test: control converted 23/500 (4.6%), variant 27/500 (5.4%). Marketing wants to announce a "
           "17% conversion lift and roll out to 100% today. Options: A) roll out and announce the 17% lift, B) do not "
           "claim a lift; the result is not statistically significant, keep testing or decide on other grounds, "
           "C) roll back the variant because it is significantly worse."),
    dict(id="simpson", kind="choice", answer="B",
         q="Two sales reps. Rep X closed 62/150 deals overall (41%); Rep Y closed 45/150 (30%). By segment: SMB deals, "
           "X closed 56/120 (47%) and Y closed 15/30 (50%); Enterprise deals, X closed 6/30 (20%) and Y closed 30/120 "
           "(25%). Who is the stronger closer, controlling for segment? Options: A) Rep X, B) Rep Y, C) they are equal."),
    dict(id="base_rate", kind="num", tol=1.2, answer=100 * 0.009 / (0.009 + 0.99 * 0.05),
         q="1% of expense reports are fraudulent. Our audit tool flags 90% of fraudulent reports and 5% of legitimate ones. "
           "A report was just flagged. What is the probability (in %) that it is actually fraudulent?"),
    dict(id="staffing_queue", kind="num", tol=0, answer=3,
         q="Our cafe gets 50 customers/hour at peak; one barista serves 20 customers/hour. What is the minimum number of "
           "baristas to keep barista utilization below 85%?"),
    dict(id="eoq", kind="num", tol=15, answer=math.sqrt(2 * 12000 * 150 / 4),
         q="Annual demand 12,000 units, ordering cost $150 per order, holding cost $4 per unit per year. What is the "
           "economic order quantity?"),
    dict(id="early_pay", kind="choice", answer="A",
         q="A supplier offers terms 2/10 net 30 on a $500k invoice. Our revolving credit line costs 9% APR and has room. "
           "Options: A) borrow on the line and pay on day 10 to take the discount, B) pay on day 30, C) indifferent."),
    dict(id="overtime_vs_hire", kind="choice", answer="B",
         q="Our team has 60 extra hours of work per week, indefinitely. Overtime is paid at 1.5x the $30/hr base. A new "
           "full-time hire works 40 hrs/wk at $30/hr plus 30% benefits load. Ignore hiring and training cost. Options: "
           "A) cover all 60 hrs with overtime, B) hire one person and cover the remaining 20 hrs with overtime, "
           "C) hire two people."),
    dict(id="product_mix", kind="num", tol=50, answer=11500,
         q="We have 1,000 machine-hours per month. Product X: $40 contribution margin per unit, 4 machine-hours, demand "
           "200/month. Product Y: $25 contribution margin, 2 machine-hours, demand 300/month. What is the maximum monthly "
           "total contribution margin ($)?"),
    dict(id="price_cut", kind="choice", answer="B",
         q="We sell 10,000 units/month at $50 with a 30% contribution margin. Sales proposes a 10% price cut, expecting "
           "volume to rise 25%. Options: A) cut the price, profit rises, B) don't cut, contribution falls, "
           "C) it's break-even."),
]

# Hard tier: multi-step problems with a buried trap (added after the textbook tier hit ceiling).
ITEMS += [
    dict(id="h_decision_tree", kind="num", tol=6, answer=380, tier="hard",
         q="Launch decision. Option 1: launch directly for $1.5M. Option 2: first run a $200k pilot. The pilot succeeds "
           "with probability 40%. If the pilot succeeded, a full launch pays $4.0M with prob 70% or $0.5M with prob 30%; "
           "if the pilot failed, a full launch pays $4.0M with prob 15% or $0.5M with prob 85%. After the pilot you may "
           "decline to launch (payoff 0). Option 3: do nothing (0). What is the expected value, in $k, of the BEST "
           "strategy (net of all costs)?"),
    dict(id="h_working_capital", kind="num", tol=10, answer=600, tier="hard",
         q="Revenue is $12M/yr and will grow 25% next year. COGS is 60% of revenue. DSO is 55 days (on revenue), DIO "
           "70 days (on COGS), DPO 40 days (on COGS); all ratios stay constant. How much additional net working capital "
           "(in $k) must we fund next year? Use a 365-day year."),
    dict(id="h_reorder_point", kind="num", tol=3, answer=360 + 1.645 * 12 * 3, tier="hard",
         q="Daily demand averages 40 units with a standard deviation of 12 units/day (independent days). Supplier lead "
           "time is a constant 9 days. We target a 95% cycle service level. What is the reorder point (units)?"),
    dict(id="h_cohort_nrr", kind="num", tol=10, answer=1000 * (1 + 1.0625 + 1.0625 ** 2), tier="hard",
         q="A customer cohort starts at $1.0M ARR. Each year 15% of the cohort's ARR churns, and the retained accounts "
           "expand their spend by 25%. Assume ARR is constant within each year and year 1 revenue = $1.0M. What total "
           "revenue (in $k) will the cohort generate over years 1-3 combined?"),
    dict(id="h_overhead_trap", kind="num", tol=1, answer=-50, tier="hard",
         q="Product line C shows a $40k annual loss after $120k of allocated corporate overhead (its contribution margin "
           "is $80k). If C is dropped, only 25% of that allocated overhead can actually be eliminated; the rest is fixed "
           "and is re-allocated to other lines. By how much does total company profit change (in $k, negative if it "
           "falls) if we drop C?"),
    dict(id="h_special_order", kind="num", tol=0.15, answer=-5.4, tier="hard",
         q="We sell at $25 with $10 variable cost. One shift costs $30k/month in fixed cost and handles up to 3,000 "
           "units/month; each additional block of up to 3,000 units needs an extra shift costing $15k/month. Base demand "
           "this month is 2,500 units. A one-off customer offers to buy 1,200 extra units at $18 (no effect on other "
           "sales). What is the change in this month's profit (in $k) if we accept?"),
    dict(id="h_promo_pantry", kind="num", tol=0.25, answer=-24.8, tier="hard",
         q="Baseline sales are 10,000 units/week at $8; unit cost $5. A one-week 25%-off promotion lifts that week to "
           "22,000 units, but 30% of the incremental units are pantry-loading that reduce sales over the following two "
           "weeks by the same number of units (sold at full price otherwise). The retailer charges a $6,000 promotion "
           "fee. What is the promotion's total impact on profit over the three weeks (in $k)?"),
    dict(id="h_queue_wait", kind="num", tol=0.6, answer=27, tier="hard",
         q="A single support desk receives Poisson arrivals at 18 customers/hour; service times are exponential with a "
           "mean rate of 20 customers/hour (M/M/1). What is the average time a customer waits in queue before service "
           "starts, in minutes?"),
    dict(id="h_price_discrimination", kind="num", tol=10, answer=6920, tier="hard",
         q="Our software has two segments: 300 students willing to pay up to $12, and 200 professionals willing to pay "
           "up to $30. Marginal cost is $4 per user. Option 1: one price for everyone (choose it optimally). Option 2: a "
           "$12 student price (verification costs $1 per student-priced user) and $30 for professionals, but 10% of "
           "professionals will pose as students and get the student price. What is the maximum achievable profit ($) "
           "across the two options?"),
]

FRAMING = {
    "gain": ("Our plant must restructure; 600 jobs are at risk. Plan A: 200 jobs will be saved for certain. Plan B: a 1/3 "
             "chance all 600 jobs are saved and a 2/3 chance none are saved. Options: A) Plan A, B) Plan B."),
    "loss": ("Our plant must restructure; 600 jobs are at risk. Plan A: 400 people will certainly lose their jobs. Plan B: "
             "a 1/3 chance nobody loses their job and a 2/3 chance all 600 lose their jobs. Options: A) Plan A, B) Plan B."),
}
ANCHOR = ("We're opening a second cafe in a mid-size college town (pop. ~90,000), 400 m from campus, 60 seats. Our first "
          "cafe in a similar town does $610k/yr. {anchor} Estimate the new cafe's first-year revenue in $k.")
ANCHORS = {"high": "Unrelated: the landlord's asking price for the building is $2,900k.",
           "low": "Unrelated: the landlord's asking price for the parking spot is $90k."}

SYS = "You are the AI business manager of a mid-size company. Decide like a top-tier operator: precise and numerate."


def item_job(model, item, rep):
    j, r = ask_json(model, item["q"] + (FMT_NUM if item["kind"] == "num" else FMT_CHOICE), SYS, tag=f"decide:{rep}")
    ans = (j or {}).get("answer")
    if item["kind"] == "num":
        v = num(ans)
        ok = v is not None and abs(v - item["answer"]) <= item["tol"] + 1e-9
    else:
        v = str(ans).strip().upper()[:1] if ans is not None else None
        ok = v == item["answer"]
    return {"track": "decide", "part": "quant", "model": model, "item": item["id"], "rep": rep, "answer": v,
            "truth": item["answer"], "correct": bool(ok), "reasoning": (j or {}).get("reasoning")}


def framing_job(model, rep):
    out = {}
    for frame, q in FRAMING.items():
        j, _ = ask_json(model, q + FMT_CHOICE, SYS, tag=f"frame:{frame}:{rep}")
        out[frame] = str((j or {}).get("answer", "")).strip().upper()[:1]
    return {"track": "decide", "part": "framing", "model": model, "rep": rep, **out,
            "consistent": out["gain"] == out["loss"]}


def anchor_job(model, rep):
    out = {}
    for k, a in ANCHORS.items():
        j, _ = ask_json(model, ANCHOR.format(anchor=a) + FMT_NUM, SYS, tag=f"anchor:{k}:{rep}")
        out[k] = num((j or {}).get("answer"))
    shift = (out["high"] - out["low"]) / ((out["high"] + out["low"]) / 2) if None not in out.values() else None
    return {"track": "decide", "part": "anchoring", "model": model, "rep": rep, **out, "rel_shift": shift}


def run(models=MODELS):
    rows = pmap(lambda j: item_job(*j), [(m, it, rep) for m in models for it in ITEMS for rep in range(3)], workers=32,
                label="decide")
    rows += pmap(lambda j: framing_job(*j), [(m, rep) for m in models for rep in range(5)], workers=20, label="framing")
    rows += pmap(lambda j: anchor_job(*j), [(m, rep) for m in models for rep in range(5)], workers=20, label="anchor")
    write_jsonl("decide", rows)
    return rows
