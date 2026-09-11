import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
"""Portable independent math/resource/cache-contract tests for the new backend."""
import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from pta import transfer
from pta.orf import raw_direct_orf
from inference.orf_blas import RealHarmonicBasis,TableBudget
from inference.orf_table_builder import atomic_new_npz

class BackendTests(unittest.TestCase):
    def setUp(self):
        self.cosine=.3
        self.points=np.array([[0.,0.,1.],[np.sqrt(1-self.cosine**2),0.,self.cosine]])
        self.y=np.array([2.,5.])
    def test_threshold_analytic_normalization(self):
        basis=RealHarmonicBasis(self.points,lmax=48,nmu=120,planned_batch=1)
        actual=basis.evaluate(np.array([0.]),self.y)[0]
        delta=self.points@self.points.T;t=np.array([transfer(float(y),1.) for y in self.y])
        expected=.2*t[:,None]*t[None,:].conj()*(3*delta**2-1)/2
        np.testing.assert_allclose(actual,expected,atol=2e-13,rtol=2e-13)
    def test_independent_direct_integrals(self):
        basis=RealHarmonicBasis(self.points,lmax=48,nmu=120,planned_batch=2)
        actual=basis.evaluate(np.array([.4,1.]),self.y)
        for i,beta in enumerate([.4,1.]):
            expected=raw_direct_orf(beta,self.cosine,self.y[0],self.y[1],nmu=96,nphi=192)
            self.assertLess(abs(actual[i,0,1]-expected),1e-11)
            self.assertLess(np.max(abs(actual[i]-actual[i].conj().T)),1e-14)
            self.assertGreaterEqual(np.linalg.eigvalsh(actual[i]).min(),-1e-12)
    def test_budget_prevents_basis_allocation(self):
        with patch('inference.orf_blas.roots_legendre',side_effect=AssertionError('Allocation reached before refusal')):
            with self.assertRaises(RuntimeError):
                RealHarmonicBasis(self.points,lmax=100,nmu=300,budget=TableBudget(maximum_estimated_memory_bytes=1024),planned_batch=8)
            with self.assertRaises(RuntimeError):
                RealHarmonicBasis(self.points,lmax=100,nmu=300,budget=TableBudget(maximum_multiplications_per_batch=1),planned_batch=8)
    def test_existing_cache_bytes_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'cache.npz'
            self.assertTrue(atomic_new_npz(p,Gamma=np.zeros((2,2)),record='first'))
            first=hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertFalse(atomic_new_npz(p,Gamma=np.ones((2,2)),record='second'))
            self.assertEqual(first,hashlib.sha256(p.read_bytes()).hexdigest())
            with np.load(p) as data:self.assertEqual(str(data['record']),'first')

if __name__=='__main__':unittest.main()
