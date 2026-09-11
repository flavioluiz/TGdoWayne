"""Independent C06 PSD and direct trace/latent checks on the four toy observations."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'src'))
from inference.model import experiment
from inference.data_generation import StoredExactORF
from pta.simulation import SpectralParameters,residual_covariances

HERE=ROOT/'tmp/c07_generator_review';cfg=json.loads((HERE/'toy_config.json').read_text());e=experiment(cfg)
with np.load(HERE/'toy_product/data.npz',allow_pickle=False) as p:data={k:p[k].copy() for k in p.files}
reader=StoredExactORF(e,cfg['orf'],HERE/'toy_product/orf_cache');rng=np.random.default_rng(cfg['data_seed']);errors=[];minimum=[]
for i,theta in enumerate(data['truth']):
    gamma=reader.evaluate(float(theta[0]))
    params=SpectralParameters(log10_gw_amplitude=theta[1],gw_slope=theta[2],log10_red_amplitude=theta[3],red_slope=cfg['fixed_red_slope'],white_efac=10**theta[4])
    C=residual_covariances(e['f'],gamma,e['sigma'],e['red'],e['dt'],params)/e['scale'][:,None,None]
    minimum.append(float(np.linalg.eigvalsh(C).min()))
    z=(rng.standard_normal(data['q'][i].shape)+1j*rng.standard_normal(data['q'][i].shape))/np.sqrt(2)
    q=np.stack([np.linalg.cholesky(c)@zz for c,zz in zip(C,z)])
    x=np.array([[np.vdot(qk,h@qk).real for h in e['H']] for qk in q])
    mean=np.array([[np.trace(h@c).real for h in e['H']] for c in C])
    cov=np.array([[[np.trace(ha@c@hb@c).real for hb in e['H']] for ha in e['H']] for c in C])
    latent=np.concatenate([np.sqrt(2)*z.real,np.sqrt(2)*z.imag],axis=-1)[:,:len(e['H'])]
    gaussian=mean+np.stack([np.linalg.cholesky(s)@v for s,v in zip(cov,latent)])
    row={'realization':i,'q_max_abs_error':float(np.max(abs(q-data['q'][i]))),
         'quadratic_max_abs_error':float(np.max(abs(x-data['x_physical'][i]))),
         'paired_gaussian_max_abs_error':float(np.max(abs(gaussian-data['x_gaussian'][i])))}
    errors.append(row)
    np.testing.assert_allclose(q,data['q'][i],rtol=2e-12,atol=2e-12)
    np.testing.assert_allclose(x,data['x_physical'][i],rtol=2e-12,atol=2e-12)
    np.testing.assert_allclose(gaussian,data['x_gaussian'][i],rtol=2e-12,atol=2e-12)
with np.load(ROOT/'results/C07/fixtures/pilot_data.npz',allow_pickle=False) as p:pilot=p['truth']
bounds=np.array(cfg['prior']['bounds'])
assert np.all((data['truth']>bounds[:,0])&(data['truth']<bounds[:,1]))
assert not np.any(np.all(data['truth'][:,None,:]==pilot[None,:,:],axis=-1))
assert data['truth'].shape==(4,5) and data['q'].shape==(4,4,12) and data['x_physical'].shape==(4,4,10)
report={'status':'PASS','scope':'Four toy draws and algebraic reproduction; not an empirical covariance/pseudocovariance campaign.',
        'arrays_shapes':{k:list(v.shape) for k,v in data.items()},'rows':errors,
        'strictly_interior_prior_truths':True,'truths_distinct_from_pilot16':True,'minimum_covariance_eigenvalue':min(minimum),
        'conventions':'Proper CN z=(N(0,1)+iN(0,1))/sqrt(2), normalized PSD C/scale, quadratic q^H H q, Gaussian trace moments and shared latent normals.',
        'physical_covariance_builder':'pta.simulation.residual_covariances; does not call inference.model.covariance_batch',
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(HERE/'independent_arrays.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
