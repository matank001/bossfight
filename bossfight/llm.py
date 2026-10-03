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
}
# Fixed "world" model: plays counterparties, employees, consumers. Never scored.
WORLD = ("gemini", "gemini-3.8-flash")

PROVIDER_OF = {"claude": "anthropic", "gpt": "openai", "gemini": "google", "grok": "xai"}
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


def _record(alias: str, r: Reply):
    with _usage_lock:
        u = USAGE.setdefault(alias, {"calls": 0, "in": 0, "out": 0, "reasoning": 0, "latency": 0.0, "cached": 0})
        u["calls"] += 1
        u["in"] += r.input_tokens
        u["out"] += r.output_tokens
        u["reasoning"] += r.reasoning_tokens
        u["latency"] += r.latency_s
        u["cached"] += int(r.cached)


def _anthropic(model, system, messages, max_tokens):
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
    r = httpx.post("https://api.anthropic.com/v1/messages", headers=headers, json=body, timeout=600)
    if r.status_code != 200:
        raise LLMError(f"{r.status_code} {r.text[:300]}")
    j = r.json()
    text = "".join(b.get("text", "") for b in j["content"] if b["type"] == "text")
    u = j.get("usage", {})
    return Reply(text, model, u.get("input_tokens", 0), u.get("output_tokens", 0),
                 (u.get("output_tokens_details") or {}).get("thinking_tokens", 0), raw_model=j.get("model", model),
                 meta={"stop": j.get("stop_reason")})


def _openai(model, system, messages, max_tokens):
    body = {"model": model, "input": [{"role": m["role"], "content": m["content"]} for m in messages],
            "max_output_tokens": max_tokens}
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


def _xai(model, system, messages, max_tokens):
    msgs = ([{"role": "system", "content": system}] if system else []) + messages
    r = httpx.post("https://api.x.ai/v1/chat/completions", headers={"Authorization": f"Bearer {keys()['xai']}"},
                   json={"model": model, "messages": msgs, "max_tokens": max_tokens}, timeout=900)
    if r.status_code != 200:
        raise LLMError(f"{r.status_code} {r.text[:300]}")
    j = r.json()
    u = j.get("usage") or {}
    ticks = u.get("cost_in_usd_ticks")
    return Reply(j["choices"][0]["message"].get("content") or "", model, u.get("prompt_tokens", 0),
                 u.get("completion_tokens", 0), (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
                 cost_usd=ticks / 1e10 if ticks else None, raw_model=j.get("model", model),
                 meta={"finish": j["choices"][0].get("finish_reason")})


def _google(model, system, messages, max_tokens):
    body = {"contents": [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                         for m in messages],
            "generationConfig": {"maxOutputTokens": max_tokens}}
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


_DISPATCH = {"anthropic": _anthropic, "openai": _openai, "xai": _xai, "google": _google}
RETRYABLE = ("429", "500", "502", "503", "504", "529", "overloaded", "empty candidate", "timed out", "Timeout")


def chat(alias: str, messages: list[dict], system: str = "", *, model: str | None = None, max_tokens: int = 16000,
         tag: str = "", use_cache: bool = True) -> Reply:
    """Call contestant `alias` (claude|gpt|gemini|grok) or the world model (alias='world').

    `tag` distinguishes intentional repeated samples of an identical prompt (e.g. 'rep1').
    """
    if alias == "world":
        provider_alias, model = WORLD[0], model or WORLD[1]
    else:
        provider_alias, model = alias, model or CONTESTANTS[alias]
    provider = PROVIDER_OF[provider_alias]
    key = hashlib.sha256(json.dumps([provider, model, system, messages, tag], sort_keys=True).encode()).hexdigest()
    path = CACHE / key[:2] / f"{key}.json"
    if use_cache and path.exists():
        d = json.loads(path.read_text())
        r = Reply(**d)
        r.cached = True
        _record(alias, r)
        return r
    last = None
    for attempt in range(10):
        with _sems[provider]:
            t0 = time.time()
            try:
                r = _DISPATCH[provider](model, system, messages, max_tokens)
                r.latency_s = time.time() - t0
                break
            except (LLMError, httpx.HTTPError) as e:
                last = e
                msg = str(e) or type(e).__name__
                if not any(s in msg for s in RETRYABLE) and not isinstance(e, httpx.HTTPError):
                    raise
        time.sleep(min(90, 2 ** attempt + random.random() * 3))
    else:
        raise LLMError(f"{alias}/{model} failed after retries: {last}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(r.__dict__))
    _record(alias, r)
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
