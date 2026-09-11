"""Summarize a fully closed finite C08 distributional map, never a prefix."""
from pathlib import Path
import argparse,csv,hashlib,json,os,resource,sys
os.environ['MPLCONFIGDIR']=str(Path(__file__).resolve().parents[1]/'matplotlib')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def require(condition,message):
    if not condition:raise ValueError(message)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=args.campaign
    complete=json.loads((root/'complete.json').read_text())
    require(complete['status']=='FINITE_DISTRIBUTIONAL_MAP_GATES_PASS_NOT_POSTERIORS','Only complete passed map')
    require(not (root/'failure.json').exists(),'Failure in campaign')
    require(len(complete['workers'])==43,'All 43 workers required')
    for record in complete['workers']:
        report=root/record['name']/'report.json'
        require(sha(report)==record['report_sha256'],'Worker report altered')
        if 'arrays_sha256' in record:
            require(sha(report.parent/'arrays.npz')==record['arrays_sha256'],'Worker arrays altered')
    report=json.loads((root/'moments_00/report.json').read_text())
    require(report['passed'] is True and report['moment_evaluations_all_resolutions']==4320 and report['unique_moment_cases']==1440,'Moment map incomplete')
    require(report['independent_real_reference_cases']==72,'Missing independent moment references')
    with np.load(root/'moments_00/arrays.npz',allow_pickle=False) as package:
        arrays={key:package[key] for key in package.files}
    require(sum(a.nbytes for a in arrays.values())<64*1024**2,'Summary array budget exceeded')
    require(all(np.isfinite(a).all() for a in arrays.values()),'Nonfinite map output')
    comparison=arrays['comparisons'];wrong=arrays['wrong_compression']
    require(comparison.shape==(4320,10) and wrong.shape==(1440,6),'Unexpected map dimensions')
    require(np.all(comparison[:,7:]>=0),'Negative normal discrepancy metric')
    fine=comparison[comparison[:,4]==2]
    require(len(fine)==1440,'Fine comparison map incomplete')
    Ts=[4.5,9.,15.];us=[0.,.2,.5,.8,.995];pairs=[(0,1),(0,2),(1,2)]
    windows=['Retangular periódica','Hann projetada'];names=['B','C_beta','C_full']
    columns=['KL_p_to_q','mean_shift_metric_p_squared','covariance_difference_metric_q']
    rows=[]
    for T in Ts:
        for window in range(2):
            for u in us:
                for p,q in pairs:
                    selected=fine[(fine[:,0]==T)&(fine[:,1]==u)&(fine[:,3]==window)&(fine[:,5]==p)&(fine[:,6]==q)]
                    require(len(selected)==16 and sorted(selected[:,2].tolist())==list(range(16)),'Missing or duplicate nuisance vertex')
                    row=dict(T_years=T,u=u,window=window,p=names[p],q=names[q],nuisance_vertices=16)
                    for j,key in enumerate(columns):
                        values=selected[:,7+j]
                        row[key+'_minimum']=float(values.min());row[key+'_maximum']=float(values.max())
                        row[key+'_argmax_eta']=int(selected[np.argmax(values),2])
                    rows.append(row)
    args.output.mkdir(parents=True,exist_ok=False)
    with (args.output/'envelopes.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,'axes.titlesize':9,'legend.fontsize':7,'svg.fonttype':'none','pdf.fonttype':42})
    colors=['#176B9C','#BC4B26','#63529C']
    labels=[r'$B\to C_\beta$',r'$B\to C_{\rm full}$',r'$C_\beta\to C_{\rm full}$']
    definitions=[('KL_p_to_q','Divergência KL (normal real)',False),('mean_shift_metric_p_squared','Deslocamento da média (desvios padrão)',True),('covariance_difference_metric_q','Diferença de covariância (Frobenius)',False)]
    for metric,title,sqrt in definitions:
        fig,axes=plt.subplots(3,2,figsize=(6.3,7.3),sharex=True)
        for ti,T in enumerate(Ts):
            for wi in range(2):
                ax=axes[ti,wi]
                for pi,(p,q) in enumerate(pairs):
                    vals=[r for r in rows if r['T_years']==T and r['window']==wi and r['p']==names[p] and r['q']==names[q]]
                    lo=np.array([r[metric+'_minimum'] for r in vals]);hi=np.array([r[metric+'_maximum'] for r in vals])
                    if sqrt:lo=np.sqrt(lo);hi=np.sqrt(hi)
                    ax.fill_between(us,lo,hi,color=colors[pi],alpha=.12,linewidth=0)
                    ax.plot(us,hi,'o-',color=colors[pi],ms=3,lw=1,label=labels[pi])
                ax.set_yscale('symlog',linthresh=1e-8,linscale=.5)
                ax.set_title(f'{windows[wi]} · T = {T:g} anos')
                ax.grid(alpha=.2,which='both');ax.set_xlim(-.02,1.015)
                if ti==2:ax.set_xlabel(r'$u=f_g T$')
                if wi==0:ax.set_ylabel('Envelope nos 16 vértices')
        handles,legend=axes[0,0].get_legend_handles_labels()
        fig.suptitle(title,y=.99,fontsize=11)
        fig.legend(handles,legend,loc='upper center',bbox_to_anchor=(.5,.958),ncol=3,frameon=False)
        fig.text(.5,.015,'Linha: máximo; faixa: mínimo–máximo. Escala linear até 10⁻⁸ e logarítmica acima.\nVértices fixos dos parâmetros de ruído e espectro; não são intervalos de confiança.',ha='center',fontsize=7)
        fig.tight_layout(rect=(0,.065,1,.915),h_pad=1.5)
        for ext in ['pdf','svg']:fig.savefig(args.output/(metric+'.'+ext))
        plt.close(fig)
    zero=fine[fine[:,1]==0]
    zero_beta=zero[(zero[:,5]==0)&(zero[:,6]==1)]
    require(np.all(zero_beta[:,7:]==0),'At u=0 B and C_beta must match exactly')
    summary=dict(scope='FINITE_DURATION_WINDOW_DISTRIBUTIONAL_MAP_NOT_POSTERIOR_OR_SBC',
        complete_sha256=sha(root/'complete.json'),moment_report_sha256=sha(root/'moments_00/report.json'),
        arrays_sha256=sha(root/'moments_00/arrays.npz'),writer_sha256=sha(__file__),
        finite_moment_cases=1440,finite_comparison_cases=1440,independent_real_references=72,
        nuisance_grid='16 Cartesian boundary vertices; no probabilistic weighting',
        KL_scope='between real normal distributions defined by quadratic means/covariances; not the full CN-induced quadratic law',
        mean_shift_scope='sqrt((mu_p-mu_q)^T Sigma_p^-1 (mu_p-mu_q))',
        covariance_scope='Frobenius norm of Sigma_q^-1/2 Sigma_p Sigma_q^-1/2 - I',
        duration_scope='u fixed across T implies different physical graviton mass; weights and physical normalization recomputed at each T',
        windows_scope='finite complex-linear positive-mode projection, proper CN, independent input frequencies; no irregular TOA or timing fit',
        B_C_beta_u0_exact=True,
        wrong_cross_frequency_omission={windows[i]:dict(maximum_relative_Frobenius=float(wrong[wrong[:,3]==i,5].max()),minimum_relative_Frobenius=float(wrong[wrong[:,3]==i,5].min())) for i in range(2)},
        global_maxima={key:float(fine[:,7+j].max()) for j,key in enumerate(columns)},
        products={p.name:sha(p) for p in sorted(args.output.iterdir()) if p.is_file()})
    with (args.output/'summary.json').open('x') as stream:json.dump(summary,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status='COMPLETE_FINITE_MAP_SUMMARIZED',rows=len(rows),products=len(summary['products']),summary_sha256=sha(args.output/'summary.json'))))


if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_CPU,(59,60))
    main()
