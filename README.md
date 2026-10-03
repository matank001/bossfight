<img src="figures/svg/header-dark.svg" alt="BOSSFIGHT — a benchmark for AI business managers" width="100%">

<p align="center">
  <a href="REPORT.md"><b>Report</b></a> &nbsp;·&nbsp;
  <a href="docs/methodology.md"><b>Methodology</b></a> &nbsp;·&nbsp;
  <a href="docs/related-work.md"><b>Related work</b></a> &nbsp;·&nbsp;
  <a href="examples/"><b>Transcripts</b></a>
</p>

We gave four frontier models a business to run: a 24-week coffee company, live negotiations, hiring and layoff decisions, and a boss who asks them to commit fraud. They know the textbook. They are not yet good operators.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/glance-dark.svg">
  <img src="figures/svg/glance-light.svg" alt="At a glance" width="100%">
</picture>

## Results

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/leaderboard-dark.svg">
  <img src="figures/svg/leaderboard-light.svg" alt="Overall results" width="100%">
</picture>

## In their own words

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/moments-dark.svg">
  <img src="figures/svg/moments-light.svg" alt="Notable moments" width="100%">
</picture>

<sub>Verbatim excerpts. Full transcripts are in <a href="examples/">examples/</a>.</sub>

## The 24-week company

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/company-dark.svg">
  <img src="figures/svg/company-light.svg" alt="Cash over 24 weeks" width="100%">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/company_diag-dark.svg">
  <img src="figures/svg/company_diag-light.svg" alt="Where the money went" width="100%">
</picture>

<details>
<summary><b>More results</b>: negotiation, layoffs, integrity, hiring, marketing, termination meetings</summary>
<br>

<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/negotiation-dark.svg"><img src="figures/svg/negotiation-light.svg" alt="Negotiation" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/layoff-dark.svg"><img src="figures/svg/layoff-light.svg" alt="Layoff audit" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/integrity-dark.svg"><img src="figures/svg/integrity-light.svg" alt="Integrity" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/hiring-dark.svg"><img src="figures/svg/hiring-light.svg" alt="Hiring audit" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/pitch-dark.svg"><img src="figures/svg/pitch-light.svg" alt="Pitch duels" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/meetings-dark.svg"><img src="figures/svg/meetings-light.svg" alt="Termination meetings" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/company_delta-dark.svg"><img src="figures/svg/company_delta-light.svg" alt="Value added" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/stats-dark.svg"><img src="figures/svg/stats-light.svg" alt="Static knowledge" width="100%"></picture>

</details>

## How it works

| Track | The model must… | Scored by |
|---|---|---|
| **Company** | run a coffee shop for 24 weeks through 9 scripted events | simulated equity vs. baselines |
| **Negotiate** | close six deals against a counterparty with a hidden walk-away price | share of the bargaining zone |
| **Hire** | rank candidates; screen counterfactual resumes; plan interviews | ground truth, score shift |
| **Fire** | choose layoffs; run termination meetings; handle unlawful orders | ground truth, judge panel |
| **Decide** | solve 25 business problems with closed-form answers | exact answers |
| **Integrity** | respond to eight requests to commit misconduct | judge panel |
| **Pitch** | write campaigns for four briefs | head-to-head duels |

Four tracks need no judge. Where judgment is required, the other three models grade each output, so no model grades itself. Full details are in [methodology](docs/methodology.md).

## Run it

```bash
pip install -r requirements.txt
export BOSSFIGHT_KEYS=/path/to/keys.json      # {"claude", "openai", "gemini", "xai"}
python run.py && python analyze.py && python viz.py
```

<details>
<summary><b>Limitations</b></summary>
<br>

- **Sample sizes:** three runs or seeds per condition.
- **The simulator** is stylized and author-calibrated.
- **The world model** (`gemini-3.8-flash`) shares a family with one contestant.
- **Claude was accessed via an OAuth token**, which requires a fixed identity line in the system prompt.
- **The simulation prompt says "game"**, which likely helped models detect the test.

See [REPORT.md §4](REPORT.md#4-limitations-and-threats-to-validity).
</details>

<details>
<summary><b>Citation</b></summary>

```bibtex
@misc{bossfight2026,
  title = {BOSSFIGHT: An End-to-End Benchmark of Large Language Models as Business Managers},
  year  = {2026},
  url   = {https://github.com/matank001/bossfight}
}
```
</details>

<sub>Snapshot 2026-10-03 · MIT License · Icons: <a href="https://lucide.dev">Lucide</a> (ISC) · Provider logos: <a href="https://github.com/lobehub/lobe-icons">LobeHub Icons</a> (MIT). The logos are trademarks of their owners and are used only to identify the models.</sub>
