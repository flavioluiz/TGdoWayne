"""Travelling tensor-wave kinematics and finite pulsar transfer.

beta=c*k/(2*pi*f)=v_group/c; y=2*pi*f*L/c. Fourier phase is
exp(+2*pi*i*f*(t-beta*Omega.x/c)), conjugate to chapter C04.
For (+---), the geometric positive kernel is the fractional frequency gain;
the usual redshift z=(nu_P-nu_E)/nu_P uses its negative. This common sign
cancels in the ORF. These routines do not model f<fg evanescence.
"""
import numpy as np

from ._domain import phase, real_array, real_scalar


def beta_from_frequency(f, fg):
    f, fg = real_scalar(f, 'f'), real_scalar(fg, 'fg')
    if f <= 0 or fg < 0:
        raise ValueError('Require f>0 and fg>=0.')
    if f < fg:
        raise ValueError('Evanescent frequency is outside travelling-wave model.')
    # Factorization preserves the audited threshold behavior.
    return np.sqrt(((f-fg)/f)*(1+fg/f))


def transfer(y, d):
    """Stable (1-exp(-i*y*d))/d, with value i*y at d=0.

    y is a nonnegative real scalar; d is a finite real scalar/array.
    A finite result does not certify the resolution of a subsequent integral.
    """
    y, d = phase(y), real_array(d, 'd')
    with np.errstate(over='ignore', invalid='ignore'):
        argument = y*d
    if not np.all(np.isfinite(argument)):
        raise ValueError('y*d exceeds the finite phase range of float arithmetic.')
    return 1j*y*np.exp(-0.5j*y*d)*np.sinc(y*d/(2*np.pi))
