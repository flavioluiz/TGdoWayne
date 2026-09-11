"""High-precision direct t integrals resolve roundoff in the extreme-tail reference."""
from pathlib import Path
from time import perf_counter
import json
import mpmath as mp
import numpy as np
import sys
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
OUTPUT = REPO / "results/C07/validation"
OUTPUT.mkdir(parents=True, exist_ok=True)

from inference.scale_gaussian import gaussian_log_scale_integral

ROOT=OUTPUT


def reference(chi,b,c,ld,d,lo,hi):
    with mp.workdps(70):
        chi,b,c,ld,d,lo,hi=map(mp.mpf,[str(v) for v in (chi,b,c,ld,d,lo,hi)])
        ln10=mp.log(10);v=(b+mp.sqrt(b*b+4*d*chi))/(2*chi)
        mode=min(hi,max(lo,-mp.log(v)/(2*ln10)))
        def ll(t):
            s=mp.power(10,t)
            return -(chi/s**4-2*b/s**2+c+ld+d*mp.log(2*mp.pi))/2-2*d*mp.log(s)
        peak=ll(mode);v=mp.power(10,-2*mode)
        slope=2*ln10*(-d+chi*v*v-b*v);curve=4*ln10**2*(b*v-2*chi*v*v)
        width=1/max(abs(slope),mp.sqrt(abs(curve)),mp.mpf(1))
        edges=sorted(set([lo,hi]+[min(hi,max(lo,mode+width*j)) for j in [-256,-64,-16,-8,-4,-2,-1,0,1,2,4,8,16,64,256]]))
        val=mp.fsum(mp.quad(lambda t:mp.exp(ll(t)-peak),[a,z]) for a,z in zip(edges[:-1],edges[1:]))
        return float(peak+mp.log(val)-mp.log(hi-lo))


def main():
    start=perf_counter();records=[]
    for d in [1,10,40]:
        for rho in [-.9,.9]:
            chi=1e8;c=15.;b=rho*np.sqrt(chi*c);ld=-.7
            for lo,hi in [(-np.log10(2),np.log10(2)),(-.25,-.24999999)]:
                ref=reference(chi,b,c,ld,d,lo,hi)
                got=gaussian_log_scale_integral(chi,b,c,ld,d,lo,hi,coarse_order=32,fine_order=64)
                error=float(got-ref)
                assert abs(error)<5e-7,(d,rho,lo,hi,error)
                records.append(dict(dimension=d,rho=rho,low=lo,high=hi,log_value=float(got),reference_log_value=ref,absolute_log_error=error))
    output=dict(status='PASS_high_precision_tail_reference',decimal_digits=70,seconds=perf_counter()-start,maximum_abs_log_error=max(abs(r['absolute_log_error']) for r in records),records=records,scope='Extreme tails have log densities near -5e8; the tolerance includes double-precision final representation.')
    (ROOT/'validation_high_precision.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({k:v for k,v in output.items() if k!='records'},indent=2))


if __name__=='__main__':main()
