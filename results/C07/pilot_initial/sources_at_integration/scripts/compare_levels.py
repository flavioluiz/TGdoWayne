"""Per-realization numerical diagnostics, never turn N=16 into SBC acceptance."""
from pathlib import Path
import json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]


def main():
    cfg=json.loads((ROOT/'config.json').read_text());p=ROOT/'results';width=np.diff(cfg['prior']['bounds'],axis=1).ravel()
    pairs=[('coarse','mass_refinement'),('mass_refinement','nuisance_refinement'),('nuisance_refinement','independent_scrambles'),('nuisance_refinement','endpoint_65_11'),('endpoint_65_11','endpoint_129_11'),('endpoint_129_11','endpoint_129_13'),('endpoint_129_13','endpoint_129_13_independent')]
    records=[]
    for left,right in pairs:
        if not (p/(left+'.json')).exists() or not (p/(right+'.json')).exists():continue
        a=json.loads((p/(left+'.json')).read_text());b=json.loads((p/(right+'.json')).read_text())
        dq=abs(np.array(a['quantiles'])-b['quantiles'])/width[None,None,:,None]
        dp=abs(np.array(a['pit'])-b['pit']);dz=abs(np.array(a['log_evidence'])-b['log_evidence'])
        ddep=abs(np.array(a['data_dependent_loglikelihood_pit'])-b['data_dependent_loglikelihood_pit'])
        model=[]
        for k,name in enumerate(a['methods']):
            model.append(dict(method=name,maximum_abs_logZ_difference=float(dz[k].max()),maximum_abs_pit_difference=float(dp[k].max()),maximum_data_dependent_pit_difference=float(ddep[k].max()),parameter_maximum_quantile_differences_fraction_prior_width=dq[k].max(axis=(0,2)).tolist(),failed_realizations_by_quantile=np.where(dq[k].max(axis=(1,2))>.001)[0].tolist(),failed_realizations_by_logZ=np.where(dz[k]>.001)[0].tolist(),failed_realizations_by_pit=np.where(dp[k].max(axis=1)>.002)[0].tolist()))
        records.append(dict(comparison=[left,right],models=model))
    levels=[]
    for f in sorted(p.glob('*.json')):
        v=json.loads(f.read_text())
        if 'level' not in v:continue
        levels.append(dict(name=v['level']['name'],seconds=v['wall_seconds'],parameter_points=v['parameter_points'],maximum_evidence_relative_se=float(np.max(v['evidence_relative_standard_error'])),minimum_nuisance_concentration_ess=float(np.min(v['nuisance_quadrature_weight_concentration_ess'])),maximum_nuisance_weight=float(np.max(v['maximum_nuisance_weight']))))
    out=dict(status='numerical_pilot_diagnostics_only; convergence evaluated per comparison, no SBC claim',n_realizations=16,parameters=cfg['parameters'],levels=levels,comparisons=records,sbc500_completed=False)
    (p/'comparison.json').write_text(json.dumps(out,indent=2)+'\n')
    for r in records:
        print(' / '.join(r['comparison']))
        for m in r['models']:print(m['method'],'dlogZ',f'{m["maximum_abs_logZ_difference"]:.4g}','dq/support',f'{max(m["parameter_maximum_quantile_differences_fraction_prior_width"]):.4g}','dPIT',f'{m["maximum_abs_pit_difference"]:.4g}','dLLPIT',f'{m["maximum_data_dependent_pit_difference"]:.4g}')


if __name__=='__main__':main()
