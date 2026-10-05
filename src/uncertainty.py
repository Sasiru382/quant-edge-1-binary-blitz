"""Circular moving-block bootstrap; heuristic effective sample sizes."""
import numpy as np
from .model import ranks, fit_copula, tail_dependence


def block_indices(n, length, rng):
    starts = rng.integers(0, n, size=int(np.ceil(n/length)))
    return ((starts[:,None] + np.arange(length)) % n).ravel()[:n]


def effective_n(indicator, max_lag):
    """Initial-positive autocorrelation sum: descriptive, not independent tail count."""
    x = np.asarray(indicator, dtype=float)
    x -= x.mean()
    denominator = np.dot(x,x)
    if denominator == 0:
        return float(len(x))
    autocorrelation_sum = 0.0
    for lag in range(1, min(max_lag,len(x)-1)+1):
        correlation = np.dot(x[:-lag],x[lag:])/denominator
        if correlation <= 0:
            break
        autocorrelation_sum += correlation
    return float(np.clip(len(x)/(1+2*autocorrelation_sum),1,len(x)))


def finite_tail(values, q):
    u = ranks(np.asarray(values))
    lower = u <= q
    upper = u >= 1-q
    lower_joint = int(np.all(lower,axis=1).sum())
    upper_joint = int(np.all(upper,axis=1).sum())
    lower_count, upper_count = int(lower[:,0].sum()), int(upper[:,0].sum())
    return dict(lower_joint_count=lower_joint, lower_condition_count=lower_count, lower_conditional=lower_joint/lower_count if lower_count else None, upper_joint_count=upper_joint, upper_condition_count=upper_count, upper_conditional=upper_joint/upper_count if upper_count else None)


def mean_interval(values, block_length, replicates, seed):
    values = np.asarray(values)
    rng = np.random.default_rng(seed)
    samples = [values[block_indices(len(values),block_length,rng)].mean() for _ in range(replicates)]
    return np.quantile(samples,[.025,.975]).tolist()


def tail_summary(values, horizon, df_grid, replicates, seed, fit=True):
    values = np.asarray(values)
    length = max(1,int(np.ceil(20/horizon)))
    rng = np.random.default_rng(seed)
    lower, upper, lambdas = [], [], []
    for _ in range(replicates):
        sample = values[block_indices(len(values), length, rng)]
        diagnostic = finite_tail(sample,.05)
        lower.append(diagnostic['lower_conditional'])
        upper.append(diagnostic['upper_conditional'])
        if fit:
            lambdas.append(tail_dependence(fit_copula(sample,'t',df_grid)))
    indicator = np.all(ranks(values)<=.05,axis=1)
    summary = dict(n=len(values), bootstrap_block_length=length, bootstrap_replicates=replicates, effective_n_q05=effective_n(indicator,length), q05=finite_tail(values,.05), q10=finite_tail(values,.10), lower_q05_ci=np.quantile(lower,[.025,.975]).tolist(), upper_q05_ci=np.quantile(upper,[.025,.975]).tolist())
    if fit:
        summary['lambda_ci'] = np.quantile(lambdas,[.025,.975]).tolist()
    return summary
