"""Static numerical diagnostic, never presented as a scientific campaign."""
import json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'tmp/matplotlib'))
os.environ.setdefault('XDG_CACHE_HOME',str(ROOT/'tmp/font_cache'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=ROOT/'results/C07/reference/cubature'
OUTPUT=ROOT/'figures/C07'
OUTPUT.mkdir(parents=True,exist_ok=True)

d=json.loads((HERE/'comparison.json').read_text())
a=d['conditional_scale_route']['20_to32'];b=d['truncated_box_route']['20cubed_to32_20_12']
if b is None:raise RuntimeError('Truncated comparison not complete.')
fig,axes=plt.subplots(1,2,figsize=(6.5,3.8),layout='constrained')
x=np.arange(20)
axes[0].semilogy(x,a['CDF_difference_by_cut'],'o',ms=4,label='Condicional: 20³ → 32³')
axes[0].semilogy(x,b['CDF_difference_by_cut'],'s',ms=4,label='Alinhada: 20³ → 32×20×12')
axes[0].axhline(.002,color='black',ls='--',lw=1,label='Tolerância: 0,002')
axes[0].set_xticks([2,7,12,17],[r'$g$',r'$\gamma$',r'$r$',r'$t$'])
for edge in [4.5,9.5,14.5]:axes[0].axvline(edge,color='.85',lw=.6)
axes[0].set_ylabel('Diferença absoluta de CDF')
axes[0].set_title('CDFs em vinte cortes congelados',fontsize=10)
axes[0].legend(fontsize=7,loc='upper left',bbox_to_anchor=(0,-.14),frameon=False)
categories=['ordem dos\nparâmetros aux.','malha\nde massa']
logz=[a['absolute_log_evidence_difference'],d['target_specific_mass_refinement_truncated']['comparison']['absolute_log_evidence_difference']]
axes[1].scatter(categories,logz,s=65,color=['#246e9e','#40877b'])
axes[1].set_xlim(-.5,1.5);axes[1].set_ylim(1e-10,.003)
axes[1].set_yscale('log');axes[1].axhline(.001,color='black',ls='--',lw=1,label='Tolerância: 0,001')
axes[1].set_ylabel(r'$|\Delta\log Z|$');axes[1].set_title('Refinamento da evidência')
axes[1].legend(fontsize=8,loc='upper left',bbox_to_anchor=(0,-.14),frameon=False)
for ax in axes:ax.grid(axis='y',alpha=.2);ax.spines[['top','right']].set_visible(False)
fig.suptitle('Referência A0 — realização 14',fontsize=10)
fig.savefig(OUTPUT/'cubatura_convergencia.png',dpi=180)
fig.savefig(OUTPUT/'cubatura_convergencia.pdf',metadata={'CreationDate':None,'ModDate':None})
