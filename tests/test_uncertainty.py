import numpy as np
from src import uncertainty


def test_block_resampling_tail_uncertainty_and_effective_sample_size():
    x = np.column_stack([np.arange(80),np.arange(80)])
    result = uncertainty.tail_summary(x, horizon=4, df_grid=[4], replicates=9, seed=10)
    assert result['bootstrap_block_length'] == 5
    assert result['n'] == 80
    assert result['q05']['lower_joint_count'] == 4
    assert result['q05']['lower_conditional'] == 1
    assert result['q05']['upper_conditional'] == 1
    assert 1 <= result['effective_n_q05'] <= 80
    assert result['lambda_ci'][0] <= result['lambda_ci'][1]
    assert result == uncertainty.tail_summary(x, horizon=4, df_grid=[4], replicates=9, seed=10)
    ci = uncertainty.mean_interval(np.ones(80)*.2, block_length=5, replicates=9, seed=10)
    np.testing.assert_allclose(ci, [.2,.2],atol=1e-15)
