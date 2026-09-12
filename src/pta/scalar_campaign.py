"""Prospective C10 population inventory; constructing records draws no data."""
import copy

ENSEMBLES = {'null': 1, 'prior2D': 2, 'recovery': 3}
PAIRS = (('A_CN', 'B_CN'), ('A_G', 'B_G'), ('A0_CN', 'A_CN'))


def inventory(protocol):
    """Assign stable SeedSequence namespaces and analysis sets before execution."""
    rows = []
    for name, namespace in ENSEMBLES.items():
        population = protocol['populations'][name]
        subset = set(protocol['C_subset'][name + '_ids'])
        if len(subset) != len(protocol['C_subset'][name + '_ids']) or not subset <= set(range(population['n'])):
            raise ValueError('Invalid C subset')
        for index in range(population['n']):
            row = dict(ensemble=name, id=index, global_id=len(rows),
                       data_seed=[population['seed_data'], namespace, index],
                       analyses=list(protocol['models']))
            if name == 'recovery':
                repeats = population['repetitions_per_cell']
                cells = [(u, e) for u in population['u'] for e in population['epsilon']]
                if population['n'] != len(cells) * repeats:
                    raise ValueError('Recovery cells do not exhaust the population')
                row.update(cell=index // repeats, repetition=index % repeats,
                           fixed_truth=list(cells[index // repeats]))
            else:
                row.update(truth_seed=[population['seed_truth'], namespace, index],
                           truth_rule='uniform_u_epsilon_zero' if name == 'null' else 'independent_uniform_u_epsilon')
            if index in subset:
                row['analyses'].extend(protocol['C_models'])
            rows.append(row)
    return rows


def hypotheses(protocol):
    """Enumerate the previously declared 39/26/6 hypotheses, not just counts."""
    families = {}
    for family, key in (('correct', 'correct_models'), ('approximate', 'approximate_models')):
        rows = []
        for model in protocol['sbc'][key]:
            for statistic in ('u', 'epsilon', 'logL_same_data'):
                rows.append(dict(model=model, kind='KS_uniform', statistic=statistic))
            for parameter in ('u', 'epsilon'):
                for probability in protocol['sbc']['quantile_probabilities']:
                    rows.append(dict(model=model, kind='binomial_two_sided', statistic=parameter,
                                     event='PIT_le_p', probability=probability))
                rows.append(dict(model=model, kind='binomial_two_sided', statistic=parameter,
                                 event='central90', probability=.9, PIT_interval=[.05, .95]))
        families[family] = rows
    families['paired_central90'] = [dict(models=list(pair), statistic=parameter,
                                        kind='exact_McNemar_two_sided', PIT_interval=[.05, .95])
                                    for pair in PAIRS for parameter in ('u', 'epsilon')]
    if {k: len(v) for k, v in families.items()} != protocol['sbc']['Holm_families']:
        raise ValueError('Enumerated hypotheses differ from declared families')
    return copy.deepcopy(families)


def budget(protocol, rows):
    counts = {name: sum(row['ensemble'] == name for row in rows) for name in ENSEMBLES}
    analyses = sum(len(row['analyses']) for row in rows)
    nu, ne = protocol['mesh']['fine']
    grid = analyses * nu * ne
    cap = protocol['resources']['maximum_production_likelihood_equivalents']
    if grid > cap:
        raise ValueError('Primary grid alone exceeds production budget')
    return dict(populations=counts, observations=len(rows), analyses=analyses,
                fine_grid_values=grid, fine_grid_bytes=grid * 8,
                remaining_values_for_truths_bridges_events_and_refinements=cap-grid,
                direct_logL_event_D_targets=counts['prior2D'] * len(protocol['models']),
                SBC_scope='prior2D only; fixed-truth recovery and nulls excluded',
                generation_performed=False, production_enabled=False)
