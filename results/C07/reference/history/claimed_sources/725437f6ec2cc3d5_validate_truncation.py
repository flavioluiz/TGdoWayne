"""Check truncated-box normalizations and a fully analytic likelihood control."""
import json,time
from dataclasses import replace
from pathlib import Path
import numpy as np
from scipy.special import roots_legendre
from cubature import HERE,LogAmplitudeBox,b_nodes,a_nodes,slope_nodes,digest

def transformed_polynomial(box,order=8):
    """Integrate 1,g,r,t,g²,r²,t²,g*r exactly in transformed coordinates."""
    volume=np.prod([hi-lo for lo,hi in [box.gw,box.red,box.efac]])
    result=np.zeros(8)
    for b,wb in zip(*b_nodes(box,order)):
        a,wa=a_nodes(box,b,order);lo,hi=box.conditional_bounds(a,b)
        if np.any(hi<=lo):raise ArithmeticError('Empty interior quadrature point.')
        I0=hi-lo;I1=.5*(hi**2-lo**2);I2=(hi**3-lo**3)/3
        terms=np.array([I0,a*I0+I1,b*I0+I1,I1,
                        a*a*I0+2*a*I1+I2,b*b*I0+2*b*I1+I2,I2,a*b*I0+(a+b)*I1+I2])
        result+=wb*(terms@wa)/volume
    mg,mr,mt=[np.mean(v) for v in [box.gw,box.red,box.efac]]
    vg,vr,vt=[np.ptp(v)**2/12 for v in [box.gw,box.red,box.efac]]
    expected=[1,mg,mr,mt,mg*mg+vg,mr*mr+vr,mt*mt+vt,mg*mr]
    return float(np.max(abs(result-expected)))

def exp_linear_integral(box,order=16):
    """L=exp(.13*g-.27*r+.7*t+.21*gamma), independent product-box reference.

    The t integral is analytic in transformed coordinates. The reference is the
    product of four elementary original-coordinate integrals, with no ratios.
    """
    ag,ar,at,az=.13,-.27,.7,.21;lam=ag+ar+at
    volume=np.prod([hi-lo for lo,hi in [box.gw,box.red,box.efac,box.slope]])
    zs,zw=slope_nodes(box,order);total=0.
    for b,wb in zip(*b_nodes(box,order)):
        a,wa=a_nodes(box,b,order);lo,hi=box.conditional_bounds(a,b)
        It=np.exp(lam*lo)*np.expm1(lam*(hi-lo))/lam
        total+=wb*np.sum(wa*np.exp(ag*a+ar*b)*It)*np.sum(zw*np.exp(az*zs))/volume
    ref=1.
    for coef,(lo,hi) in zip([ag,ar,at,az],[box.gw,box.red,box.efac,box.slope]):
        ref*=np.exp(coef*lo)*np.expm1(coef*(hi-lo))/(coef*(hi-lo))
    return total,ref

def main():
    start=time.perf_counter();full=LogAmplitudeBox();rng=np.random.default_rng(7110101);boxes=[full]
    for _ in range(40):
        updates={}
        for name in ['gw','red','efac','slope']:
            lo,hi=getattr(full,name);fraction=float(rng.uniform(.003,1.))
            updates[name]=(lo,lo+fraction*(hi-lo))
        boxes.append(replace(full,**updates))
    polynomial=[transformed_polynomial(b) for b in boxes]
    elementary=[exp_linear_integral(b) for b in boxes]
    maxrel=max(abs(v-r)/abs(r) for v,r in elementary)
    if max(polynomial)>2e-11 or maxrel>2e-12:raise AssertionError((max(polynomial),maxrel))
    # The ratio of a numerator's full-prior integral to the full evidence equals
    # the analytic exponential-family CDF in each original coordinate.
    z,_=exp_linear_integral(full);cdf_errors=[]
    for name,coef in [('gw',.13),('red',-.27),('efac',.7),('slope',.21)]:
        lo,hi=getattr(full,name)
        for fraction in [.003,.1,.4,.9,.999]:
            cut=lo+fraction*(hi-lo);small=replace(full,**{name:(lo,cut)})
            v,_=exp_linear_integral(small)
            cdf=v*fraction/z
            exact=np.expm1(coef*(cut-lo))/np.expm1(coef*(hi-lo))
            cdf_errors.append(abs(cdf-exact))
    if max(cdf_errors)>2e-12:raise AssertionError(max(cdf_errors))
    result=dict(status='PASS',random_seed=7110101,boxes=len(boxes),includes_widths_below_scale_width=True,
                polynomial_max_abs_error=max(polynomial),exponential_product_integral_max_relative_error=maxrel,
                exponential_original_coordinate_cdf_max_abs_error=max(cdf_errors),seconds=time.perf_counter()-start,
                source_hashes={str(p):digest(p) for p in [Path(__file__),HERE/'cubature.py',HERE/'truncated_cdf.py']})
    (HERE/'results/truncation_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
