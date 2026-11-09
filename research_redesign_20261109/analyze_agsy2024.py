"""Paired ecological-economic case, preserving original table discrepancies."""
import json
import csv
import math
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    d=json.loads((ROOT/"data/agsy2024.json").read_text())
    base=json.loads((ROOT/"data/evidence.json").read_text())
    supplement=json.loads((ROOT/"data/agsy2024_supplement.json").read_text())
    soil={}
    for row in supplement["tables_verbatim"]["S1"][1:]:
        soil[row[0]]={}
        for metric,cell in zip(["SOC","TN","TP","TK"],row[1:]):
            match=re.fullmatch(r"([\d.]+) ± ([\d.]+) ([a-z]+)",cell)
            assert match, cell
            mean,spread,letters=match.groups()
            soil[row[0]][metric]={"mean_g_kg":float(mean),"reported_plus_minus":float(spread),"letters":letters,"spread_kind":"not defined in supplementary file"}
    factor=d["conversion"]["yuan_per_usd_source"]/d["conversion"]["mu_per_ha"]
    costs={t:sum(x[t]*x["unit_price_usd"] for x in d["table2_inputs"]) for t in ["CT","MP","NT"]}
    rows=[]; comparisons=[]; audit=[]
    for year in ["2020","2021"]:
        for t in ["CT","MP","NT"]:
            income=d["table5_grain_revenue_usd_ha"][year][t]
            listed=d["table5_cost_total_usd_ha"][t]
            neeb=d["table6_neeb_usd_ha"][year][t]
            implied_yield=d["energy_output_MJ_ha"][year][t]/d["grain_energy_MJ_kg"]
            if abs(income-listed-neeb)>1:
                audit.append({"year":int(year),"treatment":t,"table5_revenue_less_cost_usd_ha":income-listed,"table6_neeb_usd_ha":neeb,"discrepancy_usd_ha":income-listed-neeb,"energy_implied_revenue_usd_ha":implied_yield*d["price_usd_kg"][year],"energy_implied_neeb_usd_ha":implied_yield*d["price_usd_kg"][year]-costs[t],"action":"retain all branches; energy-derived values are cross-checks, not additional observations"})
            rows.append({"year":int(year),"treatment":t,"grain_revenue_yuan_mu":income*factor,"table5_material_cost_yuan_mu":listed*factor,"table2_material_cost_recalculated_yuan_mu":costs[t]*factor,"table6_margin_yuan_mu":neeb*factor,"table6_margin_se_yuan_mu":d["table6_neeb_se_usd_ha"][year][t]*factor,"table5_margin_recalculated_yuan_mu":(income-listed)*factor,"energy_implied_grain_yield_kg_ha":implied_yield,"source_net_ghg_kgCO2e_ha":d["aighg_published_kgCO2e_ha"][t]+d["table3_soil_gwp_kgCO2e_ha"][year][t],"cf_published":d["table6_cf_kgCO2e_kg"][year][t]})
        for t,c in [("NT","CT"),("NT","MP"),("MP","CT")]:
            p={r["treatment"]:r for r in rows if r["year"]==int(year)}
            avoided=p[c]["source_net_ghg_kgCO2e_ha"]-p[t]["source_net_ghg_kgCO2e_ha"]
            soil_avoided=d["table3_soil_gwp_kgCO2e_ha"][year][c]-d["table3_soil_gwp_kgCO2e_ha"][year][t]
            diesel=(next(x for x in d["table2_inputs"] if x["item"]=="diesel")[c]-next(x for x in d["table2_inputs"] if x["item"]=="diesel")[t])*d["diesel_ghg_kgCO2e_L"]
            assert math.isclose(avoided,soil_avoided+diesel,abs_tol=1e-8)
            comparisons.append({"year":int(year),"treatment":t,"control":c,"margin_delta_table6_yuan_mu":p[t]["table6_margin_yuan_mu"]-p[c]["table6_margin_yuan_mu"],"margin_delta_table5_yuan_mu":p[t]["table5_margin_recalculated_yuan_mu"]-p[c]["table5_margin_recalculated_yuan_mu"],"table2_material_cost_saving_yuan_mu":(costs[c]-costs[t])*factor,"avoided_input_ghg_kgCO2e_ha":diesel,"avoided_soil_nonCO2_ghg_kgCO2e_ha":soil_avoided,"avoided_total_kgCO2e_ha":avoided,"avoided_total_kgCO2e_mu":avoided/15,"emissions_reduction_pct":100*avoided/p[c]["source_net_ghg_kgCO2e_ha"],"benchmark_value_yuan_mu":avoided/1000/15*base["ccer2025"]["mean"],"grain_yield_change_implied_pct":100*(p[t]["energy_implied_grain_yield_kg_ha"]/p[c]["energy_implied_grain_yield_kg_ha"]-1),"net_profit_delta":None,"soil_stock_increment":None,"verified_carbon_revenue":None})
    soil_contrasts=[]
    for t,c in [("NT","CT"),("NT","MP"),("MP","CT")]:
        for metric in ["SOC","TN","TP","TK"]:
            a,b=soil[t][metric],soil[c][metric]
            soil_contrasts.append({"year":2020,"depth_cm":"0-20","treatment":t,"control":c,"metric":metric,"response_pct":100*(a["mean_g_kg"]/b["mean_g_kg"]-1),"source_letters_differ":not bool(set(a["letters"]) & set(b["letters"])),"source_letters":a["letters"]+"/"+b["letters"],"soil_stock_increment":None})
    thresholds=[{"year":r["year"],"treatment":r["treatment"],"control":r["control"],"uncovered_burden_threshold_table6_yuan_mu":r["margin_delta_table6_yuan_mu"],"uncovered_burden_threshold_table5_yuan_mu":r["margin_delta_table5_yuan_mu"],"remaining_burden_observed":None,"required_compensation_yuan_mu":None} for r in comparisons]
    out={"source":d["doi"],"unit":"CNY/mu/year unless stated; growing-season soil flux only", "baseline_and_treatments":rows,"contrasts":comparisons,"soil_2020":soil,"soil_contrasts":soil_contrasts,"compensation_thresholds":thresholds,"audit":audit,"limits":d["limitations"],"supplement_limits":supplement["interpretation_zh"],"subsidy_rule":"Let U = omitted incremental cost + lost net straw value + supported transition risk - realized carbon net cash - existing actual subsidy benefit. Incremental compensation = max(0, U - listed material margin gain). U is signed and unobserved; no default of zero. This is an accounting threshold, not an optimal subsidy estimate."}
    (ROOT/"results/agsy2024_results.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
    for name,rs in [("agsy2024_budget",rows),("agsy2024_contrasts",comparisons),("agsy2024_soil_contrasts",soil_contrasts),("agsy2024_compensation_thresholds",thresholds)]:
        with (ROOT/"results"/(name+".csv")).open("w",newline="",encoding="utf-8-sig") as f:
            w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
    assert len(audit)==1 and audit[0]["discrepancy_usd_ha"]==10
    ntct=[x for x in comparisons if x["treatment"]=="NT" and x["control"]=="CT"]
    assert math.isclose(ntct[0]["margin_delta_table6_yuan_mu"],78.08)
    assert math.isclose(ntct[1]["margin_delta_table6_yuan_mu"],68.69333333333333)
    assert math.isclose(ntct[0]["avoided_total_kgCO2e_ha"],799.39)
    assert all(x["soil_stock_increment"] is None for x in comparisons)
    soc={r["treatment"]+"_vs_"+r["control"]:r for r in soil_contrasts if r["metric"]=="SOC"}
    for key,value in supplement["derived_SOC_concentration_percent"].items():
        assert math.isclose(soc[key]["response_pct"],value)
    assert soc["NT_vs_CT"]["source_letters_differ"] and not soc["NT_vs_MP"]["source_letters_differ"]
    # Multiplicative consistency across the three paired controls.
    assert math.isclose((1+soc["NT_vs_MP"]["response_pct"]/100)*(1+soc["MP_vs_CT"]["response_pct"]/100),1+soc["NT_vs_CT"]["response_pct"]/100)
    for year in [2020,2021]:
        pairs={(r["treatment"],r["control"]):r for r in comparisons if r["year"]==year}
        for field in ["margin_delta_table6_yuan_mu","avoided_total_kgCO2e_ha"]:
            assert math.isclose(pairs["NT","CT"][field],pairs["NT","MP"][field]+pairs["MP","CT"][field],abs_tol=1e-8)
    assert all(r["required_compensation_yuan_mu"] is None for r in thresholds)
    print(json.dumps({"NT_CT":ntct,"audit":audit,"checks":"PASS: source discrepancy, historical FX/area conversion, avoided-emission decomposition; no invented SOC increment"},ensure_ascii=False,indent=2))

if __name__=="__main__":main()
