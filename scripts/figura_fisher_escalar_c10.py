"""Scientific figure from the audited C10 Fisher matrices."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]
def main():
    audit=json.loads((R/'results/C10/fisher_audit/audit.json').read_text())
    done=json.loads((R/'results/C10/fisher_v4/complete.json').read_text())
    values=np.array([r['compression_generalized_eigenvalues'] for r in audit['results']]);x=np.arange(len(values))
    labels=[f"{r['point']['u']:g}\n{r['point']['epsilon']:g}".replace('.',',') for r in audit['results']]
    fig,ax=plt.subplots(figsize=(8.4,4.4),layout='constrained')
    for k in range(1,5):ax.plot(x,values[:,k],'.-',color='#aab2bb',lw=.9,alpha=.8)
    ax.plot(x,values[:,0],'o-',color='#ad341b',label='Menor autovalor generalizado')
    ax.plot(x,values[:,-1],'s-',color='#17668e',label='Maior autovalor generalizado')
    ax.axhline(1,color='black',lw=.8,ls='--',label='Informação preservada')
    ax.set_yscale('log');ax.set_ylim(.003,1.3);ax.set_xticks(x,labels);ax.set_xlabel('Cenário: u (linha superior) e ε (linha inferior)')
    ax.set_ylabel('Fração local de informação: B_G em relação a A_G');ax.grid(axis='y',which='both',alpha=.2);ax.legend(loc='center right',fontsize=8)
    out=R/'figures/escalar';out.mkdir(exist_ok=True)
    fig.savefig(out/'fisher_compressao.pdf');fig.savefig(out/'fisher_compressao.png',dpi=180);plt.close(fig)
    lines=['\\begin{tabular}{rrccc}','\\toprule','$u$ & $\\varepsilon$ & A0\\_CN & A\\_G & B\\_G \\\\','\\midrule']
    for r in done['results']:
        ranks=[r['levels'][2][-1]['diagnostics'][m]['rank'] for m in ('A0_CN','A_G','B_G')]
        lines.append(f"{r['point']['u']:g} & {r['point']['epsilon']:g} & "+' & '.join(map(str,ranks))+' \\\\')
    lines+=['\\bottomrule','\\end{tabular}']
    (out/'fisher_postos.tex').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
