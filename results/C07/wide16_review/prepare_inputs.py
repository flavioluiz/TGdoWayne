"""Lossless reshape of128 immutable wide16 raws for the frozen v1 benchmark reader."""
from pathlib import Path
import argparse,hashlib,json,sys,time
import numpy as np


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    for name in ['index','manifest','production_config','protocol','data','experiment','truth_logl','output']:
        p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    a=p.parse_args();started=time.perf_counter()
    index=json.loads(a.index.read_text());manifest=json.loads(a.manifest.read_text())
    production=json.loads(a.production_config.read_text());protocol=json.loads(a.protocol.read_text())
    exp=json.loads(a.experiment.read_text());truthlog=json.loads(a.truth_logl.read_text())
    if index['status']!='WIDE16_IID_COMPLETE_AWAITING_INDEPENDENT_DIAGNOSTICS':raise ValueError('Closed new wide16 production required.')
    targets=index['targets'];levels=index['levels']
    if targets!=protocol['target_ids'] or targets!=production['targets'] or levels!=[16384,65536] or levels!=production['levels'] or index['replicates']!=4 or index['seed']!=907150101:
        raise ValueError('Frozen wide16 design differs.')
    if sha(a.data)!=manifest['inputs'][str(a.data)] or sha(a.experiment)!=manifest['inputs'][str(a.experiment)]:raise RuntimeError('Production data/experiment hash mismatch.')
    if (truthlog['data_sha256']!=sha(a.data) or truthlog['config_sha256']!=sha(a.experiment) or
        truthlog['status']!='DIRECT_ORF_TRUTH_LOGL_DIAGNOSTIC_ONLY' or truthlog['shape']!=[5,16]):
        raise RuntimeError('Independent truth-logL does not belong to these16observations.')
    bounds=np.array(exp['prior']['bounds']);width=np.diff(bounds,axis=1)[:,0]
    with np.load(a.data,allow_pickle=False) as data:truth=data['truth'].copy()
    if truth.shape!=(16,5) or not np.isfinite(truth).all():raise ValueError('Original16 prior-predictive fixture required.')
    truth_unit=np.array([(truth[t%16]-bounds[:,0])/width for t in targets])
    records=index['records'];seen=set();raw_hashes={};proposal_by_target={r['target']:r['sha256'] for r in production['proposal_records']}
    for r in records:
        key=(r['target'],r['N'],r['replicate'])
        if key in seen:raise ValueError('Duplicate target/level/replica.')
        seen.add(key)
        if r['proposal_sha256']!=proposal_by_target[r['target']]:raise RuntimeError('Raw proposal identity differs.')
    expected={(t,n,r) for t in targets for n in levels for r in range(4)}
    if seen!=expected or len(records)!=128:raise ValueError('Incomplete128raw inventory.')
    a.output.mkdir(parents=True,exist_ok=True);products=[];saturation=[]
    for n in levels:
        if (a.output/f'iid_N{n}.npz').exists():raise FileExistsError('Preserve converted inputs; no overwrite.')
        arrays={key:np.empty((4,n,16,5) if key=='x_unit' else (4,n,16),float)
                for key in ['x_unit','log_weights','log_likelihood','log_prior_logit','log_proposal']}
        for j,t in enumerate(targets):
            for r in range(4):
                row=next(v for v in records if (v['target'],v['N'],v['replicate'])==(t,n,r))
                path=Path(row['file']);digest=sha(path)
                if digest!=row['sha256']:raise RuntimeError('Immutable raw changed: '+str(path))
                raw_hashes[str(path)]=digest
                with np.load(path,allow_pickle=False) as source:
                    if int(source['target'])!=t or int(source['replicate'])!=r:raise RuntimeError('Raw internal identity mismatch.')
                    for key in arrays:
                        value=source[key];shape=(n,5) if key=='x_unit' else (n,)
                        if value.shape!=shape or not np.isfinite(value).all():raise ValueError('Raw shape/finitude mismatch.')
                        arrays[key][r,:,j]=value
                    if not np.array_equal(source['log_weights'],source['log_likelihood']+source['log_prior_logit']-source['log_proposal']):
                        raise RuntimeError('Complete log-weight arithmetic identity differs.')
                    x=source['x_unit'];w=source['log_weights']
                    if np.any((x<0)|(x>1)):raise ValueError('Raw prior coordinates out of support; no clipping.')
                    saturated=np.any((x==0)|(x==1),axis=1)
                    from scipy.special import logsumexp
                    mass=float(np.exp(logsumexp(w[saturated])-logsumexp(w))) if saturated.any() else 0.
                    saturation.append(dict(target=t,N=n,replicate=r,rows=int(saturated.sum()),normalized_weight=mass))
        arrays.update(truth_unit=truth_unit,targets=np.array(targets),probabilities=np.array([.05,.5,.9,.95]),models=np.array(exp['models']),prior_bounds=bounds)
        path=a.output/f'iid_N{n}.npz';np.savez(path,**arrays)
        products.append(dict(N=n,path=str(path),sha256=sha(path),bytes=path.stat().st_size))
        del arrays
    selected=dict(targets=targets,truth_log_likelihood=[truthlog['log_likelihood'][t//16][t%16] for t in targets],
        source=str(a.truth_logl),source_sha256=sha(a.truth_logl),data_sha256=sha(a.data),statistic=truthlog['statistic'])
    (a.output/'truth_logl_selected.json').write_text(json.dumps(selected,indent=2)+'\n')
    protocol['levels_draws_per_replication']=levels
    protocol['execution']={'scope':'WIDE16_ENGINEERING_NOT_SBC500','seed':907150101,'proposal':'.75GM(C)+.10GM(9C)+.15Student5global',
        'source_protocol':str(a.protocol),'source_protocol_sha256':sha(a.protocol),'criteria_unchanged':True,
        'execution_index_sha256':sha(a.index),'production_config_sha256':sha(a.production_config)}
    (a.output/'protocol_execution.json').write_text(json.dumps(protocol,indent=2)+'\n')
    sources={str(path):sha(path) for path in [Path(__file__),a.index,a.manifest,a.production_config,a.protocol,a.data,a.experiment,a.truth_logl]}
    report=dict(status='LOSSLESS_RESHAPE_AND_TRUTH_SELECTION_FOR_DIAGNOSTICS_ONLY',records=128,targets=targets,levels=levels,
        weight_identity_exact=True,raw_sha256=raw_hashes,sources=sources,products=products,saturation=saturation,
        maximum_saturated_normalized_weight=max(r['normalized_weight'] for r in saturation),seconds=time.perf_counter()-started,
        new_likelihood_evaluations=0,new_draws=0)
    (a.output/'input_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'seconds':report['seconds'],'maximum_saturated_weight':report['maximum_saturated_normalized_weight']},indent=2))


if __name__=='__main__':main()
