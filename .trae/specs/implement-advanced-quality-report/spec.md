# P2 高级质量检验与报告 Spec

## Why
P1 仅提供了基础质量检验，但工程审计要求更全面的质量评估体系，包括不平衡报价检测（基尼系数、Z-Score）、同方向浮动检测（二项检验）、相关性检测（Spearman、K-S检验）等。同时用户需要可读的检验报告和灵活的配置系统来控制调价参数，以及通过不同随机种子生成多个方案进行比选。

## What Changes
- 新增完整质量检验体系（基尼系数、Z-Score异常值、IQR、二项检验、Spearman ρ、K-S检验）
- 新增检验报告生成模块，输出结构化文本报告
- 新增 YAML 配置系统，支持用户自定义所有调价参数
- 新增多方案生成功能，支持不同随机种子生成多个方案

## Impact
- Affected specs: P1 价格控制与基础质量（扩展检验指标）
- Affected code: src/data_processor.py（新增高级检验），新增 src/report_generator.py，新增 src/config.py

## ADDED Requirements

### Requirement: 不平衡报价检测
系统 SHALL 对调价方案执行不平衡报价检测。

#### Scenario: 基尼系数检测
- **WHEN** 调价完成后执行质量检验
- **THEN** 系统计算基尼系数 G = ΣΣ|x_i - x_j| / (2n²μ)，合格标准为 G < 0.25

#### Scenario: Z-Score异常值检测
- **WHEN** 调价完成后执行质量检验
- **THEN** 系统计算每项的 Z-Score = (x_i - μ) / σ，|Z| > 2 的项目数应 < 5%

### Requirement: 同方向浮动检测
系统 SHALL 检测调价方案是否存在同方向浮动规律。

#### Scenario: 涨跌比例检测
- **WHEN** 调价完成后执行质量检验
- **THEN** 系统计算上涨项占比 n_up / (n_up + n_down)，合格标准为 0.4~0.6

#### Scenario: 二项检验
- **WHEN** 涨跌比例检测完成
- **THEN** 系统计算二项检验 p 值 P(X ≤ n_up | p=0.5)，合格标准为 p > 0.05

### Requirement: 相关性检测
系统 SHALL 检测调整后价格与原价格的统计相关性。

#### Scenario: Spearman 秩相关检测
- **WHEN** 调价完成后执行质量检验
- **THEN** 系统计算 Spearman ρ，合格标准为 0.3 ≤ ρ ≤ 0.6

#### Scenario: K-S 检验
- **WHEN** 相关性检测完成
- **THEN** 系统执行 K-S 检验，计算 sup|F_n(x) - F(x)|，合格标准为 p > 0.05

### Requirement: 检验报告生成
系统 SHALL 生成结构化的质量检验报告。

#### Scenario: 报告内容完整性
- **WHEN** 所有质量检验完成
- **THEN** 报告包含：基本信息（输入文件、处理时间、随机种子）、数量统计（总项目数、锁定项/可调项数量及占比、分层统计）、总价变化（原总价、新总价、变化额、变化率）、涨跌分布（上涨/下跌项数量及占比、二项检验p值）、浮动范围（最大上涨/下跌、分层极值、浮动-合价Spearman）、相关性检验（Pearson r、Spearman ρ、K-S检验p值）、不平衡检测（基尼系数、Z-Score异常值）、结论（通过/警告/失败统计）

#### Scenario: 报告结论判定
- **WHEN** 报告生成完成
- **THEN** 系统根据各检验指标结果判定为 ✓通过、⚠警告 或 ✗失败，并给出建议

### Requirement: YAML 配置系统
系统 SHALL 支持通过 YAML 配置文件自定义所有调价参数。

#### Scenario: 配置文件加载
- **WHEN** 程序启动时
- **THEN** 系统读取 config.yaml 配置文件，解析所有参数

#### Scenario: 配置参数完整性
- **WHEN** 配置文件加载完成
- **THEN** 系统支持以下参数：input_file、output_file、target_discount_pct、tolerance、max_float_large、max_float_medium、max_float_small、random_seed、up_down_ratio、correlation_max、gini_max

#### Scenario: 缺省参数默认值
- **WHEN** 配置文件中某些参数未指定
- **THEN** 系统使用默认值（max_float_large=0.01, max_float_medium=0.02, max_float_small=0.03, tolerance=0.01, correlation_max=0.5, gini_max=0.25）

### Requirement: 多方案生成
系统 SHALL 支持通过不同随机种子生成多个调价方案。

#### Scenario: 指定多个随机种子
- **WHEN** 用户指定多个随机种子（如 [42, 123, 456]）
- **THEN** 系统分别为每个种子生成独立的调价方案和检验报告

#### Scenario: 自动生成多方案
- **WHEN** 用户指定方案数量（如3个）但未指定种子
- **THEN** 系统自动生成指定数量的随机种子并生成对应方案

## MODIFIED Requirements

### Requirement: 基础质量检验（P1 修改）
P1 的基础质量检验 SHALL 扩展为完整质量检验体系，包含不平衡报价检测、同方向浮动检测和相关性检测的全部指标。

## REMOVED Requirements
无
