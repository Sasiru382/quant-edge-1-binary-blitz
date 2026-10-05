"""One-command, deterministic French two-sector horizon risk study."""
import numpy as np
from .model import split_blocks, fit_copula, tail_dependence, simulate_losses, risk
from .evaluate import score
from .uncertainty import tail_summary, mean_interval


def analyze(frame, config):
    results = dict(risk=[], dependence=[], comparisons=[], block_audit=[])
    daily_train, _, _ = split_blocks(frame, 1, config['split'])
    daily_params = fit_copula(daily_train.values,'t',config['df_grid'])
    for horizon in config['horizons']:
        train, test, audit = split_blocks(frame,horizon,config['split'])
        seed = config['seed'] + horizon
        length = max(1,int(np.ceil(20/horizon)))
        reps = config['bootstrap_replicates']
        t_params = fit_copula(train.values,'t',config['df_grid'])
        gaussian = fit_copula(train.values,'gaussian',config['df_grid'])
        train_uncertainty = tail_summary(train.values,horizon,config['df_grid'],reps,seed)
        test_diagnostic = tail_summary(test.values,horizon,config['df_grid'],reps,seed+100,fit=False)
        results['dependence'].append(dict(horizon=horizon,t=t_params,gaussian=gaussian,lambda_t=tail_dependence(t_params),training=train_uncertainty,evaluation=test_diagnostic))
        results['block_audit'].append(dict(horizon=horizon, **audit))
        losses = -test.values.mean(axis=1)
        forecasts = {}
        for name, params in [('horizon_t',t_params),('gaussian',gaussian),('invariant_t',daily_params),('historical',None)]:
            if params is None:
                var, es = risk(-train.values.mean(axis=1))
                repeats = [(var,es)]*3
            else:
                repeats = [risk(simulate_losses(train.values,params,config['simulation_size'],seed+10000*k)) for k in range(3)]
                var, es = repeats[0]
            metrics = score(losses,var,es)
            metrics['breach_block_ci'] = mean_interval((losses>var).astype(float),length,reps,seed)
            residuals = es-var-np.maximum(losses-var,0)/.05
            metrics['es_residual_block_ci'] = mean_interval(residuals,length,reps,seed)
            results['risk'].append(dict(horizon=horizon,model=name,n_train=len(train),var95=var,es95=es,mc_var_range=[float(min(r[0] for r in repeats)),float(max(r[0] for r in repeats))],mc_es_range=[float(min(r[1] for r in repeats)),float(max(r[1] for r in repeats))], **metrics))
            forecasts[name] = (var,es)
        t_var, t_es = forecasts['horizon_t']
        comparison = dict(horizon=horizon)
        for name in ['gaussian','invariant_t','historical']:
            var, es = forecasts[name]
            short = 'invariant' if name=='invariant_t' else name
            comparison['delta_var_vs_'+short] = float(t_var-var)
            comparison['delta_es_vs_'+short] = float(t_es-es)
            t_pinball = np.maximum(.95*(losses-t_var),-.05*(losses-t_var))
            baseline_pinball = np.maximum(.95*(losses-var),-.05*(losses-var))
            difference = t_pinball-baseline_pinball
            comparison['pinball_difference_vs_'+short] = float(difference.mean())
            comparison['pinball_difference_ci_vs_'+short] = mean_interval(difference,length,reps,seed)
        results['comparisons'].append(comparison)
    return results


def run(config, output, offline=False, refresh=False):
    import json
    from pathlib import Path
    import pandas as pd
    from .data import acquire, audit_returns
    root = Path(__file__).resolve().parents[1]
    frame, provenance = acquire(config, root/'data', offline=offline, refresh=refresh)
    results = analyze(frame,config)
    results.update(config=config, provenance=provenance, audit=audit_returns(frame,config['split']))
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    (output/'results.json').write_text(json.dumps(results,indent=2,sort_keys=True,allow_nan=False)+'\n')
    for key in ['risk','comparisons','block_audit']:
        pd.DataFrame(results[key]).to_csv(output/(key+'.csv'),index=False,float_format='%.12g',lineterminator='\n')
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2,sort_keys=True)+'\n')
    from .report import report
    report(results,output)
    print(json.dumps(dict(rows=len(frame),horizons=config['horizons'],risk_rows=len(results['risk']),output=str(output)),sort_keys=True))
    return results


def main():
    import argparse
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline',action='store_true')
    parser.add_argument('--refresh',action='store_true')
    parser.add_argument('--config',type=Path,default=root/'config/study.json')
    parser.add_argument('--out',type=Path,default=root/'reports')
    args = parser.parse_args()
    run(json.loads(args.config.read_text()),args.out,args.offline,args.refresh)


if __name__ == '__main__':
    main()
