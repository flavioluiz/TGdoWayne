"""Load only the audited C07 synthesis and original truth member; fail closed."""
from pathlib import Path
import hashlib,json
import numpy as np

MODELS=('A0_CN','A_CN','B_CN','A_G','B_G')
PARAMETERS=('u','log10_Agw','gamma_gw','log10_Ar','log10_EFAC')
SUMMARY_SHA='909ef28817342c19293fe9cb832bcf659dd480be5fd82c3708ee73b832cd4f9a'
ARRAYS_SHA='2effb30fafb2db1ae6371952d933cb9f8be63bf2875cd8a55ea15188a39a4a4f'
DATA_SHA='63679c96852f3c0aa1e25c8a3f087c0646ceb22cd7701758491cabdd42ac0103'
CONFIG_SHA='f22b0a8cd7c86e477365ea02d3b37a836458d44285b0abd323bccd174c89fdfa'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def checked(path,expected):
    path=Path(path)
    if not path.is_file() or sha(path)!=expected:raise ValueError('Frozen input hash differs: '+str(path))
    return path


def read(path):return json.loads(Path(path).read_text())


def load_c07_results(repository):
    root=Path(repository).resolve()
    paths={
      'summary':root/'results/C07/synthesis/summary.json',
      'arrays':root/'results/C07/synthesis/arrays.npz',
      'data':root/'results/C07/prior_predictive/data.npz',
      'config':root/'configs/calibration/prior_predictive_500_v1.json',
      'generation':root/'results/C07/prior_predictive/generation.json',
      'G0':root/'tmp/c08_G0/c07_publication_resource_release.json',
      'release_manifest':root/'releases/v0.7.1/manifest.json'}
    for name,digest in [('summary',SUMMARY_SHA),('arrays',ARRAYS_SHA),('data',DATA_SHA),('config',CONFIG_SHA)]:checked(paths[name],digest)
    s=read(paths['summary']);cfg=read(paths['config']);generation=read(paths['generation']);g0=read(paths['G0'])
    manifest=read(paths['release_manifest'])
    if (manifest['version']!='v0.7.1' or manifest['stage']!='C07' or
        g0['status']!='C07_PUBLISHED_AND_RELEASED' or g0['publication']['tag']!='v0.7.1' or
        g0['publication']['status']!='PUBLISHED'):raise ValueError('Final C07 publication identity required')
    publication=read(checked(g0['publication']['evidence']['path'],g0['publication']['evidence']['sha256']))
    if (publication['status']!='PUBLISHED_ASSETS_BYTE_VERIFIED' or publication['version']!='v0.7.1' or
        publication['commit']!=g0['publication']['commit']):raise ValueError('Publication receipt differs')
    asset=next(a for a in publication['assets'] if a['name']=='manifest.json')
    checked(paths['release_manifest'],asset['sha256'])
    if asset.get('byte_equal') is not True:raise ValueError('Published manifest must be byte verified')
    for name in ['summary','arrays','data','config','generation']:
        relative=str(paths[name].relative_to(root));checked(paths[name],manifest['inputs_sha256'][relative])
    if (s['models']!=list(MODELS) or s['parameters']!=list(PARAMETERS) or
        s['simulations_per_model']!=500 or s.get('all_simulations_retained') is not True or
        s['arrays_sha256']!=ARRAYS_SHA or s['provenance']['all_ids_retained'] is not True or
        s['provenance']['data_sha256']!=DATA_SHA or s['provenance']['experiment_sha256']!=CONFIG_SHA or
        s['provenance']['runtime_identity']!=g0['c07_runtime_identity'] or
        cfg['n_realizations']!=500 or cfg['models']!=list(MODELS) or
        generation['realizations']!=500 or generation['config_sha256']!=CONFIG_SHA or generation['data_sha256']!=DATA_SHA):
        raise ValueError('Models, data, prior or complete500 provenance differ')
    inventory=s['provenance']['inventory'];seen=set()
    if len(inventory)!=2500:raise ValueError('Exactly2500 inventory entries required')
    for row in inventory:
        target=row['target'];datum=row['datum'];model=row['model']
        if (type(target)is not int or type(datum)is not int or target in seen or
            not 0<=target<2500 or not 0<=datum<500 or model!=MODELS[target//500] or datum!=target%500):
            raise ValueError('Duplicate or mismatched target/model/datum inventory')
        for key in ['diagnostic_sha256','numeric_sha256','producer_sha256']:
            h=row[key]
            if not isinstance(h,str) or len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('Invalid inventory hash')
        seen.add(target)
    if seen!=set(range(2500)):raise ValueError('Missing target inventory')
    shapes=dict(quantiles_unit=(5,500,5,4),quantiles_physical=(5,500,5,4),cut_precision_pass=(5,500,5,4),
                resolved=(5,500,6),weight_ess=(5,500),maximum_weight=(5,500),truth=(500,5),bounds=(5,2),probabilities=(4,))
    with np.load(paths['arrays'],allow_pickle=False) as p:a={k:p[k].copy() for k in shapes}
    for k,shape in shapes.items():
        x=a[k]
        if x.shape!=shape or not np.isfinite(x).all() or x.dtype!=(np.bool_ if k in ['resolved','cut_precision_pass'] else np.float64):
            raise ValueError('Invalid compact array shape/dtype/finitude: '+k)
    if not np.array_equal(a['probabilities'],[.05,.5,.9,.95]) or not np.array_equal(a['bounds'],cfg['prior']['bounds']):raise ValueError('Prior/probabilities differ')
    q=a['quantiles_unit'];width=np.diff(a['bounds'],axis=1)[:,0]
    if np.any(width<=0) or np.any((q<0)|(q>1)) or np.any(np.diff(q,axis=-1)<0):raise ValueError('Invalid ordered quantiles/prior')
    if not np.array_equal(a['quantiles_physical'],a['bounds'][None,None,:,0,None]+width[None,None,:,None]*q):raise ValueError('Quantile units differ')
    with np.load(paths['data'],allow_pickle=False) as p:truth=p['truth'].copy()
    if not np.array_equal(truth,a['truth']) or len(np.unique(truth,axis=0))!=500:raise ValueError('500 distinct original truths required')
    if np.any(truth<a['bounds'][:,0]) or np.any(truth>a['bounds'][:,1]):raise ValueError('Truth outside prior')
    if np.any(a['weight_ess']<1) or np.any(a['weight_ess']>262144*(1+1e-12)) or np.any((a['maximum_weight']<=0)|(a['maximum_weight']>1)):
        raise ValueError('Impossible saved high-level weights')
    provenance=dict(inputs={k:dict(path=str(p.relative_to(root)),sha256=sha(p),bytes=p.stat().st_size) for k,p in paths.items()},
        publication=dict(path=g0['publication']['evidence']['path'],sha256=g0['publication']['evidence']['sha256']),
        original_inventory_entries=2500,unique_targets=2500,models=list(MODELS),datasets_per_model=500,
        distinct_original_truths=500,all_targets_retained=True,source_arrays_only=True,
        underlying2500_diagnostics_reaudited=False,physical_or_posterior_arrays_read=False,
        original_data_only_member_read='truth',new_inference=False)
    return s,a,provenance
