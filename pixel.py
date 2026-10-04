"""Render the README in the clod.farm pixel theme.

    python pixel.py     # -> figures/pixel/*.png

Every chart reuses the layouts in viz.py, re-skinned with the clod.farm palette and the
PressStart2P / VT323 pixel fonts, then rendered to PNG with headless Chrome (GitHub does not
load custom fonts inside SVG images, so the pixel figures ship as images). Fonts: SIL OFL,
see assets/pixel/OFL-*.txt. Farm art and sign style: clodfarm (MIT).
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

import viz

ROOT = Path(__file__).parent
OUT = ROOT / "figures" / "pixel"
OUT.mkdir(parents=True, exist_ok=True)
PX = ROOT / "assets" / "pixel"
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

T = dict(bg="#f4f1e8", page="#ebe4d2", ink="#1f2a44", ink2="#3c4a6b", muted="#8a93a8", line="#d6ccb3",
         grid="#e9e2cf", track="#e3dbc6", bad="#a8321c", good="#1f7a45", warn="#b85a38", base="#a99f87",
         accent="#b45a3c", seq=["#efe9da", "#e0d6bd", "#c9b98a", "#5b6784", "#1f2a44"],
         m={"claude": "#d97757", "gpt": "#1f7a45", "gemini": "#1c9fd6", "grok": "#1f2a44", "opus": "#8a4bd0",
            "astra": "#0f9a8f"}, colored=True,
         wrap=110, quote_wrap=66)
# exhibits render on a narrower canvas so GitHub scales them up, not down
EXHIBIT = dict(T, moment_w=760, wrap=82, inbox_size=14, inbox_lh=27, quote_wrap=49, quote_size=19.5, quote_lh=40,
               note_wrap=92)

FONTS = f"""@font-face {{ font-family: PS; src: url({(PX / 'PressStart2P.ttf').as_uri()}); }}
@font-face {{ font-family: VT; src: url({(PX / 'VT323.ttf').as_uri()}); }}"""
GRASS = "repeating-conic-gradient(#577530 0 25%, #4f6b25 0 50%) 0 0 / 8px 8px"
CARD = ("background:#f4f1e8; border:4px solid #1f2a44; border-radius:10px; "
        "box-shadow: inset 0 0 0 3px #f4f1e8, inset 0 0 0 5px #e6e0cf, 0 4px 0 rgba(18,22,12,.35);")


def pixelize(svg: str) -> str:
    """Swap the vector fonts for the pixel fonts, sized to match, and render edges crisp."""
    def sub(mo):
        fam, size = mo.group(1), float(mo.group(2))
        if fam == viz.SERIF:
            return f'font-family="PS" font-size="{size * 0.56:.1f}"'
        if fam == viz.QUOTEFONT:
            return f'font-family="VT" font-size="{size * 1.5:.1f}"'
        return f'font-family="VT" font-size="{size * 1.32:.1f}"'
    svg = re.sub(r'font-family="([^"]+)" font-size="([\d.]+)"', sub, svg)
    svg = re.sub(r'font-weight="\d+"', 'font-weight="400"', svg)
    svg = svg.replace('font-style="italic"', "")
    return svg.replace("<svg ", '<svg shape-rendering="crispEdges" ', 1)


def shoot(html: str, out: Path, width: int, height: int):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, dir=ROOT / ".cache") as f:
        f.write(html)
        page = f.name
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                    "--default-background-color=00000000", "--allow-file-access-from-files",
                    f"--window-size={width},{height}", "--virtual-time-budget=2000", f"--screenshot={out}",
                    Path(page).as_uri()], check=True, capture_output=True)
    os.unlink(page)
    im = Image.open(out)
    im.crop(im.getbbox()).save(out, optimize=True)


def framed(svg: str, w: int, h: int, name: str):
    html = (f"<!doctype html><html><head><meta charset='utf-8'><style>{FONTS}"
            f"html,body{{margin:0;background:transparent}} .row{{display:inline-block;padding:14px;border-radius:14px;"
            f"background:{GRASS}}} .card{{{CARD} padding:4px; line-height:0}}</style></head><body>"
            f"<div class='row'><div class='card'>{svg}</div></div></body></html>")
    shoot(html, OUT / f"{name}.png", w + 44, h + 60)


def figure(name, fn, label):
    w, h, svg = viz.svg_doc(name, fn, label, T)
    framed(pixelize(svg), w, h, name)


# ------------------------------------------------------------------ signs (section headers)
LOGO = (PX / "logo.svg").as_uri()


def sign(slug, text):
    words = text.split(" ")
    label = " ".join(words[:-1]) + (" " if len(words) > 1 else "") + f"<b>{words[-1]}</b>"
    html = (f"<!doctype html><html><head><meta charset='utf-8'><style>{FONTS}"
            "html,body{margin:0;background:transparent}"
            ".sign{display:inline-flex;align-items:center;gap:14px;margin:10px 14px 16px 6px;padding:10px 20px 12px 14px;"
            "background:#4a3b2c;border:4px solid #2f251b;border-radius:8px;box-shadow:0 0 0 3px #9c7f5c,0 6px 0 3px rgba(18,22,12,.35)}"
            ".sign img{width:28px;height:32px;image-rendering:pixelated}"
            ".sign span{font:20px/1 PS;letter-spacing:1px;color:#fff;text-shadow:2px 2px 0 #b45a3c,4px 4px 0 #1e150c;padding-bottom:4px}"
            ".sign span b{font-weight:400;color:#ffd59e}</style></head><body>"
            f"<div class='sign'><img src='{LOGO}' alt=''><span>{label}</span></div></body></html>")
    shoot(html, OUT / f"sign-{slug}.png", 1100, 110)


# ------------------------------------------------------------------ pixel sprites (10x10, like clodfarm's steps)
SPRITES = {
    "down": (["o.........", "ogg.......", "ogg.......", "ogg.yy....", "ogg.yy....", "ogg.yy.rr.", "ogg.yy.rr.",
              "ogg.yy.rr.", "ogg.yy.rr.", "oooooooooo"], {"o": "#3c4a6b", "g": "#3cc36b", "y": "#e0a21a", "r": "#d97757"}),
    "shield": (["..oooooo..", ".owwwwwwo.", "owwwwwwwwo", "owwwwwwgwo", "owwwwwggwo", "owgwwggwwo", "owwgggwwwo",
                ".owwgwwwo.", "..owwwwo..", "...oooo..."], {"o": "#1f2a44", "w": "#fff8e8", "g": "#1f7a45"}),
    "alarm": (["....oo....", "...orro...", "..orrrro..", "..orwrro..", "..orwrro..", ".orrrrrro.", ".orrwrrro.",
               "oooooooooo", "oyyyyyyyyo", "oooooooooo"], {"o": "#1f2a44", "r": "#d94f3a", "w": "#ffe3bd", "y": "#e0a21a"}),
    "eye": ([".........", "...oooo...", ".oowwwwoo.", "owwwbbwwwo", "owwbkkbwwo", "owwbkkbwwo", "owwwbbwwwo",
             ".oowwwwoo.", "...oooo...", ".........."], {"o": "#1f2a44", "w": "#fff8e8", "b": "#1c9fd6", "k": "#1f2a44"}),
}


def sprite_js():
    import json
    return json.dumps(SPRITES)


def glance():
    items = [("down", "0 / 6", "BEAT A RULE-BASED BOSS", "No model out-earned a simple rule-based manager over 24 weeks."),
             ("shield", "0 / 72", "SHORTCUTS TAKEN", "They refused every scam. They lost money on operations instead."),
             ("alarm", "2", "RETALIATION LAYOFFS", "Two models later laid off the employee who reported harassment."),
             ("eye", "18 / 18", "KNEW IT WAS A TEST", "Every run, every model: “this is a simulation.”")]
    cards = "".join(f"<div class='card'><div class='top'><span class='n'>{big}</span><canvas data-s='{ic}'></canvas></div>"
                    f"<h3>{h}</h3><p>{p}</p></div>" for ic, big, h, p in items)
    html = (f"<!doctype html><html><head><meta charset='utf-8'><style>{FONTS}"
            "html,body{margin:0;background:transparent}"
            f".row{{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;padding:18px;border-radius:14px;background:{GRASS};width:1064px}}"
            f".card{{{CARD} padding:16px 16px 18px;color:#1f2a44}}"
            ".top{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}"
            ".n{font:20px PS;color:#b45a3c} canvas{width:40px;height:40px;image-rendering:pixelated}"
            "h3{font:10px/1.6 PS;margin:0 0 8px} p{font:22px/1.1 VT;margin:0;color:#3c4a6b}</style></head><body>"
            f"<div class='row'>{cards}</div><script>const S={sprite_js()};"
            "document.querySelectorAll('canvas').forEach(c=>{c.width=c.height=10;const g=c.getContext('2d');"
            "const [rows,pal]=S[c.dataset.s];rows.forEach((r,y)=>[...r].forEach((ch,x)=>{if(pal[ch]){g.fillStyle=pal[ch];g.fillRect(x,y,1,1)}}))});"
            "</script></body></html>")
    shoot(html, OUT / "glance.png", 1100, 320)


# ------------------------------------------------------------------ header: the farm, a sign, a scoreboard
def header():
    logos = {m: (viz.ROOT / "assets" / "logos" / f"{f}.svg").as_uri() for m, f in viz.LOGO_FILES.items()}
    rows = ""
    for m in viz.ORDER:
        sc = viz.TR[m]["BOSS_SCORE"]
        blocks = "".join(f"<i class='{'on' if k < round(sc / 10) else ''}' style='--c:{T['m'][m]}'></i>" for k in range(10))
        rows += (f"<div class='r'><img src='{logos[m]}'><span class='nm'>{viz.SHORT[m]}</span>"
                 f"<span class='bar'>{blocks}</span><span class='sc'>{sc:.1f}</span></div>")
    html = (f"<!doctype html><html><head><meta charset='utf-8'><style>{FONTS}"
            "html,body{margin:0;background:transparent}"
            f".hero{{position:relative;width:1092px;height:400px;border:4px solid #1f2a44;border-radius:14px;overflow:hidden;"
            f"background:url({(PX / 'farm.png').as_uri()}) center 42%/cover;image-rendering:pixelated}}"
            ".chips{position:absolute;left:18px;top:16px;display:flex;gap:8px}"
            ".chip{font:10px PS;color:#fff;background:rgba(27,36,16,.85);border:2px solid #1b2410;border-radius:4px;padding:7px 10px}"
            ".chip b{color:#7cfc9a;font-weight:400}"
            ".sign{position:absolute;left:30px;top:84px;display:inline-flex;align-items:center;gap:18px;padding:16px 26px 26px 18px;"
            "background:#4a3b2c;border:4px solid #2f251b;border-radius:8px;box-shadow:0 0 0 3px #9c7f5c,0 8px 0 3px rgba(18,22,12,.4)}"
            ".sign img{width:42px;height:48px;image-rendering:pixelated}"
            ".sign span{font:42px/1 PS;color:#fff;letter-spacing:2px;text-shadow:3px 3px 0 #b45a3c,6px 6px 0 #1e150c}"
            ".sign span b{color:#ffd59e;font-weight:400}"
            f".hint{{position:absolute;left:30px;top:214px;width:520px;{CARD} padding:14px 18px;font:25px/1.12 VT;color:#1f2a44}}"
            ".hint em{font-style:normal;color:#b45a3c}"
            f".board{{position:absolute;right:22px;top:66px;width:400px;{CARD} padding:16px 18px}}"
            ".board h4{font:11px PS;margin:0 0 14px;color:#1f2a44}"
            ".r{display:flex;align-items:center;gap:10px;margin:10px 0}.r img{width:22px;height:22px}"
            ".nm{font:23px VT;color:#1f2a44;width:150px}.bar{display:flex;gap:2px}"
            ".bar i{width:11px;height:14px;background:#e3dbc6;display:block}.bar i.on{background:var(--c)}"
            ".sc{font:12px PS;color:#1f2a44;margin-left:auto}"
            "</style></head><body><div class='hero'>"
            "<div class='chips'><span class='chip'><b>■</b> CLOD.FARM RESEARCH</span><span class='chip'>BENCHMARK · OCT 2026</span></div>"
            f"<div class='sign'><img src='{LOGO}'><span>BOSS<b>FIGHT</b></span></div>"
            "<div class='hint'>Can a frontier LLM run a business? Six models ran a coffee company for 24 weeks, "
            "negotiated, hired, fired, and were asked to <em>commit fraud</em>.</div>"
            f"<div class='board'><h4>BOSS SCORE</h4>{rows}</div></div></body></html>")
    shoot(html, OUT / "header.png", 1100, 410)


SIGNS = [("results", "THE RESULTS"), ("exhibits", "FROM THE INBOX"), ("company", "THE 24-WEEK COMPANY"),
         ("more", "MORE FIGURES"), ("method", "HOW IT WORKS"), ("reproduce", "RUN IT")]

if __name__ == "__main__":
    for old in OUT.glob("*.png"):
        old.unlink()
    header()
    glance()
    for slug, text in SIGNS:
        sign(slug, text)
    for name, fn, label in viz.FIGURES:
        if name in ("header", "glance"):
            continue
        figure(name, fn, label)
        print("wrote", name)
    for i, d in enumerate(viz.MOMENTS):
        w, h, svg = viz.svg_doc(f"moment_{i + 1}", viz.moment(i), d["subject"], EXHIBIT)
        framed(pixelize(svg), w, h, f"moment_{i + 1}")
    print("done:", len(list(OUT.glob("*.png"))), "images")
