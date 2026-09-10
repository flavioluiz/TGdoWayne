import json
from pathlib import Path
from time import perf_counter
import numpy as np
import scipy
from functools import partial
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from pta.orf import (raw_harmonic_orf as harmonic_orf,
                     raw_direct_orf as direct_orf, raw_auto_weighted,
                     earth_analytic, hellings_downs)

# Preserve the original adaptive reference configuration explicitly.
auto_weighted = partial(raw_auto_weighted, small_epsabs=1e-13,
                        small_epsrel=1e-12, oscillatory_epsabs=1e-12, limit=300)
OUTPUT_DIR = ROOT / 'results' / 'C05'


def record(v): return {'real':float(np.real(v)),'imag':float(np.imag(v))}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / 'benchmark_results.json').write_text(json.dumps({'status':'in_progress','rows':[]}, indent=2)+'\n')
    cases=[]
    for fL in [0.125,1.125,10.125,100.125]:
        for beta in [0,0.01,0.9,1]:
            cases.append((beta,fL,np.pi/8))
    # Large PTA-like light-travel baseline and both difficult limits.
    for beta in [0.00001,0.01,0.9,1]:
        cases.append((beta,1000.125,np.pi/8))
    rows=[]
    for beta,fL,angle in cases:
        y=2*np.pi*fL
        d=float(np.cos(angle))
        lmax=max(80,int(beta*y+90))
        nh=max(200,int(2*beta*y+190))
        nm=max(120,int(1.2*beta*y+120))
        np_=max(240,int(2.4*beta*y*np.sin(angle)+240))
        t=perf_counter()
        h,_=harmonic_orf(beta,d,y,y,lmax=lmax,nmu=nh)
        th=perf_counter()-t
        t=perf_counter()
        direct=direct_orf(beta,d,y,y,nmu=nm,nphi=np_)
        td=perf_counter()-t
        # A finer harmonic grid and multipole cutoff checks both sources of numerical error.
        t=perf_counter()
        hr,_=harmonic_orf(beta,d,y,y,lmax=lmax+50,nmu=nh+100)
        tr=perf_counter()-t
        earth=earth_analytic(beta,d)
        auto,aerr=auto_weighted(beta,y)
        row={'beta':beta,'fL_over_c':fL,'angle':angle,'harmonic':record(h),
            'direct':record(direct),'harmonic_refined':record(hr),
            'abs_direct_harmonic':float(abs(direct-hr)),'abs_harmonic_refinement':float(abs(h-hr)),
            'earth_only':earth,'full_minus_earth':float(h.real-earth),
            'auto_finite':auto,'auto_large_y':2*earth_analytic(beta,1),'auto_quad_error':aerr,
            'lmax':lmax,'nmu_harmonic':nh,'nmu_direct':nm,'nphi_direct':np_,
            'seconds':{'harmonic':th,'direct':td,'harmonic_refined':tr}}
        rows.append(row)
        print(f"beta={beta:g} fL={fL:g} direct-harmonic={abs(direct-hr):.3g} ref={abs(h-hr):.3g} time={th+td+tr:.3f}s",flush=True)
        (OUTPUT_DIR / 'benchmark_results.json').write_text(json.dumps({
            'status':'in_progress','numpy':np.__version__,'scipy':scipy.__version__,'rows':rows},indent=2,allow_nan=False)+'\n')
    maxerr=max(r['abs_direct_harmonic'] for r in rows)
    (OUTPUT_DIR / 'benchmark_results.json').write_text(json.dumps({
        'status':'PASS' if maxerr<1e-5 else 'FAIL','numpy':np.__version__,'scipy':scipy.__version__,
        'absolute_acceptance':1e-5,'maximum_abs_difference':maxerr,'rows':rows},indent=2,allow_nan=False)+'\n')
    if maxerr >= 1e-5:
        raise RuntimeError('Cross-method absolute acceptance exceeded.')

if __name__ == '__main__':
    main()
