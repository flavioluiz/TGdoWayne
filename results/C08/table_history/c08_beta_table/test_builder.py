import json,tempfile,unittest
from pathlib import Path
import numpy as np
import beta_builder as b
from pta.orf import raw_direct_orf

class Tests(unittest.TestCase):
 def test_coordinates(self):
  for f in [b.beta_from_u,b.u_from_beta]:
   for bad in [[1j],[float('nan')],[-.1],[1.1],['0.5'],[True],.5]:
    with self.assertRaises(ValueError):f(bad)
   np.testing.assert_array_equal(f([0.,1.]),[1.,0.])
 def test_plan(self):
  plan=json.loads((b.HERE/'preflight_v2.json').read_text());v=np.array(plan['validation_nodes_u'])
  for r in plan['rows']:
   u,f,c=b.planned_nodes(r['channel'],v)
   self.assertEqual(len(u),r['validation_and_table_unique_evaluations'])
   self.assertTrue(np.isin(v,u).all());self.assertTrue(np.isin(c,f).all())
 def test_matrix_guards(self):
  g=np.eye(2,dtype=complex)[None];b.matrices(g,1,2)
  for bad in [g.real,g[:,0],g*np.nan,g*-1,g+np.array([[[0,1j],[0,0]]])]:
   with self.assertRaises(ValueError):b.matrices(bad,1,2)
 def test_atomic_no_overwrite(self):
  with tempfile.TemporaryDirectory(dir=b.HERE) as t:
   p=Path(t)/'x.json';b.write_json(p,{'a':1});before=p.read_bytes()
   with self.assertRaises(FileExistsError):b.write_json(p,{'a':2})
   self.assertEqual(before,p.read_bytes())
 def test_cache_guards(self):
  with tempfile.TemporaryDirectory(dir=b.HERE) as t:
   p=Path(t)/'x.npz';u=np.array([.5]);beta=b.beta_from_u(u);g=np.eye(2,dtype=complex)[None];record={'signature':'test','channel':2};r=record|{'Gamma_sha256':b.digest(g)}
   b.write_npz(p,u=u,beta=beta,Gamma=g,record=b.canonical(r));np.testing.assert_array_equal(g,b.read_chunk(p,record,u,beta,2))
   with self.assertRaises(RuntimeError):b.read_chunk(p,record|{'channel':3},u,beta,2)
   with self.assertRaises(RuntimeError):b.read_chunk(p,record,u+.1,beta,2)
   for n,bad in enumerate([g*np.nan,g*-1,g*2]):
    pp=Path(t)/f'bad{n}.npz';b.write_npz(pp,u=u,beta=beta,Gamma=bad,record=b.canonical(r))
    with self.assertRaises((RuntimeError,ValueError)):b.read_chunk(pp,record,u,beta,2)
 def test_ledger(self):
  with tempfile.TemporaryDirectory(dir=b.HERE) as t:
   p=Path(t)/'ledger';l=b.Ledger(p,{'real':10},'abc');l.charge('real',7,{});l=b.Ledger(p,{'real':10},'abc');self.assertEqual(l.totals['real'],7)
   with self.assertRaises(RuntimeError):l.charge('real',4,{})
   with self.assertRaises(RuntimeError):b.Ledger(p,{'real':10},'wrong')
   for v in [True,-1,0,1.1]:
    with self.assertRaises(ValueError):b.scalar_int(v,'amount')
 def test_small_independent_sky(self):
  p=np.array([[0.,0.,1.],[.8,0,.6]]);y=np.array([3.,7.]);basis=b.RealHarmonicBasis(p,lmax=48,nmu=100,budget=b.TableBudget(10**7,10**7,8),planned_batch=3)
  vals=basis.evaluate(np.array([0.,.4,1.]),y)
  for i,beta in enumerate([0.,.4,1.]):
   expected=raw_direct_orf(beta,.6,*y,nmu=90,nphi=180)
   self.assertLess(abs(vals[i,0,1]-expected),1e-12)
if __name__=='__main__':unittest.main(verbosity=2)
