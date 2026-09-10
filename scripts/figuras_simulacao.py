#!/usr/bin/env python3
"""C06: fresh paired Monte Carlo figure, using population standardization.

No samples are reused from the fixture and no negative Gaussian autos are clipped.
Histogram heights are counts/(N*bin_width), including out-of-window draws in N.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import scipy
from scipy.special import ndtr
from scipy.stats import kstat

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEED = 2026091066
DRAW_COUNT = 65536
AUTO_INDEX = 8
BLOCK_COUNT = 64
WINDOW = (-4., 7.)
BIN_COUNT = 88


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def histogram_record(samples, mean, variance, edges, physical):
    sigma = np.sqrt(variance)
    z = (samples-mean)/sigma
    counts, _ = np.histogram(z, bins=edges)
    widths = np.diff(edges)
    density = counts/(len(samples)*widths)
    below, above = int(np.count_nonzero(z < edges[0])), int(np.count_nonzero(z > edges[-1]))
    if int(counts.sum())+below+above != len(samples):
        raise ValueError('Histogram count bookkeeping failed.')
    cumulants = np.array([kstat(samples, n=order) for order in range(1,5)])
    standardized_cumulants = cumulants/np.array([sigma, variance, sigma**3, variance**2])
    standardized_cumulants[0] -= mean/sigma
    blocks = z.reshape(BLOCK_COUNT, -1)
    block_moments = np.array([np.mean(blocks**order, axis=1) for order in range(1,5)]).T
    moments = block_moments.mean(axis=0)
    mc_se = block_moments.std(axis=0, ddof=1)/np.sqrt(BLOCK_COUNT)
    negatives = int(np.count_nonzero(samples < 0))
    if physical and negatives:
        raise ValueError('A positive-semidefinite auto estimator unexpectedly became negative.')
    return {
        'draw_count': len(samples), 'counts': counts.tolist(), 'density': density.tolist(),
        'density_normalization': 'counts/(total_draw_count*bin_width), never conditional on plot window',
        'mass_inside_window': float(np.sum(density*widths)),
        'outside_window': {'below_count': below, 'above_count': above,
                           'total_fraction': (below+above)/len(samples)},
        'negative_auto_count': negatives, 'negative_auto_fraction': negatives/len(samples),
        'raw_range': [float(samples.min()), float(samples.max())],
        'standardized_range': [float(z.min()), float(z.max())],
        'estimated_raw_cumulants_k1_to_k4': cumulants.tolist(),
        'estimated_standardized_cumulants': standardized_cumulants.tolist(),
        'cumulant_estimator': 'Unbiased k-statistics; centering/scaling uses theoretical mu and sigma for the affine standardized variable.',
        'population_centered_standardized_moments_1_to_4': moments.tolist(),
        'population_centered_moment_mc_standard_errors': mc_se.tolist(),
        'population_centered_skewness_estimate': float(moments[2]),
        'population_centered_excess_kurtosis_estimate': float(moments[3]-3),
        'mc_error_estimation': f'{BLOCK_COUNT} independent postprocessing blocks; no generator changes or new draws for this estimate.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=SCRIPT_ROOT)
    parser.add_argument('--output-root', type=Path)
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    project = args.project_root.resolve()
    output = (args.output_root or project).resolve()
    sys.path.insert(0, str(project/'src'))
    from pta.simulation import paired_physical_and_gaussian
    from pta.statistics import (quadratic_moments, quadratic_cumulants,
                                compress_independent_moments, compress_frequencies)
    fixture = project/'results/C06/massive/fixture.npz'
    source_paths = ['src/pta/simulation.py', 'src/pta/statistics.py']
    source_hashes = {path: sha256(project/path) for path in source_paths}
    fixture_hash = sha256(fixture)
    with np.load(fixture, allow_pickle=False) as data:
        c = data['C_normalized_dispersive'].copy()
        h = data['estimator_matrices'].copy()
        weights = data['frequency_weights'].copy()
        frequencies = data['frequencies_hz'].copy()
    selected = h[AUTO_INDEX]
    if not np.allclose(selected, np.diag(np.diag(selected)), rtol=0, atol=1e-14):
        raise ValueError('Requested index is not an auto estimator.')
    if np.min(np.diag(selected).real) < 0 or np.any(weights < 0):
        raise ValueError('The declared auto support requires nonnegative diagonal and frequency weights.')
    mu_a, sigma_a = quadratic_moments(c,h)
    mu_b, sigma_b = compress_independent_moments(mu_a,sigma_a,weights)
    all_cumulants = np.array([quadratic_cumulants(channel,selected) for channel in c])
    compressed_cumulants = np.sum(all_cumulants*weights[:,None]**np.arange(1,5),axis=0)
    kappa = [all_cumulants[0], compressed_cumulants]
    means = [float(mu_a[0,AUTO_INDEX]),float(mu_b[AUTO_INDEX])]
    variances = [float(sigma_a[0,AUTO_INDEX,AUTO_INDEX]),float(sigma_b[AUTO_INDEX,AUTO_INDEX])]
    for k,m,v in zip(kappa,means,variances):
        np.testing.assert_allclose(k[:2],[m,v],rtol=1e-12,atol=0)
    rng = np.random.default_rng(args.seed)
    # One unchanged public-generator call. Saved realization arrays are deliberately unused.
    _, physical_a, normal_a = paired_physical_and_gaussian(c,h,DRAW_COUNT,rng)
    physical_b = compress_frequencies(physical_a,weights)
    normal_b = compress_frequencies(normal_a,weights)
    physical = [physical_a[:,0,AUTO_INDEX],physical_b[:,AUTO_INDEX]]
    control = [normal_a[:,0,AUTO_INDEX],normal_b[:,AUTO_INDEX]]
    edges = np.linspace(*WINDOW,BIN_COUNT+1)
    panels = []
    for label,k,m,v,p,g in zip(['A_first_channel','B_compressed'],kappa,means,variances,physical,control):
        theory = [0.,1.,float(k[2]/v**1.5),float(k[3]/v**2)]
        panels.append({
            'view': label, 'mean': m, 'variance': v, 'standardization': '(Y-theoretical_mean)/sqrt(theoretical_variance)',
            'physical_theory_raw_cumulants': k.tolist(),
            'physical_theory_standardized_cumulants': theory,
            'normal_theory_raw_cumulants': [m,v,0.,0.],
            'normal_theory_standardized_cumulants': [0.,1.,0.,0.],
            'physical_lower_support_standardized': -m/np.sqrt(v),
            'normal_theory_negative_auto_probability': float(ndtr(-m/np.sqrt(v))),
            'physical': histogram_record(p,m,v,edges,True),
            'normal_control': histogram_record(g,m,v,edges,False),
        })
    plt.rcParams.update({
        'font.family':'DejaVu Sans', 'font.size':9.3, 'axes.titlesize':10,
        'axes.labelsize':9.3, 'xtick.labelsize':8.5, 'ytick.labelsize':8.5,
        'axes.spines.top':False, 'axes.spines.right':False, 'pdf.fonttype':42,
    })
    fig, axes = plt.subplots(1,2,figsize=(7.0,3.35),sharex=True,sharey=True)
    fig.subplots_adjust(left=.085,right=.985,bottom=.24,top=.86,wspace=.12)
    titles = ['(a) A: primeiro canal','(b) B: compressão dos três canais']
    curve_x = np.linspace(*WINDOW,700)
    curve_y = np.exp(-curve_x**2/2)/np.sqrt(2*np.pi)
    for ax,panel,title in zip(axes,panels,titles):
        ax.stairs(panel['physical']['density'],edges,fill=True,alpha=.22,color='#0072B2',label='Físico: quadráticas CN')
        ax.stairs(panel['physical']['density'],edges,fill=False,linewidth=1.2,color='#0072B2')
        ax.stairs(panel['normal_control']['density'],edges,fill=False,linewidth=1.05,color='#D55E00',label='Controle normal')
        ax.plot(curve_x,curve_y,color='#444444',linestyle='--',linewidth=1.1,label=r'Normal $N(0,1)$')
        support=panel['physical_lower_support_standardized']
        ax.axvline(support,color='#777777',linestyle=':',linewidth=.9)
        ax.text(support+.08,.20,r'$Y=0$',rotation=90,ha='left',va='bottom',fontsize=8,color='#555555')
        skew,excess=panel['physical_theory_standardized_cumulants'][2:]
        annotation=f'Físico (teoria)\nAssimetria: {skew:.2f}\nExcesso: {excess:.2f}'.replace('.',',')
        ax.text(.98,.96,annotation,transform=ax.transAxes,ha='right',va='top',fontsize=8.3,
                bbox=dict(facecolor='white',alpha=.9,edgecolor='none',pad=2))
        ax.set(title=title,xlabel=r'$(Y-\mu)/\sigma$ (momentos teóricos)',xlim=WINDOW,ylim=(0,.56))
        ax.set_xticks([-4,-2,0,2,4,6])
        ax.grid(axis='y',alpha=.18,linewidth=.6)
    axes[0].set_ylabel('Densidade de probabilidade')
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.51,.025),ncol=3,frameon=False,fontsize=8.6)
    figure_dir=output/'figures/C06'
    figure_dir.mkdir(parents=True,exist_ok=True)
    pdf=figure_dir/'nao_normalidade.pdf'
    fig.savefig(pdf,metadata={'CreationDate':None,'ModDate':None,
        'Title':'C06: não normalidade de estimadores auto e compressão em frequência',
        'Author':'Projeto TGdoWayne'})
    plt.close(fig)
    final_source_hashes={path:sha256(project/path) for path in source_paths}
    if final_source_hashes!=source_hashes or sha256(fixture)!=fixture_hash:
        raise RuntimeError('Scientific sources or fixture changed during figure generation.')
    report={
        'status':'PASS','seed':args.seed,'rng_bit_generator':type(rng.bit_generator).__name__,
        'draw_count_per_experiment':DRAW_COUNT,'generator_call_count':1,
        'new_draws':'Fresh paired draws; no saved realization arrays from the fixture were used.',
        'bin_index_zero_based':AUTO_INDEX,'bin_label':'auto_0',
        'auto_pulsars_zero_based':np.flatnonzero(np.diag(selected).real).tolist(),
        'auto_weights':np.diag(selected).real.tolist(),
        'frequency_weights':weights.tolist(),'frequencies_hz':frequencies.tolist(),
        'fixture_path':'results/C06/massive/fixture.npz','fixture_sha256':fixture_hash,
        'source_sha256':source_hashes,'script_sha256':sha256(Path(__file__)),
        'versions':{'python':platform.python_version(),'numpy':np.__version__,
                    'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},
        'plot':{'window':list(WINDOW),'bin_edges':edges.tolist(),
                'histogram_rule':'counts/(65536*bin_width); all draws contribute to the denominator',
                'negative_gaussian_autos':'Preserved in standardization, moments and histogram counts; never clipped.',
                'pdf':'figures/C06/nao_normalidade.pdf','pdf_sha256':sha256(pdf)},
        'panels':panels,
        'interpretation':'One fixed massive synthetic configuration, no likelihood calibration or posterior inference. A and B use the same realizations and fixed weights; the paired normal control is a distinct experiment.',
    }
    destination=output/'results/C06/figure_summary.json'
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'pdf':str(pdf),'summary':str(destination),'seed':args.seed,
        'outside_window':{p['view']:{name:p[name]['outside_window']['total_fraction'] for name in ['physical','normal_control']} for p in panels},
        'negative_gaussian_autos':{p['view']:p['normal_control']['negative_auto_count'] for p in panels}},indent=2))


if __name__=='__main__':
    main()
