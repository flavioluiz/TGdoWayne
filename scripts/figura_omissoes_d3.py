#!/usr/bin/env python3
"""Paired inclusion/omission quantiles on each model's own saved datum."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];D=R/'tmp/c09_D3_components_v1';S=R/'tmp/c09_D3_self_controls_v1';B=R/'tmp/c09_D3_BG_omission_v1'
def read(p):return json.loads(p.read_text())
def q95(path):
 r=read(path)['results'][0];q=next(x for x in r['quantiles'] if x['probability']==.95);return q['lower'],q['upper']
models=['A0_CN','A_G','B_CN_full_variable','B_G_full_variable'];labels=[r'$A_0$',r'$A_G$',r'$B_{CN}$',r'$B_G$']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
fig,axes=plt.subplots(2,2,figsize=(8.1,5.1),sharex=True,sharey=True)
for ax,i in zip(axes.ravel(),(9,10,11,12)):
 for j,model in enumerate(models):
  original=D/f'posterior_execution/d{i}/results/d{i}_{model}.json'
  omitted=B/f'execution/results/omitted_BG_{i}.json' if model=='B_G_full_variable' else S/f'execution/omitted_{i}/results/omitted_{i}_{model}.json'
  for label,p,color,offset in [('Incluído',original,'#1664a1',-.09),('Omitido',omitted,'#ca5b12',.09)]:
   lo,hi=q95(p);ax.errorbar((lo+hi)/2,j+offset,xerr=(hi-lo)/2,fmt='o',markersize=5,color=color,capsize=2,label=label if j==0 else None)
 ax.axvline(.5,color='#333333',ls='--',lw=1,label=r'$u_*=0,5$');ax.axvline(.95,color='#888888',ls=':',lw=1,label=r'$Q_{95}$ da priori')
 ax.set_title(('Monopolo' if i<11 else 'Dipolo')+(', ρ=0,25' if i in (9,11) else ', ρ=1')+f' — dado {i}',fontsize=10)
 ax.set_yticks(range(4),labels);ax.set_xlim(0,1.02);ax.set_ylim(3.5,-.5);ax.grid(axis='x',alpha=.2)
for ax in axes[1]:ax.set_xlabel(r'Quantil superior $Q_{95}$ em $u$')
handles,legendlabels=axes[0,0].get_legend_handles_labels();fig.legend(handles,legendlabels,loc='lower center',ncol=4,frameon=False)
fig.tight_layout(rect=(0,.08,1,1));dest=R/'figures/robustez';dest.mkdir(parents=True,exist_ok=True)
fig.savefig(dest/'omissoes_piloto.pdf');fig.savefig(dest/'omissoes_piloto.png',dpi=180);plt.close(fig)
