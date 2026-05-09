# llm-wiki-skill 移植到 Trae Spec

## Why

llm-wiki-skill 目前是为 Claude Code 设计的知识库技能系统，需要通过 install.sh 安装到 ~/.claude/skills/、依赖 SessionStart hook 注入上下文。用户希望将其移植到 Trae IDE，使其能直接复制到 Obsidian vault 根目录后用 Trae 打开即可使用，无需任何安装步骤。

## What Changes

- 新增 `.trae/rules/project_rules.md` 作为 Trae 入口文件，替代 CLAUDE.md + SKILL.md 的路由角色
- 保留 `SKILL.md` 作为详细工作流定义文件，由 project_rules.md 引用
- 保留 `scripts/` 核心脚本，精简可选提取器相关逻辑
- 保留 `templates/` 页面模板（原样保留）
- 精简 `source-registry.tsv`，移除 optional_adapter 行，只保留 core_builtin + manual_only
- 精简 `adapter-state.sh`，移除可选外挂检测逻辑，只保留 core_builtin 路径
- 移除 `deps/` 目录（baoyu-url-to-markdown、youtube-transcript）
- 移除 `install.sh`、`setup.sh`、`install.ps1`（无需安装）
- 移除 `platforms/` 目录（无需跨平台支持）
- 移除 `CLAUDE.md`、`AGENTS.md`、`HERMES.md`（Trae 不需要这些入口）
- 移除 `docs/` 目录（开发文档，用户不需要）
- 移除 `tests/` 目录（开发测试，用户不需要）
- 移除 `README.en.md`、`PLAN.md`、`TODOS.md`、`CHANGELOG.md`（开发文档）
- 移除 `platforms/claude/companions/llm-wiki-upgrade/`（升级机制）
- 移除 `scripts/hook-session-start.sh`（Trae 无等价 hook 机制）
- 调整 `scripts/` 中所有脚本的 SKILL_DIR 路径解析，从 ~/.claude/skills/llm-wiki/ 改为项目根目录（即 Obsidian vault 根目录）
- 保留 graph 工作流，依赖缺失时降级为纯 Mermaid 静态图
- URL 类素材统一走手动粘贴回退路径

## Impact

- Affected specs: llm-wiki-skill 全部工作流（init、ingest、batch-ingest、query、digest、lint、status、graph、delete、crystallize）
- Affected code: scripts/ 下所有脚本、source-registry.tsv、adapter-state.sh、SKILL.md

## ADDED Requirements

### Requirement: Trae 入口文件

系统 SHALL 提供 `.trae/rules/project_rules.md` 作为 Trae IDE 的入口文件，包含以下内容：
- llm-wiki 技能的触发条件和工作流路由表
- 通用前置检查逻辑（CWD 检查 .wiki-schema.md）
- 对 SKILL.md 的引用（详细工作流定义）
- 对 scripts/ 目录的路径说明
- 会话启动时的 wiki 上下文感知指令（替代 SessionStart hook）

#### Scenario: 用户在 Trae 中打开 Obsidian vault 并提到知识库
- **WHEN** 用户在 Trae 中打开包含 .trae/rules/project_rules.md 的 Obsidian vault 目录
- **AND** 用户提到"知识库"、"wiki"或要求执行知识库操作
- **THEN** AI 加载 project_rules.md 中的路由逻辑，根据用户意图路由到对应工作流
- **AND** AI 读取 SKILL.md 获取详细工作流定义

#### Scenario: 会话启动时自动感知知识库
- **WHEN** Trae 会话启动
- **AND** 当前工作目录存在 .wiki-schema.md
- **THEN** AI 自动感知知识库上下文，在回答问题时优先查阅 wiki 内容

### Requirement: 复制即用部署

系统 SHALL 支持将整个文件集合直接复制到 Obsidian vault 根目录后立即使用，无需任何安装步骤。

#### Scenario: 用户复制文件到 Obsidian vault
- **WHEN** 用户将 .trae/、scripts/、templates/、SKILL.md 复制到 Obsidian vault 根目录
- **AND** 用 Trae 打开该 vault 目录
- **THEN** 所有工作流可直接执行，无需运行 install.sh 或其他安装命令

### Requirement: 路径解析适配

系统 SHALL 将所有脚本中的 SKILL_DIR 路径解析从 ~/.claude/skills/llm-wiki/ 改为当前项目根目录。

#### Scenario: 脚本执行时解析路径
- **WHEN** 任何 scripts/ 下的脚本被执行
- **THEN** SKILL_DIR 解析为脚本所在目录的父目录（即 Obsidian vault 根目录）
- **AND** 所有相对路径引用（templates/、scripts/）基于该 SKILL_DIR 正确解析

### Requirement: URL 素材手动回退

系统 SHALL 对所有 URL 类素材统一走手动粘贴回退路径，不再尝试自动提取。

#### Scenario: 用户提供 URL 素材
- **WHEN** 用户提供一个 URL（网页、X/Twitter、微信公众号、YouTube、知乎等）
- **THEN** AI 提示用户手动复制内容粘贴，或保存为本地文件后继续
- **AND** 不尝试调用任何外挂提取器

### Requirement: Graph 工作流降级

系统 SHALL 在 graph 工作流中支持依赖缺失时的降级处理。

#### Scenario: 用户请求知识图谱但缺少 node 或 jq
- **WHEN** 用户请求生成知识图谱
- **AND** 系统缺少 node 或 jq
- **THEN** 仅生成 Mermaid 静态图（wiki/knowledge-graph.md），跳过交互式 HTML 生成
- **AND** 提示用户安装 node + jq 后可获取交互式图谱

## MODIFIED Requirements

### Requirement: source-registry.tsv 精简

source-registry.tsv SHALL 只包含以下来源定义：
- local_pdf（core_builtin）
- local_document（core_builtin）
- plain_text（core_builtin）
- x_twitter（manual_only，原 optional_adapter 降级）
- wechat_article（manual_only，原 optional_adapter 降级）
- youtube_video（manual_only，原 optional_adapter 降级）
- zhihu_article（manual_only，原 optional_adapter 降级）
- xiaohongshu_post（manual_only，原样保留）
- web_article（manual_only，原 optional_adapter 降级）

所有原 optional_adapter 来源降级为 manual_only，adapter_name 和 dependency_name 设为 -，dependency_type 设为 none，fallback_hint 统一为手动粘贴提示。

### Requirement: adapter-state.sh 精简

adapter-state.sh SHALL 只处理 core_builtin 和 manual_only 两种 source_category：
- core_builtin：直接返回 available
- manual_only：直接返回 unsupported，附带 fallback_hint

移除所有 optional_adapter 相关的检测逻辑（uv 检测、Chrome 调试端口检测、bundled/install_time 依赖检测）。

### Requirement: SKILL.md 精简

SKILL.md SHALL 移除以下内容：
- 依赖检查章节中的可选依赖说明和安装命令
- 外挂状态模型章节中 optional_adapter 相关的状态说明
- 素材提取路由中的外挂前置判断和调用逻辑（baoyu-url-to-markdown、wechat-article-to-markdown、youtube-transcript）
- Chrome 提示相关内容
- 所有指向 install.sh --with-optional-adapters 的引用

SKILL.md SHALL 修改以下内容：
- 素材提取路由简化为：URL 类统一走 manual_only 回退，本地文件直接读取，纯文本直接使用
- Script Directory 章节更新路径解析说明

### Requirement: install.sh / setup.sh 移除

install.sh 和 setup.sh SHALL 被移除，不再需要安装流程。

### Requirement: runtime-context.sh 精简

runtime-context.sh SHALL 移除 resolve_platform_skill_root 函数中的 claude/codex/openclaw/hermes 平台路径解析，替换为直接返回项目根目录的逻辑。

## REMOVED Requirements

### Requirement: 可选提取器
**Reason**: 用户明确要求剔除可选提取器，Trae 环境下无法保证 Chrome CDP / uv / bun 等依赖可用
**Migration**: URL 类素材统一走手动粘贴回退路径

### Requirement: SessionStart Hook
**Reason**: Trae 无等价的 hook 机制，project_rules.md 在每次会话自动加载，可替代此功能
**Migration**: 在 project_rules.md 中写入会话启动时的 wiki 上下文感知指令

### Requirement: 多平台支持
**Reason**: 只面向 Trae，不需要 Claude Code / Codex / OpenClaw / Hermes 适配
**Migration**: 无需迁移

### Requirement: 安装/升级机制
**Reason**: 目标是复制即用，不需要 install.sh / setup.sh / llm-wiki-upgrade
**Migration**: 无需迁移
