# Tasks

- [x] Task 1: 创建 .trae/rules/project_rules.md 入口文件
  - [x] SubTask 1.1: 编写 project_rules.md，包含触发条件、工作流路由表、通用前置检查、对 SKILL.md 的引用、会话启动 wiki 上下文感知指令
  - [x] SubTask 1.2: 编写路径说明，定义 SKILL_DIR = 项目根目录（Obsidian vault 根目录）

- [x] Task 2: 精简 SKILL.md
  - [x] SubTask 2.1: 移除依赖检查章节中的可选依赖说明和 install.sh 引用
  - [x] SubTask 2.2: 移除外挂状态模型章节中 optional_adapter 相关内容
  - [x] SubTask 2.3: 简化素材提取路由：URL 类统一走 manual_only 回退，移除外挂前置判断和调用逻辑
  - [x] SubTask 2.4: 移除 Chrome 提示相关内容
  - [x] SubTask 2.5: 更新 Script Directory 章节的路径解析说明
  - [x] SubTask 2.6: 移除 SKILL.md 顶部的 hermes metadata 块

- [x] Task 3: 精简 source-registry.tsv
  - [x] SubTask 3.1: 将所有 optional_adapter 来源降级为 manual_only，更新 adapter_name/dependency_name/dependency_type/fallback_hint 字段
  - [x] SubTask 3.2: 验证 source-registry.sh 仍能正确读取精简后的 TSV

- [x] Task 4: 精简 adapter-state.sh
  - [x] SubTask 4.1: 移除 optional_adapter 检测逻辑（uv 检测、Chrome 调试端口检测、bundled/install_time 依赖检测）
  - [x] SubTask 4.2: 简化 resolve_preflight_state：core_builtin 直接返回 available，manual_only 直接返回 unsupported
  - [x] SubTask 4.3: 移除 classify_run_state 中对外挂运行结果的分类逻辑，简化为直接返回 available/unsupported
  - [x] SubTask 4.4: 移除 shared-config.sh 中的 WECHAT_TOOL_URL 和 uv 相关函数

- [x] Task 5: 精简 runtime-context.sh
  - [x] SubTask 5.1: 移除 resolve_platform_skill_root 中的多平台路径解析，替换为直接返回项目根目录
  - [x] SubTask 5.2: 移除 detect_layout_mode 和 resolve_layout_mode 中的 source_checkout 模式
  - [x] SubTask 5.3: 简化 resolve_optional_adapter_root，移除对 deps/ 目录的引用

- [x] Task 6: 精简其他脚本
  - [x] SubTask 6.1: 移除 hook-session-start.sh（Trae 无等价 hook）
  - [x] SubTask 6.2: 更新 init-wiki.sh 中的路径解析逻辑
  - [x] SubTask 6.3: 更新 cache.sh、create-source-page.sh、delete-helper.sh、lint-runner.sh、lint-fix.sh 中的路径引用
  - [x] SubTask 6.4: 更新 build-graph-data.sh 和 build-graph-html.sh 中的路径引用
  - [x] SubTask 6.5: 在 graph 相关脚本中添加依赖缺失时的降级逻辑（缺少 node/jq 时跳过交互式 HTML 生成）

- [x] Task 7: 移除不需要的文件和目录
  - [x] SubTask 7.1: 删除 deps/ 目录
  - [x] SubTask 7.2: 删除 platforms/ 目录
  - [x] SubTask 7.3: 删除 docs/ 目录
  - [x] SubTask 7.4: 删除 tests/ 目录
  - [x] SubTask 7.5: 删除 install.sh、setup.sh、install.ps1
  - [x] SubTask 7.6: 删除 CLAUDE.md、AGENTS.md、HERMES.md
  - [x] SubTask 7.7: 删除 README.en.md、PLAN.md、TODOS.md、CHANGELOG.md
  - [x] SubTask 7.8: 删除 .gitignore

- [x] Task 8: 更新 README.md
  - [x] SubTask 8.1: 重写 README.md 为 Trae 版本说明，包含：项目简介、使用方式（复制到 Obsidian vault 根目录 + Trae 打开）、目录结构、前置条件、核心功能列表

- [x] Task 9: 验证端到端流程
  - [x] SubTask 9.1: 验证 source-registry.sh list 输出正确
  - [x] SubTask 9.2: 验证 adapter-state.sh check 对 core_builtin 和 manual_only 来源返回正确状态
  - [x] SubTask 9.3: 验证 init-wiki.sh 能正确创建知识库目录结构
  - [x] SubTask 9.4: 验证 project_rules.md 内容完整且路径引用正确

# Task Dependencies

- [Task 2] depends on [Task 3] (SKILL.md 引用 source-registry.tsv 的内容，需要先精简 TSV)
- [Task 4] depends on [Task 3] (adapter-state.sh 依赖 source-registry.tsv 的数据)
- [Task 6] depends on [Task 5] (其他脚本依赖 runtime-context.sh 的路径解析)
- [Task 9] depends on [Task 1-8] (验证需要所有修改完成)
- [Task 1] and [Task 3] can run in parallel
- [Task 5] and [Task 4] can run in parallel
