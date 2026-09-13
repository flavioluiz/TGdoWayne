"""Plot synthetic timing transfer and Fourier covariance; evaluate Gaussian KL."""
from pathlib import Path
import os
import hashlib
import json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'tmp/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

source=ROOT/'results/C13/timing_projection/matrices.npz'
out=ROOT/'figures/timing';out.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.size':11,'axes.labelsize':11,'legend.fontsize':10,
    'savefig.bbox':'tight','pdf.fonttype':42})
with np.load(source) as z:
    fig,ax=plt.subplots(figsize=(6.3,3.4),layout='constrained')
    styles=[('none','Sem ajuste','#606060','--'),('spin','Rotação','#0072B2','-'),
            ('spin_annual','Rotação + termos anuais','#D55E00','-')]
    for fit,label,color,style in styles:
        ax.plot(z['transfer_frequency_per_year'],z['regular_'+fit+'_transfer'],
            label=label,color=color,ls=style,lw=1.8)
    ax.axvline(1,color='#aaa',ls=':',lw=1)
    ax.set(xlabel=r'Frequência (ano$^{-1}$)',ylabel='Fração de potência retida',
        xlim=(0,3),ylim=(-.03,1.05))
    ax.legend(loc='lower right',frameon=False)
    fig.savefig(out/'transferencia.pdf');fig.savefig(out/'transferencia.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(6.8,3.4),layout='constrained')
    for ax,key,title in zip(axes,['correlation','pseudocorrelation'],
            [r'$|C_{kl}|/\sqrt{C_{kk}C_{ll}}$',r'$|P_{kl}|/\sqrt{C_{kk}C_{ll}}$']):
        im=ax.imshow(abs(z['regular_spin_annual_'+key]),vmin=0,vmax=1,cmap='cividis',origin='lower')
        ax.set(title=title,xlabel='Canal l',ylabel='Canal k',xticks=range(8),yticks=range(8),
            xticklabels=range(1,9),yticklabels=range(1,9))
    fig.colorbar(im,ax=axes,shrink=.8,label='Módulo normalizado')
    fig.savefig(out/'covariancias.pdf');fig.savefig(out/'covariancias.png',dpi=180);plt.close(fig)
    rows=[]
    for sampling in ('regular','jittered'):
        for fit,_,_,_ in styles:
            prefix=sampling+'_'+fit;C=z[prefix+'_C'];R=z[prefix+'_real_covariance']
            record=dict(sampling=sampling,fit=fit)
            for name,cov in [('proper_full_C',C),('proper_independent',np.diag(np.diag(C)))]:
                S=np.block([[cov.real,-cov.imag],[cov.imag,cov.real]])/2
                sr,lr=np.linalg.slogdet(R);ss,ls=np.linalg.slogdet(S);assert sr==ss==1
                value=.5*(np.trace(np.linalg.solve(S,R))-len(R)+ls-lr)
                assert value>=-1e-10
                record[name+'_KL_nats']=float(max(0,value))
            rows.append(record)
report=dict(scope='KL between the exact 16-dimensional real Gaussian law and proper-complex approximations, with full C or independent channels. Not posterior-prior KL or a mass-information loss.',
    records=rows,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(ROOT/'results/C13/timing_projection/gaussian_density_loss.json').write_text(json.dumps(report,indent=2)+'\n')
simulation=json.loads((source.parent/'results.json').read_text())
def format_number(value):
    if value<1e-10:
        return r'$<10^{-10}$'
    if value<.0005:
        mantissa, exponent=f'{value:.2e}'.split('e')
        return '$'+mantissa.replace('.',',')+r'\times10^{'+str(int(exponent))+'}$'
    return f'{value:.3f}'.replace('.',',')
table=[r'\begin{tabular}{llrrr}',r'\toprule',
       r'Amostragem & Ajuste & $\max_{k\ne l}|\rho_{kl}|$ & $\max|\eta_{kl}|$ & KL (nat)\\',r'\midrule']
labels={'none':'Nenhum','spin':'Rotação','spin_annual':'Rotação + anual'}
for record,loss in zip(simulation['records'],rows):
    assert (record['sampling'],record['fit'])==(loss['sampling'],loss['fit'])
    table.append(' & '.join(['Regular' if record['sampling']=='regular' else 'Irregular',labels[record['fit']],
        format_number(record['maximum_cross_frequency_correlation']),
        format_number(record['maximum_normalized_pseudocovariance']),
        format_number(loss['proper_independent_KL_nats'])])+r'\\')
table += [r'\bottomrule',r'\end{tabular}']
(out/'tabela.tex').write_text('\n'.join(table)+'\n')
print(json.dumps(rows,indent=2))
