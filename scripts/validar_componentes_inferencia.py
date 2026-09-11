#!/usr/bin/env python3
"""Confere componentes C07; este comando não aprova posteriors nem executa SBC PTA.

Os testes curtos são executados novamente. As integrações independentes e o
controle TOY têm relatórios preservados, cujos critérios e hashes são conferidos.
Para refazer essas integrações, executar scripts/inference_checks/*.py e
scripts/validar_diagnosticos_toy.py antes de registrar uma nova validação.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import scipy


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(relative):
    return json.loads((ROOT / relative).read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def bounded(value, upper, label):
    require(np.isfinite(value) and 0 <= value <= upper, label)


def verify_hashes(records):
    for relative, expected in records.items():
        path = (ROOT / relative).resolve()
        require(path.is_relative_to(ROOT), "Caminho de evidência fora do repositório.")
        require(digest(path) == expected, f"Hash divergente: {relative}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Não substituir o registro validado.")
    args = parser.parse_args()
    test_paths = [ROOT / "tests" / name for name in
                  ("test_inference_kernel.py", "test_inference_diagnostics.py",
                   "test_mcmc_diagnostics.py", "test_inference_data.py",
                   "test_orf_blas.py", "test_orf_table_integrity.py",
                   "test_portable_reference.py", "test_mcmc_optimized.py",
                   "test_iid_diagnostics.py", "test_native_likelihood.py",
                   "test_iid_optimized.py", "test_sbc_sensitivity.py",
                   "test_portable_contract.py", "test_campaign_diagnostics.py",
                   "test_campaign_sbc.py", "test_campaign_driver.py",
                   "test_proposal_broadening.py", "test_fixed_generation.py",
                   "test_fixed_diagnostics.py", "test_fixed_operational.py",
                   "test_sbc_delivery.py", "test_compact_archive.py",
                   "test_fixed_synthesis.py")]
    suite = unittest.TestSuite()
    for path in test_paths:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = module
        spec.loader.exec_module(module)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    require(result.wasSuccessful(), "Falha nos testes de componentes de inferência.")

    base = "results/C07/validation/"
    cn = read(base + "scale_cn.json")
    require(cn["status"] == "PASS" and cn["analytic_integral_cases"] == 90,
            "Integração CN incompleta.")
    require(cn["source_sha256"] == digest(ROOT / "src/inference/scale_cn.py"),
            "A marginalização CN mudou após sua validação.")
    bounded(cn["maximum_absolute_log_integral_difference"], 1e-7, "Integral CN divergente.")
    bounded(cn["maximum_CDF_absolute_difference"], 1e-10, "CDF CN divergente.")
    for row in cn["physical_C07"]["scale_integral_checks"]:
        bounded(row["absolute_log_difference"], 1e-7, "Integral CN física divergente.")

    statuses = {
        "validation_integral.json": "PASS_conditional_gaussian_scale_reference",
        "validation_high_precision.json": "PASS_high_precision_tail_reference",
        "validation_kernel.json": "PASS_same_A_B_G_families_and_conditional_prior",
        "validation_guards.json": "PASS_explicit_failure_guards",
        "fast_kernel_validation.json": "PASS_reference_equivalence",
        "orf_blas_builder.json": "COMPLETE",
    }
    reports = {name: read(base + name) for name in statuses}
    for name, expected in statuses.items():
        require(reports[name]["status"] == expected, f"Validação incompleta: {name}")
    bounded(reports["validation_high_precision.json"]["maximum_abs_log_error"], 1e-6,
            "Referência de alta precisão divergente.")
    physical = reports["validation_kernel.json"]
    verify_hashes(physical["source_hashes"])
    for mass in physical["records"]:
        for row in mass["independent_direct_scale_checks"]:
            bounded(row["maximum_log_integral_error"], 1e-7, "Integral normal física divergente.")
            bounded(row["reference_refinement"], 1e-7, "Referência normal não convergiu.")
    for row in reports["fast_kernel_validation.json"]["checks"]:
        bounded(row["maximum_abs_difference_within_30_logunits_of_peak"], 1e-8,
                "Verossimilhança rápida diverge da referência.")
    direct = read(base + "orf_direct_checks.json")
    require(len(direct) == 7, "Checagens independentes esparsas da ORF incompletas.")
    for row in direct:
        bounded(row["absolute_difference"], 1e-7, "ORF diverge da quadratura direta.")
    fast_orf = reports['orf_blas_builder.json']
    require(len(fast_orf['sparse_direct_checks']) == 7, 'Checagem direta do novo backend incompleta.')
    for row in fast_orf['sparse_direct_checks']:
        bounded(row['absolute_difference'], 1e-7, 'Novo backend diverge da quadratura direta.')
    for row in fast_orf['legacy_cache_and_likelihood_comparisons']:
        bounded(row['matrix_max_abs_difference'], 1e-8, 'Novo backend diverge da ORF original.')
        bounded(row['maximum_logL_difference'], 1e-7, 'Novo backend altera a verossimilhança.')

    inventories = ["results/C07/fixtures/copied_fixture_inventory.json",
                   "results/C07/pilot_initial/archive_inventory.json"]
    inventory_paths = []
    for name in inventories:
        inventory = read(name)["files"]
        verify_hashes({r["path"]: r["sha256"] for r in inventory})
        for row in inventory:
            path = ROOT / row["path"]
            require(path.stat().st_size == row["size_bytes"], f"Tamanho divergente: {path}")
            inventory_paths.append(path)

    toy = read("results/C07/toy/toy_summary.json")
    require(toy["status"] == "PASS_TOY_CROSSCHECKS_AND_NEGATIVE_CONTROL"
            and toy["pta_sbc500_executed"] is False, "Escopo/validação TOY divergente.")
    verify_hashes(toy["source_hashes"])
    require(toy["input_npz_sha256"] == digest(ROOT / "results/C07/toy/toy_inputs.npz"),
            "Dados TOY alterados.")
    for value in toy["independent_analytic_checks"].values():
        bounded(value, 1e-10, "Referência analítica TOY divergente.")

    mcmc_toy = read("results/C07/mcmc_toy/toy_summary.json")
    require(mcmc_toy["all_numeric_checks_pass"] and
            all(mcmc_toy["predeclared_numeric_checks"].values()) and
            mcmc_toy["PTA_SBC_executed"] is False, "Diagnósticos MCMC TOY incompletos.")
    verify_hashes(mcmc_toy["source_sha256"])
    require(mcmc_toy["config_sha256"] == digest(ROOT / "configs/calibration/diagnostics_mcmc_v2.json"),
            "O protocolo MCMC mudou após a validação TOY.")

    iid_toy = read("results/C07/iid_toy/toy_summary.json")
    require(iid_toy["label"] == "ANALYTIC_TOY_ONLY_NOT_PTA_SBC" and
            iid_toy["all_predeclared_checks_pass"] and
            len(iid_toy["checks"]) == 7 and all(c["pass"] for c in iid_toy["checks"]),
            "Diagnósticos IID TOY incompletos.")
    verify_hashes(iid_toy["source_hashes"])

    reference = read('results/C07/reference/quantiles/quantile_summary.json')
    require(reference['all_requested_quantiles_pass'] and reference['parameter_quantiles_completed'] == 16,
            'Referência A0 d14 incompleta.')
    bounded(reference['maximum_between_rule_quantile_difference_bound_fraction_prior'], .001,
            'Quantis de referência não satisfazem o refinamento horizontal.')
    for row in read('results/C07/reference/port_manifest.json').values():
        verify_hashes({row['portable']:row['portable_sha256']})
    claims = read('results/C07/reference/port_validation/historical_source_claims.json')
    for row in claims:
        require(row['all_claims_match_current_bytes'], 'Fonte histórica divergente na portabilidade.')
        verify_hashes({row['preserved_claimed_source']:row['current_sha256']})
    optimization = read('results/C07/mcmc_optimization/benchmark.json')
    rounding = read('results/C07/mcmc_optimization/roundoff.json')
    require(optimization['all_detailed_fields_match'] and rounding['decisions_failures_statuses_exact'],
            'Otimização alterou diagnósticos MCMC.')
    bounded(rounding['maximum_absolute_difference'], 1e-12, 'Otimização MCMC diverge da referência.')
    recorded_optimized_hash = read('results/C07/mcmc_optimization/tests.json')['source_hashes']['tmp/c07_mcmc_optimized/mcmc_optimized.py']
    require(digest(ROOT/'src/inference/mcmc_optimized.py') == recorded_optimized_hash,
            'O verificador otimizado mudou após a comparação histórica.')

    native = read('results/C07/native_review_history/independent/results/owned_review.json')
    require(native['all_checks_pass'] and native['check_count'] == 34,
            'Contrato do wrapper nativo não foi validado.')
    physical_native = read('results/C07/native_review_history/independent/results/owned_physical_review.json')
    require(physical_native['all_pass'] and sum(r['N'] for r in physical_native['rows']) == 912,
            'Comparação física nativa incompleta.')
    native_claims = physical_native['source_hashes']
    for suffix, integrated in [('native_owned.py', 'src/inference/native_likelihood.py'),
                               ('full_guarded.cpp', 'src/inference/native/likelihood.cpp')]:
        claimed = [h for p,h in native_claims.items() if p.endswith('/'+suffix)]
        require(claimed == [digest(ROOT/integrated)], 'Backend nativo mudou após sua auditoria.')

    interpolation = read('results/C07/orf_interpolation/orf_table_manifest.json')
    require(interpolation['status'] == 'VALIDATED_IN_STATED_NUMERICAL_TEST_DOMAIN' and
            interpolation['nodes'] == 8336 and not interpolation['fallback_intervals'],
            'Tabela angular final não validada.')
    require(digest(ROOT/'results/C07/orf_interpolation/orf_table_pilot12x4.npz') == interpolation['file_sha256'],
            'Tabela angular publicada difere da validada.')
    interpolation_check = read('results/C07/orf_interpolation/dense_local_validation.json')
    require(interpolation_check['passes_tested_domain'], 'Refinamento angular não aprovado.')
    for row in interpolation_check['comparisons'].values():
        bounded(row['maximum_abs_loglikelihood_difference'], .001, 'Refinamento angular excede o limite.')
    accepted_pilot = read('results/C07/pilot_iid_approved/diagnostics_root_summary.json')
    final_pilot = accepted_pilot['levels'][-1]
    require(final_pilot['N'] == 65536 and final_pilot['cdf_precision_pass'] == 416 and
            final_pilot['all_precision_weight_targets'] == 16 and
            final_pilot['A0d14_brackets'] == 20 and final_pilot['A0d14_brackets_precision'] == 20 and
            accepted_pilot['replication_failed'] == accepted_pilot['refinement_failed'] == 0,
            'Piloto IID selecionado incompleto ou impreciso.')

    optimized_iid = read('results/C07/iid_optimization/results/comparison_final.json')
    require(optimized_iid['all_flags_exact'] and optimized_iid['all_statistical_fields_within_1e_12'],
            'A otimização IID alterou o relatório de referência.')
    bounded(optimized_iid['maximum_abs_difference'], 1e-12, 'Diagnóstico IID otimizado divergente.')
    require(digest(ROOT/'src/inference/iid_optimized.py') ==
            'b9d1ab59bf0323b933084b518c2bc249e32fdad044a02f7d380e1690d968d458',
            'Diagnóstico IID mudou após a comparação independente.')
    engineering = read('results/C07/integrated_engineering/diagnostic_summary.json')
    require(engineering['cdf_precise'] == 401 and engineering['cdf_total'] == 416 and
            engineering['reference_consistent'] == engineering['reference_precise'] == 20 and
            engineering['all_pooled_weight_guards'] is False and
            engineering['raw_count_after_release'] == 0 and engineering['PTA_SBC500_executed'] is False,
            'O histórico do ensaio integrado, inclusive suas falhas, mudou.')
    wide = read('results/C07/wide16_review/diagnostics_v1_wide16_summary.json')
    high = wide['levels'][1]
    require(high['N'] == 65536 and high['cdf_precision_pass'] == high['cdf_total'] == 416
            and high['all_precision_weight_targets'] == 16
            and high['A0d14_brackets'] == high['A0d14_brackets_precision'] == 20
            and wide['replication_failed'] == wide['refinement_failed'] == 0,
            'Ensaio independente da proposta ampla incompleto.')
    bounded(high['max_mcse'], .00335, 'Proposta ampla sem precisão no ensaio de engenharia.')
    wide_flow = read('results/C07/integrated_wide3/campaign/campaign_complete.json')
    require(wide_flow['status'] == 'ALL_TARGET_PRODUCTS_ARCHIVED'
            and wide_flow['targets'] == [25, 51, 78]
            and wide_flow['numerically_unresolved_targets'] == [],
            'Ensaio integrado das novas credenciais incompleto.')

    files = set(test_paths + inventory_paths + [Path(__file__)])
    for directory, pattern in [("src/inference", "*.py"), ("src/pta", "*.py"),
                               ("scripts/inference_checks", "*.py"),
                               ("results/C07/validation", "*.json"),
                               ("configs/calibration", "*.json")]:
        files.update((ROOT / directory).glob(pattern))
    files.update(ROOT / p for p in inventories + list(toy["source_hashes"]) +
                 ["results/C07/toy/toy_summary.json", "results/C07/toy/toy_inputs.npz"])
    files.update(ROOT / p for p in list(mcmc_toy["source_sha256"]) +
                 ["results/C07/mcmc_toy/toy_summary.json",
                  "results/C07/mcmc_toy/toy_validation_arrays.npz",
                  "docs/protocolo_diagnosticos_mcmc_c07_v2.md"])
    files.update((ROOT / "results/C07/pilot_mcmc_history").glob("*"))
    files.update(p for p in (ROOT/'results/C07/reference').rglob('*') if p.is_file())
    files.update((ROOT/'results/C07/mcmc_optimization').glob('*'))
    files.update(p for p in (ROOT/'results/C07/generator_review_history').rglob('*') if p.is_file())
    files.update((ROOT/'results/C07/iid_toy').glob('*'))
    files.update(ROOT / p for p in iid_toy['source_hashes'])
    files.add(ROOT/'docs/protocolo_diagnosticos_iid_c07_v1.md')
    files.add(ROOT/'scripts/reference_a0.py')
    files.add(ROOT/'scripts/gerar_calibracao.py')
    files.add(ROOT/'scripts/build_native.py')
    files.add(ROOT/'src/inference/native/likelihood.cpp')
    for dirname in ['native_review_history', 'orf_interpolation', 'pilot_iid_approved', 'iid_pilot_history',
                    'proposal_review','cold_training','cold_final','proposal_efficiency',
                    'training_benchmark','iid_optimization','data500_independent_review',
                    'integrated_engineering','portable_inference','sbc_sensitivity_review',
                    'truth_interpolation500','cold_tail_review','wide16_review',
                    'integrated_wide3','proposal_broadening','campaign_driver',
                    'fixed_scenarios','fixed_operational','sbc_delivery',
                    'fixed_synthesis_review','compact_archive_review']:
        files.update(p for p in (ROOT/'results/C07'/dirname).rglob('*') if p.is_file())
    files.add(ROOT/'scripts/diagnosticar_importancia_iid.py')
    files.add(ROOT/'scripts/planejar_custos_iid.py')
    files.update(ROOT/'scripts'/p for p in ['run_calibration_campaign.py','infer_calibration.py',
        'diagnose_calibration_target.py','calcular_logl_verdades.py',
        'run_fixed_campaign.py','gerar_injecoes_fixas.py',
        'sintetizar_calibracao.py','figuras_calibracao.py','tabelas_calibracao.py',
        'sintetizar_injecoes_fixas.py','tabelas_injecoes_fixas.py','compactar_calibracao.py',
        'diagnosticar_importancia_iid_otimizada.py','validate_portable_sampler.py'])
    record = {
        "stage": "C07", "status": "PASS_COMPONENTS_ONLY",
        "scope": "Repeated unit checks, conditional integrals, diagnostic TOYs, one selected A0 reference, ORF interpolation and selected16 IID pilot; no approval of the 2500 production posterior targets or PTA SBC.",
        "tests_run": result.testsRun, "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "archived_files_verified": len(inventory_paths),
        "independent_direct_orf_pairs": len(direct),
        "files_sha256": {str(p.relative_to(ROOT)): digest(p) for p in sorted(files)},
    }
    destination = ROOT / "results/C07/component_validation.json"
    if args.check:
        require(read(str(destination.relative_to(ROOT))) == record,
                "Registro dos componentes C07 diverge; investigar antes de regenerar.")
    else:
        destination.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    print(f"C07: {result.testsRun} testes de componentes; integrais condicionais e TOY conferidos. Campanha PTA não é validada por este comando.")


if __name__ == "__main__":
    main()
