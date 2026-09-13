"""Public sky directions used by the synthetic nested C11 experiment."""
from pathlib import Path
import hashlib,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path(__file__).resolve().parents[1]
source=root/'configs/application/c11_geometry.json';data=json.loads(source.read_text())
points=np.array([r['unit_direction'] for r in data['selected']]);ra=np.arctan2(points[:,1],points[:,0]);dec=np.arcsin(points[:,2]);longitude=-ra
fig=plt.figure(figsize=(8.4,4.5));ax=fig.add_subplot(111,projection='aitoff');ax.grid(alpha=.35)
for sl,color,marker,label in [(slice(0,12),'#0072B2','o','Compartilhados: P12K4 e P16K8'),(slice(12,16),'#D55E00','s','Adicionais: P16K8')]:
 ax.scatter(longitude[sl],dec[sl],s=38,c=color,marker=marker,label=label,zorder=3)
for i,(x,y) in enumerate(zip(longitude,dec),1):ax.annotate(str(i),(x,y),xytext=(5,4),textcoords='offset points',fontsize=8)
ticks=np.arange(-150,151,30);ax.set_xticks(np.deg2rad(ticks));ax.set_xticklabels([str(int(-t%360))+'°' for t in ticks],fontsize=8)
ax.set_xlabel('Ascensão reta (sentido astronômico)',labelpad=22);ax.set_ylabel('Declinação')
ax.set_title('Posições celestes dos pulsares simulados',pad=18)
ax.legend(loc='lower center',bbox_to_anchor=(.5,-.24),ncol=2,frameon=False,fontsize=8)
fig.subplots_adjust(bottom=.21,top=.85)
out=root/'figures/aplicacao';out.mkdir(parents=True,exist_ok=True)
for ext in ('pdf','png'):fig.savefig(out/('geometria_academica.'+ext),dpi=180,bbox_inches='tight')
plt.close(fig)
receipt=dict(source=str(source.relative_to(root)),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),public_quantities='Sky directions only; no observed timing residuals plotted',synthetic_quantities='Distances, signal and noise are synthetic and are not encoded in this sky plot.',point_labels={str(i):r['pulsar'] for i,r in enumerate(data['selected'],1)},license='MeerKAT data metadata: CC BY 4.0, DOI 10.57891/j0vh-5g31',outputs={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('geometria_academica.*')})
(root/'results/C13/geometry_figure.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
