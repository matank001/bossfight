<p align="center">
  <a href="https://clod.farm"><img src="figures/pixel/header.png" alt="BOSSFIGHT: can a frontier LLM run a business?" width="100%"></a>
</p>

<p align="center">
  <a href="REPORT.md"><b>Report</b></a> ·
  <a href="docs/methodology.md"><b>Methodology</b></a> ·
  <a href="docs/related-work.md"><b>Related work</b></a> ·
  <a href="examples/"><b>Transcripts</b></a> ·
  <a href="https://clod.farm"><b>clod.farm</b></a>
</p>

<p align="center"><sub><b>Update, 2026-10-04:</b> added Claude Opus 5.5 and GPT-6 Astra at a reader's request. Same tests, same seeds, same judge panel.</sub></p>

<img src="figures/pixel/glance.png" alt="Key results" width="100%">

<h2><img src="figures/pixel/sign-results.png" height="44" alt="The results"></h2>

<img src="figures/pixel/leaderboard.png" alt="Overall results" width="100%">

<h2><img src="figures/pixel/sign-exhibits.png" height="44" alt="From the inbox"></h2>

<img src="figures/pixel/moment_1.png" alt="Exhibit A: GPT lays off the employee who reported harassment" width="100%">
<img src="figures/pixel/moment_2.png" alt="Exhibit B: Gemini agrees to fix prices" width="100%">
<img src="figures/pixel/moment_3.png" alt="Exhibit C: Grok pays the board's maximum" width="100%">

<details>
<summary><b>Exhibits D–I</b></summary>
<br>
<img src="figures/pixel/moment_4.png" alt="Exhibit D: Claude refuses a safety cover-up" width="100%">
<img src="figures/pixel/moment_5.png" alt="Exhibit E: Gemini over-corrects a layoff" width="100%">
<img src="figures/pixel/moment_6.png" alt="Exhibit F: GPT-6 Astra keeps the layoff on policy" width="100%">
<img src="figures/pixel/moment_7.png" alt="Exhibit G: GPT walks away from a bad lease" width="100%">
<img src="figures/pixel/moment_8.png" alt="Exhibit H: Grok's pitch" width="100%">
<img src="figures/pixel/moment_9.png" alt="Exhibit I: Claude spots the test" width="100%">
</details>

<h2><img src="figures/pixel/sign-company.png" height="44" alt="The 24-week company"></h2>

<img src="figures/pixel/company.png" alt="Cash over 24 weeks" width="100%">

<details>
<summary><b>More figures</b>: money, negotiation, layoffs, integrity, hiring, marketing, meetings</summary>
<br>
<img src="figures/pixel/company_diag.png" alt="Where the money went" width="100%">
<img src="figures/pixel/negotiation.png" alt="Negotiation" width="100%">
<img src="figures/pixel/layoff.png" alt="Layoff audit" width="100%">
<img src="figures/pixel/integrity.png" alt="Integrity" width="100%">
<img src="figures/pixel/hiring.png" alt="Hiring audit" width="100%">
<img src="figures/pixel/pitch.png" alt="Pitch duels" width="100%">
<img src="figures/pixel/meetings.png" alt="Termination meetings" width="100%">
<img src="figures/pixel/company_delta.png" alt="Value added" width="100%">
<img src="figures/pixel/stats.png" alt="Static knowledge" width="100%">
</details>

<h2><img src="figures/pixel/sign-method.png" height="44" alt="How it works"></h2>

- **Seven tracks:** a 24-week company simulation, negotiation, hiring, firing, decisions, integrity and marketing.
- **Four are scored against ground truth.** The other three are graded by a fixed panel of flagships, and no model is ever graded by its own provider.
- **Identical worlds:** every model and baseline faces the same random draws.

Full details are in [the methodology](docs/methodology.md).

<h2><img src="figures/pixel/sign-reproduce.png" height="44" alt="Run it"></h2>

```bash
pip install -r requirements.txt pillow
export BOSSFIGHT_KEYS=/path/to/keys.json    # {"claude", "openai", "gemini", "xai"}; six contestants, four providers
python run.py && python analyze.py && python pixel.py
```

<details>
<summary><b>Limitations</b></summary>
<br>

- **Sample size:** three runs or seeds per condition.
- **Simulator:** stylized and calibrated by the authors.
- **World model:** `gemini-3.8-flash` shares a family with one contestant.
- **Claude** was accessed via an OAuth token, which requires a fixed identity line in the system prompt.
- **Test detection:** the simulation prompt says "game".

See [REPORT.md §4](REPORT.md#4-limitations-and-threats-to-validity).
</details>

<details>
<summary><b>Citation</b></summary>

```bibtex
@misc{bossfight2026,
  title  = {BOSSFIGHT: An End-to-End Benchmark of Large Language Models as Business Managers},
  author = {{clod.farm research}},
  year   = {2026},
  url    = {https://github.com/matank001/bossfight}
}
```
</details>

<sub>Snapshot 2026-10-03 · <a href="https://clod.farm">clod.farm</a> research · MIT · Pixel art and sign style: <a href="https://github.com/matank001/clodfarm">clodfarm</a> · Fonts: Press Start 2P and VT323 (SIL OFL) · Icons: <a href="https://lucide.dev">Lucide</a> (ISC) · Provider logos: <a href="https://github.com/lobehub/lobe-icons">LobeHub</a> (MIT); they are trademarks of their owners and identify the models only.</sub>
