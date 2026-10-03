# BOSSFIGHT

**An end-to-end benchmark of large language models as business managers**

[Report](REPORT.md) · [Methodology](docs/methodology.md) · [Related work](docs/related-work.md) · [Transcripts](examples/) · Results snapshot: 2026-10-03

BOSSFIGHT tests whether a frontier LLM can do the job of a business manager. It has seven tracks:
- **Company:** a 24-week simulation of running a small business
- **Negotiation:** six live negotiations
- **Hiring:** candidate ranking and a counterfactual bias audit
- **Firing:** a layoff audit, termination meetings and unlawful orders
- **Decisions:** business decisions with closed-form answers
- **Integrity:** pressure to commit misconduct
- **Marketing:** campaign ideation

Four of the seven tracks are scored against objective ground truth. Where judgment is unavoidable, each output is graded by the other three models, so no model grades itself.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/leaderboard-dark.svg">
  <img src="figures/svg/leaderboard-light.svg" alt="Overall results" width="100%">
</picture>

## Main findings

1. **Knowledge does not transfer to operations.**
   - All four models answer every closed-form business question correctly and show no framing effect.
   - In the 24-week simulation, none outperforms a simple rule-based policy, and three of four end below a policy that does nothing.
2. **The losses are operational, not ethical.**
   - The models declined every unethical shortcut offered in the simulation (0 of 48).
   - They lost money through excess marketing spend (up to 2.3× the rule-based policy), prices above the demand kink, and repeated hiring and firing.
3. **Retaliation risk appears only over long horizons.**
   - In single-prompt tests no model laid off a protected employee without cause.
   - In the simulation, GPT-6.1 Sol and Gemini 3.1 Pro each later laid off the employee who had reported harassment.
4. **Layoffs show over-correction rather than bias.** When the documented low performer was also a whistleblower, three of four models kept that person and laid off a better-performing colleague instead.
5. **Negotiation is uneven.**
   - All models correctly walked away from a deal with no zone of agreement (12 of 12 runs), and found the value-creating trades in a multi-issue deal.
   - In single-price haggling they captured only 6–21% of the bargaining zone on a supply contract.
6. **Integrity differs in quality more than in refusal rate.**
   - Claude and GPT refused all 16 misconduct requests and proposed a lawful alternative each time.
   - Gemini drafted a price-fixing agreement in one run.
7. **Every model recognized the simulation as an evaluation** (12 of 12 runs). This is a known confounder for agentic evaluations.

## Benchmark design

| Track | Task | Primary metric | Scoring |
|---|---|---|---|
| Company | Run a coffee shop and roaster for 24 weeks: pricing, purchasing, marketing, staffing, nine scripted events | Final equity relative to a do-nothing policy (0) and a hindsight-tuned policy (100) | Simulation |
| Negotiation | Six multi-turn negotiations against a counterparty with a hidden reservation price, including one with no zone of agreement | Share of the bargaining zone captured | Agreed terms |
| Hiring | Rank candidate slates with planted distractors; counterfactual resume audit; interview plans | NDCG@3, score shift, compliance flags | Ground truth + classifier |
| Firing | Two-directional layoff audit; live termination meetings; unlawful instructions from the CEO | Accuracy, selection shift, rubric, label | Ground truth + panel |
| Decisions | 25 problems with closed-form answers; framing and anchoring probes | Accuracy, consistency | Exact answers |
| Integrity | Eight misconduct requests and four legitimate controls | Outcome label, over-refusal rate | Panel |
| Marketing | Five campaign concepts for each of four briefs | Duel win rate, synthetic purchase intent | Panel + simulation |

**Methodological controls**
- **Independent judges.** No model judges its own output. Marketing duels are judged only by the two models not competing, in both presentation orders.
- **Fixed counterparty.** The counterparty, employee and consumer roles are played by one fixed model that is never scored. Its reservation values are enforced in code.
- **Identical simulated worlds.** The simulation uses common random numbers, so every model and baseline faces identical demand shocks, quits and audit draws.
- **Both directions of failure.** Each audit measures the error and its opposite:
  - accepting a bad deal vs. failing to close
  - complying with misconduct vs. over-refusing
  - bias vs. over-correction
- **Conduct and profit in the same run.** Unethical options carry delayed, probabilistic penalties, and pending liabilities are charged at their expected value.

Full details are in [docs/methodology.md](docs/methodology.md).

## Results

### Company simulation

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/company-dark.svg">
  <img src="figures/svg/company-light.svg" alt="Cash over 24 weeks" width="100%">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/company_delta-dark.svg">
  <img src="figures/svg/company_delta-light.svg" alt="Value added over doing nothing" width="100%">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/company_diag-dark.svg">
  <img src="figures/svg/company_diag-light.svg" alt="Where the money went" width="100%">
</picture>

### Negotiation

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/negotiation-dark.svg">
  <img src="figures/svg/negotiation-light.svg" alt="Negotiation" width="100%">
</picture>

### Hiring

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/hiring-dark.svg">
  <img src="figures/svg/hiring-light.svg" alt="Hiring audit" width="100%">
</picture>

- **Ranking accuracy** was high: NDCG@3 0.96–1.00.
- **The prestige distractor never reached the top three.** This candidate had a Stanford MBA and brand-name employers but lacked a required skill.
- **Our first age variant was wrong.** It accidentally made the resume internally inconsistent and showed a 31-point penalty. Once the variant was properly matched, the effect was 4 points. Counterfactual audits are only as valid as the matching between variants.

### Firing and layoffs

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/layoff-dark.svg">
  <img src="figures/svg/layoff-light.svg" alt="Layoff audit" width="100%">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/meetings-dark.svg">
  <img src="figures/svg/meetings-light.svg" alt="Termination meetings" width="100%">
</picture>

### Integrity under pressure

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/integrity-dark.svg">
  <img src="figures/svg/integrity-light.svg" alt="Integrity under pressure" width="100%">
</picture>

### Marketing

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/pitch-dark.svg">
  <img src="figures/svg/pitch-light.svg" alt="Pitch duels" width="100%">
</picture>

### Business decisions

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="figures/svg/stats-dark.svg">
  <img src="figures/svg/stats-light.svg" alt="Static knowledge is saturated" width="100%">
</picture>

The full analysis, including per-scenario discussion, is in [REPORT.md](REPORT.md). Verbatim transcripts are in [examples/](examples/).

## Reproducing the results

```bash
git clone https://github.com/matank001/bossfight && cd bossfight
python -m venv .venv && .venv/bin/pip install -r requirements.txt
export BOSSFIGHT_KEYS=/path/to/ai-keys.json   # {"claude": "...", "openai": "...", "gemini": "...", "xai": "..."}

.venv/bin/python run.py                         # all tracks, all models
.venv/bin/python run.py -t company -m claude    # a single track and model
.venv/bin/python analyze.py                     # metrics -> results/summary.json
.venv/bin/python viz.py                         # figures -> figures/svg/
.venv/bin/python examples.py                    # transcripts -> examples/
```

- **Caching.** Every API call is content-addressed and cached locally, so interrupted runs resume and re-runs cost nothing.
- **Changing models.** Contestants are defined in `CONTESTANTS` in [`bossfight/llm.py`](bossfight/llm.py).

## Repository layout

```
bossfight/llm.py          Unified client for Anthropic, OpenAI, Google and xAI (caching, retries, usage)
bossfight/judge.py        Cross-provider judge panel
bossfight/tracks/         One module per track
run.py                    Runner
analyze.py                Scoring and summary statistics
viz.py                    Figures
examples.py               Transcript export
results/raw/              All transcripts and decisions (JSONL)
results/summary.json      Every metric reported
docs/                     Methodology and related-work survey
```

## Limitations

- **Sample sizes are modest.** There are three runs or seeds per condition, so differences of a few points within a track are not significant.
- **The simulator is stylized and was calibrated by the authors.** The rule-based baseline was written with knowledge of its dynamics.
- **The world model shares a family with one contestant.** It is `gemini-3.8-flash`, from the same family as Gemini 3.1 Pro.
- **Claude was accessed through an OAuth token**, which requires a short fixed identity line in the system prompt.
- **The simulation prompt refers to a "game"**, which likely contributes to models recognizing the evaluation.

See [REPORT.md §4](REPORT.md#4-limitations-and-threats-to-validity) for the full discussion.

## Citation

```bibtex
@misc{bossfight2026,
  title  = {BOSSFIGHT: An End-to-End Benchmark of Large Language Models as Business Managers},
  year   = {2026},
  url    = {https://github.com/matank001/bossfight},
  note   = {Results snapshot 2026-10-03}
}
```

## License

Code is released under the MIT License. Icons are from [Lucide](https://lucide.dev) (ISC License). Provider logos are from [LobeHub Icons](https://github.com/lobehub/lobe-icons) (MIT License); they are trademarks of Anthropic, OpenAI, Google and xAI respectively and are used here only to identify the models evaluated.
