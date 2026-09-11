"""Truth-blind fixed-cut and raw-weight assessment of both new cold trainings."""
import os
os.environ.setdefault('VECLIB_MAXIMUM_THREADS','1')
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.special import logsumexp
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'executed_sources/src'))
from inference.iid_diagnostics import replicated_cdf,replicated_weights,simultaneous_differences,json_safe

def main():
    cfg=json.loads((HERE/'config.json').read_text());grid=json.loads((ROOT/cfg['frozen_cdf_grid']).read_text());rows=[];sources={}
    for steps in cfg['training_lengths']:
        for N in cfg['levels']:
            path=HERE/'results'/f'train{steps}_iid_N{N}.npz';sources[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
            with np.load(path,allow_pickle=False) as f:
                assert f['targets'].tolist()==cfg['targets'];x=f['x_unit'];ll=f['log_likelihood'];lw=f['log_weights'];z=f['z'];comp=f['proposal_component']
            for j,target in enumerate(cfg['targets']):
                cuts=next(t for t in grid['targets'] if t['target']==target)['functions'];functions=[]
                for name in dict.fromkeys(c['function'] for c in cuts):
                    group=[c for c in cuts if c['function']==name]
                    values=ll[:,:,j] if name=='log_likelihood' else x[:,:,j,int(name[-1])]
                    ds=replicated_cdf(values,lw[:,:,j],[c['cdf']['threshold'] for c in group])
                    functions.extend(dict(function=name,pilot_quantile_probability=c['pilot_quantile_probability'],cdf=d) for c,d in zip(group,ds))
                weights=replicated_weights(lw[:,:,j]);worst=max(functions,key=lambda f:f['cdf']['mcse'])
                flat=lw[:,:,j].ravel();ix=np.argsort(flat)[-10:][::-1];p=np.exp(flat-logsumexp(flat));sat=np.any((x[:,:,j]==0)|(x[:,:,j]==1),axis=-1)
                top=[dict(rep=int(i//N),index_in_rep=int(i%N),normalized_weight=float(p[i]),x_unit=x[:,:,j].reshape(-1,5)[i].tolist(),z=z[:,:,j].reshape(-1,5)[i].tolist(),component=int(comp[:,:,j].ravel()[i]),log_likelihood=float(ll[:,:,j].ravel()[i])) for i in ix]
                rows.append(dict(training_steps=steps,N=N,target=target,precise_cuts=sum(f['cdf']['precision_pass'] for f in functions),cuts=54,maximum_mcse=worst['cdf']['mcse'],worst_function=worst['function'],worst_quantile=worst['pilot_quantile_probability'],functions=functions,weights=weights,largest_weights=top,saturated_normalized_weight=float(p[sat.ravel()].sum())))
    contrasts=[]
    for name,a_key,b_key in [('refine_train8192',(8192,16384),(8192,65536)),('refine_train32768',(32768,16384),(32768,65536)),('compare_training_high',(8192,65536),(32768,65536))]:
        a=[r for r in rows if (r['training_steps'],r['N'])==a_key];b=[r for r in rows if (r['training_steps'],r['N'])==b_key]
        keys=[(r['target'],f['function'],f['pilot_quantile_probability']) for r in a for f in r['functions']]
        estimates=lambda rr:[f['cdf']['estimate'] for r in rr for f in r['functions']]
        ses=lambda rr:[f['cdf']['mcse'] for r in rr for f in r['functions']]
        c=simultaneous_differences(estimates(a),ses(a),estimates(b),ses(b))
        contrasts.append(dict(name=name,keys=keys,contrast=c))
    report=dict(status='TRUTH_BLIND_FIXED_GRID_DIAGNOSTICS_NOT_SBC',rows=rows,contrasts=contrasts,uses_truth=False,fixed_grid_sha256=hashlib.sha256((ROOT/cfg['frozen_cdf_grid']).read_bytes()).hexdigest(),raw_source_sha256=sources,diagnostic_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),limitations=['Grid54 cuts were fixed before this experiment; no new truth thresholds read.','Independent production seeds by training,level,target,replicate; separate contrasts have explicitly declared families.','MCSE is max of pooled IID influence and independent replica influence, not ESS/binomial.','Every failure remains reported; finite checks do not prove absence of missed tails.'])
    with (HERE/'results/grid_diagnostics.json').open('x') as f:json.dump(json_safe(report),f,indent=2);f.write('\n')
    summary=dict(rows=[{k:r[k] for k in ['training_steps','N','target','precise_cuts','maximum_mcse','worst_function','worst_quantile']}|{k:r['weights'][k] for k in ['log_evidence','log_evidence_delta_mcse','maximum_normalized_weight','single_deletion_guard_pass','weight_ess_concentration_only']} for r in rows],contrasts=[dict(name=c['name'],all_consistent=c['contrast']['all_consistent'],failures=int(np.count_nonzero(~c['contrast']['consistent'])),maximum_standardized_difference=float(np.max(np.abs(c['contrast']['difference'])/c['contrast']['difference_mcse']))) for c in contrasts])
    with (HERE/'results/grid_summary.json').open('x') as f:json.dump(json_safe(summary),f,indent=2);f.write('\n')
    print(json.dumps(json_safe(summary),indent=2))

if __name__=='__main__':main()
