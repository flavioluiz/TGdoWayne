"""Check scientific external products actually read by the latest LaTeX build."""
from pathlib import Path
import argparse,hashlib,json,subprocess
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--clean-root',type=Path,required=True);a=p.parse_args();C=a.clean_root
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
fls=R/'tmp/latex/dissertacao/dissertacao.fls';inputs=set()
for line in fls.read_text().splitlines():
 if not line.startswith('INPUT '):continue
 path=Path(line[6:]);path=(R/'latex'/path).resolve() if not path.is_absolute() else path.resolve()
 try:rel=path.relative_to(R)
 except ValueError:continue
 if rel.parts[0] in ('figures','results') and path.suffix in ('.pdf','.tex'):inputs.add(str(rel))
old=json.loads((R/'results/C13/central_products_inventory.json').read_text())
known={r['artifact']:r for r in old['products']}
out=R/'tmp/c13_current_products';out.mkdir(exist_ok=True)
records=[]
for i,name in enumerate(sorted(inputs)):
 src=R/name;previous=known.get(name)
 row={'artifact':name,'sha256':sha(src)}
 if previous and previous['sha256']==sha(src) and previous['regeneration_comparison_passed']:
  row.update(passed=True,method='Unchanged bytes of a previously reproduced artifact',evidence='results/C13/central_products_inventory.json')
 else:
  other=C/name;assert other.is_file(),name
  row['reproduced_sha256']=sha(other)
  if src.suffix=='.pdf':
   images=[]
   for label,path in [('original',src),('reproduced',other)]:
    target=out/f'{i}_{label}'
    subprocess.run(['pdftoppm','-singlefile','-r','120','-png',str(path),str(target)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    images.append(np.asarray(Image.open(target.with_suffix('.png'))))
   row.update(passed=np.array_equal(*images),method='Independent regenerated PDF raster equality at 120 dpi')
  else:row.update(passed=src.read_bytes()==other.read_bytes(),method='Regenerated table byte equality')
 assert row['passed'],name
 records.append(row)
result={'passed':all(r['passed'] for r in records),'scope':'External scientific figures and table files actually opened by the latest LaTeX build; inline tables checked separately.','pdf_sha256':sha(R/'tmp/latex/dissertacao/dissertacao.pdf'),'latex_recorder_sha256':sha(fls),'products':records,'figures':sum(r['artifact'].endswith('.pdf') for r in records),'table_files':sum(r['artifact'].endswith('.tex') for r in records)}
(R/'results/C13/current_products_inventory.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='products'}))
