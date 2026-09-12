"""Publication figures from the completed, audited C10 population synthesis."""
from pathlib import Path
import os,json,sys
R=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(R/'tmp/matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,str(R/'src'))
from inference.sbc_sensitivity import ecdf_envelope


def main():
    synthesis=R/'results/C10/population_synthesis'
    result=json.loads((synthesis/'results.json').read_text())
    audit=json.loads((R/'results/C10/production_audit/audit.json').read_text())
    assert audit['targets']==result['targets']==6344
    out=R/'figures/escalar';out.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':9,'pdf.fonttype':42})
    models=['A0_CN','A_CN','B_CN','A_G','B_G']
    colors=['#1b5e85','#b24c30','#8a6815','#386e4b','#77639c']
    def save(fig,name):
        fig.savefig(out/(name+'.pdf'));fig.savefig(out/(name+'.png'),dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(9,3.8),layout='constrained')
    groups=[models,['C_beta_CN','C_full_CN','C_beta_G','C_full_G']]
    for ax,group in zip(axes,groups):
        rows=[next(r for r in result['ensemble_summaries'] if r['ensemble']=='null' and r['label']==m) for m in group]
        fractions=np.array([r['detection']['nominal_fraction'] for r in rows])*100
        intervals=np.array([r['detection']['CP95_union'] for r in rows])*100
        assert np.all(intervals[:,0]<=fractions) and np.all(fractions<=intervals[:,1])
        ax.errorbar(np.arange(len(rows)),fractions,yerr=np.array([fractions-intervals[:,0],intervals[:,1]-fractions]),fmt='o',color='#17668e',capsize=3)
        ax.set_xticks(np.arange(len(rows)),[r['label'].replace('C_beta','Cβ').replace('C_full','Cfull') for r in rows],rotation=25)
        ax.set_title(f"Injeções tensoriais — N={rows[0]['n']} por método")
        ax.set_ylabel('Declarações BF₁₀ > 10 (%)');ax.set_ylim(bottom=-1);ax.grid(axis='y',alpha=.2)
    save(fig,'falsos_positivos')
    data=np.load(synthesis/'PITs.npz');grid=np.linspace(0,1,201)
    fig,axes=plt.subplots(5,3,figsize=(8.6,9),sharex=True,sharey=True,layout='constrained')
    for row,model in enumerate(models):
        point=data[model+'_point'];bounds=data[model+'_interval']
        for col in range(3):
            ax=axes[row,col];lo,hi=ecdf_envelope(bounds[:,col,0],bounds[:,col,1],grid)
            nominal=np.searchsorted(np.sort(point[:,col]),grid,side='right')/500
            ax.fill_between(grid,lo-grid,hi-grid,color=colors[row],alpha=.22)
            ax.plot(grid,nominal-grid,color=colors[row],lw=1)
            ax.axhline(0,color='black',lw=.6);ax.grid(alpha=.15)
            if row==0:ax.set_title(('u','ε','logL dos mesmos dados')[col])
            if col==0:ax.set_ylabel(model+'\nF̂(t) − t')
            if row==4:ax.set_xlabel('t')
    save(fig,'sbc_ecdf')
    values=np.empty((6,5));annotations={};cell_labels=[]
    for cell in range(6):
        first=next(r for r in result['ensemble_summaries'] if r['label']==models[0] and r['ensemble']=='recovery' and r['cell']==cell)
        u=(.2,.8,.995)[cell//2];e=(.1,.5)[cell%2];cell_labels.append(f'u={u:g}, ε={e:g}')
        for j,model in enumerate(models):
            r=next(r for r in result['ensemble_summaries'] if r['label']==model and r['ensemble']=='recovery' and r['cell']==cell)
            assert r['n']==32
            d=r['detection'];values[cell,j]=d['nominal_fraction']*100
            annotations[cell,j]=f"{d['nominal_count']}/32\n[{d['certain_count']}, {d['possible_count']}]"
    fig,ax=plt.subplots(figsize=(8,4.9),layout='constrained')
    im=ax.imshow(values,vmin=0,vmax=100,cmap='Blues',aspect='auto')
    for (i,j),text in annotations.items():ax.text(j,i,text,ha='center',va='center',fontsize=8,color='white' if values[i,j]>60 else 'black')
    ax.set_xticks(range(5),models);ax.set_yticks(range(6),cell_labels);ax.set_xlabel('Método');ax.set_ylabel('Célula de recuperação fixa')
    fig.colorbar(im,ax=ax,label='Declarações nominais BF₁₀ > 10 (%)')
    save(fig,'recuperacao_deteccao')
    rows=[]
    for family in ('correct','approximate','paired_central90'):
        tests=[t for t in result['tests'] if t['family']==family]
        rows.append(dict(family=family,tests=len(tests),nominal_rejections=sum(t['nominal_reject'] for t in tests),
                         persistent_rejections=sum(t['decision']=='REJECT_FOR_ALL_INTERVAL_VALUES' for t in tests),
                         indeterminate=sum(t['decision']=='INDETERMINATE' for t in tests)))
    (out/'sbc_counts.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
