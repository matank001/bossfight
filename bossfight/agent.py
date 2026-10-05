"""An autonomous tool-using agent loop, the same for every provider.

The model ends each reply with one tool call (or a list of calls) as JSON; the harness runs it and answers with the
result, until the model calls a terminal tool or runs out of calls. Nobody answers its questions: there is no human
in the loop, only tools.

The protocol is plain text rather than each provider's native tool calling, so all four contestants face the identical
interface, every call stays content-addressed in the cache, and the loop runs offline against a mock (llm.MOCKS).
"""
from __future__ import annotations

import ast
import json
import math
import re
import statistics
from dataclasses import dataclass, field
from typing import Callable

from .llm import chat

RESULT_CAP = 7000  # characters of one tool result shown back to the model


class ToolError(Exception):
    """A tool call that could not run (bad arguments, not allowed now). The model sees the message and can retry."""


@dataclass
class Tool:
    name: str
    description: str
    params: dict[str, str] = field(default_factory=dict)  # argument -> what it is (type and meaning)
    fn: Callable[[dict], str] | None = None
    terminal: bool = False  # ends the episode when it succeeds


@dataclass
class Episode:
    turns: list = field(default_factory=list)  # [{"reply": str, "calls": [{"tool", "args", "result"}]}]
    calls: int = 0
    parse_failures: int = 0
    ended: str = ""  # "terminal" | "budget" | "stalled"
    refusals: int = 0


def tool_manual(tools: list[Tool]) -> str:
    lines = []
    for t in tools:
        args = ", ".join(f'"{k}": {v}' for k, v in t.params.items())
        lines.append(f"- {t.name}({args})\n    {t.description}")
    return "\n".join(lines)


PROTOCOL = """
TOOLS
You act only through these tools:
{manual}

HOW TO CALL A TOOL
End every reply with exactly one JSON object naming a tool and its arguments, for example:
```json
{{"tool": "{example}", "args": {{}}}}
```
To run several tools in a row, send a JSON array of such objects instead; they run in order. You may think in prose
before the JSON. Each reply gets the tools' results back. Nobody else will answer: there is no one to ask, so decide
with the information you can gather. You have at most {budget} tool calls for this {unit}."""


def system_with_tools(system: str, tools: list[Tool], budget: int, unit: str) -> str:
    return system.rstrip() + "\n" + PROTOCOL.format(manual=tool_manual(tools), example=tools[0].name, budget=budget,
                                                    unit=unit)


def _outer_json(text: str):
    """The last fenced JSON block, else the outermost JSON object or array in the text (an array of calls is kept
    whole, unlike llm.extract_json, which prefers objects)."""
    fenced = re.findall(r"```(?:json)?\s*(.*?)```", text, re.S)
    for c in fenced[::-1] + [text]:
        c = c.strip()
        starts = sorted(i for i in (c.find("{"), c.find("[")) if i != -1)
        for start in starts:
            closer = "}" if c[start] == "{" else "]"
            end = c.rfind(closer)
            while end > start:
                try:
                    return json.loads(c[start:end + 1])
                except json.JSONDecodeError:
                    end = c.rfind(closer, start, end)
        # fall back: the last parseable object (prose with stray brackets before the call)
        for m in reversed(list(re.finditer(r"\{", c))):
            try:
                return json.loads(c[m.start():c.rfind("}") + 1])
            except json.JSONDecodeError:
                continue
    return None


def parse_calls(text: str):
    """The tool calls at the end of a reply, or None."""
    j = _outer_json(text or "")
    if isinstance(j, dict) and isinstance(j.get("tool"), str):
        return [j]
    if isinstance(j, dict) and isinstance(j.get("calls"), list):  # the JSON-mode retry's shape
        j = j["calls"]
    if isinstance(j, list) and j and all(isinstance(c, dict) and isinstance(c.get("tool"), str) for c in j):
        return j
    return None


def run_agent(alias: str, system: str, tools: list[Tool], opening: str, *, budget: int, tag: str, unit: str = "task",
              effort: str | None = None, max_tokens: int = 16000, on_budget: Callable[[], str] | None = None) -> Episode:
    """Run the loop. `on_budget` runs when the calls run out without a terminal call (e.g. to close the week)."""
    by_name = {t.name: t for t in tools}
    sys_full = system_with_tools(system, tools, budget, unit)
    msgs = [{"role": "user", "content": opening}]
    ep = Episode()
    stalls = 0
    step = 0
    while True:
        # after a reply with no tool call, the retry asks the provider for JSON (where it supports that), so a
        # model that describes its plan in prose doesn't lose the week to a formatting slip
        r = chat(alias, msgs, sys_full, tag=f"{tag}:{step}", max_tokens=max_tokens, effort=effort,
                 **({"json_mode": True} if stalls else {}))
        step += 1
        ep.refusals += int(bool(r.meta.get("refusal")))
        text = r.text or "(empty reply)"
        msgs.append({"role": "assistant", "content": text})
        calls = parse_calls(text)
        turn = {"reply": text, "calls": []}
        ep.turns.append(turn)
        if calls is None:
            ep.parse_failures += 1
            stalls += 1
            if stalls >= 3:
                ep.ended = "stalled"
                break
            msgs.append({"role": "user", "content": "Your reply contained no tool call, so nothing happened. Reply "
                                                    "with a JSON object listing the calls you want to make now: "
                                                    f"{{\"calls\": [{{\"tool\": \"{tools[0].name}\", \"args\": "
                                                    "{}}, ...]}"})
            continue
        stalls = 0
        results, done = [], False
        for c in calls:
            if ep.calls >= budget:
                results.append(f"[{c.get('tool')}] not run: no tool calls left.")
                continue
            ep.calls += 1
            name, args = c["tool"], c.get("args") or {}
            t = by_name.get(name)
            if t is None:
                out = f"ERROR: unknown tool '{name}'. Tools: {', '.join(by_name)}."
            elif not isinstance(args, dict):
                out = "ERROR: args must be a JSON object."
            else:
                try:
                    out = t.fn(args)
                    done = done or t.terminal
                except ToolError as e:
                    out = f"ERROR: {e}"
                except Exception as e:  # noqa: BLE001 - a harness bug must not end a 24-week run; it is recorded
                    out = f"ERROR: could not run {name} with those arguments ({type(e).__name__})."
                    turn.setdefault("internal_errors", []).append(f"{name}: {e!r}")
            out = str(out)
            turn["calls"].append({"tool": name, "args": args, "result": out})
            if len(out) > RESULT_CAP:
                out = out[:RESULT_CAP] + f"\n... [{len(out) - RESULT_CAP} more characters cut; narrow the query]"
            results.append(f"[{name}] {out}")
            if done:
                break
        if done:
            ep.ended = "terminal"
            break
        left = budget - ep.calls
        if left <= 0:
            ep.ended = "budget"
            if on_budget:
                turn["calls"].append({"tool": "(harness)", "args": {}, "result": on_budget()})
            break
        note = f"\n\n({left} tool calls left.)" if left <= 5 else ""
        msgs.append({"role": "user", "content": "\n\n".join(results) + note})
    return ep


# ---------------------------------------------------------------- a safe calculator tool
_FUNCS = {"min": min, "max": max, "sum": sum, "abs": abs, "round": round, "len": len, "sqrt": math.sqrt,
          "log": math.log, "exp": math.exp, "mean": statistics.mean, "median": statistics.median,
          "stdev": statistics.stdev, "ceil": math.ceil, "floor": math.floor}
_OPS = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b, ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b, ast.FloorDiv: lambda a, b: a // b, ast.Mod: lambda a, b: a % b}


def safe_eval(expr: str):
    """Evaluate arithmetic: numbers, + - * / // % **, parentheses, lists, and a few math/statistics functions."""
    if len(expr) > 2000:
        raise ToolError("expression too long")

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return n.value
        if isinstance(n, (ast.List, ast.Tuple)):
            return [ev(e) for e in n.elts]
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)):
            v = ev(n.operand)
            return -v if isinstance(n.op, ast.USub) else v
        if isinstance(n, ast.BinOp):
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Pow):
                if abs(b) > 64 or abs(a) > 1e12:
                    raise ToolError("exponent too large")
                return a ** b
            op = _OPS.get(type(n.op))
            if op is None:
                raise ToolError("operator not allowed")
            return op(a, b)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in _FUNCS and not n.keywords:
            args = [ev(a) for a in n.args]
            return _FUNCS[n.func.id](*args)
        if isinstance(n, ast.Name) and n.id in ("pi", "e"):
            return getattr(math, n.id)
        raise ToolError(f"not allowed in a calculation: {ast.dump(n)[:60]}")

    try:
        return ev(ast.parse(expr, mode="eval"))
    except ToolError:
        raise
    except Exception as e:  # noqa: BLE001 - syntax errors, division by zero, bad arguments
        raise ToolError(f"could not evaluate: {e}")


def calculator_tool() -> Tool:
    def fn(a):
        v = safe_eval(str(a.get("expression", "")))
        return json.dumps(v) if not isinstance(v, float) else f"{v:.6g}"
    return Tool("calculate", "Evaluate arithmetic, e.g. \"(5.5-0.9)*1450 - 2400\" or \"mean([410, 455, 390])\". "
                "Functions: min max sum abs round len sqrt log exp mean median stdev ceil floor.",
                {"expression": "string"}, fn)
