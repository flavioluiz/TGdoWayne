"""Readable dissertation figures from unchanged population summaries."""
from pathlib import Path
import argparse, csv, hashlib, json, os, sys
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from inference.sbc_sensitivity import ecdf_envelope
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'tmp/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'figures/academicas')
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
        'axes.titlesize': 11, 'axes.labelsize': 10, 'xtick.labelsize': 10,
        'ytick.labelsize': 10, 'pdf.fonttype': 42, 'axes.spines.top': False,
        'axes.spines.right': False})
    sources = {}; plotted = {}; products = []
    def source(path):
        p = ROOT / path
        sources[path] = hashlib.sha256(p.read_bytes()).hexdigest()
        return p
    def save(fig, name):
        fig.savefig(out / (name + '.pdf'), metadata={'CreationDate': None, 'ModDate': None})
        fig.savefig(out / (name + '.png'), dpi=140)
        products.append(name)
        plt.close(fig)
    labels = [r'$u$', r'$\log_{10} A_{\rm GW}$', r'$\gamma_{\rm GW}$',
        r'$\log_{10} A_{\rm r}$', r'$\log_{10}\mathrm{EFAC}$', r'$\log L(\theta_{\rm true};d)$']
    models_math = {'A0_CN': r'$A_{0,\rm CN}$', 'A_CN': r'$A_{\rm CN}$',
        'B_CN': r'$B_{\rm CN}$', 'A_G': r'$A_{\rm G}$', 'B_G': r'$B_{\rm G}$'}
    s = json.loads(source('results/C07/synthesis/summary.json').read_text())
    p = source('results/C07/synthesis/arrays.npz')
    assert hashlib.sha256(p.read_bytes()).hexdigest() == s['arrays_sha256']
    with np.load(p) as data:
        grid = np.linspace(0, 1, 1001)
        for m, model in enumerate(s['models']):
            group = 'correct' if model in s['config']['families']['correct']['models'] else 'approximate'
            family = s['config']['families'][group]['hypotheses']
            n = s['simulations_per_model']
            eps = np.sqrt(np.log(2 * family / s['config']['scientific_alpha']) / (2 * n))
            fig, axes = plt.subplots(3, 2, figsize=(6.3, 6.8), sharex=True, sharey=True)
            fig.subplots_adjust(left=.12, right=.98, top=.93, bottom=.17, hspace=.43, wspace=.26)
            for j, ax in enumerate(axes.flat):
                nominal = np.searchsorted(np.sort(data['pit'][m, :, j]), grid, side='right') / n
                lo, hi = ecdf_envelope(data['pit_lower'][m, :, j], data['pit_upper'][m, :, j], grid)
                plotted[f'c07_{model}_{j}'] = np.array([grid, nominal, lo, hi])
                ax.fill_between(grid, np.maximum(0, grid-eps), np.minimum(1, grid+eps), color='#e6e7e9')
                ax.fill_between(grid, lo, hi, color='#197aab', alpha=.25, step='post')
                ax.plot(grid, grid, '--', color='#32383e', lw=.8)
                ax.step(grid, nominal, where='post', color='#075781', lw=1.3)
                ax.set(xlim=(0,1), ylim=(0,1), xticks=[0,.5,1], yticks=[0,.5,1], title=labels[j])
                if j % 2 == 0: ax.set_ylabel('CDF empírica')
                if j >= 4: ax.set_xlabel('PIT')
                ax.grid(alpha=.15)
            fig.suptitle(models_math[model], y=.985)
            fig.legend(handles=[Line2D([], [], color='#075781', label='CDF empírica'),
                Patch(color='#197aab', alpha=.25, label='Faixa numérica'),
                Line2D([], [], color='#32383e', ls='--', label='Uniforme'),
                Patch(color='#e6e7e9', label='Faixa DKW ideal')],
                loc='lower center', bbox_to_anchor=(.5,.015), ncol=2, frameon=False, fontsize=10)
            save(fig, 'ecdf_' + model)
    colors = ['#075781', '#c25c31', '#527f50']
    contrasts = [r'$A_{\rm CN}-A_{0,\rm CN}$', r'$B_{\rm CN}-A_{\rm CN}$', r'$B_{\rm G}-A_{\rm G}$']
    with np.load(source('results/C08/c07_descriptive/results/paired_arrays.npz')) as data:
        dq = data['delta_quantiles_unit']; dw = data['delta_width90_unit']
        assert dq.shape == (3,500,5,4) and dw.shape == (3,500,5)
        plotted['paired_quantile_mean'] = dq.mean(axis=1)
        plotted['paired_quantile_median'] = np.median(dq, axis=1)
        plotted['paired_width_mean'] = dw.mean(axis=1)
        plotted['paired_width_median'] = np.median(dw, axis=1)
        for name, indices in [('paired_quantiles', [0,1,2]), ('paired_noise', [3,4])]:
            fig, axes = plt.subplots(len(indices), 2, figsize=(6.3, 2.0*len(indices)+1.0), gridspec_kw={'width_ratios':[1.65,1]})
            fig.subplots_adjust(left=.16, right=.98, bottom=.13, top=.89, wspace=.38, hspace=.65)
            for row, j in enumerate(indices):
                for ax in axes[row]: ax.axhline(0, color='#999999', lw=.7); ax.grid(axis='y', alpha=.2)
                for c in range(3):
                    x = np.arange(4)+(c-1)*.06
                    axes[row,0].plot(x, dq[c,:,j,:].mean(0), 'o-', ms=4, color=colors[c])
                    axes[row,0].plot(x, np.median(dq[c,:,j,:], axis=0), 'x', ms=5, color=colors[c])
                    axes[row,1].bar(c, dw[c,:,j].mean(), color=colors[c], width=.58, alpha=.75)
                    axes[row,1].plot(c, np.median(dw[c,:,j]), 'x', color='black', ms=5)
                axes[row,0].set_xticks(range(4), ['05','50','90','95'])
                axes[row,1].set_xticks(range(3), ['1','2','3'])
                axes[row,0].set_ylabel(labels[j]+'\n'+r'$\Delta$/largura da priori')
            axes[0,0].set_title('Diferença de quantis')
            axes[0,1].set_title(r'Diferença de $W_{90}$')
            axes[-1,0].set_xlabel('Percentil (%)'); axes[-1,1].set_xlabel('Contraste')
            fig.legend(handles=[Line2D([],[],color=c,label=f'{i+1}: '+v) for i,(c,v) in enumerate(zip(colors,contrasts))], loc='upper center', ncol=3, frameon=False, fontsize=10)
            save(fig, name)
    grids = np.full((2,3,2,3), np.nan); counts = np.zeros((2,3), int)
    with source('results/C08/c07_descriptive/results/descriptive_bins.csv').open() as f:
        for row in csv.DictReader(f):
            if row['group'] != 'u_x_gamma' or row['parameter'] != 'u': continue
            metric = 0 if row['quantity'] == 'quantile' and float(row['probability']) == .95 else 1 if row['quantity'] == 'central90_width' else None
            if metric is None: continue
            c,j,i = [int(row[k]) for k in ('contrast_index','gamma_bin','u_bin')]
            grids[metric,c,j,i] = float(row['mean']); counts[j,i] = int(row['n'])
    assert np.isfinite(grids).all() and counts.sum() == 500
    plotted['paired_bins'] = grids; plotted['paired_bin_counts'] = counts
    vmax = np.abs(grids).max()
    fig, axes = plt.subplots(3,2,figsize=(6.3,7.4), sharex=True, sharey=True)
    fig.subplots_adjust(left=.18,right=.98,top=.90,bottom=.22,hspace=.45,wspace=.14)
    for c in range(3):
        for metric in range(2):
            ax=axes[c,metric]
            im=ax.imshow(grids[metric,c],origin='lower',cmap='RdBu_r',vmin=-vmax,vmax=vmax,aspect='auto')
            for j in range(2):
                for i in range(3):
                    value=grids[metric,c,j,i]
                    ax.text(i,j,f'{value:+.3f}',ha='center',va='center',fontsize=11,color='white' if abs(value)>.65*vmax else '#242a30')
            ax.set_title(contrasts[c],fontsize=11)
            ax.set_xticks(range(3), ['0–0,5','0,5–0,9','0,9–1'])
            ax.set_yticks(range(2), ['3–4,25','4,25–5,5'])
            if metric==0: ax.set_ylabel(r'$\gamma_{\rm GW}$')
            if c==2: ax.set_xlabel(r'$u$ verdadeiro')
    fig.text(.38,.965,r'$\langle\Delta Q_{95}(u)\rangle$',ha='center')
    fig.text(.79,.965,r'$\langle\Delta W_{90}(u)\rangle$',ha='center')
    cb=fig.add_axes([.22,.075,.70,.025]);fig.colorbar(im,cax=cb,orientation='horizontal',label='Diferença / largura da priori')
    save(fig,'paired_bins')
    with np.load(source('results/C10/population_synthesis/PITs.npz')) as data:
        grid=np.linspace(0,1,201)
        extent = 0.0
        for model in models_math:
            bounds = data[model+'_interval']
            for col in range(3):
                lo, hi = ecdf_envelope(bounds[:,col,0], bounds[:,col,1], grid)
                extent = max(extent, float(np.max(np.abs(lo-grid))), float(np.max(np.abs(hi-grid))))
        limit = np.ceil(extent*20)/20
        for name, models in [('scalar_reference',['A0_CN','A_G','B_G']),('scalar_approximation',['A_CN','B_CN'])]:
            fig, axes=plt.subplots(len(models),3,figsize=(6.3,2.1*len(models)+.6),sharex=True,sharey=True)
            fig.subplots_adjust(left=.15,right=.98,bottom=.12,top=.94,hspace=.32,wspace=.18)
            for row,model in enumerate(models):
                point=data[model+'_point'];bounds=data[model+'_interval']
                assert point.shape==(500,3)
                for col in range(3):
                    lo,hi=ecdf_envelope(bounds[:,col,0],bounds[:,col,1],grid)
                    nominal=np.searchsorted(np.sort(point[:,col]),grid,side='right')/500
                    plotted[f'scalar_{model}_{col}']=np.array([grid,nominal,lo,hi])
                    ax=axes[row,col]
                    ax.fill_between(grid,lo-grid,hi-grid,color='#197aab',alpha=.25)
                    ax.plot(grid,nominal-grid,color='#075781',lw=1.3)
                    ax.axhline(0,color='black',lw=.6);ax.grid(alpha=.15)
                    ax.set(xlim=(0,1),ylim=(-limit,limit),xticks=[0,.5,1],yticks=[-limit,0,limit])
                    if row==0: ax.set_title([r'$u$',r'$\epsilon$',r'$\log L(\theta_{\rm true};d)$'][col],fontsize=10)
                    if col==0: ax.set_ylabel(models_math[model]+'\n'+r'$\widehat F(t)-t$')
                    if row==len(models)-1:ax.set_xlabel('PIT, $t$')
            save(fig,name)
    audit=json.loads(source('results/C11/statistical_audit.json').read_text())
    models=['A0_CN','A_CN','B_CN','C_beta_CN','C_full_CN','A_G','B_G','C_beta_G','C_full_G']
    names=[r'$A_{0,\rm CN}$',r'$A_{\rm CN}$',r'$B_{\rm CN}$',r'$C_{\beta,\rm CN}$',r'$C_{\rm full,CN}$',r'$A_{\rm G}$',r'$B_{\rm G}$',r'$C_{\beta,\rm G}$',r'$C_{\rm full,G}$']
    fig,axes=plt.subplots(1,2,figsize=(6.3,5.6),sharey=True)
    fig.subplots_adjust(left=.15,right=.98,bottom=.16,top=.86,wspace=.23)
    y=np.arange(9)
    for population,offset,color,marker in [('P12K4',-.13,'#0072B2','o'),('P16K8',.13,'#D55E00','s')]:
        rows=[next(r for r in audit['prior_information'] if r['population']==population and r['model']==m) for m in models]
        numbers=np.array([[r['mean_KL_nats'],r['MCSE_mean_KL'],r['event_unresolved_prior']/500] for r in rows])
        plotted['population_information_'+population]=numbers
        axes[0].errorbar(numbers[:,0],y+offset,xerr=numbers[:,1],fmt=marker,color=color,capsize=2,label=population,ms=4)
        axes[1].scatter(numbers[:,2],y+offset,color=color,marker=marker,s=18)
    axes[0].set_yticks(y,names);axes[0].invert_yaxis();axes[0].set_xscale('log')
    axes[0].set_xlabel('KL média (nat)');axes[0].set_title('Informação sobre a massa')
    axes[1].set(xlim=(-.015,.4),xticks=[0,.2,.4],xlabel='Fração de eventos\nindeterminados',title='Precisão de log L')
    for ax in axes:ax.grid(axis='x',alpha=.2)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',ncol=2,frameon=False)
    save(fig,'population_information')
    np.savez(out/'plot_values.npz',**plotted)
    manifest={'sources':sources,'products':products,'all_500_cases_retained':True,'plotted_arrays':len(plotted),
        'description':'Presentation changes only; existing PIT envelopes and paired descriptive statistics retained.'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__ == '__main__': main()
