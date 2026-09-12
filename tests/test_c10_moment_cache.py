"""Synthetic algebra/cache tests; no physical draws, ORFs or population."""
from pathlib import Path
import sys
import unittest
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'src'),str(R/'scripts'),str(R/'tmp/c10_exact_lifecycle_v1')]
from pta.moment_cache import MomentCache
from selected_kernel import ConditionalLikelihood
from c10_memoized_kernel import MemoizedLikelihood


class MomentCacheChecks(unittest.TestCase):
    def setup_inputs(self):
        rng=np.random.default_rng(10022026)
        q=rng.normal(size=(2,2,3))+1j*rng.normal(size=(2,2,3));x=rng.normal(size=(2,2,2));g=rng.normal(size=(2,2,2))
        H=np.array([np.diag([1.,0.,0.]),np.diag([0.,0.,1.])]);w=np.array([.4,.6])
        B=rng.normal(size=(2,3,3))+1j*rng.normal(size=(2,3,3));c0=B@B.conj().transpose(0,2,1)+np.eye(3);c1=np.broadcast_to(.1*np.eye(3),c0.shape).copy()
        return q,x,g,H,w,c0,c1

    def test_same_densities_distinct_observations_and_unchanged_counts(self):
        q,x,g,H,w,c0,c1=self.setup_inputs();cache=MomentCache();options=dict(maximum_logl_values=10000,maximum_workspace_bytes=16*1024**2)
        for factor in (1.,1.25):
            reference=ConditionalLikelihood(q*factor,x*factor,g*factor,H,w,**options)
            candidate=MemoizedLikelihood(q*factor,x*factor,g*factor,H,w,moment_cache=cache,**options)
            for eps in ([0.,.25,.5,1.],[.1,.9]):
                a=reference.evaluate(c0,c1,eps)[0];b=candidate.evaluate(c0,c1,eps)[0]
                np.testing.assert_array_equal(a,b)
                self.assertEqual(reference.logl_values,candidate.logl_values)
                self.assertEqual(reference.completed_logl_values,candidate.completed_logl_values)
        self.assertEqual(cache.misses,1);self.assertEqual(cache.hits,3)

    def test_changed_covariance_and_bounded_eviction(self):
        q,x,g,H,w,c0,c1=self.setup_inputs();cache=MomentCache(maximum_entries=1)
        candidate=MemoizedLikelihood(q,x,g,H,w,moment_cache=cache,maximum_logl_values=1000,maximum_workspace_bytes=16*1024**2)
        a=candidate.moments(c0,c1);self.assertFalse(a[2][0].flags.writeable)
        changed=c0.copy();changed[0,0,0]+=.001
        b=candidate.moments(changed,c1);self.assertFalse(np.array_equal(a[2][0],b[2][0]));self.assertEqual(len(cache.entries),1)
        candidate.moments(c0,c1);self.assertEqual(cache.misses,3)

    def test_geometry_mutation_rejected_and_metadata_not_aliased(self):
        q,x,g,H,w,c0,c1=self.setup_inputs();cache=MomentCache()
        candidate=MemoizedLikelihood(q,x,g,H,w,moment_cache=cache,maximum_logl_values=1000,maximum_workspace_bytes=16*1024**2)
        checks=candidate.moments(c0,c1)[3];checks['C1_minimum_eigenvalue'][0]=-999
        self.assertGreater(candidate.moments(c0,c1)[3]['C1_minimum_eigenvalue'][0],0)
        candidate.H.setflags(write=True);candidate.H[0,0,0]+=1
        with self.assertRaises(RuntimeError):candidate.moments(c0,c1)


if __name__=='__main__':unittest.main()
