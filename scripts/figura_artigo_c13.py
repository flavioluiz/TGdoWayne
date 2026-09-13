"""English manuscript figure from unchanged prior-predictive summaries."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
p=root/'results/C11/statistical_audit.json'; a=json.loads(p.read_text()); assert a['passed']
models=['A0_CN','A_CN','B_CN','C_beta_CN','C_full_CN','A_G','B_G','C_beta_G','C_full_G']
labels=['A0/CN','A/CN','B/CN','Cβ/CN','Cfull/CN','A/G','B/G','Cβ/G','Cfull/G']
plt.rcParams.update({'font.size':10,'axes.titlesize':10,'pdf.fonttype':42})
fig,axes=plt.subplots(1,2,figsize=(6.3,4.7),sharey=True)
y=np.arange(9)
for population,offset,color,marker in [('P12K4',-.13,'#0072B2','o'),('P16K8',.13,'#D55E00','s')]:
 rows=[next(r for r in a['prior_information'] if r['population']==population and r['model']==m) for m in models]
 axes[0].errorbar([r['mean_KL_nats'] for r in rows],y+offset,xerr=[r['MCSE_mean_KL'] for r in rows],fmt=marker,color=color,capsize=3,label=population)
 axes[1].scatter([r['event_unresolved_prior']/500 for r in rows],y+offset,color=color,marker=marker)
axes[0].set_yticks(y,labels);axes[0].invert_yaxis();axes[0].set_xscale('log')
axes[0].set_xlabel('Mean KL (nat)');axes[0].set_title('Mass information')
axes[1].set_xlabel('Fraction of unresolved\nlikelihood events');axes[1].set_xlim(-.015,.4);axes[1].set_xticks([0,.2,.4]);axes[1].set_title('Numerical precision')
for ax in axes:ax.grid(axis='x',alpha=.25)
axes[0].legend(frameon=False);fig.tight_layout()
outputs={}
for ext in ('pdf','png'):
 out=root/f'article/figures/information_academic.{ext}';fig.savefig(out,dpi=180,bbox_inches='tight');outputs[str(out.relative_to(root))]=hashlib.sha256(out.read_bytes()).hexdigest()
(root/'results/C13/article_figure.json').write_text(json.dumps(dict(input_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),outputs=outputs),indent=2)+'\n')
