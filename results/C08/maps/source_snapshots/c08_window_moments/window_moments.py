"""Proper-CN quadratic moments after a finite complex-linear frequency window.

Input Fourier channels are independent and already divided by sqrt(scale_k).
S acts on the physical coefficients. Arbitrary timing projections and improper
complex noise are outside this API. No ORF, likelihood or inference is called.
"""
import numpy as np


def estimated_numeric_bytes(k,p,d):
    # Caller logical inputs; covariance blocks/output; conservative contraction,
    # eigenvalue, finite/Hermitian-check and reduction temporaries. BLAS allocator
    # retention/Python overhead are not an RSS bound.
    return int(16*(k*p*p+d*p*p+k*k)+8*(2*k)+
               8*(6*k*k*p*p+8*d*p*p+4*k*k*d*d+8*k*d+8*d*d+4*k*k))


def _array(value,shape,name,kind):
    if not isinstance(value,np.ndarray) or value.shape!=shape or value.dtype not in kind:
        raise TypeError(name+' requires an existing float64/complex128 ndarray with exact shape')
    if not np.isfinite(value).all():
        raise ValueError(name+' must be finite')
    return value


def _hermitian(a,name):
    scale=np.maximum(np.max(abs(a),axis=(-2,-1)),np.finfo(float).tiny)
    error=np.max(abs(a-a.swapaxes(-2,-1).conj()),axis=(-2,-1))/scale
    if np.any(error>1e-11):raise ValueError(name+' is not Hermitian within declared roundoff')
    return float(np.max(error))


def _real_trace(a,name):
    scale=max(float(np.max(abs(a))),np.finfo(float).tiny)
    if np.max(abs(a.imag))>1e-11*scale:
        raise FloatingPointError(name+' has a nonreal residual above roundoff')
    return a.real


def window_moments(covariance,estimators,scales,physical_operator,weights,*,
                   maximum_numeric_bytes=64*1024**2):
    """Return full frequency covariance and W compression, preserving cross terms.

    C[K,P,P] and H[D,P,P] must already be ndarray objects. The budget is checked
    from shape metadata before scanning values or allocating numeric buffers.
    Arrays in the return value are owned, read-only products; inputs are intact.
    """
    if not isinstance(covariance,np.ndarray) or covariance.ndim!=3:
        raise TypeError('covariance must be an existing rank3 ndarray')
    if not isinstance(estimators,np.ndarray) or estimators.ndim!=3:
        raise TypeError('estimators must be an existing rank3 ndarray')
    k,p,p2=covariance.shape;d,hp,hp2=estimators.shape
    if not 1<=k<=8 or not 1<=p<=16 or not 1<=d<=16 or (p2,hp,hp2)!=(p,p,p):
        raise ValueError('Supported finite block dimensions are K<=8,P<=16,D<=16')
    if type(maximum_numeric_bytes) is not int or maximum_numeric_bytes<1:
        raise TypeError('Explicit positive integer memory limit required')
    estimate=estimated_numeric_bytes(k,p,d)
    if estimate>maximum_numeric_bytes:raise MemoryError('Window moment estimate exceeds the numeric budget')
    complex_types=(np.dtype('float64'),np.dtype('complex128'))
    c=_array(covariance,(k,p,p),'covariance',complex_types)
    h=_array(estimators,(d,p,p),'estimators',complex_types)
    s=_array(scales,(k,),'scales',(np.dtype('float64'),))
    op=_array(physical_operator,(k,k),'physical_operator',complex_types)
    w=_array(weights,(k,),'weights',(np.dtype('float64'),))
    if np.any(s<=0):raise ValueError('Positive fixed Fourier scales required')
    c_herm=_hermitian(c,'covariance');h_herm=_hermitian(h,'estimators')
    np.linalg.cholesky(c)  # Positive intrinsic/white noise; no repair/jitter.
    with np.errstate(over='raise',invalid='raise',divide='raise'):
        normalized=op*np.sqrt(s[None,:]/s[:,None])
        blocks=np.einsum('kn,ln,nab->klab',normalized,normalized.conj(),c,optimize=False)
        mu=np.empty((k,d));sigma=np.empty((k*d,k*d))
        for a in range(k):
            mu[a]=_real_trace(np.trace(h@blocks[a,a],axis1=-2,axis2=-1),'mean')
            for b in range(k):
                hc=h@blocks[a,b];hr=h@blocks[b,a]
                value=np.einsum('iab,jba->ij',hc,hr,optimize=False)
                sigma[a*d:(a+1)*d,b*d:(b+1)*d]=_real_trace(value,'quadratic covariance')
        if not np.isfinite(mu).all() or not np.isfinite(sigma).all():
            raise FloatingPointError('Nonfinite transformed moments')
        relative_symmetry=_hermitian(sigma,'quadratic covariance')
        cm=np.einsum('k,kd->d',w,mu)
        cs=np.einsum('k,l,kilj->ij',w,w,sigma.reshape(k,d,k,d),optimize=False)
        # All transformations are proper complex linear. Finite roundoff can
        # yield tiny negative eigenvalues for deliberately singular S or H;
        # record them and reject material negativity without clipping.
        eig=np.linalg.eigvalsh(sigma)
        norm=max(float(np.max(abs(sigma))),np.finfo(float).tiny)
        if eig.min() < -1e-11*norm:
            raise FloatingPointError('Quadratic covariance has a material negative eigenvalue')
    outputs=dict(mean_by_frequency=mu,covariance_full=sigma,compressed_mean=cm,
                 compressed_covariance=cs,normalized_operator=normalized,covariance_blocks=blocks)
    for a in outputs.values():a.flags.writeable=False
    outputs['diagnostics']=dict(estimated_numeric_bytes=estimate,
        input_covariance_relative_hermiticity=c_herm,estimators_relative_hermiticity=h_herm,
        output_covariance_relative_symmetry=relative_symmetry,
        minimum_quadratic_covariance_eigenvalue=float(eig.min()),
        pseudocovariance_assumed_zero=True,cross_frequency_covariance_retained=True,
        no_jitter_clipping_or_covariance_diagonalization=True,
        scope='ALGEBRA_ONLY_NOT_ORF_OR_POSTERIOR_VALIDATION')
    return outputs
