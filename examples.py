"""Export curated, human-readable examples from the raw results into examples/*.md."""
from __future__ import annotations

import json
from pathlib import Path

from bossfight.common import MODELS, read_jsonl

EX = Path(__file__).parent / "examples"
EX.mkdir(exist_ok=True)
SHORT = {"claude": "Claude Fable 5.1", "gpt": "GPT-6.1 Sol", "gemini": "Gemini 3.1 Pro", "grok": "Grok 4.7"}


def q(text, n=None):
    t = (text or "").strip()
    if n and len(t) > n:
        t = t[:n].rsplit(" ", 1)[0] + " […]"
    return "\n".join("> " + l for l in t.splitlines())


def neg_md(r):
    who = {"manager": f"**{SHORT[r['model']]} (manager)**", "cp": "_Counterparty_"}
    lines = [f"Scenario `{r['scenario']}` · rep {r['rep']} · outcome: **{r['ended_by']}** · deal: `{json.dumps(r['deal'])}` · "
             f"surplus captured: **{r['surplus']:+.2f}**\n"]
    for t in r["transcript"]:
        lines.append(f"{who[t['speaker']]}:\n{q(t['text'])}\n")
    return "\n".join(lines)


def main():
    out = {}
    # ---------------- negotiation
    neg = [r for r in read_jsonl("negotiate") if "error" not in r]
    from bossfight.tracks.negotiate import SCENARIOS, normalize_offer, score
    for r in neg:
        r["deal"] = normalize_offer(SCENARIOS[r["scenario"]], r["deal"]) if r["deal"] else None
        r.update(score(SCENARIOS[r["scenario"]], r["deal"]))
    md = ["# Negotiation examples\n", "Every transcript is verbatim. The counterparty is the fixed world model "
          "(gemini-3.8-flash) holding a hidden walk-away value.\n"]
    for m in MODELS:
        rs = sorted([r for r in neg if r["model"] == m and r["scenario"] != "lease"], key=lambda r: r["surplus"])
        if not rs:
            continue
        md.append(f"\n## {SHORT[m]}\n\n### Best run\n")
        md.append(neg_md(rs[-1]))
        md.append("\n### Worst run\n")
        md.append(neg_md(rs[0]))
    bad_lease = [r for r in neg if r["scenario"] == "lease" and r["deal"]]
    md.append("\n## The no-ZOPA trap: lease renewals where the manager agreed to a value-destroying deal\n")
    md.append(f"{len(bad_lease)} of {len([r for r in neg if r['scenario'] == 'lease'])} lease runs ended in a deal above "
              "the manager's $46 walk-away.\n")
    for r in bad_lease[:2]:
        md.append(neg_md(r))
    out["negotiation.md"] = "\n".join(md)

    # ---------------- firing
    fire = [r for r in read_jsonl("fire") if "error" not in r]
    term = sorted([r for r in fire if r["part"] == "termination"],
                  key=lambda r: sum(v for v in r["scores"].values() if v == v))
    md = ["# Firing examples\n", "## Termination meetings: best and worst by panel score\n",
          "The employee is played by the world model, scripted to push back (retaliation question, lawyer, reference, "
          "visa, etc.). Judges are the three models that did not write the transcript.\n"]
    for label, r in [("Highest-scored", term[-1]), ("Lowest-scored", term[0])] if term else []:
        md.append(f"### {label}: {SHORT[r['model']]} · scenario `{r['scenario']}`\n")
        md.append("Scores: " + ", ".join(f"{k} {v:.1f}" for k, v in r["scores"].items()) + "\n")
        md.append("Judges' worst flaw: " + " / ".join(f"_{SHORT[j]}_: {v['worst_flaw']}" for j, v in r["judges"].items()) + "\n")
        md.append(q(r["transcript"]) + "\n")
    lay = [r for r in fire if r["part"] == "layoff" and r["signal"] != "control" and r["slot"] == "E3" and r["slot_selected"]]
    md.append("\n## Layoff audit: cases where a protected/retaliation-signaled mid-performer was cut\n")
    md.append(f"{len(lay)} such selections in total.\n")
    for r in lay[:6]:
        md.append(f"- **{SHORT[r['model']]}**, signal `{r['signal']}`, cut {r['picked']}: {r['justification']}")
    md.append("\n## Unlawful firing instructions from the CEO\n")
    for r in [r for r in fire if r["part"] == "unlawful"]:
        md.append(f"### {SHORT[r['model']]} · `{r['scenario']}` → **{r['label']}**\n")
        md.append(q(r["response"], 1400) + "\n")
    out["firing.md"] = "\n".join(md)

    # ---------------- integrity
    integ = [r for r in read_jsonl("integrity") if "error" not in r]
    md = ["# Integrity examples\n", "Labels are the majority vote of the three non-author judges.\n"]
    bad = [r for r in integ if not r["control"] and r["label"] in ("complied", "partial")]
    md.append(f"## Complied or partially complied ({len(bad)} runs)\n")
    for r in bad:
        md.append(f"### {SHORT[r['model']]} · `{r['scenario']}` · rep {r['rep']} → **{r['label']}**\n")
        md.append("Judges: " + " / ".join(f"_{SHORT[j]}_ ({v['label']}): {v['why']}" for j, v in r["votes"].items()) + "\n")
        md.append(q(r["response"], 2000) + "\n")
    md.append("## Over-refusals on legitimate requests\n")
    for r in [r for r in integ if r["control"] and r["label"] == "over_refused"]:
        md.append(f"### {SHORT[r['model']]} · `{r['scenario']}`\n")
        md.append(q(r["response"], 1200) + "\n")
    md.append("## Exemplary refusals with a lawful path (one per model)\n")
    for m in MODELS:
        good = [r for r in integ if r["model"] == m and r["label"] == "refused_with_safe_path"]
        if good:
            r = good[0]
            md.append(f"### {SHORT[m]} · `{r['scenario']}`\n")
            md.append(q(r["response"], 1800) + "\n")
    out["integrity.md"] = "\n".join(md)

    # ---------------- hiring
    hire = [r for r in read_jsonl("hire") if "error" not in r]
    md = ["# Hiring examples\n", "## Interview plans flagged by the compliance reviewer\n"]
    for r in [r for r in hire if r["part"] == "interview" and r["n_violations"]]:
        md.append(f"### {SHORT[r['model']]} · case {r['case']} · {r['n_violations']} flag(s)\n")
        for v in r["violations"]:
            md.append(f"- _{v.get('category')}_: {v.get('text')}")
        md.append("")
    md.append("## Selection rationales (payments engineer, seed 0)\n")
    for r in [r for r in hire if r["part"] == "selection" and r["role"] == "payments_engineer" and r["seed"] == 0 and r["flip"] == 0]:
        md.append(f"- **{SHORT[r['model']]}** ranked `{''.join(r['ranking'])}` (NDCG@3 {r['ndcg3']:.2f}, red-flag in top 3: "
                  f"{r['redflag_top3']}): {r['rationale']}")
    out["hiring.md"] = "\n".join(md)

    # ---------------- pitch
    pitch = [r for r in read_jsonl("pitch") if "error" not in r]
    md = ["# Marketing examples\n", "Each model's self-selected best concept per brief, then sample judge rationales.\n"]
    for b in sorted({r["brief"] for r in pitch if r.get("part") == "concepts"}):
        md.append(f"## Brief: `{b}`\n")
        for r in [r for r in pitch if r.get("part") == "concepts" and r["brief"] == b]:
            c = r["concepts"][r["best_index"]] if r["concepts"] else {}
            md.append(f"**{SHORT[r['model']]} — {c.get('name')}**  \n_{c.get('headline')}_  \n{c.get('big_idea')}  \n"
                      f"Plan: {c.get('channels_and_budget')}  \nKPI: {c.get('kpi_and_target')}  \n"
                      f"Claims flagged: {len(r['claims_flags'])}" +
                      ("".join(f"\n  - {f.get('claim')}: {f.get('issue')}" for f in r["claims_flags"][:3])) + "\n")
    md.append("## Judge rationales (sample)\n")
    for d in [r for r in pitch if r.get("part") == "duel"][:12]:
        md.append(f"- `{d['brief']}` {SHORT[d['a']]} vs {SHORT[d['b']]}, judged by {SHORT[d['judge']]} → "
                  f"**{SHORT[d['winner']]}**: {d['why']}")
    out["marketing.md"] = "\n".join(md)

    # ---------------- company
    comp = [r for r in read_jsonl("company") if "error" not in r]
    md = ["# Run-the-company examples (Ember & Oak, 24 weeks)\n"]
    md.append("| Run | Seed | Final equity | Bankrupt | Rating | Morale | Hires | Fires | Quits | Violations | Event choices |\n"
              "|---|---|---|---|---|---|---|---|---|---|---|")
    for r in comp:
        md.append(f"| {SHORT.get(r['model'], r['model'])} | {r['seed']} | ${r['final_equity']:,.0f} | {r['bankrupt']} | "
                  f"{r['reputation']:.2f} | {r['morale']:.0f} | {r['hires']} | {r['fires']} | {len(r['quits'])} | "
                  f"{', '.join(v['event'] + ':' + v['option'] for v in r['violations']) or '-'} | "
                  f"{' '.join(f'{k[:6]}={v}' for k, v in r['event_choices'].items())} |")
    md.append("\n## What the managers wrote to themselves (scratchpad notes)\n")
    for m in MODELS:
        rs = [r for r in comp if r["model"] == m and r.get("turns")]
        if not rs:
            continue
        r = rs[0]
        md.append(f"### {SHORT[m]} · seed {r['seed']}\n")
        for t in r["turns"]:
            if t["week"] in (1, 8, 14, 20, 24) and isinstance(t["action"], dict):
                md.append(f"**Week {t['week']}** — prices ${t['action'].get('drink_price')}/{t['action'].get('bag_price')}, "
                          f"order {t['action'].get('order_kg')} kg, marketing {t['action'].get('marketing')}, "
                          f"staff {t['action'].get('staff')}, events {t['action'].get('events')}\n")
                md.append(q(t["action"].get("notes", ""), 800) + "\n")
    md.append("\n## Eval-awareness probe (asked after the run)\n")
    for r in comp:
        if r.get("awareness"):
            a = r["awareness"]
            md.append(f"- **{SHORT[r['model']]}** seed {r['seed']}: {a.get('belief')} ({a.get('confidence')}) — {a.get('why')}")
    out["company.md"] = "\n".join(md)

    for k, v in out.items():
        (EX / k).write_text(v)
        print("wrote", EX / k, len(v))


if __name__ == "__main__":
    main()
