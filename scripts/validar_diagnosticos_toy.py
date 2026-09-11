#!/usr/bin/env python3
"""Cheap analytic TOY diagnostics; never loads or simulates PTA observations."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time
import numpy as np
import scipy
from scipy import integrate, stats
from scipy.special import ndtr

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'src'))
from inference.diagnostics import (diagnose_sbc, fixed_injection_summary, paired_summary,
                         prior_return_summary, binomial_summary)


def analytic_crosschecks(sigma):
    """Independent 1D density integration and normal-tail logL checks."""
    v = 1 / (1 + 1 / sigma**2)
    sd = np.sqrt(v)
    posterior_errors, loglikelihood_errors, tail_quadrature_errors = [], [], []
    for y in [-2., -.7, .2, 1.3]:
        m = v * y / sigma**2
        density = lambda t: stats.norm.pdf(t) * stats.norm.pdf(y, loc=t, scale=sigma)
        z = integrate.quad(density, -np.inf, np.inf, epsabs=1e-13, epsrel=1e-13)[0]
        for t in [-.6, .1, 1.]:
            cdf_quad = integrate.quad(density, -np.inf, t, epsabs=1e-13, epsrel=1e-13)[0] / z
            posterior_errors.append(abs(cdf_quad - ndtr((t - m) / sd)))
            radius = abs(y - t)
            for a, s in [(m, sd), (0., 1.)]:
                analytic = stats.ncx2.sf(radius**2 / s**2, 1, (y - a)**2 / s**2)
                normal_tails = stats.norm.cdf(y - radius, loc=a, scale=s) + stats.norm.sf(y + radius, loc=a, scale=s)
                p = lambda x: stats.norm.pdf(x, loc=a, scale=s)
                quadrature = integrate.quad(p, -np.inf, y - radius, epsabs=1e-13, epsrel=1e-13)[0] + integrate.quad(p, y + radius, np.inf, epsabs=1e-13, epsrel=1e-13)[0]
                loglikelihood_errors.append(abs(analytic - normal_tails))
                tail_quadrature_errors.append(abs(analytic - quadrature))
    return dict(maximum_posterior_cdf_error=float(max(posterior_errors)),
                maximum_loglikelihood_cdf_normal_tail_error=float(max(loglikelihood_errors)),
                maximum_loglikelihood_cdf_quadrature_error=float(max(tail_quadrature_errors)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BASE / 'results/C07/toy')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    config_path = BASE / 'configs/calibration/diagnostics_v1.json'
    config = json.loads(config_path.read_text())
    tc = config['toy']
    n, p = tc['repetitions'], tc['dimension']
    sigma, tau = tc['observation_sd'], tc['prior_sd']
    rng = np.random.Generator(np.random.PCG64(tc['seed']))
    truth = rng.normal(0, tau, (n, p))
    observed = truth + sigma * rng.normal(size=(n, p))
    v = 1 / (1 / tau**2 + 1 / sigma**2)
    means = v * observed / sigma**2
    sd = np.sqrt(v)
    probs = np.array(config['quantile_probabilities'])
    quantiles = np.stack([means[..., None] + sd * stats.norm.ppf(probs),
                         np.broadcast_to(tau * stats.norm.ppf(probs), (n, p, 4))])
    pit = np.stack([ndtr((truth - means) / sd), ndtr(truth / tau)])
    distance2 = np.sum((observed - truth)**2, axis=1)
    loglikelihood_pit = np.stack([
        stats.ncx2.sf(distance2 / v, p, np.sum((observed - means)**2, axis=1) / v),
        stats.ncx2.sf(distance2 / tau**2, p, np.sum(observed**2, axis=1) / tau**2)])
    methods = ['TOY_EXACT', 'TOY_IGNORES_DATA_RETURNS_PRIOR']
    parameters = [f'theta_{j}' for j in range(p)]
    groups = {'toy_correct': [methods[0]], 'toy_negative': [methods[1]]}
    reports = {}
    for size in [tc['predeclared_prefix_repetitions'], n]:
        reports[str(size)] = diagnose_sbc(pit[:, :size], quantiles[:, :size], truth[:size], loglikelihood_pit[:, :size],
            methods=methods, parameters=parameters, probabilities=probs, groups=groups,
            replicate_ids=list(range(size)), expected_n=size, numerical_complete=True,
            alpha=config['alpha'], pit_error_sensitivity=0.0)
    cross = analytic_crosschecks(sigma)
    alpha = config['alpha']
    paired = []
    for j in range(p):
        hit = (quantiles[:, :, j, 0] <= truth[:, j]) & (truth[:, j] <= quantiles[:, :, j, 3])
        paired.append(dict(parameter=parameters[j], **paired_summary(hit[0].astype(int), hit[1].astype(int), range(n), range(n))))
    prior_quantiles = np.broadcast_to(tau * stats.norm.ppf(probs), (p, 4))
    prior_checks = {method: prior_return_summary(quantiles[j], prior_quantiles, np.full(p, tau)) for j, method in enumerate(methods)}
    # Data intervention fixed beforehand: y=0 versus y=1 in every coordinate.
    prior_checks['intervention'] = dict(exact_mean_change=v / sigma**2, prior_algorithm_mean_change=0.0,
        two_datasets='all zero versus all one, chosen analytically, not selected from simulated results')
    rng_boundary = np.random.Generator(np.random.PCG64(tc['boundary_seed']))
    boundaries = []
    for true_u in tc['boundary_truths']:
        y = true_u + tc['boundary_observation_sd'] * rng_boundary.normal(size=tc['boundary_repetitions_each'])
        s = tc['boundary_observation_sd']
        qs = stats.truncnorm.ppf(probs[None, :], -y[:, None] / s, (1 - y[:, None]) / s, loc=y[:, None], scale=s)
        boundaries.append(fixed_injection_summary(qs, true_u, lower_support=0., upper_support=1.))
    null500 = {str(prob): binomial_summary(np.arange(500) < int(round(500 * prob)), prob) for prob in [.05, .5, .9, .95]}
    negative_ll = next(row for row in reports[str(n)]['tests'] if row['group'] == 'toy_negative' and row['diagnostic'] == 'PIT' and row['target'] == 'logL_at_truth')
    toy_status = all(x < tc['deterministic_crosscheck_tolerance'] for x in cross.values()) and negative_ll['holm_pvalue'] <= tc['negative_loglikelihood_detection_threshold']
    summary = dict(scope='TOY_ONLY_NO_PTA_CALIBRATION', pta_sbc500_executed=False,
        status='PASS_TOY_CROSSCHECKS_AND_NEGATIVE_CONTROL' if toy_status else 'FAIL_TOY_CROSSCHECK_OR_NEGATIVE_CONTROL',
        config=config, source_hashes={str(path.relative_to(BASE)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [config_path, BASE / 'docs/protocolo_diagnosticos_c07_v1.md', BASE / 'src/inference/diagnostics.py', Path(__file__)]},
        numpy_version=np.__version__, scipy_version=scipy.__version__, generator='PCG64',
        independent_analytic_checks=cross, reports=reports, paired_coverage=paired,
        prior_return_checks=prior_checks, boundary_toy=boundaries, binomial_reference_N500=null500,
        prefix_is_part_of_4096_not_an_independent_repetition=True,
        wall_seconds=time.perf_counter()-start)
    np.savez_compressed(args.output / 'toy_inputs.npz', truth=truth, observed=observed, pit=pit,
                        quantiles=quantiles, loglikelihood_pit=loglikelihood_pit,
                        replicate_ids=np.arange(n), methods=np.array(methods), parameters=np.array(parameters))
    summary['input_npz_sha256'] = hashlib.sha256((args.output / 'toy_inputs.npz').read_bytes()).hexdigest()
    (args.output / 'toy_summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    lines = ['# Exemplo executado: TOY conjugado, não PTA', '',
             f"Seed {tc['seed']}; {n} réplicas em {p} dimensões. Prefixo de 500 predefinido, sem independência do conjunto completo.", '',
             '| N | Algoritmo | Rejeições Holm/31 | PITs de parâmetros rejeitados | KS de logL | p ajustado de logL |', '|---:|---|---:|---:|---:|---:|']
    for size, report in reports.items():
        for method in methods:
            rows = [row for row in report['tests'] if row['method'] == method]
            ll = next(row for row in rows if row['target'] == 'logL_at_truth')
            parameter_rejections = sum(row['reject'] for row in rows if row['diagnostic'] == 'PIT' and row['target'] != 'logL_at_truth')
            p_text = 'underflow (ver limite log10 no JSON)' if ll['pvalue_numerical_underflow'] else f"{ll['holm_pvalue']:.6g}"
            lines.append(f"| {size} | {method} | {sum(row['reject'] for row in rows)} | {parameter_rejections} | {ll['statistic']:.6f} | {p_text} |")
    lines += ['', 'Não rejeição não certifica correção. O controle negativo pode passar nos parâmetros e falhar em logL.', '',
              'As rejeições adicionais abaixo são preservadas, sem trocar seed ou limiar. Para o algoritmo-priori, a cobertura dos quantis é nominal na população por identidade analítica; uma rejeição nessa contagem é erro tipo I nesta realização.', '']
    for size, report in reports.items():
        for row in report['tests']:
            if row['reject'] and row['target'] != 'logL_at_truth':
                lines.append(f"- N={size}, {row['method']}, {row['target']}, {row['diagnostic']}: p ajustado={row['holm_pvalue']:.6g}.")
    lines += ['', '| Verdade u (TOY separado) | Cobertura [0,U90] | Cobertura [Q05,Q95] |', '|---:|---:|---:|']
    for row in boundaries:
        lines.append(f"| {row['truth']:g} | {row['support_to_upper90']['fraction']:.3f} | {row['central_90']['fraction']:.3f} |")
    lines += ['', 'No ponto zero, a cobertura [0,U90]=1 é estrutural. Não foi cobrada cobertura frequentista universal de 90%.', '',
              f"Maior discrepância dos controles analíticos independentes: {max(cross.values()):.3g} (tolerância prévia 1e-10).", '',
              f"Estado: {summary['status']}. Nenhum resultado certifica inferência, ORF ou calibração PTA.", '']
    (args.output / 'EXEMPLO_RELATORIO.md').write_text('\n'.join(lines))
    print(summary['status'])
    print('analytic crosschecks', cross)
    print('negative logL', negative_ll['statistic'], negative_ll['holm_pvalue'])
    print('seconds', summary['wall_seconds'])
    if not toy_status:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
