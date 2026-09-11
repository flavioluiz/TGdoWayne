"""Layout correction only, using the completed descriptive CSV; no inference."""
from pathlib import Path
import csv,json,os,hashlib
import numpy as np

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'results/descriptive_bins.csv'
OUT=HERE/'figures_v2'
OUT.mkdir(exist_ok=False)
os.environ.setdefault('MPLCONFIGDIR',str(HERE/'results/matplotlib_cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,
 'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'pdf.fonttype':42,
 'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
grid=np.full((2,3,2,3),np.nan);counts=np.zeros((2,3),int)
for row in csv.DictReader(SOURCE.open()):
    if row['group']!='u_x_gamma' or row['parameter']!='u':continue
    metric=0 if row['quantity']=='quantile' and row['probability']=='0.95' else 1 if row['quantity']=='central90_width' else None
    if metric is None:continue
    c,i,j=map(int,[row['contrast_index'],row['u_bin'],row['gamma_bin']])
    grid[metric,c,j,i]=float(row['mean']);counts[j,i]=int(row['n'])
if not np.isfinite(grid).all() or counts.sum()!=500:raise ValueError('Complete fixed-bin table required')
vmax=float(np.max(abs(grid)))
labels=[r'$A_{\rm CN}-A0_{\rm CN}$',r'$B_{\rm CN}-A_{\rm CN}$',r'$B_{\rm G}-A_{\rm G}$']
fig,axes=plt.subplots(2,3,figsize=(8.2,5.2),sharex=True,sharey=True)
fig.subplots_adjust(left=.16,right=.82,bottom=.185,top=.855,wspace=.16,hspace=.42)
for metric in range(2):
    for c in range(3):
        ax=axes[metric,c];im=ax.imshow(grid[metric,c],origin='lower',cmap='RdBu_r',vmin=-vmax,vmax=vmax,aspect='auto')
        for j in range(2):
            for i in range(3):
                value=grid[metric,c,j,i]
                ax.text(i,j,f'{value:+.4f}\nn={counts[j,i]}',ha='center',va='center',fontsize=8,
                  color='white' if abs(value)>.65*vmax else '#242a30')
        ax.set_title(labels[c],fontsize=9)
        ax.set_xticks(range(3),['[0;.5)','[.5;.9)','[.9;1]'])
        ax.set_yticks(range(2),['[3;4.25)','[4.25;5.5]'])
        if metric==1:ax.set_xlabel(r'$u_{\rm verdadeiro}$')
        if c==0:ax.set_ylabel(r'$\gamma_{\rm verdadeiro}$',labelpad=2)
cax=fig.add_axes([.865,.26,.023,.50]);fig.colorbar(im,cax=cax,label='Média / largura da priori de u')
fig.text(.017,.72,'ΔQ95 de u',rotation=90,va='center',ha='center',fontsize=10)
fig.text(.017,.33,'Δlargura90 de u',rotation=90,va='center',ha='center',fontsize=10)
fig.suptitle('Descrição por bins fixos da verdade: todos os 500 casos',y=.98,fontsize=11)
fig.text(.5,.04,'Cores e números: médias empíricas das diferenças, nova análise − anterior.\nOs bins não filtram guardas numéricas; não são testes de viés ou equivalência.',ha='center',fontsize=8,color='#444b52')
products={}
for ext in ['pdf','svg','png']:
    p=OUT/('paired_mass_bins.'+ext);fig.savefig(p,dpi=150)
    products[p.name]=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
plt.close(fig)
(OUT/'manifest.json').write_text(json.dumps(dict(scope='LAYOUT_ONLY_FROM_COMPLETE_DESCRIPTIVE_CSV',
 source=dict(path=str(SOURCE),sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest()),
 script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),products=products,
 original_figure_preserved=True,new_ORF=0,new_likelihood=0,new_Monte_Carlo=0),indent=2)+'\n')
print('Corrected layout generated from unchanged CSV')
