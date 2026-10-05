"""Out-of-sample coverage and explicitly descriptive ES diagnostics."""
import numpy as np
from scipy.stats import binomtest


def score(losses, var, es, alpha=.95):
    losses = np.asarray(losses)
    breach = losses > var
    count = int(breach.sum())
    result = binomtest(count, len(losses), 1-alpha)
    interval = result.proportion_ci(confidence_level=.95, method='exact')
    difference = losses-var
    return dict(n_test=len(losses), breaches=count, breach_rate=float(breach.mean()), coverage_p_iid=float(result.pvalue), breach_iid_ci_low=float(interval.low), breach_iid_ci_high=float(interval.high), pinball=float(np.maximum(alpha*difference,(alpha-1)*difference).mean()), observed_breach_mean=float(losses[breach].mean()) if count else None, es_residual=float(es-var-np.maximum(difference,0).mean()/(1-alpha)))
