"""Recompute final-manuscript analyses from archived published values.
Parameter grids are scenarios, never observations. Sources are snapshotted with hashes.
"""
from pathlib import Path
import json,csv,hashlib,itertools,math
import numpy as np
P=Path(__file__).resolve().parent;B=P.parent;S=B/'research_synthesis_20261109';V=S/'regional_lishu/v2'
paths={'yang':V/'yang2022_tables.json','water':S/'results/dynamic_water_index.json','benchmark':V/'index_benchmark.json','farm':S/'regional_lishu/published_data.json','economics':S/'mainline_v10/economic_comparisons.json','pairs':S/'mainline_v10/paired_effects.json','baseline':S/'mainline_v10/baseline_comparisons.json','frontier':S/'mainline_v10/choice_and_compensation.json','rules':S/'results/index_added_value_v8.json','carbon_summary':B/'artifacts/reassessment/summary.json'}
archived=json.loads((P/'data/source_snapshot.json').read_text()) if (P/'data/source_snapshot.json').exists() else {}
snapshot={}
for key,path in paths.items():
 if path.exists():snapshot[key]={'path':str(path.relative_to(B)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'data':json.loads(path.read_text())}
 else:snapshot[key]=archived[key]
stock_path=B/'artifacts/reassessment/carbon_profiles.csv'
if stock_path.exists():snapshot['profiles']={'path':str(stock_path.relative_to(B)),'sha256':hashlib.sha256(stock_path.read_bytes()).hexdigest(),'data':list(csv.DictReader(stock_path.open(encoding='utf-8-sig')))}
else:snapshot['profiles']=archived['profiles']
(P/'data/source_snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
d={k:v['data'] for k,v in snapshot.items()};checks=[]
def check(name,ok):
 assert ok,name
 checks.append(name)
ys=np.array([r['yield_kg_ha_figure'] for r in d['yang']['records']]);cs=np.array([r['SOC_Mg_ha_figure'] for r in d['yang']['records']])
frequency_gain=((ys[1]+ys[3])/(ys[0]+ys[2])-1)*100
same_dose=[100*(ys[1]/ys[0]-1),100*(ys[3]/ys[2]-1)]
w=np.linspace(0,1,1001);score=100*(cs[None,:]/cs[0])**w[:,None]*(ys[None,:]/ys[0])**(1-w[:,None])
best=np.argmax(score,axis=1);switches=[]
for i in range(1,len(w)):
 if best[i]!=best[i-1]:switches.append({'from':d['yang']['records'][best[i-1]]['treatment'],'to':d['yang']['records'][best[i]]['treatment'],'interval':[float(w[i-1]),float(w[i])]})
check('Frequency gain agrees with source abstract',abs(frequency_gain-14.1)<.1)
water=[]
for r in d['water']['results']:
 a=np.asarray(r['original_table3_percent']);v=a@np.array([.125,.125,.25,.5])
 check('Water stage scores '+str(r['year'])+r['treatment'],np.allclose(v,r['candidate_diagnostics']['primary_0_40_thickness']['stage_scores']))
 water.append({'year':r['year'],'treatment':r['treatment'],'rain_type':r['rain_type'],'stages':v.tolist(),'minimum':float(v.min()),'worst':int(v.argmin()),'min_0_20':float((a[:,:3]@np.array([.25,.25,.5])).min()),'min_equal':float(a.mean(axis=1).min())})
farm=d['farm'];totals={}
for g in ['CRT','SRTS']:
 costs=sum(r[g] for r in farm['cost_rows'])/15;yield_mu=farm['yield_t_ha'][g]*1000/15;rev=yield_mu*farm['price_CNY_kg'];emissions=sum(r[g]*r['emission_factor'] for r in farm['input_rows'])/15
 totals[g]={'yield':yield_mu,'revenue':rev,'cost':costs,'balance':rev-costs,'emissions':emissions}
 check('Source cost total '+g,abs(costs*15-farm['reported_totals_CNY_ha'][g]['cost'])<1e-7)
 check('Source emissions '+g,abs(emissions*15-farm['reported_carbon_kgCO2e_ha'][g])<.01)
components=[('粮食增收',totals['SRTS']['revenue']-totals['CRT']['revenue'])]
for label,items in [('机械节本',farm['cost_rows'][:7]),('农资节本',farm['cost_rows'][7:10]),('人工节本',farm['cost_rows'][10:])]:components.append((label,sum(r['CRT']-r['SRTS'] for r in items)/15))
gain=totals['SRTS']['balance']-totals['CRT']['balance'];saving=sum(x[1] for x in components[1:]);avoided=totals['CRT']['emissions']-totals['SRTS']['emissions']
check('Farm budget decomposition closes',abs(sum(v for _,v in components)-gain)<1e-7)
check('Changchun decompositions close',all(abs(r['revenue_change']+r['cost_saving']-r['balance_change'])<1e-7 for r in d['economics']['changchun']))
check('Paired records preserve three experiments',len(d['pairs'])==21 and len({r['experiment'] for r in d['pairs']})==3)
check('Rule equivalence on 12 records',len(d['rules']['rows'])==12 and all(r['score_targets_met']==(r['direct_check']['status']=='point_targets_met') for r in d['rules']['rows']))
check('Four microplot geometric shortfalls retained',sum(r['geometric_hides_point_shortfall'] for r in d['rules']['rows'])==4)
check('Source stock median',abs(np.median([float(r['stock_0_30_tC_ha']) for r in d['profiles']])-d['carbon_summary']['stock_summary'][0]['median'])<1e-9)
summary={'frequency_gain_pct':frequency_gain,'same_dose_frequency_gain_pct':same_dose,'weight_switches':switches,'water':water,'farm_totals':totals,'components':components,'gain':gain,'cost_saving':saving,'saving_share_pct':100*saving/gain,'avoided_emissions_kg_mu':avoided,'carbon_reference_value':avoided/1000*70.76,'benchmark_field_reduction_pct':100*(29-6)/29,'benchmark_r2_increment':.56-.654**2,'boundaries':[{'additional_support':s,'extra_cost_limit_at_observed_yield':gain+s,'yield_loss_limit_at_zero_extra_cost':(saving+s)/2.3} for s in [0,80,105]],'dehui_means':{crop:float(np.mean([r['NT_minus_RT'] for r in d['economics']['dehui'] if r['crop']==crop])) for crop in ['maize','soybean']},'checks':checks}
(P/'data/analysis_results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
for name,rows in [('water_stage_analysis',water),('yang_treatment_means',d['yang']['records']),('paired_soil_yield',d['pairs']),('baseline_comparisons',d['baseline']),('changchun_budget',d['economics']['changchun']),('dehui_annual',d['economics']['dehui'])]:
 with (P/'data'/f'{name}.csv').open('w',encoding='utf-8-sig',newline='') as f:
  keys=list(dict.fromkeys(k for r in rows for k in r));writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows)
print(json.dumps({k:summary[k] for k in ['frequency_gain_pct','same_dose_frequency_gain_pct','weight_switches','gain','cost_saving','saving_share_pct','benchmark_field_reduction_pct','dehui_means']},ensure_ascii=False,indent=2))
