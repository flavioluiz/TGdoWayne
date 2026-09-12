"""Generate compact thesis tables from the completed C10 synthesis."""
from pathlib import Path
import json

R = Path(__file__).resolve().parents[1]


def main():
    result = json.loads((R / 'results/C10/population_synthesis/results.json').read_text())
    audit = json.loads((R / 'results/C10/production_audit/audit.json').read_text())
    assert audit['status'] == 'PRODUCTION_INDEPENDENT_NUMERICAL_AUDIT_PASS'
    assert result['targets'] == audit['targets'] == 6344
    assert result['no_targets_discarded']
    out = R / 'figures/escalar'
    models = ['A0_CN', 'A_CN', 'B_CN', 'A_G', 'B_G']
    def escaped(value):
        return value.replace('_', r'\_')
    def write_table(name, columns, header, rows):
        text = '\\begin{tabular}{' + columns + '}\n\\hline\n'
        text += ' & '.join(header) + r' \\' + '\n\\hline\n'
        text += ''.join(' & '.join(map(str, row)) + r' \\' + '\n' for row in rows)
        text += '\\hline\n\\end{tabular}\n'
        (out / name).write_text(text)
    rows = []
    for model in models:
        row = next(x for x in result['ensemble_summaries'] if x['label'] == model and x['ensemble'] == 'null')
        d = row['detection']
        interval = '--'.join(f'{100*x:.2f}'.replace('.', ',') for x in d['CP95_union'])
        rows.append([escaped(model), row['n'], d['nominal_count'], f"[{d['certain_count']}, {d['possible_count']}]", interval])
    write_table('tabela_falsos_positivos.tex', 'lrrrr', ['Método', '$N$', 'Nominais', 'Certas/possíveis', 'IC 95\\% (\\%)'], rows)
    rows = []
    for family, label, n in [('correct', 'Corretos', 39), ('approximate', 'Aproximações', 26), ('paired_central90', 'Pareados', 6)]:
        tests = [x for x in result['tests'] if x['family'] == family]
        assert len(tests) == n
        rows.append([label, n, sum(x['nominal_reject'] for x in tests), sum(x['decision'] == 'REJECT_FOR_ALL_INTERVAL_VALUES' for x in tests), sum(x['decision'] == 'INDETERMINATE' for x in tests)])
    write_table('tabela_sbc_familias.tex', 'lrrrr', ['Família', 'Testes', 'Rej. nominais', 'Persistentes', 'Indeterminados'], rows)
    rows = [[escaped(m), *result['resolved_PIT_counts'][m]] for m in models]
    write_table('tabela_sbc_resolucao.tex', 'lrrr', ['Método', '$u$', '$\\varepsilon$', '$\\log L$'], rows)
    print(json.dumps({'status': 'C10_TABLES_GENERATED', 'tables': 3, 'new_likelihood_values': 0}))


if __name__ == '__main__':
    main()
