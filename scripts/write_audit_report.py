"""Render the phase-one findings from computed tables into a readable record."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    audit = json.loads((ROOT / 'artifacts/audit/summary.json').read_text())
    fixed = json.loads((ROOT / 'artifacts/fixed_depth/summary.json').read_text())
    scenarios = pd.read_csv(ROOT / 'artifacts/audit/soil_scenarios.csv')
    lines = ['# 第一阶段数据与结果核查', '', '日期：2026年11月8日', '',
             '已恢复数据，复现历史结果，建立空间范围、固定土层和管理措施编码的修订分析。以下是可追溯的计算结果与采用边界，尚不构成论文发表或碳信用核证。', '',
             '## 数据恢复与复现', '',
             '从原中期工作区恢复了39个文件，包含原始输入、数值结果和方法说明。恢复时逐文件计算SHA-256，源文件保留原位。旧版8个分析脚本均运行成功，9张历史实证CSV在1e-10容差内与原表一致。', '',
             '中国SOC V9、TRACESoils、figshare SOC文件的MD5分别与官方仓储公布值一致；V10文件也与作者仓储公布MD5一致。因此已确认若干问题存在于公开版本或原分析口径，不能简单归因于文件复制损坏。', '',
             '官方来源：', '',
             '- SOC V9：https://zenodo.org/records/15851730',
             '- SOC V10：https://zenodo.org/records/17304024',
             '- 黑土区边界：https://doi.org/10.3974/geodb.2021.06.08.V1',
             '- TRACESoils：https://zenodo.org/records/13468926',
             '- figshare：https://doi.org/10.6084/m9.figshare.11983959.v4',
             '- KBS：https://doi.org/10.5061/dryad.1rn8pk0x1', '',
             '## 研究区与数据版本', '',
             '边界投影面积核算：黑土区约55.65万平方千米、典型黑土区约33.30万平方千米，与数据发布说明相符。空间分析按边界原始Albers投影转换点位，以边界覆盖判定，不再用矩形范围代替黑土区。', '',
             'V9中pH与Clay相关约0.999997，质地三项之和中位数152.28；V10分别约−0.431和100。这支持以V10为新分析输入。V10文件可数得7955个不同Profile编号，与Readme写的7995不一致；样本数及剖面识别依据本文件计算并披露。', '',
             '|数据与范围|ECI表层有效样本|三种赋权最低秩相关|严格0—30cm储量样本|储量中位数 tC/ha|',
             '|---|---:|---:|---:|---:|']
    for row in scenarios.to_dict('records'):
        lines.append(f"|{row['source_version']} / {row['subset']}|{row['n']}|{row['min_weighting_rho']:.3f}|{row['stock030_n']}|{row['stock030_median_tC_ha']:.2f}|")
    lines += ['', '表中各情景单独拟合指数，不比较其分数绝对高低。表层ECI样本与储量样本的有效条件不同，不能将其视为同一总体。', '',
              '## 固定0—30cm的共同样本', '',
              f"进一步统一ECI中的SOC含量与储量深度，得到{fixed['n_fixed_depth_profiles']}个共同有效农田剖面。其SOC储量中位数为{fixed['stock_median_tC_ha']:.2f} tC/ha，四分位区间为{fixed['stock_q25_tC_ha']:.2f}—{fixed['stock_q75_tC_ha']:.2f} tC/ha。熵权ECI范围{fixed['eci_entropy_min']:.2f}—{fixed['eci_entropy_max']:.2f}，三种赋权排序的最低Spearman相关为{fixed['minimum_weighting_rho']:.3f}。", '',
              '共同样本仅来自两条数据来源引用（75条Liu et al., 2022，14条Zhang et al., 2022），空间分布不均匀。去掉占主导的一条来源后，仅剩14个样本，重新拟合排序相关约0.868。赋权和删指标稳健不能替代来源及空间代表性。', '',
              '## 管理效应结论修订', '',
              'TRACESoils原167条的完整分类为66增、72平、3减、23未报告、3可变。中国23条为10增、11平、2未报告。之前文字没有交代的条目已找到，不是数据丢失。限定standard_tillage对照后为154条：62增、64平、3减、22未报告、3可变。', '',
              'figshare原49条含耕作比较中，37条涉及其他措施组合、12条仅编码为tillage。原+7.63%未加权响应比与+6.23%观测级DL合并能够复现，但不应被写成单一保护性耕作的普遍效应。', '',
              '按研究分组并对研究内相关作敏感性后，宽子集的合并点估计约20%，95%区间跨越零。仅tillage编码子集有12条，完整方差只有9条/4项研究；点估计偏大但适用范围局限于原有机农业研究，必须逐篇确认具体处理。所有重分析保留于meta_reanalysis.csv，不按显著与否选择汇报。', '',
              'KBS原差分约+3.65 tC/ha，p=0.679；匹配相同重复地块后变化差约+3.67 tC/ha，Welch p=0.630。处理是Late successional系统，2001年不构成已验证的共同干预前期，所以从主因果结论中移出。', '',
              '## 外部产品与单位', '',
              f"SoilGrids留存18点查询中14点有完整返回，其中12点落在黑土区边界。逐层核算后的全体有效点储量范围为{fixed['soilgrids_stock_min']:.2f}—{fixed['soilgrids_stock_max']:.2f} tC/ha。没有逐点配对与误差评价，不使用人为0.95一致性条，也不称为严格外部精度验证。", '',
              'MAP字段说明写为mm，但源值量级有疑点。保持原始值、暂停物理量解释，同时提供删MAP敏感性；不凭常识擅自乘10或12。GPP为另一类模型产品，农田适用性未确立，不作为农田主分析验证证据。', '',
              '## 后续研究报告的采用建议', '',
              '主线采用V10、正式黑土区边界、农田类别、完整0—30cm共同样本。原表层、典型黑土区范围、赋权和删指标结果作为敏感性。论文结论限于公开数据中样点的生态状态与核算框架，不外推区域总碳库，不声称当地因果增汇或真实交易收益。', '',
              '研究报告应将生态状况评价、存量核算、管理措施文献证据和收益情景分开组织。资产化模拟需包含增汇假设、价格、核查成本、缓冲扣减、农户分成和盈亏平衡条件。', '',
              '## 已完成检查', '',
              '- 8个历史脚本成功执行；9张历史实证CSV比对一致。',
              '- 4个固定深度单元测试通过，覆盖已知单位换算、缺底层、缺层、重叠和负储量。',
              '- 3张新结果图已生成并视觉检查。',
              '- 新旧数据、处理筛选、剖面排除、研究级Meta和KBS匹配表均已落盘。', '',
              '## 项目信息', '',
              '用户确认学院内部截止为2026年11月12日，获批2000元，论文与软著尚无提交记录。正式编号和实际支出待补；不填写虚构编号、报销金额或提交凭证。', '']
    target = ROOT / 'docs/第一阶段数据与结果核查.md'
    target.write_text('\n'.join(lines))
    print(target)


if __name__ == '__main__':
    main()
