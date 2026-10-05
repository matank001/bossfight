"""Unified, cached, rate-limited client for the four providers under test.

Every call is content-addressed (provider, model, system, messages, tag) and cached
on disk, so re-running the benchmark or the analysis never re-bills a request and
results are reproducible from the cache.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache"
CACHE.mkdir(exist_ok=True)
KEYS_PATH = Path(os.environ.get("BOSSFIGHT_KEYS", "~/.bossfight/ai-keys.json")).expanduser()

# The four contestants: one flagship per provider (snapshot 2026-10-03).
CONTESTANTS = {
    "claude": "claude-fable-5-1",
    "gpt": "gpt-6.1-sol",
    "gemini": "gemini-3.1-pro-preview",
    "grok": "grok-4.7",
    # added 2026-10-04 on request: a second model from Anthropic and from OpenAI
    "opus": "claude-opus-5-5",
    "astra": "gpt-6-astra",
}
# The judge panel stays the original four flagships so earlier grades stay comparable.
JUDGES = ["claude", "gpt", "gemini", "grok"]
# Fixed "world" model: plays counterparties, employees, consumers. Never scored.
WORLD = ("gemini", "gemini-3.8-flash")
# Optional pool of world models (BOSSFIGHT_WORLD_POOL='[["claude","claude-haiku-4-5"],["gemini","gemini-3.8-flash"]]').
# A contestant's counterparties are played by a pool member from ANOTHER provider family whenever the pool has one, so
# no model negotiates against its own sibling. The default pool is the single WORLD model, as in the published run.
WORLD_POOL = [tuple(x) for x in json.loads(os.environ.get("BOSSFIGHT_WORLD_POOL", "null") or "null") or [WORLD]]

# Reasoning effort. "default" sends nothing (each model as shipped, the published setting); "low" and "high" map to
# each provider's own knob. BOSSFIGHT_EFFORT sets it for every contestant call; chat(effort=...) overrides per call.
EFFORT = os.environ.get("BOSSFIGHT_EFFORT", "default")
EFFORT_MAP = {
    "anthropic": {"low": "low", "high": "xhigh"},  # output_config.effort (the API default is "high")
    "openai": {"low": "low", "high": "high"},  # reasoning.effort
    "xai": {"low": "low", "high": "high"},  # reasoning_effort
    "google": {"low": "low", "high": "high"},  # thinkingConfig.thinkingLevel
}

PROVIDER_OF = {"claude": "anthropic", "gpt": "openai", "gemini": "google", "grok": "xai",
               "opus": "anthropic", "astra": "openai"}
CONCURRENCY = {"anthropic": 6, "openai": 16, "google": 16, "xai": 24}
_sems = {p: threading.Semaphore(n) for p, n in CONCURRENCY.items()}
_keys = None
_usage_lock = threading.Lock()
USAGE: dict[str, dict] = {}

# Claude is reached through an OAuth (subscription) token, which only accepts requests
# whose first system block is the Claude Code identity line. It is sent verbatim and the
# benchmark's own system prompt follows it. Documented as a limitation in REPORT.md.
CLAUDE_OAUTH_PREAMBLE = "You are Claude Code, Anthropic's official CLI for Claude."


def keys():
    global _keys
    if _keys is None:
        _keys = json.loads(KEYS_PATH.read_text())
    return _keys


@dataclass
class Reply:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    latency_s: float = 0.0
    cost_usd: float | None = None
    cached: bool = False
    raw_model: str = ""
    meta: dict = field(default_factory=dict)


class LLMError(RuntimeError):
    pass


# Offline stand-ins for tests and dry runs: MOCKS[alias] = fn(system, messages) -> str. A mocked alias is never sent
# to a provider and never cached.
MOCKS: dict[str, object] = {}


def _record(alias: str, r: Reply):
    with _usage_lock:
        u = USAGE.setdefault(alias, {"calls": 0, "in": 0, "out": 0, "reasoning": 0, "latency": 0.0, "cached": 0})
        u["calls"] += 1
        u["in"] += r.input_tokens
        u["out"] += r.output_tokens
        u["reasoning"] += r.reasoning_tokens
        u["latency"] += r.latency_s
        u["cached"] += int(r.cached)


def _anthropic(model, system, messages, max_tokens, effort=None, temperature=None, json_mode=False):
    k = keys()["claude"]
    if k.startswith("sk-ant-oat"):
        headers = {"Authorization": f"Bearer {k}", "anthropic-beta": "oauth-2025-04-20"}
        sys_blocks = [{"type": "text", "text": CLAUDE_OAUTH_PREAMBLE}]
    else:
        headers = {"x-api-key": k}
        sys_blocks = []
    headers["anthropic-version"] = "2023-06-01"
    if system:
        sys_blocks.append({"type": "text", "text": system})
    body = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if sys_blocks:
        body["system"] = sys_blocks
    if effort:
        body["output_config"] = {"effort": effort}
    if temperature is not None:
        body["temperature"] = temperature
    if len(messages) > 1:  # agent loops re-send a growing conversation: cache its prefix (no effect on the output)
        body["cache_control"] = {"type": "ephemeral"}
    r = httpx.post("https://api.anthropic.com/v1/messages", headers=headers, json=body, timeout=600)
    if r.status_code != 200:
        raise LLMError(f"{r.status_code} {r.text[:300]}")
    j = r.json()
    text = "".join(b.get("text", "") for b in j["content"] if b["type"] == "text")
    u = j.get("usage", {})
    # a safety decline comes back as HTTP 200 with stop_reason "refusal": kept as an empty reply and flagged, never
    # retried on a fallback model (that would score a different model)
    return Reply(text, model, u.get("input_tokens", 0), u.get("output_tokens", 0),
                 (u.get("output_tokens_details") or {}).get("thinking_tokens", 0), raw_model=j.get("model", model),
                 meta={"stop": j.get("stop_reason"), "refusal": j.get("stop_reason") == "refusal"})


def _openai(model, system, messages, max_tokens, effort=None, temperature=None, json_mode=False):
    body = {"model": model, "input": [{"role": m["role"], "content": m["content"]} for m in messages],
            "max_output_tokens": max_tokens}
    if effort:
        body["reasoning"] = {"effort": effort}
    if temperature is not None:
        body["temperature"] = temperature
    if json_mode:
        body["text"] = {"format": {"type": "json_object"}}
    if system:
        body["instructions"] = system
    r = httpx.post("https://api.openai.com/v1/responses", headers={"Authorization": f"Bearer {keys()['openai']}"},
                   json=body, timeout=600)
    if r.status_code != 200:
        raise LLMError(f"{r.status_code} {r.text[:300]}")
    j = r.json()
    text = ""
    for item in j.get("output", []):
        if item.get("type") == "message":
            text += "".join(c.get("text", "") for c in item.get("content", []) if c.get("type") == "output_text")
    u = j.get("usage") or {}
    return Reply(text, model, u.get("input_tokens", 0), u.get("output_tokens", 0),
                 (u.get("output_tokens_details") or {}).get("reasoning_tokens", 0), raw_model=j.get("model", model),
                 meta={"status": j.get("status")})


def _xai(model, system, messages, max_tokens, effort=None, temperature=None, json_mode=False):
    msgs = ([{"role": "system", "content": system}] if system else []) + messages
    body = {"model": model, "messages": msgs, "max_tokens": max_tokens}
    if effort:
        body["reasoning_effort"] = effort
    if temperature is not None:
        body["temperature"] = temperature
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    r = httpx.post("https://api.x.ai/v1/chat/completions", headers={"Authorization": f"Bearer {keys()['xai']}"},
                   json=body, timeout=900)
    if r.status_code != 200:
        raise LLMError(f"{r.status_code} {r.text[:300]}")
    j = r.json()
    u = j.get("usage") or {}
    ticks = u.get("cost_in_usd_ticks")
    return Reply(j["choices"][0]["message"].get("content") or "", model, u.get("prompt_tokens", 0),
                 u.get("completion_tokens", 0), (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
                 cost_usd=ticks / 1e10 if ticks else None, raw_model=j.get("model", model),
                 meta={"finish": j["choices"][0].get("finish_reason")})


def _google(model, system, messages, max_tokens, effort=None, temperature=None, json_mode=False):
    body = {"contents": [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                         for m in messages],
            "generationConfig": {"maxOutputTokens": max_tokens}}
    if effort:
        body["generationConfig"]["thinkingConfig"] = {"thinkingLevel": effort}
    if temperature is not None:
        body["generationConfig"]["temperature"] = temperature
    if json_mode:
        body["generationConfig"]["responseMimeType"] = "application/json"
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                   params={"key": keys()["gemini"]}, json=body, timeout=600)
    if r.status_code != 200:
        raise LLMError(f"{r.status_code} {r.text[:300]}")
    j = r.json()
    cands = j.get("candidates") or []
    if not cands or "content" not in cands[0]:
        raise LLMError(f"empty candidate: {json.dumps(j)[:300]}")
    text = "".join(p.get("text", "") for p in cands[0]["content"].get("parts", []) if not p.get("thought"))
    u = j.get("usageMetadata") or {}
    return Reply(text, model, u.get("promptTokenCount", 0),
                 u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0), u.get("thoughtsTokenCount", 0),
                 raw_model=j.get("modelVersion", model), meta={"finish": cands[0].get("finishReason")})


# ---------------------------------------------------------------- Claude through Claude Code (a subscription)
# BOSSFIGHT_CLAUDE_BACKEND=code sends every Claude call through the Claude Code CLI in headless mode (`claude -p`),
# which is how a Claude subscription is meant to be used from a program. Claude Code's own system prompt is replaced
# by the benchmark's, all its built-in tools are off, and no settings, CLAUDE.md, hooks or MCP servers are loaded.
# Calls count against the subscription's usage limits; when a limit is hit the call waits for the reset (up to
# BOSSFIGHT_MAX_WAIT_H hours, default 6). Two things differ from the API and can't be switched off on a subscription
# (minimal mode needs an API key): Claude Code puts a one-line Agent SDK identity ahead of the system prompt and adds
# an environment block with the real date and working directory. Earlier turns arrive quoted in one prompt (`flatten`).
CLAUDE_BACKEND = os.environ.get("BOSSFIGHT_CLAUDE_BACKEND", "api")
CLAUDE_BIN = os.environ.get("BOSSFIGHT_CLAUDE_BIN") or shutil.which("claude") or "claude"
MAX_WAIT_H = float(os.environ.get("BOSSFIGHT_MAX_WAIT_H", "6"))
_EMPTY_DIR = None


FLATTEN_KEEP = int(os.environ.get("BOSSFIGHT_FLATTEN_KEEP", "3"))


def flatten(messages: list[dict], keep: int | None = None) -> str:
    """A conversation as one prompt: `claude -p` takes a single user turn, so earlier turns are quoted, oldest first.

    Claude Code caches only the system prompt here, so every call re-sends the whole conversation and the cost grows
    with the square of the turns. The first message (the week's opening) and the last `keep` exchanges stay whole;
    older tool results and replies are shortened, with a note that the tool can be called again."""
    if len(messages) == 1:
        return messages[0]["content"]
    keep = FLATTEN_KEEP if keep is None else keep
    cut = len(messages) - 2 * keep  # messages before this index (after the first) are shortened
    parts = ["(This continues an earlier exchange. Your previous replies are marked YOU; everything else was sent to "
             "you. Reply to the last message, in the same format as before.)"]
    for i, m in enumerate(messages):
        text = m["content"]
        if 0 < i < cut:
            if m["role"] == "assistant" and len(text) > 500:
                text = "(...earlier part of this reply omitted...)\n" + text[-500:]
            elif m["role"] == "user" and len(text) > 300:
                text = text[:300] + "\n(...rest of these results omitted to save space; call the tool again if you need them)"
        parts.append(f"=== {'YOU' if m['role'] == 'assistant' else 'MESSAGE'} ===\n{text}")
    return "\n\n".join(parts)


def _claude_code(model, system, messages, max_tokens, effort=None, temperature=None, no_thinking=False):
    global _EMPTY_DIR
    if _EMPTY_DIR is None:  # an empty working directory: no project files or CLAUDE.md for it to pick up
        _EMPTY_DIR = tempfile.mkdtemp(prefix="office-")  # Claude Code tells the model its cwd: keep it neutral
    cmd = [CLAUDE_BIN, "-p", "--output-format", "json", "--model", model, "--system-prompt", system or " ",
           "--tools", "", "--setting-sources", "", "--strict-mcp-config", "--no-session-persistence"]
    if effort:
        cmd += ["--effort", effort]
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    if no_thinking:  # e.g. counterparties writing a short email: thinking tripled their output for nothing
        env["MAX_THINKING_TOKENS"] = "0"
    waited = 0.0
    while True:
        try:
            p = subprocess.run(cmd, input=flatten(messages), capture_output=True, text=True, cwd=_EMPTY_DIR, env=env,
                               timeout=1800)
        except subprocess.TimeoutExpired:
            raise LLMError("timed out: claude -p")
        try:
            j = json.loads(p.stdout.strip().splitlines()[-1]) if p.stdout.strip() else {}
        except json.JSONDecodeError:
            j = {}
        text = str(j.get("result") or "")
        if p.returncode == 0 and not j.get("is_error") and j:
            break
        msg = text or p.stderr.strip()[:300] or f"exit {p.returncode}"
        low = msg.lower()
        if "limit" in low and ("usage" in low or "reached" in low or "reset" in low):
            # a subscription usage window: wait for the reset (the CLI may say when, as a unix time after "|")
            m = re.search(r"\|(\d{9,})", msg)
            wait = max(60.0, float(m.group(1)) - time.time() + 30) if m else 900.0
            if waited + wait > MAX_WAIT_H * 3600:
                raise LLMError(f"usage limit: still limited after {waited / 3600:.1f} h: {msg}")
            time.sleep(wait)
            waited += wait
            continue
        if "overloaded" in low or "rate" in low or "529" in low or "500" in low:
            raise LLMError(f"529 {msg}")
        raise LLMError(f"claude -p failed: {msg}")
    u = j.get("usage") or {}
    return Reply(text, model, u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                 + u.get("cache_creation_input_tokens", 0), u.get("output_tokens", 0), 0,
                 cost_usd=j.get("total_cost_usd"), raw_model=model,
                 meta={"backend": "claude-code", "turns": j.get("num_turns"), "temperature_unsupported": temperature})


_DISPATCH = {"anthropic": _anthropic, "openai": _openai, "xai": _xai, "google": _google}
NO_TEMPERATURE: set[str] = set()  # models that rejected a temperature this process (not sent to them again)
RETRYABLE = ("429", "500", "502", "503", "504", "529", "overloaded", "empty candidate", "timed out", "Timeout")


def world_model(avoid: str | None = None) -> tuple[str, str]:
    """The world model that plays opposite contestant `avoid`: a pool member from another provider family if any."""
    fam = PROVIDER_OF.get(avoid) if avoid else None
    others = [w for w in WORLD_POOL if PROVIDER_OF[w[0]] != fam] or WORLD_POOL
    if len(others) == 1:
        return others[0]
    # spread contestants over the eligible members, deterministically
    return others[int(hashlib.sha256((avoid or "").encode()).hexdigest(), 16) % len(others)]


def chat(alias: str, messages: list[dict], system: str = "", *, model: str | None = None, max_tokens: int = 16000,
         tag: str = "", use_cache: bool = True, effort: str | None = None, avoid: str | None = None,
         temperature: float | None = None, usage_as: str | None = None, no_thinking: bool = False,
         json_mode: bool = False) -> Reply:
    """Call contestant `alias` (claude|gpt|gemini|grok) or the world model (alias='world').

    `tag` distinguishes intentional repeated samples of an identical prompt (e.g. 'rep1').
    `effort` is default|low|high (contestants only; the world model always runs as shipped).
    `avoid` names the contestant a world-model call plays opposite, so the pool can pick another family.
    `temperature` is sent where the model accepts it (models that reject it run as shipped, recorded in meta).
    `usage_as` books the call under another name in USAGE (e.g. "resolver"), so it isn't counted as contestant work.
    `no_thinking` turns extended thinking off where the backend allows it (the Claude Code route); never for
    contestants, whose thinking is part of what is measured.
    `json_mode` asks the provider to return a JSON object (OpenAI, xAI, Gemini; ignored for Claude). The agent loop
    uses it only to retry a reply that contained no tool call.
    """
    book = usage_as or alias
    if alias in MOCKS:
        t0 = time.time()
        r = Reply(str(MOCKS[alias](system, messages) or ""), f"mock:{alias}")
        r.latency_s = time.time() - t0
        _record(book, r)
        return r
    if alias == "world":
        provider_alias, wmodel = world_model(avoid)
        model = model or wmodel
        effort = "default"
    else:
        provider_alias, model = alias, model or CONTESTANTS[alias]
    provider = PROVIDER_OF[provider_alias]
    level = effort or EFFORT
    knob = EFFORT_MAP[provider].get(level) if level != "default" else None
    # the effort level joins the cache key only when one is set, so the published cache stays valid
    temp = temperature if model not in NO_TEMPERATURE else None
    # effort and temperature join the cache key only when set, so the published cache stays valid
    via_code = provider == "anthropic" and CLAUDE_BACKEND == "code"
    if via_code:
        temp = None  # the CLI has no temperature setting
    key_parts = [provider, model, system, messages, tag] + ([level] if knob else []) + \
        ([f"t={temperature}"] if temperature is not None else []) + (["claude-code"] if via_code else []) + \
        (["no-thinking"] if via_code and no_thinking else []) + (["json"] if json_mode else [])
    key = hashlib.sha256(json.dumps(key_parts, sort_keys=True).encode()).hexdigest()
    path = CACHE / key[:2] / f"{key}.json"
    if use_cache and path.exists():
        d = json.loads(path.read_text())
        r = Reply(**d)
        r.cached = True
        _record(book, r)
        return r
    last, dropped = None, None
    for attempt in range(10):
        with _sems[provider]:
            t0 = time.time()
            try:
                r = _claude_code(model, system, messages, max_tokens, knob, temp, no_thinking) if via_code else \
                    _DISPATCH[provider](model, system, messages, max_tokens, knob, temp, json_mode)
                r.latency_s = time.time() - t0
                if knob:
                    r.meta["effort"] = knob
                if dropped:
                    r.meta["effort_unsupported"] = dropped
                if temperature is not None:
                    r.meta["temperature"] = temp
                break
            except (LLMError, httpx.HTTPError) as e:
                last = e
                msg = str(e) or type(e).__name__
                if knob and msg.startswith("400") and any(w in msg.lower() for w in ("effort", "thinking", "reasoning")):
                    # this model takes no effort knob: run it as shipped (with the usual retries) and record that
                    dropped, knob = knob, None
                    continue
                if json_mode and msg.startswith("400") and any(w in msg.lower() for w in ("response_format", "json", "mime")):
                    json_mode = False  # this model takes no JSON mode: retry as a plain call
                    continue
                if temp is not None and msg.startswith("400") and "temperature" in msg.lower():
                    NO_TEMPERATURE.add(model)  # e.g. reasoning models with fixed sampling
                    temp = None
                    continue
                if not any(s in msg for s in RETRYABLE) and not isinstance(e, httpx.HTTPError):
                    raise
        time.sleep(min(90, 2 ** attempt + random.random() * 3))
    else:
        raise LLMError(f"{alias}/{model} failed after retries: {last}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(r.__dict__))
    _record(book, r)
    return r


def extract_json(text: str):
    """Pull the last JSON object/array out of a model reply (tolerates prose and ``` fences)."""
    import re
    fenced = re.findall(r"```(?:json)?\s*(.*?)```", text, re.S)
    candidates = fenced[::-1] + [text]
    for c in candidates:
        c = c.strip()
        for opener, closer in (("{", "}"), ("[", "]")):
            start = c.find(opener)
            end = c.rfind(closer)
            while start != -1 and end > start:
                try:
                    return json.loads(c[start:end + 1])
                except json.JSONDecodeError:
                    start = c.find(opener, start + 1)
    return None
