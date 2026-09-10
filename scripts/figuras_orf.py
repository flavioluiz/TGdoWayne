#!/usr/bin/env python3
"""Figuras analíticas de C05; sem interpolar os benchmarks esparsos."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pta.orf import earth_analytic


def main():
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'pdf.fonttype': 42})
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.5), layout='constrained')
    angle = np.linspace(0, 180, 361)
    for beta, color in zip((0, 0.5, 0.9, 1), ('#555555', '#0072B2', '#D55E00', '#009E73')):
        curve = [earth_analytic(beta, float(np.cos(np.deg2rad(a)))) for a in angle]
        axes[0].plot(angle, curve, color=color, label=rf'$\beta={beta:g}$')
    axes[0].axhline(0, color='#aaaaaa', linewidth=0.7)
    axes[0].set(xlabel=r'Separação $\zeta$ (graus)', ylabel=r'$\Gamma^{EE}_{ab}$',
                title='(a) Apenas Terra; normalização fixa', xlim=(0, 180))
    axes[0].legend(frameon=False, ncol=2, fontsize=9)
    distance = np.linspace(100, 102, 801)
    axes[1].plot(distance, 0.8 * np.sin(np.pi * distance)**2, color='#0072B2',
                 label=r'Limiar exato: $\beta=0$')
    axes[1].axhline(0.4, color='#D55E00', linestyle='--',
                    label=r'$y\to\infty$ antes de $\beta\to0$')
    axes[1].set(xlabel=r'$fL/c$', ylabel=r'$\Gamma_{aa}$', ylim=(-0.025, 0.88),
                title='(b) Auto: ordem dos limites', xlim=(100, 102))
    axes[1].legend(frameon=False, fontsize=9, loc='upper center')
    for ax in axes:
        ax.grid(alpha=0.2)
    target = ROOT / 'figures' / 'C05'
    target.mkdir(parents=True, exist_ok=True)
    fig.savefig(target / 'orf_limites.pdf', metadata={'CreationDate': None, 'ModDate': None,
                'Title': 'C05: normalização da ORF e ordem dos limites',
                'Author': 'Projeto TGdoWayne'})
    preview = ROOT / 'tmp' / 'pdfs' / 'v0.5.0'
    preview.mkdir(parents=True, exist_ok=True)
    fig.savefig(preview / 'orf_limites.png', dpi=180)
    plt.close(fig)
    print(target / 'orf_limites.pdf')


if __name__ == '__main__':
    main()
