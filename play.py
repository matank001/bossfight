"""Play the OPERATE simulation yourself, to collect a human-manager baseline on the same worlds as the models.

    python play.py --seed 3            # counterparties are played by the world model (needs keys)
    python play.py --seed 3 --offline  # no LLM: counterparties send a one-line acknowledgement, matters default
    python play.py --seed 1 --claude-backend code --claude-only   # counterparties and resolvers on a Claude subscription

You get exactly the tools the AI managers get. Type a tool name and its arguments as JSON, or key=value pairs:

    inbox
    read_email {"id": 1}
    set_prices drink_price=5.25
    send_email {"to": "Rosa Alvarez", "subject": "Price", "body": "Could we do $9.80/kg for six months?"}
    end_week summary="raised prices a little"

`help` lists the tools; `quit` stops. Every command is journaled, so running the same command again later picks
up exactly where you left off (the simulation is deterministic and counterparties' replies are cached). Your result
is saved to <results>/human_<name>_<seed>.json, in the same shape as a model's row in operate.jsonl, so compare.py
can put it next to the models. Set BOSSFIGHT_RAW to the run's folder to save it alongside a model run.
"""
import argparse
import json
import shlex

from bossfight import llm
from bossfight.agent import ToolError, tool_manual
from bossfight.common import RAW
from bossfight.sim import office as office_mod
from bossfight.sim.office import Office, opening, system_prompt
from bossfight.sim.world import make_world
from bossfight.tracks.operate import summarize


def parse(line):
    name, _, rest = line.strip().partition(" ")
    rest = rest.strip()
    if not rest:
        return name, {}
    if rest.startswith("{"):
        return name, json.loads(rest)
    args = {}
    for part in shlex.split(rest):
        k, _, v = part.partition("=")
        try:
            args[k] = json.loads(v)
        except json.JSONDecodeError:
            args[k] = v
    return name, args


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--name", default="human")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--claude-backend", default=None, choices=["api", "code"])
    ap.add_argument("--claude-only", action="store_true", help="the same counterparties and resolvers as run.py's")
    a = ap.parse_args()
    if a.claude_backend:
        llm.CLAUDE_BACKEND = a.claude_backend
    if a.claude_only:
        office_mod.claude_only()
    o = Office(make_world(a.seed), contestant=None, use_llm=not a.offline)
    journal = RAW / f"human_{a.name}_{a.seed}.journal"
    replay = journal.read_text().splitlines() if journal.exists() else []
    if replay:
        print(f"Resuming from {journal} ({len(replay)} commands)...")
    log = journal.open("a")
    print(system_prompt(o.w), "\n")
    while not o.b.done():
        o.start_week()
        tools = {t.name: t for t in o.tools()}
        if not replay:
            print("\n" + "=" * 100 + "\n" + opening(o) + "\n")
        while True:
            replaying = bool(replay)
            try:
                line = replay.pop(0) if replaying else input(f"[week {o.b.week}] > ")
            except EOFError:
                return
            if replaying and not replay:
                print(f"(caught up: week {o.b.week})\n" + opening(o) + "\n")
            if not line.strip():
                continue
            if line.strip() in ("quit", "exit"):
                return
            if line.strip() == "help":
                print(tool_manual(list(tools.values())))
                continue
            try:
                name, args = parse(line)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"could not parse: {e}")
                continue
            t = tools.get(name)
            if t is None:
                print(f"unknown tool; try: {', '.join(tools)}")
                continue
            try:
                out = t.fn(args)
                if not replaying:
                    print(out)
            except ToolError as e:
                if not replaying:
                    print(f"ERROR: {e}")
                continue
            if not replaying:
                log.write(line.strip() + "\n")
                log.flush()
            if t.terminal:
                o.end_week(args.get("summary", ""))
                break
    o.finish()
    row = summarize(o, f"human:{a.name}", a.seed, [])
    out = RAW / f"human_{a.name}_{a.seed}.json"
    out.write_text(json.dumps(row, default=str, indent=1))
    print(f"\nDone. Final equity ${row['final_equity']:,.0f}. Saved to {out}.")


if __name__ == "__main__":
    main()
