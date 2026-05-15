# Plite 独立化改造计划

## 问题
Plite/lite_processor.py 通过 `sys.path.insert` + `from src.data_processor import DataProcessor` 依赖了项目根目录的 src/ 模块。用户单独拷贝 Plite 文件夹到其他位置时，import 失败。

## 目标
Plite 文件夹完全自包含，用户只需 `pip install -r requirements.txt` + `python lite_app.py` 即可运行，无需 src/ 目录。

## 改造步骤

### Step 1: 创建 Plite/core.py — 内联核心算法
从 src/data_processor.py 中提取 Plite 实际使用的方法，创建独立的 `Plite/core.py`，包含：

**LiteCore 类**（不继承 DataProcessor，完全独立实现）：
- `identify_locked_items(data)` — 复制自 DataProcessor，但简化：lite 版中锁定项主要由用户手动勾选，保留关键字/零值自动识别作为辅助
- `tier_grouping(data)` — 复制自 DataProcessor，逻辑不变
- `control_up_down_ratio(data, min_ratio, max_ratio)` — 复制自 DataProcessor，但 `_regenerate_coefficient` 使用参数化区间
- `control_correlation(data, target_min, target_max, large_range, medium_range, small_range)` — 复制自 DataProcessor，但系数生成使用参数化区间
- `advanced_quality_check(data)` — 复制自 DataProcessor，逻辑不变

关键改动：所有内部系数生成（`_regenerate_coefficient`、`control_correlation` 中的重新生成）都使用用户传入的 large_range/medium_range/small_range 参数，而非硬编码值。

### Step 2: 重写 Plite/lite_processor.py — 移除 src 依赖
- 删除 `sys.path.insert` 和 `from src.data_processor import DataProcessor`
- 删除 `_ParameterizedDataProcessor` 子类
- 改为 `from core import LiteCore`
- `run_lite_adjustment` 中使用 LiteCore 实例替代 DataProcessor/_ParameterizedDataProcessor

### Step 3: 修改 Plite/lite_app.py — 移除 src 依赖
- 删除 `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))`
- 改为 `from lite_processor import LiteDataProcessor`（同目录直接 import）

### Step 4: 更新 Plite/requirements.txt
- 确保包含所有依赖：gradio, openpyxl, pandas, numpy, scipy
- 不再需要 src/ 下的任何模块

### Step 5: 验证
- 在 Plite 目录下直接运行 `python lite_app.py`，确认无 import 错误
- 执行调价功能，确认结果与改造前一致

## 文件变更清单
| 文件 | 操作 |
|------|------|
| Plite/core.py | 新建 — 内联核心算法 |
| Plite/lite_processor.py | 重写 — 移除 src 依赖，改用 core.py |
| Plite/lite_app.py | 修改 — 移除 sys.path.insert，改用直接 import |
| Plite/requirements.txt | 确认 — 无需修改 |
