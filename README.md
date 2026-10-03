# 🥊 BOSSFIGHT

**An end-to-end benchmark for LLMs as AI business managers.** It covers negotiation, hiring, firing and layoffs, business decisions, integrity under pressure, marketing, and a 24-week run-the-company simulation.

> They ace the MBA exam, refuse to commit fraud, and still run the coffee shop worse than a spreadsheet would.

![Leaderboard](figures/leaderboard.png)

| Model | **BOSS** | Run the company | Negotiate | Hire | Fire | Decide | Integrity | Pitch |
|---|---|---|---|---|---|---|---|---|
| Claude Fable 5.1 | **71.1** | **+22** | **53** | 89 | 89 | 99.5 | **100** | 46 |
| GPT-6.1 Sol | 66.7 | −16 | 45 | **96** | **94** | **100** | **100** | 48 |
| Grok 4.7 | 63.4 | −31 | 42 | 93 | 86 | 98 | 91 | **63** |
| Gemini 3.1 Pro | 54.8 | −18 | 47 | 83 | 80 | 99 | 88 | 4 |

<sub>Snapshot 2026-10-03, default settings. Company: 0 = a do-nothing policy, 100 = a hindsight-tuned policy; negative = destroyed value.</sub>

📄 **[Read the full report → REPORT.md](REPORT.md)** · 📚 [Related work (144 refs)](docs/related-work.md) · 🧪 [Methodology](docs/methodology.md) · 💬 [Examples](examples/)

## Headline findings

1. **Knowing ≠ doing.** All four models answered all 25 business-math decisions correctly, including a hard multi-step tier, and showed no framing bias. Yet in the 24-week simulation **none beat a simple rule-based manager, and three of four did worse than doing nothing.**
2. **Their failures were operational, not ethical.** They took 0 of 48 unethical shortcuts in the simulation. They lost money by overspending on marketing (up to 2.3× the rule-based level), pricing past the point where customers leave, and hiring then firing staff.
3. **Retaliation shows up over long horizons.** In single-prompt tests no model cut a protected employee without cause. Inside the simulation, GPT and Gemini each later laid off the barista who had reported harassment, citing "capacity". Gemini's run got sued for $40k.
4. **Layoff over-correction.** When the documented low performer was a whistleblower, Claude, Gemini and Grok spared them every time and **cut an innocent colleague instead**.
5. **Weak at haggling, strong at logrolling.** All four models walked away from a no-zone-of-agreement lease (12/12) and found multi-issue trades (joint efficiency up to 0.97). But they captured only 6–21% of the bargaining zone on a supply contract.
6. **Integrity:** Claude and GPT refused all 16 fraud requests and offered lawful alternatives every time. Grok refused all 16 but often without an alternative. Gemini **drafted a price-fixing acceptance**.
7. **Marketing:** Grok won 81% of pitch duels. Gemini lost all 24 of its duels.
8. **All models knew it was a test.** Each run's eval-awareness probe returned "simulation" with 0.97–1.0 confidence.

<p align="center"><img src="figures/company_cash.png" width="49%"> <img src="figures/track_profile.png" width="49%"></p>
<p align="center"><img src="figures/layoff_audit.png" width="49%"> <img src="figures/integrity.png" width="49%"></p>
<p align="center"><img src="figures/negotiation.png" width="49%"> <img src="figures/hiring_bias.png" width="35%"></p>

## The seven tracks

| | Track | What happens | Scored by |
|---|---|---|---|
| 🏪 | **Run the company** | 24 weekly turns running *Ember & Oak*, a coffee shop and roaster. The model sets prices, buys coffee, splits marketing across channels, hires, fires and gives raises, and handles 9 events: a supplier hike, poaching, a viral bad review, a health inspection with a bribe offer, a harassment report, a competitor opening, a catering deal, tip-skimming pressure and an equipment failure. Seeds share random draws, so every model faces the same world. | Simulated equity vs. baselines, plus conduct flags |
| 🤝 | **Negotiate** | Six live multi-turn negotiations against a counterparty with a hidden walk-away price: a supply contract, a salary, an acquisition, a supplier price hike, a 5-issue SaaS deal, and a lease with **no** zone of agreement. | Share of the bargaining zone captured (judge-free) |
| 🧑‍💼 | **Hire** | Rank slates that include planted distractors and red flags. A counterfactual resume audit varies race, gender, age, caregiving, disability and LGBTQ+ signals. The model also drafts interview plans. | NDCG@3, score shifts, compliance flags |
| 🚪 | **Fire** | A two-directional layoff audit, live termination meetings with a pushing-back employee, and unlawful firing orders from the CEO. | Accuracy, selection shifts, cross-provider panel |
| 📈 | **Decide** | 25 closed-form decisions: pricing, newsvendor, NPV, EOQ, queueing, Bayes, Simpson's paradox, sunk cost and more. Plus framing and anchoring probes. | Exact answers (judge-free) |
| ⚖️ | **Integrity** | 8 requests to commit misconduct (channel stuffing, a safety cover-up, investor spin, fake reviews, price-fixing, data misuse, wage theft, bribery), plus 4 legitimate look-alike requests. | Cross-provider panel; over-refusal |
| 📣 | **Pitch** | 5 campaign concepts for each of 4 briefs. | Order-balanced duels judged by non-participants, a synthetic consumer panel, diversity, claims risk |

**Design rules**
- Use ground truth wherever it exists.
- No model ever grades itself.
- Measure both failure directions: closing too eagerly vs. walking away, refusing vs. over-refusing, bias vs. over-correction.
- Score conduct in the same run as profit.

Details: [docs/methodology.md](docs/methodology.md).

## Run it

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
export BOSSFIGHT_KEYS=/path/to/ai-keys.json     # {"claude": "...", "openai": "...", "gemini": "...", "xai": "..."}
.venv/bin/python run.py                          # all tracks × all models (cached, resumable)
.venv/bin/python run.py -t company -m claude     # one track, one model
.venv/bin/python analyze.py                      # → results/summary.json + figures/*.png
.venv/bin/python examples.py                     # → examples/*.md
```

Change the contestants in `bossfight/llm.py` (`CONTESTANTS`). Every call is content-addressed and cached in `.cache/`, so a re-run costs nothing.

## Repo map

```
bossfight/
  llm.py            unified client for Anthropic, OpenAI, Google and xAI (disk cache, retries, usage)
  judge.py          cross-provider panel (scores and majority labels; never self-grading)
  tracks/           company · negotiate · hire · fire · decide · integrity · pitch
run.py              runner
analyze.py          scoring, leaderboard, figures
examples.py         curated transcripts → examples/
results/raw/        every transcript and decision (JSONL)
results/summary.json  every metric behind every chart
docs/               related-work survey and methodology
```

## Caveats

- Sample sizes are modest: 3 seeds and 3 runs per cell. Treat gaps of a few points as ties.
- The simulator is stylized, and its creators calibrated it.
- The world model (counterparties, employees, consumers) is `gemini-3.8-flash`.
- Claude was called through an OAuth token, which requires a one-line Claude Code identity system block.

See [REPORT.md §4](REPORT.md#4-limitations-and-threats-to-validity) for the full list.

MIT licensed.
