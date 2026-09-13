"""Presentation figures from published results; no scientific simulations."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).parent/'figures'
OUT.mkdir(exist_ok=True)
navy='#132D46';teal='#008B8B';orange='#DA6B34';gray='#64748B'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':14,'axes.labelsize':14,'axes.titlesize':15,'xtick.labelsize':12,'ytick.labelsize':12,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#CAD5DF','text.color':navy,'axes.labelcolor':navy,'xtick.color':gray,'ytick.color':gray,'pdf.fonttype':42})
sources={}
def src(rel):
 p=ROOT/rel;sources[rel]=hashlib.sha256(p.read_bytes()).hexdigest();return p
def save(fig,name):
 fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None});fig.savefig(OUT/(name+'.png'),bbox_inches='tight',dpi=150);plt.close(fig)
# Explicit analytic illustrations, rather than fabricated observations.
u=np.linspace(0,1,500);fig,ax=plt.subplots(figsize=(7.3,3.6))
for k,col in [(1,orange),(2,teal),(4,navy)]:ax.plot(u,np.sqrt(1-(u/k)**2),lw=3,color=col,label=f'canal k = {k}')
ax.set(xlabel=r'Massa adimensional $u=f_gT$',ylabel=r'$v_g/c=\beta_k$',ylim=(0,1.07));ax.legend(frameon=False,loc='lower left');save(fig,'dispersao')
fig,ax=plt.subplots(figsize=(7.3,3.4));ax.axhline(1,color=teal,lw=3,label='priori = posterior');ax.fill_between(u,0,1,where=u<=.95,color=teal,alpha=.16);ax.axvline(.95,color=orange,lw=2,ls='--');ax.text(.94,1.18,r'$Q_{95}=0{,}95$',ha='right',color=orange,fontsize=18);ax.set(xlim=(0,1),ylim=(0,1.5),xlabel=r'$u=f_gT$',ylabel='Densidade');ax.legend(frameon=False,loc='upper left');save(fig,'priori')
coverage=json.loads(src('results/C13/review_efac_coverage.json').read_text())['coverage_counts'];fig,ax=plt.subplots(figsize=(7.5,3.8));names=[r'$A_{0,\mathrm{CN}}$',r'$A_{\mathrm{CN}}$',r'$B_{\mathrm{CN}}$',r'$A_{\mathrm{G}}$',r'$B_{\mathrm{G}}$']
for i,r in enumerate(coverage):
 val=100*r['nominal']/r['n'];lo=100*r['guaranteed']/r['n'];hi=100*r['possible']/r['n'];col=orange if i in [1,2] else teal
 ax.barh(i,val,color=col,alpha=.18,height=.54);ax.errorbar(val,i,xerr=[[val-lo],[hi-val]],fmt='o',color=col,capsize=4,ms=8);ax.text(hi+1,i,f'{val:.1f}%'.replace('.',','),va='center',color=col,fontsize=15)
ax.axvline(90,color=navy,ls='--',lw=1.7);ax.set(yticks=range(5),yticklabels=names,xlim=(50,102),xlabel='Cobertura central de 90% (%)');ax.invert_yaxis();save(fig,'cobertura')
with np.load(src('figures/academicas/plot_values.npz')) as d:
 fig,axs=plt.subplots(1,2,figsize=(9,3.7),sharex=True,sharey=True)
 for ax,model,title,col in zip(axs,['A0_CN','A_CN'],['Coeficientes complexos','Normal dos estimadores'],[teal,orange]):
  x,v,l,h=d[f'c07_{model}_4'];ax.plot(x,x,color=gray,ls='--');ax.fill_between(x,l,h,color=col,alpha=.18);ax.plot(x,v,color=col,lw=2.5);ax.set(title=title,xlabel='PIT',xlim=(0,1),ylim=(0,1))
 axs[0].set_ylabel('CDF empírica');fig.tight_layout();save(fig,'pit_efac')
audit=json.loads(src('results/C11/statistical_audit.json').read_text());fig,ax=plt.subplots(figsize=(7.5,3.5));r=audit['paired_information'];v=[x['mean_KL_difference_nats'] for x in r];err=[x['MCSE'] for x in r];ax.barh([1,0],v,color=[teal,navy],height=.46);ax.errorbar(v,[1,0],xerr=err,fmt='none',color=orange,capsize=5,lw=2)
for y,x,e in zip([1,0],v,err):ax.text(x+e+.004,y,f'{x:.3f} ± {e:.3f}',va='center',fontsize=15,color=navy)
ax.set(yticks=[1,0],yticklabels=['12 pulsares · 4 canais','16 pulsares · 8 canais'],xlim=(0,.165),xlabel='Perda média de informação por compressão (nat)');save(fig,'informacao')
cond=json.loads(src('results/C13/conditional_contrasts/results.json').read_text());fig,ax=plt.subplots(figsize=(8,3.7));ax.axvspan(-.01,.01,color=teal,alpha=.09);ax.axvline(0,color=gray,lw=1);labels=[]
for i,r in enumerate(cond['contrasts']):
 lo,hi=r['mean_numerical_interval'];v=r['mean'];col=teal if i<2 else orange
 ax.errorbar(v,3-i,xerr=[[v-lo],[hi-v]],fmt='o',color=col,capsize=5,lw=2.4,ms=7)
labels=[r'$C_\beta-B$ · G',r'$C_{\rm full}-C_\beta$ · G',r'$C_\beta-B$ · CN',r'$C_{\rm full}-C_\beta$ · CN'];ax.set(yticks=[3,2,1,0],yticklabels=labels,xlim=(-.012,.012),xlabel=r'Diferença média de $Q_{95}(u)$');ax.set_xticks([-.01,-.005,0,.005,.01]);save(fig,'condicional')
with np.load(src('results/C13/timing_projection/matrices.npz')) as a:
 fig,ax=plt.subplots(figsize=(7.6,3.5));f=a['transfer_frequency_per_year']
 for model,lab,col in [('none','Sem ajuste',gray),('spin','Rotação',teal),('spin_annual','Rotação + termos anuais',orange)]:ax.plot(f,a[f'regular_{model}_transfer'],label=lab,color=col,lw=2.5)
 ax.set(xlabel=r'Frequência (ano$^{-1}$)',ylabel='Fração de potência retida',ylim=(-.03,1.08));ax.legend(frameon=False,fontsize=12,loc='lower right');save(fig,'timing_transfer')
 fig,axs=plt.subplots(1,2,figsize=(8.4,3.8))
 for ax,key,title in zip(axs,['correlation','pseudocorrelation'],['Correlação entre canais','Pseudocovariância normalizada']):
  im=ax.imshow(np.abs(a[f'regular_spin_annual_{key}']),vmin=0,vmax=1,cmap='viridis',origin='lower');ax.set(title=title,xlabel='Canal de Fourier',xticks=[0,3,7],xticklabels=[1,4,8],yticks=[0,3,7],yticklabels=[1,4,8])
 fig.colorbar(im,ax=axs,fraction=.025,pad=.04);save(fig,'timing_matrices')
(OUT/'sources.json').write_text(json.dumps({'sources_sha256':sources,'analytic_illustrations':['dispersao','priori'],'scope':'Existing numerical results redrawn for projection; no new inference.'},indent=2)+'\n')
