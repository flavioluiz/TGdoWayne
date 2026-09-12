"""Registered production summaries and paired q95 contrasts, retaining every ID.

Finite-sample descriptive intervals propagate numerical brackets only; they are
not confidence intervals for population effects. No new likelihood evaluations.
"""
from pathlib import Path
import collections
import hashlib
import json
import numpy as np
R = Path(__file__).resolve().parents[1]


def main():
    bindings = {}; posts = {}
    def read(p): bindings[str(p.relative_to(R))] = hashlib.sha256(p.read_bytes()).hexdigest(); return json.loads(p.read_text())
    truths = {r['id']:r for r in read(R/'tmp/c09_production_v1/prepared/rows.json')}
    for campaign in ('c09_nominal_production_v1', 'c09_self_production_v1'):
        base = R/'tmp'/campaign
        for job in read(base/'plan.json')['jobs']:
            for row in read(base/'execution'/job['job_id']/'posteriors.json'):
                assert row['curve_id'] not in posts; posts[row['curve_id']] = row
    refined = read(R/'tmp/c09_nominal_refinement_v1/execution/refined_omission_49/posteriors.json')
    assert len(refined) == 1 and refined[0]['curve_id'] in posts
    posts[refined[0]['curve_id']] = refined[0]
    for row in read(R/'tmp/c09_distance_production_v1/posterior_recovery/posteriors.json'):
        assert row['curve_id'] not in posts; posts[row['curve_id']] = row
    expected = {r['id']+'__'+m for r in truths.values() for m in r['models']}
    assert set(posts) == expected and len(posts) == 25956

    def q95(name):
        r = posts[name]; gate = r.get('mesh_gate', r.get('mesh_passed', False)) and r.get('finite_backend_gate', True) and r.get('heldout_passed', True) and r.get('scipy_passed', True)
        index = r['quantile_probabilities'].index(.95)
        return [r['quantile_lower'][index], r['quantile_upper'][index]] if gate else [0., 1.]

    grouped = collections.defaultdict(list)
    for name in posts:
        datum, model = name.split('__', 1); t = truths[datum]
        grouped[(t['stage_id'], t['prior_id'], t['scenario_id'], model)].append(name)
    groups = []
    for (stage, prior, scenario, model), names in sorted(grouped.items()):
        names.sort(key=lambda n:truths[n.split('__')[0]]['datum_id'])
        q = np.array([q95(n) for n in names]); t = truths[names[0].split('__')[0]]
        def quantile_envelope(p): return np.quantile(q, p, axis=0).tolist()
        groups.append(dict(stage=stage, prior_id=prior, scenario=scenario, kind=t['kind'], model=model, n=len(names),
            q95_resolved=int(np.sum(q[:, 1]-q[:, 0] < 1)), median_q95=quantile_envelope(.5),
            realization_p10_q95=quantile_envelope(.1), realization_p90_q95=quantile_envelope(.9),
            median_KL_table=float(np.median([posts[n]['summary']['KL'] for n in names])),
            curve_ids=names, scope='All IDs; numerical brackets only; raw KL descriptive of interpolated tables'))
    contrasts = []
    def contrast(label, left, right):
        assert len(left) == len(right) and all(a.split('__')[0] == b.split('__')[0] for a,b in zip(left,right))
        a, b = np.array([q95(n) for n in left]), np.array([q95(n) for n in right])
        delta = np.column_stack((a[:, 0]-b[:, 1], a[:, 1]-b[:, 0]))
        contrasts.append(dict(label=label, n=len(left), mean_delta_q95=delta.mean(axis=0).tolist(),
            median_delta_q95=np.median(delta, axis=0).tolist(),
            negative=int(np.sum(delta[:, 1] < 0)), positive=int(np.sum(delta[:, 0] > 0)),
            sign_unresolved=int(np.sum((delta[:, 0] <= 0)&(delta[:, 1] >= 0))),
            left_ids=left, right_ids=right, delta_q95_intervals=delta.tolist()))
    for prior in range(3):
        prefix = [f's1_p{prior}_c0_d{i}__' for i in range(500)]
        for source in ('CN', 'G'):
            for left, right in [('diagonal_variable', 'full_variable'), ('diagonal_fixed', 'full_fixed'),
                                ('full_fixed', 'full_variable'), ('diagonal_fixed', 'diagonal_variable')]:
                contrast(f'p{prior}_B_{source}_{left}_minus_{right}',
                    [p+f'B_{source}_{left}' for p in prefix], [p+f'B_{source}_{right}' for p in prefix])
    for scenario in range(4):
        for model in ('A0_CN', 'B_CN_full_variable', 'B_G_full_variable'):
            prefix = [f's5_p0_c{scenario}_d{i}__{model}' for i in range(64)]
            contrast(f'contaminant_{scenario}_{model}_omitted_minus_included',
                [p+'__omitted' for p in prefix], [p+'__known_included' for p in prefix])
    for model in ('A0_CN', 'B_CN_full_variable', 'B_G_full_variable'):
        prefix = [f's6_p0_c1_d{i}__{model}' for i in range(500)]
        contrast(f'distance_{model}_nominal_minus_mixture', [p+'__nominal_scale_only' for p in prefix], [p+'__correct_mixture' for p in prefix])
    assert len(groups) == 90 and len(contrasts) == 39
    out = R/'results/C09/robustness_synthesis'; out.mkdir(parents=True, exist_ok=False)
    for name, obj in [('groups', groups), ('paired_contrasts', contrasts)]:
        (out/(name+'.json')).write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')
    bindings[str(Path(__file__).relative_to(R))] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    audit = dict(posteriors=25956, groups=90, paired_contrasts=39, paired_differences=sum(c['n'] for c in contrasts),
        inputs=bindings, outputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.json')},
        new_likelihood_values=0, failed_gate_policy='q95=[0,1]; no deletion or narrowing',
        scope='Descriptive finite ensemble; no population confidence/equivalence or cross-observation-space evidence ratio')
    (out/'audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    lines = ['# Síntese descritiva da robustez C09', '',
        'Todos os IDs são preservados. Intervalos abaixo propagam somente a incerteza numérica dos quantis; não são intervalos de confiança populacionais.', '',
        'Diferenças são esquerda menos direita, na unidade adimensional u. Casos sem aprovação numérica usam [0,1]. A mediana de KL descreve a tabela interpolada.', '',
        '## Contrastes pareados', '', '| Contraste | n | Média Δq95 | Menor / maior / sinal indeterminado |', '|---|---:|---|---|']
    for c in contrasts:
        lo, hi = c['mean_delta_q95']; lines.append(f"| {c['label']} | {c['n']} | [{lo:.5f}; {hi:.5f}] | {c['negative']} / {c['positive']} / {c['sign_unresolved']} |")
    lines += ['', '## Distribuições entre realizações', '', '| Etapa/priori/cenário | Modelo | n (resolvidos) | Mediana q95 | P10–P90: envelopes | KL mediana (nat) |', '|---|---|---:|---|---|---:|']
    fmt = lambda v: '['+'; '.join(f'{x:.4f}' for x in v)+']'
    for g in groups:
        lines.append(f"| {g['stage']}/{g['prior_id']}/{g['scenario']} | {g['model']} | {g['n']} ({g['q95_resolved']}) | {fmt(g['median_q95'])} | {fmt(g['realization_p10_q95'])} a {fmt(g['realization_p90_q95'])} | {g['median_KL_table']:.5f} |")
    (R/'docs/c09_sintese_robustez_producao.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('inputs', 'outputs')}))


if __name__ == '__main__': main()
