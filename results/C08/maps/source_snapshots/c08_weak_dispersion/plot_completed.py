"""Figures from the closed finite G2 and weak-dispersion summary, no physics."""
import os
os.environ.setdefault('MPLCONFIGDIR', 'tmp/matplotlib')
from pathlib import Path
import argparse
import csv
import hashlib
import json
import resource
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    with Path(path).open() as f:
        return list(csv.DictReader(f))


def save(fig, base):
    fig.savefig(base.with_suffix('.pdf'), metadata={'CreationDate': None, 'ModDate': None})
    fig.savefig(base.with_suffix('.svg'), metadata={'Date': None})
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--summary', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (29, 30))
    summary = json.loads((args.summary/'summary.json').read_text())
    if summary['status'] != 'PASS_READ_ONLY_SUMMARY_AND_INDEPENDENT_METRICS':
        raise ValueError('Closed reviewed summary required')
    rows = read(args.summary/'g2_envelopes.csv')
    weak = read(args.summary/'weak_envelopes.csv')
    if len(rows) != 24 or len(weak) != 12:
        raise ValueError('Complete envelope tables required')
    args.output.mkdir(parents=True, exist_ok=False)
    plt.rcParams.update({'font.size': 9, 'axes.titlesize': 10, 'axes.labelsize': 10,
                         'svg.fonttype': 'none', 'pdf.fonttype': 42})
    fig, axes = plt.subplots(3, 1, figsize=(6.3, 7.0), sharex=True, layout='constrained')
    pairs = [('B', 'C_beta', '#1f5b99', r'$B\to C_\beta$'),
             ('B', 'C_full', '#c35a20', r'$B\to C_{\rm full}$'),
             ('C_beta', 'C_full', '#488249', r'$C_\beta\to C_{\rm full}$')]
    metrics = [('KL', r'$D_{\rm KL}(p\Vert q)$'),
               ('mean_squared_in_p', r'$\sqrt{\Delta\mu^T\Sigma_p^{-1}\Delta\mu}$'),
               ('covariance_in_q', r'$\|\Sigma_q^{-1/2}(\Sigma_p-\Sigma_q)\Sigma_q^{-1/2}\|_F$')]
    for ax, (metric, label) in zip(axes, metrics):
        for p, q, color, legend in pairs:
            selection = [r for r in rows if r['p'] == p and r['q'] == q]
            x = np.array([float(r['u']) for r in selection])
            low = np.array([float(r[metric+'_min']) for r in selection])
            high = np.array([float(r[metric+'_max']) for r in selection])
            if metric == 'mean_squared_in_p':
                low, high = np.sqrt(low), np.sqrt(high)
            ax.fill_between(x, low, high, color=color, alpha=.12)
            ax.plot(x, high, 'o-', color=color, ms=3.5, lw=1.2, label=legend)
        ax.set_yscale('symlog', linthresh=1e-8)
        ax.set_ylabel(label)
        ax.grid(alpha=.2)
    axes[0].set_title('Oito massas, 16 vértices de parâmetros; T = 4,5 anos')
    axes[0].legend(loc='best', ncol=3, fontsize=8)
    axes[-1].set_xlabel(r'$u=f_gT$')
    axes[-1].set_xlim(-.015, 1.015)
    fig.supxlabel('Faixas: mínimo–máximo dos vértices. Linhas apenas ligam os pontos.', fontsize=8)
    save(fig, args.output/'g2_momentos')

    fig, axes = plt.subplots(1, 2, figsize=(6.3, 3.2), layout='constrained')
    names = [('Gamma', '#1f5b99', r'$\Gamma$'), ('C', '#c35a20', r'$C$'),
             ('mean', '#488249', r'$\mu_B$'), ('covariance', '#925e9f', r'$\Sigma_B$')]
    for name, color, label in names:
        selected = [r for r in weak if r['quantity'] == name]
        u = np.array([float(r['u']) for r in selected])
        low = np.array([float(r['relative_remainder_min']) for r in selected])
        high = np.array([float(r['relative_remainder_max']) for r in selected])
        axes[1].fill_between(u, low, high, color=color, alpha=.13)
        axes[1].loglog(u, high, 'o-', ms=4, color=color, label=label)
        if name == 'Gamma':
            absolute = np.array([float(r['absolute_remainder_max']) for r in selected])
            axes[0].loglog(u, absolute, 'o-', color=color, label='Resto calculado')
            axes[0].loglog(u, absolute[0]*(u/u[0])**4, '--', color='#777777', label=r'Guia $u^4$')
    axes[0].set_ylabel(r'$\|\Delta\Gamma-\Delta\Gamma^{(2)}\|_F$')
    axes[1].set_ylabel('Norma do resto / norma da diferença')
    for ax in axes:
        ax.set_xlabel(r'$u=f_gT$')
        ax.set_xticks([.001, .002, .004], labels=['0,001', '0,002', '0,004'])
        ax.minorticks_off()
        ax.grid(alpha=.2)
        ax.legend(fontsize=8, loc='best')
    fig.suptitle(r'Expansão de $C_\beta-B$ em massa pequena, fases fixas', fontsize=10)
    save(fig, args.output/'expansao_fraca')
    record = dict(status='FIGURES_FROM_COMPLETE_FINITE_RESULTS_PENDING_VISUAL_REVIEW',
        input_sha256={str(args.summary/f): sha(args.summary/f) for f in ['summary.json', 'g2_envelopes.csv', 'weak_envelopes.csv']},
        script_sha256=sha(__file__), outputs={p.name: sha(p) for p in args.output.iterdir()},
        CPU_seconds_including_imports=time.process_time(), RSS_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        ORF_evaluations=0, likelihood_evaluations=0,
        scope='Finite normal-moment comparisons and descriptive weak remainders, not posterior uncertainty.')
    if record['RSS_peak_bytes'] > 256*1024**2:
        raise MemoryError('Figure rendering memory allowance')
    with (args.output/'figures.json').open('x') as f:
        json.dump(record, f, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps(record))


if __name__ == '__main__':
    main()
