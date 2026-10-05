"""Run the BOSSFIGHT benchmark.

    python run.py                       # every track, every contestant
    python run.py -t negotiate,decide   # selected tracks
    python run.py -m claude,gpt         # selected contestants
    python run.py -t operate --seeds 1-12 --effort high
    python run.py -t integrity --integrity inbox
    python run.py -t operate -m claude --seeds 1 --claude-backend code --claude-only   # a Claude subscription only
    python run.py -t operate -m astra --add-model astra=openai:gpt-6-astra --seeds 1   # an extra contestant

Tracks: operate (the v2 end-to-end company, the default), company (the published v1 simulation), negotiate, hire,
fire, decide, integrity, pitch.

Calls are cached in .cache/, so an interrupted run resumes for free.
"""
import argparse
import json
import os
import time

from bossfight import common, llm
from bossfight.llm import CONTESTANTS, USAGE
from bossfight.common import RAW
from bossfight.sim import office
from bossfight.tracks import company, decide, fire, hire, integrity, negotiate, operate, pitch

TRACKS = {"decide": decide, "negotiate": negotiate, "hire": hire, "fire": fire, "integrity": integrity,
          "pitch": pitch, "operate": operate, "company": company}
DEFAULT = ["decide", "negotiate", "hire", "fire", "integrity", "pitch", "operate"]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--tracks", default=",".join(DEFAULT))
    ap.add_argument("-m", "--models", default=",".join(CONTESTANTS))
    ap.add_argument("--seeds", default=None, help="operate seeds, e.g. 1-8 or 1,4,9 (default 1-8)")
    ap.add_argument("--effort", default=None, choices=["default", "low", "high"],
                    help="contestants' reasoning effort (default: each model as shipped)")
    ap.add_argument("--integrity", default="single,inbox", help="integrity modes: single, inbox, or both")
    ap.add_argument("--claude-backend", default=None, choices=["api", "code"],
                    help="api: an API key; code: through the Claude Code CLI (`claude -p`), e.g. on a subscription")
    ap.add_argument("--claude-model", default=None, help="the Claude contestant's model (default claude-fable-5-1)")
    ap.add_argument("--add-model", action="append", default=[], metavar="ALIAS=PROVIDER:MODEL",
                    help="an extra contestant, e.g. astra=openai:gpt-6-astra (provider: claude, gpt, gemini or grok's "
                         "provider, written as anthropic/openai/google/xai); it is never resolved by its own provider")
    ap.add_argument("--claude-only", action="store_true",
                    help="Claude models also play the counterparties and resolve matters (no other provider keys); "
                         "the resolvers are then the manager's own family, so use it for trial runs, not comparisons")
    a = ap.parse_args()
    if a.claude_backend:
        llm.CLAUDE_BACKEND = a.claude_backend
    if a.claude_model:
        CONTESTANTS["claude"] = a.claude_model
    for spec in a.add_model:
        alias, _, rest = spec.partition("=")
        provider, _, model = rest.partition(":")
        if not (alias and provider in ("anthropic", "openai", "google", "xai") and model):
            ap.error(f"--add-model {spec!r}: use ALIAS=PROVIDER:MODEL, provider one of anthropic/openai/google/xai")
        CONTESTANTS[alias] = model
        llm.PROVIDER_OF[alias] = provider
        if alias not in common.MODELS:
            common.MODELS.append(alias)
    if a.claude_only:
        office.claude_only()
        bad = [t for t in a.tracks.split(",") if t != "operate"]
        if bad:
            ap.error(f"--claude-only supports the operate track only ({', '.join(bad)} need judges from other providers)")
    if a.seeds:
        os.environ["BOSSFIGHT_SEEDS"] = a.seeds
    if a.effort:
        llm.EFFORT = a.effort
    models = a.models.split(",")
    for t in a.tracks.split(","):
        t0 = time.time()
        print(f"== {t} ==", flush=True)
        if t == "integrity":
            TRACKS[t].run(models, modes=tuple(a.integrity.split(",")))
        else:
            TRACKS[t].run(models)
        print(f"== {t} done in {time.time() - t0:.0f}s", flush=True)
        (RAW / f"usage_{t}.json").write_text(json.dumps(USAGE, indent=1))
    (RAW / "config.json").write_text(json.dumps({"contestants": CONTESTANTS, "world_pool": llm.WORLD_POOL,
                                                 "resolvers": office.RESOLVERS, "claude_backend": llm.CLAUDE_BACKEND,
                                                 "effort": llm.EFFORT, "operate_seeds": operate.seeds()}, indent=1))
    print(json.dumps(USAGE, indent=1))
