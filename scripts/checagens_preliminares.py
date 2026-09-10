#!/usr/bin/env python3
"""Checagens cinemáticas para a proposta de mestrado, sem dependências externas.

Não ajusta dados, não calcula ORFs e não demonstra estabilidade da ação.
Convenções: eta=(+---), c=1 no cálculo tensorial, fase exp(i*(-w*t+k*z)).
O sinal global de Riemann pode diferir do apêndice do TG; razões não mudam.
Execute: python3 scripts/checagens_preliminares.py
"""

from decimal import Decimal, localcontext
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path


PAIRS = [(a, b) for a in range(4) for b in range(a, 4)]
ETA = [1, -1, -1, -1]


def metric_amplitude(values):
    h = [[F(0) for _ in range(4)] for _ in range(4)]
    for (a, b), value in zip(PAIRS, values):
        h[a][b] = h[b][a] = F(value)
    return h


def riemann(h, w, k, a, b, c, d):
    q = [-F(w), F(0), F(0), F(k)]
    return (-q[b]*q[c]*h[a][d] - q[a]*q[d]*h[b][c]
            + q[b]*q[d]*h[a][c] + q[a]*q[c]*h[b][d]) / 2


def constraints(h, w, k, model):
    q = [-F(w), F(0), F(0), F(k)]
    trace = sum(ETA[a]*h[a][a] for a in range(4))
    div = [sum(ETA[a]*q[a]*h[a][b] for a in range(4)) for b in range(4)]
    if model == 'Visser_linear':
        return [div[b] - q[b]*trace/2 for b in range(4)]
    return div + [trace]


def rref(matrix):
    a = [[F(x) for x in row] for row in matrix]
    pivots = []
    row = 0
    for col in range(len(a[0])):
        pivot = next((r for r in range(row, len(a)) if a[r][col]), None)
        if pivot is None:
            continue
        a[row], a[pivot] = a[pivot], a[row]
        value = a[row][col]
        a[row] = [x/value for x in a[row]]
        for r in range(len(a)):
            if r != row:
                factor = a[r][col]
                a[r] = [x-factor*y for x, y in zip(a[r], a[row])]
        pivots.append(col)
        row += 1
        if row == len(a):
            break
    return a, pivots


def nullspace(matrix):
    reduced, pivots = rref(matrix)
    basis = []
    for free in range(len(matrix[0])):
        if free in pivots:
            continue
        vector = [F(0)]*len(matrix[0])
        vector[free] = F(1)
        for row, pivot in enumerate(pivots):
            vector[pivot] = -reduced[row][free]
        basis.append(vector)
    return basis


def tidal(h, w, k):
    return [riemann(h, w, k, 0, i, 0, j)
            for i, j in [(1, 1), (2, 2), (3, 3), (1, 2), (1, 3), (2, 3)]]


def exact_checks():
    ranks = []
    for w, k in [(1, 0), (5, 3), (13, 12), (1, 1)]:
        for model, dim in [('Visser_linear', 6), ('Fierz_Pauli', 5)]:
            columns = [constraints(metric_amplitude([int(i == j) for i in range(10)]),
                                   w, k, model) for j in range(10)]
            matrix = list(map(list, zip(*columns)))
            basis = nullspace(matrix)
            assert len(basis) == dim
            for v in basis:
                assert not any(constraints(metric_amplitude(v), w, k, model))
            image = [tidal(metric_amplitude(v), w, k) for v in basis]
            rank = len(rref(list(map(list, zip(*image))))[1])
            assert rank == (2 if w == k else dim)
            ranks.append({'w': w, 'k': k, 'modelo': model,
                          'dimensao_amplitudes_com_vinculos': dim,
                          'posto_mapa_de_mares': rank})

    for w, k in [(5, 0), (5, 3), (13, 12)]:
        m2 = F(w*w-k*k)
        h = metric_amplitude([0]*10)
        h[0][0], h[0][3], h[3][0] = -2*k*k, 2*w*k, 2*w*k
        h[1][1] = h[2][2] = m2
        h[3][3] = -2*w*w
        assert not any(constraints(h, w, k, 'Fierz_Pauli'))
        e = tidal(h, w, k)
        assert e[2]/(e[0]+e[1]) == -m2/F(w*w)

        # Cross polarization from TG Eq. (5.60), with A12=1 only.
        # Calibrate the conversion to R_0x0y at the null limit first.
        h_cross = metric_amplitude([int(pair == (1, 2)) for pair in PAIRS])
        psi4_im = F(4*k*k*w*w + 4*w*k**3 + 4*w**3*k + 2*k**4 + 2*w**4,
                    8*(w*w+k*k))
        exact_e_xy = riemann(h_cross, w, k, 0, 1, 0, 2)
        assert (psi4_im/2)/exact_e_xy == F((w+k)**2, 4*w*w)

    h = metric_amplitude(range(1, 11))
    w, k = 5, 3
    for a, b, c, d in product(range(4), repeat=4):
        r = lambda i, j, l, n: riemann(h, w, k, i, j, l, n)
        assert r(a, b, c, d) == -r(b, a, c, d)
        assert r(a, b, c, d) == r(c, d, a, b)
        assert r(a, b, c, d)+r(a, c, d, b)+r(a, d, b, c) == 0
    q, xi = [-F(w), F(0), F(0), F(k)], [F(2), F(-1), F(3), F(7)]
    pure_gauge = [[q[a]*xi[b]+q[b]*xi[a] for b in range(4)] for a in range(4)]
    assert all(riemann(pure_gauge, w, k, *abcd) == 0
               for abcd in product(range(4), repeat=4))
    return ranks


def scale_check(mass_energy_ev, frequency_hz):
    with localcontext() as ctx:
        ctx.prec = 70
        h_planck = Decimal('6.62607015e-34') / Decimal('1.602176634e-19')
        fg = Decimal(mass_energy_ev)/h_planck
        f = Decimal(frequency_hz)
        x = (fg/f)**2
        result = {'mg_c2_eV': mass_energy_ev, 'f_Hz': frequency_hz,
                  'fg_Hz': str(fg), 'x_fg_sobre_f_ao_quadrado': str(x),
                  'propagacao': 'viajante' if x < 1 else 'limiar' if x == 1 else 'evanescente'}
        if x <= 1:
            beta = (1-x).sqrt()
            # Pure tensor wave: null-calibrated projection ratio ((1+beta)/2)^2.
            # Stable algebra avoids subtracting two almost identical numbers.
            error = x*(3+beta)/(4*(1+beta))
            result.update({'vg_sobre_c': str(beta),
                           'erro_relativo_projecao_tensorial_quase_nula': str(error),
                           'epsilon_quase_nula': str(x/(1-x)) if x < 1 else 'infinito'})
        return result


def main():
    ranks = exact_checks()
    scenarios = [('1.92e-23', f) for f in ['1e-9', '1e-8', '1e-7', '1e-4', '100', '3000']]
    scenarios += [('4.4e-22', '1.1e-7'), ('3e-24', '2e-9'), ('0', '1e-8')]
    values = [scale_check(m, f) for m, f in scenarios]
    assert Decimal(values[-1]['x_fg_sobre_f_ao_quadrado']) == 0
    assert Decimal(values[-1]['vg_sobre_c']) == 1
    assert Decimal(values[-1]['erro_relativo_projecao_tensorial_quase_nula']) == 0
    result = {
        'status': 'checagens exatas e numericas aprovadas',
        'escopo': 'Cinematica linear; sem ajuste de dados, ORFs ou prova de estabilidade.',
        'fontes': {'limite_LVK_2026': 'https://arxiv.org/pdf/2603.19020',
                   'massa_historica_2004': 'https://arxiv.org/abs/gr-qc/0409041'},
        'postos_exatos': ranks,
        'relacao_escalar_FP': 'p_l/p_b = -(1-k^2/w^2), p_b=R_0x0x+R_0y0y, p_l=R_0z0z',
        'escalas': values,
    }
    with localcontext() as ctx:
        ctx.prec = 50
        planck_ev_s = Decimal('6.62607015e-34') / Decimal('1.602176634e-19')
        baseline_s = Decimal('4.5')*Decimal('365.25')*Decimal(86400)
        ceiling_ev = planck_ev_s/baseline_s
        prior_p90 = Decimal('0.9')*ceiling_ev
        result['comparacao_prior_MeerKAT_2026'] = {
            'fonte': 'https://arxiv.org/html/2607.14790v1',
            'hipotese': 'T=4.5 anos julianos; prior uniforme entre 0 e h/(T*c^2)',
            'limite_superior_prior_mg_c2_eV': str(ceiling_ev),
            'percentil90_apenas_prior_mg_c2_eV': str(prior_p90),
            'limites90_reportados_eV': {'DATA': '2.10e-23', 'ER': '2.58e-23', 'ALT': '2.25e-23'},
            'ressalva': 'Comparacao aritmetica; nao substitui reanalise dos dados ou medida de informacao.',
        }
    out = Path(__file__).resolve().parents[1]/'output'/'pesquisa'
    out.mkdir(parents=True, exist_ok=True)
    (out/'checagens_preliminares.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(result['status'])
    print('mg*c^2 [eV]    f [Hz]       x=(fg/f)^2      propagacao')
    for r in values:
        print(f"{r['mg_c2_eV']:13} {r['f_Hz']:12} {Decimal(r['x_fg_sobre_f_ao_quadrado']):.6E}  {r['propagacao']}")
    print('Resultado: output/pesquisa/checagens_preliminares.json')


if __name__ == '__main__':
    main()
