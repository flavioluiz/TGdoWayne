#!/usr/bin/env python3
"""Prepare checked truth ORFs and independent prior-predictive data; no posterior fit.

Run `preflight` first. `build-orfs` keeps construction checkpoints in tmp and
copies only the validated final nodes into the data product. `generate` refuses
to overwrite observations. `verify` regenerates observations from saved nodes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import numpy as np
import scipy
from inference.data_generation import prior_truths, generate_prior_fixture, StoredExactORF
from inference.model import experiment
from inference.orf_backend import ExactNodeORF
from inference.orf_table_builder import build_checked_nodes, ConstructionBudget, atomic_new_npz, token
from inference.orf_blas import estimate


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['preflight', 'build-orfs', 'generate', 'verify'])
    parser.add_argument('--config', type=Path, default=ROOT/'configs/calibration/prior_predictive_500_v1.json')
    parser.add_argument('--output', type=Path, default=ROOT/'results/C07/prior_predictive')
    parser.add_argument('--construction-cache', type=Path, default=ROOT/'tmp/c07_prior_predictive_orfs')
    args = parser.parse_args()
    config_path = args.config.resolve(); config = json.loads(config_path.read_text())
    output = args.output.resolve(); cache = output/'orf_cache'
    truth = prior_truths(config); exp = experiment(config)
    budget = ConstructionBudget(**config['generation_orf_budget'])
    # Metadata initialization uses only a temporary directory; no scientific cache.
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        meta = ExactNodeORF(exp, config['orf'], directory)
    nodes = np.unique(np.r_[truth[:,0], config['orf']['direct_mass_points'], .5])
    count = len(nodes); pulsars = len(exp['points']); channels = len(exp['f'])
    work = int(2*count*pulsars*np.sum((meta.l-1)*meta.n+(meta.lf-1)*meta.nf))
    memory = int(16*count*(channels+2)*pulsars**2+8*count*channels + max(
        estimate(int(l),int(n),pulsars,budget.batch_size)['estimated_memory_bytes']
        for l,n in zip(np.r_[meta.l,meta.lf],np.r_[meta.n,meta.nf])))
    if count > budget.maximum_requested_nodes or work > budget.maximum_total_real_multiplications or memory > budget.maximum_estimated_numeric_memory_bytes:
        raise RuntimeError('Declared truth-node construction budget is insufficient.')
    preview = dict(realizations=len(truth),distinct_exact_nodes_with_anchors=count,
                   maximum_total_real_multiplications=work,estimated_numeric_bytes=memory,
                   config_sha256=sha(config_path),truth_array_sha256=hashlib.sha256(truth.tobytes()).hexdigest(),
                   output=str(output),observation_generation=False,posterior_execution=False)
    if args.action == 'preflight':
        print(json.dumps(preview,indent=2)); return
    source_paths = [Path(__file__), config_path] + [ROOT/'src/inference'/name for name in
                    ['data_generation.py','model.py','orf_backend.py','orf_blas.py','orf_table_builder.py']]
    source_paths += list((ROOT/'src/pta').glob('*.py'))
    sources = {str(path.relative_to(ROOT)): sha(path) for path in source_paths}
    started = time.perf_counter()
    if args.action == 'build-orfs':
        manifest_path = output/'orf_construction.json'
        if manifest_path.exists():
            raise FileExistsError('Construction report exists; preserve it and use another output for a new execution.')
        report = build_checked_nodes(exp, config['orf'], truth[:,0], args.construction_cache,
                                     budget=budget, validate_direct=True)
        reader = StoredExactORF(exp,config['orf'],args.construction_cache)
        for u in nodes: reader.evaluate(float(u))
        cache.mkdir(parents=True,exist_ok=True)
        copied = []
        for u in nodes:
            name = token(meta.signature,float(u))+'.npz'
            original = args.construction_cache/name; destination = cache/name
            if destination.exists():
                if sha(destination) != sha(original):
                    raise RuntimeError('Existing published truth node differs; it was preserved.')
            else:
                with original.open('rb') as src, destination.open('xb') as dst:
                    shutil.copyfileobj(src,dst)
            copied.append(dict(path='orf_cache/'+name,sha256=sha(destination)))
        if any(sha(ROOT/path) != digest for path,digest in sources.items()):
            raise RuntimeError('Source changed during construction; preserve outputs and investigate.')
        report.update(source_sha256=sources,config_sha256=sha(config_path),final_copied_nodes=copied,
                      observation_generation=False,posterior_execution=False)
        with manifest_path.open('x') as target: json.dump(report,target,indent=2); target.write('\n')
        print(f'{count} exact checked truth/anchor nodes preserved; no observations generated.'); return

    data_path = output/'data.npz'; report_path = output/'generation.json'
    if args.action == 'generate' and (data_path.exists() or report_path.exists()):
        raise FileExistsError('Data product exists. Use verify; do not overwrite simulated observations.')
    construction = json.loads((output/'orf_construction.json').read_text())
    if construction['config_sha256'] != sha(config_path) or construction['status'] != 'COMPLETE':
        raise RuntimeError('Exact truth-node construction is missing or belongs to another configuration.')
    direct = construction['sparse_direct_checks']
    if len(direct) != 7 or any(not np.isfinite(r['absolute_difference']) or r['absolute_difference'] > 1e-7 for r in direct):
        raise RuntimeError('The independent sparse ORF checks were not satisfied.')
    for row in construction['final_copied_nodes']:
        if sha(output/row['path']) != row['sha256']:
            raise RuntimeError('A saved exact truth-node file changed.')
    arrays, records = generate_prior_fixture(config,cache)
    if any(sha(ROOT/path) != digest for path,digest in sources.items()):
        raise RuntimeError('Source changed during observation generation.')
    if args.action == 'verify':
        report = json.loads(report_path.read_text())
        if sha(data_path) != report['data_sha256'] or sha(config_path) != report['config_sha256']:
            raise RuntimeError('Saved data/configuration hash mismatch.')
        for path,digest in report['source_sha256'].items():
            if sha(ROOT/path) != digest:
                raise RuntimeError('A recorded generation source changed; investigate before claiming reproduction.')
        with np.load(data_path,allow_pickle=False) as data:
            for name,value in arrays.items():
                np.testing.assert_allclose(value,data[name],rtol=1e-12,atol=1e-12)
        print(f'{len(truth)} observations regenerated from their checked truth nodes; no posterior or SBC test executed.'); return
    if not atomic_new_npz(data_path,**arrays,config_sha256=sha(config_path)):
        raise FileExistsError('Concurrent observation product exists; it was preserved.')
    report = dict(status='DATA_GENERATED_NOT_POSTERIOR_CALIBRATION',realizations=len(truth),
                  models=config['models'],truth_seed=config['truth_seed'],data_seed=config['data_seed'],
                  config_sha256=sha(config_path),source_sha256=sources,data_sha256=sha(data_path),
                  orf_construction_sha256=sha(output/'orf_construction.json'),truth_orf_records=records,
                  numpy_version=np.__version__,scipy_version=scipy.__version__,
                  seconds=time.perf_counter()-started,posterior_execution=False,
                  interpolation_in_data_generation=False,paired_CN_G=True)
    with report_path.open('x') as target: json.dump(report,target,indent=2); target.write('\n')
    print(f'{len(truth)} fresh prior-predictive observations generated; posterior calibration remains separate.')


if __name__ == '__main__':main()
