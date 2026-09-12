#!/usr/bin/env python3
"""Audita e preserva o lote D2 encerrado; não executa likelihoods."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'tmp/c09_D2_execution_resume_v1'
RUNTIME = ROOT / 'tmp/c09_D2_runtime_resume_v1'
DEST = ROOT / 'results/C09/D2_retoma'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    import numpy as np
    end = read(RUN / 'execution_end.json')
    worker = read(RUN / 'worker/worker_end.json')
    plan = read(RUNTIME / 'preflight.json')
    assert end['plan_sha256'] == sha(RUNTIME / 'preflight.json')
    for path, digest in plan['bindings'].items():
        assert sha(ROOT / path) == digest, path
    for entry in read(ROOT / 'results/pausa_v0.8.5/c09_manifest.json')['files']:
        assert sha(ROOT / entry['path']) == entry['sha256'], entry['path']
    resources = worker['resources']
    assert resources['additional_charged_values'] == sum(resources['by_curve'].values())
    assert resources['additional_charged_values'] <= 200000
    assert resources['cumulative_values'] == 544316 + resources['additional_charged_values']
    config = read(RUNTIME / 'runtime_config.json')
    records = []
    reconstructed_charged = 0
    for curve in config['curves']:
        name = curve['curve_id']
        result_path = RUN / 'worker/results' / (name + '.json')
        result = read(result_path) if result_path.exists() else {}
        identity_path = RUN / 'worker/caches' / (name + '_identity.json')
        identity = read(identity_path)
        cache_path = RUN / 'worker/caches' / (name + '.npz')
        with np.load(cache_path, allow_pickle=False) as cache:
            u, ell = cache['u'], cache['log_likelihood']
            assert len(u) == identity['stored_values']
            assert np.isfinite(u).all() and np.isfinite(ell).all()
            assert np.all(np.diff(u) > 0) and 0 <= u[0] <= u[-1] <= 1
            for history in config['historical_cache_inputs']:
                if history['curve_id'] == name:
                    with np.load(ROOT / history['cache_path'], allow_pickle=False) as old:
                        indices = np.searchsorted(u, old['u'])
                        assert np.array_equal(u[indices], old['u'])
                        assert ell[indices].tobytes() == old['log_likelihood'].tobytes()
        assert identity['charged_values'] == resources['by_curve'][name]
        # 32 table/harmonic controls + 3 SciPy values per curve; historical
        # imports have 32 additional direct bridge checks. The interrupted
        # baseline_d3 query was charged but did not reach the cache.
        controls = 35 + (32 if identity['imported_values'] else 0)
        failed = 1 if name == 'baseline_d3' else 0
        reconstructed = len(u) - identity['imported_values'] + controls + failed
        assert reconstructed == identity['charged_values'], name
        reconstructed_charged += reconstructed
        backend = read(RUN / 'worker/backend_checks' / (name + '.json'))
        assert backend['new_curve_checks_passed']
        panels = sorted((RUN / 'worker/references' / name).glob('panel_*.json'))
        records.append(dict(curve_id=name, data_id=curve['data_id'],
            analyses_planned=len(curve['prior_ids']),
            result_status=result.get('status', result.get('schema', 'NOT_RECORDED')),
            saved_values=len(u), imported_values=identity['imported_values'],
            charged_values=identity['charged_values'], completed_reference_panels=len(panels),
            backend_max_delta_logL=backend['maximum_absolute_logL_difference'],
            scipy_max_delta_logL=backend['scipy_maximum_absolute_difference']))
    DEST.mkdir(parents=True, exist_ok=True)
    assert reconstructed_charged == resources['additional_charged_values']
    paths = sorted(p for base in (RUN, RUNTIME) for p in base.rglob('*')
                   if p.is_file() and '__pycache__' not in p.parts)
    archive = DEST / 'execucao_e_fontes.zip'
    entries = [dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size, sha256=sha(p)) for p in paths]
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in paths:
            z.write(p, p.relative_to(ROOT))
    with zipfile.ZipFile(archive) as z:
        for entry in entries:
            assert hashlib.sha256(z.read(entry['path'])).hexdigest() == entry['sha256']
    summary = dict(schema='C09_D2_RESUMPTION_AUDIT_v1', date='2026-09-12',
        execution_status=end['status'], execution_errors=end['errors'],
        resources=resources, measured_stage_CPU_seconds=end['measured_stage_CPU_seconds'],
        cumulative_CPU_seconds=end['cumulative_CPU_seconds'],
        wall_seconds=end['wall_seconds'], RSS_sum_peak_bytes=end['RSS_sum_peak_bytes'],
        curves=records, original_1070_snapshot_files_unchanged=True,
        historical_imports_verified_bitwise=True, archive_members_verified=len(entries),
        charged_values_reconstructed_from_caches_and_controls=reconstructed_charged,
        supervisor_reservation_upper_values=end['unresolved_reservation_upper_values'],
        supervisor_failure_not_reclassified=True,
        C09_complete=False, SBC_executed=False, new_ORF=0, new_draws=0,
        interpretation='Finite backend controls and saved partial references; no promotion of unresolved functionals.')
    manifest = dict(archive=str(archive.relative_to(ROOT)), archive_sha256=sha(archive),
                    archive_bytes=archive.stat().st_size, files=entries,
                    dependencies='Original snapshot v0.8.5 and bound C06-C08 inputs; paths preserve local provenance.')
    for name, value in [('audit.json', summary), ('manifest.json', manifest), ('execution_end.json', end)]:
        (DEST / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
