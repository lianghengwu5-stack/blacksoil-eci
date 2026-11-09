export async function appendResearch({presentation,input}) {
const FONT='PingFang SC', green='#246349', blue='#39729B', ink='#172A25', muted='#52685D';
function text(s,v,x,y,w,h,size=28,color=ink,bold=false){let q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});q.text=v;q.text.style={typeface:FONT,fontSize:size,color,bold};return q;}
function slide(title,source){const s=presentation.slides.add({width:1280,height:720});s.background.fill='#FAFBF9';text(s,title,64,48,1152,95,42,ink,true);text(s,source,64,655,1100,45,16,muted);text(s,String(presentation.slides.items.length).padStart(2,'0'),1180,655,60,30,18,muted);return s;}
function table(s,values,widths,top=170,height=310){const t=s.tables.add({rows:values.length,columns:values[0].length,left:64,top,width:1152,height,columnWidths:widths,values});t.borders.assign({fill:'#D4DED7',width:1});for(let i=0;i<values.length;i++)for(let j=0;j<values[0].length;j++){const c=t.getCell(i,j);c.fill=i===0?'#E3ECE5':'#FFFFFF';c.text.style={typeface:FONT,fontSize:22,color:ink,bold:i===0};}return t;}
function chart(s,cats,series,max=160,title='',type='bar'){s.charts.add(type,{position:{left:65,top:178,width:1125,height:365},title,titleTextStyle:{fontSize:22,fill:ink},categories:cats,series,hasLegend:series.length>1,legend:{position:'bottom',textStyle:{fontSize:20,fill:ink}},barOptions:{direction:'column',grouping:'clustered',gapWidth:95},xAxis:{textStyle:{fontSize:22,fill:ink}},yAxis:{min:0,max:max,numberFormatCode:'0',textStyle:{fontSize:19,fill:ink},majorGridlines:{fill:'#DAE1DC',width:1}},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{fontSize:20,fill:ink}}});}
if(input.batch===1){
let s=slide('研究问题是土壤改善能否转化为农户收益','研究定位：公开证据的案例再分析，东北黑土为重点');
text(s,'生态响应',65,185,340,55,34,green,true);text(s,'有机碳与结构是否改善？\n深层是否也有改善？',65,265,340,190,28);
text(s,'经营变化',460,185,340,55,34,green,true);text(s,'粮食收入与成本如何变？\n农户新增负担有多少？',460,265,340,190,28);
text(s,'补偿依据',855,185,340,55,34,green,true);text(s,'区分私人损失与公共收益\n按可核查证据确定补偿',855,265,340,190,28);
text(s,'土壤评分、经营利润、土壤增汇与避免排放分别核算。',65,520,1120,80,32,green,true);
s=slide('六项核心田间研究各自回答不同问题','来源及全文定位见研究报告参考文献 [1–5,10]');
table(s,[['地区与来源','核心证据','用途'],['公主岭 梁尧等2021','分层SOC与水稳性MWD','指数与固定深度碳'],['海伦 Chen等2021','行内 行间 土壤与产量','空间参照敏感性'],['公主岭 李瑞平等2024','覆盖与条带措施产量','冷凉区适配'],['齐齐哈尔 徐超等2024','产值与所列成本','试验经营差额'],['栾城 Agronomy 2022','2001–2018年碳变化','长期与短期对照'],['长春 Zhang等2024及附表','材料预算 排放 SOC','同试验联合比较']],[340,470,342],160,405);
text(s,'指数只在两项具备必要指标的研究中计算；不拼接虚构农户。',65,580,1130,55,26,green);
s=slide('指数浓缩两个土壤功能并保留分层信息','主设定 H=30 cm，α=0.5；源数据与复算见 analyze.py');
text(s,'有机碳浓度 SOC',65,175,520,60,34,green,true);text(s,'土壤有机资源的相对状态',65,245,520,60,28);
text(s,'水稳性团聚体 MWD',670,175,540,60,34,green,true);text(s,'结构抵抗水作用破坏的相对稳定性',670,245,540,90,28);
text(s,'每层：处理 ÷ 对照 → 取对数 → 两功能加权\n剖面：按层厚加权 → 指数变换 × 100',65,365,1140,130,32);
text(s,'对照=100；等权是研究设定。必须同时展示分量与负响应。\n这是描述性原型，尚未证明能独立预测侵蚀、稳产或采纳。',65,530,1140,105,27,green);
s=slide('公主岭土壤指数改善与产量下降并存','梁尧等2021：10.11975/j.issn.1002-6819.2021.01.017；不同指标观测期不完全一致');
chart(s,['覆盖免耕 SM','深翻还田 SI'],[{name:'综合指数 对照=100',values:[115.73,126.72],fill:green}],150,'综合指数 对照=100');
text(s,'SM多年平均干籽粒产量低7.63%；20–30 cm团聚体均值为负响应。\nSI是措施比较，不归为免耕；指数提高不能替代产量评价。',65,555,1130,90,27,green);
s=slide('参照与采样深度足以改变改善幅度','公主岭：梁尧等2021；海伦：Chen等2021 DOI 10.3390/agriculture11100939');
table(s,[['敏感性维度','同一处理的结果','解释'],['公主岭SM 采样深度','0–10 cm 125.3 → 0–40 cm 112.2','只看表层放大响应'],['公主岭SM 功能权重','0–30 cm 114.76–116.71','权重稳定不等于效度已验证'],['海伦NT 空间参照','行内110.91；行间149.07','缺面积权重，不能简单平均']],[300,480,372],190,285);
text(s,'两个海伦指数不是置信区间，也不是两项独立研究。\n先保证采样与对照可比，再讨论赋权方法。',65,520,1120,110,30,green);
}
if(input.batch===2){
let s=slide('真实经营基线必须区分利润与现金收益','辽阳2024年生产形势分析；威海2026年玉米成本收益直报（完整URL见报告 [6,7]）');
table(s,[['地区与时期','产值','总成本','利润'],['辽阳2023实际口径','1708.21','1646.97','61.24'],['辽阳2024预测口径','1143.83','1884.97','−741.14'],['威海2026直报口径','890.30','1045.95','−155.65']],[420,244,244,244],185,290);
text(s,'单位：元/亩/年。威海现金收益为40.36元/亩。\n官方调查未识别耕作措施，不能把亏损归因于常规耕作。',65,520,1130,110,29,green);
s=slide('长春免耕的材料毛利优势取决于对照','Zhang等2024 Agricultural Systems 215:103872 表5/6；DOI 10.1016/j.agsy.2024.103872');
chart(s,['2020','2021'],[{name:'NT对CT 耕作与还田同时改变',values:[78.08,68.69],fill:green},{name:'NT对MP 同样还田',values:[35.84,29.44],fill:blue}],100);
text(s,'单位：元/亩/年。原文收益差异不显著；尚未扣除全部经营成本。\n2020表5复算分别为82.35、40.11；保留表间矛盾，不擅自改数。',65,555,1140,95,26,green);
s=slide('同样还田时SOC差异也明显缩小','Zhang等2024 附表S1；2020年0–20 cm；沿用原文显著性字母');
table(s,[['处理对照','SOC浓度变化','原文差异'],['NT / CT 免耕还田 对 翻耕移除','+12.54%','显著'],['NT / MP 免耕还田 对 翻耕还田','+1.95%','不显著'],['MP / CT 翻耕还田 对 翻耕移除','+10.39%','显著']],[660,246,246],180,290);
text(s,'整套措施效应不能全部归因于免耕。\n浓度变化不能直接年化为碳汇；缺MWD，不填造长春总指数。',65,520,1120,105,29,green);
s=slide('土壤新增碳与减少排放分别定价','参考价：2025年全国自愿减排市场均价70.76元/t CO₂e；来源 [1,5,8,10]');
table(s,[['案例与口径','数量或年度变化','参考价值 元/亩/年'],['公主岭SM 额外土壤碳','1.97–2.07 t C/ha/年','34.02–35.83'],['栾城NT对CT 2001–2018','−0.335 t C/ha/年','−5.80'],['长春NT对CT 2020减排','53.29 kg CO₂e/亩','3.77'],['长春NT对CT 2021减排','53.90 kg CO₂e/亩','3.81']],[490,360,302],170,325);
text(s,'固定深度碳、投入排放与生长季气体边界不同，不跨地块相加。\n公主岭范围是来源口径差异；所有金额均非已成交的农户收入。',65,530,1130,105,28,green);
}
if(input.batch===3){
let s=slide('补偿测算给出临界条件而非拍定金额','会计补偿框架：已列毛利差与未计增量负担分别记录');
text(s,'新增私人损失补偿 = max(0，U − ΔM)',65,180,1140,80,43,green,true);
text(s,'ΔM：已列材料毛利差。\nU：遗漏新增成本、秸秆净机会成本、可核查转型负担，\n       减已兑现碳净现金及已受益的同类补贴。',65,295,1140,155,30);
text(s,'长春2021 NT对CT：max(0，U − 68.69) 元/亩\n同样还田NT对MP：max(0，U − 29.44) 元/亩',65,480,1140,95,31,green);
text(s,'U尚未观测，不能补零。公共生态奖励另行核定。',65,593,1140,45,27);
s=slide('东北补贴应衔接作业核验与持续绩效','吉林省政府办公厅 吉政办规〔2026〕1号，2026-08-15；报告参考文献 [9]');
text(s,'现行规则',65,180,440,60,34,green,true);text(s,'覆盖率60%以上：80元/亩上限\n叠加条耕、耙混或深松之一：\n合计105元/亩上限\n覆盖率30%以下取消补贴',65,265,515,255,29);
text(s,'研究建议',670,180,500,60,34,green,true);text(s,'先核对实际作业与受益主体。\n完整增量预算识别过渡负担。\n连续土壤和产量监测支持绩效。\n重点考虑东北冷凉水热条件。',670,265,510,260,29);
text(s,'政策上限不是到户金额；不拿2020–2021材料预算评价2026补贴高低。',65,570,1130,65,26,green);
s=slide('成果可复算 适用边界必须随结果保留','项目经费2000元已发生且有凭证；论文与软著尚未提交');
text(s,'已形成',65,175,500,60,35,green,true);text(s,'六项研究的必要事实转录与来源\n指数、收支、碳核算与自动检查\n研究报告、论文稿、结项书\n可编辑答辩图表与代码成果包',65,260,535,255,28);
text(s,'仍需验证',670,175,500,60,35,green,true);text(s,'综合指数的独立生态预测能力\n同地同期完整农户经营预算\n全年度、等土壤质量碳核算\n地区推广效果与实际补贴受益',670,260,535,255,28);
text(s,'结论：土壤改善、私人增收和公共生态收益分别评价，\n补贴依据可核查的新增负担与持续生态绩效。',65,540,1130,100,31,green,true);
}
return {count:presentation.slides.items.length};
}
