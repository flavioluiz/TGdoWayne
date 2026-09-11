"""Descriptive paired C07 products; no inference, resampling, or decisions."""
from pathlib import Path
import argparse,csv,json,os,resource,time
import numpy as np
from load_c07_results import load_c07_results,MODELS,PARAMETERS,read,sha


def write_json(path,value):
    with Path(path).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def csv_rows(path,rows):
    with Path(path).open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def describe(x):
    return dict(n=len(x),mean=float(np.mean(x)),median=float(np.median(x)),
      std_between_datasets=float(np.std(x,ddof=1)) if len(x)>1 else None,
      empirical_p05=float(np.quantile(x,.05)),empirical_p25=float(np.quantile(x,.25)),
      empirical_p75=float(np.quantile(x,.75)),empirical_p95=float(np.quantile(x,.95)),
      minimum=float(np.min(x)),maximum=float(np.max(x)))


def masks_for(truth,design):
    masks=[('all500',-1,-1,np.ones(500,bool))]
    bins=[]
    for j,edges in [(0,design['u_bins']),(2,design['gamma_bins'])]:
        group=[(truth[:,j]>=lo)&((truth[:,j]<hi) if i<len(edges)-2 else (truth[:,j]<=hi))
               for i,(lo,hi) in enumerate(zip(edges[:-1],edges[1:]))]
        if not np.array_equal(np.sum(group,axis=0),np.ones(500,int)):raise ValueError('Truth bins do not partition all500')
        bins.append(group)
    for i,m in enumerate(bins[0]):masks.append(('u',i,-1,m))
    for j,m in enumerate(bins[1]):masks.append(('gamma',-1,j,m))
    for i,a in enumerate(bins[0]):
        for j,b in enumerate(bins[1]):masks.append(('u_x_gamma',i,j,a&b))
    if any(not np.any(m) for _,_,_,m in masks):raise ValueError('Empty specified bin: report separately before summarizing')
    return masks


def figures(out,design,delta_q,delta_width,rows):
    os.environ.setdefault('MPLCONFIGDIR',str(out/'matplotlib_cache'))
    os.environ.setdefault('XDG_CACHE_HOME',str(out/'font_cache'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,
      'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'pdf.fonttype':42,
      'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
    colors=['#075781','#c25c31','#527f50']
    labels=[r'$A_{\rm CN}-A0_{\rm CN}$',r'$B_{\rm CN}-A_{\rm CN}$',r'$B_{\rm G}-A_{\rm G}$']
    params=[r'$u$',r'$\log_{10}A_{\rm GW}$',r'$\gamma_{\rm GW}$',r'$\log_{10}A_{\rm r}$',r'$\log_{10}{\rm EFAC}$']
    fig,axes=plt.subplots(5,2,figsize=(7.1,9.1),gridspec_kw={'width_ratios':[2.3,1]})
    fig.subplots_adjust(left=.13,right=.98,top=.885,bottom=.085,wspace=.35,hspace=.48)
    for j in range(5):
        for ax in axes[j]:ax.axhline(0,color='#9ca1a8',lw=.7);ax.grid(axis='y',alpha=.2)
        for c in range(3):
            x=np.arange(4)+(c-1)*.06
            axes[j,0].plot(x,delta_q[c,:,j,:].mean(0),'o-',ms=3.3,lw=1,color=colors[c])
            axes[j,0].plot(x,np.median(delta_q[c,:,j,:],axis=0),'x',ms=4,color=colors[c])
            axes[j,1].bar(c,delta_width[c,:,j].mean(),color=colors[c],width=.58,alpha=.72)
            axes[j,1].plot(c,np.median(delta_width[c,:,j]),'x',color='#20252b',ms=5)
        axes[j,0].set_xticks(range(4),['Q05','Q50','Q90','Q95']);axes[j,1].set_xticks(range(3),['1','2','3'])
        axes[j,0].set_ylabel(params[j]+'\n'+r'$\Delta$/largura da priori')
    axes[0,0].set_title('Quantis: média (●) e mediana (×)')
    axes[0,1].set_title('Largura Q95−Q05')
    axes[-1,1].set_xlabel('Contraste 1 / 2 / 3')
    handles=[Line2D([0],[0],color=c,lw=1.6,label=f'{i+1}: '+l) for i,(c,l) in enumerate(zip(colors,labels))]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.54,.958),ncol=3,frameon=False,fontsize=8)
    fig.suptitle('Diferenças pareadas nas 500 realizações publicadas',y=.992,fontsize=11)
    fig.text(.5,.022,'Todos os casos são retidos, inclusive pendências numéricas.\nMédias/medianas descritivas: sem intervalo de confiança ou precisão horizontal certificada.',ha='center',fontsize=8,color='#444b52')
    products=[]
    for ext in ['pdf','svg','png']:
        p=out/('paired_quantiles_widths.'+ext)
        fig.savefig(p,dpi=150,metadata={'Creator':'C08 descriptive existing C07 results'} if ext=='pdf' else None)
        products.append(p)
    plt.close(fig)
    grids=np.empty((2,3,2,3));counts=np.empty((2,3),int)
    for row in rows:
        if row['group']!='u_x_gamma' or row['parameter']!='u':continue
        metric=0 if row['quantity']=='quantile' and row['probability']==.95 else 1 if row['quantity']=='central90_width' else None
        if metric is None:continue
        grids[metric,row['contrast_index'],row['gamma_bin'],row['u_bin']]=row['mean']
        counts[row['gamma_bin'],row['u_bin']]=row['n']
    vmax=float(np.max(abs(grids)))
    fig,axes=plt.subplots(2,3,figsize=(7.1,4.8),sharex=True,sharey=True)
    fig.subplots_adjust(left=.115,right=.88,bottom=.19,top=.87,wspace=.15,hspace=.38)
    for metric in range(2):
        for c in range(3):
            ax=axes[metric,c];im=ax.imshow(grids[metric,c],origin='lower',cmap='RdBu_r',vmin=-vmax,vmax=vmax,aspect='auto')
            for j in range(2):
                for i in range(3):
                    value=grids[metric,c,j,i]
                    ax.text(i,j,f'{value:+.3f}\nn={counts[j,i]}',ha='center',va='center',fontsize=8,
                        color='white' if abs(value)>.65*vmax else '#242a30')
            ax.set_title(labels[c],fontsize=9)
            ax.set_xticks(range(3),['[0;.5)','[.5;.9)','[.9;1]'])
            ax.set_yticks(range(2),['[3;4.25)','[4.25;5.5]'])
            if metric==1:ax.set_xlabel(r'$u_{\rm verdadeiro}$')
            if c==0:ax.set_ylabel(('ΔQ95 de u' if metric==0 else 'Δlargura90 de u')+'\n'+r'$\gamma_{\rm verdadeiro}$')
    cax=fig.add_axes([.91,.255,.025,.535]);fig.colorbar(im,cax=cax,label='Média / largura da priori de u')
    fig.suptitle('Descrição por bins fixos da verdade: todos os 500 casos',y=.985,fontsize=11)
    fig.text(.5,.037,'Cores e números: médias empíricas das diferenças, nova análise − anterior.\nOs bins não filtram guardas numéricas; não são testes de viés ou equivalência.',ha='center',fontsize=8,color='#444b52')
    for ext in ['pdf','svg','png']:
        p=out/('paired_mass_bins.'+ext);fig.savefig(p,dpi=150);products.append(p)
    plt.close(fig)
    return products


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repository',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();out=args.output
    if out.exists():raise FileExistsError('Use a new output directory; existing description remains immutable')
    design_path=Path(__file__).with_name('design.json');design=read(design_path)
    summary,a,provenance=load_c07_results(args.repository)
    masks=masks_for(a['truth'],design)
    contrasts=design['contrasts_new_minus_old'];q=a['quantiles_unit'];widths=q[...,3]-q[...,0]
    dq=np.stack([q[MODELS.index(new)]-q[MODELS.index(old)] for new,old in contrasts])
    dw=np.stack([widths[MODELS.index(new)]-widths[MODELS.index(old)] for new,old in contrasts])
    rows=[];points=[];pairguards=[]
    for c,(new,old) in enumerate(contrasts):
        ni,oi=MODELS.index(new),MODELS.index(old)
        cuts=a['cut_precision_pass'][ni]&a['cut_precision_pass'][oi]
        resolved=a['resolved'][ni]&a['resolved'][oi]
        for datum in range(500):
            row=dict(contrast_index=c,new_model=new,old_model=old,datum=datum,truth_u=float(a['truth'][datum,0]),truth_gamma=float(a['truth'][datum,2]),
                both_all6_PIT_functions_resolved=bool(resolved[datum].all()),both_all20_LOW_cut_CDF_precision=bool(cuts[datum].all()))
            for j,name in enumerate(PARAMETERS):
                for k,prob in enumerate(a['probabilities']):row[f'delta_{name}_Q{int(round(prob*100)):02d}']=float(dq[c,datum,j,k])
                row[f'delta_{name}_width90']=float(dw[c,datum,j])
            points.append(row)
        for group,ubin,gbin,mask in masks:
            for j,name in enumerate(PARAMETERS):
                for k in range(5):
                    value=dq[c,mask,j,k] if k<4 else dw[c,mask,j]
                    precision=cuts[mask,j,k] if k<4 else cuts[mask,j,0]&cuts[mask,j,3]
                    rows.append(dict(contrast_index=c,new_model=new,old_model=old,group=group,u_bin=ubin,gamma_bin=gbin,
                        parameter=name,quantity='quantile' if k<4 else 'central90_width',probability=float(a['probabilities'][k]) if k<4 else None,
                        units='fraction_prior_width',**describe(value),
                        both_parameter_PIT_functions_resolved=int(resolved[mask,j].sum()),
                        both_LOW_cut_CDF_precision=int(precision.sum()),all_bin_datasets_retained=True))
            pairguards.append(dict(contrast_index=c,new_model=new,old_model=old,group=group,u_bin=ubin,gamma_bin=gbin,n=int(mask.sum()),
                both_resolved_PIT_by_function=np.sum(resolved[mask],axis=0).tolist(),both_all6_resolved=int(np.all(resolved[mask],axis=1).sum()),
                both_LOW_cut_CDF_precision=np.sum(cuts[mask],axis=0).tolist(),both_all20_LOW_cut_CDF_precision=int(np.all(cuts[mask],axis=(1,2)).sum()),
                maximum_saved_high_weight=float(max(a['maximum_weight'][ni,mask].max(),a['maximum_weight'][oi,mask].max())),
                minimum_saved_high_ESS=float(min(a['weight_ess'][ni,mask].min(),a['weight_ess'][oi,mask].min())) ))
    modelguards=[]
    for mi,model in enumerate(MODELS):
        modelguards.append(dict(model=model,n=500,resolved_PIT_by_function=a['resolved'][mi].sum(0).tolist(),
            all6_PIT_functions_resolved=int(a['resolved'][mi].all(1).sum()),LOW_cut_CDF_precision=a['cut_precision_pass'][mi].sum(0).tolist(),
            all20_LOW_cut_CDF_precision=int(a['cut_precision_pass'][mi].all((1,2)).sum()),
            high_ESS=describe(a['weight_ess'][mi]),high_maximum_weight=describe(a['maximum_weight'][mi])))
    out.mkdir(parents=True)
    csv_rows(out/'paired_values.csv',points);csv_rows(out/'descriptive_bins.csv',rows)
    np.savez(out/'paired_arrays.npz',delta_quantiles_unit=dq,delta_width90_unit=dw,truth=a['truth'],bounds=a['bounds'],
             probabilities=a['probabilities'],original_resolved=a['resolved'],original_cut_precision_pass=a['cut_precision_pass'])
    products=figures(out,design,dq,dw,rows)
    record=dict(schema='C08_C07_500_DESCRIPTIVE_SUMMARY_v1',status='COMPLETE_DESCRIPTION_PENDING_ROOT_REVIEW',design=design,
        design_sha256=sha(design_path),source_sha256={str(Path(__file__)):sha(__file__),str(Path(__file__).with_name('load_c07_results.py')):sha(Path(__file__).with_name('load_c07_results.py'))},
        provenance=provenance,counts=dict(original_targets=2500,original_datasets=500,contrasts=3,quantile_comparisons_per_pair=20,width_comparisons_per_pair=5,
            groupings=len(masks),aggregate_rows=len(rows),paired_rows=len(points),numerically_filtered_out=0),
        group_counts=[dict(group=g,u_bin=u,gamma_bin=gamma,n=int(m.sum())) for g,u,gamma,m in masks],
        all500=[r for r in rows if r['group']=='all500'],model_guards=modelguards,paired_guards=pairguards,
        guard_scope='PIT resolution by function and CDF precision at independent LOW-selected cuts are inherited, not horizontal quantile bounds or full target approval.',
        no_small_shift_or_equivalence_decision=True,no_confidence_intervals=True,no_new_hypothesis_tests=True,
        new_ORF=0,new_likelihood_values=0,new_Monte_Carlo_draws=0,posterior_raw_arrays_read=False,
        products={p.name:dict(sha256=sha(p),bytes=p.stat().st_size) for p in products+[out/'paired_values.csv',out/'descriptive_bins.csv',out/'paired_arrays.npz']},
        CPU_seconds_including_imports=time.process_time(),RSS_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(out/'summary.json',record)
    print(json.dumps(dict(status=record['status'],counts=record['counts'],group_counts=record['group_counts'],CPU_seconds=record['CPU_seconds_including_imports'],RSS_peak_bytes=record['RSS_peak_bytes'])))


if __name__=='__main__':main()
