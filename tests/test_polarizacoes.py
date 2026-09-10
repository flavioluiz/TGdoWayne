import unittest
from itertools import product
import sympy as s
from polarizacoes.foundations import *


def zero(expr):
    if isinstance(expr,s.MatrixBase):
        return all(s.cancel(e)==0 for e in expr)
    return s.cancel(expr)==0


class GeneralIdentities(unittest.TestCase):
    def setUp(self):
        self.variables=s.symbols('h00 h01 h02 h03 h11 h12 h13 h22 h23 h33')
        self.h=symmetric(self.variables)

    def test_all_256_connection_components(self):
        formula, connection = riemann(self.h),riemann_from_connection(self.h)
        for index in formula:
            self.assertTrue(zero(formula[index]-connection[index]), index)

    def test_riemann_symmetries_and_bianchi_general(self):
        r=riemann(self.h)
        for a,b,c,d in product(range(4),repeat=4):
            self.assertTrue(zero(r[a,b,c,d]+r[b,a,c,d]))
            self.assertTrue(zero(r[a,b,c,d]+r[a,b,d,c]))
            self.assertTrue(zero(r[a,b,c,d]-r[c,d,a,b]))
            self.assertTrue(zero(r[a,b,c,d]+r[a,c,d,b]+r[a,d,b,c]))
        for a,b,c,d,e in product(range(4),repeat=5):
            self.assertTrue(zero(Q[e]*r[a,b,c,d]+Q[c]*r[a,b,d,e]+Q[d]*r[a,b,e,c]))

    def test_coordinate_perturbation_curvature_vanishes(self):
        xi=s.Matrix(s.symbols('xi0 xi1 xi2 xi3'))
        hg=Q*xi.T+xi*Q.T
        self.assertTrue(all(zero(e) for e in riemann(hg).values()))
        self.assertTrue(zero(constraint_vector(hg,'Visser')-DELTA*xi))
        self.assertTrue(zero(constraint_vector(hg,'FP')[:4,0]
                      - DELTA*xi - Q*(Q.T*ETA*xi)[0]))

    def test_regular_parameterizations_constraints(self):
        self.assertTrue(zero(constraint_vector(visser_amplitude(),'Visser')))
        self.assertTrue(zero(constraint_vector(fp_amplitude(),'FP')))
        # Independent construction: linear system constraints solved for eliminated h's.
        hv, hf=visser_amplitude(),fp_amplitude()
        eliminated_v=[self.variables[j] for j in [1,2,3,4]]
        sol_v=s.solve(list(constraint_vector(self.h,'Visser')),eliminated_v,dict=True)[0]
        base_subs={self.variables[j]:val for j,val in zip([0,5,6,7,8,9],[A,C,VX,B,VY,D])}
        reconstructed_v=self.h.subs(sol_v).subs(base_subs)
        self.assertTrue(zero(reconstructed_v-hv))
        eliminated_f=[self.variables[j] for j in [0,1,2,3,4]]
        sol_f=s.solve(list(constraint_vector(self.h,'FP')),eliminated_f,dict=True)[0]
        reconstructed_f=self.h.subs(sol_f).subs(base_subs)
        self.assertTrue(zero(reconstructed_f-hf))

    def test_constraint_rank_proofs(self):
        v=constraint_vector(self.h,'Visser').jacobian(self.variables)
        f=constraint_vector(self.h,'FP').jacobian(self.variables)
        # Nonzero minors for every real k and omega!=0 prove full row ranks 4 and 5.
        self.assertTrue(zero(v[:,[1,2,3,4]].det()+OMEGA**2*SIGMA/2))
        self.assertTrue(zero(f[:,[0,1,2,3,4]].det()+OMEGA**4))

    def test_tidal_closed_forms(self):
        hv,hf=visser_amplitude(),fp_amplitude()
        ev=tidal(hv)
        expected=s.Matrix([[OMEGA**2*(-B-DELTA/SIGMA*(A+D))/2,OMEGA**2*C/2,DELTA*VX/2],
             [OMEGA**2*C/2,OMEGA**2*B/2,DELTA*VY/2],
             [DELTA*VX/2,DELTA*VY/2,DELTA*(OMEGA**2*D-K**2*A)/(2*SIGMA)]])
        self.assertTrue(zero(ev-expected))
        self.assertTrue(zero(tidal(hf)-expected.subs(A,K**2/OMEGA**2*D)))

    def test_tidal_rank_by_minors_massive_and_null(self):
        mv=tidal_coordinates(visser_amplitude()).jacobian([A,D,B,C,VX,VY])
        mf=tidal_coordinates(fp_amplitude()).jacobian([B,C,VX,VY,D])
        self.assertTrue(zero(mv.det()-OMEGA**6*DELTA**4/(32*SIGMA)))
        # Rows pb, tensor difference, xy, xz, yz. Rank 5 for Delta!=0.
        self.assertTrue(zero(mf[[0,2,3,4,5],:].det()-OMEGA**4*DELTA**3/16))
        for matrix in [mv,mf]:
            null=matrix.subs(K,OMEGA)
            self.assertEqual(null.rank(),2)
            # Threshold k=0 retains full respective rank; no propagation direction preferred.
            self.assertEqual(matrix.subs(K,0).rank(),matrix.cols)

    def test_zero_fourvector_separate_domain(self):
        # Parameterizations exclude omega=0; direct tensors/constraints handle the exceptional point.
        self.assertTrue(zero(constraint_vector(self.h,'Visser').subs({OMEGA:0,K:0})))
        self.assertEqual(constraint_vector(self.h,'FP').subs({OMEGA:0,K:0}).jacobian(self.variables).rank(),1)
        self.assertTrue(zero(tidal(self.h).subs({OMEGA:0,K:0})))

    def test_fp_scalar_relation_including_nonuniform_limit(self):
        e=tidal(fp_amplitude())
        pb,pl=s.factor(e[0,0]+e[1,1]),s.factor(e[2,2])
        self.assertTrue(zero(pl+DELTA/OMEGA**2*pb))
        self.assertTrue(zero(pb+DELTA*D/2))
        self.assertTrue(zero(pl-DELTA**2*D/(2*OMEGA**2)))
        # Isotropic transverse helicity-zero family. D=-2omega²/Delta yields fixed breathing.
        normalized=fp_amplitude().subs({D:-2*OMEGA**2/DELTA,B:1,C:0,VX:0,VY:0})
        ens=tidal(normalized)
        self.assertTrue(zero(ens[0,0]-OMEGA**2/2))
        self.assertTrue(zero(ens[1,1]-OMEGA**2/2))
        self.assertTrue(zero(ens[2,2]+DELTA))
        self.assertEqual(s.limit(ens[0,0],K,OMEGA),OMEGA**2/2)

    def test_hyun_equation_330_independent_transcription(self):
        # Eq. (3.30), arXiv:1810.09316v1. Order (pb,pl,p+,pcross,px,py).
        hyun=s.Matrix([-s.Rational(1,2)*DELTA/SIGMA*OMEGA**2*(A+D),
            s.Rational(1,2)*DELTA/SIGMA*OMEGA**2*(A+D)-s.Rational(1,2)*DELTA*A,
            -s.Rational(1,2)*DELTA/SIGMA*OMEGA**2*(A+D)-OMEGA**2*B,
            s.Rational(1,2)*OMEGA**2*C,s.Rational(1,2)*DELTA*VX,s.Rational(1,2)*DELTA*VY])
        self.assertTrue(zero(tidal_coordinates(visser_amplitude())-hyun))

    def test_tg_equations_558_559_561(self):
        w,k=OMEGA,K
        literal2=-(k**2*w**2*A+k**2*w**2*D-A*k**4-D*w**4)/(12*SIGMA)
        literal3=-(s.I*VY*k**3-s.I*VY*k*w**2+VX*k**3-VX*w**2*k
                  -VX*w**3+s.I*VY*w*k**2-s.I*VY*w**3+VX*k**2*w)/(8*w)
        literal22=(A*k**4+k**4*D-w**4*A-D*w**4+2*k**3*w*A+2*k**3*w*D
                   -2*k*w**3*A-2*k*w**3*D)/(8*SIGMA)
        n=s.Matrix([1,0,0,-1])/s.sqrt(2)
        l=s.Matrix([1,0,0,1])/s.sqrt(2)
        m=s.Matrix([0,1,s.I,0])/s.sqrt(2)
        mb=s.conjugate(m)
        r=riemann(visser_amplitude())
        self.assertTrue(zero(literal2-tetrad_contraction(r,n,l,n,l)/6))
        self.assertTrue(zero(literal3-tetrad_contraction(r,n,l,n,m)/2))
        self.assertTrue(zero(literal22-tetrad_contraction(r,n,mb,n,m)))
        self.assertTrue(zero(literal2-DELTA*(w**2*D-k**2*A)/(12*SIGMA)))
        self.assertTrue(zero(literal3-DELTA*(w+k)*(VX+s.I*VY)/(8*w)))
        self.assertTrue(zero(literal22+DELTA*(w+k)**2*(A+D)/(8*SIGMA)))

    def test_tg_equation_560_from_contraction_and_null_calibration(self):
        # Choose complex transverse direction to match positive Im(Psi4) of TG.
        n=s.Matrix([1,0,0,-1])/s.sqrt(2)
        m=s.Matrix([0,1,s.I,0])/s.sqrt(2)
        contracted=tetrad_contraction(riemann(visser_amplitude()),n,m,n,m)
        # R_TG=-R_here; -R_TG(n,m,n,m)=R_here(n,m,n,m).
        self.assertTrue(zero(contracted-tg_psi4()))
        factored=(OMEGA+K)**2/8*(-2*B-DELTA/SIGMA*(A+D)+2*s.I*C)
        self.assertTrue(zero(tg_psi4()-factored))
        cross=s.expand_complex(tg_psi4().subs({A:0,D:0,B:0,C:1})).as_real_imag()[1]
        exact=OMEGA**2/2
        self.assertTrue(zero(cross/(2*exact)-(1+K/OMEGA)**2/4))
        self.assertEqual(s.limit(cross/(2*exact),K,OMEGA),1)
        self.assertEqual(s.simplify((cross/(2*exact)).subs(K,0)),s.Rational(1,4))


if __name__ == '__main__':
    unittest.main()
