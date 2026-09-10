"""Cinemática simbólica: convenções e cinemática linear, não dinâmica completa.

Requer SymPy 1.14.0. Unidades geométricas c=1; omega != 0, k real.
R^a_bcd = partial_c Gamma^a_db - partial_d Gamma^a_cb a primeira ordem.
"""
from itertools import product
import sympy as s

PAIRS = [(a,b) for a in range(4) for b in range(a,4)]
ETA = s.diag(1,-1,-1,-1)
OMEGA, K = s.symbols('omega k', real=True)
A, D, B, C, VX, VY = s.symbols('A D B C Vx Vy', real=True)
DELTA = OMEGA**2-K**2
SIGMA = OMEGA**2+K**2
Q = s.Matrix([-OMEGA,0,0,K])


def symmetric(values):
    h = s.zeros(4)
    for (a,b),value in zip(PAIRS, values):
        h[a,b] = h[b,a] = value
    return h


def riemann(h, q=Q):
    return {(a,b,c,d): s.expand((-q[b]*q[c]*h[a,d]-q[a]*q[d]*h[b,c]
             +q[b]*q[d]*h[a,c]+q[a]*q[c]*h[b,d])/2)
            for a,b,c,d in product(range(4), repeat=4)}


def riemann_from_connection(h, q=Q):
    """Rota independente pelo símbolo de Christoffel linearizado."""
    connection = {(a,b,c): s.I*sum(ETA[a,r]*(q[b]*h[r,c]+q[c]*h[r,b]-q[r]*h[b,c])
                    for r in range(4))/2 for a,b,c in product(range(4),repeat=3)}
    return {(a,b,c,d): s.expand(sum(ETA[a,r]*s.I*(q[c]*connection[r,d,b]
                     -q[d]*connection[r,c,b]) for r in range(4)))
            for a,b,c,d in product(range(4),repeat=4)}


def tidal(h):
    r = riemann(h)
    return s.Matrix(3,3,lambda i,j:s.factor(r[0,i+1,0,j+1]))


def constraint_vector(h, model):
    tr = s.trace(ETA*h)
    div = h.T*ETA*Q
    if model == 'Visser':
        return div-Q*tr/2
    if model == 'FP':
        return div.col_join(s.Matrix([tr]))
    raise ValueError(model)


def visser_amplitude():
    return s.Matrix([[A,-K/OMEGA*VX,-K/OMEGA*VY,-OMEGA*K/SIGMA*(A+D)],
        [-K/OMEGA*VX,-B-DELTA/SIGMA*(A+D),C,VX],
        [-K/OMEGA*VY,C,B,VY],
        [-OMEGA*K/SIGMA*(A+D),VX,VY,D]])


def fp_amplitude():
    return s.simplify(visser_amplitude().subs(A,K**2/OMEGA**2*D))


def tidal_coordinates(h):
    e=tidal(h)
    return s.Matrix([e[0,0]+e[1,1],e[2,2],e[0,0]-e[1,1],e[0,1],e[0,2],e[1,2]])


def tg_psi4():
    """Transcrição literal da Eq. (5.60), em A do APÊNDICE (h covariante)."""
    w,k=OMEGA,K
    return (4*s.I*C*k**2*w**2+4*s.I*C*w*k**3+4*s.I*C*w**3*k-D*w**4
         +A*k**4-4*k**2*B*w**2+2*k**3*w*A-4*k**3*w*B+2*k**3*w*D
         -2*k*w**3*A-4*k*w**3*B-2*k*w**3*D+2*s.I*C*k**4
         +2*s.I*C*w**4-2*k**4*B+k**4*D-2*B*w**4-w**4*A)/(8*(w**2+k**2))


def tetrad_contraction(r, a,b,c,d):
    return s.factor(sum(a[i]*b[j]*c[k]*d[l]*r[i,j,k,l]
                for i,j,k,l in product(range(4),repeat=4)))


def expressions():
    hv,hf=visser_amplitude(),fp_amplitude()
    return {'h_Visser':str(hv),'h_FP':str(hf),'E_Visser':str(tidal(hv)),
            'E_FP':str(tidal(hf)),'psi4_TG_factorized':str(s.factor(tg_psi4())),
            'scalar_ratio_FP':str(s.factor(tidal_coordinates(hf)[1]/tidal_coordinates(hf)[0]))}
