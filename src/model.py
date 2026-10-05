"""Causal horizon returns and parsimonious rank copulas."""
import numpy as np
import pandas as pd
import pywt


def split_blocks(frame, horizon, split):
    """Completed, disjoint Haar blocks; reset alignment at train/test boundary."""
    if horizon < 1 or horizon & (horizon - 1):
        raise ValueError('horizon must be positive dyadic')
    outputs, audit = [], {}
    for label, part in [('train', frame.loc[frame.index < split]), ('test', frame.loc[frame.index >= split])]:
        n = len(part) // horizon
        logs = np.log1p(part.iloc[:n * horizon].values).reshape(n, horizon, 2)
        if horizon == 1:
            scaling = logs[:, 0, :]
        else:
            scaling = pywt.wavedec(logs, 'haar', level=int(np.log2(horizon)), axis=1, mode='periodization')[0][:, 0, :]
        compounded = np.expm1(np.sqrt(horizon) * scaling)
        outputs.append(pd.DataFrame(compounded, index=part.index[horizon-1:n*horizon:horizon], columns=part.columns))
        audit[label + '_discarded_days'] = len(part) % horizon
        audit[label + '_blocks'] = n
    return *outputs, audit


def ranks(values):
    from scipy.stats import rankdata
    return np.column_stack([rankdata(values[:, j], method='average') for j in range(2)]) / (len(values) + 1)


def fit_copula(values, kind, df_grid):
    """Maximum pseudo-likelihood on training ranks; bounded rho, discrete df."""
    from scipy.stats import t, norm
    from scipy.special import gammaln
    from scipy.optimize import minimize_scalar
    u = ranks(np.asarray(values))
    candidates = []
    for df in df_grid if kind == 't' else [None]:
        z = t.ppf(u, df) if kind == 't' else norm.ppf(u)
        marginal = t.logpdf(z, df).sum(axis=1) if kind == 't' else norm.logpdf(z).sum(axis=1)

        def negative_loglik(rho):
            determinant = 1 - rho * rho
            q = (z[:,0]**2 - 2*rho*z[:,0]*z[:,1] + z[:,1]**2) / determinant
            if kind == 't':
                joint = gammaln((df+2)/2) - gammaln(df/2) - np.log(df*np.pi) - .5*np.log(determinant) - (df+2)/2*np.log1p(q/df)
            else:
                joint = -np.log(2*np.pi) - .5*np.log(determinant) - .5*q
            return float(-np.sum(joint - marginal))

        fit = minimize_scalar(negative_loglik, bounds=(-.98,.98), method='bounded', options={'xatol':1e-7})
        if not fit.success:
            raise RuntimeError('Copula optimization failed')
        candidates.append(dict(kind=kind, rho=float(fit.x), df=df, loglik=float(-fit.fun)))
    return max(candidates, key=lambda item: item['loglik'])


def tail_dependence(params):
    from scipy.stats import t
    if params['kind'] == 'gaussian':
        return 0.0
    rho, df = params['rho'], params['df']
    return float(2*t.cdf(-np.sqrt((df+1)*(1-rho)/(1+rho)), df+1))


def simulate_losses(values, params, size, seed):
    from scipy.stats import t, norm
    rng = np.random.default_rng(seed)
    rho = params['rho']
    # Common normal draws for horizon-t and invariant-t comparisons at same seed.
    z = rng.standard_normal((size, 2)) @ np.linalg.cholesky([[1,rho],[rho,1]]).T
    if params['kind'] == 't':
        z /= np.sqrt(rng.chisquare(params['df'], size)[:,None] / params['df'])
        u = t.cdf(z, params['df'])
    else:
        u = norm.cdf(z)
    ordered = np.sort(np.asarray(values), axis=0)
    indices = np.minimum((u * len(ordered)).astype(int), len(ordered)-1)
    returns = np.column_stack([ordered[indices[:,j],j] for j in range(2)])
    return -returns.mean(axis=1)


def risk(losses, alpha=.95):
    """Empirical inverse-CDF VaR and integrated worst 1-alpha mass ES (ties weighted)."""
    ordered = np.sort(np.asarray(losses))
    var = float(np.quantile(ordered, alpha, method='inverted_cdf'))
    mass = (1-alpha)*len(ordered)
    whole = int(np.floor(mass))
    fraction = mass-whole
    total = ordered[-whole:].sum() if whole else 0.0
    if fraction > 1e-12:
        total += fraction * ordered[-whole-1]
    return var, float(total/mass)
