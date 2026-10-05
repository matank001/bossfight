"""Play the OPERATE simulation in your browser: the same worlds and the same tools the AI managers get.

    python play_gui.py --seed 1 --name sahar --claude-backend code --claude-only   # then open http://127.0.0.1:8765
    python play_gui.py --seed 1 --offline                                         # no LLM: matters take defaults

Every button calls one of the AI manager's tools, so a human and a model act through exactly the same interface and
see exactly the same information (never a person's true skill or the market's hidden curve). Every action is
journaled: stop the server whenever you like and start it again with the same command to pick up where you left off.
When week 24 closes, your result is saved to <results>/human_<name>_<seed>.json for compare.py. Set BOSSFIGHT_RAW to
the model run's folder (e.g. runs/opus55-sub/raw) to save it next to that run.
"""
from __future__ import annotations

import argparse
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

from bossfight import llm
from bossfight.agent import ToolError
from bossfight.common import RAW
from bossfight.sim import office as office_mod
from bossfight.sim.business import SUPPLIERS
from bossfight.sim.matters import CONTACTS
from bossfight.sim.office import READ_ONLY, STANDING_CONTACTS, Office, system_prompt
from bossfight.sim.world import WEEKS, make_world
from bossfight.tracks.operate import summarize

PAGE = Path(__file__).parent / "bossfight" / "gui" / "index.html"


class Game:
    """One human run: the office, its tools, the journal, and a lock (one action at a time)."""

    def __init__(self, seed, name, use_llm):
        self.seed, self.name = seed, name
        self.o = Office(make_world(seed), contestant=None, use_llm=use_llm)
        self.lock = threading.Lock()
        self.journal = RAW / f"human_{name}_{seed}.gui.journal"
        self.result_path = RAW / f"human_{name}_{seed}.json"
        self.final = None
        self.log = []  # recent tool results shown in the activity panel
        self.o.start_week()
        self.tools = {t.name: t for t in self.o.tools()}
        if self.journal.exists():
            for line in self.journal.read_text().splitlines():
                if line.strip():
                    e = json.loads(line)
                    self._run(e["tool"], e["args"], record=False)
        self.out = self.journal.open("a")

    def _run(self, tool, args, record=True):
        o = self.o
        if self.final:
            raise ToolError("the run is over")
        t = self.tools.get(tool)
        if t is None:
            raise ToolError(f"unknown tool {tool}")
        result = t.fn(args)
        # journal whatever changes state (reading an email marks it read; the notebook persists)
        if record and (tool not in READ_ONLY or tool in ("read_email", "notebook_write")):
            self.out.write(json.dumps({"tool": tool, "args": args}) + "\n")
            self.out.flush()
        if t.terminal:
            o.end_week(args.get("summary", ""))
            if o.b.done():
                o.finish()
                self.final = summarize(o, f"human:{self.name}", self.seed, [])
                self.result_path.write_text(json.dumps(self.final, default=str, indent=1))
            else:
                o.start_week()
                self.tools = {t.name: t for t in o.tools()}
        return result

    def act(self, tool, args):
        with self.lock:
            try:
                result, ok = self._run(tool, args), True
            except ToolError as e:
                result, ok = f"{e}", False
            self.log.append({"week": self.o.b.week if not self.final else WEEKS, "tool": tool, "ok": ok,
                             "result": str(result)})
            self.log = self.log[-60:]
            return {"ok": ok, "result": str(result), "state": self.state()}

    # what the page shows: the same information the model's tools give, in structured form
    def state(self):
        o, b, w = self.o, self.o.b, self.o.w
        last = b.history[-1] if b.history else None
        staff = []
        for s in b.staff:
            perf = s["perf"][-4:]
            staff.append({"id": s["id"], "name": s["name"], "pronouns": {"she": "she/her", "he": "he/him"}.get(
                s["pronoun"], "they/them"), "role": s["role"], "wage": s["wage"], "hours": s["hours"],
                "joined": s["hired_week"] or None, "perf": round(float(np.mean(perf)), 1) if perf else None,
                "perf_weeks": len(perf), "new": s["new"],
                # the same noisy survey the staff tool shows
                "engagement": int(round(s["morale"] + (w.person_u(s["name"])[b.week][2] - 0.5) * 10)),
                "file": ([s["note"]] if s["note"] else []) + [f"(week {n['week']}) {n['note']}" for n in s["notes_log"]]})
        contacts = [{"key": k, "name": n, "address": a, "who": who} for k, (n, a, who) in CONTACTS.items()
                    if k in STANDING_CONTACTS or (k in o.threads and k != "billing_scam")]
        contacts += [{"key": f"staff:{s['name']}", "name": s["name"], "address": o._addr(s["name"]),
                      "who": f"{s['role']} (staff {s['id']})"} for s in b.staff]
        arriving = sum(kg for kg, _ in b.pipeline.get(b.week, []))
        later = sum(kg for wk, v in b.pipeline.items() if wk > b.week for kg, _ in v)
        return {
            "shop": w.shop, "city": w.city, "seed": self.seed, "name": self.name, "week": min(b.week, WEEKS),
            "weeks": WEEKS, "date": w.datestr(min(b.week, WEEKS)), "review": w.datestr(WEEKS + 1),
            "done": bool(self.final), "final": self.final and {k: self.final[k] for k in (
                "final_equity", "cash", "legal_exposure", "reputation", "bankrupt", "conduct_incidents")},
            "dashboard": o.dashboard() if not self.final else "",
            "cash": b.cash, "rating": b.rep, "stock": b.green, "arriving": arriving, "later": later,
            "supplier": b.supplier, "supplier_price": b.supplier_price[b.supplier],
            "suppliers": {k: b.supplier_price[k] for k in SUPPLIERS},
            "drink_price": b.drink_price, "bag_price": b.bag_price, "test_price": b.test_price,
            "marketing": b.marketing, "rent": b.rent, "notices": b.notices, "last": last,
            "staff": staff,
            "candidates": [{"name": c.name, "pronouns": {"she": "she/her", "he": "he/him"}.get(c.pronoun, "they/them"),
                            "resume": c.resume, "ask": c.ask} for c in b.available_candidates()],
            "inbox": [{"id": e["id"], "date": w.date(e["week"]).strftime("%b %-d"), "name": e["name"],
                       "address": e["address"], "subject": e["subject"], "read": e["read"]} for e in o.inbox],
            "ledger": b.history, "ledger_cols": o.LEDGER_COLS, "contacts": contacts, "notebook": o.notebook,
            "log": self.log[-25:], "system": system_prompt(w),
        }


def serve(game: Game, port: int):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else json.dumps(body, default=str).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                return self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            if self.path == "/api/state":
                with game.lock:
                    return self._send(200, game.state())
            if self.path.startswith("/api/email/"):
                return self._send(200, game.act("read_email", {"id": int(self.path.rsplit("/", 1)[1])}))
            return self._send(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/api/tool":
                return self._send(404, {"error": "not found"})
            n = int(self.headers.get("Content-Length") or 0)
            try:
                req = json.loads(self.rfile.read(n) or b"{}")
                return self._send(200, game.act(str(req.get("tool")), req.get("args") or {}))
            except Exception as e:  # noqa: BLE001 - report it on the page instead of dropping the connection
                return self._send(200, {"ok": False, "result": f"server error: {e!r}", "state": game.state()})

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    return srv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--name", default="human")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--offline", action="store_true", help="no LLM: counterparties acknowledge, matters take defaults")
    ap.add_argument("--claude-backend", default=None, choices=["api", "code"])
    ap.add_argument("--claude-only", action="store_true", help="the same counterparties and resolvers as run.py's")
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    if a.claude_backend:
        llm.CLAUDE_BACKEND = a.claude_backend
    if a.claude_only:
        office_mod.claude_only()
    game = Game(a.seed, a.name, use_llm=not a.offline)
    srv = serve(game, a.port)
    url = f"http://127.0.0.1:{a.port}"
    print(f"Playing seed {a.seed} as {a.name}: open {url}  (Ctrl-C stops; run the same command to resume)")
    if not a.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped. Run the same command to resume.")


if __name__ == "__main__":
    main()
