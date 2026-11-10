"""可更新的措施选择与收入补差计算。金额均为元/亩/年，产量为kg/亩。
python decision_calculator.py farm_input_template.json
空白表示缺测，0表示确认无此项。测试夹具不用于研究结果。
"""
import json, sys, math
from pathlib import Path

def calculate(data):
    required=['yield_kg_mu','price_CNY_kg','production_cost_CNY_mu',
              'land_cost_CNY_mu','annual_transition_cost_CNY_mu',
              'existing_support_CNY_mu','realized_carbon_net_cash_CNY_mu']
    missing=[];rows=[]
    minima=data.get('ecological_minima',{})
    for k,v in minima.items():
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0:
            raise ValueError('保护目标下限须为有限正数')
    if data.get('accounting_scope')!='complete_farm_account':missing.append('accounting_scope')
    if not data.get('period'):missing.append('period')
    if not data.get('alternatives'):missing.append('alternatives')
    for a in data.get('alternatives',[]):
        name=a.get('id','未命名措施')
        for k in required:
            if not isinstance(a.get(k),(int,float)) or isinstance(a.get(k),bool) or not math.isfinite(a.get(k,math.nan)):
                missing.append(f'{name}.{k}')
        if not isinstance(a.get('available'),bool):missing.append(f'{name}.available')
        if a.get('available'):
            for k in data.get('ecological_minima',{}):
                value=a.get('indicators',{}).get(k)
                if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
                    missing.append(f'{name}.indicators.{k}')
    if missing:return {'status':'需要补充数据','missing':missing}
    ids=[a['id'] for a in data['alternatives']]
    if len(set(ids))!=len(ids):raise ValueError('措施ID重复')
    for a in data['alternatives']:
        if not a['available']:continue
        if any(a[k]<0 for k in ['yield_kg_mu','price_CNY_kg','production_cost_CNY_mu','land_cost_CNY_mu','annual_transition_cost_CNY_mu','existing_support_CNY_mu']):
            raise ValueError('产量、价格与成本补助不得为负值')
        balance=a['yield_kg_mu']*a['price_CNY_kg']-a['production_cost_CNY_mu']-a['land_cost_CNY_mu']-a['annual_transition_cost_CNY_mu']+a['existing_support_CNY_mu']+a['realized_carbon_net_cash_CNY_mu']
        passed=all(a['indicators'][k]>=v for k,v in data.get('ecological_minima',{}).items())
        ratios={k:100*a['indicators'][k]/v for k,v in minima.items()}
        limiting=min(ratios,key=ratios.get) if ratios else None
        rows.append(dict(id=a['id'],balance_CNY_mu=balance,meets_targets=passed,
                         target_completion_percent=ratios.get(limiting),limiting_indicator=limiting))
    if not rows:return {'status':'没有可用备选措施'}
    best=max(r['balance_CNY_mu'] for r in rows)
    for r in rows:r['additional_income_compensation_CNY_mu']=max(0,best-r['balance_CNY_mu'])
    eligible=[r for r in rows if r['meets_targets']]
    chosen=max(eligible,key=lambda r:r['balance_CNY_mu']) if eligible else None
    return {'status':'计算完成','period':data['period'],'alternatives':rows,'selected':chosen,
            'scope':'收入补差；已有补贴与实际碳净收入只计一次。生态奖励另按服务量和项目规则确定。'}

def selftest():
    def option(i,y=100,cost=100,pay=0,cover=60):
        return dict(id=i,available=True,yield_kg_mu=y,price_CNY_kg=2,
         production_cost_CNY_mu=cost,land_cost_CNY_mu=0,annual_transition_cost_CNY_mu=0,
         existing_support_CNY_mu=pay,realized_carbon_net_cash_CNY_mu=0,indicators={'cover':cover})
    d=dict(accounting_scope='complete_farm_account',period='TEST_ONLY',ecological_minima={'cover':60},
           alternatives=[option('baseline',cover=0),option('target',y=90)])
    assert calculate(d)['selected']['additional_income_compensation_CNY_mu']==20
    d['alternatives'][1]['existing_support_CNY_mu']=15
    assert calculate(d)['selected']['additional_income_compensation_CNY_mu']==5
    d['alternatives'].append(option('better_available',y=120,cover=0))
    assert calculate(d)['selected']['additional_income_compensation_CNY_mu']==45
    d['alternatives'][1]['realized_carbon_net_cash_CNY_mu']=5
    assert calculate(d)['selected']['additional_income_compensation_CNY_mu']==40
    d['alternatives'][1]['land_cost_CNY_mu']=None
    assert calculate(d)['status']=='需要补充数据'
    d['alternatives'][1]['land_cost_CNY_mu']=0
    assert calculate(d)['status']=='计算完成'
    d['alternatives'][1]['indicators']['cover']=59
    assert calculate(d)['selected'] is None
    d['alternatives'][1]['indicators']['cover']=60
    assert calculate(d)['selected']['id']=='target'
    assert calculate(d)['selected']['target_completion_percent']==100
    d['alternatives'][1]['indicators']['cover']=float('nan')
    assert calculate(d)['status']=='需要补充数据'
    return 10

if __name__=='__main__':
    if len(sys.argv)>1:
        print(json.dumps(calculate(json.loads(Path(sys.argv[1]).read_text())),ensure_ascii=False,indent=2))
    else: print(f'{selftest()}项核算边界检查通过')
