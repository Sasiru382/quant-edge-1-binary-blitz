# Work plan

Suggested internal checkpoints only; assign owners as a team. No responsibility or completed result is assumed.

## Scope and data
- [ ] Agree on a small portfolio, weights, public source and date range.
- [ ] Check licensing, adjustments, missing observations and calendar alignment.
- [ ] Document returns, train/test dates, confidence level and risk horizon.

## Methods
- [ ] Agree on a simple benchmark and evaluation protocol.
- [ ] Choose wavelet transform, scales and boundary handling; avoid future-data leakage.
- [ ] Fit marginal models and copulas on training data only.
- [ ] Estimate and compare tail dependence by horizon.
- [ ] Calculate risk and assess out-of-sample performance against benchmark.
- [ ] State uncertainty, assumptions, sample-size limits and sensitivity checks.

## Reproducibility and report
- [ ] Add component tests and fixed seeds where needed.
- [ ] Record dependencies and data provenance.
- [ ] Implement a single reproduction entry point.
- [ ] Write the report and one actionable recommendation.
- [ ] Update AI disclosure and ensure everyone understands the implementation.
- [ ] Re-run from a clean environment and compare every reported number/figure.

## Submission
- [ ] Confirm PDF page count and ZIP ≤25 MB.
- [ ] Exclude secrets, irrelevant environments, caches and unnecessary large data.
- [ ] Upload final folder to Drive and test judge access.
- [ ] Team leader submits ZIP/link using registration details privately.
- [ ] Submit before 7 October, 23:59 Sri Lanka time; leave a buffer for upload issues.
