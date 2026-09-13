from pathlib import Path
import importlib.util,runpy,sys
root=Path.cwd()
package=root/'tmp/c13_c07_frozen_namespace/pta'
spec=importlib.util.spec_from_file_location('pta',package/'__init__.py',submodule_search_locations=[str(package)])
module=importlib.util.module_from_spec(spec);sys.modules['pta']=module;spec.loader.exec_module(module)
runpy.run_path(str(root/'scripts/run_calibration_campaign.py'),run_name='__main__')
