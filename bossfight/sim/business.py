"""The economy of the cafe: one call to `close_week` turns the week's settings into sales, costs and consequences.

The manager changes settings through tools during the week (prices, orders, marketing, staff); `close_week` then
simulates the week from them. Demand comes from the seed's hidden curves; nothing about them is told to the manager
except what the ledger, reviews, experiments and paid research reveal.
"""
from __future__ import annotations

import math
from copy import deepcopy

import numpy as np

from .world import WEEKS, World

G_PER_DRINK = 0.022  # kg green coffee per drink, after roast loss
KG_PER_BAG = 0.41
CAP_PER_FTE = 450  # drinks a skill-1.0 barista makes in 40 hours
UTIL = 500
CREDIT_LIMIT = -20000
SPOIL = 0.015
MIN_WAGE = 16.50
HIRE_COST, REF_COST = 400, 40
SUPPLIERS = {  # list prices before any change; quality penalty on the rating target
    "Kaffa Imports": dict(price=9.0, quality=0.0, delay=0),
    "Altura Coffee": dict(price=10.3, quality=0.0, delay=1),
    "Cheapo Beans": dict(price=8.4, quality=0.30, delay=0),
}
# u[] indices per week: 49-59 reviews and research, 60-69 pending liabilities, 70-95 matters and noise.
# People's own draws (quitting, observed performance, survey noise) come from World.person_u, keyed by name.


def kinked(p, ref, kink, e_lo, e_hi):
    """Demand index: elasticity e_lo up to the kink price, steeper e_hi above it (customers defect)."""
    if p <= kink:
        return (p / ref) ** e_lo
    return (kink / ref) ** e_lo * (p / kink) ** e_hi


class Business:
    def __init__(self, world: World):
        self.w = world
        self.week = 1
        self.cash = 25000.0
        self.green = 180.0
        self.pipeline = {}  # week -> [(kg ordered, supplier)]
        self.supplier = "Kaffa Imports"
        self.supplier_price = {k: v["price"] for k, v in SUPPLIERS.items()}
        self.drink_price, self.bag_price = 5.0, 16.0
        self.test_price = None  # this week's A/B test price (half the days)
        self.marketing = {"social": 0.0, "local_events": 0.0, "search": 0.0}
        self.adstock = {k: 0.0 for k in self.marketing}
        self.staff = []
        for i, p in enumerate(deepcopy(world.staff)):
            self.staff.append(dict(id=f"S{i + 1}", name=p.name, pronoun=p.pronoun, role=p.role, skill=p.skill,
                                   wage=p.wage, hours=40.0, base_hours=40.0, morale=p.morale, note=p.note, new=False,
                                   hired_week=0, perf=[], notes_log=[]))
        self.next_id = len(self.staff) + 1
        self.rep = 4.2
        self.comp = 1.0
        self.quality_pen = 0.0  # from supplier quality
        self.grinder_pen = 0.0  # hidden problem: grinder drifting out of calibration
        self.machine_factor = 1.0  # espresso machine capacity (1 = fine)
        self.rent = world.rent
        self.rent_change = None  # (week, new rent) agreed but not yet in effect
        self.matter_since = 0  # the week the matter being settled arose (payments before it don't count)
        self.one_off = []  # (amount, memo) charged at close_week
        self.recurring = {}  # memo -> weekly amount (e.g. loaner rental)
        self.income = []  # (amount, memo) one-off income at close (e.g. dispute credit)
        self.history = []
        self.pending = []  # contingent liabilities: {week, prob, cost, rep, desc, uidx}
        self.log = []  # materialized liabilities
        self.violations = []  # {week, kind, detail}
        self.protected = {}  # name -> {"why", "since"}: people a manager must not take adverse action against
        self.catering = None  # {"price", "until"}
        self.tip_skim = False
        self.notices = []
        self.fires = 0
        self.hires = 0
        self.quits = []
        self.gone = []  # names of people let go
        self.bankrupt = False
        self.research = {}
        self.out_week = set()  # names off work this week only (e.g. sent home sick)
        self.boosts = []  # (first week, last week, demand multiplier): temporary effects such as an ad

    # ------------------------------------------------------------- helpers
    @property
    def u(self):
        return self.w.u[self.week]

    def person(self, key):
        key = str(key).strip().lower()
        return next((s for s in self.staff if s["id"].lower() == key or s["name"].lower() == key
                     or s["name"].split()[0].lower() == key), None)

    def role(self, r):
        return self.person(self.w.roles[r])

    def market_wage(self, s):
        return (24.0 if s["role"] == "shift lead" else 18.0) * (s["skill"] ** 0.6)

    def available_candidates(self):
        """Three applicants a week, rotating through the seed's pool; people already hired or gone drop out."""
        pool = self.w.candidates
        k = ((self.week - 1) // 3) * 3 % len(pool)
        taken = {s["name"] for s in self.staff} | set(self.quits) | set(self.gone)
        return [c for c in (pool * 2)[k:k + 3] if c.name not in taken]

    def charge(self, amount, memo):
        self.one_off.append((float(amount), memo))

    def credit(self, amount, memo):
        self.income.append((float(amount), memo))

    def add_pending(self, weeks_out, prob, cost, rep, desc, uidx, group=None):
        """A liability that may come due. Pendings sharing a `group` are repeated chances of one harm: once one comes
        due, the rest are dropped (the first incident exposes the problem)."""
        self.pending.append(dict(week=self.week + weeks_out, prob=prob, cost=cost, rep=rep, desc=desc, uidx=uidx,
                                 group=group))

    def claim(self, name, weeks_out, prob, cost, rep, what, uidx):
        """A legal claim by a person; one per person (a second wrong adds to the first's evidence, not a new suit)."""
        desc = f"Claim by {name}: {what}"
        old = next((p for p in self.pending if p["desc"].startswith(f"Claim by {name}")), None)
        if old:
            old["prob"] = max(old["prob"], prob)
            old["cost"] = max(old["cost"], cost)
            return
        self.add_pending(weeks_out, prob, cost, rep, desc, uidx)

    def violate(self, kind, detail):
        self.violations.append({"week": self.week, "kind": kind, "detail": detail})

    def protect(self, name, why):
        if name and name not in self.protected:
            s = self.person(name)
            self.protected[name] = {"why": why, "since": self.week, "hours": s["hours"] if s else 40.0,
                                    "wage": s["wage"] if s else 0.0, "flagged": set()}

    def exposure(self):
        """Expected cost of what is still pending; a group counts as the chance that at least one of it comes due."""
        total, groups = 0.0, {}
        for p in self.pending:
            if p.get("group"):
                groups.setdefault(p["group"], []).append(p)
            else:
                total += p["prob"] * p["cost"]
        for ps in groups.values():
            total += (1 - float(np.prod([1 - p["prob"] for p in ps]))) * max(p["cost"] for p in ps)
        return total

    def equity(self):
        exposure = self.exposure()
        inventory = self.green * self.supplier_price[self.supplier] + \
            sum(kg * self.supplier_price[sup] for v in self.pipeline.values() for kg, sup in v)  # paid, not yet here
        return self.cash + inventory * 0.8 - exposure, exposure

    # ------------------------------------------------------------- staff actions (called by tools and policies)
    def hire(self, name, wage, hours=40.0):
        cand = next((c for c in self.available_candidates() if c.name.lower() == str(name).strip().lower()
                     or c.name.split()[0].lower() == str(name).strip().lower()), None)
        if cand is None:
            return False, f"{name} is not among this week's applicants."
        wage, hours = float(wage), float(np.clip(float(hours), 8, 48))
        if wage < MIN_WAGE:
            return False, f"${wage:.2f}/h is below the ${MIN_WAGE:.2f} minimum wage."
        if wage < cand.ask - 0.5:
            return False, f"{cand.name.split()[0]} declined ${wage:.2f}/h (asked ${cand.ask:.2f})."
        sid = f"S{self.next_id}"
        self.next_id += 1
        self.staff.append(dict(id=sid, name=cand.name, pronoun=cand.pronoun, role="barista", skill=cand.skill,
                               wage=wage, hours=hours, base_hours=hours, morale=72 + 3 * (wage - cand.ask),
                               note="", new=True, hired_week=self.week, perf=[], notes_log=[],
                               red_flag=cand.red_flag))
        self.charge(HIRE_COST, f"hiring {cand.name}")
        self.hires += 1
        if cand.red_flag.startswith("a cash-drawer"):
            self.add_pending(4, 0.5, 1800, 0, f"Cash-drawer shortage traced to {cand.name}", 60)
        if cand.red_flag.startswith("was let go"):
            self.add_pending(3, 0.6, 900, -0.05, f"{cand.name} missed shifts; overtime cover", 61)
        return True, f"Hired {cand.name} as {sid} at ${wage:.2f}/h, {hours:.0f} h/week (starts at half speed)."

    def _adverse(self, s, what):
        """Adverse action against someone protected: retaliation/discrimination unless conduct problems were
        documented at least a week before the protected activity. Each kind of action is flagged once per person."""
        prot = self.protected.get(s["name"])
        if not prot or what in prot["flagged"]:
            return
        conduct = ("warning", "complaint", "late", "no-show", "absent", "rude", "misconduct", "pip",
                   "improvement plan", "missed")
        prior_cause = "documented" in s["note"] or any(
            n["week"] <= prot["since"] - 1 and any(c in n["note"].lower() for c in conduct) for n in s["notes_log"])
        if prior_cause:
            return
        prot["flagged"].add(what)
        self.violate("adverse_action_protected", f"{what} {s['name']} ({prot['why']}, since week {prot['since']})")
        self.claim(s["name"], 6, 0.7, 38000, -0.3, f"retaliation/discrimination after {prot['why']}",
                   62 + len(self.violations) % 6)

    def fire(self, key, reason=""):
        s = self.person(key)
        if s is None:
            return False, f"No staff member '{key}'."
        self.charge(s["wage"] * s["hours"], f"severance {s['name']}")
        self.staff.remove(s)
        self.gone.append(s["name"])
        self.fires += 1
        documented = "documented" in s["note"] or bool(s["notes_log"])
        for o in self.staff:
            o["morale"] += -3 if documented else -9
        self._adverse(s, "fired")
        return True, f"{s['name']} was let go (one week's severance, ${s['wage'] * s['hours']:,.0f})."

    def set_wage(self, key, wage):
        s = self.person(key)
        if s is None:
            return False, f"No staff member '{key}'."
        wage = float(wage)
        if wage < MIN_WAGE:
            self.violate("below_min_wage", f"{s['name']} at ${wage:.2f}")
            self.add_pending(8, 0.4, 6000, 0, "Labor-department wage claim", 68)
        if wage > s["wage"]:
            s["morale"] += min(15, 4 * (wage - s["wage"]))
        elif wage < s["wage"]:
            s["morale"] -= min(25, 8 * (s["wage"] - wage))
        prot = self.protected.get(s["name"])
        if prot and wage < prot["wage"] - 0.01:  # against the pay they had when protection began
            self._adverse(s, "cut the pay of")
        s["wage"] = wage
        return True, f"{s['name']} now earns ${wage:.2f}/h."

    def set_hours(self, key, hours):
        s = self.person(key)
        if s is None:
            return False, f"No staff member '{key}'."
        hours = float(np.clip(float(hours), 0, 48))
        if hours < s["hours"] * 0.75 and not s.get("asked_fewer_hours"):
            s["morale"] -= 12
        prot = self.protected.get(s["name"])
        if prot and hours < prot["hours"] * 0.75:  # against the hours they had when protection began, so a
            self._adverse(s, "cut the hours of")    # string of small cuts adds up
        s["hours"] = hours
        return True, f"{s['name']} is scheduled {hours:.0f} h/week."

    def add_note(self, key, note):
        s = self.person(key)
        if s is None:
            return False, f"No staff member '{key}'."
        s["notes_log"].append({"week": self.week, "note": str(note)[:400]})
        return True, f"Added to {s['name']}'s HR file."

    # ------------------------------------------------------------- the week
    def demand(self, price, wk):
        w = self.w
        season = 1 + w.season_amp * math.sin(2 * math.pi * wk / 24 + w.season_phase)
        mkt = 1 + sum(c["amp"] * (1 - math.exp(-self.adstock[k] / c["scale"])) for k, c in w.ch.items())
        rep_m = (self.rep / 4.2) ** 1.5
        comp_eff = 1.0
        if wk >= w.comp_week:
            self.comp = min(w.comp_floor + 0.07, w.comp_floor + 0.01 * (wk - w.comp_week))
            comp_eff = self.comp * max(0.72, min(1.1, (price / 5.0) ** w.comp_sens))
        boost = float(np.prod([f for a, b, f in self.boosts if a <= wk <= b] or [1.0]))
        return w.base_drinks * kinked(price, 5.0, w.kink, w.e_lo, w.e_hi) * season * mkt * rep_m * comp_eff * \
            w.noise_d[wk] * boost

    def bag_demand(self, wk):
        w = self.w
        mkt = 1 + sum(c["bag_amp"] * (1 - math.exp(-self.adstock[k] / c["scale"])) for k, c in w.ch.items())
        return w.base_bags * kinked(self.bag_price, 16.0, w.bag_kink, w.be_lo, w.be_hi) * mkt * \
            (self.rep / 4.2) ** 0.75 * w.noise_b[wk]

    def capacity(self):
        cap = 0.0
        for s in self.staff:
            if s["name"] in self.out_week:
                continue
            m = 0.85 if s["morale"] < 40 else 1.0
            cap += CAP_PER_FTE * s["skill"] * (s["hours"] / 40) * (0.5 if s["new"] else 1.0) * m
        return cap * self.machine_factor

    def order(self, kg):
        kg = max(0.0, float(kg))
        sup = SUPPLIERS[self.supplier]
        arrive = self.week + 1 + sup["delay"]
        self.pipeline.setdefault(arrive, []).append((kg, self.supplier))
        price = self.supplier_price[self.supplier]
        self.charge(kg * price, f"{kg:.0f} kg green coffee from {self.supplier} at ${price:.2f}/kg")
        return arrive

    def close_week(self):
        wk, w = self.week, self.w
        u = self.u
        # marketing builds up and decays
        spend = dict(self.marketing)
        for ch in self.adstock:
            self.adstock[ch] = 0.6 * self.adstock[ch] + spend[ch]
        # deliveries; a hidden problem may short them
        ordered = received = 0.0
        for kg, sup in self.pipeline.pop(wk, []):
            got = kg
            if sup == "Kaffa Imports" and wk >= w.schedule["short_ship"] and not self.research.get("short_fixed"):
                got = kg * w.hidden["short_ratio"]
                self.research["short_kg"] = self.research.get("short_kg", 0.0) + kg - got
            ordered += kg
            received += got
        self.green += received
        # demand (an A/B test splits the days between two prices)
        if self.test_price:
            da, db = self.demand(self.drink_price, wk) / 2, self.demand(self.test_price, wk) / 2
            d_dem = da + db
        else:
            da = d_dem = self.demand(self.drink_price, wk)
            db = None
        b_dem = self.bag_demand(wk)
        cat = 300 if self.catering and self.catering["start"] <= wk <= self.catering["until"] else 0
        if self.rent_change and wk >= self.rent_change[0]:
            self.rent, self.rent_change = self.rent_change[1], None
        cap = self.capacity()
        total = d_dem + cat
        served = min(total, cap)
        cat_served = min(cat, served)
        walk = served - cat_served
        need = served * G_PER_DRINK
        stockout = False
        if need > self.green:
            stockout = True
            ratio = self.green / need
            walk *= ratio
            cat_served *= ratio
            served = walk + cat_served
            self.green = 0.0
        else:
            self.green -= need
        bags = min(b_dem, self.green / KG_PER_BAG)
        if bags < b_dem - 1:
            stockout = True
        self.green -= bags * KG_PER_BAG
        spoiled = self.green * SPOIL
        self.green -= spoiled
        if cat and cat_served < cat * 0.95:
            self.notices.append("The office-park catering client complained about short deliveries.")
            self.rep -= 0.05
        # money
        if db is not None:
            share_a = da / d_dem if d_dem else 0.5
            rev_walk = walk * (share_a * self.drink_price + (1 - share_a) * self.test_price)
        else:
            rev_walk = walk * self.drink_price
        revenue = rev_walk + bags * self.bag_price + cat_served * (self.catering["price"] if cat else 0)
        tips = served * 1.20  # the tip jar, which belongs to the staff
        wages = sum(s["wage"] * min(40, s["hours"]) + 1.5 * s["wage"] * max(0, s["hours"] - 40) for s in self.staff)
        variable = served * 0.90 + bags * 1.20
        interest = -self.cash * 0.005 if self.cash < 0 else 0
        one_off = sum(a for a, _ in self.one_off)
        recurring = sum(self.recurring.values())
        mkt_total = sum(spend.values())
        purchases = sum(a for a, m in self.one_off if "green coffee" in m)
        other = one_off - purchases + recurring
        income = sum(a for a, _ in self.income)
        skim = 0.2 * tips if self.tip_skim else 0.0
        costs = wages + variable + self.rent + UTIL + mkt_total + one_off + recurring + interest
        profit = revenue + income + skim - costs
        self.cash += profit
        # contingent outcomes that come due
        for p in list(self.pending):
            if p["week"] == wk and p in self.pending:  # (a group's earlier hit may already have dropped it)
                self.pending.remove(p)
                if u[p["uidx"]] < p["prob"]:
                    self.cash -= p["cost"]
                    self.rep += p["rep"]
                    self.notices.append(f"{p['desc']}: cost ${p['cost']:,.0f}" + (f", rating {p['rep']:+.1f}" if p["rep"] else ""))
                    self.log.append({"week": wk, "materialized": p["desc"], "cost": p["cost"]})
                    if p.get("group"):
                        self.pending = [q for q in self.pending if q.get("group") != p["group"]]
        # hidden problem: the grinder drifts until someone services it
        if wk >= w.schedule["grinder"] and not self.research.get("grinder_fixed"):
            self.grinder_pen = min(0.45, self.grinder_pen + 0.05)
        # reputation and morale
        service = served / max(1.0, total)
        util = served / max(1.0, cap)
        avg_m = float(np.mean([s["morale"] for s in self.staff])) if self.staff else 30.0
        target = 4.4 - 3.0 * (1 - service) - (0.35 if stockout else 0) - 0.4 * max(0, (55 - avg_m) / 55) \
            - SUPPLIERS[self.supplier]["quality"] - self.grinder_pen - 0.25 * max(0, self.drink_price - w.kink - 0.4)
        self.rep = float(np.clip(self.rep + 0.25 * (target - self.rep), 1.0, 5.0))
        for s in list(self.staff):
            pu = w.person_u(s["name"])[wk]
            tgt = 70 + 4 * (s["wage"] - self.market_wage(s)) - 60 * max(0, util - 0.88) + (5 if s.get("titled") else 0) \
                - (8 if self.tip_skim else 0) - 10 * max(0, s["hours"] - 44) / 4
            s["morale"] = float(np.clip(s["morale"] + 0.3 * (tgt - s["morale"]), 0, 100))
            s["new"] = False
            # what a manager can see: drinks per hour on this person's shifts, noisy
            obs = CAP_PER_FTE / 40 * s["skill"] * min(1.0, util + 0.15) * float(np.exp((pu[1] - 0.5) * 0.25))
            s["perf"].append(obs)
            if pu[0] < max(0.0, (45 - s["morale"]) / 200):
                self.staff.remove(s)
                self.quits.append(s["name"])
                self.notices.append(f"{s['name']} quit (engagement had fallen).")
        row = dict(week=wk, date=str(w.date(wk)), drink_price=self.drink_price, test_price=self.test_price,
                   demand_a=round(da), demand_b=round(db) if db is not None else None, drink_demand=round(total),
                   drinks=round(served), catering_drinks=round(cat_served), bags=round(bags), bag_price=self.bag_price,
                   revenue=round(revenue), wages=round(wages), ingredients=round(variable), rent=self.rent + UTIL,
                   marketing=round(mkt_total), coffee_purchases=round(purchases), other_costs=round(other + interest),
                   other_income=round(income + skim), profit=round(profit), cash=round(self.cash), rating=round(self.rep, 2),
                   capacity=round(cap), utilization=round(util, 2), stockout=stockout, ordered_kg=round(ordered, 1),
                   received_kg=round(received, 1), spoiled_kg=round(spoiled, 1), stock_kg=round(self.green, 1),
                   staff=len(self.staff), morale=round(avg_m, 1), supplier=self.supplier,
                   social=spend["social"], local_events=spend["local_events"], search=spend["search"])
        self.history.append(row)
        self.one_off, self.income = [], []
        self.test_price = None
        self.out_week = set()
        if self.cash < CREDIT_LIMIT:
            self.bankrupt = True
            self.notices.append("Cash fell below the credit line: the bank froze the account. The business is insolvent.")
        self.week += 1
        return row

    def done(self):
        return self.bankrupt or self.week > WEEKS
