#!/usr/bin/env python3
"""Executa as provas simbólicas de C04 e registra ou confere suas evidências."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from polarizacoes.foundations import expressions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Reexecuta sem substituir o registro versionado.")
    args = parser.parse_args()
    names = ["tests.test_polarizacoes.GeneralIdentities", "tests.test_normalizacao.EinsteinNormalization"]
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
    test_names = [test.id() for group in suite for test in group]
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    # Sem tempos de execução ou caminhos locais: comparação determinística entre checkouts.
    record = {
        "stage": "C04", "status": "PASS", "tests_run": result.testsRun,
        "errors": len(result.errors), "failures": len(result.failures), "tests": test_names,
        "dependencies": {name: importlib.metadata.version(name) for name in ("sympy", "mpmath")},
        "domain": "omega != 0, k real; Delta > 0 massive travelling; Delta=0 evaluated separately; linear vacuum",
        "expressions": expressions(),
        "rank_proofs": {
            "Visser_constraint_minor": "-omega**2*(omega**2+k**2)/2",
            "FP_constraint_minor": "-omega**4",
            "Visser_tidal_determinant": "omega**6*Delta**4/(32*Sigma)",
            "FP_tidal_minor": "omega**4*Delta**3/16",
            "null_tidal_rank_bounded_metric": 2,
            "threshold_ranks": {"Visser": 6, "FP": 5},
        },
        "normalization_audit": {
            "einstein_under_Lorenz": "G_here=-Box(hbar_metric)/2; G_historical=+Box(hbar_metric)/2",
            "tg_literal_mass_coefficient": "+2*m_TG**2/(hbar_Planck**2*c**2)",
            "tg_coefficient_dimension_if_SI": "L**(-6)*T**4",
            "article_2004_literal_mass_coefficient": "-2*m_article**2*c**2/hbar_Planck**2",
            "article_2004_printed_mass_coefficient": "-m_article**2*c**2/hbar_Planck**2",
            "operational_definition": "mu=m_g*c/hbar_Planck; omega_SI**2=c**2*k**2+(m_g*c**2/hbar_Planck)**2",
            "interpretation": "Algebraic diagnostic of consulted equations; not a confirmed editorial erratum.",
        },
        "scope": "Curvature, constraints and conventions; no PTA inference or nonlinear stability claim.",
    }
    output = ROOT / "results/C04/validacao.json"
    if args.check:
        if not output.exists() or json.loads(output.read_text()) != record:
            raise SystemExit("Registro C04 diverge. Investigue a alteração antes de gerar uma nova versão.")
        print(f"C04: {result.testsRun} testes e registro simbólico conferidos.")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        print(f"C04: {result.testsRun} testes aprovados; {output.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
