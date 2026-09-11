"""Optional density broadening after a four-component fit; no new EM or data access."""
import numpy as np


def _real(value,name):
    raw=np.asarray(value)
    if raw.dtype.kind not in 'fiu' or not np.isfinite(raw).all():raise ValueError(name+' must be finite real numeric.')
    return np.array(raw,dtype=float,copy=True)


def _scalar(value,name):
    if isinstance(value,(bool,np.bool_)) or not np.isscalar(value) or np.iscomplexobj(value):raise ValueError(name+' must be a real scalar.')
    value=float(value)
    if not np.isfinite(value):raise ValueError(name+' must be finite.')
    return value


def broaden_gaussian_fit(weights,means,covariances,configuration,*,defensive_fraction=.15):
    """Return eight Gaussian components and transformation metadata, without mutation.

    The Gaussian weights returned here are CONDITIONAL on choosing the Gaussian
    part of the defensive proposal, exactly as GaussianDefensiveProposal expects.
    Student mean/covariance/df/scale are untouched outside this transformation.
    """
    if not isinstance(configuration,dict) or set(configuration)!={'wide_total_probability','variance_multiplier'}:
        raise ValueError('Explicit wide_total_probability and variance_multiplier required.')
    w,m,c=[_real(v,k) for v,k in ((weights,'weights'),(means,'means'),(covariances,'covariances'))]
    if m.ndim!=2 or m.shape[0]!=4 or m.shape[1]<1 or w.shape!=(4,) or c.shape!=(4,m.shape[1],m.shape[1]):
        raise ValueError('Exactly four fitted Gaussian components required.')
    if np.any(w<=0) or abs(w.sum()-1)>1e-14:raise ValueError('Positive fitted weights summing to one required; no silent repair.')
    if np.max(abs(c-c.swapaxes(-1,-2)))>1e-12*max(1.,float(np.max(abs(c)))):raise ValueError('Fitted covariances must be symmetric.')
    try:np.linalg.cholesky(c)
    except np.linalg.LinAlgError as error:raise ValueError('Fitted covariances must be positive definite.') from error
    alpha=_scalar(defensive_fraction,'defensive_fraction');wide=_scalar(configuration['wide_total_probability'],'wide_total_probability');multiplier=_scalar(configuration['variance_multiplier'],'variance_multiplier')
    if alpha!=.15:raise ValueError('This registered transformation preserves the0.15 defensive Student fraction.')
    if not 0<wide<1-alpha or multiplier<=1:raise ValueError('Require0<wide<0.85 and variance_multiplier>1.')
    narrow=1-alpha-wide;factor=narrow/(1-alpha)
    new_w=np.r_[factor*w,wide/(1-alpha)*w];new_m=np.concatenate([m,m]);new_c=np.concatenate([c,multiplier*c])
    if not np.isfinite(new_c).all():raise ValueError('Covariance broadening overflows; no clipping.')
    metadata=dict(method='duplicate_means_and_scale_covariances',fitted_gaussian_components=4,proposal_gaussian_components=8,
        narrow_total_probability=narrow,wide_total_probability=wide,defensive_student_probability=alpha,
        variance_multiplier=multiplier,pointwise_density_lower_bound_factor=factor,
        density_bound='q_new >= factor*q_old at every logit point; also in physical/unit coordinates after their common Jacobian',
        proof='q_new-factor*q_old = wide*p_wide + alpha*(1-factor)*p_Student >=0',
        requires_same_fitted_components_and_unchanged_student=True,no_new_fit=True)
    return new_w,new_m,new_c,metadata
