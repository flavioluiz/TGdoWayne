#!/usr/bin/env python3
"""Extrai estimativas tabuladas DRAFT dos caches D2; zero novas likelihoods.

Convergência entre tabelas é um diagnóstico separado da referência incompleta.
Nenhum número produzido aqui é promovido a resultado fisicamente validado.
"""
import json
import os
from pathlib import Path
import resource
import sys

ROOT = Path(__file__).resolve().parents[1]
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[name] = '1'
sys.path[:0] = [str(ROOT / 'tmp/c09_D2_components_v1'),
                str(ROOT / 'tmp/c09_event_repair_v1')]


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (90, 95))
    import numpy as np
    from priors import PriorMeasure
    from posterior_table import PosteriorTable
    from d1.grid import event_grid, exact_union
    from d1.measure import Prior
    dest = ROOT / 'results/C09/D2_retoma'
    audit = json.loads((dest / 'audit.json').read_text())
    assert audit['historical_imports_verified_bitwise']
    config = json.loads((ROOT / 'tmp/c09_D2_runtime_resume_v1/runtime_config.json').read_text())
    nominal = json.loads((ROOT / config['nominal_config']).read_text())
    with np.load(ROOT / nominal['table_file'], allow_pickle=False) as bank:
        nodes = bank['nodes']
    grid = event_grid(nodes, Prior('uniform_u'), validation_count=1)
    edges = np.array([0., 1e-4, 1e-3, .01, .8, 1.])
    coarse = exact_union(grid['coarse_u'], edges)
    fine = exact_union(grid['fine_u'], edges)
    specs = {p['id']: p for p in config['priors']}
    rows = []
    for curve in config['curves']:
        with np.load(ROOT / 'tmp/c09_D2_execution_resume_v1/worker/caches' /
                     (curve['curve_id'] + '.npz'), allow_pickle=False) as cache:
            u, ell = cache['u'], cache['log_likelihood']
            ic, ih = np.searchsorted(u, coarse), np.searchsorted(u, fine)
            assert np.array_equal(u[ic], coarse) and np.array_equal(u[ih], fine)
            lc, lh = ell[ic], ell[ih]
        for prior_id in curve['prior_ids']:
            spec = specs[prior_id]
            prior = PriorMeasure(spec['kind'], spec['lower'], spec['upper'])
            tables = [PosteriorTable(coarse, lc, prior, order=16),
                      PosteriorTable(fine, lh, prior, order=16),
                      PosteriorTable(fine, lh, prior, order=32)]
            summaries = [t.summary() for t in tables]
            q95 = [sum(t.candidate_quantile_bracket(.95))/2 for t in tables]
            rows.append(dict(curve_id=curve['curve_id'], data_id=curve['data_id'],
                analysis=curve['analysis'], prior_id=prior_id, prior=spec,
                status='DRAFT_TABLE_ONLY_REFERENCE_INCOMPLETE',
                table_summaries=summaries, prior_quantile_95=float(prior.ppf(.95)),
                table_quantiles_95=q95,
                delta_quantile_95_tables=max(abs(q-q95[-1]) for q in q95),
                delta_logZ_tables=max(abs(t.logZ-tables[-1].logZ) for t in tables),
                delta_KL_tables=max(abs(t.kl_to_prior-tables[-1].kl_to_prior) for t in tables)))
    usage = resource.getrusage(resource.RUSAGE_SELF)
    result = dict(status='DRAFT_NOT_VALIDATED', analyses=rows,
        analysis_count=len(rows), new_likelihood_values=0, new_ORF=0, new_draws=0,
        CPU_seconds=usage.ru_utime+usage.ru_stime, RSS_bytes=usage.ru_maxrss,
        interpretation='Cached table estimates only. No independent reference completion, no SBC or uniform physical certificate.')
    (dest / 'posteriores_draft.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    selected = [r for r in rows if r['curve_id'] == 'baseline_d2' and
                (r['prior']['upper'] == 1 or r['prior_id'] == 'uniform_u_a0_b0.8')]
    labels = {'uniform_u': 'Uniforme em massa',
              'uniform_u_squared': 'Uniforme em massa ao quadrado',
              'log_uniform_u': 'Logarítmica'}
    lines = [r'\begin{table}[htbp]', r'\centering\small',
        r'\caption{Estimativas tabuladas DRAFT para a mesma observação ID~2, análise A0. Referências funcionais incompletas; números sem aprovação física.}',
        r'\label{tab:d2-draft-prioris}',
        r'\begin{tabular}{@{}lrrrr@{}}\toprule',
        r'Priori e suporte & $Q_{0,95}^{\pi}$ & $Q_{0,95}^{\rm tab}$ & $E_{\rm tab}[u]$ & $D_{\rm KL}^{\rm tab}$ \\',
        r'\midrule']
    for r in selected:
        p = r['prior']; s = r['table_summaries'][-1]
        label = labels[p['kind']] + f" $[{p['lower']:g},{p['upper']:g}]$"
        nums = [r['prior_quantile_95'], r['table_quantiles_95'][-1], s['mean'], s['kl_to_prior']]
        lines.append(label + ' & ' + ' & '.join(f'{v:.4f}' for v in nums) + r' \\')
    lines += [r'\bottomrule\end{tabular}', r'\end{table}',
        r'\noindent A divergência é expressa em nats. O quantil tabulado é o da interpolação positiva da likelihood salva; não é um intervalo de confiança nem uma aprovação da quadratura independente.']
    table_path = ROOT / 'latex/tabelas/d2_retoma_draft.tex'
    table_path.parent.mkdir(exist_ok=True)
    table_path.write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'analyses'}, indent=2))


if __name__ == '__main__':
    main()
