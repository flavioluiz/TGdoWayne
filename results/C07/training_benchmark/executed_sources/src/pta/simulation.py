"""Physical Fourier simulation under a declared periodic, band-limited PTA experiment.

C(f) is a one-sided timing-residual PSD [s^3], and q=sqrt(2T)*a [s^(3/2)].
No timing fit/window, posterior, or observational inference is implicit here.
The ORF is supplied by an explicit matrix-builder callback; no silent raw fallback.
"""
from dataclasses import dataclass
from typing import Callable
import numpy as np
from .statistics import quadratic_moments,quadratic_statistics

JULIAN_YEAR_SECONDS=365.25*86400
LIGHT_SPEED_M_S=299792458.0
LIGHT_YEAR_METERS=LIGHT_SPEED_M_S*JULIAN_YEAR_SECONDS


@dataclass(frozen=True)
class SpectralParameters:
    log10_gw_amplitude: float
    gw_slope: float
    log10_red_amplitude: float
    red_slope: float
    white_efac: float


def _positive_vector(value,name):
    a=np.asarray(value,dtype=float)
    if a.ndim!=1 or not len(a) or not np.isfinite(a).all() or np.any(a<=0):raise ValueError(f'{name} must be a nonempty positive finite vector.')
    return a


def _scalar(value,name,*,positive=False,nonnegative=False):
    if isinstance(value,(bool,np.bool_,complex,np.complexfloating)) or np.ndim(value)!=0:raise ValueError(f'{name} must be a real scalar.')
    try:x=float(value)
    except (TypeError,ValueError,OverflowError) as exc:raise ValueError(f'{name} must be a real scalar.') from exc
    if not np.isfinite(x) or (positive and x<=0) or (nonnegative and x<0):raise ValueError(f'Invalid {name}.')
    return x


def velocity_ratio(frequency_hz,mass_frequency_hz):
    f=_scalar(frequency_hz,'frequency_hz',positive=True)
    fg=_scalar(mass_frequency_hz,'mass_frequency_hz',nonnegative=True)
    if f<fg:raise ValueError('Evanescent channel outside this travelling-wave experiment; retain data under a separately specified cutoff model.')
    return float(np.sqrt(((f-fg)/f)*(1+fg/f)))


def orf_stack(frequencies_hz,mass_frequency_hz,directions,distances_m,*,matrix_builder:Callable,
              model='dispersive',reference_frequency_hz=None):
    """Build physical, C_full, or C_beta ORFs through builder(beta,phases,directions).

    The callback must return a Hermitian PSD matrix and enforce its numerical
    budget/convergence. Its audit metadata should be retained by the caller.
    """
    f=_positive_vector(frequencies_hz,'frequencies_hz');distance=_positive_vector(distances_m,'distances_m')
    p=np.asarray(directions,dtype=float)
    if p.shape!=(len(distance),3) or not np.isfinite(p).all() or not np.allclose(np.linalg.norm(p,axis=1),1,atol=1e-12,rtol=0):raise ValueError('Finite unit pulsar directions matching distances required.')
    if model not in {'dispersive','C_full','C_beta'}:raise ValueError('Choose dispersive, C_full, or C_beta explicitly.')
    fg=_scalar(mass_frequency_hz,'mass_frequency_hz',nonnegative=True)
    # All observed channels remain present. No approximation may silently change support.
    for ff in f:velocity_ratio(ff,fg)
    if model!='dispersive':
        ref=_scalar(reference_frequency_hz,'reference_frequency_hz',positive=True)
        beta_ref=velocity_ratio(ref,fg)
    result=[]
    for ff in f:
        beta=velocity_ratio(ff,fg) if model=='dispersive' else beta_ref
        phase_f=ref if model=='C_full' else ff
        phases=2*np.pi*phase_f*distance/LIGHT_SPEED_M_S
        gamma=np.asarray(matrix_builder(beta,phases,p),dtype=np.complex128)
        if gamma.shape!=(len(p),len(p)) or not np.isfinite(gamma).all():raise ValueError('ORF builder returned an invalid shape/value.')
        scale=max(float(np.linalg.norm(gamma,2)),np.finfo(float).tiny)
        if np.max(abs(gamma-gamma.conj().T))>1e-10*scale:raise ValueError('ORF builder returned a non-Hermitian matrix.')
        # Averaging only removes tolerated roundoff; no eigenvalue clipping or mass-dependent normalization.
        gamma=(gamma+gamma.conj().T)/2
        if np.linalg.eigvalsh(gamma).min() < -1e-10*scale:raise ValueError('ORF builder returned a non-positive-semidefinite matrix.')
        result.append(gamma)
    return np.array(result)


def residual_power_spectrum(frequencies_hz,log10_amplitude,slope,*,pivot_hz=1/JULIAN_YEAR_SECONDS):
    f=_positive_vector(frequencies_hz,'frequencies_hz');pivot=_scalar(pivot_hz,'pivot_hz',positive=True)
    gamma=_scalar(slope,'slope')
    loga=float(log10_amplitude)
    if not np.isfinite(loga) and loga!=-np.inf:raise ValueError('Amplitude logarithm must be finite or -inf for zero signal.')
    amplitude2=0.0 if loga==-np.inf else 10.0**(2*loga)
    psd=amplitude2/(12*np.pi*np.pi*pivot**3)*(f/pivot)**(-gamma)
    if not np.isfinite(psd).all():raise ValueError('Power spectrum overflowed.')
    return psd


def residual_covariances(frequencies_hz,gamma,nominal_toa_sigma_seconds,red_amplitude_pattern,
                          cadence_seconds,parameters:SpectralParameters):
    """S_gw Gamma + diagonal intrinsic red and white PSDs; no noise truth in bin weights."""
    f=_positive_vector(frequencies_hz,'frequencies_hz')
    sigma=_positive_vector(nominal_toa_sigma_seconds,'nominal_toa_sigma_seconds')
    red=np.asarray(red_amplitude_pattern,dtype=float)
    if red.shape!=sigma.shape or not np.isfinite(red).all() or np.any(red<0):raise ValueError('Nonnegative finite red-amplitude pattern required.')
    dt=_scalar(cadence_seconds,'cadence_seconds',positive=True)
    efac=_scalar(parameters.white_efac,'white_efac',positive=True)
    g=np.asarray(gamma,dtype=complex)
    if g.shape!=(len(f),len(sigma),len(sigma)) or not np.isfinite(g).all():raise ValueError('ORF shape must be (frequency,pulsar,pulsar).')
    if not np.allclose(g,g.swapaxes(-1,-2).conj(),rtol=1e-11,atol=1e-14):raise ValueError('Non-Hermitian ORF.')
    scale=np.maximum(np.linalg.norm(g,axis=(-2,-1)),np.finfo(float).tiny)
    if np.any(np.linalg.eigvalsh(g).min(axis=-1)<-1e-10*scale):raise ValueError('ORF is not positive semidefinite.')
    sg=residual_power_spectrum(f,parameters.log10_gw_amplitude,parameters.gw_slope)
    sr=residual_power_spectrum(f,parameters.log10_red_amplitude,parameters.red_slope)
    c=sg[:,None,None]*g
    index=np.arange(len(sigma))
    c[:,index,index]+=sr[:,None]*red[None,:]**2+2*(efac*sigma[None,:])**2*dt
    if not np.allclose(c,c.swapaxes(-1,-2).conj(),rtol=1e-11,atol=0):raise ValueError('Non-Hermitian spectral covariance.')
    np.linalg.cholesky(c) # Reject an invalid covariance, do not repair it by clipping.
    return c


def normalize_spectra(covariance,fixed_scale_psd):
    c=np.asarray(covariance,dtype=complex);scale=_positive_vector(fixed_scale_psd,'fixed_scale_psd')
    if c.ndim!=3 or c.shape[0]!=len(scale) or c.shape[1]!=c.shape[2]:raise ValueError('Expected C(frequency,pulsar,pulsar).')
    return c/scale[:,None,None]


def draw_proper_complex(covariance,count,rng):
    c=np.asarray(covariance,dtype=complex)
    if c.ndim<2 or c.shape[-1]!=c.shape[-2] or not np.isfinite(c).all():raise ValueError('Finite square covariance required.')
    if not np.allclose(c,c.swapaxes(-1,-2).conj(),atol=0,rtol=1e-11):raise ValueError('Hermitian covariance required.')
    if isinstance(count,bool) or not isinstance(count,(int,np.integer)) or count<1:raise ValueError('Positive integer count required.')
    if not isinstance(rng,np.random.Generator):raise TypeError('Pass an explicit numpy Generator.')
    factor=np.linalg.cholesky(c)
    z=(rng.standard_normal((count,*c.shape[:-1]))+1j*rng.standard_normal((count,*c.shape[:-1])))/np.sqrt(2)
    return np.einsum('...ij,r...j->r...i',factor,z,optimize=True)


def paired_physical_and_gaussian(covariance,matrices,count,rng):
    """CN physical statistics and a Gaussian moment-matched control with shared latent draws.

    The normal control is a distinct experiment, NOT the exact quadratic likelihood.
    A/B/C should each receive the same physical realization (or the same control realization).
    """
    c=np.asarray(covariance,dtype=complex);h=np.asarray(matrices,dtype=complex)
    # Reuse explicit standard normals: each marginal remains exactly specified.
    z=draw_proper_complex(np.broadcast_to(np.eye(c.shape[-1]),c.shape),count,rng)
    factor=np.linalg.cholesky(c)
    q=np.einsum('...ij,r...j->r...i',factor,z,optimize=True)
    physical=quadratic_statistics(q,h)
    mu,sigma=quadratic_moments(c,h)
    v=np.concatenate((np.sqrt(2)*z.real,np.sqrt(2)*z.imag),axis=-1)
    if h.shape[0]>v.shape[-1]:
        extra=rng.standard_normal((*v.shape[:-1],h.shape[0]-v.shape[-1]))
        v=np.concatenate((v,extra),axis=-1)
    control=mu+np.einsum('...ij,r...j->r...i',np.linalg.cholesky(sigma),v[...,:h.shape[0]],optimize=True)
    return q,physical,control


def real_periodic_series(fourier_coefficients,times_seconds,duration_seconds):
    """r(t)=sqrt(2/T) Re sum_n q_n exp(i2pi*n*t/T), frequencies n=1..K.

    Input q must carry physical PSD normalization, not dimensionless normalized units.
    This reconstructs only the supplied band; it does not add higher white-noise modes.
    """
    q=np.asarray(fourier_coefficients,dtype=complex);t=np.asarray(times_seconds,dtype=float)
    T=_scalar(duration_seconds,'duration_seconds',positive=True)
    if q.ndim<2 or t.ndim!=1 or not np.isfinite(q).all() or not np.isfinite(t).all():raise ValueError('Finite coefficients (...,K,Np) and times required.')
    basis=np.exp(2j*np.pi*np.outer(t/T,np.arange(1,q.shape[-2]+1)))
    return np.sqrt(2/T)*np.einsum('tk,...ka->...ta',basis,q,optimize=True).real
