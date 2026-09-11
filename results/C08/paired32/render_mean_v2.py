from pathlib import Path
import json
import numpy as np
def render(report,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    labels=[r['new']+' − '+r['previous'] for r in report['contrasts']]
    meanpath=output/'u95_representative_mean.pdf'
    if meanpath.exists():raise FileExistsError(meanpath)
    boot=report['bootstrap'];point=np.asarray(boot['point_mean']);ci=np.asarray(boot['point_bootstrap_interval']);env=np.asarray(boot['bootstrap_numeric_envelope'])
    fig,ax=plt.subplots(figsize=(10,5.5),layout='constrained');y=np.arange(7)
    ax.axvspan(-.01,.01,color='#d7e8dd',alpha=.7);ax.axvline(0,color='.4',lw=.7)
    ax.hlines(y,env[:,0],env[:,1],color='#286a91',lw=2,label='Bootstrap + limites numéricos operacionais')
    ax.hlines(y+.13,ci[:,0],ci[:,1],color='.4',lw=2,label='Bootstrap dos pontos originais')
    ax.scatter(point,y+.13,s=20,color='#c55b25',zorder=3,label='Média pontual, 24 IDs')
    ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlabel('Média pareada de ΔU95(u), largura da priori')
    ax.set_title('Piloto representativo: sete contrastes; oito casos de estresse excluídos\nEnvelope aproximado; não certifica equivalência populacional ou cobertura conjunta de 95%')
    ax.legend(fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.15),ncol=1);fig.savefig(meanpath);plt.close(fig)
    return [meanpath]

if __name__=='__main__':render(json.loads(Path('tmp/c08_paired_synthesis_OUTPUT/summary.json').read_text()),'tmp/c08_synthesis_visual/mean_v2')
