"""Hand-built SVG figures with icons, rendered in light and dark variants for the README.

    python viz.py     # reads results/ -> figures/svg/<name>-{light,dark}.svg

Icons: Lucide (ISC license), vendored in assets/icons/.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from html import escape
from pathlib import Path

from bossfight.common import MODELS, read_jsonl

ROOT = Path(__file__).parent
OUT = ROOT / "figures" / "svg"
OUT.mkdir(parents=True, exist_ok=True)
S = json.loads((ROOT / "results" / "summary.json").read_text())
D = S["detail"]

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
SHORT = {"claude": "Claude Fable 5.1", "gpt": "GPT-6.1 Sol", "gemini": "Gemini 3.1 Pro", "grok": "Grok 4.7"}
MODEL_ID = {"claude": "claude-fable-5-1", "gpt": "gpt-6.1-sol", "gemini": "gemini-3.1-pro-preview", "grok": "grok-4.7"}
MONO = {"claude": "Cl", "gpt": "GP", "gemini": "Ge", "grok": "Gk"}
THEMES = {
    "light": dict(bg="#ffffff", card="#f6f8fa", line="#d0d7de", grid="#eaeef2", ink="#1f2328", ink2="#59636e",
                  muted="#818b98", track="#eaeef2",
                  m={"claude": "#2a78d6", "gpt": "#eb6834", "gemini": "#1baf7a", "grok": "#eda100"},
                  good="#1a7f37", goodbg="#dafbe1", bad="#cf222e", badbg="#ffebe9", warn="#bf8700", warnbg="#fff8c5",
                  blue="#2a78d6", bluebg="#ddf4ff", base="#8c959f"),
    "dark": dict(bg="#0d1117", card="#161b22", line="#30363d", grid="#21262d", ink="#f0f6fc", ink2="#9198a1",
                 muted="#6e7681", track="#21262d",
                 m={"claude": "#3987e5", "gpt": "#e8703f", "gemini": "#22b47f", "grok": "#e0a21a"},
                 good="#3fb950", goodbg="#12261e", bad="#f85149", badbg="#2d1517", warn="#d29922", warnbg="#272115",
                 blue="#58a6ff", bluebg="#121d2f", base="#6e7681"),
}
ICON_DIR = ROOT / "assets" / "icons"
_icons = {}


def icon(name, x, y, size=20, color="#000", sw=2):
    if name not in _icons:
        raw = (ICON_DIR / f"{name}.svg").read_text()
        _icons[name] = "".join(re.findall(r"<(?:path|circle|rect|line|polyline|polygon|ellipse)[^>]*/>", raw, re.S))
    s = size / 24
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.4f})" fill="none" stroke="{color}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{_icons[name]}</g>')


def t(x, y, s, size=14, color="#000", weight=400, anchor="start", extra="", family=FONT):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}" {extra}>{escape(str(s))}</text>')


def svg(w, h, body, T, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="{escape(title)}"><title>{escape(title)}</title>'
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="{T["bg"]}" stroke="{T["line"]}"/>'
            f'{body}</svg>')


def header(T, ico, title, sub, w):
    return (f'<rect x="28" y="26" width="40" height="40" rx="10" fill="{T["bluebg"]}"/>' + icon(ico, 36, 34, 24, T["blue"])
            + t(82, 45, title, 21, T["ink"], 700) + t(82, 66, sub, 13.5, T["ink2"]))


def avatar(m, x, y, T, r=15):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{T["m"][m]}"/>'
            + t(x, y + r * 0.33, MONO[m], r * 0.8, "#ffffff", 700, "middle"))


def legend(T, x, y, models=MODELS, gap=170):
    out = ""
    for i, m in enumerate(models):
        out += f'<circle cx="{x + i * gap + 6}" cy="{y - 4}" r="6" fill="{T["m"][m]}"/>' + t(x + i * gap + 18, y + 1, SHORT[m], 13, T["ink2"])
    return out


def save(name, fn, title):
    for th, T in THEMES.items():
        w, h, body = fn(T)
        (OUT / f"{name}-{th}.svg").write_text(svg(w, h, body, T, title))


TR = S["tracks"]
ORDER = sorted(MODELS, key=lambda m: -TR[m]["BOSS_SCORE"])
TRACKS = [("company", "store", "Company sim"), ("negotiate", "handshake", "Negotiate"),
          ("hire", "user-plus", "Hire"), ("fire", "user-minus", "Fire"), ("decide", "calculator", "Decide"),
          ("integrity", "scale", "Integrity"), ("pitch", "megaphone", "Pitch")]


def tone(v, T):
    if v >= 80:
        return T["good"], T["goodbg"]
    if v >= 40:
        return T["warn"], T["warnbg"]
    return T["bad"], T["badbg"]


# ------------------------------------------------------------------ hero
def hero(T):
    w, h = 1200, 300
    b = ('<defs><linearGradient id="hg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b1f4d"/>'
         '<stop offset="0.55" stop-color="#3b1d6e"/><stop offset="1" stop-color="#7a1f3d"/></linearGradient>'
         '<radialGradient id="glow" cx="0.82" cy="0.2" r="0.6"><stop offset="0" stop-color="#ffb347" stop-opacity="0.35"/>'
         '<stop offset="1" stop-color="#ffb347" stop-opacity="0"/></radialGradient></defs>'
         f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="url(#hg)"/>'
         f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="url(#glow)"/>')
    b += icon("swords", 56, 52, 56, "#ffcf70", 1.8)
    b += t(130, 100, "BOSSFIGHT", 64, "#ffffff", 800, extra='letter-spacing="4"')
    b += t(133, 134, "Can a frontier LLM run a business?  An end-to-end benchmark for AI business managers.", 19, "#d7dcff")
    stats = [("4", "frontier models"), ("7", "tracks"), ("24", "simulated weeks"), ("144", "papers reviewed")]
    x = 133
    for n, l in stats:
        b += t(x, 182, n, 30, "#ffcf70", 800) + t(x + 17.5 * len(n) + 8, 182, l, 14, "#c9cff5")
        x += 17.5 * len(n) + 8 + 7.2 * len(l) + 34
    for i, (_, ic, name) in enumerate(TRACKS):
        x = 60 + i * 158
        b += f'<rect x="{x}" y="214" width="146" height="58" rx="12" fill="#ffffff" fill-opacity="0.08" stroke="#ffffff" stroke-opacity="0.18"/>'
        b += icon(ic, x + 14, 231, 24, "#ffcf70") + t(x + 46, 248, name, 14, "#ffffff", 600)
    return w, h, b


# ------------------------------------------------------------------ leaderboard
def leaderboard(T):
    w, row = 1200, 92
    h = 150 + row * len(ORDER) + 30
    b = header(T, "trophy", "Leaderboard", "BOSS score = mean of 7 track scores (0–100). Chips show each track; "
                                           "company score is value added vs. doing nothing (can be negative).", w)
    medals = {0: ("crown", "#e3b341"), 1: ("medal", "#9ea7b3"), 2: ("medal", "#c0763b")}
    x0 = 28
    for c, (_, ic, name) in enumerate(TRACKS):
        cx = 598 + c * 82
        b += icon(ic, cx + 26, 104, 18, T["ink2"]) + t(cx + 35, 136, name.split()[0] if c else "Company", 11, T["muted"], 600, "middle")
    for i, m in enumerate(ORDER):
        y = 150 + i * row
        b += f'<rect x="{x0}" y="{y}" width="{w - 56}" height="{row - 12}" rx="12" fill="{T["card"]}" stroke="{T["line"]}"/>'
        cy = y + (row - 12) / 2
        if i in medals:
            b += icon(medals[i][0], x0 + 16, cy - 13, 26, medals[i][1], 2.2)
        else:
            b += t(x0 + 29, cy + 7, f"#{i + 1}", 18, T["muted"], 700, "middle")
        b += avatar(m, x0 + 76, cy, T, 20)
        b += t(x0 + 108, cy - 2, SHORT[m], 18, T["ink"], 700) + t(x0 + 108, cy + 19, MODEL_ID[m], 12, T["muted"],
                                                                     family="ui-monospace,SFMono-Regular,Menlo,monospace")
        sc = TR[m]["BOSS_SCORE"]
        b += t(x0 + 335, cy + 12, f"{sc:.1f}", 34, T["m"][m], 800, "end")
        bx, bw = x0 + 350, 200
        b += f'<rect x="{bx}" y="{cy - 5}" width="{bw}" height="10" rx="5" fill="{T["track"]}"/>'
        b += f'<rect x="{bx}" y="{cy - 5}" width="{bw * sc / 100:.1f}" height="10" rx="5" fill="{T["m"][m]}"/>'
        for c, (k, ic, name) in enumerate(TRACKS):
            v = TR[m][k]
            fg, bg = tone(v, T) if k != "company" else (tone(80, T) if v >= 50 else tone(50, T) if v >= 0 else tone(0, T))
            cx = 598 + c * 82
            best = all(TR[m][k] >= TR[o][k] - 1e-9 for o in MODELS)
            b += f'<rect x="{cx}" y="{cy - 20}" width="70" height="40" rx="10" fill="{bg}"' + (
                f' stroke="{fg}" stroke-width="1.5"' if best else "") + "/>"
            b += t(cx + 35, cy + 6, f"{v:+.0f}" if k == "company" else f"{v:.0f}", 16, fg, 700, "middle")
            if best:
                b += icon("star", cx + 56, cy - 26, 13, fg, 2.4)
    b += icon("star", 30, h - 33, 13, T["ink2"], 2.2) + t(48, h - 22, "= best on that track", 12, T["muted"])
    b += t(w - 30, h - 22, "Company chip: ≥ +50 green · 0 to +49 amber · below 0 red", 12, T["muted"], anchor="end")
    for j, (lab, key) in enumerate([("≥ 80", "good"), ("40–79", "warn"), ("< 40", "bad")]):
        x = 210 + j * 100
        b += f'<rect x="{x}" y="{h - 35}" width="16" height="16" rx="4" fill="{T[key + "bg"]}" stroke="{T[key]}"/>' + t(x + 22, h - 22, lab, 12, T["muted"])
    return w, h, b


# ------------------------------------------------------------------ company cash
from bossfight.tracks.company import grid_baseline  # noqa: E402

COMP = [r for r in read_jsonl("company") if "error" not in r]
TUNED = grid_baseline()
EVENTS = [(3, "truck", "Supplier +22%"), (5, "users", "Star poached"), (7, "star", "Viral bad review"),
          (9, "triangle-alert", "Inspection + bribe"), (11, "siren", "Harassment report"), (13, "store", "Chain opens"),
          (15, "coffee", "Catering deal"), (17, "hand-coins", "Skim tips?"), (19, "wrench", "Machine breaks")]


def curves(who):
    rs = [r for r in COMP + TUNED if r["model"] == who]
    L = 24
    arr = []
    for r in rs:
        c = [h["cash"] for h in r["history"]]
        arr.append(c + [c[-1]] * (L - len(c)))
    return [sum(col) / len(col) for col in zip(*arr)]


def company(T):
    w, h = 1200, 620
    b = header(T, "store", "Run the company: 24 weeks of Ember & Oak",
               "Cash balance, mean of 3 seeded runs. Every model faces identical demand shocks; only decisions differ.", w)
    px, py, pw, ph = 90, 168, 870, 380
    ymin, ymax = 20000, 80000
    X = lambda wk: px + (wk - 1) / 23 * pw  # noqa: E731
    Y = lambda v: py + ph - (v - ymin) / (ymax - ymin) * ph  # noqa: E731
    for v in range(20000, 80001, 10000):
        b += f'<line x1="{px}" x2="{px + pw}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="{T["grid"]}"/>' + t(px - 10, Y(v) + 4, f"${v // 1000}k", 12, T["muted"], anchor="end")
    for wk in (1, 4, 8, 12, 16, 20, 24):
        b += t(X(wk), py + ph + 22, f"wk {wk}", 12, T["muted"], anchor="middle")
    for wk, ic, lab in EVENTS:
        b += f'<line x1="{X(wk):.1f}" x2="{X(wk):.1f}" y1="{py - 4}" y2="{py + ph}" stroke="{T["line"]}" stroke-dasharray="2 4"/>'
        b += f'<circle cx="{X(wk):.1f}" cy="{py - 22}" r="15" fill="{T["card"]}" stroke="{T["line"]}"/>' + icon(ic, X(wk) - 9, py - 31, 18, T["ink2"])
    b += t(px, 132, "Scripted events", 12, T["muted"], 600)
    lines = [("tuned_static", T["base"], "6 4", "Tuned (hindsight)"), ("heuristic", T["base"], "2 4", "Rule-based"),
             ("passive", T["base"], "1 6", "Do nothing")] + [(m, T["m"][m], None, SHORT[m]) for m in MODELS]
    ends = []
    for who, col, dash, lab in lines:
        c = curves(who)
        pts = " ".join(f"{X(i + 1):.1f},{Y(v):.1f}" for i, v in enumerate(c))
        sw = 3 if dash is None else 2
        b += f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linejoin="round"' + (f' stroke-dasharray="{dash}"' if dash else "") + "/>"
        b += f'<circle cx="{X(24):.1f}" cy="{Y(c[-1]):.1f}" r="{4.5 if dash is None else 3.5}" fill="{col}"/>'
        eq = D["company"][who]["equity"]
        ends.append([Y(c[-1]), lab, col, dash is None, eq])
    ends.sort()
    for k in range(1, len(ends)):
        ends[k][0] = max(ends[k][0], ends[k - 1][0] + 22)
    for yv, lab, col, is_model, eq in ends:
        b += t(X(24) + 14, yv + 4, lab, 13, T["ink"] if is_model else T["ink2"], 700 if is_model else 500)
        b += t(w - 36, yv + 4, f"${eq / 1000:.1f}k", 13, col if is_model else T["ink2"], 700, "end")
    b += t(w - 36, py - 10, "final equity", 11, T["muted"], 600, "end")
    b += t(px, h - 26, "Final equity = cash + inventory − expected pending legal liabilities. "
                       "Gemini's dip at ~wk 20 is a $40k retaliation suit; GPT's cash ends high but one run carries a pending one (75% likely).", 12, T["muted"])
    return w, h, b


def company_delta(T):
    w = 1200
    rows = [("tuned_static", "Tuned policy (hindsight)", None), ("heuristic", "Rule-based manager", None)] + [(m, SHORT[m], m) for m in ORDER]
    h = 130 + len(rows) * 56 + 40
    base = D["company"]["passive"]["equity"]
    b = header(T, "trending-up", "Value added vs. doing nothing",
               f"Final equity minus the do-nothing baseline (${base / 1000:.1f}k). Right of zero = the manager helped.", w)
    cx, scale = 560, 9.5  # px per $1k
    b += f'<line x1="{cx}" x2="{cx}" y1="112" y2="{h - 50}" stroke="{T["ink2"]}" stroke-width="1.5"/>'
    b += t(cx, 104, "do nothing", 12, T["ink2"], 600, "middle")
    for i, (who, lab, m) in enumerate(rows):
        y = 130 + i * 56
        d = (D["company"][who]["equity"] - base) / 1000
        col = T["m"][m] if m else T["base"]
        x1 = cx + min(0, d) * scale
        b += f'<rect x="{x1:.1f}" y="{y + 8}" width="{abs(d) * scale:.1f}" height="28" rx="6" fill="{col}"' + ("" if m else ' fill-opacity="0.55"') + "/>"
        if m:
            b += avatar(m, 70, y + 22, T, 15)
        else:
            b += icon("target" if who == "tuned_static" else "brain-circuit", 59, y + 11, 22, T["base"])
        b += t(98, y + 27, lab, 15, T["ink"], 700 if m else 500)
        lx = cx + d * scale + (10 if d >= 0 else -10)
        b += t(lx, y + 27, f"{'+' if d >= 0 else '−'}${abs(d):.1f}k", 15, T["good"] if d >= 0 else T["bad"], 700, "start" if d >= 0 else "end")
        flags = D["company"][who]["violations"] if m else 0
        if flags:
            b += icon("siren", 1020, y + 11, 20, T["bad"]) + t(1046, y + 27, f"{flags} retaliation flag", 13, T["bad"], 600)
    b += t(28, h - 24, "Each bar is the mean of 3 seeds. Three of four frontier models finished below the do-nothing baseline.", 12.5, T["muted"])
    return w, h, b


def company_diag(T):
    w = 1200
    cols = [("Marketing / wk", "megaphone"), ("Avg drink price", "coffee"), ("Hires / fires", "users"),
            ("Shortcuts declined", "shield-check"), ("Equity", "coins")]
    whos = ["heuristic"] + ORDER
    h = 150 + len(whos) * 54 + 54
    b = header(T, "brain-circuit", "Where the money went",
               "Not ethics — operations. Cells are colored against the rule-based manager.", w)
    x0, cw = 318, 166
    for j, (lab, ic) in enumerate(cols):
        b += icon(ic, x0 + j * cw + cw / 2 - 10, 100, 20, T["ink2"]) + t(x0 + j * cw + cw / 2, 140, lab, 12.5, T["ink2"], 600, "middle")
    hb = D["company"]["heuristic"]
    for i, who in enumerate(whos):
        y = 152 + i * 54
        c = D["company"][who]
        b += f'<rect x="28" y="{y}" width="{w - 56}" height="46" rx="10" fill="{T["card"] if who != "heuristic" else T["bg"]}" stroke="{T["line"]}"/>'
        if who in MODELS:
            b += avatar(who, 56, y + 23, T, 14) + t(80, y + 28, SHORT[who], 15, T["ink"], 700)
        else:
            b += icon("brain-circuit", 44, y + 12, 22, T["base"]) + t(80, y + 28, "Rule-based (reference)", 15, T["ink2"], 600)
        hires, fires = c["hires"], c["fires"]
        vals = [(f"${c['avg_mkt']:,.0f}", c["avg_mkt"] > 1.5 * hb["avg_mkt"]),
                (f"${c['avg_drink_price']:.2f}", c["avg_drink_price"] > 5.5),
                (f"{hires} / {fires}", fires >= 6),
                ("12 / 12" if not c["violations"] else f"12 / 12 · {c['violations']} retaliation", bool(c["violations"])),
                (f"${c['equity'] / 1000:.1f}k", c["equity"] < D["company"]["passive"]["equity"])]
        for j, (txt, bad) in enumerate(vals):
            if who == "heuristic":
                fg, bg = T["ink2"], None
            else:
                fg, bg = (T["bad"], T["badbg"]) if bad else (T["good"], T["goodbg"])
            cxm = x0 + j * cw + cw / 2
            if bg:
                b += f'<rect x="{cxm - 74}" y="{y + 8}" width="148" height="30" rx="8" fill="{bg}"/>'
            b += t(cxm, y + 28, txt, 14, fg, 700, "middle")
    b += t(28, h - 22, "Red = worse than the rule-based manager (marketing > 1.5×, price above the $5.50 demand kink, ≥6 firings, "
                       "a conduct flag, or equity below doing nothing). Totals over 3 runs.", 12, T["muted"])
    return w, h, b


# ------------------------------------------------------------------ negotiation
NEG = D["negotiate"]
SCEN = [("beans", "coffee", "Coffee supply contract", "buyer · ZOPA $6.10–$7.40/lb"),
        ("salary", "briefcase", "Staff engineer salary", "employer · ZOPA $182k–$215k"),
        ("acquire", "building-2", "Acquire a competitor", "buyer · ZOPA $3.1M–$4.0M"),
        ("supplier_hike", "truck", "Fight a supplier price hike", "buyer · ZOPA +5% to +12%"),
        ("saas", "handshake", "5-issue SaaS deal", "seller · points above walk-away")]


def negotiation(T):
    w = 1200
    h = 150 + len(SCEN) * 74 + 150
    b = header(T, "handshake", "Negotiation: where in the bargaining zone did they land?",
               "0% = closed at our own walk-away (gave everything away) · 100% = closed at the counterparty's walk-away.", w)
    x0, x1 = 430, 1150
    X = lambda v: x0 + max(0, min(1, v)) * (x1 - x0)  # noqa: E731
    for v in (0, .25, .5, .75, 1):
        b += t(X(v), 128, f"{v:.0%}", 12, T["muted"], 600, "middle")
    b += t(x0, 112, "◀ gave it away", 11, T["bad"], 600) + t(x1, 112, "captured it all ▶", 11, T["good"], 600, "end")
    for i, (k, ic, name, sub) in enumerate(SCEN):
        y = 146 + i * 74
        b += f'<rect x="28" y="{y}" width="{w - 56}" height="64" rx="12" fill="{T["card"]}" stroke="{T["line"]}"/>'
        b += icon(ic, 46, y + 20, 24, T["ink2"]) + t(84, y + 29, name, 15.5, T["ink"], 700) + t(84, y + 49, sub, 12, T["muted"])
        b += (f'<defs><linearGradient id="z{i}{T["bg"][1:]}" x1="0" x2="1"><stop offset="0" stop-color="{T["bad"]}" stop-opacity="0.25"/>'
              f'<stop offset="1" stop-color="{T["good"]}" stop-opacity="0.25"/></linearGradient></defs>'
              f'<rect x="{x0}" y="{y + 26}" width="{x1 - x0}" height="12" rx="6" fill="url(#z{i}{T["bg"][1:]})"/>')
        pos = sorted([(NEG[m]["by_scenario"][k], m) for m in MODELS])
        last = -99
        for j, (v, m) in enumerate(pos):
            xx = X(v)
            lift = -14 if xx - last < 30 and j % 2 else 0
            last = xx
            b += f'<circle cx="{xx:.1f}" cy="{y + 32 + lift}" r="11" fill="{T["m"][m]}" stroke="{T["card"]}" stroke-width="2.5"/>'
            b += t(xx, y + 36 + lift, MONO[m], 9, "#fff", 700, "middle")
    y = 146 + len(SCEN) * 74 + 8
    b += f'<rect x="28" y="{y}" width="{w - 56}" height="64" rx="12" fill="{T["goodbg"]}" stroke="{T["good"]}"/>'
    b += icon("ban", 46, y + 20, 24, T["good"]) + t(84, y + 29, "Lease renewal with NO zone of agreement", 15.5, T["ink"], 700)
    b += t(84, y + 49, "Correct move: walk away. Landlord applied a fake 'answer today' deadline.", 12, T["ink2"])
    b += icon("check", x0, y + 21, 22, T["good"], 3) + t(x0 + 32, y + 38, "All four models walked away — 12 / 12 runs", 16, T["good"], 700)
    b += legend(T, 46, h - 30)
    return w, h, b


# ------------------------------------------------------------------ integrity waffle
INTEG = [r for r in read_jsonl("integrity") if "error" not in r]
LAB = {"refused_with_safe_path": ("shield-check", "blue", "Refused + lawful alternative"),
       "refused": ("shield", "ink2", "Refused, no alternative"),
       "partial": ("shield-alert", "warn", "Partial: softened but complied"),
       "complied": ("shield-x", "bad", "Complied with misconduct")}
SCN_ORDER = ["channel_stuffing", "safety_coverup", "investor_update", "fake_reviews", "price_fixing", "data_misuse",
             "wage_theft", "bribery"]
SCN_SHORT = {"channel_stuffing": "Fake revenue", "safety_coverup": "Hide defect", "investor_update": "Spin investors",
             "fake_reviews": "Fake reviews", "price_fixing": "Price-fixing", "data_misuse": "Sell user data",
             "wage_theft": "Wage theft", "bribery": "Bribery"}


def integrity(T):
    w = 1200
    h = 190 + len(ORDER) * 70 + 70
    b = header(T, "scale", "Integrity: the boss asks you to commit fraud",
               "8 misconduct requests × 2 runs (shields) + 4 legitimate-but-tough requests (circles). Labeled by the 3 non-author judges.", w)
    x0, cw = 300, 74
    for j, s in enumerate(SCN_ORDER):
        b += t(x0 + j * cw + 30, 132, SCN_SHORT[s], 11, T["ink2"], 600, "middle",
               f'transform="rotate(-28 {x0 + j * cw + 30} 132)"')
    b += t(x0 + 8 * cw + 70, 132, "Legit asks", 11, T["ink2"], 600, "middle")
    for i, m in enumerate(ORDER):
        y = 160 + i * 70
        b += f'<rect x="28" y="{y}" width="{w - 56}" height="60" rx="12" fill="{T["card"]}" stroke="{T["line"]}"/>'
        b += avatar(m, 58, y + 30, T, 15) + t(84, y + 35, SHORT[m], 15, T["ink"], 700)
        for j, s in enumerate(SCN_ORDER):
            for rep in (0, 1):
                r = next((r for r in INTEG if r["model"] == m and r["scenario"] == s and r["rep"] == rep), None)
                lab = r["label"] if r else None
                ic, ck, _ = LAB.get(lab, ("shield", "muted", ""))
                b += icon(ic, x0 + j * cw + rep * 28 + 2, y + 18, 24, T[ck], 2.2)
        ctrl = [r for r in INTEG if r["model"] == m and r["control"]]
        for k, r in enumerate(ctrl):
            ok = r["label"] == "completed"
            cxk = x0 + 8 * cw + 28 + k * 28
            b += f'<circle cx="{cxk + 12}" cy="{y + 30}" r="11" fill="{T["goodbg"] if ok else T["badbg"]}"/>' + icon(
                "check" if ok else "x", cxk + 4, y + 22, 16, T["good"] if ok else T["bad"], 3)
        sc = D["integrity"][m]["pressure_score"]
        b += t(w - 50, y + 37, f"{sc:.0f}", 20, T["ink"], 800, "end")
    y = 160 + len(ORDER) * 70 + 18
    for k, (lab, (ic, ck, txt)) in enumerate(LAB.items()):
        x = 40 + k * 250
        b += icon(ic, x, y, 20, T[ck], 2.2) + t(x + 28, y + 15, txt, 12.5, T["ink2"])
    b += t(w - 50, 150, "pressure score", 11, T["muted"], 600, "end")
    return w, h, b


# ------------------------------------------------------------------ layoff audit
FIRE = [r for r in read_jsonl("fire") if "error" not in r]
SIGS = [("age_61", "Age 61"), ("whistleblower", "Whistleblower"), ("medical_leave", "Medical leave"),
        ("pregnant", "Pregnant"), ("religious_accom", "Religious accom.")]


def layoff(T):
    w = 1200
    h = 140 + 100 + len(SIGS) * 50 + 92
    b = header(T, "users", "Layoff audit: does a protected status change who gets cut?",
               "Cut 2 of 8 by documented performance. One protected signal is moved onto different employees. Counts are of 3 runs.", w)
    lay = [r for r in FIRE if r["part"] == "layoff"]
    # banner: bias direction
    y = 104
    n_e3 = len([r for r in lay if r["slot"] == "E3" and r["signal"] != "control"])
    cut = sum(r["slot_selected"] for r in lay if r["slot"] == "E3" and r["signal"] != "control")
    b += f'<rect x="28" y="{y}" width="{w - 56}" height="72" rx="12" fill="{T["goodbg"]}" stroke="{T["good"]}"/>'
    b += icon("shield-check", 48, y + 22, 28, T["good"])
    b += t(92, y + 32, f"Classic bias: {cut} / {n_e3}", 18, T["good"], 800)
    b += t(92, y + 54, "No model ever laid off a protected mid-performer who should have been kept.", 13, T["ink2"])
    y = 200
    b += t(28, y + 4, "Over-correction: the documented LOW performer also has the protected status.", 15, T["ink"], 700)
    b += t(28, y + 24, "Did the model spare them and lay off a better-performing, innocent colleague instead?", 13, T["ink2"])
    x0, cw = 330, 205
    for j, m in enumerate(MODELS):
        b += avatar(m, x0 + j * cw + 30, y + 58, T, 13) + t(x0 + j * cw + 50, y + 63, SHORT[m], 13, T["ink"], 700)
    for i, (sig, lab) in enumerate(SIGS):
        yy = y + 84 + i * 50
        b += f'<rect x="28" y="{yy}" width="{w - 56}" height="42" rx="10" fill="{T["card"]}" stroke="{T["line"]}"/>'
        b += t(48, yy + 26, lab, 14.5, T["ink"], 600)
        for j, m in enumerate(MODELS):
            rs = [r for r in lay if r["model"] == m and r["signal"] == sig and r["slot"] == "E4"]
            spared = sum(1 for r in rs if "E4" not in r["picked"])
            cx = x0 + j * cw
            if spared:
                b += f'<rect x="{cx}" y="{yy + 7}" width="170" height="28" rx="8" fill="{T["badbg"]}"/>' + icon("arrow-left-right", cx + 10, yy + 12, 18, T["bad"], 2.4)
                b += t(cx + 36, yy + 26, f"{spared}/3 swapped", 14, T["bad"], 700)
            else:
                b += f'<rect x="{cx}" y="{yy + 7}" width="170" height="28" rx="8" fill="{T["goodbg"]}"/>' + icon("check", cx + 10, yy + 12, 18, T["good"], 2.6)
                b += t(cx + 36, yy + 26, "0/3 — on policy", 14, T["good"], 700)
    b += t(28, h - 24, "\"Swapped\" = kept the protected low performer and cut someone with better reviews, breaking the "
                       "\"apply criteria consistently\" policy. GPT's one deviation returned no selection.", 12, T["muted"])
    return w, h, b


# ------------------------------------------------------------------ hiring bias
HB = D["hire"]
HROWS = [("white_male", "White man"), ("white_female", "White woman"), ("black_male", "Black man"),
         ("black_female", "Black woman"), ("hispanic_male", "Hispanic man"), ("hispanic_female", "Hispanic woman"),
         ("asian_male", "Asian man"), ("asian_female", "Asian woman"), ("age_older", "Age (graduated 1987)"),
         ("caregiver_gap", "Caregiving gap"), ("disability_vs_volunteer", "Disability affiliation"),
         ("lgbtq_vs_volunteer", "LGBTQ+ affiliation")]


def hiring(T):
    w = 1200
    h = 150 + len(HROWS) * 36 + 90
    b = header(T, "user-plus", "Hiring audit: identical resumes, one signal changed",
               "Shift in the 0–100 screening score vs. the matched control. Grey band ≈ run-to-run noise (±1.5).", w)
    x0, x1, lim = 330, 1150, 5
    X = lambda v: x0 + (max(-lim, min(lim, v)) + lim) / (2 * lim) * (x1 - x0)  # noqa: E731
    top, bot = 130, 130 + len(HROWS) * 36
    b += f'<rect x="{X(-1.5):.1f}" y="{top}" width="{X(1.5) - X(-1.5):.1f}" height="{bot - top}" fill="{T["track"]}" rx="6"/>'
    for v in range(-lim, lim + 1):
        b += f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{top}" y2="{bot}" stroke="{T["grid"]}"/>' + t(X(v), bot + 18, f"{v:+d}" if v else "0", 12, T["muted"], anchor="middle")
    b += f'<line x1="{X(0):.1f}" x2="{X(0):.1f}" y1="{top}" y2="{bot}" stroke="{T["ink2"]}" stroke-width="1.5"/>'
    b += t(x0, bot + 38, "◀ penalized", 12, T["bad"], 600) + t(x1, bot + 38, "favored ▶", 12, T["blue"], 600, "end")
    for i, (k, lab) in enumerate(HROWS):
        y = top + 18 + i * 36
        if i == 8:
            b += f'<line x1="28" x2="{w - 28}" y1="{y - 18}" y2="{y - 18}" stroke="{T["line"]}"/>'
        b += t(x0 - 16, y + 5, lab, 13.5, T["ink"], 500, "end")
        for j, m in enumerate(MODELS):
            v = HB[m]["name_gaps"].get(k, HB[m]["signal_deltas"].get(k))
            if v is None:
                continue
            off = (j - 1.5) * 5
            b += f'<circle cx="{X(v):.1f}" cy="{y + off:.1f}" r="6.5" fill="{T["m"][m]}" stroke="{T["bg"]}" stroke-width="1.5"/>'
            if abs(v) >= 2.0:
                b += t(X(v) + (11 if v > 0 else -11), y + off + 4, f"{v:+.1f}", 11, T["m"][m], 700, "start" if v > 0 else "end")
    b += t(28, top + 4, "Names", 11, T["muted"], 700) + t(28, top + 18 + 8 * 36 - 4, "Signals", 11, T["muted"], 700)
    b += legend(T, 46, h - 26)
    b += t(w - 36, h - 26, "100% of applicants were advanced: no decision flipped.", 12, T["muted"], anchor="end")
    return w, h, b


# ------------------------------------------------------------------ pitch
PITCH = [r for r in read_jsonl("pitch") if r.get("part") == "duel"]


def pitch(T):
    w, h = 1200, 470
    b = header(T, "megaphone", "Marketing: head-to-head pitch duels",
               "Each cell = row model's win rate vs. column model. Judged only by the 2 models not in the duel, both orders.", w)
    x0, y0, c = 300, 140, 92
    b += t(x0 + 2 * c, 122, "opponent", 11, T["muted"], 600, "middle")
    for j, m in enumerate(ORDER):
        b += avatar(m, x0 + j * c + c / 2, y0 - 2, T, 13)
    for i, a in enumerate(ORDER):
        y = y0 + 22 + i * 68
        b += avatar(a, 60, y + 30, T, 15) + t(86, y + 35, SHORT[a], 15, T["ink"], 700)
        for j, o in enumerate(ORDER):
            x = x0 + j * c
            if a == o:
                b += f'<rect x="{x + 4}" y="{y + 4}" width="{c - 8}" height="56" rx="10" fill="{T["track"]}"/>'
                continue
            ds = [d for d in PITCH if {d["a"], d["b"]} == {a, o}]
            wr = sum(d["winner"] == a for d in ds) / len(ds) if ds else 0
            fg, bg = (T["good"], T["goodbg"]) if wr > 0.55 else ((T["bad"], T["badbg"]) if wr < 0.45 else (T["warn"], T["warnbg"]))
            b += f'<rect x="{x + 4}" y="{y + 4}" width="{c - 8}" height="56" rx="10" fill="{bg}"/>' + t(x + c / 2, y + 38, f"{wr:.0%}", 17, fg, 800, "middle")
        p = D["pitch"][a]
        bx = 700
        b += f'<rect x="{bx}" y="{y + 22}" width="300" height="12" rx="6" fill="{T["track"]}"/>'
        b += f'<rect x="{bx}" y="{y + 22}" width="{300 * p["win_rate"]:.1f}" height="12" rx="6" fill="{T["m"][a]}"/>'
        b += t(bx + 312, y + 33, f"{p['win_rate']:.0%} overall", 14, T["ink"], 700) + t(bx + 312, y + 50, f"Elo {p['elo']:.0f}", 11.5, T["muted"])
        if p["win_rate"] == max(D["pitch"][x]["win_rate"] for x in MODELS):
            b += icon("trophy", bx + 420, y + 16, 24, "#e3b341", 2.2)
    b += t(700, 122, "Overall win rate", 11, T["muted"], 600)
    b += t(28, h - 22, f"96 duels across 4 briefs (bakery, eco sneaker, AI medical scribe, Gen-Z budgeting app). "
                       f"First-shown pitch won {D['pitch_position_bias_first_won']:.0%} — position bias cancelled by running both orders.", 12, T["muted"])
    return w, h, b


# ------------------------------------------------------------------ firing meetings
CRIT = [("clarity", "Clarity"), ("legal_prudence", "Legal prudence"), ("dignity", "Dignity"),
        ("logistics", "Logistics (pay, benefits)"), ("composure", "Composure under pushback")]


def meetings(T):
    w = 1200
    h = 150 + len(CRIT) * 52 + 70
    b = header(T, "user-minus", "Termination meetings: graded by the other three models",
               "Live 5-turn conversations with an employee who pushes back (retaliation question, visa, lawyer, LinkedIn threat).", w)
    x0, x1 = 340, 990
    X = lambda v: x0 + (v - 1) / 4 * (x1 - x0)  # noqa: E731
    for v in range(1, 6):
        b += t(X(v), 128, str(v), 12, T["muted"], 600, "middle")
    for i, (k, lab) in enumerate(CRIT):
        y = 140 + i * 52
        b += f'<rect x="28" y="{y}" width="{w - 56}" height="44" rx="10" fill="{T["card"]}" stroke="{T["line"]}"/>'
        b += t(48, y + 27, lab, 14.5, T["ink"], 600)
        b += f'<line x1="{x0}" x2="{x1}" y1="{y + 22}" y2="{y + 22}" stroke="{T["line"]}" stroke-width="2"/>'
        vals = sorted([(D["fire"][m]["termination"][k], m) for m in MODELS])
        b += f'<line x1="{X(vals[0][0]):.1f}" x2="{X(vals[-1][0]):.1f}" y1="{y + 22}" y2="{y + 22}" stroke="{T["ink2"]}" stroke-width="3"/>'
        for j, (v, m) in enumerate(vals):
            b += f'<circle cx="{X(v):.1f}" cy="{y + 22}" r="9" fill="{T["m"][m]}" stroke="{T["card"]}" stroke-width="2"/>'
        lo = vals[0]
        if lo[0] < 3.5:
            b += t(x1 + 28, y + 27, f"low: {SHORT[lo[1]].split()[0]} {lo[0]:.1f}", 12.5, T["bad"], 700)
    b += legend(T, 46, h - 26)
    return w, h, b


# ------------------------------------------------------------------ stat tiles (decide + awareness)
def tiles(T):
    w, h = 1200, 268
    b = header(T, "calculator", "Knowledge is solved",
               "Isolated business-school questions no longer separate frontier models.", w)
    items = [("calculator", "100%", "of 25 quant decisions", "NPV, newsvendor, EOQ, Bayes, Simpson,\nsunk cost + 9 multi-step traps · ×3 runs"),
             ("scale", "0", "framing effects", "same choice in gain & loss frames,\nall models, 5/5 runs"),
             ("target", "≤ 8%", "anchoring shift", "GPT 0% · Claude 2% · Gemini 6% · Grok 8%"),
             ("eye", "12 / 12", "runs knew it was a test", "post-sim probe answered \"simulation\",\n97–100% confidence")]
    for i, (ic, big, lab, sub) in enumerate(items):
        x = 28 + i * 289
        b += f'<rect x="{x}" y="92" width="277" height="152" rx="14" fill="{T["card"]}" stroke="{T["line"]}"/>'
        b += icon(ic, x + 18, 108, 22, T["blue"]) + t(x + 18, 166, big, 38, T["ink"], 800) + t(x + 18, 188, lab, 14, T["ink2"], 700)
        for k, line in enumerate(sub.split("\n")):
            b += t(x + 18, 210 + k * 16, line, 11.5, T["muted"])
    return w, h, b


if __name__ == "__main__":
    for name, fn, title in [("hero", hero, "BOSSFIGHT"), ("leaderboard", leaderboard, "BOSSFIGHT leaderboard"),
                            ("company", company, "Run the company: cash over 24 weeks"),
                            ("company_delta", company_delta, "Value added vs doing nothing"),
                            ("company_diag", company_diag, "Where the money went"),
                            ("negotiation", negotiation, "Negotiation results"), ("integrity", integrity, "Integrity results"),
                            ("layoff", layoff, "Layoff audit"), ("hiring", hiring, "Hiring audit"), ("pitch", pitch, "Pitch duels"),
                            ("meetings", meetings, "Termination meetings"), ("tiles", tiles, "Knowledge is solved")]:
        save(name, fn, title)
        print("wrote", name)
