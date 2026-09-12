"""Run the archived C11 component suites used by the published experiment."""
from pathlib import Path
import os,subprocess,sys,unittest
ROOT=Path(__file__).resolve().parents[1]

class C11Components(unittest.TestCase):
    def run_suite(self,relative):
        source=ROOT/relative
        self.assertTrue(source.exists(),f'Restore C11 archives first: missing {relative}')
        env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
        result=subprocess.run([sys.executable,str(source),'-v'],cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    def test_pilot_and_exact_self_angle(self):self.run_suite('tmp/c11_pilot16_candidate_v2/test_candidate.py')
    def test_extended_generation(self):self.run_suite('tmp/c11_production_v1/test_generation.py')
    def test_functional_intervals(self):self.run_suite('tmp/c11_production_v1/test_functional.py')

if __name__=='__main__':unittest.main()
