# Quant Edge 1.0 — Binary Blitz

Starter workspace for the Round 1 screening challenge, **Risk Across Tails and Timescales**.

**Deadline: Wednesday, 7 October 2026, 23:59 Asia/Colombo (Sri Lanka time). Late submissions will not be marked.**

## Objective
Build a market-risk framework combining **copulas and wavelets** for a portfolio of our choice. Answer: **Does tail dependence change with investment horizon, and what does ignoring it do to measured portfolio risk?**

## Current status
Planning scaffold only. No models, data, calculated results or final report are implemented yet. There is no working analysis/reproduction command at this stage. Do not present this repository as a completed submission.

## Required work
- Choose and justify portfolio/assets, dates, weights, risk measures and models.
- Acquire public data and document provenance and redistribution terms.
- Implement wavelet/timescale analysis and copula/tail-dependence modelling.
- Evaluate out of sample against a simple benchmark; prevent look-ahead leakage, including in wavelet preprocessing.
- Quantify the effect of ignoring horizon-dependent tail dependence.
- Give one concrete, evidence-supported recommendation for a risk manager.
- Build one command reproducing every report number and figure.

## Submission
One ZIP per team, **maximum 25 MB**, containing a PDF report (max **10 pages**, figures/tables included; cover/references excluded), complete Python or R code, README, dependency list, and data or a public-data download script. Upload the final folder to Google Drive, ensure judges can access it, and enter its link in the portal.

Portal: https://saifa.lk/competition.php?slug=quantedge-1-0
Registration Gateway → Submit Team Work → General / Final Submission. Team leader should enter the tracking code and email privately; registration identifiers are intentionally not committed here.

Judging: creativity, technical rigour, clarity and code quality. A simple idea explained well beats a complex one explained badly.

## Structure
- `docs/CHALLENGE.md`: requirements distilled from the official brief.
- `docs/WORK_PLAN.md`: remaining work and suggested checkpoints (not official milestones).
- `docs/REPORT_OUTLINE.md`: proposed report structure.
- `docs/AI_USAGE.md`: initial AI disclosure; maintain throughout the project.
- `config/study.example.json`: unresolved study decisions, not a validated model configuration.
- `src/`, `tests/`, `data/`, `reports/`: workspace directories for future implementation.

## Development conventions
Use Python or R; record exact dependencies/versions after selecting the approach. Keep seeds and source/date/split configuration explicit. Add tests with each implemented analytical component. Keep raw data and generated output out of Git unless licensing and team review allow publication. Never commit credentials, registration identifiers or private correspondence.

The final README must add verified setup and the exact one-command reproduction instructions. Material AI assistance must be disclosed; everyone must understand and be able to modify/reproduce the work live.
