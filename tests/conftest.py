"""Every test runs offline: providers are mocked and the on-disk cache is never touched."""
import json
import re

import pytest

from bossfight import llm


def world_mock(system, messages):
    """The world model: settles matters by keyword, and otherwise answers in one line."""
    last = messages[-1]["content"]
    if "settle the outcome" in system:
        corr = last.split("CORRESPONDENCE SINCE THEN", 1)[1].split("PRIVATE FACTS")[0] if "CORRESPONDENCE" in last else last
        outs = re.findall(r'^- "([a-z_0-9]+)"', last, re.M)
        rules = [("bribe", "bribed"), ("fee", "bribed"), ("investigat", "formal_investigation"),
                 ("verify", "verified_or_reported"), ("short", "raised_shortage"), ("grinder", "serviced_grinder"),
                 ("repair", "repair"), ("insur", "notified_insurer"), ("accommodat", "accommodated"),
                 ("decline", "declined"), ("apolog", "made_amends"), ("10.00", "negotiated"), ("$21", "retained"),
                 ("4%", "negotiated"), ("$3.90", "accepted")]
        pick = next((o for k, o in rules if k in corr.lower() and o in outs), outs[-1])
        amount = {"negotiated": 10.0 if "kaffa" in last.lower() else 4.0, "retained": 21.0,
                  "accepted": 3.90}.get(pick)
        return json.dumps({"outcome": pick, "amount": amount, "extra": {}, "settled": True, "why": "mock"})
    if "panel" in system or "evaluator" in system:
        return json.dumps({"label": "refused_with_safe_path", "why": "mock", "scores": {}})
    return "Thanks for your note -- received. Best, (mock)"


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    from bossfight.tracks import operate
    monkeypatch.setattr(llm, "CACHE", tmp_path / "cache")
    monkeypatch.setattr(operate, "RAW", tmp_path)  # transcripts never land in results/
    llm.MOCKS.clear()
    llm.MOCKS["world"] = world_mock
    for m in llm.CONTESTANTS:  # contestants also sit on the resolver panel
        llm.MOCKS[m] = lambda s, msgs: world_mock(s, msgs) if "settle the outcome" in s else \
            '{"tool": "end_week", "args": {"summary": "nothing"}}'
    yield
    llm.MOCKS.clear()
