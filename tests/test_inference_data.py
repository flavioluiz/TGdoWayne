import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from inference.data_generation import prior_truths, StoredExactORF, generate_prior_fixture
from inference.model import experiment


class InferenceDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT/'configs/calibration/pilot_initial.json').read_text())
        cls.cache = ROOT/'results/C07/fixtures/orf_cache'

    def test_reproduce_all_sixteen_preparatory_draws(self):
        arrays, records = generate_prior_fixture(self.config, self.cache)
        with np.load(ROOT/'results/C07/fixtures/pilot_data.npz') as expected:
            for name, value in arrays.items():
                np.testing.assert_allclose(value, expected[name], rtol=1e-12, atol=1e-12)
        self.assertEqual(len(records), 16)
        self.assertTrue(all(not r['interpolation_used'] for r in records))

    def test_missing_truth_node_cannot_fall_back_to_interpolation(self):
        with tempfile.TemporaryDirectory() as temporary:
            provider = StoredExactORF(experiment(self.config), self.config['orf'], temporary)
            with self.assertRaises(FileNotFoundError):
                provider.evaluate(.123456789)
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_corrupted_exact_cache_is_rejected(self):
        provider = StoredExactORF(experiment(self.config), self.config['orf'], self.cache)
        gamma = provider.evaluate(0.)
        filename = provider.records[0]['file']
        with np.load(self.cache/filename) as existing:
            record = str(existing['record'])
        with tempfile.TemporaryDirectory() as temporary:
            corrupted = gamma.copy(); corrupted[0,0,0] = np.nan
            np.savez_compressed(Path(temporary)/filename, Gamma=corrupted, record=record)
            reader = StoredExactORF(experiment(self.config), self.config['orf'], temporary)
            with self.assertRaises(RuntimeError):
                reader.evaluate(0.)

    def test_unsupported_spectral_design_is_rejected(self):
        for changes in [{'positive_channels':[1,2,4,8]}, {'positive_channels':[1,2,3]},
                        {'fixed_red_slope':3.5}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                prior_truths({**self.config,**changes})


if __name__ == '__main__':unittest.main()
