"""Explicit hypothetical cash-flow scenarios, independent of observed SOC stock."""
from dataclasses import dataclass, asdict
from itertools import product
from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/asset_scenarios'


@dataclass(frozen=True)
class Scenario:
    area_ha: float = 100
    assumed_gain_tC_ha_yr: float = .3
    assumed_price_yuan_tCO2: float = 100
    assumed_buffer_fraction: float = .2
    assumed_farmer_share: float = .7
    assumed_farm_cost_yuan_ha_yr: float = 100
    assumed_mrv_variable_yuan_ha_yr: float = 20
    assumed_mrv_fixed_yuan_yr: float = 1000


def cashflow(s):
    if s.area_ha <= 0 or any(v < 0 for k, v in asdict(s).items() if k != 'area_ha'):
        raise ValueError('Area must be positive and other scenario inputs nonnegative')
    if not 0 <= s.assumed_buffer_fraction < 1 or not 0 < s.assumed_farmer_share <= 1:
        raise ValueError('Invalid buffer or farmer share')
    quantity = s.area_ha * s.assumed_gain_tC_ha_yr * 44 / 12 * (1 - s.assumed_buffer_fraction)
    gross = quantity * s.assumed_price_yuan_tCO2
    mrv = s.area_ha * s.assumed_mrv_variable_yuan_ha_yr + s.assumed_mrv_fixed_yuan_yr
    distributable = max(0., gross - mrv)
    farmer = s.assumed_farmer_share * distributable
    farm_cost = s.area_ha * s.assumed_farm_cost_yuan_ha_yr
    net = farmer - farm_cost
    break_price = (mrv + farm_cost / s.assumed_farmer_share) / quantity if quantity else math.inf
    return asdict(s) | {'assumed_distributable_tCO2_yr': quantity, 'gross_yuan_yr': gross,
                       'mrv_cost_yuan_yr': mrv, 'distributable_cash_yuan_yr': distributable,
                       'project_funding_gap_yuan_yr': max(0., mrv - gross),
                       'farmer_receipt_yuan_yr': farmer, 'farmer_net_yuan_yr': net,
                       'farmer_net_yuan_ha_yr': net / s.area_ha,
                       'farmer_net_yuan_mu_yr': net / s.area_ha / 15,
                       'farmer_compensation_gap_yuan_yr': max(0., -net),
                       'assumed_break_even_price_yuan_tCO2': break_price,
                       'scenario_is_financially_feasible': gross >= mrv and net >= 0,
                       'evidence_type': 'hypothetical_scenario_not_observed_revenue'}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [cashflow(Scenario(area_ha=a, assumed_gain_tC_ha_yr=q, assumed_price_yuan_tCO2=p,
                              assumed_farm_cost_yuan_ha_yr=c))
            for a, q, p, c in product([1, 10, 100, 1000], [.1, .3, .5], [50, 100, 150], [0, 100, 300])]
    pd.DataFrame(rows).to_csv(OUT / 'cashflow_scenarios.csv', index=False, encoding='utf-8-sig')
    base = cashflow(Scenario())
    (OUT / 'base_scenario.json').write_text(json.dumps(base, ensure_ascii=False, indent=2))
    d = pd.read_csv(ROOT / 'artifacts/fixed_depth/fixed_depth_eci_profiles.csv')
    cards = []
    for level, quantile in [('lower_score', .1), ('median_score', .5), ('higher_score', .9)]:
        row = d.loc[(d.eci_entropy - d.eci_entropy.quantile(quantile)).abs().idxmin()]
        card = {k: row[k].item() if hasattr(row[k], 'item') else row[k]
                for k in ['profile_id', 'latitude', 'longitude', 'Year', 'References',
                          'stock_0_30_tC_ha', 'SOC_0_30_g_kg_thickness_mean', 'eci_entropy']}
        card.update(selection_label=level, selection_rule=f'closest observed entropy score to quantile {quantile}',
                    point_type='public_dataset_sample_not_owned_or_field_verified_plot',
                    observed_carbon_credit=None, observed_income=None)
        cards.append(card)
    pd.DataFrame(cards).to_csv(OUT / 'sample_state_cards.csv', index=False, encoding='utf-8-sig')
    (OUT / 'sample_state_cards.json').write_text(json.dumps(cards, ensure_ascii=False, indent=2))
    prices, gains = [50, 100, 150, 200, 300], [.1, .3, .5, .8, 1.]
    heat = [cashflow(Scenario(assumed_gain_tC_ha_yr=q, assumed_price_yuan_tCO2=p))
            for q, p in product(gains, prices)]
    pd.DataFrame(heat).to_csv(OUT / 'price_gain_sensitivity.csv', index=False, encoding='utf-8-sig')
    z = np.array([r['farmer_net_yuan_ha_yr'] for r in heat]).reshape(len(gains), len(prices))
    fig, ax = plt.subplots(figsize=(7.6, 4.7))
    bound = max(abs(z.min()), abs(z.max()))
    im = ax.imshow(z, cmap='RdYlGn', vmin=-bound, vmax=bound, aspect='auto')
    ax.set_xticks(range(len(prices)), prices); ax.set_yticks(range(len(gains)), gains)
    for i in range(len(gains)):
        for j in range(len(prices)):
            ax.text(j, i, f'{z[i,j]:.1f}', ha='center', va='center', color='black', fontsize=10)
    ax.set(xlabel='Hypothetical price (CNY/t CO2)', ylabel='Assumed annual gain (t C/ha)',
           title='Farmer net income sensitivity (CNY/ha/year)\n100 ha; farm cost 100; MRV 20/ha + 1000; buffer 20%; share 70%')
    fig.colorbar(im, ax=ax, label='CNY/ha/year');fig.tight_layout()
    fig.savefig(OUT / 'fig04_cashflow_sensitivity.png', dpi=180);plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    areas = [1, 10, 100, 1000]
    values = [cashflow(Scenario(area_ha=a))['assumed_break_even_price_yuan_tCO2'] for a in areas]
    ax.plot(areas, values, marker='o', color='#276b4d')
    for x,y in zip(areas,values):ax.annotate(f'{y:.1f}', (x,y), xytext=(5,8), textcoords='offset points')
    ax.set_xscale('log');ax.set_xticks(areas,[str(a) for a in areas])
    ax.set(xlabel='Hypothetical aggregated area (ha)', ylabel='Break-even price (CNY/t CO2)',
           title='Aggregation spreads fixed MRV cost\nOther assumptions held at the base scenario')
    ax.spines[['top','right']].set_visible(False);fig.tight_layout()
    fig.savefig(OUT / 'fig05_scale_break_even.png', dpi=180);plt.close(fig)
    print(json.dumps(base, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
