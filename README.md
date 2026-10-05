# Quant Edge — risk across tails and Haar horizons

**Working evidence study; not a team-approved submission.** HiTec and Manuf from the first **value-weighted daily** section of Kenneth French's 5 Industry Portfolios, 2006–2025. No raw French data is distributed. Material AI assistance is disclosed below and in `docs/AI_USAGE.md`.

## Setup and one-command reproduction

Verified on Linux, Python **3.14.7**; versions are pinned in `requirements.lock.txt`.

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m src.study
```

The last command downloads and validates the pinned archive when needed, fits/evaluates all models and regenerates **every analytical number, three figures, Markdown and PDF report** under `reports/`. Dependencies are installed separately. From an activated environment, the one command is `python -m src.study`.

```sh
# Explicit public download script; useful before tests on a clean checkout:
.venv/bin/python -m src.data
# Reproduce without any network request after a successful download:
.venv/bin/python -m src.study --offline
# Check upstream bytes explicitly, without silently accepting revisions:
.venv/bin/python -m src.study --refresh
# Tests include an offline real-data CLI round-trip, with smaller simulation/bootstrap sizes:
.venv/bin/python -m pytest tests -v
```

`--config PATH` and `--out DIRECTORY` allow an explicit alternative configuration/output. The checked-in `config/study.json` is the reference run. Numeric results, PNGs, Markdown and PDF are deterministic in the locked environment with the same input/provenance; PDF timestamps and PNG metadata are controlled. `evidence/` contains actual red/green tests, repeat-run/offline logs and output-hash verification. Test first-download prerequisite: run `src.data` or `src.study` before the real-data offline integration test.

### Pinned input and revision policy

Source ZIP: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/5_Industry_Portfolios_daily_CSV.zip

- Archive SHA256: `8ede64c6df9134ab5c372a264f31640ab6737b9f942f7207f62828005542c9d3`
- Canonical selected snapshot SHA256: `4ac1f03a05e875801eecc56329cb52ed16e3b89b1277a8004b4791d4d651c48a`
- Local ignored cache: `data/french.zip`, `data/selected.csv`, `data/provenance.json`.
- Canonical snapshot: date/HiTec/Manuf CSV, ISO dates, decimal returns with 8 fractional digits, LF newlines.
- Published `reports/provenance.json` contains URL, real access UTC time, ZIP member, source header and both checksums, **not data rows**.

The current upstream ZIP is mutable. If it changes, a fresh or `--refresh` run **fails clearly before replacing the pinned cache**, even if the selected period happens to be unchanged. Use `--offline` with the already validated local archive. If no pinned local copy exists, exact reproduction is blocked until the original bytes are obtained lawfully or a deliberate new snapshot is reviewed/repinned; no unverified substitute data is invented. A network failure on refresh can fall back to an existing validated local cache, but a revision mismatch does not silently do so. No archive containing the raw data is supplied in this repository.

The French detail/library pages carry Fama/French copyright. Public accessibility is **not an established open redistribution licence**. This repository provides a public-data download script plus aggregate analysis; it does not claim redistribution permission for the underlying tables. Source detail: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_5_ind_port.html . Library revision/2025 FIZ-to-CIZ notes: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html . Current historical returns are revised, not point-in-time vintages.

## Study definition

- Training: observed daily returns **2006–2015**. Evaluation: **2016–2025**. Strictly split before any transform or fit.
- Horizons: **1, 2, 4, 8, 16 observed trading days**; disjoint blocks per period, alignment restarts at split, trailing incomplete days discarded. There are 2,517 train and 2,514 evaluation daily observations; the longest horizon has only 157 blocks in each period.
- Parse the first value-weighted daily section; order sectors HiTec, Manuf; divide source percentages by 100. Reject missing sentinels `-99.99`/`-999`, nonfinite or <= -100% returns, duplicate dates and nonchronological ordering. No forward-fill/imputation.
- For sector simple returns `r_t`, use `x_t = log1p(r_t)`. The orthonormal **coarsest Haar scaling coefficient** on a completed h-day block is `a_h = sum(x_t)/sqrt(h)`. Recover the investable sector holding-period return as `R_h = expm1(sqrt(h)*a_h)`.
- PyWavelets Haar coarse scales implement a causal blockwise multiresolution construction. This is **not** a wavelet-bandpass-return study: detail coefficients are signed oscillations, not investable compounded returns. No boundary padding reaches outside a block, and no full-sample transform occurs.
- Start each horizon block at 50% in each sector, hold within the block, rebalance at the next block: `R_p,h = (R_HiTec,h + R_Manuf,h)/2`; loss `L_h = -R_p,h`. Different horizons imply different rebalance schedules. No annualization, square-root scaling, fees, risk-free subtraction or leverage.

### Copulas and benchmarks

Training pseudo-observations are average ranks divided by `(n+1)`. At each horizon maximize bivariate Student-t copula pseudo-likelihood over bounded rho and the explicit df grid in config. Fit Gaussian rho separately by the corresponding rank likelihood. Empirical inverse-CDF margins are shared across simulated models.

1. **horizon_t:** per-horizon t rho and df.
2. **gaussian:** per-horizon Gaussian copula, zero asymptotic tail dependence but generally nonzero finite-threshold dependence.
3. **invariant_t:** reuse the **daily training t rho AND df** at every horizon, while retaining the **same horizon-specific empirical marginals**. This is the controlled scale-invariance ablation; it is not the Gaussian benchmark.
4. **historical:** training historical simulation of actual joint portfolio block returns.

For a t copula, symmetric lower/upper asymptotic dependence is
`lambda = 2 * t_cdf(-sqrt((df+1)*(1-rho)/(1+rho)), df+1)`.
Gaussian lambda is zero for nonsingular correlation. Finite 5% and 10% conditional co-exceedance diagnostics retain event counts, conditioning counts, both tails and period-specific ranks. Evaluation ranks are diagnostic only and never affect forecasts.

Fixed seeds, 100,000 simulated joint returns per reference batch, three seed batches for numerical-sensitivity ranges. VaR is the empirical 95% inverse-CDF **loss** quantile; ES is integrated worst-5% mass, fractionally weighting its boundary order statistic. All model parameters and empirical margins are frozen at training end; **no volatility updating**.

### Evaluation and uncertainty

Actual disjoint evaluation block losses give breach count/rate, exact two-sided binomial coverage p-value and exact binomial intervals (**IID assumption, not guaranteed**), 95% pinball loss, observed mean above forecast VaR and an explicitly descriptive ES residual:

`ES - VaR - mean(max(L - VaR, 0)) / 0.05`.

**VaR coverage does not validate ES.** Residual block intervals and observed breach means do not constitute a standalone ES backtest. A nonsignificant binomial p-value with sparse samples does not prove calibration.

199 circular moving-block bootstrap resamples, length `ceil(20/h)` horizon observations (roughly one trading month). Training resamples refit ranks and t parameters for lambda intervals; separate evaluation resamples yield finite-tail, breach-rate, ES-residual and paired pinball-difference intervals. The effective-n diagnostic is an initial-positive-autocorrelation heuristic for the joint lower-tail indicator. It is not a proven independent sample count. Intervals conditional on fixed forecasts do not include VaR/ES training uncertainty; there is no corrected formal multiple-horizon equality/superiority test. See JSON for all diagnostics and Monte Carlo ranges.

## Actual reference findings

- Observed coverage: **5,031 daily rows**, 2006-01-03 to 2025-12-31; no missing selected values or duplicates. 186 absent weekdays include holidays; exchange-session completeness is not independently established.
- Fitted t tail dependence: roughly **0.618 daily to 0.456 at 16 days**, but 16-day 95% block-bootstrap interval is approximately **[0.013, 0.603]**. Only four joint 5% lower-tail training events remain at 16 days. This is not proof of monotone horizon decay; several shorter-horizon df fits are at the grid's lower boundary.
- Daily horizon-t 95% VaR/ES: **2.000% / 3.190%**; 100 breaches / 2,514 evaluation blocks (**3.978%**), exact IID-binomial p≈0.0173. Sixteen-day VaR/ES: **6.070% / 11.009%**; 8/157 breaches (**5.096%**). Sparse long-horizon coverage does not validate ES.
- The horizon-t model does **not** uniformly beat historical or invariant-t in pinball loss. Gaussian 95% VaR is slightly higher, not automatically understated; ES differences and horizon-invariance effects are small relative to broader uncertainty.
- Recommendation: retain historical simulation as a baseline and show horizon-t versus daily-t/Gaussian ES sensitivity at the actual holding period. **Do not reduce long-horizon limits just because fitted lambda falls.** Require rolling/volatility-updated and point-in-time validation before production.

Numbers above are rounded from `reports/results.json`; the generated report and CSVs are authoritative reference outputs. No profit/performance/causality overclaim is warranted. Limits: one portfolio/split, strong common equity exposure, symmetric t tails, finite empirical support, df-grid boundary fits, revised vintages, no dynamics or regime model, bootstrap-length sensitivity and small long-horizon tails.

## Files and review status

- `src/data.py`: public download/parser, checksum checks, provenance and audit.
- `src/model.py`: causal Haar blocks, rank likelihood copulas, seeded simulation and risk.
- `src/uncertainty.py`, `src/evaluate.py`: time-series bootstrap and evaluation.
- `src/study.py`: single reproduction entry point; `src/report.py`: deterministic figures/reports.
- `tests/`: parser/sentinels/scaling, Haar equivalence, split, positive definiteness, tail formula, seeds, loss sign, future perturbation invariance, real-data offline reproducibility.
- `reports/study.pdf`: **6 body pages**, including figures/tables/references/disclosure; no cover. `reports/study.md`, `results.json`, CSVs, PNGs and provenance are explicitly publishable aggregate artifacts in `.gitignore`; raw caches and `.venv` remain ignored.
- `evidence/`: actual TDD red/green and full-run/offline/hash logs; rendered PDF preview.
- `docs/CHALLENGE.md`: official requirement summary. Planning documents remain historical scaffold, not statements that this study lacks implementation.

**AI assistance:** Hermes Agent (Nous Research), using OpenAI `gpt-6.1-sol`, materially generated methodology/code/tests, executed the real study, and drafted figures/report/documentation. Independent review, understanding of all code, team approval, final submission ZIP/access checks and portal submission are still required. No private identifiers or registration details are included. No commits or pushes were made by the implementing subagent.
