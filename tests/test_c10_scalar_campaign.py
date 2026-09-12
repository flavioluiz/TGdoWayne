"""Inventory checks use metadata only and cannot generate physical observations."""
from pathlib import Path
import copy
import json
import sys
import unittest
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'src'))
from pta.scalar_campaign import inventory, hypotheses, budget


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.p = json.loads((R/'tmp/c10_execution_design/c10_protocol_candidate_v1.json').read_text())

    def test_counts_and_disjoint_namespaces(self):
        rows = inventory(self.p)
        b = budget(self.p, rows)
        self.assertEqual((b['observations'], b['analyses'], b['fine_grid_values']), (1192, 6344, 210322632))
        seeds = [tuple(row['data_seed']) for row in rows] + [tuple(row['truth_seed']) for row in rows if 'truth_seed' in row]
        self.assertEqual(len(seeds), len(set(seeds)))
        self.assertEqual(len([r for r in rows if len(r['analyses']) == 9]), 96)
        self.assertIn(133, self.p['C_subset']['recovery_ids'])
        self.assertIn(165, self.p['C_subset']['recovery_ids'])
        recovery = [r for r in rows if r['ensemble'] == 'recovery']
        self.assertEqual([r['fixed_truth'] for r in recovery[::32]],
                         [[.2,.1],[.2,.5],[.8,.1],[.8,.5],[.995,.1],[.995,.5]])
        self.assertEqual(rows, inventory(self.p))

    def test_hypothesis_membership_and_sensitivity_to_protocol(self):
        f = hypotheses(self.p)
        self.assertEqual({k:len(v) for k,v in f.items()}, {'correct':39,'approximate':26,'paired_central90':6})
        self.assertEqual(len({json.dumps(x, sort_keys=True) for rows in f.values() for x in rows}), 71)
        changed = copy.deepcopy(self.p)
        changed['sbc']['quantile_probabilities'].append(.99)
        with self.assertRaises(ValueError): hypotheses(changed)

    def test_malformed_subset_and_excess_budget_rejected(self):
        changed = copy.deepcopy(self.p); changed['C_subset']['null_ids'].append(0)
        with self.assertRaises(ValueError): inventory(changed)
        changed = copy.deepcopy(self.p); changed['resources']['maximum_production_likelihood_equivalents'] = 10
        with self.assertRaises(ValueError): budget(changed, inventory(changed))


if __name__ == '__main__': unittest.main()
