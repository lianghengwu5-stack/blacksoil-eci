"""Scientific invariants and independent reconciliation checks."""
import math
import json
from analyze import response, valuation, ROOT

r=response([2],[1],[0.5],[1],[[0,30]])
assert math.isclose(r["index"],100)  # Improvement can conceal decline.
assert r["component_min"]==50 and r["point_estimate_decline_layers"]
for a,b in [(1,1),(2,1),(0.5,1)]:
    x=response([a],[b],[a],[b],[[0,30]])["index"]
    y=response([b],[a],[b],[a],[[0,30]])["index"]
    assert math.isclose(x*y,10000)
assert math.isclose(response([2,2],[1,1],[3,3],[1,1],[[0,10],[10,30]])["index"],100*math.sqrt(6))
try:
    response([None],[1],[1],[1],[[0,30]])
except ValueError:
    pass
else:
    raise AssertionError("Missing observations silently accepted")
assert math.isclose(valuation(1,70.76),17.29688888888889)
d=json.loads((ROOT/"results/results.json").read_text())
assert len(d["source_arithmetic_flags"])==2
assert {r["difference"] for r in d["source_arithmetic_flags"]}=={375,-18}
x=next(r for r in d["margin_contrasts"] if r["year"]==2022 and r["treatment"]=="CK" and r["control"]=="WS20")
assert math.isclose(x["delta_margin_recalculated"],126.8)
x=next(r for r in d["luancheng_carbon"] if r["start"]==2001 and r["end"]==2018)
assert math.isclose(x["additional_tC_ha_year"],-5.7/17)
assert all(r["eligible_cash_income"] is None for r in d["liang_carbon"])
print("PASS: units, reciprocal contrasts, depth weights, hidden decline flag, missing data, source arithmetic and carbon additionality")
