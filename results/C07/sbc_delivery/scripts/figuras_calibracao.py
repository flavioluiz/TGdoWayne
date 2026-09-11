#!/usr/bin/env python3
"""Static scientific ECDF figures: numerical sensitivity and ideal IID DKW separated."""
from pathlib import Path
import argparse,json,os,sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from inference.campaign_io import read_json,sha256,write_json_new
from inference.sbc_sensitivity import ecdf_envelope


def make_figures(summary_path,arrays_path,output):
    summary=read_json(summary_path);output=Path(output)
    if sha256(arrays_path)!=summary['arrays_sha256']:raise RuntimeError('Synthesis arrays no longer match summary.')
    if output.exists():raise FileExistsError('Figure destination must be new.')
    output.mkdir(parents=True);os.environ.setdefault('MPLCONFIGDIR',str(output/'matplotlib_cache'));os.environ.setdefault('XDG_CACHE_HOME',str(output/'font_cache'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    with np.load(arrays_path,allow_pickle=False) as p:
        pit=p['pit'].copy();lower=p['pit_lower'].copy();upper=p['pit_upper'].copy();resolved=p['resolved'].copy()
    models=summary['models'];n=summary['simulations_per_model'];cfg=summary['config'];grid=np.linspace(0,1,1001)
    if pit.shape!=(5,n,6) or lower.shape!=pit.shape or upper.shape!=pit.shape or resolved.shape!=pit.shape:raise ValueError('All30 registered PIT panels required.')
    labels=[r'$u$',r'$\log_{10} A_{\rm GW}$',r'$\gamma_{\rm GW}$',r'$\log_{10} A_{\rm r}$',r'$\log_{10}{\rm EFAC}$',r'$\log L(\theta_{\rm true};d)$']
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
    produced=[];toy=summary['scope'].startswith('TOY64')
    for group,title in [('correct','Modelos de referência'),('approximate','Aproximações da verossimilhança')]:
        selected=cfg['families'][group]['models'];rows=len(selected);family=cfg['families'][group]['hypotheses']
        eps=float(np.sqrt(np.log(2*family/cfg['scientific_alpha'])/(2*n)))
        fig,axes=plt.subplots(rows,6,figsize=(17.5,3.0*rows+1.6),sharex=True,sharey=True,squeeze=False)
        fig.subplots_adjust(left=.052,right=.989,bottom=.15 if rows==3 else .19,top=.875,wspace=.23,hspace=.39)
        for row,name in enumerate(selected):
            m=models.index(name)
            for j,ax in enumerate(axes[row]):
                ecdf=np.searchsorted(np.sort(pit[m,:,j]),grid,side='right')/n
                lo,hi=ecdf_envelope(lower[m,:,j],upper[m,:,j],grid)
                ax.fill_between(grid,np.maximum(0,grid-eps),np.minimum(1,grid+eps),color='#e6e7e9',zorder=0)
                ax.plot(grid,np.maximum(0,grid-eps),color='#9ca1a8',ls=':',lw=.65,zorder=1)
                ax.plot(grid,np.minimum(1,grid+eps),color='#9ca1a8',ls=':',lw=.65,zorder=1)
                ax.fill_between(grid,lo,hi,color='#197aab',alpha=.22,step='post',zorder=2)
                ax.plot(grid,grid,color='#32383e',ls='--',lw=.8,zorder=3)
                ax.step(grid,ecdf,where='post',color='#075781',lw=1.2,zorder=4)
                ax.set(xlim=(0,1),ylim=(0,1),xticks=[0,.5,1],yticks=[0,.5,1])
                ax.set_title(name+' | '+labels[j],pad=7)
                ax.text(.96,.055,'CDF analítica' if toy else f'{int(resolved[m,:,j].sum())}/{n} resolvidas',transform=ax.transAxes,ha='right',va='bottom',fontsize=8,color='#333b43',bbox=dict(facecolor='white',edgecolor='none',alpha=.8,pad=2))
                if j==0:ax.set_ylabel('CDF empírica')
                if row==rows-1:ax.set_xlabel('PIT')
                ax.grid(alpha=.14,lw=.5)
        subtitle='TOY analítico de 64 dados; teste do pipeline, sem resultados PTA' if toy else f'{n} realizações por modelo; todos os identificadores retidos'
        fig.suptitle(title+'\n'+subtitle,fontsize=15,y=.977)
        legend=[Line2D([0],[0],color='#075781',lw=1.4,label='ECDF dos PITs calculados'),Patch(facecolor='#197aab',alpha=.22,label='Sensibilidade numérica'),Patch(facecolor='#e6e7e9',label=f'DKW IID ideal (família {family})'),Line2D([0],[0],color='#32383e',ls='--',lw=.8,label='Uniforme ideal')]
        fig.legend(handles=legend,loc='lower center',bbox_to_anchor=(.5,.048 if rows==3 else .066),ncol=4,frameon=False,fontsize=9)
        footer='Faixa numérica: 0,002 + z × MCSE, alphaMC=0,01 / 15.000; não resolvidas: [0,1]. DKW ideal é separado.\nConclusões condicionais às evidências independentes; não rejeição não prova correção.'
        if toy:footer='TOY: PITs analíticos; MCSE sintética de 1e-8 verifica a interface, sem certificação de precisão PTA.\n'+footer
        fig.text(.5,.007 if toy else .017,footer,ha='center',va='bottom',fontsize=8.5,color='#444b52')
        for suffix in ['pdf','svg']:
            file=output/f'ecdf_{group}.{suffix}';fig.savefig(file,format=suffix,facecolor='white');produced.append(dict(file=file.name,sha256=sha256(file),panels=rows*6))
        plt.close(fig)
    write_json_new(output/'figure_manifest.json',dict(scope=summary['scope'],source_sha256=sha256(__file__),summary_sha256=sha256(summary_path),arrays_sha256=sha256(arrays_path),files=produced,numerical_and_ideal_sampling_bands_are_distinct=True))
    return produced


def main():
    parser=argparse.ArgumentParser()
    for name in ('summary','arrays','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();print(json.dumps(make_figures(args.summary,args.arrays,args.output)))

if __name__=='__main__':main()
