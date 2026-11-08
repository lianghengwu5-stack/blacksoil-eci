"""Unit conversion and depth-coverage checks independent of project inputs."""
import sys
from pathlib import Path
import unittest
import math
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_results import integrate_profile


class DepthIntegrationTests(unittest.TestCase):
    def test_known_uniform_profile(self):
        # 2 kg C/m2 per 10 cm gives 6 kg/m2 = 60 tC/ha to 30 cm.
        stock, status = integrate_profile([(0, 10, 2), (10, 40, 6)])
        self.assertEqual(status, 'complete')
        self.assertAlmostEqual(stock, 60.)

    def test_missing_bottom_is_not_30cm(self):
        stock, status = integrate_profile([(0, 25, 5)])
        self.assertEqual(status, 'incomplete_depth')
        self.assertTrue(math.isnan(stock))

    def test_gap_and_duplicate_layers_are_rejected(self):
        self.assertEqual(integrate_profile([(0, 10, 2), (15, 30, 3)])[1], 'gap')
        self.assertEqual(integrate_profile([(0, 20, 4), (10, 30, 4)])[1], 'overlap')

    def test_nonphysical_layer_is_rejected(self):
        self.assertEqual(integrate_profile([(0, 30, -1)])[1], 'invalid_layer')


if __name__ == '__main__':
    unittest.main()
