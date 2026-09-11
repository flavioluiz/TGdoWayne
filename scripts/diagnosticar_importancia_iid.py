"""Portable reader for the frozen two-level C07 IID NPZ contract."""
from pathlib import Path
import argparse,hashlib,json,sys,time
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from inference.iid_diagnostics import (replicated_cdf,replicated_weights,weighted_quantiles,
    compare_brackets,simultaneous_differences,json_safe)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
    with np.load(p,allow_pickle=False) as a:return {k:a[k] for k in a.files}
def main():
    parser=argparse.ArgumentParser()
    for key in ('low','high','truth_logl','reference','protocol','output'):parser.add_argument('--'+key.replace('_','-'),type=Path,required=True)
    args=parser.parse_args();begin=time.perf_counter()
    if args.output.exists():raise FileExistsError('Preserve previous diagnostic result')
    config=json.loads(args.protocol.read_text())
    if config['maximum_single_weight_deletion_bound'] != .00335 or config['independent_replications'] != 4:
        raise ValueError('This v1 reader requires the frozen four-replicate weight diagnostic contract')
    data=[load(args.low),load(args.high)];truth=json.loads(args.truth_logl.read_text());ref=json.loads(args.reference.read_text())
    targets=data[0]['targets'].tolist()
    if targets!=config['target_ids'] or targets!=data[1]['targets'].tolist() or targets!=truth['targets']:
        raise ValueError('Target IDs differ from frozen protocol/truth inputs')
    if ref['model']!='A0_CN' or ref['data_index_zero_based']!=14:raise ValueError('Wrong reference')
    bounds=np.asarray(ref['prior_bounds_original']);width=np.diff(bounds,axis=1)[:,0]
    brackets=(np.asarray(ref['brackets_original'])-bounds[:,0,None,None])/width[:,None,None]
    qfixed=[]
    for j,target in enumerate(targets):
        qfixed.append(np.array([weighted_quantiles(data[0]['x_unit'][:,:,j,p].ravel(),data[0]['log_weights'][:,:,j].ravel(),data[0]['probabilities']) for p in range(5)]))
    levels=[];stability_entries=[];stability_meta=[];refinement=[];refinement_meta=[]
    for level,a in enumerate(data):
        r,n,t,p=a['x_unit'].shape
        if (r,n,t,p)!=(4,config['levels_draws_per_replication'][level],16,5):raise ValueError('Frozen level shape differs')
        if not np.allclose(a['log_weights'],a['log_likelihood']+a['log_prior_logit']-a['log_proposal'],rtol=0,atol=1e-12):raise ValueError('Full log weight identity failed')
        rows=[]
        for j,target in enumerate(targets):
            x=a['x_unit'][:,:,j];lw=a['log_weights'][:,:,j];cdfs=[]
            for parameter in range(5):
                cuts=np.r_[a['truth_unit'][j,parameter],qfixed[j][parameter]]
                cs=replicated_cdf(x[:,:,parameter],lw,cuts,mcse_target=config['cdf_mcse_target'])
                for k,c in enumerate(cs):c['label']=f'p{parameter}_truth' if k==0 else f'p{parameter}_q{a["probabilities"][k-1]:g}'
                cdfs.extend(cs)
            cs=replicated_cdf(a['log_likelihood'][:,:,j],lw,[truth['truth_log_likelihood'][j]],mcse_target=config['cdf_mcse_target'])
            cs[0]['label']='logL_truth';cdfs.extend(cs)
            w=replicated_weights(lw)
            row={'target':target,'model':str(a['models'][target//16]),'data_index':target%16,'cdf_rows':cdfs,'weights':w,
                'mcse_pass_count':sum(c['precision_pass'] for c in cdfs),'total_cdfs':len(cdfs),
                'maximum_finite_mcse':max((c['mcse'] for c in cdfs if np.isfinite(c['mcse'])),default=None),
                'unresolved_cdf_count':sum(not np.isfinite(c['mcse']) for c in cdfs),
                'precision_and_observed_weight_guard_pass':bool(all(c['precision_pass'] for c in cdfs) and w['single_deletion_guard_pass'])}
            # Prespecified formal replicate family excludes sample-selected low cuts.
            for c in cdfs:
                if level==0 and '_q' in c['label']:continue
                for ra in range(r):
                    for rb in range(ra+1,r):
                        stability_entries.append([c['replication_estimates'][ra],c['replication_mcse'][ra],c['replication_estimates'][rb],c['replication_mcse'][rb]])
                        stability_meta.append({'level':n,'target':target,'label':c['label'],'replications':[ra,rb]})
            for ra in range(r):
                for rb in range(ra+1,r):
                    wa,wb=w['replications'][ra],w['replications'][rb]
                    stability_entries.append([wa['log_evidence'],wa['log_evidence_delta_mcse'],wb['log_evidence'],wb['log_evidence_delta_mcse']])
                    stability_meta.append({'level':n,'target':target,'label':'logZ','replications':[ra,rb]})
            if target==14:
                row['external_reference_brackets']=compare_brackets(x,lw,brackets,ref['probabilities'],ref['endpoint_CDF_fine139'],ref['endpoint_CDF_resolution_spread'],ref['endpoint_CDF_omission_bound'],alpha=config['alpha_bracket_family'],deterministic_error=config['deterministic_cdf_component'],quantile_width=config['deterministic_quantile_width_prior_units'],mcse_target=config['cdf_mcse_target'])
            rows.append(row)
        levels.append({'N_per_replication':n,'R':r,'targets':rows})
    for lo,hi in zip(levels[0]['targets'],levels[1]['targets']):
        for a,b in zip(lo['cdf_rows'],hi['cdf_rows']):
            if '_q' in a['label']:continue
            refinement.append([a['estimate'],a['mcse'],b['estimate'],b['mcse']]);refinement_meta.append({'target':lo['target'],'label':a['label']})
        a,b=lo['weights'],hi['weights'];refinement.append([a['log_evidence'],a['log_evidence_delta_mcse'],b['log_evidence'],b['log_evidence_delta_mcse']]);refinement_meta.append({'target':lo['target'],'label':'logZ'})
        if lo['target']==14:
            for ra,rb in zip(lo['external_reference_brackets']['rows'],hi['external_reference_brackets']['rows']):
                for ea,eb in zip(ra['ends'],rb['ends']):
                    a,b=ea['cdf'],eb['cdf'];refinement.append([a['estimate'],a['mcse'],b['estimate'],b['mcse']]);refinement_meta.append({'target':14,'label':f'bracket_p{ra["parameter_index"]}_{ra["probability"]}_{ea["side"]}'})
    st=np.asarray(stability_entries).T;rf=np.asarray(refinement).T
    stability=simultaneous_differences(*st,alpha=config['alpha_replicate_family']);stability['contrasts']=stability_meta
    refinement_result=simultaneous_differences(*rf,alpha=config['alpha_refinement_family']);refinement_result['contrasts']=refinement_meta
    import inference.iid_diagnostics as executed_module
    paths=[Path(__file__),Path(executed_module.__file__),args.protocol,args.low,args.high,args.truth_logl,args.reference]
    result={'label':'SELECTED16_IID_DIAGNOSTICS_NOT_PTA_SBC_NOT_ORF_APPROVAL','config':config,'levels':levels,
        'replication_family':stability,'refinement_family':refinement_result,
        'quantile_cuts_from_independent_low_level':qfixed,'low_level_quantile_CDFs_descriptive_only':True,
        'source_hashes':{str(p):sha(p) for p in paths},'seconds':time.perf_counter()-begin}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(json_safe(result),indent=2,allow_nan=False)+'\n')
    summary={'levels':[{'N':a['N_per_replication'],'cdf_precision_pass':sum(t['mcse_pass_count'] for t in a['targets']),
        'cdf_total':sum(t['total_cdfs'] for t in a['targets']),'unresolved':sum(t['unresolved_cdf_count'] for t in a['targets']),
        'all_precision_weight_targets':sum(t['precision_and_observed_weight_guard_pass'] for t in a['targets']),
        'max_mcse':max(t['maximum_finite_mcse'] for t in a['targets']),
        'A0d14_brackets':next(t['external_reference_brackets']['consistent_brackets'] for t in a['targets'] if t['target']==14),
        'A0d14_brackets_precision':next(t['external_reference_brackets']['brackets_passing_mc_precision'] for t in a['targets'] if t['target']==14)} for a in levels],
        'replication_contrasts':stability['family_size'],'replication_failed':int(np.sum(~stability['consistent'])),
        'refinement_contrasts':refinement_result['family_size'],'refinement_failed':int(np.sum(~refinement_result['consistent'])),
        'seconds':result['seconds']}
    args.output.with_name(args.output.stem+'_summary.json').write_text(json.dumps(json_safe(summary),indent=2,allow_nan=False)+'\n')
    print(json.dumps(json_safe(summary),indent=2))

if __name__=='__main__':main()
