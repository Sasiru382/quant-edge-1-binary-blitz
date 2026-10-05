import numpy as np
import pandas as pd
import pytest
from src import model


def test_haar_coarse_scaling_recovers_compounding_without_straddles():
    dates = pd.to_datetime(['2015-12-28','2015-12-29','2015-12-30','2015-12-31','2016-01-04','2016-01-05','2016-01-06'])
    frame = pd.DataFrame(np.arange(14).reshape(7,2)/1000, index=dates, columns=['HiTec','Manuf'])
    train, test, audit = model.split_blocks(frame, 2, '2016-01-01')
    expected = np.prod(1 + frame.iloc[:4].values.reshape(2,2,2), axis=1) - 1
    np.testing.assert_allclose(train.values, expected, atol=1e-15)
    np.testing.assert_allclose(test.values, np.prod(1+frame.iloc[4:6].values,axis=0)[None,:]-1,atol=1e-15)
    assert max(train.index) < pd.Timestamp('2016-01-01') <= min(test.index)
    assert audit['train_discarded_days'] == 0
    assert audit['test_discarded_days'] == 1
    with pytest.raises(ValueError, match='dyadic'):
        model.split_blocks(frame, 3, '2016-01-01')


@pytest.mark.parametrize('horizon', [1,2,4,8,16])
def test_each_dyadic_haar_scale_agrees_with_direct_compounding(horizon):
    rng = np.random.default_rng(18)
    frame = pd.DataFrame(rng.uniform(-.08,.08,(65,2)), index=pd.bdate_range('2015-11-18',periods=65), columns=['HiTec','Manuf'])
    split = frame.index[32].strftime('%Y-%m-%d')
    train, test, audit = model.split_blocks(frame,horizon,split)
    for blocks, part in [(train,frame.iloc[:32]),(test,frame.iloc[32:])]:
        count = len(part)//horizon
        expected = np.prod(1+part.iloc[:count*horizon].values.reshape(count,horizon,2),axis=1)-1
        np.testing.assert_allclose(blocks.values,expected,rtol=1e-12,atol=1e-14)
    assert train.index.max() < pd.Timestamp(split) <= test.index.min()


def test_rank_likelihood_fit_positive_definite_and_tail():
    rng = np.random.default_rng(20)
    z = rng.multivariate_normal([0,0], [[1,.7],[.7,1]], size=500)
    x = z / np.sqrt(rng.chisquare(4,500)[:,None]/4)
    params = model.fit_copula(x, 't', [3,4,7,30])
    assert abs(params['rho']) < 1
    assert np.linalg.eigvalsh([[1, params['rho']], [params['rho'],1]]).min() > 0
    assert params['df'] in [3,4,7,30]
    assert 0 < model.tail_dependence(params) < 1
    normal = model.fit_copula(x, 'gaussian', [3,4,7,30])
    assert model.tail_dependence(normal) == 0
    assert model.tail_dependence(dict(kind='t',rho=.7,df=4)) == pytest.approx(.3906840165, rel=1e-8)


def test_seeded_simulation_empirical_marginals_loss_sign_and_es():
    x = np.array([[-.04,-.02],[-.01,0],[.01,.02],[.02,.04]])
    params = dict(kind='t',rho=.5,df=4)
    a = model.simulate_losses(x, params, 1000, seed=7)
    b = model.simulate_losses(x, params, 1000, seed=7)
    np.testing.assert_array_equal(a, b)
    assert set(np.unique(a)).issubset(set((-x[:,0,None]/2-x[:,1]/2).ravel()))
    assert not np.array_equal(a, model.simulate_losses(x, params, 1000, seed=8))
    var, es = model.risk(np.array([-.02,-.01,0,.01,.02,.10]))
    assert var == .10
    assert es == .10
    assert model.risk(np.array([-.04,-.02])) == (-.02,-.02)
