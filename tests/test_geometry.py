"""C06 adapter policy tests; the moment script separately executes real C05 quadrature."""
import unittest
from unittest.mock import patch
import numpy as np
from pta.geometry import CheckedPairMatrixBuilder,fibonacci_directions
from pta.validation import Resolution,ResourceBudget,MAX_VALIDATED_PHASE

class MatrixAuditPolicy(unittest.TestCase):
    def builder(self,budget=600):
        return CheckedPairMatrixBuilder(coarse=Resolution(4,8,8,16),fine=Resolution(6,12,12,24),
            pair_budget=ResourceBudget(100,10000),aggregate_work_budget=budget,atol=1e-5,rtol=1e-3)

    def test_aggregate_refusal_precedes_pair_calculation(self):
        with patch('pta.geometry.checked_orf') as pair:
            with self.assertRaises(ValueError):self.builder(599)(.8,np.array([1.,2,3]),fibonacci_directions(3))
            pair.assert_not_called()

    def test_exact_cache_hermitian_fill_and_common_resolutions(self):
        reports={'resources':{'work_units_proxy':80,'estimated_memory_bytes':500}}
        def pair(beta,cosine,ya,yb,**kwargs):
            # Analytically PSD synthetic kernel, expressly not a physical ORF.
            self.assertEqual(kwargs['coarse'],Resolution(4,8,8,16))
            self.assertEqual(kwargs['fine'],Resolution(6,12,12,24))
            return np.exp(-1j*(ya-yb)),reports
        p=fibonacci_directions(3);y=np.array([1.,2,3]);builder=self.builder()
        with patch('pta.geometry.checked_orf',side_effect=pair) as mock:
            result=builder(.8,y,p)
            np.testing.assert_allclose(result,result.conj().T)
            self.assertGreater(abs(result[0,1].imag),.5)
            result[0,0]=99 # The returned matrix cannot mutate the cache.
            cached=builder(.8,y.copy(),p.copy())
            self.assertAlmostEqual(cached[0,0],1)
            self.assertEqual(mock.call_count,6)
            with self.assertRaises(ValueError):builder(.80001,y,p)
            self.assertEqual(mock.call_count,6)
        self.assertEqual(builder.summary()['cache_hits'],1)
        self.assertEqual(builder.summary()['unique_pairs'],6)

    def test_domain_refusal_and_no_psd_repair(self):
        p=fibonacci_directions(2);builder=self.builder()
        with patch('pta.geometry.checked_orf') as pair:
            for beta,y in [(1.1,[1,2]),(.8,[1,MAX_VALIDATED_PHASE+1]),(.8,[1,-1])]:
                with self.assertRaises(ValueError):builder(beta,np.array(y),p)
            pair.assert_not_called()
        bad={'resources':{'work_units_proxy':80,'estimated_memory_bytes':500}}
        with patch('pta.geometry.checked_orf',return_value=(-1+0j,bad)):
            with self.assertRaises(ValueError):builder(.8,np.array([1.,2]),p)
        self.assertEqual(builder.summary()['unique_matrices'],0)

if __name__=='__main__':unittest.main(verbosity=2)
