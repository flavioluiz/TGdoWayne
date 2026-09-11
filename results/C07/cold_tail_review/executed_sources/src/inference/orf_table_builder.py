"""Compatible cache payloads with a separate, explicit table-construction budget.

Existing cache files are never replaced. Coarse/fine checks apply at every new
node; sparse direct checks use the frozen legacy method on in-memory matrices.
"""
from dataclasses import dataclass,asdict
from pathlib import Path
import gc,hashlib,json,os,tempfile,time
import numpy as np
from .orf_blas import RealHarmonicBasis,TableBudget,estimate
from .orf_backend import ExactNodeORF

@dataclass(frozen=True)
class ConstructionBudget:
    maximum_estimated_numeric_memory_bytes:int=768*1024**2
    maximum_total_real_multiplications:int=40_000_000_000_000
    maximum_requested_nodes:int=6000
    batch_size:int=8
    maximum_batch_real_multiplications:int=50_000_000_000

def token(signature,u):return hashlib.sha256(signature.encode()+float(u).hex().encode()).hexdigest()

def atomic_new_npz(path,**values):
    """Publish one complete file atomically, never overwrite an existing file."""
    fd,name=tempfile.mkstemp(dir=path.parent,prefix='.tmp_real_blas_',suffix='.npz');os.close(fd)
    try:
        np.savez_compressed(name,**values)
        try:os.link(name,path)
        except FileExistsError:return False
        return True
    finally:os.unlink(name)

def matrix_digest(gamma):
    """Canonical digest of numeric contents; legacy records may lack this field."""
    a=np.ascontiguousarray(gamma,dtype=np.complex128)
    return hashlib.sha256(np.asarray(a.shape,dtype=np.int64).tobytes()+a.tobytes()).hexdigest()

def validate_matrices(gamma,shape,*,context='matrix'):
    """Reject corruption before Hermitian eigensolvers; never repair or clip."""
    a=np.asarray(gamma)
    if a.shape!=tuple(shape) or not np.issubdtype(a.dtype,np.number):
        raise RuntimeError(f'{context}: numeric matrix shape mismatch.')
    if not np.isfinite(a).all():raise RuntimeError(f'{context}: nonfinite matrix.')
    scale=max(1.,float(np.max(abs(a),initial=0.)))
    if float(np.max(abs(a-a.swapaxes(-1,-2).conj()),initial=0.))>1e-12*scale:
        raise RuntimeError(f'{context}: matrix is not Hermitian.')
    eigen=np.linalg.eigvalsh(a)
    minimum=float(eigen.min(initial=np.inf))
    if not np.isfinite(eigen).all() or minimum < -1e-12:
        raise RuntimeError(f'{context}: matrix fails PSD tolerance; no eigenvalue clipping.')
    return minimum

def validate_errors(errors,shape,tolerance,*,context='errors'):
    a=np.asarray(errors)
    if a.shape!=tuple(shape) or not np.issubdtype(a.dtype,np.number) or np.iscomplexobj(a):
        raise RuntimeError(f'{context}: real error-array shape mismatch.')
    if not np.isfinite(a).all() or np.any(a<0) or np.any(a>tolerance):
        raise RuntimeError(f'{context}: errors must be finite, nonnegative and within tolerance.')
    return a

def finite_scalar(value,name):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not np.isfinite(value):
        raise RuntimeError(f'{name}: finite real scalar required.')
    return float(value)

def read_validated_entry(path,*,signature,u,K,P,tolerance):
    """Accept compatible legacy entries after numeric and metadata validation.

    A legacy entry without a digest cannot prove absence of arbitrary historical
    changes that preserve all tested properties. New v2 rows also check a digest.
    """
    try:
        with np.load(path,allow_pickle=False) as payload:
            gamma=payload['Gamma'].copy();record=json.loads(str(payload['record']))
        if not isinstance(record,dict) or record.get('signature')!=signature:
            raise RuntimeError('Cache signature mismatch.')
        if finite_scalar(record.get('u'),'cache u')!=float(u):raise RuntimeError('Cache mass mismatch.')
        minimum=validate_matrices(gamma,(K,P,P),context='cache')
        errors=validate_errors(record.get('channel_errors'),(K,),tolerance,context='cache channel errors')
        maximum=finite_scalar(record.get('maximum_coarse_fine_difference'),'cache maximum error')
        if maximum<0 or maximum>tolerance or not np.isclose(maximum,errors.max(),rtol=1e-12,atol=1e-15):
            raise RuntimeError('Cache maximum error is inconsistent.')
        declared=finite_scalar(record.get('minimum_eigenvalue'),'cache minimum eigenvalue')
        if declared < -1e-12 or not np.isclose(declared,minimum,rtol=1e-10,atol=1e-10):
            raise RuntimeError('Cache minimum eigenvalue is inconsistent.')
        if record.get('integrity_schema')==2 and 'Gamma_sha256' not in record:
            raise RuntimeError('Missing v2 matrix digest.')
        if 'Gamma_sha256' in record and record['Gamma_sha256']!=matrix_digest(gamma):
            raise RuntimeError('Cache numeric-content digest mismatch.')
        return gamma,record
    except (KeyError,ValueError,TypeError,OSError) as error:
        raise RuntimeError(f'Invalid cache payload {path}: {error}') from error

def read_validated_checkpoint(path,*,signature,nodes,frequency,P,tolerance,resolutions):
    try:
        with np.load(path,allow_pickle=False) as payload:
            oldnodes=payload['u'];gamma=payload['Gamma'].copy();errors=payload['errors'].copy()
            timing=json.loads(str(payload['timing']));stored_signature=str(payload['signature'])
            digest=str(payload['Gamma_sha256'])
        if stored_signature!=signature or oldnodes.shape!=nodes.shape or not np.isfinite(oldnodes).all() or not np.array_equal(oldnodes,nodes):
            raise RuntimeError('Checkpoint signature or nodes mismatch.')
        minimum=validate_matrices(gamma,(len(nodes),P,P),context='checkpoint')
        validate_errors(errors,(len(nodes),),tolerance,context='checkpoint errors')
        if timing.get('frequency')!=frequency or len(timing.get('stages',[]))!=2:
            raise RuntimeError('Checkpoint frequency/stage metadata mismatch.')
        for stage,(label,l,n) in zip(timing['stages'],resolutions):
            if (stage.get('resolution'),stage.get('lmax'),stage.get('nmu'))!=(label,int(l),int(n)):
                raise RuntimeError('Checkpoint resolution mismatch.')
            for name in ['basis_build_seconds','evaluation_seconds']:
                if finite_scalar(stage.get(name),'checkpoint '+name)<0:raise RuntimeError('Negative checkpoint time.')
        maximum=finite_scalar(timing.get('maximum_coarse_fine_difference'),'checkpoint maximum error')
        declared=finite_scalar(timing.get('minimum_eigenvalue'),'checkpoint minimum eigenvalue')
        if not np.isclose(maximum,errors.max(),rtol=1e-12,atol=1e-15) or not np.isclose(declared,minimum,rtol=1e-10,atol=1e-10):
            raise RuntimeError('Checkpoint numeric metadata mismatch.')
        if digest!=matrix_digest(gamma):raise RuntimeError('Checkpoint matrix digest mismatch.')
        return gamma,errors,timing
    except (KeyError,ValueError,TypeError,OSError) as error:
        raise RuntimeError(f'Invalid checkpoint {path}: {error}') from error

def build_checked_nodes(exp,config,nodes,destination,*,budget,validate_direct=True):
    """Return manifest. Caller must coordinate overlapping writers on same nodes.

    This function is independent of ExactNodeORF's legacy work/memory counters;
    it never edits their config values. The physical cache signature is kept.
    Backend provenance and new budgets are stored separately in every new row.
    """
    start=time.perf_counter();destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    requested=np.asarray(nodes,float)
    if requested.ndim!=1 or not np.isfinite(requested).all() or np.any(requested<0) or np.any(requested>1):raise ValueError('Finite mass nodes in[0,1] required.')
    if validate_direct:requested=np.r_[requested,config['direct_mass_points'],.5]
    requested=np.unique(requested)
    if len(requested)>budget.maximum_requested_nodes:raise RuntimeError('Requested-node budget exceeded before construction.')
    if budget.batch_size<1 or budget.batch_size>16:raise ValueError('Explicit batch size must be1..16.')
    meta=ExactNodeORF(exp,config,destination);signature=meta.signature;K=len(exp['f']);P=len(exp['points'])
    pending=[];existing={};existing_paths={}
    for u in requested:
        path=destination/(token(signature,u)+'.npz')
        if path.exists():
            g,r=read_validated_entry(path,signature=signature,u=u,K=K,P=P,tolerance=config['maximum_matrix_abs_difference'])
            existing[float(u)]=g;existing_paths[float(u)]=str(path)
        else:pending.append(float(u))
    pending=np.array(pending);N=len(pending);B=min(max(N,1),budget.batch_size)
    legacy_node_work=int(P*np.sum(meta.l*meta.n+meta.lf*meta.nf))
    total_work=int(2*N*P*np.sum((meta.l-1)*meta.n+(meta.lf-1)*meta.nf))
    # Store the whole fine table plus both current-frequency result arrays.
    reserve=int(16*max(N,1)*(K+2)*P*P+8*max(N,1)*K+sum(g.nbytes for g in existing.values()))
    basis_estimates=[estimate(int(l),int(n),P,B) for l,n in zip(np.r_[meta.l,meta.lf],np.r_[meta.n,meta.nf])]
    memory=reserve+max(r['estimated_memory_bytes'] for r in basis_estimates)
    if total_work>budget.maximum_total_real_multiplications:raise RuntimeError('New aggregate BLAS work budget exceeded before construction.')
    if memory>budget.maximum_estimated_numeric_memory_bytes:raise RuntimeError('New numeric-memory budget exceeded before basis allocation.')
    source={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_name('orf_blas.py')]}
    provenance=dict(name='real_blas_precomputed_associated_legendre_v2_guarded',source_sha256=source,
                    own_budget=asdict(budget),legacy_provider_limits_modified=False,
                    physical_signature_unchanged=True,geometry_dot_roundoff_clipping=True,eigenvalue_clipping=False)
    request_hash=hashlib.sha256(signature.encode()+pending.tobytes()+json.dumps(source,sort_keys=True).encode()).hexdigest()
    scratch=destination/'.real_blas_staging'/request_hash;scratch.mkdir(parents=True,exist_ok=True)
    matrices=np.empty((N,K,P,P),complex);errors=np.empty((N,K));timings=[]
    for k in range(K):
        if N==0:break
        checkpoint=scratch/f'frequency_{k+1}.npz'
        resolutions=[('coarse',meta.l[k],meta.n[k]),('fine',meta.lf[k],meta.nf[k])]
        if checkpoint.exists():
            g,err,timing=read_validated_checkpoint(checkpoint,signature=signature,nodes=pending,frequency=k+1,P=P,tolerance=config['maximum_matrix_abs_difference'],resolutions=resolutions)
            matrices[:,k]=g;errors[:,k]=err;timings.append(timing)
            continue
        results=[];stage_times=[]
        for label,l,n in resolutions:
            table_budget=TableBudget(budget.maximum_estimated_numeric_memory_bytes-reserve,budget.maximum_batch_real_multiplications,16)
            before=time.perf_counter();basis=RealHarmonicBasis(exp['points'],lmax=int(l),nmu=int(n),budget=table_budget,planned_batch=B)
            build_seconds=time.perf_counter()-before;values=np.empty((N,P,P),complex);before=time.perf_counter()
            for first in range(0,N,budget.batch_size):
                u=pending[first:first+budget.batch_size]
                beta=np.sqrt((1-u/(k+1))*(1+u/(k+1)))
                values[first:first+len(u)]=basis.evaluate(beta,meta.y[k])
            elapsed=time.perf_counter()-before;results.append(values)
            stage_times.append(dict(resolution=label,lmax=int(l),nmu=int(n),basis_build_seconds=build_seconds,evaluation_seconds=elapsed))
            del basis;gc.collect()
        for label,values in zip(['coarse','fine'],results):
            validate_matrices(values,(N,P,P),context='new '+label)
        error=np.max(abs(results[0]-results[1]),axis=(1,2));minimum=np.linalg.eigvalsh(results[1]).min(axis=1)
        validate_errors(error,(N,),config['maximum_matrix_abs_difference'],context='new coarse/fine')
        if np.any(error>config['maximum_matrix_abs_difference']) or np.any(minimum<-1e-12):raise RuntimeError('New matrix failed coarse/fine agreement or PSD check; no clipping.')
        matrices[:,k]=results[1];errors[:,k]=error
        timing=dict(frequency=k+1,stages=stage_times,maximum_coarse_fine_difference=float(error.max()),minimum_eigenvalue=float(minimum.min()))
        timings.append(timing)
        if not atomic_new_npz(checkpoint,u=pending,Gamma=results[1],errors=error,timing=json.dumps(timing),signature=signature,Gamma_sha256=matrix_digest(results[1])):
            old,_,_=read_validated_checkpoint(checkpoint,signature=signature,nodes=pending,frequency=k+1,P=P,tolerance=config['maximum_matrix_abs_difference'],resolutions=resolutions)
            if np.max(abs(old-results[1]))>config['maximum_matrix_abs_difference']:
                raise RuntimeError('Concurrent checkpoint differs; existing bytes preserved.')
        print(json.dumps(dict(frequency_complete=k+1,total_frequencies=K,new_nodes=N,timing=timing)),flush=True)
        del results;gc.collect()
    by_u={**existing,**{float(u):matrices[j] for j,u in enumerate(pending)}}
    class InMemoryAudit(ExactNodeORF):
        def evaluate(self,u):
            if float(u) not in by_u:raise RuntimeError('Required independent-check mass was not staged.')
            return by_u[float(u)]
    audit=InMemoryAudit(exp,config,scratch/'direct_metadata')
    direct=audit.direct_checks() if validate_direct else []
    for row in direct:
        if not 0<=finite_scalar(row.get('absolute_difference'),'direct difference')<=1e-7:
            raise RuntimeError('Independent direct check is nonfinite or outside tolerance.')
    direct_status='passed_sparse_checks' if validate_direct else 'not_run_by_explicit_request'
    written=0;concurrent_existing=[]
    for j,u in enumerate(pending):
        record=dict(u=float(u),seconds=(time.perf_counter()-start)/max(N,1),
                    maximum_coarse_fine_difference=float(errors[j].max()),channel_errors=errors[j].tolist(),
                    minimum_eigenvalue=float(np.linalg.eigvalsh(matrices[j]).min()),
                    work_units=legacy_node_work,work_units_interpretation='Legacy reference operation proxy, not a charge to the legacy provider budget.',
                    estimated_memory_bytes=memory,estimated_memory_budget_namespace='independent_real_blas_table_construction',
                    signature=signature,construction_backend=provenance,independent_direct_status=direct_status,integrity_schema=2,Gamma_sha256=matrix_digest(matrices[j]))
        path=destination/(token(signature,u)+'.npz')
        if atomic_new_npz(path,Gamma=matrices[j],record=json.dumps(record)):written+=1
        else:
            old,_=read_validated_entry(path,signature=signature,u=u,K=K,P=P,tolerance=config['maximum_matrix_abs_difference'])
            delta=float(np.max(abs(old-matrices[j])))
            if delta>config['maximum_matrix_abs_difference']:raise RuntimeError('Concurrent existing cache value differs; it was preserved.')
            concurrent_existing.append(dict(u=float(u),difference=delta))
    manifest=dict(status='COMPLETE',requested_nodes=len(requested),new_nodes=N,written_nodes=written,existing_nodes=len(existing),
                  physical_signature=signature,provenance=provenance,total_real_multiplications=total_work,
                  estimated_peak_numeric_bytes=memory,estimated_table_storage_bytes=int(16*len(requested)*K*P*P),
                  timings=timings,sparse_direct_checks=direct,concurrent_existing_preserved=concurrent_existing,
                  VECLIB_MAXIMUM_THREADS=os.environ.get('VECLIB_MAXIMUM_THREADS','unset'),
                  seconds=time.perf_counter()-start,destination=str(destination))
    (scratch/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
