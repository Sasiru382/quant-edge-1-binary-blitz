"""Deterministic figures and a six-body-page evidence report (not submission approved)."""
from pathlib import Path
from html import escape
import numpy as np


def figures(results, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    horizons = [d['horizon'] for d in results['dependence']]
    dependence = results['dependence']
    values = np.array([d['lambda_t'] for d in dependence])
    ci = np.array([d['training']['lambda_ci'] for d in dependence])
    fig, ax = plt.subplots(figsize=(7.2,3.0),layout='constrained')
    ax.plot(horizons,values,'o-',label='Fitted t asymptotic lower/upper tail')
    ax.vlines(horizons,ci[:,0],ci[:,1],alpha=.7,label='95% block-bootstrap percentile interval')
    ax.plot(horizons,[d['training']['q05']['lower_conditional'] for d in dependence],'s--',label='Training finite 5% lower conditional')
    ax.plot(horizons,[d['evaluation']['q05']['lower_conditional'] for d in dependence],'^:',label='Evaluation finite 5% lower conditional')
    ax.axhline(0,color='gray',linewidth=.8,label='Gaussian asymptotic tail = 0')
    ax.set(xlabel='Horizon (observed trading days)',ylabel='Tail dependence / conditional frequency',ylim=(-.03,1.03),xticks=horizons)
    ax.legend(fontsize=7,loc='upper right')
    fig.savefig(output/'tail_dependence.png',dpi=160,metadata={'Software':'French copula Haar study'})
    plt.close(fig)
    fig, axes = plt.subplots(1,2,figsize=(7.2,2.8),layout='constrained')
    for model in ['horizon_t','gaussian','invariant_t','historical']:
        rows = [r for r in results['risk'] if r['model']==model]
        for ax, key in zip(axes,['var95','es95']):
            ax.plot(horizons,[100*r[key] for r in rows],'o-',label=model,markersize=3)
    axes[0].set(ylabel='Loss (% of block-start wealth)',title='95% VaR')
    axes[1].set(title='95% ES')
    for ax in axes:
        ax.set(xlabel='Trading-day horizon',xticks=horizons)
    axes[1].legend(fontsize=7)
    fig.savefig(output/'risk.png',dpi=160,metadata={'Software':'French copula Haar study'})
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.2,2.8),layout='constrained')
    for model in ['horizon_t','gaussian','invariant_t','historical']:
        rows = [r for r in results['risk'] if r['model']==model]
        ax.plot(horizons,[10000*r['pinball'] for r in rows],'o-',label=model,markersize=3)
    ax.set(xlabel='Trading-day horizon',ylabel='Mean 95% pinball loss (basis points)',xticks=horizons)
    ax.legend(fontsize=7)
    fig.savefig(output/'pinball.png',dpi=160,metadata={'Software':'French copula Haar study'})
    plt.close(fig)


def report(results, output):
    """All displayed calculations derive from the same numeric results object."""
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    output = Path(output)
    figures(results,output)
    styles = getSampleStyleSheet()
    styles['Normal'].fontSize = 8.5
    styles['Normal'].leading = 11
    styles['Heading1'].fontSize = 16
    styles['Heading2'].fontSize = 11
    story, markdown = [], []
    audit, config, provenance = results['audit'], results['config'], results['provenance']

    def heading(text, page=False):
        if page:
            story.append(PageBreak())
        story.append(Paragraph(escape(text),styles['Heading1']))
        markdown.append('\n# '+text+'\n')

    def paragraph(text):
        story.append(Paragraph(escape(text),styles['Normal']))
        story.append(Spacer(1,7))
        markdown.append(text+'\n')

    def table(headers, rows):
        cells = [headers]+[[str(item) for item in row] for row in rows]
        t = Table(cells,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),7),('LEADING',(0,0),(-1,-1),9),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5edf5')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f7fa')]),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
        story.extend([t,Spacer(1,9)])
        markdown.extend(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,row))+' |' for row in rows]+[''])

    def image(name, height=185):
        story.extend([Image(str(output/name),width=480,height=height),Spacer(1,7)])
        markdown.append(f'![{name}]({name})\n')

    def interval(ci, factor=1):
        return f'[{ci[0]*factor:.3f}, {ci[1]*factor:.3f}]'

    heading('Risk across tails and Haar horizons: HiTec + Manuf')
    paragraph('Evidence draft for human/team review; NOT submission approved. Question: does fitted tail dependence change with horizon, and how much risk changes when dependence is held invariant or Gaussian? A fixed 2006-2015 model is evaluated on untouched 2016-2025 returns. This is a risk-model comparison, not a trading strategy or causal study.')
    paragraph(f"Data: first value-weighted daily section of Kenneth French 5 Industry Portfolios; sectors HiTec and Manuf. Selected coverage {audit['first_date']} through {audit['last_date']}: {audit['rows']} observed dates; training {audit['train_rows']}, evaluation {audit['test_rows']}. Percentage returns are divided by 100. Missing sentinels -99.99/-999, nonfinite/invalid returns, duplicate and unsorted dates are rejected, not imputed.")
    paragraph(f"Audit: {audit['missing_values']} missing values, {audit['nonfinite_values']} nonfinite values, {audit['duplicate_dates']} duplicate dates. There are {audit['absent_weekdays_between_observed_endpoints']} absent weekdays between observed endpoints; these include exchange holidays and are not established missing trading sessions. No independent exchange-calendar completeness claim is made. Full year counts and extrema dates are in results.json.")
    table(['Sector','Minimum daily (%)','Maximum daily (%)','Mean daily (%)'],[[s,f"{100*v['min']:.3f}",f"{100*v['max']:.3f}",f"{100*v['mean']:.4f}"] for s,v in audit['sector_extrema'].items()])
    paragraph('Choose two broad US sector research portfolios to keep estimation interpretable: technology and manufacturing provide distinct labels but are strongly exposed to common equity shocks. These are research portfolios, not frictionless tradeable ETFs. Source construction assigns NYSE/AMEX/NASDAQ stocks by SIC at June-end; the present archive is revised historical data, not point-in-time vintages. The library documents its 2025 FIZ-to-CIZ format change.')
    paragraph('Causal Haar construction: for h = 1,2,4,8,16, x_t = log(1+r_t). On each completed disjoint block, orthonormal Haar coarse coefficient a_h = sum(x_t)/sqrt(h). Recover the actual sector holding-period return R_h = exp(sqrt(h)*a_h)-1. PyWavelets computes the coarsest scaling coefficient within each block. At h=1 the transform is identity. This is a wavelet multiresolution scaling/coarse approximation, NOT a band-pass detail-return study; Haar details describe signed oscillations and cannot be compounded as investable returns.')
    paragraph('Portfolio starts every h-day block with 50% wealth in each sector and holds those sector exposures until block-end, then rebalances: R_p,h = (R_HiTec,h + R_Manuf,h)/2; loss L_h = -R_p,h. This is not daily rebalancing inside multi-day blocks. No annualization, square-root-of-time risk scaling, risk-free subtraction, fees or leverage. Split before transformations; align separately at first training and evaluation observation. Incomplete terminal blocks are discarded. No block straddles the split and no full-sample transform/filter is used.')

    heading('Dependence estimation and tail uncertainty',page=True)
    paragraph(f"Ranks U_ij = rank(R_ij)/(n+1), with average ties, train each horizon independently. Maximize bivariate Student-t copula pseudo-log-likelihood sum(log f_t,2(z1,z2;rho,nu) - log f_t(z1;nu) - log f_t(z2;nu)), z_j=t_nu inverse(U_j), rho bounded [-0.98,0.98], nu grid {config['df_grid']}. Gaussian rho is separately fitted by the corresponding normal copula likelihood. Empirical margins stay the same across all simulated copulas. Grid/bounds are numerical/model restrictions, not evidence of a true tail law; boundary fits especially require caution.")
    paragraph('Student-t symmetric asymptotic lower/upper tail lambda = 2*t_(nu+1)(-sqrt((nu+1)*(1-rho)/(1+rho))). Gaussian lambda=0 for |rho|<1, but its finite-threshold co-exceedance need not be zero. Finite lower diagnostic is Pr(U_Manuf <= q | U_HiTec <= q), upper analog at 1-q. Each period is ranked independently for diagnostics only; evaluation ranks never set forecasts. Results include q=0.05 and q=0.10 and both tails. Symmetric t cannot represent asymmetric crash/rally dependence.')
    table(['h','n train','rho t','nu','lambda t','95% lambda interval','n effective*'],[[d['horizon'],d['training']['n'],f"{d['t']['rho']:.3f}",d['t']['df'],f"{d['lambda_t']:.3f}",interval(d['training']['lambda_ci']),f"{d['training']['effective_n_q05']:.1f}"] for d in results['dependence']])
    image('tail_dependence.png',190)
    paragraph(f"Uncertainty: {config['bootstrap_replicates']} seeded circular moving-block resamples of paired horizon observations; block length ceil(20/h), approximately one trading month. Refit ranks and t likelihood per training resample, report 2.5/97.5 percentile intervals. Separate evaluation finite-tail resamples never affect forecasts. *Effective n is an initial-positive-autocorrelation heuristic for the lower joint 5% indicator, not a proven count of independent observations. Overlapping intervals alone are not a formal equality test. Horizon estimates are dependent; no formal multiple-horizon significance claim is made.")
    paragraph('Point estimates vary with horizon, but this sample does not establish a reliable monotone horizon law. Long-horizon intervals are broad and only a few joint-tail events remain. A single stationary fit blends crisis/non-crisis states; uncertainty conditional on this choice does not cover all regime or grid misspecification.')

    heading('Measured holding-period risk and controlled ablation',page=True)
    paragraph(f"Simulate {config['simulation_size']:,} paired uniforms per copula with seed {config['seed']}+h, then empirical inverse-CDF sector margins (no extrapolation past training extremes). Compute the equal-weight portfolio loss. VaR is the empirical 95% inverse-CDF loss quantile. ES is the integrated worst 5% loss mass, with a fractional order statistic at the boundary to handle ties exactly. Three deterministic independent Monte Carlo seed batches quantify numerical sensitivity; JSON stores their min/max ranges, not statistical confidence intervals.")
    paragraph('Models: horizon_t refits both rho and nu per scale; gaussian removes asymptotic tail dependence but has its own fitted correlation; invariant_t reuses DAILY TRAINING t rho and nu at every horizon with that horizon\'s SAME empirical margins; historical samples the observed training joint portfolio distribution. The invariant_t comparison isolates scale dependence within the t family. Gaussian comparison changes copula family/shape and cannot alone isolate horizon invariance. Models are frozen after training, with no volatility updating.')
    table(['h','Model','VaR95 (%)','ES95 (%)'],[[r['horizon'],r['model'],f"{100*r['var95']:.4f}",f"{100*r['es95']:.4f}"] for r in results['risk']])
    image('risk.png',180)
    table(['h','t-Gauss VaR (bp)','t-Gauss ES (bp)','t-invariant VaR (bp)','t-invariant ES (bp)'],[[r['horizon'],f"{1e4*r['delta_var_vs_gaussian']:.2f}",f"{1e4*r['delta_es_vs_gaussian']:.2f}",f"{1e4*r['delta_var_vs_invariant']:.2f}",f"{1e4*r['delta_es_vs_invariant']:.2f}"] for r in results['comparisons']])
    paragraph('Positive differences mean the horizon-t risk estimate is larger; signs are not presumed. Tail dependence does not imply every 95% quantile rises: dependence shape, high common correlation, and finite empirical margins matter. Small differences can be comparable to Monte Carlo variation or much smaller than estimation uncertainty. Daily t and invariant-t agree exactly by design.')

    heading('Actual out-of-sample backtest',page=True)
    paragraph('Each completed evaluation block contributes one actual portfolio loss; no overlaps within a horizon. Forecasts are constant within each horizon. Breach = observed loss strictly above VaR; target 5%. Exact two-sided binomial p-values and Clopper-Pearson intervals assume independent identically distributed breaches, an assumption not assured by financial time series. Serially dependent data motivate additional moving-block breach-rate intervals in JSON. Multiple models/horizons are descriptive comparisons, not corrected hypothesis tests.')
    table(['h','Model','n test','Breaches','Rate (%)','Binomial p*','Pinball (bp)'],[[r['horizon'],r['model'],r['n_test'],r['breaches'],f"{100*r['breach_rate']:.2f}",f"{r['coverage_p_iid']:.4f}",f"{1e4*r['pinball']:.3f}"] for r in results['risk']])
    image('pinball.png',180)
    paragraph('95% pinball loss = mean(max(0.95*(L-VaR), -0.05*(L-VaR))); lower is better, in loss units. It jointly penalizes breaches and unnecessarily high quantiles; breach rates alone do not rank models. Different horizon losses have different units of holding-period exposure, so do not interpret increasing cross-horizon pinball as declining model quality.')
    paragraph('The horizon-specific t model is not uniformly best against historical or invariant-t. Short-horizon fixed forecasts can be overly conservative, while crisis losses still cluster; a nonsignificant coverage test at a sparse horizon is not proof of calibration. No trading-profit, investable-strategy, causal, or universal superiority claim is supported.')

    heading('Small tails and ES: diagnostics, not validation',page=True)
    table(['h','Train lower joint / cond.','Train lower freq [95% CI]','Eval lower joint / cond.','Eval lower freq [95% CI]'],[[d['horizon'],f"{d['training']['q05']['lower_joint_count']}/{d['training']['q05']['lower_condition_count']}",f"{d['training']['q05']['lower_conditional']:.3f} {interval(d['training']['lower_q05_ci'])}",f"{d['evaluation']['q05']['lower_joint_count']}/{d['evaluation']['q05']['lower_condition_count']}",f"{d['evaluation']['q05']['lower_conditional']:.3f} {interval(d['evaluation']['lower_q05_ci'])}"] for d in results['dependence']])
    paragraph('Finite 5% conditional frequencies are not asymptotic lambda estimates. At the longest horizon only a handful of conditioning observations remain, and bootstrap ties may reduce rank counts further. Full upper-tail and 10% diagnostics, effective sample sizes, and incomplete-block counts are retained in results.json.')
    paragraph('ES is not validated by the VaR coverage test. Descriptive ES residual = ES - VaR - mean(max(L-VaR,0))/0.05; zero is a calibration moment when VaR and ES are jointly correct (with quantile/tie qualifications). It is not a standalone ES test. Observed mean loss above forecast VaR is also stored, but differs from an unconditional 5%-tail ES when coverage differs. Positive residual means the forecast excess-tail budget is above observed average excess loss, not proven conservatism under future stress.')
    table(['h','Model','ES residual (%)','95% block interval (%)'],[[r['horizon'],r['model'],f"{100*r['es_residual']:.4f}",interval(r['es_residual_block_ci'],100)] for r in results['risk']])
    table(['h','Pinball t-HS (bp)','Paired 95% block interval (bp)','Pinball t-invariant (bp)','Paired interval (bp)'],[[r['horizon'],f"{1e4*r['pinball_difference_vs_historical']:.4f}",interval(r['pinball_difference_ci_vs_historical'],1e4),f"{1e4*r['pinball_difference_vs_invariant']:.4f}",interval(r['pinball_difference_ci_vs_invariant'],1e4)] for r in results['comparisons']])
    paragraph('Paired bootstrap intervals resample evaluation loss differences at common block indices, conditional on frozen forecasts; they do not include training-parameter uncertainty or correct for multiple comparisons. Bootstrap length is a transparent fixed choice rather than optimally estimated; sensitivity to other lengths/regimes remains future work. Historical empirical margins truncate possible novel crashes and simulation cannot fix that.')

    heading('Recommendation, provenance and reproducibility',page=True)
    longest = max(results['dependence'],key=lambda d:d['horizon'])
    first = min(results['dependence'],key=lambda d:d['horizon'])
    paragraph(f"Answer: fitted symmetric t tail dependence changes from {first['lambda_t']:.3f} at {first['horizon']} day to {longest['lambda_t']:.3f} at {longest['horizon']} days, with longest-horizon 95% interval {interval(longest['training']['lambda_ci'])}. This is suggestive variation, not established horizon decay: there are only {longest['training']['n']} training blocks and {longest['training']['q05']['lower_joint_count']} joint 5% lower-tail events at that horizon. Gaussian and invariant-t risk differences are measured separately above; ignoring tails is not shown to mechanically understate every 95% VaR.")
    paragraph('Actionable recommendation: retain historical simulation as a transparent baseline and add an explicit horizon-specific t-versus-daily-t/ Gaussian ES sensitivity panel to each holding-period risk review. Do not reduce long-horizon limits because fitted lambda fell; sparse tails and wide intervals do not support that decision. Require a separate rolling/volatility-updated, point-in-time validation before production use, rather than declaring this frozen model superior.')
    paragraph('Main limitations: one two-sector portfolio, one split, high dependence, coarse df grid (some lower-bound fits), symmetric tails, rank ties, finite empirical support, no volatility/regime updating, overlapping information across scales, month-length bootstrap choice, no parameter-uncertainty interval for VaR/ES, and revised historical source vintages. Strict chronological fitting prevents algorithmic look-ahead, not vintage revision bias. Sensitivity ranges across three Monte Carlo batches measure only numerical randomness.')
    paragraph('One command after installing locked dependencies: python -m src.study. It acquires/pin-checks data and regenerates results JSON/CSV, all three figures, this markdown/PDF evidence report and provenance. python -m src.study --offline uses the validated local cache; --refresh checks upstream and fails clearly on revision without replacing the pinned cache. No raw or selected French data is distributed. A fresh download after upstream changes may be blocked until the snapshot is deliberately reviewed and repinned; an existing validated local cache is the fallback, not a promise of perpetual public-byte availability.')
    paragraph('Source: '+provenance['url'])
    paragraph('Accessed UTC: '+str(provenance['accessed_utc'])+'; source archive header: '+provenance['source_header'])
    paragraph('Archive SHA256: '+provenance['archive_sha256'])
    paragraph('Canonical selected snapshot SHA256: '+provenance['snapshot_sha256'])
    paragraph('Selected snapshot serialization: date,HiTec,Manuf CSV; ISO dates, decimal returns at 8 fractional digits, LF line endings. Source detail/library pages carry Fama/French copyright; public accessibility is NOT proof of an open redistribution licence. Consult source terms independently. Public download code plus aggregate analytical outputs are provided, not French raw tables.')
    paragraph('References: Kenneth French Data Library, 5 Industry Portfolios detail: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_5_ind_port.html ; library revision/format notes: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html ; PyWavelets Haar multiresolution implementation; SciPy rankdata, t distributions, bounded optimization and exact binomtest. All statistical formulas used are stated here and in code.')
    paragraph('AI disclosure: Hermes Agent (Nous Research), OpenAI gpt-6.1-sol, materially assisted methodology, implementation, tests, execution, figures and report drafting. Tests and real downloaded data were executed; independent human/team review and submission approval remain outstanding. Team members must understand and be able to modify and reproduce all calculations. See docs/AI_USAGE.md and evidence/ for red/green and reproduction logs.')
    def footer(canvas, doc):
        canvas.setFont('Helvetica',7)
        canvas.drawString(38,22,'Evidence draft - human review required - no submission approval')
        canvas.drawRightString(A4[0]-38,22,f'Body page {doc.page}')
    doc = SimpleDocTemplate(str(output/'study.pdf'),pagesize=A4,rightMargin=38,leftMargin=38,topMargin=32,bottomMargin=35,title='Risk across tails and Haar horizons',author='Research study; AI assistance disclosed',invariant=1)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    (output/'study.md').write_text('\n'.join(markdown)+'\n')
