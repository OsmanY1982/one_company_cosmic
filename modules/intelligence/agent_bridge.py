"""
AgentBridge v2 — opcclaw 自主 Agent 引擎（对标 Codex / Claude Code）

双模式：
  chat(message)       → 对话模式（单轮工具调用，ChatEngine）
  run_task(message)   → 自主执行模式（多步 Think-Plan-Act-Observe-Reflect，AgentLoop）

工具套件（12 个专业工具）：
  文件:   read_file / write_file / edit_file / list_directory / search_files
  代码:   search_code / run_tests
  系统:   execute_shell / desktop_control
  Git:    git_operation
  网络:   web_search / web_fetch_page
"""

import os
import sys
import json
import subprocess
import fnmatch
import traceback
import time
from typing import Optional, Callable, Dict, Any, List

# ── opcclaw 引擎路径 ──
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_opcclaw_pkg = os.path.join(_project_root, "opcclaw")
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _opcclaw_pkg not in sys.path:
    sys.path.insert(0, _opcclaw_pkg)

from opcclaw.core.chat_engine import ChatEngine
from opcclaw.core.tool_registry import ToolRegistry
from opcclaw.core.llm_backend import BaseLLMBackend
from opcclaw.core.agent_loop import AgentLoop, AgentEvent, AgentEventType, AgentResult
from opcclaw.core.memory_store import MemoryStore
from PyQt5.QtCore import QObject, pyqtSignal, QThread


# ═══════════════════════════════════════════
# AgentBridge 主类
# ═══════════════════════════════════════════

class AgentBridge:
    """
    opcclaw 自主 Agent 引擎

    用法:
        bridge = AgentBridge(backend)
        reply = bridge.chat("今天天气如何")          # 对话模式
        bridge.run_task("重构 src/ 下的 import")     # 自主执行模式
    """

    DEFAULT_SYSTEM_PROMPT = (
        "你是 opcclaw，一人公司的全能 AI 助理。\n"
        "\n"
        "核心能力：\n"
        "1. 文件系统：读写、编辑、搜索、列目录\n"
        "2. 代码：搜索、运行测试、Shell 执行\n"
        "3. Git：查看状态、diff、提交\n"
        "4. 桌面：打开应用、控制系统设置\n"
        "5. 网络：搜索、抓取网页\n"
        "\n"
        "执行原则（严格遵守）：\n"
        "- 工具优先：用户要求读写文件、执行命令、搜索等操作时，必须调用对应工具，禁止只回复文字说「我可以帮你」\n"
        "- 创建文件必须调用 write_file，读取文件必须调用 read_file，编辑文件必须调用 edit_file\n"
        "- 每次只做一步，观察结果后再继续\n"
        "- 出错后分析原因，尝试替代方案\n"
        "- 关键操作（删除/覆盖）前确认安全性\n"
    )

    def __init__(
        self,
        backend: BaseLLMBackend,
        system_prompt: str = "",
        session_id: str = "floating_planet",
        persistence_dir: str = "",
    ):
        self.backend = backend
        self.session_id = session_id

        # ── 对话持久化存储 ──
        if not persistence_dir:
            persistence_dir = os.path.join(
                os.path.expanduser("~"), ".opcclaw", "sessions"
            )
        os.makedirs(persistence_dir, exist_ok=True)
        self._memory_store = MemoryStore(
            base_dir=persistence_dir,
        )

        # ── 项目上下文感知 ──
        self._project_context: Dict[str, Any] = {}
        self._detect_project_context()

        # ── 增强版 System Prompt（含项目上下文）──
        full_prompt = self._build_system_prompt(system_prompt)

        # ── 工具注册表 ──
        self.registry = ToolRegistry(enable_metrics=False)
        # 始终注册工具；Ollama+qwen2.5:7b 等本地模型已支持 OpenAI 兼容的 tool_calls
        self._register_tools()

        # ── ChatEngine（对话模式，开启 auto_save）──
        self._engine = ChatEngine(
            backend=backend,
            registry=self.registry,
            system_prompt=full_prompt,
            memory_store=self._memory_store,
            auto_save=True,
            session_id=session_id,
        )

        # ── AgentLoop（自主执行模式）──
        self._agent_loop = AgentLoop(
            engine=self._engine,
            max_iterations=50,
            max_retries=3,
            timeout_seconds=600,  # 10 分钟
            verbose=True,
        )

        # ── 后台线程 ──
        self._task_thread: Optional[QThread] = None
        self._task_worker: Optional[_TaskWorker] = None

    # ── 信号转发 ──
    @property
    def on_tool_start(self): return self._engine.on_tool_start
    @property
    def on_tool_result(self): return self._engine.on_tool_result
    @property
    def on_agent_event(self): return self._agent_loop.on_event
    @property
    def on_agent_progress(self): return self._agent_loop.on_progress

    # ═══════════════════════════════════════════
    # 项目上下文感知
    # ═══════════════════════════════════════════

    def _detect_project_context(self) -> None:
        """自动检测当前工作区项目结构，注入系统提示"""
        cwd = os.getcwd()
        ctx: Dict[str, Any] = {
            "cwd": cwd,
            "has_git": os.path.isdir(os.path.join(cwd, ".git")),
            "top_files": [],
            "package_managers": [],
        }

        # 检测顶层文件（.py, .json, .md, .txt）
        try:
            for f in sorted(os.listdir(cwd))[:30]:
                fp = os.path.join(cwd, f)
                if os.path.isfile(fp) and not f.startswith("."):
                    ctx["top_files"].append(f)
        except Exception as e:
            print(f"[agent_bridge] 扫描工作目录文件失败: {e}")

        # 检测包管理器
        pm_indicators = {
            "Python/pip": ["requirements.txt", "setup.py", "setup.cfg", "pyproject.toml", "Pipfile"],
            "Node.js": ["package.json", "yarn.lock", "pnpm-lock.yaml"],
            "Git": [".git"],
            "Docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
        }
        for pm, indicators in pm_indicators.items():
            if any(os.path.exists(os.path.join(cwd, i)) for i in indicators):
                ctx["package_managers"].append(pm)

        self._project_context = ctx

    def _build_system_prompt(self, base_prompt: str) -> str:
        """将项目上下文和 macOS 环境注入 System Prompt"""
        base = base_prompt or self.DEFAULT_SYSTEM_PROMPT
        ctx = self._project_context

        lines = [base, ""]

        # ── macOS 环境（始终注入，确保 AgentLoop 知道路径）──
        lines.append("## macOS 环境")
        lines.append("- 操作系统: macOS 26, Apple M5")
        lines.append("- 用户主目录: `/Users/opc`")
        lines.append("- 桌面路径: `/Users/opc/Desktop`")
        lines.append("- 下载目录: `/Users/opc/Downloads`")
        lines.append("- 文档目录: `/Users/opc/Documents`")
        lines.append("- 项目根目录: `/Volumes/D盘工作区/一人公司/one_company_cosmic/`")
        lines.append("- 常用应用: 终端(`/System/Applications/Utilities/Terminal.app`)、访达(Finder)、Safari、系统设置")
        lines.append("")

        # ── 当前项目环境 ──
        if ctx and ctx.get("cwd"):
            lines.append("## 当前项目环境")
            lines.append(f"- 工作目录: `{ctx['cwd']}`")

            if ctx.get("has_git"):
                lines.append("- Git 仓库: 是")
            if ctx.get("package_managers"):
                lines.append(f"- 技术栈: {', '.join(ctx['package_managers'])}")
            if ctx.get("top_files"):
                top = ctx["top_files"][:15]
                lines.append(f"- 顶层文件: {', '.join(top)}")

            lines.append("")

        lines.append(
            '所有文件操作默认基于以上路径。用户说"桌面"即指 `/Users/opc/Desktop`，'
            '说"下载"即指 `/Users/opc/Downloads`。如需访问其他目录，请使用绝对路径。'
        )
        return "\n".join(lines)

    # ═══════════════════════════════════════════
    # 对话持久化
    # ═══════════════════════════════════════════

    def save_session(self) -> bool:
        """手动保存当前会话到磁盘"""
        try:
            self._memory_store.save_session(
                self._engine.messages, self.session_id
            )
            return True
        except Exception as e:
            traceback.print_exc()
            return False

    def load_session(self) -> int:
        """从磁盘恢复会话历史，返回恢复的消息数"""
        try:
            msgs = self._memory_store.load_session(self.session_id)
            if msgs:
                self._engine.messages = msgs
                return len(msgs)
            return 0
        except Exception:
            return 0

    def get_history(self) -> list:
        """获取当前对话历史（用于 UI 展示）"""
        return self._engine.get_history()

    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有已保存的会话"""
        try:
            return self._memory_store.list_sessions()
        except Exception:
            return []

    # ═══════════════════════════════════════════
    # 模型管理（统一配置入口，替代分散的 llm_config.json）
    # ═══════════════════════════════════════════

    # ── 统一配置路径 ──
    @staticmethod
    def _config_path() -> str:
        """opcclaw_config.json 的绝对路径"""
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "opcclaw", "data", "opcclaw_config.json"
        )

    @staticmethod
    def _load_config() -> dict:
        """加载 opcclaw_config.json"""
        try:
            cfg_path = AgentBridge._config_path()
            if os.path.exists(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            import traceback; traceback.print_exc()
        return {"cloud_providers": {}, "local_providers": {}}

    def get_model(self) -> str:
        """获取当前使用的模型名"""
        return getattr(self.backend.config, "model", "") if hasattr(self.backend, "config") else ""

    def get_provider_info(self) -> dict:
        """获取当前供应商信息"""
        if hasattr(self.backend, "config"):
            cfg = self.backend.config
            return {
                "model": getattr(cfg, "model", ""),
                "provider_type": getattr(cfg, "provider_type", ""),
                "base_url": getattr(cfg, "base_url", ""),
                "name": getattr(cfg, "name", ""),
            }
        return {}

    @staticmethod
    def list_all_models() -> list:
        """
        从 opcclaw_config.json 读取所有已配置的模型（云端+自定义+本地+Ollama动态发现）。
        返回: [{"provider_id": str, "provider_name": str, "model": str, "category": str, "base_url": str}, ...]
          category: "cloud" | "local"
        """
        config = AgentBridge._load_config()
        models = []

        # 云端供应商
        for pid, pdata in config.get("cloud_providers", {}).items():
            pname = pdata.get("name", pid)
            model = pdata.get("model", "")
            base_url = pdata.get("base_url", "")
            if model:
                models.append({
                    "provider_id": pid,
                    "provider_name": pname,
                    "model": model,
                    "category": "cloud",
                    "base_url": base_url,
                })

        # 本地供应商
        for pid, pdata in config.get("local_providers", {}).items():
            pname = pdata.get("name", pid)
            model = pdata.get("model", "")
            base_url = pdata.get("base_url", "")

            # Ollama: 动态发现已安装模型
            if pid == "ollama":
                discovered = AgentBridge.discover_local_models()
                if discovered:
                    for m in discovered:
                        models.append({
                            "provider_id": pid,
                            "provider_name": pname,
                            "model": m["name"],
                            "category": "local",
                            "base_url": base_url,
                            "size": m.get("size", 0),
                        })
                    continue  # 跳过静态 model 字段

            if model:
                models.append({
                    "provider_id": pid,
                    "provider_name": pname,
                    "model": model,
                    "category": "local",
                    "base_url": base_url,
                })

        return models

    @staticmethod
    def discover_local_models() -> list:
        """自动发现本地 Ollama 已安装的模型（含大小）"""
        try:
            import urllib.request
            resp = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
            data = json.loads(resp.read())
            return [
                {"name": m["name"], "size": m.get("size", 0)}
                for m in data.get("models", [])
            ]
        except Exception:
            return []

    def switch_model(self, provider_id: str, model: str) -> bool:
        """
        切换模型：从 opcclaw_config.json 查找供应商配置，
        更新 backend config（name/base_url/api_key/model/provider_type），
        重建 ChatEngine 保留对话历史。
        """
        if not hasattr(self.backend, "config"):
            return False

        config = AgentBridge._load_config()
        provider_data = (
            config.get("cloud_providers", {}).get(provider_id)
            or config.get("local_providers", {}).get(provider_id)
        )
        if not provider_data:
            print(f"[AgentBridge] 未找到供应商: {provider_id}")
            return False

        old_model = self.get_model()
        old_messages = self._engine.messages
        cfg = self.backend.config

        # 更新 backend config 全部字段
        cfg.name = provider_data.get("name", provider_id)
        cfg.base_url = provider_data.get("base_url", "")
        cfg.api_key = provider_data.get("api_key", "")
        cfg.model = model
        cfg.provider_type = provider_data.get("provider_type", "openai_compatible")

        # 重建 ChatEngine，继承对话历史
        self._engine = ChatEngine(
            backend=self.backend,
            registry=self.registry,
            system_prompt=self._build_system_prompt(""),
            memory_store=self._memory_store,
            auto_save=True,
            session_id=self.session_id,
        )
        self._engine.messages = old_messages
        self._agent_loop = AgentLoop(
            engine=self._engine,
            max_iterations=50,
            max_retries=3,
            timeout_seconds=600,
            verbose=True,
        )
        print(f"[AgentBridge] 模型切换: {old_model} → {model} (供应商: {cfg.name})")
        return True

    # ═══════════════════════════════════════════
    # 流式输出（打字机效果，对标 Codex）
    # ═══════════════════════════════════════════

    def chat_stream_generator(self, message: str):
        """返回 ChatEngine.chat_stream() 的原始生成器。不做线程包装。
        调用方自行负责线程管理（适用于已有 QThread 的场景）。"""
        return self._engine.chat_stream(message)

    def chat_stream(
        self,
        message: str,
        on_chunk: Callable[[str], None] = None,
        on_done: Callable[[str], None] = None,
        on_tool: Callable[[str, str], None] = None,
    ):
        """
        流式对话（逐字输出，打字机效果）。在后台线程执行，回调运行在主线程。

        Args:
            message: 用户输入
            on_chunk: 每收到一个文本块时回调 on_chunk(chunk_str)
            on_done: 流式完成后回调 on_done(full_text)
            on_tool: 工具调用时回调 on_tool(tool_name, status)
        """
        # 终止前一次流式（如果还在运行），防止旧 finished 信号误杀新线程
        self._abort_stream()

        self._stream_thread = QThread()
        self._stream_worker = _StreamWorker(self._engine, message)
        self._stream_worker.moveToThread(self._stream_thread)

        # 连接信号到回调（跨线程安全，回调在主线程执行）
        from PyQt5.QtCore import Qt
        if on_chunk:
            self._stream_worker.chunk_ready.connect(on_chunk, Qt.QueuedConnection)
        if on_tool:
            self._stream_worker.tool_event.connect(on_tool, Qt.QueuedConnection)
        if on_done:
            self._stream_worker.stream_done.connect(on_done, Qt.QueuedConnection)

        self._stream_thread.started.connect(self._stream_worker.run)
        self._stream_worker.finished.connect(self._stream_thread.quit)
        self._stream_worker.finished.connect(self._stream_worker.deleteLater)
        self._stream_thread.finished.connect(self._stream_thread.deleteLater)
        self._stream_thread.start()

    def _abort_stream(self):
        """安全终止当前正在运行的流式线程（清除旧引用防止信号串扰）"""
        if hasattr(self, '_stream_worker') and self._stream_worker:
            try:
                self._stream_worker.finished.disconnect()
            except Exception:
                import traceback; traceback.print_exc()
        if hasattr(self, '_stream_thread') and self._stream_thread:
            try:
                self._stream_thread.quit()
                self._stream_thread.wait(200)
            except Exception:
                import traceback; traceback.print_exc()
        self._stream_worker = None
        self._stream_thread = None

    # ═══════════════════════════════════════════
    # 模式 1: 对话模式
    # ═══════════════════════════════════════════

    # ── 任务检测关键词 ──
    TASK_KEYWORDS = [
        "帮我", "重构", "写一个", "生成", "修改", "创建", "修复", "优化",
        "部署", "安装", "配置", "搜索文件", "查找", "整理", "编译",
        "测试", "运行", "迁移", "打包", "发布", "调试", "分析代码",
        "把", "请把", "找出", "提取", "转换", "合并", "拆分", "检查",
        "执行", "启动", "关闭", "重启", "清理", "格式化", "添加",
        "删除", "移除", "替换", "升级", "降级", "回滚", "备份",
    ]

    def chat(self, message: str) -> str:
        """
        智能入口：自动判定路由到对话模式或自主执行模式。

        规则：
        - 包含任务动词 → run_task_sync（AgentLoop 自主执行）
        - 否则 → 单轮对话（ChatEngine）
        - AgentLoop 失败时自动回退到 ChatEngine
        """
        is_task = any(kw in message for kw in self.TASK_KEYWORDS)

        if is_task:
            try:
                result = self.run_task_sync(message)
                if result.success:
                    return result.summary
                else:
                    return (
                        f"[任务未完成] {result.summary}\n\n"
                        f"已执行 {result.steps_taken} 步，"
                        f"调用工具: {', '.join(result.tools_called) if result.tools_called else '无'}"
                    )
            except Exception as e:
                traceback.print_exc()
                try:
                    return self._engine.chat(message)
                except Exception:
                    return f"[AgentBridge 错误] {e}"

        try:
            return self._engine.chat(message)
        except Exception as e:
            traceback.print_exc()
            return f"[AgentBridge 错误] {e}"

    def reset(self):
        """重置对话历史"""
        self._engine.messages = []
        self._engine.initialize_session()

    # ═══════════════════════════════════════════
    # 模式 2: 自主执行模式（对标 Codex）
    # ═══════════════════════════════════════════

    def run_task(self, message: str, on_event: Callable = None, on_done: Callable = None):
        """
        异步执行多步自主任务。

        Args:
            message: 任务描述（如"重构 src/ 下所有 import"）
            on_event: 每步事件回调 on_event(AgentEvent)
            on_done: 完成回调 on_done(AgentResult)
        """
        self._task_thread = QThread()
        self._task_worker = _TaskWorker(self._agent_loop, message)

        self._task_worker.moveToThread(self._task_thread)
        self._task_thread.started.connect(self._task_worker.run)

        if on_event:
            self._agent_loop.on_event.connect(on_event)
        if on_done:
            self._task_worker.finished.connect(on_done)

        self._task_worker.finished.connect(self._task_thread.quit)
        self._task_worker.finished.connect(self._task_worker.deleteLater)
        self._task_thread.finished.connect(self._task_thread.deleteLater)

        # 清理连接
        if on_event:
            self._task_thread.finished.connect(
                lambda: self._agent_loop.on_event.disconnect(on_event)
            )

        self._task_thread.start()

    def run_task_sync(self, message: str) -> AgentResult:
        """同步执行多步自主任务（会阻塞 UI，仅用于测试）"""
        return self._agent_loop.run(message)

    def stream_task(self, message: str):
        """
        流式执行自主任务，以生成器形式逐步骤返回 AgentEvent。

        用法:
            for event in bridge.stream_task("帮我在桌面创建一个 test.txt"):
                # event: AgentEvent 对象
                # event.type: THINK / PLAN / ACT / OBSERVE / REFLECT / COMPLETE / ERROR
                # event.message: 人类可读的阶段描述
                # event.data: 附加数据（工具调用结果等）
                yield event

        可用于 UI 实时展示 AgentLoop 的五阶段执行过程。
        """
        return self._agent_loop.run_stream(message)

    def cancel_task(self):
        """取消正在执行的自主任务"""
        if self._agent_loop:
            self._agent_loop.cancel()

    # ═══════════════════════════════════════════
    # 工具注册（12 个专业工具）
    # ═══════════════════════════════════════════

    def _register_tools(self):
        # ── 文件系统工具 ──
        self._reg_read_file()
        self._reg_write_file()
        self._reg_edit_file()
        self._reg_list_directory()
        self._reg_search_files()
        # ── 代码工具 ──
        self._reg_search_code()
        self._reg_run_tests()
        # ── 系统工具 ──
        self._reg_execute_shell()
        self._reg_desktop_control()
        self._reg_system_control()
        self._reg_open_application()
        self._reg_window_control()
        self._reg_clipboard_read()
        self._reg_clipboard_write()
        self._reg_take_screenshot()
        # ── Git ──
        self._reg_git_operation()
        # ── 网络 ──
        self._reg_web_search()
        self._reg_web_fetch_page()

    # ── 1. read_file ──
    def _reg_read_file(self):
        def handler(path: str, limit: int = 200) -> dict:
            try:
                if not os.path.exists(path):
                    return {"error": f"文件不存在: {path}"}
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()[:limit]
                return {
                    "content": "".join(lines),
                    "total_lines": len(lines),
                    "truncated": len(lines) >= limit,
                    "path": path,
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="read_file",
            description="读取文本文件内容，返回行数和全文",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件绝对路径"},
                    "limit": {"type": "integer", "description": "最大读取行数，默认200", "default": 200},
                },
                "required": ["path"],
            },
            category="file",
        )(handler)

    # ── 2. write_file ──
    def _reg_write_file(self):
        def handler(path: str, content: str) -> dict:
            try:
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"success": True, "path": path, "bytes": len(content)}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="write_file",
            description="创建或覆盖写入文件（自动创建目录）",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件绝对路径"},
                    "content": {"type": "string", "description": "要写入的全部内容"},
                },
                "required": ["path", "content"],
            },
            category="file",
        )(handler)

    # ── 3. edit_file（精准行级编辑，对标 Claude Code）──
    def _reg_edit_file(self):
        def handler(path: str, old_str: str, new_str: str, replace_all: bool = False) -> dict:
            try:
                if not os.path.exists(path):
                    return {"error": f"文件不存在: {path}"}
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                count = content.count(old_str)
                if count == 0:
                    return {"error": f"未找到匹配文本。请确认 old_str 与文件中内容完全一致（含空格/换行）"}
                if not replace_all and count > 1:
                    return {
                        "error": f"找到 {count} 处匹配，请设置 replace_all=true 或提供更精确的 old_str",
                        "matches": count,
                    }
                new_content = content.replace(old_str, new_str) if replace_all else content.replace(old_str, new_str, 1)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return {
                    "success": True,
                    "path": path,
                    "replacements": count if replace_all else 1,
                    "old_bytes": len(content),
                    "new_bytes": len(new_content),
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="edit_file",
            description="精准替换文件中的文本片段（行级编辑）。old_str 必须与文件内容完全一致（含空格/换行）",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件绝对路径"},
                    "old_str": {"type": "string", "description": "要替换的原始文本，必须完全匹配"},
                    "new_str": {"type": "string", "description": "替换后的新文本"},
                    "replace_all": {"type": "boolean", "description": "是否替换所有匹配项", "default": False},
                },
                "required": ["path", "old_str", "new_str"],
            },
            category="file",
        )(handler)

    # ── 4. list_directory ──
    def _reg_list_directory(self):
        def handler(path: str, pattern: str = "*") -> dict:
            try:
                if not os.path.isdir(path):
                    return {"error": f"不是有效目录: {path}"}
                items = []
                for entry in sorted(os.listdir(path)):
                    full = os.path.join(path, entry)
                    is_dir = os.path.isdir(full)
                    items.append({
                        "name": entry,
                        "type": "dir" if is_dir else "file",
                        "size": os.path.getsize(full) if not is_dir else 0,
                    })
                if pattern != "*":
                    items = [i for i in items if fnmatch.fnmatch(i["name"], pattern)]
                return {"path": path, "count": len(items), "items": items[:200]}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="list_directory",
            description="列出目录内容。支持 fnmatch 过滤（如 *.py, test_*）",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "目录绝对路径"},
                    "pattern": {"type": "string", "description": "文件名通配符，默认 *", "default": "*"},
                },
                "required": ["path"],
            },
            category="file",
        )(handler)

    # ── 5. search_files（glob 搜索）──
    def _reg_search_files(self):
        def handler(directory: str, pattern: str, recursive: bool = True) -> dict:
            import glob
            try:
                if recursive:
                    search_pattern = os.path.join(directory, "**", pattern)
                else:
                    search_pattern = os.path.join(directory, pattern)
                results = glob.glob(search_pattern, recursive=recursive)
                return {"pattern": pattern, "count": len(results), "files": results[:100]}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="search_files",
            description="按通配符模式搜索文件（如 **/*.py 递归搜索所有 .py 文件）",
            parameters={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "搜索根目录"},
                    "pattern": {"type": "string", "description": "glob 模式（如 *.py, test_*.py, **/*.json）"},
                    "recursive": {"type": "boolean", "description": "是否递归子目录", "default": True},
                },
                "required": ["directory", "pattern"],
            },
            category="file",
        )(handler)

    # ── 6. search_code（ripgrep 代码搜索）──
    def _reg_search_code(self):
        def handler(query: str, directory: str = ".", file_pattern: str = "*", max_results: int = 50) -> dict:
            try:
                cmd = ["rg", "--line-number", "--max-count", str(max_results), query]
                if file_pattern != "*":
                    cmd.extend(["--glob", file_pattern])
                cmd.append(directory)
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                                       cwd=os.path.expanduser("~"))
                if result.returncode == 1:
                    return {"query": query, "count": 0, "matches": [], "note": "未找到匹配"}
                lines = result.stdout.strip().split("\n")[:max_results]
                return {"query": query, "count": len(lines), "matches": lines}
            except FileNotFoundError:
                # 回退到 grep
                try:
                    cmd = ["grep", "-rn", "--include=" + file_pattern if file_pattern != "*" else "-r", query, directory]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    lines = result.stdout.strip().split("\n")[:max_results]
                    return {"query": query, "count": len(lines), "matches": lines, "backend": "grep"}
                except Exception as e:
                    return {"error": f"ripgrep 和 grep 均不可用: {e}"}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="search_code",
            description="在代码库中搜索文本（ripgrep）。支持正则、文件类型过滤",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词或正则表达式"},
                    "directory": {"type": "string", "description": "搜索目录，默认当前目录", "default": "."},
                    "file_pattern": {"type": "string", "description": "文件类型过滤（如 *.py, *.js）", "default": "*"},
                    "max_results": {"type": "integer", "description": "最大结果数", "default": 50},
                },
                "required": ["query"],
            },
            category="code",
        )(handler)

    # ── 7. run_tests ──
    def _reg_run_tests(self):
        def handler(test_path: str = "", framework: str = "auto") -> dict:
            try:
                if not test_path:
                    return {"error": "请指定测试文件或目录路径"}
                if framework == "auto":
                    if "pytest" in test_path.lower() or os.path.exists("pytest.ini") or os.path.exists("pyproject.toml"):
                        framework = "pytest"
                    else:
                        framework = "unittest"

                if framework == "pytest":
                    result = subprocess.run(
                        [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"],
                        capture_output=True, text=True, timeout=120,
                        cwd=os.path.expanduser("~"),
                    )
                else:
                    result = subprocess.run(
                        [sys.executable, "-m", "unittest", test_path, "-v"],
                        capture_output=True, text=True, timeout=120,
                        cwd=os.path.expanduser("~"),
                    )
                return {
                    "framework": framework,
                    "returncode": result.returncode,
                    "passed": result.returncode == 0,
                    "stdout": result.stdout[-3000:],
                    "stderr": result.stderr[-1000:],
                }
            except subprocess.TimeoutExpired:
                return {"error": "测试超时（120秒）"}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="run_tests",
            description="运行测试套件（自动检测 pytest/unittest）",
            parameters={
                "type": "object",
                "properties": {
                    "test_path": {"type": "string", "description": "测试文件或目录路径"},
                    "framework": {"type": "string", "description": "pytest / unittest / auto", "default": "auto"},
                },
                "required": ["test_path"],
            },
            category="code",
        )(handler)

    # ── 8. execute_shell ──
    def _reg_execute_shell(self):
        def handler(command: str, timeout: int = 60) -> dict:
            try:
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True, timeout=timeout,
                    cwd=os.path.expanduser("~"),
                )
                return {
                    "stdout": result.stdout[:8000],
                    "stderr": result.stderr[:4000],
                    "returncode": result.returncode,
                }
            except subprocess.TimeoutExpired:
                return {"error": f"命令超时 ({timeout}s)", "stdout": "", "stderr": ""}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="execute_shell",
            description="在 macOS 终端执行 shell 命令。适用：安装依赖、运行脚本、系统查询",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "shell 命令"},
                    "timeout": {"type": "integer", "description": "超时秒数", "default": 60},
                },
                "required": ["command"],
            },
            category="system",
        )(handler)

    # ── 9. desktop_control（AppleScript 桌面操控）──
    def _reg_desktop_control(self):
        def handler(action: str, target: str = "", text: str = "") -> dict:
            try:
                scripts = {
                    "open_app": f'tell application "{target}" to activate',
                    "close_app": f'tell application "{target}" to quit',
                    "type_text": f'tell application "System Events" to keystroke "{text}"',
                    "press_keys": f'tell application "System Events" to keystroke "{text}"',
                    "get_frontmost": 'tell application "System Events" to get name of first application process whose frontmost is true',
                    "switch_app": f'tell application "{target}" to activate',
                    "open_url": f'open location "{target}"',
                    "volume_up": "set volume output volume (output volume of (get volume settings) + 10)",
                    "volume_down": "set volume output volume (output volume of (get volume settings) - 10)",
                    "mute": "set volume with output muted",
                    "sleep": 'tell application "System Events" to sleep',
                    "screenshot": 'do shell script "screencapture -i ~/Desktop/screenshot.png"',
                }
                if action not in scripts:
                    return {"error": f"不支持的操作: {action}。可用: {list(scripts.keys())}"}
                script = scripts[action]
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15)
                if result.returncode != 0:
                    return {"error": result.stderr.strip()}
                return {"success": True, "action": action, "output": result.stdout.strip()}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="desktop_control",
            description="macOS 桌面操控：打开/关闭应用、模拟输入、系统控制",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "操作: open_app/close_app/type_text/press_keys/switch_app/volume_up/volume_down/mute/sleep/screenshot"},
                    "target": {"type": "string", "description": "目标应用名/按键/URL", "default": ""},
                    "text": {"type": "string", "description": "要输入的文本（type_text/press_keys 时使用）", "default": ""},
                },
                "required": ["action"],
            },
            category="system",
        )(handler)

    # ── 10. system_control（macOS 系统控制）──
    def _reg_system_control(self):
        """执行 macOS 系统操作：锁屏/静音/取消静音/打开系统设置等"""
        def handler(action: str) -> dict:
            try:
                action_map = {
                    "lock_screen": 'tell application "System Events" to keystroke "q" using {command down, control down}',
                    "mute": "set volume with output muted",
                    "unmute": "set volume without output muted",
                    "open_system_settings": 'tell application "System Settings" to activate',
                    "open_system_preferences": 'tell application "System Preferences" to activate',
                    "show_desktop": 'tell application "System Events" to keystroke "d" using {command down, option down}',
                    "empty_trash": 'tell application "Finder" to empty the trash',
                }
                if action not in action_map:
                    return {"error": f"不支持的系统操作: {action}。可用: {list(action_map.keys())}"}
                script = action_map[action]
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    return {"error": result.stderr.strip()}
                return {"success": True, "action": action, "output": result.stdout.strip()}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="system_control",
            description="执行 macOS 系统操作：锁屏(lock_screen)、静音(mute)、取消静音(unmute)、打开系统设置(open_system_settings)、显示桌面(show_desktop)、清空废纸篓(empty_trash)",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "系统操作: lock_screen/mute/unmute/open_system_settings/open_system_preferences/show_desktop/empty_trash"},
                },
                "required": ["action"],
            },
            category="system",
        )(handler)

    # ── 11. open_application（启动 macOS 应用）──
    def _reg_open_application(self):
        """按应用名启动 macOS 应用"""
        def handler(app_name: str) -> dict:
            try:
                script = f'tell application "{app_name}" to activate'
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    # 尝试通过 open 命令启动
                    try:
                        subprocess.run(["open", "-a", app_name], capture_output=True, text=True, timeout=10, check=True)
                        return {"success": True, "app_name": app_name, "method": "open -a"}
                    except Exception:
                        return {"error": f"无法启动应用: {app_name}。请确认应用名称是否正确。"}
                return {"success": True, "app_name": app_name}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="open_application",
            description="按应用名启动 macOS 应用。常用名: Safari/Finder/终端/Terminal/微信/企业微信/飞书/钉钉/Chrome/VSCode/Notes",
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "应用名称（如 Safari、微信、终端）"},
                },
                "required": ["app_name"],
            },
            category="system",
        )(handler)

    # ── 12. window_control（窗口操作）──
    def _reg_window_control(self):
        """窗口操作：最小化/关闭/切换"""
        def handler(app_name: str, action: str = "switch") -> dict:
            try:
                actions = {
                    "switch": f'tell application "{app_name}" to activate',
                    "minimize": f'tell application "System Events" to tell process "{app_name}" to set value of attribute "AXMinimized" of window 1 to true',
                    "close": f'tell application "{app_name}" to close window 1',
                    "hide": f'tell application "System Events" to tell process "{app_name}" to set visible to false',
                }
                if action not in actions:
                    return {"error": f"不支持的窗口操作: {action}。可用: {list(actions.keys())}"}
                script = actions[action]
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    return {"error": result.stderr.strip()}
                return {"success": True, "app_name": app_name, "action": action}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="window_control",
            description="窗口操作：切换(switch)、最小化(minimize)、关闭(close)、隐藏(hide)指定应用的窗口",
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "应用进程名（如 Safari、微信）"},
                    "action": {"type": "string", "description": "窗口操作: switch/minimize/close/hide", "default": "switch"},
                },
                "required": ["app_name"],
            },
            category="system",
        )(handler)

    # ── 13. clipboard_read（读取剪贴板）──
    def _reg_clipboard_read(self):
        """读取 macOS 剪贴板内容"""
        def handler() -> dict:
            try:
                result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
                content = result.stdout
                return {"success": True, "content": content[:5000], "length": len(content)}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="clipboard_read",
            description="读取 macOS 剪贴板文本内容",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            category="system",
        )(handler)

    # ── 14. clipboard_write（写入剪贴板）──
    def _reg_clipboard_write(self):
        """写入 macOS 剪贴板"""
        def handler(text: str) -> dict:
            try:
                proc = subprocess.run(["pbcopy"], input=text, capture_output=True, text=True, timeout=5)
                if proc.returncode != 0:
                    return {"error": proc.stderr.strip()}
                return {"success": True, "length": len(text)}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="clipboard_write",
            description="写入文本到 macOS 剪贴板",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要写入剪贴板的文本内容"},
                },
                "required": ["text"],
            },
            category="system",
        )(handler)

    # ── 15. take_screenshot（截取屏幕截图）──
    def _reg_take_screenshot(self):
        """截取屏幕截图并保存"""
        def handler(mode: str = "full", save_path: str = "") -> dict:
            try:
                import time
                timestamp = int(time.time())
                if not save_path:
                    save_path = os.path.join(os.path.expanduser("~"), "Desktop", f"screenshot_{timestamp}.png")
                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                if mode == "selection":
                    cmd = ["screencapture", "-i", save_path]
                elif mode == "window":
                    cmd = ["screencapture", "-w", save_path]
                else:
                    cmd = ["screencapture", save_path]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if not os.path.exists(save_path):
                    return {"error": "截图失败或被用户取消", "mode": mode}
                size = os.path.getsize(save_path)
                return {"success": True, "path": save_path, "mode": mode, "size_bytes": size}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="take_screenshot",
            description="截取 macOS 屏幕截图并保存。模式: full(全屏)/selection(选区)/window(窗口)",
            parameters={
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "description": "截图模式: full/selection/window", "default": "full"},
                    "save_path": {"type": "string", "description": "保存路径（默认桌面）", "default": ""},
                },
                "required": [],
            },
            category="system",
        )(handler)

    # ── 16. git_operation ──
    def _reg_git_operation(self):
        def handler(operation: str, repo_path: str = ".", args: str = "") -> dict:
            try:
                valid_ops = ["status", "diff", "log", "branch", "add", "commit", "pull", "push", "stash", "checkout"]
                if operation not in valid_ops:
                    return {"error": f"不支持的 Git 操作: {operation}。可用: {valid_ops}"}

                cmd = ["git", "-C", repo_path, operation]
                if args:
                    cmd.extend(args.split())

                if operation == "commit":
                    cmd.append("-m")
                    cmd.append(args)

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                return {
                    "operation": operation,
                    "repo": repo_path,
                    "returncode": result.returncode,
                    "stdout": result.stdout[:4000],
                    "stderr": result.stderr[:2000],
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="git_operation",
            description="Git 版本控制：查看状态、diff、log、提交等",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "description": "Git 操作: status/diff/log/branch/add/commit/pull/push/stash/checkout"},
                    "repo_path": {"type": "string", "description": "仓库路径", "default": "."},
                    "args": {"type": "string", "description": "额外参数（如文件路径、commit message）", "default": ""},
                },
                "required": ["operation"],
            },
            category="code",
        )(handler)

    # ── 11. web_search ──
    def _reg_web_search(self):
        def handler(query: str, max_results: int = 8) -> dict:
            try:
                import urllib.request, urllib.parse
                url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                })
                with urllib.request.urlopen(req, timeout=10) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                from html.parser import HTMLParser

                class P(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.results = []
                        self._cur = {}
                        self._in_result = self._in_link = self._in_snippet = False
                    def handle_starttag(self, tag, attrs):
                        d = dict(attrs)
                        cls = d.get("class", "")
                        if tag == "div" and "result" in cls:
                            self._in_result = True
                            self._cur = {"title": "", "link": "", "snippet": ""}
                        if self._in_result and tag == "a" and "result__a" in cls:
                            self._in_link = True
                            self._cur["link"] = d.get("href", "")
                        if self._in_result and tag == "a" and "result__snippet" in cls:
                            self._in_snippet = True
                    def handle_endtag(self, tag):
                        if tag == "div" and self._cur:
                            self.results.append(self._cur)
                            self._cur = {}
                            self._in_result = False
                        if tag == "a":
                            self._in_link = self._in_snippet = False
                    def handle_data(self, data):
                        if self._in_link:
                            self._cur["title"] += data
                        if self._in_snippet:
                            self._cur["snippet"] += data

                parser = P()
                parser.feed(html)
                return {"query": query, "count": len(parser.results[:max_results]), "results": parser.results[:max_results]}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="web_search",
            description="DuckDuckGo 网页搜索，获取实时信息",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "max_results": {"type": "integer", "description": "最大结果数", "default": 8},
                },
                "required": ["query"],
            },
            category="web",
        )(handler)

    # ── 12. web_fetch_page ──
    def _reg_web_fetch_page(self):
        def handler(url: str) -> dict:
            try:
                import urllib.request
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                # 简易正文提取
                from html.parser import HTMLParser
                class TextExtractor(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.text = []
                        self._skip = False
                    def handle_starttag(self, tag, attrs):
                        if tag in ("script", "style", "noscript"):
                            self._skip = True
                    def handle_endtag(self, tag):
                        if tag in ("script", "style", "noscript"):
                            self._skip = False
                    def handle_data(self, data):
                        if not self._skip:
                            t = data.strip()
                            if t:
                                self.text.append(t)
                ex = TextExtractor()
                ex.feed(html)
                content = "\n".join(ex.text)
                return {"url": url, "chars": len(content), "content": content[:8000]}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="web_fetch_page",
            description="抓取网页正文内容（提取纯文本）",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "网页 URL（含 https://）"},
                },
                "required": ["url"],
            },
            category="web",
        )(handler)


# ═══════════════════════════════════════════
# 后台任务 Worker（用于 AgentLoop 异步执行）
# ═══════════════════════════════════════════

class _TaskWorker(QObject):
    """在 QThread 中执行 AgentLoop.run()"""

    finished = pyqtSignal(object)  # AgentResult

    def __init__(self, agent_loop: AgentLoop, message: str):
        super().__init__()
        self._agent_loop = agent_loop
        self._message = message

    def run(self):
        try:
            result = self._agent_loop.run(self._message)
            self.finished.emit(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(AgentResult(
                success=False,
                summary=f"AgentLoop 执行异常: {e}",
                steps_taken=0,
                tools_called=[],
                errors=[str(e)],
                events=[],
                duration_seconds=0,
            ))


# ═══════════════════════════════════════════
# 流式 Worker（用于 chat_stream 异步逐块输出）
# ═══════════════════════════════════════════

class _StreamWorker(QObject):
    """在 QThread 中执行 ChatEngine.chat_stream()，通过信号逐块回调到主线程"""

    chunk_ready = pyqtSignal(str)      # 文本块
    tool_event = pyqtSignal(str, str)  # (tool_name, status: running/OK/Failed)
    stream_done = pyqtSignal(str)      # (full_text)
    stream_error = pyqtSignal(str)     # (error_message)
    finished = pyqtSignal()

    def __init__(self, engine: ChatEngine, message: str):
        super().__init__()
        self._engine = engine
        self._message = message

    def run(self):
        accumulated = ""
        try:
            for chunk in self._engine.chat_stream(self._message):
                # 工具调用标记
                if "Calling tool:" in chunk:
                    name = chunk.split("Calling tool:")[1].split("...")[0].strip()
                    self.tool_event.emit(name, "running")
                elif ": OK]" in chunk and not chunk.startswith('{"'):
                    name = chunk[1:].split(":")[0].strip()
                    self.tool_event.emit(name, "OK")
                elif ": Failed]" in chunk and not chunk.startswith('{"'):
                    name = chunk[1:].split(":")[0].strip()
                    self.tool_event.emit(name, "Failed")

                # 跳过 usage JSON
                if chunk.startswith('{"usage"'):
                    continue

                accumulated += chunk
                self.chunk_ready.emit(chunk)

            self.stream_done.emit(accumulated)

        except Exception as e:
            import traceback
            traceback.print_exc()
            err = f"\n[流式传输中断: {e}]"
            accumulated += err
            self.stream_error.emit(err)
            self.stream_done.emit(accumulated)

        self.finished.emit()
