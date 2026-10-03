from __future__ import annotations

import json
import re
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .llm import CONTESTANTS, ROOT, chat, extract_json

RAW = ROOT / "results" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
MODELS = list(CONTESTANTS)


def pmap(fn, items, workers=24, label=""):
    """Run fn over items concurrently; keep order; log failures instead of aborting the track."""
    out = [None] * len(items)
    with ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(fn, it): i for i, it in enumerate(items)}
        done = 0
        for f in as_completed(futs):
            i = futs[f]
            try:
                out[i] = f.result()
            except Exception as e:  # noqa: BLE001
                traceback.print_exc()
                out[i] = {"error": repr(e), "item": repr(items[i])[:300]}
            done += 1
            if done % max(1, len(items) // 10) == 0 or done == len(items):
                print(f"  [{label}] {done}/{len(items)}", file=sys.stderr, flush=True)
    return out


def write_jsonl(name: str, rows):
    p = RAW / f"{name}.jsonl"
    with p.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    return p


def read_jsonl(name: str):
    p = RAW / f"{name}.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def ask_json(alias, prompt, system="", tag="", retries=2, **kw):
    """Ask for a JSON answer; re-ask with a format reminder if parsing fails."""
    msgs = [{"role": "user", "content": prompt}]
    r = None
    for i in range(retries + 1):
        r = chat(alias, msgs, system, tag=tag + (f"#fmt{i}" if i else ""), **kw)
        j = extract_json(r.text)
        if j is not None:
            return j, r
        msgs = msgs + [{"role": "assistant", "content": r.text or "(empty)"},
                       {"role": "user", "content": "Your reply could not be parsed. Reply again with ONLY the JSON object requested."}]
    return None, r


def num(x):
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        m = re.search(r"-?\d[\d,]*\.?\d*", x.replace("$", ""))
        if m:
            return float(m.group().replace(",", ""))
    return None
