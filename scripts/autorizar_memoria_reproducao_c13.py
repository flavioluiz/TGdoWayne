"""Record a reproduction-only RSS allowance without changing scientific parameters."""
from pathlib import Path
import argparse,hashlib,json
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--clean-root',type=Path,required=True);a=p.parse_args();root=a.clean_root.resolve()
config=root/'configs/application/c11_production_design.json';approval=root/'tmp/c11_production_v1/approval.json'
original=config.read_bytes();c=json.loads(original);oldsha=hashlib.sha256(original).hexdigest()
assert oldsha=='3a4291d51754ccbdd79261596cab03d5638a41a7921985ce301df0a610e15baf'
new=dict(c);new['RSS_bytes_candidate']=3*1024**3
assert [k for k in c if c[k]!=new[k]]==['RSS_bytes_candidate']
record=dict(original_config_sha256=oldsha,changed_fields={'RSS_bytes_candidate':{'before':c['RSS_bytes_candidate'],'after':new['RSS_bytes_candidate']}},reason='Isolated replay exceeded the 2 GiB RSS cap with the I/O audit attached; numerical formulas, sources, seeds, population, grids and tolerances are unchanged.')
config.write_text(json.dumps(new,indent=2)+'\n');record['reproduction_config_sha256']=hashlib.sha256(config.read_bytes()).hexdigest()
app=json.loads(approval.read_text());assert app['config_sha256']==oldsha
app['config_sha256']=record['reproduction_config_sha256'];app['reproduction_only']=record
out=root/'c13_population_approval.json'
with out.open('x') as f:json.dump(app,f,indent=2);f.write('\n')
with (root/'c13_memory_allowance.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(record))
