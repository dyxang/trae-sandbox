# Tasks

- [ ] Task 1: 实现 LiteDataProcessor（src/lite_processor.py）
  - [ ] SubTask 1.1: 实现 gui_data_to_processor_format 方法，将 GUI 表格数据转为 DataProcessor 可处理的 dict 列表
  - [ ] SubTask 1.2: 实现自定义分层浮动区间支持，替代硬编码的 ±1%/±2%/±3%
  - [ ] SubTask 1.3: 实现单项限价叠加逻辑（取分层区间与自定义限价的交集）
  - [ ] SubTask 1.4: 实现总价限价校准（支持总价上限+下限，复用 calibrate_total_price 逻辑）
  - [ ] SubTask 1.5: 实现 run_lite_adjustment 主方法，串联全流程：分层→浮动→涨跌控制→总价校准→返回结果
- [ ] Task 2: 实现 Gradio GUI 界面（src/lite_app.py）
  - [ ] SubTask 2.1: 实现数据输入表格（序号、项目名称、工程量、综合单价、合价、单价浮动上限%、单价浮动下限%、是否锁定）
  - [ ] SubTask 2.2: 实现合价自动计算（工程量×综合单价）
  - [ ] SubTask 2.3: 实现添加行/删除行功能
  - [ ] SubTask 2.4: 实现算法参数面板（大项/中项/小项浮动区间、随机种子、涨跌比例范围、总价上限/下限）
  - [ ] SubTask 2.5: 实现调价按钮和结果展示表格
  - [ ] SubTask 2.6: 实现检验报告展示区域
  - [ ] SubTask 2.7: 实现导出 Excel 按钮（生成 .xlsx 下载）
- [ ] Task 3: 集成测试与验证
  - [ ] SubTask 3.1: 端到端测试：输入数据→调价→结果展示→导出
  - [ ] SubTask 3.2: 验证自定义浮动区间生效
  - [ ] SubTask 3.3: 验证单项限价叠加逻辑
  - [ ] SubTask 3.4: 验证总价限价校准
  - [ ] SubTask 3.5: 验证随机种子可复现

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
