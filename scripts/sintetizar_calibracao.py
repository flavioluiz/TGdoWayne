#!/usr/bin/env python3
"""Strict campaign inventory and conditional SBC synthesis; no discarded targets."""
from pathlib import Path
import argparse,csv,hashlib,itertools,json,sys
import numpy as np
from scipy.stats import norm
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from inference.campaign_io import MODELS,read_json,sha256,write_json_new,write_npz_new,atomic_new
from inference.campaign_sbc import resolved_by_function,synthesize
from inference.iid_diagnostics import json_safe

PIT=np.array([0,5,10,15,20,25]);PROBS=np.array([.05,.5,.9,.95])
SPECS=np.array([[level,j,a,b] for level,indices in [(0,list(PIT)+[26]),(1,range(27))] for j in indices for a,b in itertools.combinations(range(4),2)])


def evidence_manifest(path):
    record=read_json(path);entries=record.get('entries',[]);roles=[];verified=[]
    for entry in entries:
        if not isinstance(entry.get('role'),str):raise ValueError('Explicit evidence role required.')
        source=Path(entry['path']);source=source if source.is_absolute() else Path(path).resolve().parent/source
        if not source.is_file() or sha256(source)!=entry['sha256']:raise RuntimeError('Independent evidence hash mismatch.')
        roles.append(entry['role']);verified.append(dict(entry,path=str(source.resolve())))
    if not {'orf_interpolation','likelihood_kernel','external_posterior_reference'}.issubset(roles):
        raise ValueError('Three independently reviewed numerical evidence roles required.')
    return dict(manifest_sha256=sha256(path),entries=verified,meaning='Presence/integrity of external provenance; no automatic validation from KS or approval booleans',limitations=record.get('limitations',[]),declarations={k:v for k,v in record.items() if k!='entries'})


def strict_array(a,key,shape,kind=None,finite=False):
    value=np.asarray(a[key])
    if value.shape!=shape or (kind is not None and value.dtype.kind not in kind) or (finite and not np.isfinite(value).all()):
        raise ValueError('Diagnostic array shape/type/finitude mismatch: '+key)
    return value


def check_numeric(a,target,datum,model,truth,bounds,truth_logl,protocol):
    for name,expected in [('target',target),('datum',datum),('model_index',model)]:
        if strict_array(a,name,(),'iu').item()!=expected:raise RuntimeError('Numeric target identity mismatch.')
    if not np.array_equal(strict_array(a,'probabilities',(4,),'f',True),PROBS):raise ValueError('Frozen quantile probabilities changed.')
    expected_truth=(truth-bounds[:,0])/np.diff(bounds,axis=1)[:,0]
    if not np.array_equal(strict_array(a,'truth_physical',(5,),'f',True),truth) or not np.array_equal(strict_array(a,'truth_unit',(5,),'f',True),expected_truth):raise RuntimeError('Truth/prior units differ from source data.')
    if strict_array(a,'truth_log_likelihood',(),'f',True).item()!=truth_logl:raise RuntimeError('Truth likelihood differs from direct-ORF diagnostic source.')
    q=strict_array(a,'quantiles_unit',(5,4),'f',True)
    if np.any((q<0)|(q>1)) or np.any(np.diff(q,axis=1)<0) or not np.array_equal(strict_array(a,'quantiles_physical',(5,4),'f',True),bounds[:,0,None]+np.diff(bounds,axis=1)*q):raise ValueError('Quantile bounds/order/units changed.')
    p=strict_array(a,'pit',(6,),'f',True);se=strict_array(a,'pit_mcse',(6,),'f')
    if np.any((p<0)|(p>1)) or np.isnan(se).any() or np.any(se<=0):raise ValueError('Invalid PIT/MCSE; unresolved errors must remain explicit.')
    estimates=strict_array(a,'cdf_estimates_by_level',(2,26),'f',True);errors=strict_array(a,'cdf_mcse_by_level',(2,26),'f')
    if np.any((estimates<0)|(estimates>1)) or np.isnan(errors).any() or np.any(errors<=0):raise ValueError('Invalid CDF uncertainty array.')
    if not np.array_equal(p,estimates[1,PIT]) or not np.array_equal(se,errors[1,PIT]):raise ValueError('PIT fields differ from full CDF fields.')
    resolution=strict_array(a,'cdf_resolved_by_level',(2,26),'b');precision=strict_array(a,'cdf_precision_by_level',(2,26),'b')
    if not np.array_equal(resolution,np.isfinite(errors)) or not np.array_equal(precision,resolution&(errors<=protocol['cdf_mcse_target'])):raise ValueError('CDF precision flags disagree with their errors.')
    for name,expected in [('pit_resolved',resolution[1,PIT]),('pit_precision_pass',precision[1,PIT])]:
        if not np.array_equal(strict_array(a,name,(6,),'b'),expected):raise ValueError('PIT flags differ from full CDF flags.')
    if not np.array_equal(strict_array(a,'replication_specification',(204,4),'iu'),SPECS):raise ValueError('The exact204 contrast specifications changed or repeat.')
    for prefix,size,family in [('replication',204,204*protocol['population_targets']),('refinement',7,7*protocol['population_targets'])]:
        difference=strict_array(a,prefix+'_difference',(size,),'f',True);error=strict_array(a,prefix+'_mcse',(size,),'f')
        resolved=strict_array(a,prefix+'_resolved',(size,),'b');passed=strict_array(a,prefix+'_pass',(size,),'b')
        if np.isnan(error).any() or np.any(error<0):raise ValueError('Invalid contrast MCSE.')
        expected=np.isfinite(error)&(error>0);alpha=protocol['alpha_replicate_family' if prefix=='replication' else 'alpha_refinement_family']
        if not np.array_equal(resolved,expected) or not np.array_equal(passed,expected&(abs(difference)<=norm.isf(alpha/(2*family))*error)):raise ValueError('Contrast flags disagree with frozen multiplicity.')
    strict_array(a,'cut_precision_pass',(5,4),'b')
    for key in ('weight_ess','maximum_weight','log_evidence'):strict_array(a,key,(),'f',True)
    strict_array(a,'weight_deletion_guard_by_level',(2,),'b');sat=strict_array(a,'saturated_weight',(2,4),'f',True)
    if np.any(sat<0):raise ValueError('Negative saturated weight.')
    return resolved_by_function(a,saturation_limit=protocol['maximum_saturated_target_weight'])


def load_campaign(diagnostics,production,experiment,data,truth_logl,config,numerical_protocol,evidence,*,toy64=False):
    cfg=read_json(config);exp=read_json(experiment);protocol=read_json(numerical_protocol);n=64 if toy64 else 500;models=list(MODELS)
    if cfg['n_realizations']!=n or cfg['models']!=models or exp['n_realizations']!=n or exp['models']!=models or cfg.get('discard_realizations') is not False:raise ValueError('Full frozen500×5 inventory required (or explicit separate TOY64).')
    if cfg['families']['correct']!={'models':['A0_CN','A_G','B_G'],'hypotheses':93} or cfg['families']['approximate']!={'models':['A_CN','B_CN'],'hypotheses':62} or cfg['families']['paired_central90']['hypotheses']!=15:raise ValueError('Scientific families93/62/15 changed.')
    if cfg['probabilities']!=PROBS.tolist() or cfg['families']['paired_central90']['pairs']!=[['A_CN','B_CN'],['A_G','B_G'],['A0_CN','A_CN']]:raise ValueError('Frozen probabilities or paired contrasts changed.')
    numerical=cfg['numerical_sensitivity']
    if numerical['family_size']!=15000 or numerical['alpha_mc']!=.01 or numerical['deterministic_component']!=.002:raise ValueError('Frozen numerical sensitivity changed.')
    if protocol['population_targets']!=5*n or protocol['independent_replications']!=4 or protocol['cdf_mcse_target']!=cfg['numerical_sensitivity']['cdf_mcse_target']:raise ValueError('Numerical campaign protocol mismatch.')
    datahash=sha256(data);exphash=sha256(experiment);llhash=sha256(truth_logl)
    if cfg['data_sha256']!=datahash:raise RuntimeError('Data differs from frozen synthesis.')
    direct=read_json(truth_logl)
    if direct['status']!='DIRECT_ORF_TRUTH_LOGL_DIAGNOSTIC_ONLY' or direct['data_sha256']!=datahash or direct['config_sha256']!=exphash or direct['models']!=models or direct['shape']!=[5,n]:raise RuntimeError('Direct truth likelihood source identity mismatch.')
    with np.load(data,allow_pickle=False) as source:truth=source['truth'].copy()
    bounds=np.asarray(exp['prior']['bounds']);parameters=exp['parameters']
    if truth.shape!=(n,5) or bounds.shape!=(5,2) or not np.isfinite(truth).all() or not np.isfinite(bounds).all() or np.any(np.diff(bounds,axis=1)<=0):raise ValueError('Truth/prior dimensions or finitude changed.')
    if np.any(truth<bounds[:,0]) or np.any(truth>bounds[:,1]):raise ValueError('Truth outside prior support.')
    proof=evidence_manifest(evidence)
    paths=sorted(Path(diagnostics).glob('diagnostic_target_*.json'))
    if len(paths)!=5*n:raise ValueError('Missing or extra diagnostic targets; none may be discarded.')
    arrays=dict(pit=np.empty((5,n,6)),mcse=np.empty((5,n,6)),resolved=np.zeros((5,n,6),bool),quantiles_unit=np.empty((5,n,5,4)),quantiles_physical=np.empty((5,n,5,4)),cut_precision_pass=np.zeros((5,n,5,4),bool),weight_ess=np.empty((5,n)),maximum_weight=np.empty((5,n)),log_evidence=np.empty((5,n)),truth=truth,bounds=bounds,probabilities=PROBS)
    seen=set();inventory=[];identity=None
    for path in paths:
        meta=read_json(path);target=meta['target']
        if type(target) is not int or not 0<=target<5*n or target in seen:raise ValueError('Duplicate/noninteger/unplanned target.')
        m,d=divmod(target,n)
        if path.name!=f'diagnostic_target_{target:06d}.json' or meta['datum']!=d or meta['model']!=models[m] or meta['status']!='NUMERICAL_DIAGNOSTICS_COMPLETE' or meta['schema']!='C07_TARGET_IID_DIAGNOSTICS_v1':raise ValueError('Diagnostic model/datum/schema mismatch.')
        if identity is None:identity=meta['identity']
        if meta['identity']!=identity:raise RuntimeError('Mixed runtime identities in campaign.')
        producer_path=Path(production)/f'target_{target:06d}.json';producer=read_json(producer_path)
        if sha256(producer_path)!=meta['diagnostic_inputs']['producer_report_sha256'] or producer['identity']!=identity or producer['target']!=target or producer['datum']!=d or producer['model']!=models[m] or producer['input_sha256']['data']!=datahash or producer['input_sha256']['experiment']!=exphash:raise RuntimeError('Producer/config/data identity mismatch.')
        if meta['diagnostic_inputs']['truth_data_sha256']!=datahash or meta['diagnostic_inputs']['truth_loglikelihood_sha256']!=llhash or meta['diagnostic_inputs']['protocol_sha256']!=sha256(numerical_protocol) or meta['proposal_sha256']!=producer['proposal_sha256']:raise RuntimeError('Diagnostic input hashes differ.')
        if meta['levels']!=protocol['levels'] or producer['levels']!=protocol['levels'] or len(producer['replicates'])!=8:raise ValueError('Two independent registered levels/four replicas required.')
        expected={(level,rep) for level in protocol['levels'] for rep in range(4)}
        if {(r['level'],r['replicate']) for r in producer['replicates']}!=expected or meta['raw_sha256']!={r['raw_file']:r['raw_sha256'] for r in producer['replicates']}:raise ValueError('Raw replication inventory differs.')
        numeric=Path(diagnostics)/meta['numeric_file']
        if numeric.name!=f'diagnostic_target_{target:06d}.npz' or Path(meta['numeric_file']).name!=meta['numeric_file'] or sha256(numeric)!=meta['numeric_sha256']:raise RuntimeError('Numeric diagnostic filename/hash changed.')
        with np.load(numeric,allow_pickle=False) as saved:a={k:saved[k] for k in saved.files}
        resolved=check_numeric(a,target,d,m,truth[d],bounds,float(direct['log_likelihood'][m][d]),protocol)
        for key,source in [('pit','pit'),('mcse','pit_mcse'),('quantiles_unit','quantiles_unit'),('quantiles_physical','quantiles_physical'),('cut_precision_pass','cut_precision_pass'),('weight_ess','weight_ess'),('maximum_weight','maximum_weight'),('log_evidence','log_evidence')]:arrays[key][m,d]=a[source]
        arrays['resolved'][m,d]=resolved;seen.add(target)
        inventory.append(dict(target=target,model=models[m],datum=d,diagnostic_sha256=sha256(path),numeric_sha256=meta['numeric_sha256'],producer_sha256=sha256(producer_path)))
    if seen!=set(range(5*n)) or len(list(Path(diagnostics).glob('diagnostic_target_*.npz')))!=5*n:raise ValueError('Incomplete/extra numeric inventory; no silent intersection.')
    provenance=dict(runtime_identity=identity,data_sha256=datahash,experiment_sha256=exphash,truth_logl_sha256=llhash,synthesis_config_sha256=sha256(config),numerical_protocol_sha256=sha256(numerical_protocol),validation_evidence=proof,inventory=inventory,all_ids_retained=True,resolution_conditional_on_independent_review_of_evidence=True)
    return arrays,cfg,parameters,provenance


def save_products(output,arrays,cfg,parameters,provenance,*,toy64=False):
    output=Path(output)
    if output.exists():raise FileExistsError('Synthesis destination must be new; preserve prior conclusions.')
    report,intervals=synthesize(arrays['pit'],arrays['mcse'],arrays['resolved'],arrays['quantiles_unit'],cfg,parameters)
    if toy64:report['toy_precision_note']='Exact analytic PITs; synthetic MCSE1e-8 is an interface fixture, not earned PTA numerical precision. External evidence role fixtures assert no ORF validation.'
    arrays.update(intervals);report.update(provenance=provenance,config=cfg,scope='TOY64_ANALYTIC_PIPELINE_VALIDATION_NOT_PTA' if toy64 else report['scope'],figure_note='Numerical sensitivity bands and ideal IID DKW bounds are separate; neither validates the integrator.')
    import inference.campaign_sbc as sbc,inference.sbc_sensitivity as sensitivity
    report['executed_source_sha256']={str(p):sha256(p) for p in (Path(__file__),Path(sbc.__file__),Path(sensitivity.__file__))}
    write_npz_new(output/'arrays.npz',**arrays);report['arrays_sha256']=sha256(output/'arrays.npz');write_json_new(output/'summary.json',json_safe(report))
    columns=['group','method','target','diagnostic','family_size','nominal_holm_pvalue','nominal_reject','rejection_robust_to_sensitivity','numerical_resolved']
    def csv_write(path):
        with path.open('w',newline='',encoding='utf-8') as stream:
            writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
            for row in report['tests']:writer.writerow({k:row[k] for k in columns})
    atomic_new(output/'tests.csv',csv_write)
    pair_columns=['method_a','method_b','parameter','nominal_holm_pvalue','nominal_reject','rejection_robust_to_sensitivity']
    def paired_csv(path):
        with path.open('w',newline='',encoding='utf-8') as stream:
            writer=csv.DictWriter(stream,fieldnames=pair_columns);writer.writeheader()
            for row in report['paired_central90']:writer.writerow({k:row[k] for k in pair_columns})
    atomic_new(output/'paired_central90.csv',paired_csv)
    lines=['# Síntese condicional de calibração','',report['scope'],'',f"Todos os {cfg['n_realizations']} dados de cada um dos cinco modelos foram retidos.",'','As famílias prévias93/62/15 são preservadas. Testes nominais condicionam-se aos PITs calculados; as faixas de sensibilidade usam erro determinístico0,002 + zBonferroni×MCSE (alphaMC0,01, família15.000). Funções não resolvidas recebem [0,1].','', 'A presença e integridade das evidências externas não constituem aprovação automática. Não rejeitar uniformidade não prova correção; quantis são descritivos e precisão de CDF não certifica erro horizontal. As bandas DKW mostradas nas figuras descrevem a amostragem IID ideal e são distintas da sensibilidade numérica.','', '| Modelo | Funções resolvidas (por coordenada) | Rejeições nominais | Rejeições robustas |','|---|---|---:|---:|']
    lines.extend(f"| {r['model']} | {r['functions_resolved_by_parameter']} | {r['nominal_rejections']} | {r['robust_rejections']} |" for r in report['model_summary'])
    atomic_new(output/'README.md',lambda p:p.write_text('\n'.join(lines)+'\n',encoding='utf-8'));return report


def main():
    parser=argparse.ArgumentParser()
    for name in ('diagnostics','production','experiment','data','truth_logl','config','numerical_protocol','validation_evidence','scientific_protocol','output'):
        parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    parser.add_argument('--toy64',action='store_true');args=parser.parse_args()
    cfg=read_json(args.config)
    if sha256(args.scientific_protocol)!=cfg['scientific_protocol_sha256']:raise RuntimeError('Underlying scientific protocol changed.')
    loaded=load_campaign(args.diagnostics,args.production,args.experiment,args.data,args.truth_logl,args.config,args.numerical_protocol,args.validation_evidence,toy64=args.toy64)
    report=save_products(args.output,*loaded,toy64=args.toy64)
    print(json.dumps(dict(scope=report['scope'],simulations_per_model=report['simulations_per_model'],tests=len(report['tests']),paired_tests=len(report['paired_central90']),unresolved=report['sensitivity_intervals']['unresolved_count'])))

if __name__=='__main__':main()
