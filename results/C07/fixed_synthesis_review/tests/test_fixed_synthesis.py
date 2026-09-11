"""Small deterministic TOY fixtures; no PTA posterior or likelihood execution."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import itertools
import json
import shutil
import sys
import tempfile
import unittest
import numpy as np
from scipy.stats import binom

ROOT = Path.cwd()
PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
spec = importlib.util.spec_from_file_location('fixed_synthesis_candidate', PACKAGE/'src/inference/fixed_synthesis.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
from inference.campaign_io import sha256, write_json_new, write_npz_new
from inference.campaign_archive import prepare_archive

BOUNDS = np.array([[0., 1.], [-16., -14.], [3., 5.5], [-17., -14.5], [-np.log10(2), np.log10(2)]])
TRUTHS = np.array([[0., -15., 13/3, -15.5, 0.], [.995, -15., 13/3, -15.5, 0.],
                   [np.nan, np.nan, np.nan, -15.5, 0.]])
PROTOCOL = json.loads((ROOT/'tmp/c07_fixed_scenarios/configs/fixed_diagnostics_v1.json').read_text())
CONFIG = json.loads((PACKAGE/'configs/fixed_synthesis_v1.json').read_text())


def numeric_fixture(target):
    defined, structural, applicable, exact = module.masks(target)
    estimates = np.full((2, 26), .5)
    errors = np.full((2, 26), .001)
    estimates[:, ~applicable] = errors[:, ~applicable] = np.nan
    estimates[:, exact] = errors[:, exact] = 0.
    resolution = np.isfinite(errors) & applicable[None]
    q = np.tile(module.PROBS, (5, 1))
    indices = np.array([[5*j+k for k in range(1, 5)] for j in range(5)])
    reps, refs = module.contrast_specifications(target)
    truth = TRUTHS[target//32]
    a = dict(target=np.asarray(target), datum=np.asarray(target), model_index=np.asarray(0),
        scenario_index=np.asarray(target//32), replicate_within_scenario=np.asarray(target%32),
        probabilities=module.PROBS.copy(), truth_physical=truth.copy(),
        truth_unit=(truth-BOUNDS[:, 0])/np.diff(BOUNDS, axis=1)[:, 0],
        truth_defined=defined[:5], truth_log_likelihood=np.asarray(-12. if target < 64 else np.nan),
        truth_log_likelihood_defined=np.asarray(target < 64), pit_applicable=defined, pit_structural_exact=structural,
        cdf_applicable=applicable, cdf_structural_exact=exact, cdf_numerically_evaluated=applicable & ~exact,
        quantiles_unit=q, quantiles_physical=BOUNDS[:, 0, None]+np.diff(BOUNDS, axis=1)*q,
        cdf_estimates_by_level=estimates, cdf_mcse_by_level=errors,
        cdf_resolved_by_level=resolution, cdf_precision_by_level=resolution.copy(),
        pit=estimates[1, module.PIT], pit_mcse=errors[1, module.PIT],
        pit_resolved=resolution[1, module.PIT], pit_precision_pass=resolution[1, module.PIT],
        cut_cdf=estimates[1, indices], cut_mcse=errors[1, indices],
        cut_resolved=resolution[1, indices], cut_precision_pass=resolution[1, indices],
        replication_specification=reps, refinement_specification=refs,
        weight_deletion_guard_by_level=np.ones(2, bool), saturated_weight=np.zeros((2, 4)))
    for prefix, count in [('replication', len(reps)), ('refinement', len(refs))]:
        a.update({prefix+'_difference': np.zeros(count), prefix+'_mcse': np.full(count, .001),
                  prefix+'_resolved': np.ones(count, bool), prefix+'_pass': np.ones(count, bool)})
    return a


def check(a, target):
    return module.check_numeric(a, target, TRUTHS[target//32],
        -12. if target < 64 else np.nan, BOUNDS, PROTOCOL)


def synthetic_arrays():
    keys = ['pit', 'pit_mcse', 'pit_applicable', 'pit_structural_exact', 'quantiles_unit',
            'quantiles_physical', 'cut_precision_pass']
    rows = [numeric_fixture(t) for t in range(96)]
    a = {k: np.stack([r[k] for r in rows]) for k in keys}
    a['resolved_for_function'] = np.stack([check(r, t) for t, r in enumerate(rows)])
    return a


def write_toy_campaign(root):
    """Exercise the actual archive/inventory on labeled invented diagnostics."""
    campaign = root/'campaign'
    sci = json.loads((ROOT/'configs/calibration/fixed_scenarios_v1.json').read_text())
    exp = json.loads((ROOT/'configs/calibration/fixed_experiment_v1.json').read_text())
    sources = root/'inputs'
    write_json_new(sources/'experiment.json', exp)
    write_json_new(sources/'scientific.json', sci)
    write_json_new(sources/'numerical.json', PROTOCOL)
    truths = np.repeat(TRUTHS, 32, axis=0)
    write_npz_new(sources/'data.npz', truth=truths, log_likelihood_at_truth=np.r_[np.full(64, -12.), np.full(32, np.nan)],
        truth_defined=np.array([module.masks(t)[0][:5] for t in range(96)]),
        log_likelihood_at_truth_defined=np.arange(96)<64,
        structural_lower_boundary_pit=np.array([module.masks(t)[1][:5] for t in range(96)]),
        target=np.arange(96), scenario_index=np.repeat(np.arange(3), 32), replicate_within_scenario=np.tile(np.arange(32), 3),
        label=np.asarray('TOY_FIXED96_METADATA_NO_PTA_OBSERVATIONS_OR_POSTERIORS'))
    write_json_new(sources/'generation.json', dict(status='FIXED_DATA_GENERATED_NOT_POSTERIOR_INFERENCE',
        data_sha256=sha256(sources/'data.npz'), absent_signal_covariance_exactly_zero=True,
        preflight={'experiment_sha256': sha256(sources/'experiment.json')}, toy=True))
    config = copy.deepcopy(CONFIG)
    paths = dict(data=sources/'data.npz', experiment=sources/'experiment.json', generation=sources/'generation.json',
                 numerical_protocol=sources/'numerical.json', scientific_protocol=sources/'scientific.json')
    config['sources'] = {k: dict(path=str(p), sha256=sha256(p)) for k, p in paths.items()}
    write_json_new(sources/'synthesis.json', config)
    evidence = []
    for name in ['orf_interpolation', 'likelihood_kernel', 'external_posterior_reference']:
        write_json_new(sources/(name+'.json'), dict(scope='TOY_EMPTY_EVIDENCE_NO_PTA_APPROVAL'))
        evidence.append(dict(role=name, path=name+'.json', sha256=sha256(sources/(name+'.json'))))
    write_json_new(sources/'evidence.json', dict(entries=evidence, scope='TOY_ONLY'))
    runtime_id, driver_id = 'toy_runtime_fixed96', 'toy_driver_fixed96'
    input_hashes = {k: sha256(v) for k, v in dict(experiment=paths['experiment'], data=paths['data']).items()}
    producer_sources = {}
    for name in ['iid_diagnostics', 'iid_optimized', 'campaign_io', 'campaign_diagnostic_io']:
        src = ROOT/'src/inference'/(name+'.py')
        dest = campaign/'provenance'/runtime_id/(name+'.py')
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        producer_sources[name] = sha256(src)
    write_json_new(campaign/'provenance'/runtime_id/'manifest.json',
        dict(identity=runtime_id, input_sha256=input_hashes, source_sha256=producer_sources))
    masked = ROOT/'tmp/c07_fixed_scenarios/src/inference/fixed_diagnostics_v2.py'
    driver_root = campaign/'driver_provenance'/driver_id
    driver_root.mkdir(parents=True)
    shutil.copyfile(masked, driver_root/'fixed_masked_reader.py')
    shutil.copyfile(paths['numerical_protocol'], driver_root/'protocol.json')
    shutil.copyfile(paths['generation'], driver_root/'generation.json')
    plan = dict(identity=runtime_id, driver_identity=driver_id, scope=module.SCOPE, all_target_ids=list(range(96)),
        models=['A0_CN'], input_sha256=input_hashes,
        extra_input_sha256=dict(protocol=sha256(paths['numerical_protocol']), truth_data=sha256(paths['data']), generation=sha256(paths['generation'])),
        driver_source_sha256=dict(fixed_masked_reader=sha256(masked)))
    write_json_new(campaign/'campaign_plan.json', plan)
    write_json_new(campaign/'campaign_complete.json', dict(status='ALL_TARGET_PRODUCTS_ARCHIVED', scope=module.SCOPE,
        driver_identity=driver_id, targets=list(range(96)), numerically_unresolved_targets=[40], toy=True))
    runtime = type('ToyRuntime', (), dict(identity=runtime_id, paths={}))()
    for t in range(96):
        a = numeric_fixture(t)
        # One numerical failure must survive the completed inventory/archive.
        if t == 40:
            a['weight_deletion_guard_by_level'][0] = False
        numeric = campaign/'diagnostics'/f'diagnostic_target_{t:06d}.npz'
        write_npz_new(numeric, **a)
        proposal = campaign/'proposals'/f'target_{t:06d}.json'
        write_json_new(proposal, dict(target=t, label='TOY_PROPOSAL_NEVER_SAMPLED'))
        reps = []
        for n in [16384, 65536]:
            for r in range(4):
                rep = dict(status='IID_REPLICATE_COMPLETE', identity=runtime_id, target=t, level=n,
                    replicate=r, raw_file=f'target_{t:06d}_N{n}_rep_{r:02d}.npz',
                    raw_sha256=hashlib.sha256(f'toy_{t}_{n}_{r}'.encode()).hexdigest(),
                    proposal_sha256=sha256(proposal), rng_recipe='TOY NO SAMPLER EXECUTED', seed=1,
                    rng_state_before={}, rng_state_after={}, saturated_normalized_target_weight=0.)
                write_json_new(campaign/'production'/f'target_{t:06d}_N{n}_rep_{r:02d}.json', rep)
                reps.append(rep)
        producer = campaign/'production'/f'target_{t:06d}.json'
        write_json_new(producer, dict(status='IID_COMPLETE_AWAITING_DIAGNOSTICS', identity=runtime_id,
            target=t, datum=t, model='A0_CN', proposal_sha256=sha256(proposal), levels=[16384,65536],
            replicates=reps, uses_truth=False, input_sha256=input_hashes))
        diagnostic = campaign/'diagnostics'/f'diagnostic_target_{t:06d}.json'
        write_json_new(diagnostic, dict(status='NUMERICAL_DIAGNOSTICS_COMPLETE', schema=module.SCHEMA,
            scope=module.SCOPE, identity=runtime_id, target=t, datum=t, model='A0_CN', raw_release_authorized=False,
            numeric_file=numeric.name, numeric_sha256=sha256(numeric), levels=[16384,65536],
            proposal_sha256=sha256(proposal), raw_sha256={r['raw_file']:r['raw_sha256'] for r in reps},
            diagnostic_inputs=dict(producer_report_sha256=sha256(producer), truth_data_sha256=sha256(paths['data']),
                generation_sha256=sha256(paths['generation']), protocol_sha256=sha256(paths['numerical_protocol']),
                source_sha256=dict(fixed_diagnostics=sha256(masked), **producer_sources)),
            summary=dict(cdf_precision_pass=True, pooled_weight_guard_pass=t!=40, saturation_guard_pass=True,
                         replication_pass=True, refinement_pass=True)))
        prepare_archive(runtime, t, campaign/'proposals', campaign/'production', diagnostic)
    args = (campaign, paths['experiment'], paths['data'], paths['generation'], paths['numerical_protocol'],
        paths['scientific_protocol'], sources/'synthesis.json', sources/'evidence.json')
    return args


class FixedSynthesisTests(unittest.TestCase):
    def test_strict_scenario_masks_and_expected_contrast_counts(self):
        for t, counts in [(0,(192,6)), (32,(204,7)), (64,(156,3))]:
            a = numeric_fixture(t)
            resolution = check(a, t)
            self.assertEqual((len(a['replication_pass']),len(a['refinement_pass'])), counts)
            self.assertTrue(resolution[a['pit_applicable']].all())
            self.assertFalse(resolution[~a['pit_applicable']].any())
        a = numeric_fixture(64);a['pit'][0] = 0.
        with self.assertRaises(ValueError):check(a,64)

    def test_structural_is_exact_even_when_other_functions_fail(self):
        a = numeric_fixture(0);a['weight_deletion_guard_by_level'][0] = False
        r = check(a,0)
        np.testing.assert_array_equal(r,[True,False,False,False,False,False])
        a['pit_mcse'][0] = .001
        with self.assertRaises(ValueError):check(a,0)

    def test_function_specific_failure_does_not_discard_others(self):
        a = numeric_fixture(32)
        select = a['replication_specification'][:,1] == 5
        a['replication_difference'][select] = 1.
        a['replication_pass'][select] = False
        np.testing.assert_array_equal(check(a,32),[True,False,True,True,True,True])

    def test_constants_infinite_mcse_and_flags_are_not_precision(self):
        a = numeric_fixture(32)
        a['cdf_mcse_by_level'][1,0] = np.inf;a['pit_mcse'][0] = np.inf
        a['cdf_resolved_by_level'][1,0]=False;a['cdf_precision_by_level'][1,0]=False
        a['pit_resolved'][0]=False;a['pit_precision_pass'][0]=False
        self.assertFalse(check(a,32)[0])
        a['pit_precision_pass'][0]=True
        with self.assertRaises(ValueError):check(a,32)

    def test_contrast_identity_and_guard_reject_omission_or_false_pass(self):
        a=numeric_fixture(64);a['replication_specification'][0]=a['replication_specification'][1]
        with self.assertRaises(ValueError):check(a,64)
        a=numeric_fixture(32);a['refinement_difference'][0]=2.
        with self.assertRaises(ValueError):check(a,32)

    def test_pointwise_cp_independent_binomial_tail_inversion(self):
        for k in [0,1,7,16,31,32]:
            p=np.r_[np.full(k,.3),np.full(32-k,.99)]
            row=module.conditional_coverage(p,p,p)
            lo,hi=row['pointwise_cp95']
            self.assertEqual(row['calculated_count'],k)
            if k:self.assertAlmostEqual(binom.sf(k-1,32,lo),.025,places=12)
            if k<32:self.assertAlmostEqual(binom.cdf(k,32,hi),.025,places=12)

    def test_envelope_counts_contain_every_assignment_without_dropping32(self):
        p=np.full(32,.5);lo=p.copy();hi=p.copy()
        lo[:3]=[0.,.8,.94];hi[:3]=[1.,.96,.99]
        for central in [False,True]:
            row=module.conditional_coverage(p,lo,hi,central=central)
            counts=[]
            for v in itertools.product(*[[lo[j],.9,.95,hi[j]] for j in range(3)]):
                if any(not lo[j]<=v[j]<=hi[j] for j in range(3)):continue
                x=p.copy();x[:3]=v
                counts.append(int(((x>=.05)&(x<=.95)).sum() if central else (x<=.9).sum()))
            self.assertEqual(row['certainly_covered'],min(counts))
            self.assertEqual(row['possibly_covered'],max(counts))
            self.assertEqual(row['n'],32)

    def test_synthesis_keeps96_nan_and_structural_exceptions_no_uniformity(self):
        a=synthetic_arrays();a['resolved_for_function'][40,0]=False
        report,bands=module.synthesize(a,CONFIG)
        self.assertTrue(report['all_ids_retained']);self.assertTrue(report['no_KS_or_uniformity_test'])
        self.assertEqual(report['numerical_sensitivity']['family_size'],576)
        self.assertTrue(np.isnan(bands['pit_lower'][64:,[0,1,2,5]]).all())
        self.assertEqual(bands['pit_lower'][40,0],0);self.assertEqual(bands['pit_upper'][40,0],1)
        zero=next(r for r in report['functions'] if r['scenario']==module.SCENARIOS[0] and r['parameter']=='u')
        self.assertEqual(zero['upper90']['calculated_count'],32)
        self.assertEqual(zero['central90']['calculated_count'],0)
        self.assertEqual(zero['upper90']['structural_population_coverage'],1)
        self.assertEqual(len(report['quantiles']),15)

    def test_prospective_protocol_cannot_reduce_family_or_change_alpha(self):
        sci=json.loads((ROOT/'configs/calibration/fixed_scenarios_v1.json').read_text())
        module.check_protocol(CONFIG,PROTOCOL,sci)
        for key,value in [('family_size',448),('alpha_mc',.05),('deterministic_component',0)]:
            cfg=copy.deepcopy(CONFIG);cfg['numerical_sensitivity'][key]=value
            with self.assertRaises(ValueError):module.check_protocol(cfg,PROTOCOL,sci)

    def test_real_archive_full96_loader_and_integrity_failures(self):
        with tempfile.TemporaryDirectory(prefix='fixed96_synthesis_toy_') as folder:
            args=write_toy_campaign(Path(folder))
            arrays,cfg,proof=module.load_campaign(*args)
            self.assertEqual(len(proof['inventory']),96)
            self.assertFalse(arrays['resolved_for_function'][40].any())
            self.assertEqual(proof['inventory'][40]['numerical_status'],'NUMERICALLY_UNRESOLVED')
            report,_=module.synthesize(arrays,cfg)
            self.assertEqual(sum(s['n'] for s in report['scenarios']),96)
            path=args[0]/'diagnostics/diagnostic_target_000095.json'
            original=path.read_bytes();path.unlink()
            with self.assertRaises(ValueError):module.load_campaign(*args)
            path.write_bytes(original)
            d=json.loads(original);d['schema']='C07_TARGET_IID_DIAGNOSTICS_v1';path.write_text(json.dumps(d))
            with self.assertRaises(ValueError):module.load_campaign(*args)
            path.write_bytes(original)
            snapshot=args[0]/'provenance/toy_runtime_fixed96/iid_optimized.py'
            snapshot.write_bytes(snapshot.read_bytes()+b'\n#changed')
            with self.assertRaises(RuntimeError):module.load_campaign(*args)


if __name__=='__main__':unittest.main()
