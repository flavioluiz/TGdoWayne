"""Analytical prior/Fisher references only; no physical likelihood or draws."""
from pathlib import Path
import hashlib
import json
import resource
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent

def main():
    out=HERE/'figuras_analiticas_v1'
    out.mkdir(exist_ok=False)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                         'pdf.fonttype':42,'axes.grid':True,'grid.alpha':.18})
    colors=['#215A8E','#BA5A24','#397B59']
    labels=[r'Uniforme em $u$',r'Uniforme em $u^2$',r'Logarítmica, $a=10^{-3}$']
    u=np.linspace(0,1,1001);a=.001;q=.95
    cdfs=[u,u*u,np.log(np.clip(u,a,1)/a)/np.log(1/a)]
    quantiles=[q,np.sqrt(q),a*(1/a)**q]
    b=np.linspace(.2,1,401)
    support_quantiles=[q*b,np.sqrt(q)*b,a*(b/a)**q]
    fig,axes=plt.subplots(1,2,figsize=(10,3.8),layout='constrained')
    for color,label,cdf,p,curve in zip(colors,labels,cdfs,quantiles,support_quantiles):
        axes[0].plot(u,cdf,color=color,label=label,lw=1.8)
        axes[0].plot([p],[q],marker='o',ms=4,color=color)
        axes[1].plot(b,curve,color=color,lw=1.8)
    axes[0].axhline(q,color='.4',ls=':',lw=1)
    axes[0].set(xlabel=r'Massa $u$',ylabel='CDF da priori',xlim=(0,1),ylim=(0,1.02),title='(a) Medidas distintas')
    axes[0].legend(loc='lower right',fontsize=8.5)
    axes[1].plot(b,b,color='.5',ls=':',lw=1,label=r'Corte $b$')
    axes[1].set(xlabel=r'Corte superior $b$',ylabel=r'Quantil prévio $Q_{0,95}(u)$',
                xlim=(.2,1),ylim=(0,1.02),title='(b) Dependência do suporte')
    axes[1].legend(loc='upper left',fontsize=8.5)
    fig.savefig(out/'prioris_suporte.pdf',metadata={'CreationDate':None,'ModDate':None})
    fig.savefig(out/'prioris_suporte.png',dpi=160)
    plt.close(fig)
    rho=np.linspace(-.8,.8,401)
    ratios=np.array([1/(1+rho),1/(1-rho)])
    fig,ax=plt.subplots(figsize=(7.2,3.7),layout='constrained')
    ax.plot(rho,ratios[0],color=colors[0],label=r'$g=(1,1)^{\mathsf{T}}$')
    ax.plot(rho,ratios[1],color=colors[1],label=r'$g=(1,-1)^{\mathsf{T}}$')
    ax.axhline(1,color='.4',ls=':',lw=1)
    ax.set(xlabel=r'Correlação $\rho$',ylabel=r'$I_{\rm completa}/I_{\rm diagonal}$',
           xlim=(-.8,.8),ylim=(0,5.2),title='Contraexemplo local: o sinal da diferença depende de g')
    ax.legend(fontsize=9)
    fig.savefig(out/'fisher_direcao.pdf',metadata={'CreationDate':None,'ModDate':None})
    fig.savefig(out/'fisher_direcao.png',dpi=160)
    plt.close(fig)
    np.savez_compressed(out/'curvas_analiticas.npz',u=u,prior_cdf=np.array(cdfs),upper=b,
                        prior_quantile95=np.array(support_quantiles),rho=rho,fisher_ratios=ratios)
    record={'scope':'Analytical identities, not fitted PTA posterior or simulated population.',
            'quantiles95_support_upper1':dict(zip(['uniform_u','uniform_u_squared','log_uniform_u_a.001'],quantiles)),
            'prior_supports':[[0,1],[0,1],[a,1]],'physical_likelihood_values':0,'ORF':0,'draws':0,
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'files':[{'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
                     for p in sorted(out.iterdir()) if p.is_file()],
            'process_CPU_seconds':sum(resource.getrusage(resource.RUSAGE_SELF)[:2]),
            'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)}
    (out/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record))

if __name__=='__main__':main()
