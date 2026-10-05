import numpy as np
import pandas as pd
from src import study


def small_inputs():
    rng = np.random.default_rng(40)
    frame = pd.DataFrame(rng.normal(0,.01,(240,2)), index=pd.bdate_range('2015-07-01',periods=240),columns=['HiTec','Manuf'])
    config = dict(split='2016-01-01',horizons=[1,2],seed=44,simulation_size=1000,bootstrap_replicates=9,df_grid=[4])
    return frame, config


def test_complete_analysis_and_future_perturbation_invariance():
    frame, config = small_inputs()
    a = study.analyze(frame, config)
    frame.loc[frame.index >= config['split']] *= 2
    b = study.analyze(frame, config)
    assert len(a['risk']) == 8
    for first, second in zip(a['risk'],b['risk']):
        assert first['var95'] == second['var95']
        assert first['es95'] == second['es95']
    for first, second in zip(a['dependence'],b['dependence']):
        assert first['t'] == second['t']
        assert first['training'] == second['training']
    daily = [r for r in a['risk'] if r['horizon']==1]
    assert daily[0]['model'] == 'horizon_t'
    assert daily[0]['var95'] == daily[2]['var95']
    assert a['comparisons'][0]['delta_var_vs_invariant'] == 0
