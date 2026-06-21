---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: b11c9da246eaa2aacfce94adf18e4927_f5224fcc652e11f1af8f5254002afed2
    ReservedCode1: P+cvt2mPMXlNpXLrSuVnmgQikTea46mpulI+9xbaPJaCNEgrynn5LgzqbR8QvUwrx0lkhmXqaOwkS/INkJLVj6IVBJhVSMhIsuISRabXYKJyhYNEi0RWh/YERpyo2yctAzKnwJLJdl9ogQok+kYK5adEuBvVdMwuZ7nJpgjGszI/JhGO5ILvcyRooXg=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: b11c9da246eaa2aacfce94adf18e4927_f5224fcc652e11f1af8f5254002afed2
    ReservedCode2: P+cvt2mPMXlNpXLrSuVnmgQikTea46mpulI+9xbaPJaCNEgrynn5LgzqbR8QvUwrx0lkhmXqaOwkS/INkJLVj6IVBJhVSMhIsuISRabXYKJyhYNEi0RWh/YERpyo2yctAzKnwJLJdl9ogQok+kYK5adEuBvVdMwuZ7nJpgjGszI/JhGO5ILvcyRooXg=
---



## 项目：Iqra · AI Agent 引擎（星空版）

### 目录结构
```
core/                 ← 核心引擎，谨慎修改（改前须确认影响范围）
  chat_engine.py      — 对话引擎（chat/chat_stream 入口）
  agent_loop.py       — 自主 Agent 循环（Think→Plan→Act→Observe→Reflect）
  workspace_indexer.py— 工作区全文索引（BM25 + SQLite 持久化）
  rag_context.py      — RAG 上下文注入单例 + IQRA.md 自动注入
  semantic_search.py  — IDF 加权余弦重排序器（混合检索：BM25+语义）
  code_intel.py       — 代码智能引擎（AST 符号/引用/度量/重构）
  git_ops.py          — Git 操作安全封装
  tool_registry.py    — 工具注册中心
  llm_backend.py      — 多供应商 LLM 后端
  multi_model.py      — 多模型路由器
  multi_model_chat_engine.py — 多模型对话引擎
  super_intelligence.py — 超级智能增强
  skill_loader.py     — 技能加载器
  memory_store.py     — 内存存储
  secure_storage.py   — 安全存储
  iqra_logging.py  — 日志系统

modules/              ← 界面模块
  chat_window.py      — 主对话窗口（侧栏 + 内容面板 + 工具注册）
  git_panel.py        — Git 状态与操作面板

tools/                ← Agent 可调用工具
  builtin/
    system_tools.py   — 系统工具（时间/日期/系统信息）
    developer_tools.py— 开发者工具（shell/文件/Grep/项目地图）
    git_tools.py      — Git 工具（status/diff/log/commit/branch/stash）
    code_tools.py     — 代码智能工具（symbols/usages/imports/metrics/refactor）
  business_tools.py   — 业务工具注册枢纽
  [87 个业务工具文件] — crm/finance/inventory/marketing/order/product...

config/               ← 配置文件
  providers.json      — LLM 供应商配置
  admin_remember.json — 管理记忆
  supabase_config.py  — 数据库配置

源码全书/             ← 自动生成（gen_book.py 产出，每个 .py 独立为一个 .py.md）
```

### 铁律（违反则任务失败）

1. **不改 chat_engine.py 的公开方法签名**（chat/chat_stream/inject_workspace_context），只能末尾追加
2. **不改 tool_registry.py 的 ToolDefinition 结构**（name/description/parameters/handler/category）
3. **不改 gen_book.py**
4. **新工具通过新增文件注册**，不修改已有工具注册文件的工具定义逻辑（允许在 `_register_tools()` 中追加 `register_xxx_tools` 调用）
5. **Iqra 新增功能不引入不必要的外部依赖**——werkzeug/jieba/numpy 能用标准库替代的绝不引入
6. Bug 修复优先继承/组合，不动已有方法签名
7. tools/builtin/ 下的工具每个文件职责单一，禁止工具定义文件超过 500 行

### 风格规范

- Agent 工具返回值统一为 `dict`，有 `success` 或有 `error` 字段
- 所有工具写操作默认 `dry_run=True` 预览，需显式传 `dry_run=False` 执行
- 破坏性操作提供 `stash` 保护（Git stash、配置备份）
- 模块文件保持在 200-500 行，超限按职责拆分
- UI 使用深色主题配色（#0D1117 底色 / #58A6FF 强调色 / #3FB950 成功色），统一从 COLORS 字典引用

### 侧栏面板注入规范

在 `chat_window.py` 中新增侧栏面板的标准流程（3 步）：
1. `NAV_ITEMS` 列表追加 `("图标 名称", 索引)`
2. `MainWindow.__init__` 中创建面板实例并 `self.stack.addWidget(panel)`
3. `_on_nav_changed` 中追加自动刷新逻辑（如需要）

### 工具注册规范

在 `tools/builtin/` 下新增工具文件的标准流程（3 步）：
1. 创建 `tools/builtin/xxx_tools.py`，实现 `register_xxx_tools(registry)` 函数
2. `tools/builtin/__init__.py` 中追加 `from .xxx_tools import register_xxx_tools`
3. `modules/chat_window.py` 中追加 import 并在 `_register_tools()` 中调用

---

## 文档更新铁律（任务合并到代码修改中，死任务）

**任何代码修改完成后，必须一并完成以下文档更新，不得省略。**

### 第一步：更新项目全书（项目全书/ 目录，46 个分片文件）

项目全书已永久拆分为 `项目全书/` 目录下的独立分片文件（对齐宇宙版结构），禁止向根目录写入单文件"Iqra全书.md"。

**目录结构：**
```
项目全书/
├── README.md              — 导航索引
├── 模块状态总表.md         — 全部 418 文件 / ~182k 行
├── 版本功能地图.md         — 按时间线的完整变更记录
├── 核心架构说明.md         — Agent 循环/RAG 链路/工具注册链/多模型路由
├── 已知问题.md            — 待办与优化清单
├── 回滚管控策略.md         — 全局回滚禁止/逐模块申请/受保护区域
├── 卷01_核心引擎/（13 文件）— chat_engine / agent_loop / tool_registry / workspace_indexer ...
├── 卷02_界面模块/（3 文件） — chat_window / git_panel / 其他界面
├── 卷03_工具系统/（7 文件） — builtin / browser / MCP / terminal / skills / files / other
├── 卷04_Agent层/（4 文件）  — 适配器 / 上下文记忆 / 凭据安全 / 传输层
├── 卷05_插件系统/（4 文件） — Google Meet / 通用插件 / 开发者工具 / 工作区
├── 卷06_技能仓库/（3 文件） — QClaw / 通用技能 / 研究工具
├── 卷07_项目文档/（3 文件） — 规则系统 / 主入口 / 数据配置
└── 附录/（3 文件）        — 文件统计 / 超限清单 / 双版本对照
```

**更新规则：**

**1.1 模块状态总表更新** → 编辑 `项目全书/模块状态总表.md`
- 新增文件 → 在对应目录的表格中新增一行
- 行数变化 → 更新行数列
- 文件删除 → 删除对应行

**1.2 版本功能地图追加** → 编辑 `项目全书/版本功能地图.md`
在顶部（最新条目位置）追加，格式：
```
### YYYY-MM-DD | 简短标题

- **文件**：具体文件名 + 行数
- **改动**：做了什么 + 为什么
- **方案**：技术方案简述
- **影响**：关联影响的文件/模块
- **验证**：导入/功能测试结果
```

**1.3 卷分片更新** → 编辑 `项目全书/卷0X_xxx/` 下对应文件
涉及某模块的详细功能/参数/注意事项变化时，更新对应卷的独立分片文件。

**禁止的写法：**
- "修复了bug""优化了代码""完善了系统"

**正确的写法：**
- "修复 chat_window.py 中 _on_nav_changed 因 index 越界导致的崩溃，在访问前增加了边界检查"
- "新增 ai_chat_styles.py（45行）抽离 12 个样式常量，原模块从 657 降至 224 行"

### 第二步：更新源码全书（源码全书/ 目录）

**每次代码修改后运行 gen_book.py：**
```bash
python3 gen_book.py
```

gen_book.py 清空并重建 `源码全书/` 目录，为每个 .py 模块生成独立 `.py.md` 文件（含路径、行数、完整源码），并生成 `源码全书/README.md` 带目录树索引。当前覆盖 core/modules/tools/config 下所有 .py 文件（约 179 个）。

### 第三步：自检验证（全部通过才算完成）

- [ ] `项目全书/版本功能地图.md` 已追加本次变更条目
- [ ] `项目全书/模块状态总表.md` 对应行已更新（行数/状态/备注）
- [ ] `python3 gen_book.py` 已执行，`源码全书/` 已重新生成
- [ ] `python3 -c "from iqra.xxx import YYY"` 受影响模块导入通过

### 文档编写准则

**写给下一个 AI 看，不是写给人看。** 下一个 AI 读取 项目全书/ 时需要能：
1. 一眼看清有哪些模块（项目全书/模块状态总表.md）
2. 知道最近做了哪些改动（项目全书/版本功能地图.md）
3. 理解改动的技术细节和原因（条目内容）
4. 找到对应的源码文件（源码全书/ 目录下按文件定位）
5. 深入理解某模块（项目全书/卷0X_xxx/ 下对应分片文件）

---

## 每次任务完成前自检

- [ ] 没动 chat_engine.py / tool_registry.py 已有方法签名
- [ ] 没改 gen_book.py
- [ ] 新增功能未引入不必要的外部依赖
- [ ] 模块文件不超过 500 行（拆分超限文件）
- [ ] 所有 import 来自已有模块，没引入新依赖（除非必要）
- [ ] 项目全书/版本功能地图.md 已追加
- [ ] 项目全书/模块状态总表.md 已更新
- [ ] python3 gen_book.py 已执行
- [ ] 受影响模块导入验证通过
*（内容由AI生成，仅供参考）*
*（内容由AI生成，仅供参考）*
