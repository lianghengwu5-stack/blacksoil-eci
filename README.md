# BlackSoil：保护性耕作、土壤保育与经营收益

正式立项名称：基于ECI模型的黑土生态价值量化与资产化路径研究。

## 当前成果（2026年11月9日整合版）

当前研究主线为**保护性耕作的土壤保育响应、经营收益与生态补偿**，使用公开田间试验与官方成本收益资料再分析，对东北黑土区作重点说明。以下独立目录为最新成果；下方旧ECI及剖面数据分析仅保留追溯用途。

- [研究方法、数据与复算说明](research_redesign_20261109/README.md)
- [研究报告PDF](research_redesign_20261109/output/manuscripts/保护性耕作研究报告_整合稿.pdf)（同目录有Word）
- [论文稿PDF](research_redesign_20261109/output/manuscripts/土壤保育与经营收益权衡_论文稿.pdf)（同目录有Word；尚未投稿）
- [结构化来源数据](research_redesign_20261109/data/)、[计算结果](research_redesign_20261109/results/)与[图表](research_redesign_20261109/figures/)
- [全新目录复算验证](research_redesign_20261109/reproduction_validation.json)

最新数值复算只需Python标准库：

```bash
cd research_redesign_20261109
python3 analyze.py
python3 check_analysis.py
python3 analyze_agsy2024.py
```

复合指标用于描述土壤有机碳与水稳性团聚体的相对响应，不代表完整生态价值或已经验证的通用评价标准。成本覆盖不全的田间收益称为经营结余；土壤固碳与避免排放分开核算，参考碳价估值不等于可出售碳信用或农户实际收入。补贴模型用于核算参与门槛，不能据此确定最优补贴。正式结项表含个人信息，仅在本地交付。

仓库暂为私有，代码许可尚待团队确定。出版商论文全文及补充材料原件不随仓库分发。

---

## 历史阶段：剖面碳储量与ECI适用性审查

以下为前一阶段记录，其中“当前”均指该历史阶段，请勿替代上方最新研究成果。


正式立项名称：基于ECI模型的黑土生态价值量化与资产化路径研究。

2026年11月9日修订后，实际主线为**公开农田剖面的碳储量核算与综合指数适用性审查**。ECI保留为历史候选方法，尚未证明额外生态评价用途。假设收益金额撤出当前主要成果，默认运行不再计算现金流。

## 当前阅读版本

- [研究报告修订稿](reports/研究报告_修订稿.pdf)，同目录提供Word。
- [论文初稿](reports/论文_碳储量与指数适用性_初稿.pdf)，尚未投稿。
- [研究调整与证据核查](docs/研究调整与证据核查_20261109.md)。

旧文件和历史结果仅用于追溯。上述11月9日修订稿为当前口径。结项表含个人信息，在本地保存，不进入仓库。

## 当前证据

90个碳储量合格剖面的0—30 cm储量中位数为68.06 tC/ha，四分位区间46.78—88.83 tC/ha。Liu来源76个，Zhang来源14个，来源与数据库年份标签重合，不能推断2014至2016的变化。仅检查目标土层，89个全为direct，1个混合direct与indirect；85个仍需对跨越30 cm的末层作比例分配。源标签不代表零测量误差。

历史89个ECI共同样本与碳储量排序相关0.843，前23名重合19个。内部赋权稳定不能证明额外用途。NDVI产品来源说明冲突，MAP单位和聚合含义未核清，当前不建立环境归因模型，也不输出保护优先级、地区碳库或管理净增汇。

新增Dryad实测SOC资料2140条，其中1066条位于研究边界。文件缺容重、逐点年份和管理字段，SOC数值单位尚待核实，本轮仅作空间覆盖审查，不并入储量样本。另一两期公开数据包只有栅格，长期试验原始工作簿尚未取得，均未用于处理效应估计。

## 复现

科学环境为Python 3.12。原始输入不随仓库分发。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python scripts/fetch_data.py
python scripts/run_project.py
python -m unittest discover -s tests -v
```

Windows请用`.venv\Scripts\activate`激活。默认入口生成历史审查、固定深度候选ECI及当前碳证据再分析。`artifacts/reassessment/`为当前碳样本、来源、网格、名次比较和验证输出。

新增覆盖审查单独执行：

```bash
python scripts/fetch_revision_data.py
python scripts/check_external_samples.py
```

源站可能限制自动下载。按脚本提示从官方页取得文件后运行`--verify-only`校验，不绕过登录或站点限制。新增两份Dryad文件已在本地实际下载并核对SHA-256；下载脚本不代表已验证所有源站能从空目录自动下载。

旧现金流仅供追溯：`python scripts/run_project.py --include-illustrative-scenarios`。运行它不会使假设参数成为实测事实。`artifacts/asset_scenarios/`和旧日期核查文件均是历史资料，不引用为当前经济成果。

2026年11月9日检查：默认科学流程运行成功，8项既有计算测试通过（其中4项为历史现金流检查）；当前再分析含4项结果断言。最新独立目录复算状态见`artifacts/reassessment/reproduction_validation.json`。未验证跨操作系统或全源站无人值守下载。

## 目录与文件用途

`data/raw/`保存本地版本化输入，Git忽略；`scripts/`为计算与文档构建代码；`artifacts/reassessment/`是当前再分析；`docs/`保存源稿、字段核查与方法决定；`reports/`提供排版后的当前PDF和Word。源稿中的表格及公式标记由构建脚本解析。

报告排版需python-docx、Pillow、文档渲染器及中文字体，不属于科学结果复算的最低依赖。主报告使用`prepare_report_assets.py`和`build_research_report.py`，论文使用`prepare_paper_assets.py`和`build_paper.py`。

## 引用与许可

数据来源、版本及限制见[数据获取与许可](docs/数据获取与许可.md)及核查记录。新增Dryad资料为CC0；通肯河包为CC BY 4.0，仅作文件审查；沈阳试验为CC BY-NC-ND 4.0，本轮只引用元数据，不重新分发文件。私有仓库尚未确定代码开源许可。论文尚未投稿，作者顺序和贡献须由团队确认。
