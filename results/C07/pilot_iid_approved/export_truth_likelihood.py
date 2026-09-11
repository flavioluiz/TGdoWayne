"""Truth thresholds from the same frozen likelihood used for new IID production."""
from pathlib import Path
import hashlib,json
import numpy as np
from run_iid import (ROOT,HERE,RESULTS,CONFIG,DATA,TABLE,TARGETS,experiment,EvenThresholdCubicORF,CubicPointLikelihood,forward_substitution,Likelihood)

def main():
    target=RESULTS/'truth_likelihood.json'
    if target.exists():raise FileExistsError('Preserve existing truth thresholds.')
    source=json.loads((HERE/'source_manifest.json').read_text())
    if not all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==digest for p,digest in source.items()):raise RuntimeError('A production input/source changed.')
    cfg=json.loads(CONFIG.read_text());e=experiment(cfg)
    with np.load(DATA,allow_pickle=False) as p:data={k:p[k].copy() for k in p.files}
    with np.load(TABLE,allow_pickle=False) as p:table=EvenThresholdCubicORF(p['nodes'],p['matrices'],coordinate='beta')
    lk=CubicPointLikelihood(e,data,table);lk.solve=forward_substitution
    truth=data['truth'][TARGETS%len(data['q'])];values=lk(truth,TARGETS)
    ref=Likelihood(e,data['q'],data['x_physical'],data['x_gaussian'])
    reference=np.array([ref(t[None,1:],table(np.array([t[0]]))[0])[0,k] for t,k in zip(truth,TARGETS)])
    difference=float(np.max(abs(values-reference)))
    if difference>1e-7:raise AssertionError('Point/reference kernel mismatch at truth.')
    out=dict(targets=TARGETS.tolist(),truth_log_likelihood=values.tolist(),truth_physical=truth.tolist(),
             table_sha256=hashlib.sha256(TABLE.read_bytes()).hexdigest(),data_sha256=hashlib.sha256(DATA.read_bytes()).hexdigest(),
             source_sha256=source,export_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             maximum_reference_logL_difference=difference,
             scope='Same beta-interpolated ORF8336 and pointwise kernel as IID production; table independently validated in the stated test domain. Truth used only as a diagnostic threshold.')
    target.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'file':str(target),'maximum_reference_logL_difference':difference},indent=2))
if __name__=='__main__':main()
