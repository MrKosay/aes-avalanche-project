import csv
import json
import tempfile
import unittest
from pathlib import Path
from statistics import mean, stdev
from round_experiments import run_round_experiments, save_results


class BatchTests(unittest.TestCase):
    def test_25_trials_and_export(self):
        result = run_round_experiments()
        rows = result['measurements']
        self.assertEqual(len(rows), 275)
        self.assertEqual(len(result['summary']), 11)
        for trial in range(1, 26):
            subset = [r for r in rows if r['trial'] == trial]
            self.assertEqual([r['round'] for r in subset], list(range(11)))
            self.assertEqual(subset[0]['changed_bits'], 1)
            self.assertEqual(len({r['flipped_bit_index'] for r in subset}), 1)
        for summary in result['summary']:
            values = [r['changed_bits'] for r in rows if r['round'] == summary['round']]
            self.assertAlmostEqual(summary['mean_changed_bits'], mean(values))
            self.assertAlmostEqual(summary['sample_std_changed_bits'], stdev(values))
        with tempfile.TemporaryDirectory() as directory:
            save_results(result, directory)
            self.assertEqual(json.loads((Path(directory)/'round_experiments.json').read_text()), result)
            with (Path(directory)/'round_trials.csv').open() as file:
                self.assertEqual(len(list(csv.DictReader(file))), 275)

    def test_boundaries(self):
        self.assertIsNone(run_round_experiments(1)['summary'][0]['sample_std_changed_bits'])
        for n in [0, -1, True, 2.5]:
            with self.assertRaises(ValueError):
                run_round_experiments(n)


if __name__ == '__main__':
    unittest.main()
