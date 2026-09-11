import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
"""Corruption tests exercise every cache-reuse contract without a large basis."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from inference.orf_table_builder import (read_validated_entry,read_validated_checkpoint,
                              matrix_digest,build_checked_nodes,ConstructionBudget)

class CacheIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'entry.npz'
        self.gamma=np.array([[[1,.1j],[-.1j,2]],[[2,.2],[.2,3]]],complex)
        self.record=dict(signature='physical',u=.5,channel_errors=[1e-9,2e-9],maximum_coarse_fine_difference=2e-9,
                         minimum_eigenvalue=float(np.linalg.eigvalsh(self.gamma).min()))
    def tearDown(self):self.temp.cleanup()
    def entry(self,g=None,r=None):
        np.savez_compressed(self.path,Gamma=self.gamma if g is None else g,record=json.dumps(self.record if r is None else r))
        digest=hashlib.sha256(self.path.read_bytes()).hexdigest()
        try:return read_validated_entry(self.path,signature='physical',u=.5,K=2,P=2,tolerance=1e-8)
        finally:self.assertEqual(digest,hashlib.sha256(self.path.read_bytes()).hexdigest())
    def test_legacy_and_v2_compatible(self):
        g,_=self.entry();np.testing.assert_array_equal(g,self.gamma)
        r={**self.record,'integrity_schema':2,'Gamma_sha256':matrix_digest(self.gamma)}
        self.entry(r=r)
    def test_corrupt_matrices_rejected_and_preserved(self):
        bad=[]
        g=self.gamma.copy();g[0,0,0]=np.nan;bad.append(g)
        g=self.gamma.copy();g[0,0,0]=np.inf;bad.append(g)
        g=self.gamma.copy();g[0,0,1]+=1;bad.append(g)
        g=self.gamma.copy();g[0,0,0]=-1;bad.append(g)
        bad.append(self.gamma[:1])
        for g in bad:
            with self.subTest(shape=g.shape),self.assertRaises(RuntimeError):self.entry(g=g)
    def test_corrupt_metadata_rejected(self):
        mutations=[{'signature':'other'},{'u':.6},{'u':float('nan')},{'u':True},
                   {'channel_errors':[float('nan'),0]},{'channel_errors':[0,float('inf')]},
                   {'channel_errors':[-1,0]},{'channel_errors':[0]},
                   {'maximum_coarse_fine_difference':float('nan')},
                   {'maximum_coarse_fine_difference':0},
                   {'minimum_eigenvalue':float('nan')},{'minimum_eigenvalue':9},
                   {'integrity_schema':2},{'Gamma_sha256':'changed'}]
        for mutation in mutations:
            with self.subTest(mutation=mutation),self.assertRaises(RuntimeError):self.entry(r={**self.record,**mutation})
    def test_digest_detects_psd_preserving_change(self):
        g=2*self.gamma;r={**self.record,'minimum_eigenvalue':float(np.linalg.eigvalsh(g).min()),
                          'integrity_schema':2,'Gamma_sha256':matrix_digest(self.gamma)}
        with self.assertRaisesRegex(RuntimeError,'digest'):self.entry(g=g,r=r)
    def checkpoint(self,mutation=None):
        resolutions=[('coarse',4,12),('fine',6,16)]
        timing=dict(frequency=2,maximum_coarse_fine_difference=2e-9,minimum_eigenvalue=self.record['minimum_eigenvalue'],
                    stages=[dict(resolution=label,lmax=l,nmu=n,basis_build_seconds=.1,evaluation_seconds=.2) for label,l,n in resolutions])
        payload=dict(u=np.array([.2,.5]),Gamma=self.gamma,errors=np.array([1e-9,2e-9]),signature='physical',
                     timing=timing,Gamma_sha256=matrix_digest(self.gamma))
        if mutation:mutation(payload)
        payload['timing']=json.dumps(payload['timing']);np.savez_compressed(self.path,**payload)
        return read_validated_checkpoint(self.path,signature='physical',nodes=np.array([.2,.5]),frequency=2,P=2,tolerance=1e-8,resolutions=resolutions)
    def test_checkpoint_valid(self):
        g,errors,_=self.checkpoint();np.testing.assert_array_equal(g,self.gamma)
    def test_checkpoint_corruption(self):
        mutations=[lambda p:p.update(signature='wrong'),lambda p:p.update(u=np.array([.3,.5])),
                   lambda p:p.update(Gamma=np.full_like(self.gamma,np.nan)),
                   lambda p:p.update(errors=np.array([np.nan,0])),lambda p:p.update(errors=np.array([0])),
                   lambda p:p.update(Gamma_sha256='bad'),lambda p:p['timing'].update(frequency=3),
                   lambda p:p['timing']['stages'][0].update(nmu=13),
                   lambda p:p['timing']['stages'][0].update(evaluation_seconds=np.inf)]
        for j,mutation in enumerate(mutations):
            with self.subTest(case=j),self.assertRaises(RuntimeError):self.checkpoint(mutation)
    def test_builder_reads_existing_entry_through_guard(self):
        # The existence path must refuse before allocating even a small basis.
        self.entry();destination=self.path.parent
        class Meta:
            signature='physical'
            def __init__(self,*args):pass
        with patch('inference.orf_table_builder.ExactNodeORF',Meta),patch('inference.orf_table_builder.token',return_value='entry'):
            self.record['u']=.7;self.entry_unsafe()
            with self.assertRaisesRegex(RuntimeError,'mass mismatch'):
                build_checked_nodes({'f':[1,2],'points':np.eye(2)}, {'maximum_matrix_abs_difference':1e-8},
                                    [.5],destination,budget=ConstructionBudget(),validate_direct=False)
    def test_fresh_build_then_checkpoint_resume(self):
        from inference.model import YEAR
        e=dict(f=np.array([1/YEAR]),distance_ly=np.array([.03,.05]),points=np.array([[0.,0.,1.],[1.,0.,0.]]))
        cfg=dict(maximum_phase=2,lmax_margin=32,nmu_margin=90,fine_lmax_addition=8,fine_nmu_addition=20,
                 maximum_matrix_abs_difference=1e-8,maximum_total_work_units=10**8,maximum_estimated_memory_bytes=10**7)
        out=build_checked_nodes(e,cfg,[.2,.7],self.path.parent,budget=ConstructionBudget(),validate_direct=False)
        self.assertEqual(out['written_nodes'],2)
        # Remove only our just-created temporary final rows to exercise checkpoint recovery.
        for p in self.path.parent.glob('*.npz'):p.unlink()
        with patch('inference.orf_table_builder.RealHarmonicBasis',side_effect=AssertionError('Checkpoint was not reused')):
            resumed=build_checked_nodes(e,cfg,[.2,.7],self.path.parent,budget=ConstructionBudget(),validate_direct=False)
        self.assertEqual(resumed['written_nodes'],2)
        for p in self.path.parent.glob('*.npz'):
            with np.load(p) as data:record=json.loads(str(data['record']))
            self.assertEqual(record['integrity_schema'],2)
            read_validated_entry(p,signature=out['physical_signature'],u=record['u'],K=1,P=2,tolerance=1e-8)
    def entry_unsafe(self):np.savez_compressed(self.path,Gamma=self.gamma,record=json.dumps(self.record))

if __name__=='__main__':unittest.main()
