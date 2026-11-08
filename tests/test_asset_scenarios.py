import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from asset_scenarios import Scenario, cashflow


class CashflowTests(unittest.TestCase):
    def test_base_reconciles(self):
        r = cashflow(Scenario())
        self.assertAlmostEqual(r['gross_yuan_yr'], 8800)
        self.assertAlmostEqual(r['mrv_cost_yuan_yr'], 3000)
        self.assertAlmostEqual(r['farmer_receipt_yuan_yr'], 4060)
        self.assertAlmostEqual(r['farmer_net_yuan_ha_yr'], -59.4)

    def test_no_gain_does_not_create_credits(self):
        r = cashflow(Scenario(assumed_gain_tC_ha_yr=0))
        self.assertEqual(r['gross_yuan_yr'], 0)
        self.assertEqual(r['farmer_receipt_yuan_yr'], 0)
        self.assertEqual(r['project_funding_gap_yuan_yr'], 3000)

    def test_break_even_and_unit_conversion(self):
        price = cashflow(Scenario())['assumed_break_even_price_yuan_tCO2']
        r = cashflow(Scenario(assumed_price_yuan_tCO2=price))
        self.assertAlmostEqual(r['farmer_net_yuan_yr'], 0, places=7)
        self.assertAlmostEqual(r['farmer_net_yuan_mu_yr']*15,r['farmer_net_yuan_ha_yr'])

    def test_bad_inputs(self):
        with self.assertRaises(ValueError):cashflow(Scenario(assumed_buffer_fraction=1))


if __name__ == '__main__':unittest.main()
