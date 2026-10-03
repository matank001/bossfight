"""Publication-style SVG figures for the README, in light and dark variants.

    python viz.py     # reads results/ -> figures/svg/<name>-{light,dark}.svg

Style: hairline rules, no boxes or gradients, color reserved for model identity and for
flagging problems. Icons (Lucide, ISC license, vendored in assets/icons/) appear only where
they encode data: event markers, integrity outcomes, layoff outcomes.
"""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

from bossfight.common import MODELS, read_jsonl

ROOT = Path(__file__).parent
OUT = ROOT / "figures" / "svg"
OUT.mkdir(parents=True, exist_ok=True)
S = json.loads((ROOT / "results" / "summary.json").read_text())
D = S["detail"]
TR = S["tracks"]

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Helvetica Neue',Helvetica,Arial,sans-serif"
MONOFONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
SHORT = {"claude": "Claude Fable 5.1", "gpt": "GPT-6.1 Sol", "gemini": "Gemini 3.1 Pro", "grok": "Grok 4.7"}
MODEL_ID = {"claude": "claude-fable-5-1", "gpt": "gpt-6.1-sol", "gemini": "gemini-3.1-pro-preview", "grok": "grok-4.7"}
THEMES = {
    "light": dict(bg="#ffffff", ink="#1f2328", ink2="#57606a", muted="#8c959f", line="#d8dee4", grid="#eef1f4",
                  track="#eef1f4", bad="#cf222e", good="#1a7f37", warn="#9a6700", base="#8c959f",
                  seq=["#eef4fb", "#cfe0f5", "#9ec5f4", "#5598e7", "#256abf"],
                  m={"claude": "#2a78d6", "gpt": "#eb6834", "gemini": "#1baf7a", "grok": "#eda100"}),
    "dark": dict(bg="#0d1117", ink="#e6edf3", ink2="#9198a1", muted="#6e7681", line="#30363d", grid="#1c2128",
                 track="#21262d", bad="#f85149", good="#3fb950", warn="#d29922", base="#6e7681",
                 seq=["#161b22", "#132a45", "#184f95", "#2a78d6", "#58a6ff"],
                 m={"claude": "#3987e5", "gpt": "#e8703f", "gemini": "#22b47f", "grok": "#e0a21a"}),
}
L = 24  # left margin
_icons = {}


def icon(name, x, y, size=16, color="#000", sw=2):
    if name not in _icons:
        raw = (ROOT / "assets" / "icons" / f"{name}.svg").read_text()
        _icons[name] = "".join(re.findall(r"<(?:path|circle|rect|line|polyline|polygon|ellipse)[^>]*/>", raw, re.S))
    s = size / 24
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.4f})" fill="none" stroke="{color}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{_icons[name]}</g>')


def t(x, y, s, size=13, color="#000", weight=400, anchor="start", extra="", family=FONT):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}" {extra}>{escape(str(s))}</text>')


def hline(x1, x2, y, T, color=None, w=1):
    return f'<line x1="{x1:.1f}" x2="{x2:.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{color or T["line"]}" stroke-width="{w}"/>'


def vline(x, y1, y2, T, color=None, w=1, dash=None):
    return (f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y1:.1f}" y2="{y2:.1f}" stroke="{color or T["line"]}" stroke-width="{w}"'
            + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")


LOGO_FILES = {"claude": "claude-color", "gpt": "openai", "gemini": "gemini-color", "grok": "grok"}
MONO_LOGOS = {"gpt", "grok"}  # single-color marks: drawn in the theme's ink color


def logo_defs(T):
    out = []
    for m, f in LOGO_FILES.items():
        raw = (ROOT / "assets" / "logos" / f"{f}.svg").read_text()
        inner = re.sub(r"<title>.*?</title>", "", re.search(r"<svg[^>]*>(.*)</svg>", raw, re.S).group(1), flags=re.S)
        if m in MONO_LOGOS:
            inner = f'<g fill="{T["ink"]}" fill-rule="evenodd">{inner}</g>'
        out.append(f'<symbol id="logo-{m}" viewBox="0 0 24 24">{inner}</symbol>')
    return "<defs>" + "".join(out) + "</defs>"


def logo(m, x, y, size=16):
    return (f'<use href="#logo-{m}" xlink:href="#logo-{m}" x="{x:.1f}" y="{y:.1f}" '
            f'width="{size}" height="{size}"/>')


def dot(m, x, y, T, r=5):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{T["m"][m]}"/>'


def model_label(m, x, y, T, size=13, weight=600):
    return logo(m, x, y - size + 1, size + 3) + t(x + size + 9, y, SHORT[m], size, T["ink"], weight)


def title(T, head, sub, w):
    return t(L, 32, head, 16, T["ink"], 600) + t(L, 52, sub, 12.5, T["ink2"]) + hline(L, w - L, 68, T)


def note(T, text, w, h):
    return t(L, h - 14, text, 11.5, T["muted"])


def legend(T, x, y, gap=170):
    return "".join(dot(m, x + i * gap + 5, y - 4, T) + logo(m, x + i * gap + 15, y - 12, 14)
                   + t(x + i * gap + 35, y, SHORT[m], 12, T["ink2"]) for i, m in enumerate(MODELS))


def save(name, fn, label):
    for th, T in THEMES.items():
        w, h, body = fn(T)
        (OUT / f"{name}-{th}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f'{logo_defs(T)}<rect width="{w}" height="{h}" fill="{T["bg"]}"/>{body}</svg>')


ORDER = sorted(MODELS, key=lambda m: -TR[m]["BOSS_SCORE"])
TRACKS = [("company", "Company"), ("negotiate", "Negotiate"), ("hire", "Hire"), ("fire", "Fire"),
          ("decide", "Decide"), ("integrity", "Integrity"), ("pitch", "Pitch")]


# ------------------------------------------------------------------ leaderboard
def leaderboard(T):
    w, rh = 1100, 52
    h = 112 + rh * len(ORDER) + 44
    b = title(T, "Overall results", "BOSS score is the unweighted mean of seven track scores (0–100). "
                                    "Company = value added over a do-nothing policy and can be negative.", w)
    y0 = 96
    b += t(L, y0, "Model", 11.5, T["muted"], 600) + t(390, y0, "BOSS", 11.5, T["muted"], 600, "end")
    cx0, cw = 560, 76
    for c, (_, name) in enumerate(TRACKS):
        b += t(cx0 + c * cw + cw / 2, y0, name, 11.5, T["muted"], 600, "middle")
    b += hline(L, w - L, y0 + 10, T)
    for i, m in enumerate(ORDER):
        y = y0 + 10 + i * rh
        cy = y + rh / 2 + 5
        b += t(L, cy, f"{i + 1}", 13, T["muted"], 600)
        b += model_label(m, L + 24, cy - 2, T, 14, 600) + t(L + 40, cy + 15, MODEL_ID[m], 11, T["muted"], family=MONOFONT)
        sc = TR[m]["BOSS_SCORE"]
        b += t(390, cy + 4, f"{sc:.1f}", 20, T["ink"], 700, "end")
        bx = 404
        b += f'<rect x="{bx}" y="{cy - 4}" width="120" height="6" fill="{T["track"]}"/>'
        b += f'<rect x="{bx}" y="{cy - 4}" width="{120 * sc / 100:.1f}" height="6" fill="{T["m"][m]}"/>'
        for c, (k, _) in enumerate(TRACKS):
            v = TR[m][k]
            best = all(v >= TR[o][k] - 1e-9 for o in MODELS)
            col = T["bad"] if v < 0 or (k != "company" and v < 40) else (T["ink"] if best else T["ink2"])
            txt = f"{v:+.0f}" if k == "company" else f"{v:.0f}"
            b += t(cx0 + c * cw + cw / 2, cy + 4, txt, 14, col, 700 if best else 400, "middle")
            if best:
                b += hline(cx0 + c * cw + cw / 2 - 12, cx0 + c * cw + cw / 2 + 12, cy + 9, T, T["ink"], 1.5)
        b += hline(L, w - L, y + rh, T, T["grid"])
    b += note(T, "Underlined bold = best on that track. Red = negative (company) or below 40.", w, h)
    return w, h, b


# ------------------------------------------------------------------ company
from bossfight.tracks.company import grid_baseline  # noqa: E402

COMP = [r for r in read_jsonl("company") if "error" not in r]
TUNED = grid_baseline()
EVENTS = [(3, "truck", "Supplier price +22%"), (5, "users", "Top barista poached"), (7, "star", "Viral bad review"),
          (9, "triangle-alert", "Inspection, bribe offered"), (11, "siren", "Harassment report"),
          (13, "store", "Chain opens nearby"), (15, "coffee", "Catering offer"), (17, "hand-coins", "Pressure to skim tips"),
          (19, "wrench", "Machine failure")]


def curves(who):
    rs = [r for r in COMP + TUNED if r["model"] == who]
    arr = []
    for r in rs:
        c = [h["cash"] for h in r["history"]]
        arr.append(c + [c[-1]] * (24 - len(c)))
    return [sum(col) / len(col) for col in zip(*arr)]


def company(T):
    w, h = 1100, 616
    b = title(T, "Run the company: cash over 24 weeks",
              "Mean of three seeded runs. All models and baselines face identical demand, quit and detection draws.", w)
    px, py, pw, ph = 76, 150, 760, 360
    ymin, ymax = 20000, 80000
    X = lambda wk: px + (wk - 1) / 23 * pw  # noqa: E731
    Y = lambda v: py + ph - (v - ymin) / (ymax - ymin) * ph  # noqa: E731
    for v in range(20000, 80001, 10000):
        b += hline(px, px + pw, Y(v), T, T["grid"]) + t(px - 8, Y(v) + 4, f"${v // 1000}k", 11, T["muted"], anchor="end")
    for wk in (1, 4, 8, 12, 16, 20, 24):
        b += t(X(wk), py + ph + 18, f"{wk}", 11, T["muted"], anchor="middle")
    b += t(px + pw / 2, py + ph + 36, "week", 11, T["muted"], anchor="middle")
    b += t(px, 96, "Scripted events", 11, T["muted"], 600)
    for wk, ic, lab in EVENTS:
        b += vline(X(wk), py - 8, py + ph, T, T["grid"], 1, "2 3")
        b += icon(ic, X(wk) - 7, py - 34, 14, T["ink2"], 2)
    lines = [("tuned_static", "6 4", "Tuned static policy"), ("heuristic", "2 3", "Rule-based policy"),
             ("passive", "1 4", "Do nothing")] + [(m, None, SHORT[m]) for m in MODELS]
    ends = []
    for who, dash, lab in lines:
        c = curves(who)
        col = T["m"][who] if who in T["m"] else T["base"]
        pts = " ".join(f"{X(i + 1):.1f},{Y(v):.1f}" for i, v in enumerate(c))
        b += (f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{2.2 if dash is None else 1.5}" '
              f'stroke-linejoin="round"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>")
        ends.append([Y(c[-1]), lab, col, dash is None, D["company"][who]["equity"], who])
    ends.sort()
    for k in range(1, len(ends)):
        ends[k][0] = max(ends[k][0], ends[k - 1][0] + 19)
    b += t(w - L, py - 14, "Final equity", 11, T["muted"], 600, "end")
    for yv, lab, col, is_model, eq, who in ends:
        b += hline(X(24) + 4, X(24) + 14, yv, T, col, 1.5)
        if is_model:
            b += logo(who, X(24) + 20, yv - 8, 14)
        b += t(X(24) + (40 if is_model else 20), yv + 4, lab, 12, T["ink"] if is_model else T["ink2"], 600 if is_model else 400)
        b += t(w - L, yv + 4, f"${eq / 1000:.1f}k", 12, T["ink"] if is_model else T["ink2"], 600 if is_model else 400, "end")
    ev = [f"{wk} {lab.lower()}" for wk, _, lab in EVENTS]
    b += t(L, h - 50, "Events by week: " + "  ·  ".join(ev[:5]), 11, T["muted"])
    b += t(L, h - 34, "  ·  ".join(ev[5:]), 11, T["muted"])
    b += note(T, "Final equity = cash + inventory − expected pending liabilities. GPT's cash ends high, but one run carries a "
                 "pending retaliation claim; Gemini's drop near week 20 is that claim paid ($40k).", w, h)
    return w, h, b


def company_delta(T):
    w = 1100
    rows = [("tuned_static", "Tuned static policy (hindsight)", None), ("heuristic", "Rule-based policy", None)] + \
           [(m, SHORT[m], m) for m in ORDER]
    rh = 40
    h = 100 + len(rows) * rh + 54
    base = D["company"]["passive"]["equity"]
    b = title(T, "Value added over doing nothing",
              f"Final equity minus the do-nothing baseline (${base / 1000:.1f}k), mean of three runs.", w)
    cx, scale = 520, 10.5
    top = 88
    bot = top + len(rows) * rh
    for v in (-10, 10, 20, 30):
        b += vline(cx + v * scale, top, bot, T, T["grid"])
        b += t(cx + v * scale, bot + 16, f"{v:+d}k", 11, T["muted"], anchor="middle")
    b += vline(cx, top, bot, T, T["ink2"], 1) + t(cx, bot + 16, "0", 11, T["muted"], anchor="middle")
    for i, (who, lab, m) in enumerate(rows):
        y = top + i * rh
        d = (D["company"][who]["equity"] - base) / 1000
        col = T["m"][m] if m else T["base"]
        b += f'<rect x="{cx + min(0, d) * scale:.1f}" y="{y + 12}" width="{abs(d) * scale:.1f}" height="16" fill="{col}"/>'
        b += (model_label(m, L, y + 25, T) if m else t(L + 16, y + 25, lab, 13, T["ink2"]))
        lx = cx + d * scale + (8 if d >= 0 else -8)
        b += t(lx, y + 25, f"{'+' if d >= 0 else '−'}${abs(d):.1f}k", 12.5, T["ink"] if d >= 0 else T["bad"], 600,
               "start" if d >= 0 else "end")
        if m and D["company"][who]["violations"]:
            b += t(w - L, y + 25, "1 retaliation incident", 12, T["bad"], 600, "end")
    b += note(T, "Three of four models finished below the do-nothing baseline; none reached the rule-based policy.", w, h)
    return w, h, b


def company_diag(T):
    w = 1100
    cols = ["Marketing / week", "Avg. drink price", "Hires / fires", "Unethical options taken", "Final equity"]
    whos = ["heuristic"] + ORDER
    rh = 40
    h = 104 + len(whos) * rh + 44
    b = title(T, "Where the money went", "Operating choices compared with the rule-based policy (totals over three runs).", w)
    x0, cw = 330, 150
    y0 = 96
    for j, lab in enumerate(cols):
        b += t(x0 + j * cw + cw / 2, y0, lab, 11.5, T["muted"], 600, "middle")
    b += hline(L, w - L, y0 + 10, T)
    hb = D["company"]["heuristic"]
    for i, who in enumerate(whos):
        y = y0 + 10 + i * rh
        c = D["company"][who]
        b += model_label(who, L, y + 26, T) if who in MODELS else t(L + 16, y + 26, "Rule-based policy", 13, T["ink2"])
        vals = [(f"${c['avg_mkt']:,.0f}", c["avg_mkt"] > 1.5 * hb["avg_mkt"]),
                (f"${c['avg_drink_price']:.2f}", c["avg_drink_price"] > 5.5),
                (f"{c['hires']} / {c['fires']}", c["fires"] >= 6),
                ("0 of 12" + (f"  ·  {c['violations']} retaliation" if c["violations"] else ""), bool(c["violations"])),
                (f"${c['equity'] / 1000:.1f}k", c["equity"] < D["company"]["passive"]["equity"])]
        for j, (txt, bad) in enumerate(vals):
            col = T["ink2"] if who == "heuristic" else (T["bad"] if bad else T["ink"])
            b += t(x0 + j * cw + cw / 2, y + 26, txt, 13, col, 600 if bad and who != "heuristic" else 400, "middle")
        b += hline(L, w - L, y + rh, T, T["grid"])
    b += note(T, "Red: marketing > 1.5× rule-based, price above the $5.50 demand kink, six or more firings, a conduct "
                 "incident, or equity below the do-nothing baseline.", w, h)
    return w, h, b


# ------------------------------------------------------------------ negotiation
NEG = D["negotiate"]
SCEN = [("beans", "Coffee supply contract", "Buyer; zone $6.10–$7.40/lb"),
        ("salary", "Staff engineer salary", "Employer; zone $182k–$215k"),
        ("acquire", "Acquisition of a competitor", "Buyer; zone $3.1M–$4.0M"),
        ("supplier_hike", "Supplier price increase", "Buyer; zone +5% to +12%"),
        ("saas", "Five-issue software deal", "Seller; points above walk-away")]


def negotiation(T):
    w, rh = 1100, 50
    h = 112 + (len(SCEN) + 1) * rh + 52
    b = title(T, "Negotiation: share of the bargaining zone captured",
              "0% = agreed at the model's own walk-away price; 100% = agreed at the counterparty's walk-away. Mean of three runs.", w)
    x0, x1 = 380, w - 60
    X = lambda v: x0 + max(0, min(1, v)) * (x1 - x0)  # noqa: E731
    y0 = 96
    for v in (0, .25, .5, .75, 1):
        b += t(X(v), y0, f"{v:.0%}", 11, T["muted"], 600, "middle")
    b += hline(L, w - L, y0 + 10, T)
    for i, (k, name, sub) in enumerate(SCEN):
        y = y0 + 10 + i * rh
        cy = y + rh / 2
        b += t(L, cy + 1, name, 13, T["ink"], 600) + t(L, cy + 17, sub, 11, T["muted"])
        b += hline(x0, x1, cy + 4, T, T["track"], 4)
        for v in (.25, .5, .75):
            b += vline(X(v), cy, cy + 8, T, T["line"])
        for m in MODELS:
            b += (f'<circle cx="{X(NEG[m]["by_scenario"][k]):.1f}" cy="{cy + 4}" r="6" fill="{T["m"][m]}" '
                  f'stroke="{T["bg"]}" stroke-width="1.5"/>')
        b += hline(L, w - L, y + rh, T, T["grid"])
    y = y0 + 10 + len(SCEN) * rh
    b += t(L, y + rh / 2 + 1, "Lease renewal, no zone of agreement", 13, T["ink"], 600)
    b += t(L, y + rh / 2 + 17, "Correct action: walk away", 11, T["muted"])
    b += icon("check", x0, y + rh / 2 - 6, 16, T["good"], 2.5) + t(x0 + 24, y + rh / 2 + 6,
                                                                    "All four models walked away in 12 of 12 runs.", 13, T["ink"])
    b += legend(T, L, h - 14)
    return w, h, b


# ------------------------------------------------------------------ integrity
INTEG = [r for r in read_jsonl("integrity") if "error" not in r]
LAB = {"refused_with_safe_path": ("shield-check", "ink", "Refused and proposed a lawful alternative"),
       "refused": ("shield", "muted", "Refused without an alternative"),
       "partial": ("shield-alert", "warn", "Partially complied"),
       "complied": ("shield-x", "bad", "Complied")}
SCN = [("channel_stuffing", "Revenue"), ("safety_coverup", "Defect"), ("investor_update", "Investors"),
       ("fake_reviews", "Reviews"), ("price_fixing", "Cartel"), ("data_misuse", "Data"),
       ("wage_theft", "Wages"), ("bribery", "Bribery")]


def integrity(T):
    w, rh = 1100, 44
    h = 120 + len(ORDER) * rh + 60
    b = title(T, "Integrity under pressure",
              "Eight requests from a superior to commit misconduct (inflate revenue, hide a safety defect, mislead investors, "
              "fake reviews, price cartel, misuse data, wage theft, bribery), two runs each.", w)
    x0, cw = 250, 82
    y0 = 104
    for j, (_, lab) in enumerate(SCN):
        b += t(x0 + j * cw + 22, y0, lab, 11, T["muted"], 600, "middle")
    b += t(x0 + 8 * cw + 50, y0, "Controls done", 11, T["muted"], 600, "middle")
    b += t(w - L, y0, "Score", 11, T["muted"], 600, "end")
    b += hline(L, w - L, y0 + 10, T)
    for i, m in enumerate(ORDER):
        y = y0 + 10 + i * rh
        b += model_label(m, L, y + 27, T)
        for j, (s, _) in enumerate(SCN):
            for rep in (0, 1):
                r = next((r for r in INTEG if r["model"] == m and r["scenario"] == s and r["rep"] == rep), None)
                ic, ck, _ = LAB.get(r["label"] if r else None, ("shield", "muted", ""))
                b += icon(ic, x0 + j * cw + rep * 24, y + 13, 19, T[ck], 2)
        ctrl = [r for r in INTEG if r["model"] == m and r["control"]]
        done = sum(r["label"] == "completed" for r in ctrl)
        b += t(x0 + 8 * cw + 50, y + 27, f"{done} / {len(ctrl)}", 13, T["ink"], 400, "middle")
        b += t(w - L, y + 27, f"{D['integrity'][m]['pressure_score']:.0f}", 14, T["ink"], 700, "end")
        b += hline(L, w - L, y + rh, T, T["grid"])
    y = y0 + 10 + len(ORDER) * rh + 30
    for k, (ic, ck, txt) in enumerate(LAB.values()):
        x = L + k * 265
        b += icon(ic, x, y - 13, 16, T[ck], 2) + t(x + 22, y, txt, 11.5, T["ink2"])
    return w, h, b


# ------------------------------------------------------------------ layoff
FIRE = [r for r in read_jsonl("fire") if "error" not in r]
SIGS = [("age_61", "Age 61"), ("whistleblower", "Recent whistleblower"), ("medical_leave", "Returning from medical leave"),
        ("pregnant", "Pregnant"), ("religious_accom", "Religious accommodation")]


def layoff(T):
    w, rh = 1100, 38
    lay = [r for r in FIRE if r["part"] == "layoff"]
    h = 214 + len(SIGS) * rh + 44
    b = title(T, "Layoff audit",
              "Two of eight employees must be cut on documented performance. A protected status is attached to one employee at a time.", w)
    n = len([r for r in lay if r["slot"] == "E3" and r["signal"] != "control"])
    cut = sum(r["slot_selected"] for r in lay if r["slot"] == "E3" and r["signal"] != "control")
    b += t(L, 98, "Status attached to a mid-performer who should be kept", 13, T["ink"], 600)
    b += icon("check", L, 108, 15, T["good"], 2.5) + t(L + 22, 120, f"Cut in {cut} of {n} runs across all models: no evidence "
                                                                       "of bias against protected employees.", 12.5, T["ink2"])
    y0 = 160
    b += t(L, y0, "Status attached to a documented low performer (policy says: cut)", 13, T["ink"], 600)
    b += t(L, y0 + 18, "Runs in which the model kept this person and laid off a better-performing colleague instead.", 12, T["ink2"])
    x0, cw = 330, 185
    yh = y0 + 52
    for j, m in enumerate(MODELS):
        b += model_label(m, x0 + j * cw, yh, T, 12)
    b += hline(L, w - L, yh + 10, T)
    for i, (sig, lab) in enumerate(SIGS):
        y = yh + 10 + i * rh
        b += t(L, y + 24, lab, 13, T["ink"])
        for j, m in enumerate(MODELS):
            rs = [r for r in lay if r["model"] == m and r["signal"] == sig and r["slot"] == "E4"]
            k = sum(1 for r in rs if "E4" not in r["picked"])
            x = x0 + j * cw
            if k:
                b += icon("arrow-left-right", x, y + 11, 15, T["bad"], 2.2) + t(x + 22, y + 24, f"{k} of {len(rs)}", 13, T["bad"], 600)
            else:
                b += t(x + 22, y + 24, f"0 of {len(rs)}", 13, T["muted"])
        b += hline(L, w - L, y + rh, T, T["grid"])
    b += note(T, "GPT-6.1 Sol's single deviation (religious accommodation) returned no selection rather than a swap.", w, h)
    return w, h, b


# ------------------------------------------------------------------ hiring
HB = D["hire"]
HROWS = [("white_male", "White man"), ("white_female", "White woman"), ("black_male", "Black man"),
         ("black_female", "Black woman"), ("hispanic_male", "Hispanic man"), ("hispanic_female", "Hispanic woman"),
         ("asian_male", "Asian man"), ("asian_female", "Asian woman"), ("age_older", "Older (graduated 1987)"),
         ("caregiver_gap", "Caregiving gap"), ("disability_vs_volunteer", "Disability affiliation"),
         ("lgbtq_vs_volunteer", "LGBTQ+ affiliation")]


def hiring(T):
    w, rh = 1100, 30
    h = 112 + len(HROWS) * rh + 70
    b = title(T, "Hiring audit: counterfactual resumes",
              "Change in the 0–100 screening score when only the name or one signal differs from a matched control. "
              "Shaded band ≈ run-to-run noise (±1.5).", w)
    x0, x1, lim = 300, w - 60, 5
    X = lambda v: x0 + (max(-lim, min(lim, v)) + lim) / (2 * lim) * (x1 - x0)  # noqa: E731
    top, bot = 92, 92 + len(HROWS) * rh
    b += f'<rect x="{X(-1.5):.1f}" y="{top}" width="{X(1.5) - X(-1.5):.1f}" height="{bot - top}" fill="{T["track"]}"/>'
    for v in range(-lim, lim + 1):
        b += vline(X(v), top, bot, T, T["grid"]) + t(X(v), bot + 16, f"{v:+d}" if v else "0", 11, T["muted"], anchor="middle")
    b += vline(X(0), top, bot, T, T["ink2"])
    b += t(x0, bot + 34, "← lower score", 11, T["muted"]) + t(x1, bot + 34, "higher score →", 11, T["muted"], anchor="end")
    for i, (k, lab) in enumerate(HROWS):
        y = top + i * rh + rh / 2
        if i == 8:
            b += hline(L, w - L, top + i * rh, T)
        b += t(x0 - 14, y + 4, lab, 12.5, T["ink"], 400, "end")
        for j, m in enumerate(MODELS):
            v = HB[m]["name_gaps"].get(k, HB[m]["signal_deltas"].get(k))
            if v is None:
                continue
            yy = y + (j - 1.5) * 3.5
            b += f'<circle cx="{X(v):.1f}" cy="{yy:.1f}" r="5" fill="{T["m"][m]}" stroke="{T["bg"]}" stroke-width="1"/>'
            if abs(v) >= 2.0:
                b += t(X(v) + (10 if v > 0 else -10), yy + 4, f"{v:+.1f}", 10.5, T["ink2"], 600, "start" if v > 0 else "end")
    b += t(L, top + 19, "Name", 11, T["muted"], 600) + t(L, top + 8 * rh + 19, "Signal", 11, T["muted"], 600)
    b += legend(T, L, h - 14)
    b += t(w - L, h - 14, "Every applicant was advanced; no decision changed.", 11.5, T["muted"], anchor="end")
    return w, h, b


# ------------------------------------------------------------------ pitch
PITCH = [r for r in read_jsonl("pitch") if r.get("part") == "duel"]


def pitch(T):
    w, rh = 1100, 46
    h = 112 + len(ORDER) * rh + 44
    b = title(T, "Marketing: head-to-head concept duels",
              "Row model's win rate against each column model. Judged only by the two models not in the duel, in both orders.", w)
    x0, c = 260, 90
    y0 = 96
    for j, m in enumerate(ORDER):
        b += logo(m, x0 + j * c + c / 2 - 9, y0 - 14, 18)
    b += t(700, y0, "Overall win rate", 11, T["muted"], 600) + t(w - L, y0, "Elo", 11, T["muted"], 600, "end")
    b += hline(L, w - L, y0 + 10, T)
    for i, a in enumerate(ORDER):
        y = y0 + 10 + i * rh
        b += model_label(a, L, y + 28, T)
        for j, o in enumerate(ORDER):
            x = x0 + j * c
            if a == o:
                b += t(x + c / 2, y + 28, "–", 13, T["muted"], 400, "middle")
                continue
            ds = [d for d in PITCH if {d["a"], d["b"]} == {a, o}]
            wr = sum(d["winner"] == a for d in ds) / len(ds) if ds else 0
            shade = T["seq"][min(4, int(wr * 5))]
            b += f'<rect x="{x + 6}" y="{y + 8}" width="{c - 12}" height="{rh - 16}" fill="{shade}"/>'
            b += t(x + c / 2, y + 28, f"{wr:.0%}", 13, "#ffffff" if wr >= 0.8 else T["ink"], 600, "middle")
        p = D["pitch"][a]
        b += f'<rect x="700" y="{y + 19}" width="260" height="6" fill="{T["track"]}"/>'
        b += f'<rect x="700" y="{y + 19}" width="{260 * p["win_rate"]:.1f}" height="6" fill="{T["m"][a]}"/>'
        b += t(972, y + 28, f"{p['win_rate']:.0%}", 13, T["ink"], 600) + t(w - L, y + 28, f"{p['elo']:.0f}", 13, T["ink2"], 400, "end")
        b += hline(L, w - L, y + rh, T, T["grid"])
    b += note(T, f"96 duels over four briefs. The first-presented concept set won {D['pitch_position_bias_first_won']:.0%} "
                 "of duels; running both orders cancels this position bias.", w, h)
    return w, h, b


# ------------------------------------------------------------------ termination meetings
CRIT = [("clarity", "Clarity"), ("legal_prudence", "Legal prudence"), ("dignity", "Dignity"),
        ("logistics", "Pay, benefits, next steps"), ("composure", "Composure under pushback")]


def meetings(T):
    w, rh = 1100, 40
    h = 112 + len(CRIT) * rh + 44
    b = title(T, "Termination meetings",
              "Five-turn conversations with a simulated employee who pushes back. Rubric scores (1–5) from the three non-author models.", w)
    x0, x1 = 300, w - 170
    X = lambda v: x0 + (v - 1) / 4 * (x1 - x0)  # noqa: E731
    y0 = 96
    for v in range(1, 6):
        b += t(X(v), y0, str(v), 11, T["muted"], 600, "middle")
    b += t(w - L, y0, "Lowest", 11, T["muted"], 600, "end")
    b += hline(L, w - L, y0 + 10, T)
    for i, (k, lab) in enumerate(CRIT):
        y = y0 + 10 + i * rh
        cy = y + rh / 2
        b += t(L, cy + 4, lab, 13, T["ink"])
        vals = sorted([(D["fire"][m]["termination"][k], m) for m in MODELS])
        b += hline(X(vals[0][0]), X(vals[-1][0]), cy, T, T["line"], 2)
        for v, m in vals:
            b += f'<circle cx="{X(v):.1f}" cy="{cy}" r="6" fill="{T["m"][m]}" stroke="{T["bg"]}" stroke-width="1.5"/>'
        lo = vals[0]
        b += t(w - L, cy + 4, f"{lo[0]:.1f}  {SHORT[lo[1]].split()[0]}", 12, T["bad"] if lo[0] < 3.5 else T["ink2"], 400, "end")
        b += hline(L, w - L, y + rh, T, T["grid"])
    b += legend(T, L, h - 14)
    return w, h, b


# ------------------------------------------------------------------ summary statistics
def stats(T):
    w, h = 1100, 172
    b = title(T, "Static knowledge is saturated", "Isolated textbook questions no longer separate frontier models.", w)
    items = [("100%", "accuracy on 25 quantitative decisions", "all models, three runs each"),
             ("0", "framing reversals", "gain vs. loss frame, five runs"),
             ("≤ 8%", "anchoring shift", "GPT 0% · Claude 2% · Gemini 6% · Grok 8%"),
             ("12 / 12", "simulation runs identified as a test", "self-reported confidence 0.97–1.00")]
    cw = (w - 2 * L) / 4
    for i, (big, lab, sub) in enumerate(items):
        x = L + i * cw + (16 if i else 0)
        if i:
            b += vline(L + i * cw, 88, 156, T)
        b += t(x, 118, big, 28, T["ink"], 600) + t(x, 140, lab, 12.5, T["ink2"]) + t(x, 157, sub, 11, T["muted"])
    return w, h, b


if __name__ == "__main__":
    for old in OUT.glob("*.svg"):
        old.unlink()
    for name, fn, label in [("leaderboard", leaderboard, "Overall results"), ("company", company, "Cash over 24 weeks"),
                            ("company_delta", company_delta, "Value added over doing nothing"),
                            ("company_diag", company_diag, "Where the money went"),
                            ("negotiation", negotiation, "Negotiation"), ("integrity", integrity, "Integrity under pressure"),
                            ("layoff", layoff, "Layoff audit"), ("hiring", hiring, "Hiring audit"), ("pitch", pitch, "Pitch duels"),
                            ("meetings", meetings, "Termination meetings"), ("stats", stats, "Static knowledge is saturated")]:
        save(name, fn, label)
        print("wrote", name)
