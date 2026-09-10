"""Portable C06 contracts; the campaign script separately checks the physical ORF backend."""
import unittest
import numpy as np
from pta.simulation import (JULIAN_YEAR_SECONDS,LIGHT_SPEED_M_S,SpectralParameters,
    velocity_ratio,orf_stack,residual_covariances,draw_proper_complex,
    paired_physical_and_gaussian,real_periodic_series)
from pta.statistics import (quadratic_moments,quadratic_statistics,
    standardized_cumulants,angular_estimators,compress_frequencies,
    compress_independent_moments,compress_full_moments,proper_complex_real_covariance)

class SimulatorContracts(unittest.TestCase):
    def test_white_psd_units_and_real_fourier_roundtrip(self):
        n=31;dt=14*86400.;T=n*dt;nm=15;sigma=np.array([100,300])*1e-9
        f=np.arange(1,nm+1)/T
        gamma=np.array([np.eye(2)]*nm)
        pars=SpectralParameters(-np.inf,4,-np.inf,4,1)
        c=residual_covariances(f,gamma,sigma,np.ones(2),dt,pars)
        np.testing.assert_allclose(c,np.array([np.diag(2*sigma*sigma*dt)]*nm))
        q=draw_proper_complex(c,3,np.random.default_rng(818))
        series=real_periodic_series(q,np.arange(n)*dt,T)
        recovered=np.sqrt(2*T)*np.fft.fft(series,axis=1)[:,1:nm+1,:]/n
        np.testing.assert_allclose(recovered,q,atol=1e-15,rtol=1e-12)

    def test_frequency_reference_changes_explicit_components(self):
        p=np.array([[0.,0,1],[1.,0,0]])
        distance=LIGHT_SPEED_M_S*np.array([.12,.2])
        calls=[]
        # Synthetic PSD callback tests argument semantics, not an astrophysical ORF.
        def builder(beta,phases,directions):
            calls.append((beta,phases.copy()))
            v=(1+beta*directions[:,0])*np.exp(-1j*phases)
            return np.eye(2)+v[:,None]*v[None,:].conj()
        f=np.array([1.,2.])
        physical=orf_stack(f,.5,p,distance,matrix_builder=builder)
        full=orf_stack(f,.5,p,distance,matrix_builder=builder,model='C_full',reference_frequency_hz=1)
        beta=orf_stack(f,.5,p,distance,matrix_builder=builder,model='C_beta',reference_frequency_hz=1)
        np.testing.assert_allclose(full[0],full[1])
        self.assertNotAlmostEqual(np.max(abs(beta[0]-beta[1])),0)
        self.assertNotAlmostEqual(np.max(abs(physical[1]-beta[1])),0)
        physical0=orf_stack(f,0,p,distance,matrix_builder=builder)
        beta0=orf_stack(f,0,p,distance,matrix_builder=builder,model='C_beta',reference_frequency_hz=1)
        np.testing.assert_array_equal(physical0,beta0)
        with self.assertRaises(ValueError):orf_stack([.4,2],.5,p,distance,matrix_builder=builder,model='C_full',reference_frequency_hz=2)
        self.assertEqual(velocity_ratio(1,1),0)
        self.assertEqual(velocity_ratio(1e-300,0),1)

    def test_physical_and_gaussian_control_share_draws_but_not_distribution(self):
        c=np.array([np.eye(2,dtype=complex)])
        h=np.array([np.diag([1.,0])])
        q,y,g=paired_physical_and_gaussian(c,h,120000,np.random.default_rng(9921))
        self.assertTrue((y>=0).all())
        self.assertTrue((g<0).any())
        self.assertLess(abs(y.mean()-1),.015);self.assertLess(abs(g.mean()-1),.015)
        self.assertLess(abs(y.var()-1),.025);self.assertLess(abs(g.var()-1),.025)
        np.testing.assert_allclose(y,quadratic_statistics(q,h))
        self.assertEqual(standardized_cumulants(c[0],h[0])['excess_kurtosis'],6)

    def test_reject_unphysical_orf_and_covariance(self):
        p=np.array([[0.,0,1],[1.,0,0]])
        with self.assertRaises(ValueError):orf_stack([1],0,p,[1,2],matrix_builder=lambda *args:-np.eye(2))
        with self.assertRaises(ValueError):draw_proper_complex(np.array([[1,2],[0,1]]),1,np.random.default_rng(1))

class StatisticIdentities(unittest.TestCase):
    def test_isserlis_covariance_independent_construction(self):
        rng=np.random.default_rng(504);b=rng.normal(size=(4,4))+1j*rng.normal(size=(4,4));c=b@b.conj().T+np.eye(4)
        pairs=[(0,1),(0,2),(2,3)];hs=[]
        for kind in [0,1]:
            for a,b in pairs:
                h=np.zeros((4,4),complex);h[a,b]=.5 if kind==0 else .5j;h[b,a]=h[a,b].conjugate();hs.append(h)
        k=np.array([[c[a,cc]*c[d,b] for cc,d in pairs] for a,b in pairs])
        j=np.array([[c[a,d]*c[cc,b] for cc,d in pairs] for a,b in pairs])
        alternative=.5*np.block([[(k+j).real,(j-k).imag],[(j+k).imag,(k-j).real]])
        mu,sigma=quadratic_moments(c,np.array(hs))
        np.testing.assert_allclose(sigma,alternative,atol=1e-13,rtol=1e-13)
        np.testing.assert_allclose(mu,np.r_[[c[a,b].real for a,b in pairs],[c[a,b].imag for a,b in pairs]])

    def test_operator_propagates_cross_frequency_covariance(self):
        mu=np.arange(6,dtype=float);a=np.arange(36,dtype=float).reshape(6,6);cov=a@a.T+np.eye(6)
        w=np.kron(np.array([[.2,.3,.5]]),np.eye(2))
        mb,sb=compress_full_moments(mu,cov,w)
        np.testing.assert_allclose(mb,w@mu);np.testing.assert_allclose(sb,w@cov@w.T)
        independent=np.array([np.eye(2)*(j+1) for j in range(3)])
        mb,vb=compress_independent_moments(mu.reshape(3,2),independent,[.2,.3,.5])
        np.testing.assert_allclose(vb,(.2**2+2*.3**2+3*.5**2)*np.eye(2))

    def test_real_covariance_keeps_pseudocovariance(self):
        c=np.array([[2,1j],[-1j,3]],complex);p=np.array([[.2,.1j],[.1j,.3]])
        real=proper_complex_real_covariance(c,p)
        self.assertGreater(np.linalg.eigvalsh(real).min(),0)
        rr,ii=real[:2,:2],real[2:,2:];ri,ir=real[:2,2:],real[2:,:2]
        np.testing.assert_allclose(rr+ii+1j*(ir-ri),c)
        np.testing.assert_allclose(rr-ii+1j*(ri+ir),p)

    def test_bins_are_fixed_and_imaginary_auto_is_not_added(self):
        p=np.array([[0.,0,1],[1.,0,0],[0.,1,0],[0.,0,-1]])
        sigma=np.array([1.,2,3,4])
        est=angular_estimators(p,sigma,cross_bins=2,auto_bins=2)
        self.assertEqual(est.matrices.shape,(6,4,4))
        np.testing.assert_array_equal(est.matrices,angular_estimators(p,sigma,cross_bins=2,auto_bins=2).matrices)
        c=np.array([np.eye(4),2*np.eye(4)])
        mu,cov=quadratic_moments(c,est.matrices)
        self.assertGreater(np.linalg.eigvalsh(cov).min(),0)
        self.assertEqual(compress_frequencies(np.zeros((3,2,6)),[.5,.5]).shape,(3,6))

if __name__=='__main__':unittest.main(verbosity=2)
