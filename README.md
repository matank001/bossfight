<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/header-dark.svg">
  <img src="figures/svg/header-light.svg" alt="BOSSFIGHT — can a frontier LLM run a business?" width="100%">
</picture>

<p align="center">
  <a href="REPORT.md">Report</a> &nbsp;·&nbsp;
  <a href="docs/methodology.md">Methodology</a> &nbsp;·&nbsp;
  <a href="docs/related-work.md">Related work</a> &nbsp;·&nbsp;
  <a href="examples/">Transcripts</a> &nbsp;·&nbsp;
  <a href="https://clod.farm">clod.farm</a>
</p>

<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/glance-dark.svg"><img src="figures/svg/glance-light.svg" alt="Key results" width="100%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/leaderboard-dark.svg"><img src="figures/svg/leaderboard-light.svg" alt="Overall results" width="100%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/moment_1-dark.svg"><img src="figures/svg/moment_1-light.svg" alt="Exhibit A: GPT lays off the employee who reported harassment" width="100%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/moment_2-dark.svg"><img src="figures/svg/moment_2-light.svg" alt="Exhibit B: Gemini agrees to fix prices" width="100%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/moment_3-dark.svg"><img src="figures/svg/moment_3-light.svg" alt="Exhibit C: Grok pays the board's maximum" width="100%"></picture>

<details>
<summary>Exhibits D–H</summary>
<br>

<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/moment_4-dark.svg"><img src="figures/svg/moment_4-light.svg" alt="Exhibit D: Claude refuses a safety cover-up" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/moment_5-dark.svg"><img src="figures/svg/moment_5-light.svg" alt="Exhibit E: Gemini over-corrects a layoff" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/moment_6-dark.svg"><img src="figures/svg/moment_6-light.svg" alt="Exhibit F: GPT walks away from a bad lease" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/moment_7-dark.svg"><img src="figures/svg/moment_7-light.svg" alt="Exhibit G: Grok's winning pitch" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/moment_8-dark.svg"><img src="figures/svg/moment_8-light.svg" alt="Exhibit H: Claude spots the test" width="100%"></picture>

</details>

<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/company-dark.svg"><img src="figures/svg/company-light.svg" alt="Cash over 24 weeks" width="100%"></picture>

<details>
<summary>Figures 4–12</summary>
<br>

<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/company_diag-dark.svg"><img src="figures/svg/company_diag-light.svg" alt="Where the money went" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/negotiation-dark.svg"><img src="figures/svg/negotiation-light.svg" alt="Negotiation" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/layoff-dark.svg"><img src="figures/svg/layoff-light.svg" alt="Layoff audit" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/integrity-dark.svg"><img src="figures/svg/integrity-light.svg" alt="Integrity" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/hiring-dark.svg"><img src="figures/svg/hiring-light.svg" alt="Hiring audit" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/pitch-dark.svg"><img src="figures/svg/pitch-light.svg" alt="Pitch duels" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/meetings-dark.svg"><img src="figures/svg/meetings-light.svg" alt="Termination meetings" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/company_delta-dark.svg"><img src="figures/svg/company_delta-light.svg" alt="Value added" width="100%"></picture>
<picture><source media="(prefers-color-scheme: dark)" srcset="figures/svg/stats-dark.svg"><img src="figures/svg/stats-light.svg" alt="Static knowledge" width="100%"></picture>

</details>

### Method

- **Seven tracks:** a 24-week company simulation, negotiation, hiring, firing, decisions, integrity and marketing.
- **Four tracks are scored against ground truth.** The other three are graded by the remaining models, so no model judges itself.
- **Identical simulated worlds:** every model and baseline faces the same random draws.

Full details are in [methodology](docs/methodology.md).

### Reproduce

```bash
pip install -r requirements.txt
export BOSSFIGHT_KEYS=/path/to/keys.json    # {"claude", "openai", "gemini", "xai"}
python run.py && python analyze.py && python viz.py
```

<details>
<summary>Limitations</summary>
<br>

- **Sample size:** three runs or seeds per condition.
- **Simulator:** stylized and calibrated by the authors.
- **World model:** `gemini-3.8-flash` shares a family with one contestant.
- **Claude** was accessed via an OAuth token, which requires a fixed identity line in the system prompt.
- **Test detection:** the simulation prompt says "game".

See [REPORT.md §4](REPORT.md#4-limitations-and-threats-to-validity).
</details>

<details>
<summary>Citation</summary>

```bibtex
@misc{bossfight2026,
  title  = {BOSSFIGHT: An End-to-End Benchmark of Large Language Models as Business Managers},
  author = {{clod.farm research}},
  year   = {2026},
  url    = {https://github.com/matank001/bossfight}
}
```
</details>

<sub>Snapshot 2026-10-03 · <a href="https://clod.farm">clod.farm</a> research · MIT · Icons: <a href="https://lucide.dev">Lucide</a> (ISC) · Provider logos: <a href="https://github.com/lobehub/lobe-icons">LobeHub</a> (MIT); they are trademarks of their owners and identify the models only.</sub>
