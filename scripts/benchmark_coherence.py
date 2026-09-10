import json
from pathlib import Path
from time import perf_counter
from scipy.optimize import brentq
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



def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / 'coherence_results.json').write_text(json.dumps({'status':'in_progress','rows':[]}, indent=2)+'\n')
    rows=[]
    y=2*np.pi*1000.125
    for beta in [0.9,1]:
        for angle in [0,1e-5,1e-3,1e-2]:
            for yb in [y,y+1]:
                d=float(np.cos(angle))
                lmax=int(beta*yb+100)
                nh=int(2*beta*yb+220)
                nm=int(1.2*beta*yb+130)
                np_=max(240,int(2.4*beta*yb*np.sin(angle)+240))
                t=perf_counter()
                h,_=harmonic_orf(beta,d,y,yb,lmax=lmax,nmu=nh)
                direct=direct_orf(beta,d,y,yb,nmu=nm,nphi=np_)
                hr,_=harmonic_orf(beta,d,y,yb,lmax=lmax+50,nmu=nh+100)
                row={'beta':beta,'fL_a_over_c':y/(2*np.pi),'fL_b_over_c':yb/(2*np.pi),
                    'angle':angle,'full_real':h.real,'full_imag':h.imag,
                    'earth_only':earth_analytic(beta,d),
                    'abs_direct_harmonic':float(abs(direct-hr)),
                    'harmonic_refinement':float(abs(h-hr)),'seconds':perf_counter()-t}
                rows.append(row)
                print(f"beta={beta} angle={angle:g} delta_y={yb-y:g} error={abs(direct-hr):.3g}",flush=True)
    roots=[brentq(lambda z:hellings_downs(np.cos(z)),0,np.pi/2),
           brentq(lambda z:hellings_downs(np.cos(z)),np.pi/2,np.pi)]
    zero_checks=[]
    for angle in roots:
        d=float(np.cos(angle));direct=direct_orf(1,d,nmu=720,nphi=1440)
        zero_checks.append({'angle_radians':angle,'angle_degrees':np.degrees(angle),
                            'earth_direct':direct.real,'absolute_error_at_HD_zero':float(abs(direct))})
    passed = (max(r['abs_direct_harmonic'] for r in rows)<1e-5
              and max(r['absolute_error_at_HD_zero'] for r in zero_checks)<1e-5)
    (OUTPUT_DIR / 'coherence_results.json').write_text(json.dumps({
        'status':'PASS' if passed else 'FAIL','near_coincidence':rows,'HD_zeros':zero_checks},indent=2,allow_nan=False)+'\n')

    if not passed:
        raise RuntimeError('Coherence or HD-zero absolute acceptance exceeded.')

if __name__ == '__main__':
    main()
