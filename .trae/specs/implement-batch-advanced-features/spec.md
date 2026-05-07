# P3 批量处理与高级特性 Spec

## Why
P0-P2 已覆盖单文件调价的核心流程和质量检验，但实际业务中用户需要批量处理多个文件、对现有报价进行风险排查、对比多个方案选择最优解，以及在万行级数据场景下提升处理速度。P3 提供这些高级特性，使系统从单次工具升级为批量生产级平台。

## What Changes
- 新增批量处理模块，支持多文件/多方案自动处理
- 新增风险排查模块，检测现有报价中的不平衡风险
- 新增多版本比选模块，对比多个方案并推荐最优
- 新增 openpyxl 加速模块，万行级纯数据场景下提升读写速度

## Impact
- Affected specs: P2 高级质量检验与报告（依赖检验报告和配置系统）
- Affected code: 新增 src/batch_processor.py，新增 src/risk_detector.py，新增 src/scheme_comparator.py

## ADDED Requirements

### Requirement: 批量处理
系统 SHALL 支持批量处理多个 Excel 文件。

#### Scenario: 多文件批量处理
- **WHEN** 用户指定一个目录或文件列表
- **THEN** 系统依次处理每个文件，为每个文件生成调价结果和检验报告

#### Scenario: 批量处理进度报告
- **WHEN** 批量处理执行中
- **THEN** 系统输出当前处理进度（已完成/总数）和每个文件的处理状态

#### Scenario: 单文件处理失败不影响批量
- **WHEN** 批量处理中某个文件处理失败
- **THEN** 系统记录失败原因，继续处理后续文件，最终汇总报告包含失败文件信息

### Requirement: 风险排查
系统 SHALL 支持对现有报价进行不平衡风险检测。

#### Scenario: 不平衡报价风险检测
- **WHEN** 用户提交一个现有报价的 Excel 文件并选择风险排查模式
- **THEN** 系统计算基尼系数、Z-Score 异常值、IQR 异常值，标记高风险项目

#### Scenario: 风险等级分类
- **WHEN** 风险检测完成
- **THEN** 系统将每个项目标记为低风险/中风险/高风险，高风险标准为 |Z| > 2 且超出 IQR 1.5倍范围

#### Scenario: 风险报告输出
- **WHEN** 风险检测完成
- **THEN** 系统输出风险排查报告，包含高风险项目列表、风险等级分布、建议调整方向

### Requirement: 多版本比选
系统 SHALL 支持对比多个调价方案并推荐最优。

#### Scenario: 方案对比
- **WHEN** 用户生成了多个调价方案
- **THEN** 系统对比各方案的检验指标（基尼系数、涨跌比例、Pearson r、总价变化率），生成对比表格

#### Scenario: 最优方案推荐
- **WHEN** 方案对比完成
- **THEN** 系统基于综合评分（各检验指标加权）推荐最优方案，并说明推荐理由

#### Scenario: 对比报告输出
- **WHEN** 方案比选完成
- **THEN** 系统输出对比报告，包含各方案关键指标、综合评分排名、推荐方案

### Requirement: openpyxl 加速
系统 SHALL 在万行级纯数据场景下支持 openpyxl 加速读写。

#### Scenario: 自动检测加速条件
- **WHEN** 输入文件数据行数超过10000行
- **THEN** 系统自动检测是否满足加速条件（无公式、无格式要求、无VBA）

#### Scenario: 使用 openpyxl 批量读取
- **WHEN** 满足加速条件
- **THEN** 系统使用 openpyxl + pandas 进行数据读取，速度提升 2-5 倍

#### Scenario: 使用 openpyxl 批量写入
- **WHEN** 满足加速条件且输出无需保留复杂格式
- **THEN** 系统使用 openpyxl 进行数据写入

#### Scenario: 加速后公式重算
- **WHEN** 使用 openpyxl 写入后文件包含公式
- **THEN** 系统自动调用 xlwings 打开文件进行公式重算

#### Scenario: 不满足加速条件时回退
- **WHEN** 数据量不足10000行或不满足纯数据条件
- **THEN** 系统回退到 xlwings 默认处理流程

## MODIFIED Requirements
无

## REMOVED Requirements
无
