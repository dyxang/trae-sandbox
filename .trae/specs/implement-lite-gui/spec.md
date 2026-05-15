# Lite GUI 版调价工具 Spec

## Why
现有调价引擎是命令行工具，需要 Excel 文件作为输入输出，对造价人员门槛高。需要一个带 GUI 的 lite 版工具，让用户直接在界面录入分项工程数据、配置算法参数、一键调价，结果可复制/导出。

## What Changes
- 新增 Gradio Web GUI 应用，替代命令行交互
- 新增 LiteDataProcessor 类，基于现有 DataProcessor 简化适配 GUI 场景
- 用户在界面表格中直接输入工程量、综合单价，自动计算合价
- 保留自动分层机制（大/中/小项），但分层浮动区间由用户自定义（不硬编码）
- 支持用户对特定项设置更严格的单价浮动限价（叠加约束）
- 支持总价限价（可选）
- 结果表格可复制、可导出 Excel
- 检验报告在界面展示

## Impact
- Affected specs: P0 核心引擎（复用 DataProcessor 算法逻辑，但不直接调用 ExcelHandler）
- Affected code: 新增 src/lite_app.py（Gradio 应用入口），新增 src/lite_processor.py（简化处理器）

## ADDED Requirements

### Requirement: GUI 数据输入
系统 SHALL 提供 Gradio Web 界面，支持用户输入分项工程数据。

#### Scenario: 表格数据输入
- **WHEN** 用户打开应用
- **THEN** 界面展示一个可编辑表格，包含列：序号、项目名称、工程量、综合单价、合价（自动计算）、单价浮动上限%、单价浮动下限%、是否锁定

#### Scenario: 合价自动计算
- **WHEN** 用户输入工程量和综合单价
- **THEN** 合价列自动计算为 工程量 × 综合单价

#### Scenario: 添加/删除行
- **WHEN** 用户点击添加行或删除行按钮
- **THEN** 表格增加一行空行或删除选中行

#### Scenario: 锁定行标记
- **WHEN** 用户勾选某行的"是否锁定"复选框
- **THEN** 该行在调价时保持原价不变

### Requirement: 算法参数配置
系统 SHALL 支持用户在界面配置算法参数。

#### Scenario: 分层浮动区间配置
- **WHEN** 用户在参数面板设置大项/中项/小项的浮动区间
- **THEN** 系统使用用户指定的区间（如大项±0.5%~1%、中项±1%~2%、小项±2%~3%）生成浮动系数

#### Scenario: 单项限价叠加
- **WHEN** 用户为某行设置了自定义的单价浮动上限/下限
- **THEN** 该项的浮动范围取自动分层区间与自定义限价的交集（更严格者生效）

#### Scenario: 总价限价配置
- **WHEN** 用户设置了总价上限或总价下限
- **THEN** 调价后总价须在 [总价下限, 总价上限] 范围内；若未设置则不约束总价

#### Scenario: 随机种子配置
- **WHEN** 用户设置随机种子
- **THEN** 相同种子生成完全相同的调价结果；用户可更换种子生成不同方案

#### Scenario: 涨跌比例控制
- **WHEN** 用户设置涨跌比例范围（默认40%~60%）
- **THEN** 调价后上涨项占比在该范围内

### Requirement: 调价执行与结果展示
系统 SHALL 执行调价算法并展示结果。

#### Scenario: 一键调价
- **WHEN** 用户点击"调价"按钮
- **THEN** 系统执行：自动分层 → 随机浮动生成 → 涨跌控制 → 总价校准 → 输出结果

#### Scenario: 结果表格展示
- **WHEN** 调价完成
- **THEN** 界面展示结果表格，包含列：序号、项目名称、工程量、原综合单价、原合价、调价后综合单价、调价后合价、浮动比例%、是否锁定

#### Scenario: 检验报告展示
- **WHEN** 调价完成
- **THEN** 界面展示质量检验摘要（基尼系数、涨跌比例、Pearson r、总价变化率、结论）

### Requirement: 结果复制与导出
系统 SHALL 支持结果表格的复制和导出。

#### Scenario: 复制表格
- **WHEN** 用户选中结果表格内容并复制
- **THEN** 复制内容可粘贴到 Excel，保持行列结构

#### Scenario: 导出 Excel
- **WHEN** 用户点击"导出 Excel"按钮
- **THEN** 系统生成 .xlsx 文件供下载，仅包含调价前后对比数据（检验报告仅在网页展示，不导出）

### Requirement: LiteDataProcessor
系统 SHALL 提供 LiteDataProcessor 类，适配 GUI 场景的数据处理。

#### Scenario: 从 GUI 表格数据构建处理输入
- **WHEN** LiteDataProcessor 接收 GUI 表格数据
- **THEN** 将其转换为 DataProcessor 可处理的 dict 列表格式，包含 code、name、price、is_locked 字段

#### Scenario: 自定义分层浮动区间
- **WHEN** 用户指定大项/中项/小项的浮动区间
- **THEN** LiteDataProcessor 使用用户指定的区间替代默认的 ±1%/±2%/±3%

#### Scenario: 单项限价叠加
- **WHEN** 某项有自定义浮动上限/下限
- **THEN** 该项的浮动范围 = min(分层上限, 自定义上限) ~ max(分层下限, 自定义下限)

#### Scenario: 总价限价校准
- **WHEN** 用户设置了总价上限或下限
- **THEN** 校准目标为总价落在 [下限, 上限] 区间内；校准策略与现有 calibrate_total_price 一致

## MODIFIED Requirements
无

## REMOVED Requirements
无
