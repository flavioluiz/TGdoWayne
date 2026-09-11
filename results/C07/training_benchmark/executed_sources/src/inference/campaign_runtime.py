"""NumPy reference runtime and an explicit optional deterministic backend factory."""
from pathlib import Path
import hashlib,importlib,json,sys
import numpy as np
from .model import experiment,YEAR
from .campaign_io import *
from .orf_interpolation import EvenThresholdCubicORF
from .pointwise_preallocated import PreallocatedCubicPointLikelihood
from .linalg_batch import forward_substitution

class CampaignRuntime:
 def __init__(self,experiment_path,data_path,table_path,table_manifest_path,validation_config_path,settings_path,*,build=False,backend_factory=None,threads=1,native_library_path=None):
  self.paths={k:Path(v).resolve() for k,v in dict(experiment=experiment_path,data=data_path,table=table_path,table_manifest=table_manifest_path,validation_config=validation_config_path,settings=settings_path).items()}
  self.native_library=None if native_library_path is None else Path(native_library_path).resolve()
  if self.native_library is not None:self.paths['native_library']=self.native_library
  if self.native_library and backend_factory:raise ValueError('Choose one explicit backend adapter.')
  self.cfg=read_json(self.paths['experiment']);self.settings=read_json(self.paths['settings']);validcfg=read_json(self.paths['validation_config']);manifest=read_json(self.paths['table_manifest']);self.exp=experiment(self.cfg)
  if self.cfg['models']!=list(MODELS) or self.cfg['prior']['kind']!='independent uniform in these coordinates' or self.cfg['fixed_red_slope']!=4 or self.cfg['positive_channels']!=[1,2,3,4]:raise ValueError('Unsupported C07 scientific configuration.')
  if manifest.get('status')!='VALIDATED_IN_STATED_NUMERICAL_TEST_DOMAIN' or sha256(self.paths['table'])!=manifest['file_sha256'] or sha256(self.paths['validation_config'])!=manifest['config_sha256']:raise ValueError('Table/reference validation identity mismatch.')
  self.bounds=np.asarray(self.cfg['prior']['bounds'],float)
  if not np.array_equal(self.bounds,np.asarray(validcfg['prior']['bounds'],float)) or self.cfg['parameters']!=validcfg['parameters']:raise ValueError('Prior/parameter domain differs from table validation.')
  y=2*np.pi*self.exp['f'][:,None]*self.exp['distance_ly'][None,:]*YEAR
  physical=hashlib.sha256(json.dumps(self.cfg['orf'],sort_keys=True).encode()+self.exp['points'].tobytes()+y.tobytes()).hexdigest()
  if physical!=manifest['physical_signature']:raise ValueError('Physical ORF signature differs from validated table.')
  self.data=load_observations(self.paths['data'],self.exp);self.n=len(self.data['q']);self.targets=target_ids(self.settings,self.n)
  if self.cfg['n_realizations']!=self.n:raise ValueError('Declared and actual dataset counts differ.')
  self.input_hashes={key:sha256(path) for key,path in self.paths.items()}
  self.backend_factory=backend_factory;self.threads=positive_int(threads,'threads')
  if backend_factory and not backend_factory.startswith('inference.'):raise ValueError('Optional backend factory must be an explicit inference.module:function.')
  modules=['campaign_runtime','campaign_io','campaign_training','campaign_iid','campaign_diagnostic_io','pointwise','pointwise_preallocated','orf_cubic_reference','orf_interpolation','linalg_batch','gmm_proposal','gmm_proposal_reference','gmm_density','likelihood_threads','gmm_fit','gmm_fit_reference','mh_training','model','iid_diagnostics']
  self.source_paths={name:Path(importlib.util.find_spec('inference.'+name).origin) for name in modules}
  if self.native_library:
   spec=importlib.util.find_spec('inference.native_likelihood')
   if spec is None:raise RuntimeError('Native module has not been integrated; choose the NumPy reference explicitly.')
   self.source_paths['native_likelihood']=Path(spec.origin)
  if backend_factory:
   name=backend_factory.split(':',1)[0];self.source_paths[name]=Path(importlib.util.find_spec(name).origin)
  pta_root=Path(next(iter(importlib.util.find_spec('pta').submodule_search_locations)))
  self.source_paths.update({'pta.'+p.stem:p for p in pta_root.glob('*.py')})
  self.source_hashes={name:sha256(path) for name,path in self.source_paths.items()}
  self.target_identity=canonical_hash({k:v for k,v in self.input_hashes.items() if k not in ('settings','native_library')})
  self.identity=canonical_hash(dict(inputs=self.input_hashes,sources=self.source_hashes,backend='native' if self.native_library else backend_factory or 'numpy_reference',threads=self.threads))
  self.table=None;self.likelihood=None
  if build:self.build()
 def preflight(self):
  s=self.settings;training=s.get('training',{});production=s.get('production',{});budget=s['budget'];pending=[]
  steps=training.get('steps');levels=production.get('levels');count=max(levels) if levels else None;replicates=production.get('replicates',4)
  if steps is None:pending.append('Training length awaiting the independent cold-training experiment.')
  else:positive_int(steps,'training steps')
  if levels and (len(levels)!=2 or levels!=sorted(set(levels))):raise ValueError('Two ordered IID levels required.')
  if count is None:pending.append('IID lengths not frozen.')
  else:positive_int(count,'samples per replicate')
  if replicates!=4:raise ValueError('The registered production requires exactly four independent replicates.')
  if not training.get('approved',False):pending.append('Cold-training settings not approved for campaign execution.')
  if not s.get('execution_enabled',False):pending.append('Execution deliberately disabled in this prospective configuration.')
  active=positive_int(s.get('targets_per_block',16),'targets_per_block');batch=positive_int(production.get('likelihood_batch',512),'likelihood batch')
  with np.load(self.paths['table'],allow_pickle=False) as p:nodes=p['nodes'];shape=p['matrices'].shape
  intervals=len(nodes)-1;K,P=shape[1:3];D=len(self.exp['H']);coefficient=4*intervals*K*P*P*16;matrix=int(np.prod(shape))*16;bank=8*intervals*K*(6*D+21*D*D)
  spline=4*coefficient+matrix+128*1024**2
  retained=bank+coefficient+matrix+128*1024**2
  raw_per_target=0 if count is None else int(sum(levels)*replicates*(14*8+1)+len(levels)*replicates*65536)
  raw_block=raw_per_target*min(active,len(self.targets));numeric=max(spline,retained*(2 if self.native_library else 1)+raw_per_target*3)+int(batch*K*(P*P*16+21*D*D*8))
  for key,value in [('maximum_numeric_bytes',numeric),('maximum_active_raw_bytes',raw_block)]:
   if value>positive_int(budget[key],key):raise RuntimeError(key+' preflight exceeded.')
  production_work=None if count is None else sum(levels)*replicates*len(self.targets)
  if production_work is not None and production_work>positive_int(budget['maximum_likelihood_values'],'maximum_likelihood_values'):raise RuntimeError('Campaign likelihood-count budget exceeded.')
  return dict(identity=self.identity,targets=len(self.targets),datasets=self.n,models=s.get('models',list(MODELS)),training_steps=steps,levels=levels,samples_per_replicate_main=count,replicates=replicates,production_likelihood_values=production_work,estimated_numeric_bytes=numeric,estimated_raw_per_target_bytes=raw_per_target,estimated_active_raw_bytes=raw_block,full_raw_if_never_released_bytes=raw_per_target*len(self.targets),blocks=[self.targets[i:i+active].tolist() for i in range(0,len(self.targets),active)],pending=pending,execution_ready=not pending,input_sha256=self.input_hashes,truth_deserialized=False,backend='native' if self.native_library else self.backend_factory or 'numpy_reference',threads=self.threads)
 def build(self):
  report=self.preflight()
  with np.load(self.paths['table'],allow_pickle=False) as p:table=EvenThresholdCubicORF(p['nodes'],p['matrices'],coordinate='beta')
  if len(table.fallback):raise RuntimeError('The approved table unexpectedly needs PSD fallbacks.')
  maximum=self.settings['budget']['maximum_numeric_bytes'];reference=PreallocatedCubicPointLikelihood(self.exp,self.data,table,maximum_estimated_numeric_bytes=maximum);reference.solve=forward_substitution
  self.table=table;self.reference=reference;self.likelihood=reference
  if self.native_library:
   from .native_likelihood import NativeLikelihood
   from .likelihood_threads import ThreadedLikelihood
   owned=NativeLikelihood(reference,self.bounds,self.native_library)
   self.likelihood=ThreadedLikelihood(owned,self.threads);self.reference=None;self.table=None
   del reference,table
  elif self.backend_factory:
   module,name=self.backend_factory.split(':',1);factory=getattr(importlib.import_module(module),name);self.likelihood=factory(reference,threads=self.threads)
   if not callable(self.likelihood):raise TypeError('Backend factory must return callable(theta,targets).')
  return self
 def close(self):
  if self.likelihood is not None and hasattr(self.likelihood,'close'):self.likelihood.close()
 def snapshot(self,output_root):
  root=Path(output_root)/'provenance'/self.identity
  manifest=root/'manifest.json'
  if manifest.exists():
   old=read_json(manifest)
   if old['source_sha256']!=self.source_hashes or old['input_sha256']!=self.input_hashes:raise RuntimeError('Provenance collision.')
   return
  for name,path in self.source_paths.items():
   dest=root/(name.replace('.','/')+'.py')
   if dest.exists():
    if sha256(dest)!=self.source_hashes[name]:raise RuntimeError('Source snapshot changed.')
   else:atomic_new(dest,lambda p,source=path:p.write_bytes(source.read_bytes()))
  write_json_new(manifest,dict(identity=self.identity,target_identity=self.target_identity,source_sha256=self.source_hashes,input_sha256=self.input_hashes,backend='native' if self.native_library else self.backend_factory or 'numpy_reference',threads=self.threads))
 def verify_unchanged(self):
  if any(sha256(p)!=self.input_hashes[k] for k,p in self.paths.items()) or any(sha256(p)!=self.source_hashes[k] for k,p in self.source_paths.items()):raise RuntimeError('A frozen campaign input or source changed during execution.')
 def require_execution(self):
  p=self.preflight()
  if not p['execution_ready']:raise RuntimeError('Execution pending: '+' '.join(p['pending']))
  if self.likelihood is None:self.build()
  return self
