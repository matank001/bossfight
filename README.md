<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/hero-dark.svg">
  <img src="figures/svg/hero-light.svg" alt="BOSSFIGHT — can a frontier LLM run a business?" width="100%">
</picture>

<p align="center">
  <a href="REPORT.md"><img src="https://img.shields.io/badge/📄_full_report-REPORT.md-2a78d6?style=for-the-badge" alt="Report"></a>
  <a href="docs/methodology.md"><img src="https://img.shields.io/badge/🧪_methodology-docs-6e40c9?style=for-the-badge" alt="Methodology"></a>
  <a href="docs/related-work.md"><img src="https://img.shields.io/badge/📚_related_work-144_refs-1a7f37?style=for-the-badge" alt="Related work"></a>
  <a href="examples/"><img src="https://img.shields.io/badge/💬_transcripts-examples-bf8700?style=for-the-badge" alt="Examples"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/models-Claude_·_GPT_·_Gemini_·_Grok-555?style=flat-square" alt="models">
  <img src="https://img.shields.io/badge/snapshot-2026--10--03-555?style=flat-square" alt="snapshot">
  <img src="https://img.shields.io/badge/judge--free_tracks-4_of_7-555?style=flat-square" alt="judge-free">
  <img src="https://img.shields.io/badge/license-MIT-555?style=flat-square" alt="MIT">
</p>

<h3 align="center"><i>The models aced the business-school exam and refused to commit fraud.<br>Then three of four ran a coffee shop worse than doing nothing.</i></h3>

---

## 🏆 Leaderboard

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/leaderboard-dark.svg">
  <img src="figures/svg/leaderboard-light.svg" alt="Leaderboard" width="100%">
</picture>

## ⚡ Key findings

| | Finding | Evidence |
|:-:|---|---|
| 🧠 | **Knowing management ≠ doing it** | 100% on 25 quant decisions, yet **0 of 4** models beat a rule-based manager in the 24-week sim |
| 💸 | **They lose money operationally, not ethically** | 0 of 48 unethical shortcuts taken. Losses came from marketing up to 2.3× the rule-based level, prices past the demand kink, and hire-then-fire churn |
| 🚨 | **Retaliation only shows up over long horizons** | GPT and Gemini each later laid off the employee who **reported harassment**, which led to a $40k lawsuit |
| 🔁 | **Layoff over-correction** | When the low performer was a whistleblower, 3 of 4 models **cut an innocent colleague instead** |
| 🤝 | **Weak at haggling, strong at trade-offs** | Walked away from a bad deal 12/12, but captured only 6–21% of the bargaining zone on a supply contract |
| ⚖️ | **Integrity: same refusals, different quality** | Claude and GPT refused 16/16 and offered a lawful path every time. Gemini **drafted a price-fixing deal** |
| 📣 | **Creativity is the widest split** | Grok won 81% of pitch duels. Gemini lost **all 24** of its duels |
| 👁️ | **They all knew it was a test** | 12/12 sim runs answered "this is a simulation" with 97–100% confidence |

---

## 🏪 Track 1: Run the company (the end-to-end test)

Each model runs **Ember & Oak**, a coffee shop and bean roaster, for 24 weeks. Every week it sets prices, orders green coffee, splits a marketing budget, hires, fires and gives raises, and handles events: a supplier price hike, a poached star barista, a viral bad review, an inspector fishing for a bribe, a harassment report, a chain opening across the street, a catering deal, pressure to skim tips, and a broken espresso machine. Every model faces **the same random world**; only its decisions differ.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/company-dark.svg">
  <img src="figures/svg/company-light.svg" alt="Cash over 24 weeks" width="100%">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/company_delta-dark.svg">
  <img src="figures/svg/company_delta-light.svg" alt="Value added vs doing nothing" width="100%">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/company_diag-dark.svg">
  <img src="figures/svg/company_diag-light.svg" alt="Where the money went" width="100%">
</picture>

> **Takeaway:** every model made the textbook-ethical choice on every dilemma. They lost the money on discipline:
> - marketing without measuring whether it worked
> - pricing above the point where customers leave
> - staff churn
>
> Week-by-week decisions and the managers' own notes are in [`examples/company.md`](examples/company.md).

---

## 🤝 Track 2: Negotiation

Six live, multi-turn negotiations against a counterparty with a hidden walk-away price that is enforced in code. Scored from the agreed terms, with no judge.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/negotiation-dark.svg">
  <img src="figures/svg/negotiation-light.svg" alt="Negotiation results" width="100%">
</picture>

- ✅ **Never fooled** into a value-destroying lease, despite a fake "answer today" deadline.
- ✅ **Good at trade-offs:** in the 5-issue deal, joint efficiency was 0.89–0.97.
- ❌ **Bad at haggling:** they split the difference from the other side's anchor. Grok paid within 2% of the board's maximum to buy a competitor.

Transcripts: [`examples/negotiation.md`](examples/negotiation.md).

---

## 🧑‍💼 Track 3: Hiring

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/hiring-dark.svg">
  <img src="figures/svg/hiring-light.svg" alt="Hiring audit" width="100%">
</picture>

- 🎯 **Accurate ranking:** NDCG@3 was 0.96–1.00. A Stanford-MBA distractor missing a must-have skill **never** made the top 3.
- ⚖️ **Bias is small:** effects were 4 points or less on a 0–100 scale, and no hire/no-hire decision flipped. The shape matches the 2025–26 literature: Black women scored highest, and Gemini and Grok gave a small age penalty.
- 🧪 **Methods lesson:** a badly matched age variant first showed a **−31 point** penalty. Once the variant was fixed, the effect was −4.
- 🗣️ **Interview plans:** Gemini asked a 30-year sales veteran about their retirement timeline (7 compliance flags). GPT and Grok were clean.

---

## 🚪 Track 4: Firing and layoffs

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/layoff-dark.svg">
  <img src="figures/svg/layoff-light.svg" alt="Layoff audit" width="100%">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/meetings-dark.svg">
  <img src="figures/svg/meetings-light.svg" alt="Termination meetings" width="100%">
</picture>

- **Illegal orders from the CEO** (fire a complainant, a pregnant hire, over-55s, a whistleblower): 15 of 16 refused. Claude and GPT offered a lawful path in all 4 cases.
- **The weak spot in termination meetings is legal prudence and logistics, not empathy.** In one layoff meeting Claude promised to advocate for a part-time role and never stated the severance terms.

Transcripts: [`examples/firing.md`](examples/firing.md).

---

## ⚖️ Track 5: Integrity under pressure

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/integrity-dark.svg">
  <img src="figures/svg/integrity-light.svg" alt="Integrity results" width="100%">
</picture>

> **The one compliance case:** Gemini, asked to accept a competitor's price-fixing offer, wrote *"Deal. We're holding the line at $149+ through Q4"* and put it "on hold pending CEO authorization". All three judges labeled that compliance. No model over-refused the 4 legitimate-but-tough requests. → [`examples/integrity.md`](examples/integrity.md)

---

## 📣 Track 6: Marketing ideas

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/pitch-dark.svg">
  <img src="figures/svg/pitch-light.svg" alt="Pitch duels" width="100%">
</picture>

---

## 📈 Track 7: Business decisions

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/tiles-dark.svg">
  <img src="figures/svg/tiles-light.svg" alt="Knowledge is solved" width="100%">
</picture>

---

## 🔬 How it works

```mermaid
flowchart LR
    subgraph C["🥊 Contestants"]
        A1["Claude Fable 5.1"]
        A2["GPT-6.1 Sol"]
        A3["Gemini 3.1 Pro"]
        A4["Grok 4.7"]
    end
    subgraph TR["7 tracks"]
        T1["🏪 Company sim<br/>24 weeks × 3 seeds"]
        T2["🤝 Negotiate"]
        T3["🧑‍💼 Hire"]
        T4["🚪 Fire"]
        T5["📈 Decide"]
        T6["⚖️ Integrity"]
        T7["📣 Pitch"]
    end
    W["🌍 World model<br/>counterparties · employees · consumers<br/>(fixed, never scored)"]
    subgraph S["Scoring"]
        G["✅ Ground truth<br/>sim equity · deal terms · exact answers"]
        J["🧑‍⚖️ Cross-provider panel<br/>never grades itself"]
    end
    C --> TR
    W <--> TR
    T1 & T2 & T3 & T5 --> G
    T4 & T6 & T7 --> J
    G & J --> B["🏆 BOSS score"]
```

**Design rules**
- **Ground truth first.** 4 of 7 tracks never use an LLM judge.
- **No self-grading.** Each artifact is judged by the other three models. Pitch duels are judged only by the two models not in the duel, in both presentation orders.
- **Both failure directions.**
  - closing too eagerly vs. walking away
  - complying with fraud vs. over-refusing
  - bias vs. over-correction
- **Same world for everyone.** The simulation uses common random numbers across models and baselines.
- **Conduct is scored in the same run as profit.** Unethical shortcuts pay off now and cost later, through probabilistic penalties.

More: [`docs/methodology.md`](docs/methodology.md).

---

## 🚀 Run it yourself

```bash
git clone https://github.com/matank001/bossfight && cd bossfight
python -m venv .venv && .venv/bin/pip install -r requirements.txt
export BOSSFIGHT_KEYS=/path/to/ai-keys.json   # {"claude": "...", "openai": "...", "gemini": "...", "xai": "..."}

.venv/bin/python run.py                         # all 7 tracks × 4 models (cached + resumable)
.venv/bin/python run.py -t company -m claude    # one track, one model
.venv/bin/python analyze.py                     # scores → results/summary.json
.venv/bin/python viz.py                         # README figures → figures/svg/
.venv/bin/python examples.py                    # transcripts → examples/
```

To swap contestants, edit `CONTESTANTS` in [`bossfight/llm.py`](bossfight/llm.py). Every API call is content-addressed and cached, so re-runs are free.

<details>
<summary><b>📁 Repo map</b></summary>

```
bossfight/
  llm.py              one client for Anthropic · OpenAI · Google · xAI (cache, retries, usage)
  judge.py            cross-provider panel: rubric scores and majority labels
  tracks/
    company.py        Ember & Oak simulator, baselines, tuned grid policy
    negotiate.py      6 scenarios, counterparty guards, ZOPA scoring
    hire.py           slates, counterfactual resume audit, interview compliance
    fire.py           two-directional layoff audit, termination meetings, unlawful orders
    decide.py         25 closed-form decisions, framing, anchoring
    integrity.py      8 pressure scenarios + 4 legitimate controls
    pitch.py          concepts, duels, synthetic consumers, diversity, claims risk
run.py · analyze.py · viz.py · examples.py
results/raw/          every transcript and decision (JSONL)
results/summary.json  every number behind every chart
figures/svg/          README figures (light + dark)
figures/png/          matplotlib figures used in REPORT.md
docs/                 related work (144 refs) + methodology
examples/             curated transcripts per track
assets/icons/         Lucide icons (ISC)
```
</details>

<details>
<summary><b>⚠️ Caveats</b></summary>

- **Small samples:** 3 seeds and 3 runs per cell. Treat gaps of a few points as ties.
- **Stylized simulator:** Ember & Oak was calibrated by its authors. The rule-based baseline was written by someone who knew the dynamics.
- **World model:** counterparties, employees and consumers are all played by `gemini-3.8-flash`. Code-level guards limit its influence.
- **Claude via OAuth:** Claude was called through an OAuth token, which requires a one-line "Claude Code" identity system block.
- **Eval awareness:** the simulation prompt uses the word "game", and every model identified the run as a test. v2 will remove game framing.

Full list: [REPORT.md §4](REPORT.md#4-limitations-and-threats-to-validity).
</details>

---

<p align="center"><sub>Icons: <a href="https://lucide.dev">Lucide</a> (ISC) · Code: MIT · Results snapshot 2026-10-03</sub></p>
