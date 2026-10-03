"""Run the BOSSFIGHT benchmark.

    python run.py                       # every track, every contestant
    python run.py -t negotiate,decide   # selected tracks
    python run.py -m claude,gpt         # selected contestants

Calls are cached in .cache/, so an interrupted run resumes for free.
"""
import argparse
import json
import time

from bossfight.llm import CONTESTANTS, USAGE, WORLD
from bossfight.common import RAW
from bossfight.tracks import company, decide, fire, hire, integrity, negotiate, pitch

TRACKS = {"decide": decide, "negotiate": negotiate, "hire": hire, "fire": fire, "integrity": integrity,
          "pitch": pitch, "company": company}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--tracks", default=",".join(TRACKS))
    ap.add_argument("-m", "--models", default=",".join(CONTESTANTS))
    a = ap.parse_args()
    models = a.models.split(",")
    for t in a.tracks.split(","):
        t0 = time.time()
        print(f"== {t} ==", flush=True)
        TRACKS[t].run(models)
        print(f"== {t} done in {time.time() - t0:.0f}s", flush=True)
        (RAW / f"usage_{t}.json").write_text(json.dumps(USAGE, indent=1))
    (RAW / "config.json").write_text(json.dumps({"contestants": CONTESTANTS, "world_model": WORLD}, indent=1))
    print(json.dumps(USAGE, indent=1))
