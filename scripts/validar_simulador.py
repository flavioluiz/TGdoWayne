#!/usr/bin/env python3
"""Executa os testes C06 e confere evidências e regeneração dos dados pequenos.

--check preserva os registros. As campanhas completas de momentos têm receita
separada; este comando regenera o primeiro bloco e confere os três relatórios.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
import scipy
from pta.simulation import paired_physical_and_gaussian
from pta.statistics import compress_frequencies

CASES = {'massive': 'c06_moments.json', 'gr': 'c06_moments_gr.json',
         'noise_only': 'c06_moments_noise_only.json'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    suite = unittest.TestSuite()
    tests_paths = [ROOT / 'tests' / name for name in ('test_simulation.py', 'test_geometry.py')]
    for path in tests_paths:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    outcomes, files = {}, list(tests_paths) + [Path(__file__)]
    for name, config_name in CASES.items():
        directory = ROOT / 'results/C06' / name
        config_path = ROOT / 'configs/experiments' / config_name
        config = json.loads(config_path.read_text())
        summary_path = directory / 'summary.json'
        report = json.loads(summary_path.read_text())
        if report['status'] != 'PASS' or report['config'] != config:
            raise ValueError(f'{name}: status/configuração divergente.')
        if report['config_sha256'] != sha(config_path):
            raise ValueError(f'{name}: hash da configuração divergente.')
        if report['script_sha256'] != sha(ROOT / 'scripts/validate_moments.py'):
            raise ValueError(f'{name}: gerador de momentos alterado.')
        for module_name, expected in report['source_sha256'].items():
            path = ROOT / 'src' / (module_name.replace('.', '/') + '.py')
            if sha(path) != expected:
                raise ValueError(f'{name}: fonte alterada: {module_name}.')
        if report['versions']['numpy'] != np.__version__ or report['versions']['scipy'] != scipy.__version__:
            raise ValueError(f'{name}: versões científicas divergentes.')
        for check in report['checks'].values():
            if check['status'] != 'PASS' or not np.isfinite(check['maximum_standard_errors']) or check['maximum_standard_errors'] > config['monte_carlo']['maximum_standard_errors']:
                raise ValueError(f'{name}: critério de momentos não satisfeito.')
        audit_path = directory / 'orf_audit.json'
        matrices = json.loads(audit_path.read_text())
        pairs = [pair for matrix in matrices for pair in matrix['pair_reports']]
        if len(pairs) != report['orf_validation']['unique_pairs']:
            raise ValueError(f'{name}: contagem da auditoria ORF divergente.')
        for pair in pairs:
            if pair['status'] != 'PASS' or any(not np.isfinite(e) or e > pair['acceptance_limit'] for e in pair['errors'].values()):
                raise ValueError(f'{name}: ORF não passou pelo critério registrado.')
        fixture_path = directory / 'fixture.npz'
        with np.load(fixture_path, allow_pickle=False) as data:
            mc = config['monte_carlo']
            q, physical, control = paired_physical_and_gaussian(
                data['C_normalized_dispersive'], data['estimator_matrices'],
                mc['draws_per_block'], np.random.default_rng(mc['seed']))
            regenerated = {'fourier_normalized': q, 'physical_A': physical,
                           'gaussian_A': control,
                           'physical_B': compress_frequencies(physical, data['frequency_weights']),
                           'gaussian_B': compress_frequencies(control, data['frequency_weights'])}
            for key, values in regenerated.items():
                np.testing.assert_allclose(data[key], values[:mc['saved_draws']], rtol=1e-12, atol=1e-12,
                                           err_msg=f'{name}/{key}: reprodução da semente falhou')
        outcomes[name] = {'status': 'PASS', 'saved_realizations_regenerated': mc['saved_draws'],
                          'recorded_full_moment_realizations': report['monte_carlo']['total_realizations'],
                          'audited_pairs': len(pairs)}
        files += [config_path, summary_path, audit_path, fixture_path]
    record = {'stage': 'C06', 'status': 'PASS', 'tests_run': result.testsRun,
              'cases': outcomes, 'files_sha256': {str(p.relative_to(ROOT)): sha(p) for p in files},
              'scope': '11 tests, source/config/campaign audit and regeneration of saved draws; no posterior/SBC.'}
    target = ROOT / 'results/C06/validacao.json'
    if args.check:
        if json.loads(target.read_text()) != record:
            raise ValueError('Registro C06 diverge; investigar antes de gerar nova versão.')
    else:
        target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(f'C06: {result.testsRun} testes; três campanhas e seus dados pequenos conferidos.')


if __name__ == '__main__':
    main()
