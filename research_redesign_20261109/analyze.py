"""Reproduce published-mean contrasts. Python standard library only.

No synthetic plot records, missing-value imputation, inferred significance,
or credit issuance. All financial amounts are CNY/mu/year unless specified.
"""
from pathlib import Path
import json
import math
import csv

ROOT = Path(__file__).resolve().parent


def response(soc_t, soc_c, mwd_t, mwd_c, depths, weight=0.5, max_depth=30):
    """Thickness-weighted log ratios. Concentration response, NOT C stock."""
    if not 0 <= weight <= 1:
        raise ValueError("Weight outside [0,1]")
    if not (len(soc_t) == len(soc_c) == len(mwd_t) == len(mwd_c) == len(depths)):
        raise ValueError("Unmatched soil layers")
    if depths[0][0] != 0 or any(depths[i][1] != depths[i+1][0] for i in range(len(depths)-1)):
        raise ValueError("Soil profile has gaps/overlap")
    layers = []
    for a,b,c,d,(lo,hi) in zip(soc_t,soc_c,mwd_t,mwd_c,depths):
        h = max(0, min(hi,max_depth)-lo)
        if h == 0:
            continue
        if any(x is None or not math.isfinite(x) or x <= 0 for x in (a,b,c,d)):
            raise ValueError("Missing/non-positive input; index unavailable")
        layers.append({"depth_cm":[lo,min(hi,max_depth)],"h":h,"soc_ratio":a/b,"mwd_ratio":c/d})
    if sum(l["h"] for l in layers) != max_depth:
        raise ValueError("Requested depth not covered")
    log_c = sum(l["h"]*math.log(l["soc_ratio"]) for l in layers)/max_depth
    log_a = sum(l["h"]*math.log(l["mwd_ratio"]) for l in layers)/max_depth
    return {"index":100*math.exp(weight*log_c+(1-weight)*log_a),
            "carbon_concentration_response":100*math.exp(log_c),
            "aggregate_response":100*math.exp(log_a),
            "component_min":100*math.exp(min(log_c,log_a)),
            "point_estimate_decline_layers":[l for l in layers if min(l["soc_ratio"],l["mwd_ratio"])<1],
            "layers":layers}


def contrast(study, treatment, control, weight=0.5, depth=30):
    return response(study["soc_g_kg"][treatment],study["soc_g_kg"][control],
                    study["mwd_mm"][treatment],study["mwd_mm"][control],
                    study["depth_cm"],weight,depth)


def mean(xs):
    return sum(xs)/len(xs)


def valuation(rate, price):
    return rate*(44/12)/15*price


def main():
    data=json.loads((ROOT/"data/evidence.json").read_text())
    out={"status":"Descriptive prototype from published means; no composite CI or credit certification", "index":[],"sensitivity":[]}
    pairs={"liang2021":[("SM","CK"),("SI","CK")],
           "chen2021":[("NT","CT_IR"),("NT","CT_BR"),("ST_IR","CT_IR"),("ST_BR","CT_BR")]}
    for key, cs in pairs.items():
        for t,c in cs:
            out["index"].append({"study":key,"treatment":t,"control":c,"depth_cm":30,**contrast(data[key],t,c)})
            for depth in ([10,20,30,40] if key=="liang2021" else [5,10,20,30]):
                for w in [0,0.25,0.5,0.75,1]:
                    r=contrast(data[key],t,c,w,depth)
                    out["sensitivity"].append({"study":key,"treatment":t,"control":c,"depth_cm":depth,"carbon_weight":w,"index":r["index"]})

    # Unknown field area fractions: endpoints give rigorous bounds for NT vs CT
    # because CT_IR exceeds CT_BR for both indicators in every layer. ST vs CT
    # needs independent fractions; sweep a grid, explicitly not a confidence CI.
    s=data["chen2021"]
    grid=[]
    for f_t in [i/100 for i in range(101)]:
        for f_c in [i/100 for i in range(101)]:
            mix=lambda metric,prefix,f:[f*a+(1-f)*b for a,b in zip(s[metric][prefix+"_IR"],s[metric][prefix+"_BR"])]
            r=response(mix("soc_g_kg","ST",f_t),mix("soc_g_kg","CT",f_c),mix("mwd_mm","ST",f_t),mix("mwd_mm","CT",f_c),s["depth_cm"])
            grid.append((r["index"],f_t,f_c))
    out["chen_spatial_grid"]={"min":min(grid),"max":max(grid),"meaning":"ST and CT IR area fractions varied independently 0..1, step .01; hypothetical weights, not measured coverage or statistical uncertainty"}

    out["yields"]=[]
    for key,control,groups in [("chen2021","CT",["NT","ST"]),("eco2024","CK",["T1","T2","T3"])]:
        s=data[key]; years=s.get("yield_years",s.get("years")); start=1 if key=="chen2021" else 0
        for t in groups:
            annual=[{"year":y,"treatment":a,"control":b,"delta_kg_ha":a-b,"change_pct":100*(a/b-1)} for y,a,b in zip(years[start:],s["yield_kg_ha"][t][start:],s["yield_kg_ha"][control][start:])]
            mt=mean([r["treatment"] for r in annual]); mc=mean([r["control"] for r in annual])
            out["yields"].append({"study":key,"treatment":t,"control":control,"annual":annual,"mean_treatment_kg_ha":mt,"mean_control_kg_ha":mc,"ratio_of_means_pct":100*(mt/mc-1),"delta_kg_mu":(mt-mc)/15})
    for t in ["SM","SI"]:
        ys=data["liang2021"]["yield_dry_Mg_ha_year"]
        out["yields"].append({"study":"liang2021","treatment":t,"control":"CK","ratio_of_means_pct":100*(ys[t]/ys["CK"]-1),"delta_dry_kg_mu":(ys[t]-ys["CK"])*1000/15,"no_price_conversion":"Dry mass; market moisture unspecified"})

    rows=[dict(zip(data["xu2024"]["columns"],r)) for r in data["xu2024"]["rows"]]
    out["trial_margin"]=[]; out["source_arithmetic_flags"]=[]; out["margin_contrasts"]=[]
    for r in rows:
        calc=r["revenue"]-r["total_cost"]
        if calc!=r["net_reported"]:
            out["source_arithmetic_flags"].append({"study":"xu2024","year":r["year"],"treatment":r["treatment"],"published":r["net_reported"],"recalculated":calc,"difference":r["net_reported"]-calc,"unit":"CNY/ha"})
        out["trial_margin"].append({"year":r["year"],"treatment":r["treatment"],"revenue":r["revenue"]/15,"listed_cost":r["total_cost"]/15,"margin_recalculated":calc/15,"margin_reported":r["net_reported"]/15})
    for year in [2021,2022]:
        sr={r["treatment"]:r for r in rows if r["year"]==year}
        for t,c,label in [("CK","WS20","no-till vs rotary; same straw/fertilizer"),("CK","WS40","no-till vs subsoil; same straw/fertilizer"),("YB","CK","added manure under no-till, not a tillage effect")]:
            revenue=(sr[t]["revenue"]-sr[c]["revenue"])/15
            cost=(sr[t]["total_cost"]-sr[c]["total_cost"])/15
            out["margin_contrasts"].append({"year":year,"treatment":t,"control":c,"meaning":label,"delta_revenue":revenue,"delta_listed_cost":cost,"delta_margin_recalculated":revenue-cost,"delta_margin_published":(sr[t]["net_reported"]-sr[c]["net_reported"])/15})
    out["regional_baselines"]=[{**r,"profit_recalculated":r["revenue"]-r["total_cost"],"unit":"CNY/mu/year"} for r in data["baselines"]]

    p=data["ccer2025"]; s=data["liang2021"]; out["liang_carbon"]=[]
    for t in ["SM","SI"]:
        rates={"endpoint_stocks_common_initial":(sum(s["stock_tC_ha"][t])-sum(s["stock_tC_ha"]["CK"]))/6,
               "published_sequestered_quantities":(sum(s["sequestered_tC_ha_0_20_20_40"][t])-sum(s["sequestered_tC_ha_0_20_20_40"]["CK"]))/6,
               "published_rates":sum(s["rate_tC_ha_year_0_20_20_40"][t])-sum(s["rate_tC_ha_year_0_20_20_40"]["CK"])}
        for method,rate in rates.items():
            out["liang_carbon"].append({"treatment":t,"control":"CK","method":method,"additional_tC_ha_year":rate,"additional_tCO2_mu_year":rate*44/12/15,"value_at_2025_mean":valuation(rate,p["mean"]),"value_at_daily_price_min":valuation(rate,p["daily_mean_min"]),"value_at_daily_price_max":valuation(rate,p["daily_mean_max"]),"eligible_cash_income":None,"status":"unresolved source reconciliation; fixed-depth soil-C benchmark valuation only"})
    # All preselected windows; no choosing only periods with positive sequestration.
    s=data["luancheng2022"]; stocks=s["stock_0_30_tC_ha"]; years=s["years"]; out["luancheng_carbon"]=[]
    for start,end,control in [(2001,2006,"CT"),(2006,2011,"CT"),(2011,2018,"CT"),(2001,2018,"CT"),(2006,2018,"CK"),(2011,2018,"CK")]:
        i,j=years.index(start),years.index(end)
        rate=((stocks["NT"][j]-stocks["NT"][i])-(stocks[control][j]-stocks[control][i]))/(end-start)
        out["luancheng_carbon"].append({"start":start,"end":end,"treatment":"NT","control":control,"additional_tC_ha_year":rate,"signed_value_at_2025_mean":valuation(rate,p["mean"]),"eligible_cash_income":None})
    out["subsidy"]={"formula":"max(0, incremental_cost + lost_straw_net_revenue + measured_transition_risk - incremental_grain_revenue - verified_carbon_net_cash - existing_actual_benefit)","scope":"Incremental adoption compensation, not compensation of all baseline farm losses", "unknown_inputs":"Keep missing costs/risk/actual subsidy receipts unknown; do not replace with zero", "policy_caps":data["jilin2026"],"ecology_role":"Index and components screen/monitor soil outcomes; no arbitrary yuan per index point", "carbon_cash_rule":"No credit claim or carbon receipts have been verified for these experimental plots"}
    (ROOT/"results").mkdir(exist_ok=True)
    (ROOT/"results/results.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
    for key in ["sensitivity","margin_contrasts","liang_carbon","luancheng_carbon"]:
        with (ROOT/"results"/(key+".csv")).open("w",newline="",encoding="utf-8-sig") as f:
            w=csv.DictWriter(f,fieldnames=list(out[key][0]));w.writeheader();w.writerows(out[key])
    brief={"index":[{k:r[k] for k in ["study","treatment","control","index","component_min"]} for r in out["index"]],"yields":[{k:r[k] for k in ["study","treatment","ratio_of_means_pct"]} for r in out["yields"]],"carbon":out["liang_carbon"],"arithmetic_flags":out["source_arithmetic_flags"]}
    print(json.dumps(brief,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
