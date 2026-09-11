"""C1 local clamped replacement, preserving every outside polynomial bit exactly."""
import numpy as np
from scipy.interpolate import CubicSpline

def coordinate(u):
 u=np.asarray(u,dtype=float);return -np.sqrt((1-u)*(1+u))

def stitch(old_nodes,old_gamma,old_coeff,patch_nodes,patch_gamma):
 n=np.asarray(old_nodes);g=np.asarray(old_gamma);c=np.asarray(old_coeff);p=np.asarray(patch_nodes);v=np.asarray(patch_gamma)
 if n.ndim!=1 or p.ndim!=1 or c.dtype.kind not in 'fc' or g.dtype.kind not in 'fc' or v.dtype.kind not in 'fc':raise ValueError('Floating matrix curves required')
 if c.shape!=(len(n)-1,4,*g.shape[1:]) or v.shape!=(len(p),*g.shape[1:]):raise ValueError('Shape mismatch')
 if not all(np.isfinite(a).all() for a in [n,g,c,p,v]):raise ValueError('Nonfinite curve')
 x=coordinate(n);z=coordinate(p)
 if np.any(np.diff(x)<=0) or np.any(np.diff(z)<=0) or p[-1]!=n[-1]:raise ValueError('Strict transformed knots/endpoints required')
 j=int(np.searchsorted(n,p[0]))
 if j<1 or j>=len(n)-1 or n[j]!=p[0] or not np.isin(n[j:],p).all():raise ValueError('Patch must retain old nodes and an interior join')
 at=np.searchsorted(p,n[j:])
 if not np.array_equal(v[at],g[j:]):raise ValueError('Old node matrices must remain bit exact')
 derivative=(c[j-1,1]+2*c[j-1,2]+3*c[j-1,3])/(x[j]-x[j-1])
 spline=CubicSpline(z,v,bc_type=((1,derivative),(1,np.zeros_like(derivative))))
 width=np.diff(z).reshape((-1,)+(1,)*(g.ndim-1));local=np.stack([spline.c[3-i]*width**i for i in range(4)],axis=1)
 nodes=np.r_[n[:j],p];gamma=np.concatenate([g[:j],v]);coeff=np.concatenate([c[:j],local])
 if not np.array_equal(coeff[:j],c[:j]) or not np.array_equal(gamma[np.searchsorted(nodes,n)],g):raise RuntimeError('Exact inheritance failed')
 left=c[j-1].sum(axis=0);right=local[0,0];right_d=local[0,1]/(z[1]-z[0]);last_d=(local[-1,1]+2*local[-1,2]+3*local[-1,3])/(z[-1]-z[-2])
 checks=dict(join_index=j,join_u=float(p[0]),join_effective_beta=float(-z[0]),outside_coefficients_bitexact=True,old_node_matrices_bitexact=True,C0_join_error=float(np.max(abs(left-right))),C1_join_error=float(np.max(abs(derivative-right_d))),threshold_derivative_error=float(np.max(abs(last_d))),automatic_fallback=False)
 if checks['C0_join_error']>1e-11 or checks['C1_join_error']>1e-7 or checks['threshold_derivative_error']>1e-7:raise ValueError('Clamped boundary gate failed')
 return nodes,gamma,coeff,checks
