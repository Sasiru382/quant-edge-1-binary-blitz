# Execution evidence

All logs were produced by real local executions in this repository's `.venv`; no fabricated study output is included. Synthetic arrays in unit tests are test fixtures only. Raw French data is local/ignored.

## Vertical TDD tracer bullets

Each numbered functional slice has an observed `NN-name-red.log` before implementation and a succeeding `NN-name-green.log` after implementation plus regression tests:

1. First value-weighted parser and percentage scaling.
2. Missing sentinels, invalid values and duplicate rejection.
3. Pinned local-cache acquisition and checksum failures.
4. Causal Haar aggregation and split/no-straddling behavior.
5. Rank-likelihood copula fit, nonsingular dependence and analytic tails.
6. Seeded empirical-marginal simulation, loss quantile and fractional-tail ES.
7. OOS coverage, pinball and descriptive ES residual. An initial exact-float assertion was corrected to numerical tolerance; the underlying formula was unchanged.
8. Moving-block bootstrap, finite tails and effective sample-size diagnostic.
9. Full model comparison and future perturbation invariance.
10. Observed data coverage/extrema audit.
11. Infinite source-return rejection.
12. Real pinned-data offline CLI numeric reproducibility.
13. Deterministic PNG, Markdown and PDF artifacts.
14. Six-page PDF layout without a spill-only page.

Supplemental final regression checks also verify direct compounding at every configured Haar scale and that an upstream revision failure leaves the validated cache intact. No new production behavior was introduced for those supplemental tests.

## Reference executions

- `download.log`: actual public ZIP acquisition and source provenance.
- `full-study-1.log`, `full-study-2.log`: normal `python -m src.study` reference runs (validated local cache after the real download).
- `full-study-3.log`: `python -m src.study --offline`; no network requests are issued in this mode.
- `run1-hashes.json`, `reproducibility.json`: every published analytical output's SHA256 compared across two normal runs and one offline run, with recorded elapsed time for later runs.
- `final-tests.log`: complete current test suite, including two real-data offline CLI runs under reduced computational settings.
- `pdf-verification.json`, `pdf-preview.png`: actual six-page text/count extraction plus rendered layout review. Report has no cover; all six pages count against the body-page limit.
- `change-statistics.json`: working-tree change accounting and in-memory compressed public-bundle size; no data/.venv contents included. This is a working-tree snapshot, not a commit or approval.

## Commands

```sh
.venv/bin/python -m src.data
.venv/bin/python -m pytest tests -v
.venv/bin/python -m src.study
.venv/bin/python -m src.study --offline
.venv/bin/python -m pip check
.venv/bin/python -m compileall -q src tests
git diff --check
```

Independent scientific/team review, source-terms review and submission approval remain outstanding. No commit, push or submission was performed by the implementation subagent.
