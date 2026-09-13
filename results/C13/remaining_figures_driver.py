from pathlib import Path
import json,shutil,zipfile,subprocess,sys,hashlib
from PIL import Image,ImageChops
root=Path.cwd(); clean=Path('/private/tmp/tgwayne-c13-clean-20260913'); out=clean/'tmp/c13_remaining_figures';out.mkdir(exist_ok=True)
recovery=[]
name='tmp/c08_G0/c07_publication_resource_release.json'; archive=clean/'results/C08/campaign_archives/replay_v1/evidence_part000.zip'
with zipfile.ZipFile(archive) as z:
 data=z.read(name); target=clean/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);recovery.append(dict(path=name,archive=str(archive.relative_to(clean)),sha256=hashlib.sha256(data).hexdigest()))
# The paired renderer expects its published summary at the historical output path.
source=clean/'results/C08/paired32/summary.json'; target=clean/'tmp/c08_paired_synthesis_OUTPUT/summary.json';target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
recovery.append(dict(path=str(target.relative_to(clean)),source=str(source.relative_to(clean)),sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
# Current academic geometry renderer is a documented C13 derivative, not frozen C11 code.
shutil.copy2(root/'scripts/figura_geometria_dissertacao.py',clean/'scripts/figura_geometria_dissertacao.py');(clean/'results/C13').mkdir(exist_ok=True)
v2=clean/'results/C08/c07_descriptive/figures_v2'
if v2.exists() and not (out/'published_bins').exists():v2.rename(out/'published_bins')
jobs=[('results/C08/maps/source_snapshots/c08_weak_dispersion/plot_completed.py',['--summary','results/C08/maps/g2_weak/summary','--output',str(out/'weak')]),('results/C08/c07_descriptive/summarize.py',['--repository',str(clean),'--output',str(out/'descriptive')]),('results/C08/c07_descriptive/plot_mass_bins_v2.py',[]),('results/C08/paired32/render_mean_v2.py',[]),('docs/pausa_v0.8.5/figuras_analiticas.py',[]),('scripts/figura_geometria_dissertacao.py',[])]
runs=[]
for i,(worker,args) in enumerate(jobs):
 assert (root/worker).read_bytes()==(clean/worker).read_bytes()
 receipt=out/f'io_{i}.json'
 if receipt.exists():
  previous=json.loads(receipt.read_text());assert previous['failure'] is None;runs.append(previous);continue
 with (out/f'log_{i}.txt').open('w') as log:subprocess.run([sys.executable,str(root/'scripts/executar_isolado_c13.py'),'--original-root',str(root),'--clean-root',str(clean),'--receipt',str(receipt),worker,*args],stdout=log,stderr=subprocess.STDOUT,check=True)
 runs.append(json.loads(receipt.read_text())); print('Completed '+worker,flush=True)
pairs=[('figures/compressao/g2_fraca/g2_momentos.pdf',out/'weak/g2_momentos.pdf'),('figures/compressao/g2_fraca/expansao_fraca.pdf',out/'weak/expansao_fraca.pdf'),('figures/compressao/c07_descritivo/paired_quantiles_widths.pdf',out/'descriptive/paired_quantiles_widths.pdf'),('figures/compressao/c07_descritivo/paired_mass_bins.pdf',v2/'paired_mass_bins.pdf'),('figures/compressao/pareado32/u95_representative_mean.pdf',clean/'tmp/c08_synthesis_visual/mean_v2/u95_representative_mean.pdf'),('figures/robustez/prioris_suporte.pdf',clean/'docs/pausa_v0.8.5/figuras_analiticas_v1/prioris_suporte.pdf'),('figures/robustez/fisher_direcao.pdf',clean/'docs/pausa_v0.8.5/figuras_analiticas_v1/fisher_direcao.pdf'),('figures/aplicacao/geometria_academica.pdf',clean/'figures/aplicacao/geometria_academica.pdf')]
comparisons=[]
for i,(original,reproduced) in enumerate(pairs):
 imgs=[]
 for name,pdf in [('old',root/original),('new',reproduced)]:
  prefix=out/f'{i}_{name}';subprocess.run(['pdftoppm','-singlefile','-r','120','-png',str(pdf),str(prefix)],check=True,stderr=subprocess.PIPE);imgs.append(prefix.with_suffix('.png'))
 with Image.open(imgs[0]) as a,Image.open(imgs[1]) as b: passed=a.size==b.size and ImageChops.difference(a.convert('RGB'),b.convert('RGB')).getbbox() is None
 comparisons.append(dict(original=original,reproduced=str(reproduced.relative_to(clean)),passed=passed,original_sha256=hashlib.sha256((root/original).read_bytes()).hexdigest(),reproduced_sha256=hashlib.sha256(reproduced.read_bytes()).hexdigest()))
result=dict(scope='Regeneration from retained inputs; identical raster comparison at 120 dpi; not physical campaign replay.',recovery=recovery,runs=runs,comparisons=comparisons,passed=all(r['passed'] for r in comparisons))
(root/'results/C13/remaining_figures_replay.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],products=len(comparisons))))
