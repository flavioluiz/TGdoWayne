"""Selected frozen A0 d14 reference. Explicit subcommands prevent implicit campaigns."""
import argparse,runpy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['cubature','truncated','anisotropic','quantiles','export'])
    a,remaining=p.parse_known_args()
    modules={'cubature':'reference_cubature','truncated':'reference_truncated','anisotropic':'reference_anisotropic','quantiles':'reference_quantiles','export':'reference_export'}
    target='inference.'+modules[a.stage];sys.argv=[target]+remaining
    runpy.run_module(target,run_name='__main__')
if __name__=='__main__':main()
