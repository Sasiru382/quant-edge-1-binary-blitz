import numpy as np
import pytest
from scipy.stats import binomtest
from src import evaluate


def test_coverage_pinball_and_es_residual_are_not_es_validation():
    losses = np.array([-.02,0,.01,.02,.08])
    scores = evaluate.score(losses, .02, .04)
    assert scores['breaches'] == 1
    assert scores['breach_rate'] == .2
    assert scores['coverage_p_iid'] == pytest.approx(binomtest(1,5,.05).pvalue)
    assert scores['pinball'] == pytest.approx(np.mean(np.maximum(.95*(losses-.02),-.05*(losses-.02))))
    assert scores['observed_breach_mean'] == .08
    assert scores['es_residual'] == pytest.approx(.04-.02-np.maximum(losses-.02,0).mean()/.05)
