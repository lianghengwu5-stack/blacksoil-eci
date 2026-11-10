# 黑土保护的生态评价与农户参与补偿

以吉林省梨树县为主案例，整合公开田间试验、土壤调查和经营资料，研究保护性耕作的生态表现、农户收益及补偿条件。

正式项目名称：**基于ECI模型的黑土生态价值量化与资产化路径研究**。

## 最新成果

2026年11月10日整理版本。论文已完成，待投稿。

- [研究报告 PDF](final_manuscripts_20261109/deliverables/梨树县保护性耕作研究报告_评审终稿.pdf) · [可编辑 Word](final_manuscripts_20261109/deliverables/梨树县保护性耕作研究报告_评审终稿.docx)
- [论文 PDF](final_manuscripts_20261109/deliverables/梨树县保护性耕作论文_评审终稿.pdf) · [可编辑 Word](final_manuscripts_20261109/deliverables/梨树县保护性耕作论文_评审终稿.docx)
- [12张分析图](final_manuscripts_20261109/figures/)：提供 PNG 和 SVG
- [分析数据与来源快照](final_manuscripts_20261109/data/)
- [措施选择与补偿计算器](final_manuscripts_20261109/decision_calculator.py) · [农户账户输入模板](final_manuscripts_20261109/farm_input_template.json)
- [运行与使用说明](final_manuscripts_20261109/使用说明.txt)

## 研究发现

梨树长期试验中，在累计秸秆还田量相同的条件下，每年还田组的产量平均高约14.1%，表明管理连续性值得关注。土壤水分的主要限制时期随年份变化，措施应与降水条件和玉米生长阶段配合。

已发表的六项土壤质量指数在原样本中的产量解释度为0.56，高于黑土层厚度单项的约0.43。本研究以此为基准检验指数用途，并比较权重变化、分项表现和保护目标。实际选择采用逐项筛选与经营收益比较，综合分用于辅助诊断。

梨树公开经营汇总中，合作社模式与传统模式的亩均经营结余相差173.27元，节本贡献55.8%。这一比较同时涉及耕作方式和组织作业条件。计算器允许录入同作物、同年度的本地完整账户，比较现实可行方案并计算新增收入补差。

## 复算

```bash
cd final_manuscripts_20261109
python3 -m pip install -r requirements.txt
python3 prepare_analysis.py
python3 decision_calculator.py
python3 build_figures.py
```

核算金额统一为元/亩/年。复制并填写 `farm_input_template.json` 后运行：

```bash
python3 decision_calculator.py 已填写的账户.json
```

科学分析以归档来源快照独立运行，不依赖前期目录。绘图使用中文字体，跨系统配置见使用说明。文稿构建程序另提供可编辑排版，PDF是固定版式阅读版本。

## 数据与使用

数据主要为公开论文的处理均值、统计结果及经营汇总，图中的参数网格用于敏感性分析。研究报告列出19项文献、数据与政策来源，原文全文不随成果包分发。

收入补差按保护目标合格措施相对最佳可行备选的经营差额计算，生态奖励另行设计。投入减排参考估值与实际碳收入分别核算。具体数据定义和适用条件见报告及数据快照。

仓库保持私有。代码许可与论文投稿安排由团队确定。

## 前期研究

[早期ECI与碳储量核算](docs/研究报告.md)、[跨地区保护性耕作分析](research_redesign_20261109/README.md)保留用于追溯。当前报告、论文和计算程序以上方最新成果为准。
