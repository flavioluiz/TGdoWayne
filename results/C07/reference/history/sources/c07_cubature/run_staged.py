from pathlib import Path
import runpy,sys
here=Path(__file__).resolve().parent;root=here.parents[1]
for p in [root/'src',root/'tmp/c07_integration/src',root/'tmp/c07_efficiency',root/'tmp/c07_scale',here]:sys.path.insert(0,str(p))
import pta
pta.__path__.insert(0,str(root/'tmp/c06_integration/src/pta'))
p=sys.argv[1];sys.argv=[p,*sys.argv[2:]];runpy.run_path(p,run_name='__main__')
