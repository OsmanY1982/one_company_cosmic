---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: b11c9da246eaa2aacfce94adf18e4927_7b2745d7667611f1a0095254002afed2
    ReservedCode1: gb8lksp+LPzW0SMP+GqzCW/8m4iBS9iT7tZZZ71NlYNduL9mpUjlHETZsMt8NtpQaqIB1gMN1BRRnpyVViRiObjHKsz40HUiEp9c2oQzH0wrnsSrLLPo23EDtLBnotkiClWxWMKOXTV4klI7TZG7547iKwtA8MUN/DOrtGjDdEuVJ7SmMoT+4YgLkPY=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: b11c9da246eaa2aacfce94adf18e4927_7b2745d7667611f1a0095254002afed2
    ReservedCode2: gb8lksp+LPzW0SMP+GqzCW/8m4iBS9iT7tZZZ71NlYNduL9mpUjlHETZsMt8NtpQaqIB1gMN1BRRnpyVViRiObjHKsz40HUiEp9c2oQzH0wrnsSrLLPo23EDtLBnotkiClWxWMKOXTV4klI7TZG7547iKwtA8MUN/DOrtGjDdEuVJ7SmMoT+4YgLkPY=
---



# 一人公司 · 宇宙版（One Company Cosmic）

"一人公司宇宙版"是一套基于 PyQt5 + opcclaw AI 引擎的全栈桌面管理软件，
以太空宇宙为视觉隐喻，集成 CRM、ERP、财务、人事、数据 BI、AI 智能助理等模块。
支持悬浮星球守护进程常驻后台，实现语音唤醒 + AI 对话。

---

## 项目路径

```
/Volumes/D盘工作区/一人公司/one_company_cosmic/
```

Python 包导入根路径即此目录。

---

## 目录结构树（两级）

```
one_company_cosmic/
├── main.py                    # ★ 桌面应用入口（PyQt5）
├── planet_daemon.py           # ★ 悬浮星球守护进程入口
├── gen_book.py                # 项目全书生成脚本
├── rollback_control.py        # 回滚控制脚本
├── siri_command_handler.py    # Siri Shortcuts 命令处理器
├── temp_test_stream.py        # 流式测试脚本
├── 启动宇宙版.command          # Shell 启动器（双击运行桌面应用）
├── 启动星球守护.command        # Shell 启动器（双击运行守护进程）
│
├── core/                      # ★ 宇宙核心引擎
│   ├── __init__.py
│   ├── cosmic.py              # 深空渲染（星空/星云/粒子/辉光）
│   ├── planet_painter.py      # 程序化星球纹理生成（地球/木星/土星）
│   ├── data.py                # 统一数据层（DB路径/schema初始化/迁移）
│   ├── deps.py                # 按需依赖管理
│   ├── agent.py               # 核心 Agent 基类
│   └── voice.py               # 语音引擎
│
├── opcclaw/                   # ★ AI 引擎（深度定制版 opcclaw）
│   ├── main.py                # opcclaw 独立入口
│   ├── __init__.py            # 包初始化（路径注入/版本号）
│   ├── start_opcclaw.py       # 启动脚本
│   ├── core/                  # 引擎核心 (43 个模块)
│   │   ├── agent_loop.py      # AgentLoop：Think-Plan-Act-Observe-Reflect
│   │   ├── chat_engine.py     # ChatEngine：对话模式核心
│   │   ├── tool_registry.py   # ToolRegistry：工具注册/发现
│   │   ├── skill_loader.py    # SkillLoader：Skill 扫描/匹配/注入
│   │   ├── memory_store.py    # MemoryStore：对话记忆持久化
│   │   ├── llm_backend.py     # LLM 后端抽象
│   │   ├── code_executor.py   # 代码执行器
│   │   ├── skill_system.py    # 技能系统
│   │   ├── task_scheduler.py  # 任务调度
│   │   ├── token_optimizer.py # Token 优化器
│   │   ├── semantic_search.py # 语义搜索
│   │   ├── multi_model.py     # 多模型管理
│   │   ├── super_intelligence.py # 超级智能引擎
│   │   └── ...                # 30+ 其他核心模块
│   ├── tools/                 # 工具套件 (100+)
│   │   ├── file_operations.py # 文件操作
│   │   ├── file_tools.py      # 文件工具集
│   │   ├── browser_tool.py    # 浏览器控制
│   │   ├── mcp_tool.py        # MCP 协议工具
│   │   ├── code_execution_tool.py # 代码执行
│   │   ├── terminal_tool.py   # 终端工具
│   │   ├── vision_tools.py    # 视觉理解
│   │   ├── tts_tool.py        # 文字转语音
│   │   ├── skills_tool.py     # 技能管理
│   │   ├── delegate_tool.py   # Agent 委托
│   │   └── ...                # 90+ 其他工具
│   ├── skills/                # 技能包（按领域分目录）
│   │   ├── macos_system/      # macOS 系统操作技能
│   │   ├── productivity/      # 生产力工具
│   │   ├── creative/          # 创意工具
│   │   ├── software-development/ # 软件开发
│   │   ├── research/          # 研究分析
│   │   └── ...                # 30+ 其他技能
│   ├── plugins/               # 插件（模型供应商/记忆/图像生成）
│   ├── agent/                 # Agent 传输层
│   ├── data/                  # 引擎配置
│   │   ├── opcclaw_config.json  # 当前活跃 provider 配置
│   │   └── model_status.json    # 模型状态
│   └── tests/                 # 引擎测试
│
├── modules/                   # ★ 业务模块
│   ├── auth/                  # 认证模块
│   │   ├── login_window.py    # 登录窗口
│   │   ├── connect_window.py  # 连接配置窗口
│   │   ├── model_setup_window.py # 模型设置窗口
│   │   ├── auth_service.py    # 认证服务
│   │   └── users.json         # 用户数据
│   ├── business/              # 业务运营模块
│   │   ├── business_window.py # 业务总窗口
│   │   ├── customer_window.py # 客户管理
│   │   ├── order_window.py    # 订单管理
│   │   ├── product_window.py  # 产品管理
│   │   ├── finance_window.py  # 财务管理
│   │   ├── customer_db.sqlite # 客户数据库
│   │   ├── order_db.sqlite    # 订单数据库
│   │   ├── product_db.sqlite  # 产品数据库
│   │   └── finance_db.sqlite  # 财务数据库
│   ├── dashboard/             # 舰桥主控面板
│   │   └── dashboard_window.py
│   ├── data_center/           # 数据中心
│   │   ├── data_window.py     # 数据窗口
│   │   ├── bi_window.py       # BI 分析
│   │   └── report_window.py   # 报表窗口
│   ├── intelligence/          # ★ 智能中枢（最大模块）
│   │   ├── agent_bridge.py    # ★ AgentBridge：AI Agent 桥接引擎
│   │   ├── opcclaw_floating_planet.py # ★ FloatingPlanet 悬浮星球 (1341 行)
│   │   ├── voice_interface.py # 语音接口
│   │   ├── whisper_recognizer.py # Whisper 语音识别
│   │   ├── edge_tts_engine.py # Edge TTS 引擎
│   │   ├── enhanced_chat.py   # 增强聊天
│   │   ├── ai_center_window_v2.py # AI 中心窗口 v2
│   │   ├── intelligence_window.py # 智能中枢总窗口
│   │   ├── business_ai_assistant.py # 业务 AI 助手
│   │   ├── model_config.py    # 模型配置（52212 行，最大文件）
│   │   ├── super_intelligence.py # 超级智能
│   │   ├── workflow_engine.py # 工作流引擎
│   │   ├── knowledge_base.py  # 知识库
│   │   ├── _ai_widgets.py     # AI 组件库
│   │   ├── _chat_dialog.py    # 聊天对话框
│   │   ├── _quick_tools.py    # 快捷工具
│   │   └── ...                # 50+ 其他文件
│   ├── personnel/             # 人事管理
│   │   ├── personnel_window.py
│   │   ├── member_window.py
│   │   ├── staff_window.py
│   │   ├── wallet_window.py   # 钱包
│   │   └── distribution_window.py # 分红
│   └── system/                # 系统设置
│       ├── system_window.py
│       ├── system_hub_window.py
│       ├── cloud_window.py    # 云同步
│       ├── activation_window.py # 激活
│       └── update_dialog.py   # 更新
│
├── data/                      # 业务数据库文件 (.db)
│   ├── customer.db            # 客户数据
│   ├── order.db               # 订单数据
│   ├── product.db             # 产品数据
│   ├── finance.db             # 财务数据
│   ├── member.db              # 成员数据
│   ├── users.db               # 用户数据
│   ├── wallet.db              # 钱包数据
│   ├── staff.db               # 员工数据
│   ├── activation.db          # 激活数据
│   ├── distribution.db        # 分红数据
│   ├── base_info.json         # 基础信息
│   ├── llm_config.json        # LLM 配置
│   └── rollback_log.json      # 回滚日志
│
├── deps/                      # 依赖 wheel 包
├── assets/                    # 资源文件
├── knowledge_base/            # 知识库文件
├── log/                       # 日志（crash.log 等）
├── backups/                   # 备份
├── temp/                      # 临时文件
├── 项目全书/                   # 项目文档（7 卷）
│   ├── 卷01_核心引擎/
│   ├── 卷02_认证与人事/
│   ├── 卷03_业务运营/
│   ├── 卷04_智能中枢/
│   ├── 卷05_数据与系统/
│   ├── 卷06_舰桥主控面板/
│   └── 卷07_未来路线图/
└── 源码全书/                   # 源码文档
    ├── core/
    ├── modules/
    └── opcclaw/
```

---

## Python 包清单

| 包路径 | 职责 |
|---|---|
| `core` | 宇宙渲染引擎 + 数据层 + 依赖管理 |
| `opcclaw` | AI 引擎根包（路径注入/版本号） |
| `opcclaw.core` | AgentLoop / ChatEngine / ToolRegistry / SkillLoader / MemoryStore 等 43 个核心模块 |
| `opcclaw.tools` | 100+ 工具（文件/浏览器/代码/终端/MCP/视觉/TTS 等） |
| `opcclaw.skills` | 技能注册中心（30+ 领域技能包） |
| `opcclaw.plugins` | 模型供应商 + 记忆系统 + 图像生成 + Web 搜索 |
| `opcclaw.agent` | Agent 传输层（transports/） |
| `opcclaw.data` | 引擎配置持久化 |
| `modules` | 业务模块根包 |
| `modules.auth` | 认证/登录/模型设置 |
| `modules.business` | 客户/订单/产品/财务 CRUD |
| `modules.dashboard` | 舰桥主控面板 |
| `modules.data_center` | 数据 BI / 报表 |
| `modules.intelligence` | AI 智能中枢（AgentBridge、FloatingPlanet、语音、知识库） |
| `modules.personnel` | 人事/成员/钱包/分红 |
| `modules.system` | 系统设置/云同步/激活/更新 |

---

## 入口文件

### main.py（完整桌面应用）

```python
# 启动流程：
# 1. 按需安装核心依赖（core/deps.py → ensure_core_deps()）
# 2. 注册全局异常捕获（crash.log）
# 3. 启动 PyQt5 QApplication（Fusion 风格）
# 4. 显示 LoginWindow（modules/auth/login_window.py）
```

**启动方式**：
- `python3 main.py`
- 双击 `启动宇宙版.command`

### planet_daemon.py（悬浮星球守护进程）

```python
# 启动流程：
# 1. 将项目根目录加入 sys.path
# 2. 加载 opcclaw/data/opcclaw_config.json
# 3. 初始化 opcclaw Engine（BackendFactory + AgentBridge）
# 4. 启动 FloatingPlanet 悬浮星球窗口
# 5. 注册语音唤醒 + 系统托盘
```

**启动方式**：
- `python3 planet_daemon.py`
- 双击 `启动星球守护.command`

**FloatingPlanet 类位置**：`modules/intelligence/opcclaw_floating_planet.py`，1341 行。

**状态机**：SLEEP → WAKING → ACTIVE → LISTENING → THINKING → SPEAKING

**尺寸**：休眠 85px / 活跃 117px

---

## 核心模块详解

### AgentBridge（modules/intelligence/agent_bridge.py，1379 行）

AI Agent 桥接引擎，封装 opcclaw 的双模式接口：

| 方法 | 模式 | 说明 |
|---|---|---|
| `bridge.chat(message)` | 对话模式 | 单轮工具调用（ChatEngine） |
| `bridge.run_task(message)` | 自主执行 | 多步 Think-Plan-Act-Observe-Reflect（AgentLoop） |

内置 12 个专业工具：read_file / write_file / edit_file / list_directory / search_files /
search_code / run_tests / execute_shell / desktop_control / git_operation / web_search / web_fetch_page

依赖：
- `opcclaw.core.chat_engine.ChatEngine`
- `opcclaw.core.tool_registry.ToolRegistry`
- `opcclaw.core.llm_backend.BaseLLMBackend`
- `opcclaw.core.agent_loop.AgentLoop`
- `opcclaw.core.memory_store.MemoryStore`

### 数据层（core/data.py，193 行）

统一管理所有业务数据库路径和 Schema：

| 变量 | 路径 |
|---|---|
| `ORDER_DB` | `data/order.db` |
| `PRODUCT_DB` | `data/product.db` |
| `CUSTOMER_DB` | `data/customer.db` |
| `FINANCE_DB` | `data/finance.db` |
| `MEMBER_DB` | `data/member.db` |
| `USERS_DB` | `data/users.db` |

`init_all_dbs()` 函数初始化所有表并执行 Schema 版本迁移（当前 v1）。

### 宇宙渲染（core/cosmic.py，435 行 + core/planet_painter.py，719 行）

- **cosmic.py**：动态星空背景（含真实星座 + 银河带）、星云、粒子效果、辉光
- **planet_painter.py**：程序化星球纹理（地球/木星/土星/海王星/火星等），纯 QPainter 实现

### 依赖管理（core/deps.py，129 行）

按需从 `deps/` 目录安装 wheel 包到 site-packages。
`ensure_core_deps()` 在 main.py 启动时自动调用。

---

## 技术栈

| 技术 | 用途 |
|---|---|
| Python 3 | 主语言 |
| PyQt5 | GUI 框架（窗口/控件/绘图/动画） |
| opcclaw 引擎 | AI Agent 框架（AgentLoop + ChatEngine + ToolRegistry + SkillLoader） |
| OpenAI 兼容 API | LLM 后端（通过 opcclaw plugins/model-providers） |
| SQLite | 业务数据库（customer/order/product/finance/member/users 等） |
| Whisper | 语音识别（本地） |
| Edge TTS | 文字转语音 |
| AppleScript / osascript | macOS 系统交互 |
| Shell (zsh) | 命令执行 |

---

## 启动方式

| 方式 | 命令 |
|---|---|
| 桌面应用 | `python3 main.py` |
| 桌面应用（双击） | `启动宇宙版.command` |
| 悬浮星球 | `python3 planet_daemon.py` |
| 悬浮星球（双击） | `启动星球守护.command` |

---

## 常见操作

| 操作 | 方法 |
|---|---|
| 调试桌面应用 | `python3 main.py`（crash 日志在 `log/crash.log`） |
| 调试守护进程 | `python3 planet_daemon.py`（日志在 stdout） |
| 查看数据库 | `sqlite3 data/customer.db .tables` |
| 重新生成项目全书 | `python3 gen_book.py` |
| 回滚操作 | `python3 rollback_control.py` |
| 重新初始化数据库 | 删除 `data/*.db` 后重启应用（自动重建） |
| 切换 AI 模型 | 通过 LoginWindow → ModelSetup 或修改 `opcclaw/data/opcclaw_config.json` |
| 检查依赖 | `core/deps.py` → `ensure_core_deps()` |
| 运行 opcclaw 测试 | `cd opcclaw && python3 test_opcclaw.py` |
| 查看引擎日志 | `opcclaw/logs/` 目录 |

---

## 关键文件速查

| 用途 | 路径 |
|---|---|
| 应用入口 | `main.py` |
| 守护进程入口 | `planet_daemon.py` |
| AI 桥接引擎 | `modules/intelligence/agent_bridge.py` |
| 悬浮星球 UI | `modules/intelligence/opcclaw_floating_planet.py` |
| 数据库 Schema | `core/data.py` |
| 宇宙渲染 | `core/cosmic.py` |
| 星球绘制 | `core/planet_painter.py` |
| 依赖管理 | `core/deps.py` |
| AgentLoop | `opcclaw/core/agent_loop.py` |
| ChatEngine | `opcclaw/core/chat_engine.py` |
| ToolRegistry | `opcclaw/core/tool_registry.py` |
| SkillLoader | `opcclaw/core/skill_loader.py` |
| MemoryStore | `opcclaw/core/memory_store.py` |
| LLM 后端 | `opcclaw/core/llm_backend.py` |
| 引擎配置 | `opcclaw/data/opcclaw_config.json` |
| 登录窗口 | `modules/auth/login_window.py` |
| 模型设置 | `modules/auth/model_setup_window.py` |
| 业务总窗口 | `modules/business/business_window.py` |
| 主控面板 | `modules/dashboard/dashboard_window.py` |
| 智能中枢 | `modules/intelligence/intelligence_window.py` |
| 项目全书 | `项目全书/` (7 卷) |
*（内容由AI生成，仅供参考）*
