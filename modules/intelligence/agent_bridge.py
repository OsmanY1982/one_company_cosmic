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
import re
import subprocess
import fnmatch
import traceback
import time
from typing import Optional, Callable, Dict, Any, List

from modules.intelligence.session_context import session_ctx

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
from opcclaw.core.smart_memory_adapter import SmartMemoryStore
from opcclaw import OPCclaw, OPCclawConfig
from PyQt5.QtCore import QObject, pyqtSignal, QThread

# ── 引擎模块（try/except，缺失不阻塞启动）──
try:
    from opcclaw.core.code_executor import CodeExecutor
    _HAVE_CODE_EXECUTOR = True
except ImportError:
    _HAVE_CODE_EXECUTOR = False
try:
    from opcclaw.core.code_intel import SymbolExtractor
    _HAVE_CODE_INTEL = True
except ImportError:
    _HAVE_CODE_INTEL = False
try:
    from opcclaw.core.workspace_indexer import WorkspaceIndexer
    _HAVE_INDEXER = True
except ImportError:
    _HAVE_INDEXER = False
try:
    from opcclaw.core.patch_engine import PatchEngine
    _HAVE_PATCH_ENGINE = True
except ImportError:
    _HAVE_PATCH_ENGINE = False
try:
    from opcclaw.core.task_scheduler import TaskScheduler
    _HAVE_TASK_SCHEDULER = True
except ImportError:
    _HAVE_TASK_SCHEDULER = False
try:
    from opcclaw.core.todo_system import TodoSystem
    _HAVE_TODO_SYSTEM = True
except ImportError:
    _HAVE_TODO_SYSTEM = False
try:
    from opcclaw.core.session_search import SessionSearch
    _HAVE_SESSION_SEARCH = True
except ImportError:
    _HAVE_SESSION_SEARCH = False
try:
    from opcclaw.core.semantic_search import SemanticSearcher, HybridRetriever
    _HAVE_SEMANTIC_SEARCH = True
except ImportError:
    _HAVE_SEMANTIC_SEARCH = False
try:
    from opcclaw.core.super_intelligence import SuperIntelligence
    _HAVE_SUPER_INTEL = True
except ImportError:
    _HAVE_SUPER_INTEL = False
try:
    from opcclaw.core.rag_context import RAGContextInjector
    _HAVE_RAG = True
except ImportError:
    _HAVE_RAG = False
try:
    from opcclaw.core.token_optimizer import TokenOptimizer
    _HAVE_TOKEN_OPT = True
except ImportError:
    _HAVE_TOKEN_OPT = False
try:
    from opcclaw.core.clarify_system import ClarifySystem
    _HAVE_CLARIFY = True
except ImportError:
    _HAVE_CLARIFY = False
try:
    from opcclaw.core.model_status import ModelStatus
    _HAVE_MODEL_STATUS = True
except ImportError:
    _HAVE_MODEL_STATUS = False
try:
    from opcclaw.core.model_status_manager import ModelStatusManager
    _HAVE_MODEL_MGR = True
except ImportError:
    _HAVE_MODEL_MGR = False
try:
    from opcclaw.core.multi_model import MultiModelRouter
    _HAVE_MULTI_MODEL = True
except ImportError:
    _HAVE_MULTI_MODEL = False
try:
    from opcclaw.core.skill_loader import SkillLoader
    _HAVE_SKILL_LOADER = True
except ImportError:
    _HAVE_SKILL_LOADER = False
try:
    from opcclaw.core.skill_system import SkillSystem
    _HAVE_SKILL_SYSTEM = True
except ImportError:
    _HAVE_SKILL_SYSTEM = False
try:
    from opcclaw.core.agent_delegate import AgentDelegate
    _HAVE_DELEGATE = True
except ImportError:
    _HAVE_DELEGATE = False
try:
    from opcclaw.core.cloud_sync import CloudSyncService
    _HAVE_CLOUD_SYNC = True
except ImportError:
    _HAVE_CLOUD_SYNC = False
try:
    from opcclaw.core.performance_monitor import PerformanceMonitor
    _HAVE_PERF_MON = True
except ImportError:
    _HAVE_PERF_MON = False
try:
    from opcclaw.core.process_manager import ProcessManager
    _HAVE_PROC_MGR = True
except ImportError:
    _HAVE_PROC_MGR = False
try:
    from opcclaw.core.secure_storage import SecureStorage
    _HAVE_SECURE = True
except ImportError:
    _HAVE_SECURE = False
try:
    from opcclaw.core.token_saver import TokenOptimizer as TokenSaverOptimizer, TokenStats
    _HAVE_TOKEN_SAVER = True
except ImportError:
    _HAVE_TOKEN_SAVER = False
try:
    from opcclaw.core.opcclaw_logging import get_logger, install as install_logging
    _HAVE_LOGGING = True
except ImportError:
    _HAVE_LOGGING = False
try:
    from opcclaw.core.provider_registry import ModelConfig
    _HAVE_PROVIDER_REG = True
except ImportError:
    _HAVE_PROVIDER_REG = False
try:
    from opcclaw.core.config_validator import ConfigValidator
    _HAVE_CONFIG_VALID = True
except ImportError:
    _HAVE_CONFIG_VALID = False
try:
    from opcclaw.core.sync_bridge import SyncBridge
    _HAVE_SYNC_BRIDGE = True
except ImportError:
    _HAVE_SYNC_BRIDGE = False
try:
    from opcclaw.core.observability import ObservableBridge
    _HAVE_OBSERVABILITY = True
except ImportError:
    _HAVE_OBSERVABILITY = False
try:
    from opcclaw.core.collaboration_client import OPCclawHermesClient
    _HAVE_COLLAB = True
except ImportError:
    _HAVE_COLLAB = False
try:
    from opcclaw.core.supabase_client import SupabaseClient
    _HAVE_SUPABASE = True
except ImportError:
    _HAVE_SUPABASE = False


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
        "执行原则：\n"
        "- 永远优先用工具完成任务，不要只给建议\n"
        "- 每次只做一步，观察结果后再继续\n"
        "- 出错后分析原因，尝试替代方案\n"
        "- 关键操作（删除/覆盖）前确认安全性\n"
        "\n"
        "能力质疑处理：\n"
        "- 如果用户问「你能不能做X」或质疑你的能力，不要用文字解释\n"
        "- 直接调用工具现场演示，用行动证明\n"
        "- 例如用户问「你不能调用工具吗」→ 立即调用 list_directory 列出桌面文件来证明\n"
    )

    def __init__(
        self,
        backend: BaseLLMBackend,
        system_prompt: str = "",
        session_id: str = None,
        persistence_dir: str = "",
    ):
        self.backend = backend
        if session_id is None:
            session_id = session_ctx.current_session_id
        self.session_id = session_id

        # ── 对话持久化存储 ──
        if not persistence_dir:
            persistence_dir = os.path.join(
                os.path.expanduser("~"), ".opcclaw", "sessions"
            )
        os.makedirs(persistence_dir, exist_ok=True)
        self._memory = SmartMemoryStore(
            base_dir=persistence_dir,
        )

        # ── 项目上下文感知 ──
        self._project_context: Dict[str, Any] = {}
        self._detect_project_context()

        # ── 增强版 System Prompt（含项目上下文）──
        full_prompt = self._build_system_prompt(system_prompt)

        # ── 工具注册表 ──
        self.registry = ToolRegistry(enable_metrics=False)
        self._register_tools()

        # ── ChatEngine（对话模式，开启 auto_save）──
        self._engine = ChatEngine(
            backend=backend,
            registry=self.registry,
            system_prompt=full_prompt,
            memory_store=self._memory,
            auto_save=True,
            session_id=session_id,
        )

        # ── 可观测性（Token/调用链/成本，缺失不阻塞引擎）──
        self.obs = None
        if _HAVE_OBSERVABILITY:
            try:
                self.obs = ObservableBridge(memory_store=self._memory)
                self.obs.attach_to(backend)
                self._engine.obs = self.obs
            except Exception:
                self.obs = None

        # ── AgentLoop（自主执行模式）──
        self._agent_loop = AgentLoop(
            engine=self._engine,
            max_iterations=50,
            max_retries=3,
            timeout_seconds=900,  # 15 分钟（35b+ 大模型需要更长推理时间）
            verbose=True,
        )

        # ── 引擎模块初始化 ──
        self._init_engine_modules()

        # ── 后台线程 ──
        self._task_thread: Optional[QThread] = None
        self._task_worker: Optional[_TaskWorker] = None

    def _init_engine_modules(self):
        """初始化所有 opcclaw 引擎模块（try/except 包裹，逐个失败不影响启动）"""
        # ── SuperIntelligence ──
        if _HAVE_SUPER_INTEL:
            try:
                self._super_intel = SuperIntelligence()
            except Exception:
                self._super_intel = None
        else:
            self._super_intel = None

        # ── RAG 上下文注入 ──
        if _HAVE_RAG:
            try:
                self._rag = RAGContextInjector()
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                self._rag.set_project(project_root, build=False)
            except Exception:
                self._rag = None
        else:
            self._rag = None

        # ── Token 优化 ──
        if _HAVE_TOKEN_OPT:
            try:
                self._token_opt = TokenOptimizer(mode="balanced")
            except Exception:
                self._token_opt = None
        else:
            self._token_opt = None

        # ── 高风险确认 ──
        if _HAVE_CLARIFY:
            try:
                self._clarify = ClarifySystem()
            except Exception:
                self._clarify = None
        else:
            self._clarify = None

        # ── 模型健康监控 + 故障切换 ──
        self._model_status = None
        if _HAVE_MODEL_STATUS:
            try:
                self._model_status = ModelStatus()
            except Exception:
                pass
        self._model_mgr = None
        if _HAVE_MODEL_MGR:
            try:
                self._model_mgr = ModelStatusManager()
            except Exception:
                pass

        # ── 多模型路由 ──
        if _HAVE_MULTI_MODEL:
            try:
                self._multi_model = MultiModelRouter()
            except Exception:
                self._multi_model = None
        else:
            self._multi_model = None

        # ── 技能系统 ──
        if _HAVE_SKILL_LOADER:
            try:
                self._skill_loader = SkillLoader()
            except Exception:
                self._skill_loader = None
        else:
            self._skill_loader = None
        if _HAVE_SKILL_SYSTEM:
            try:
                skills_dir = os.path.join(_project_root, "opcclaw", "skills")
                self._skill_system = SkillSystem(skills_dir) if os.path.isdir(skills_dir) else None
            except Exception:
                self._skill_system = None
        else:
            self._skill_system = None

        # ── 子代理分派 ──
        if _HAVE_DELEGATE:
            try:
                self._delegate = AgentDelegate()
            except Exception:
                self._delegate = None
        else:
            self._delegate = None

        # ── 工作效率工具 ──
        self._code_executor = CodeExecutor(default_timeout=30) if _HAVE_CODE_EXECUTOR else None
        self._patch_engine = PatchEngine() if _HAVE_PATCH_ENGINE else None
        if _HAVE_TASK_SCHEDULER:
            try:
                self._task_scheduler = TaskScheduler()
            except Exception:
                self._task_scheduler = None
        else:
            self._task_scheduler = None
        if _HAVE_TODO_SYSTEM:
            try:
                self._todo = TodoSystem()
            except Exception:
                self._todo = None
        else:
            self._todo = None
        self._session_search = SessionSearch() if _HAVE_SESSION_SEARCH else None

        # ── 后台服务 ──
        self._cloud_sync = None
        if _HAVE_CLOUD_SYNC:
            try:
                self._cloud_sync = CloudSyncService()
            except Exception:
                pass
        self._perf_mon = None
        if _HAVE_PERF_MON:
            try:
                self._perf_mon = PerformanceMonitor()
            except Exception:
                pass
        self._proc_mgr = ProcessManager() if _HAVE_PROC_MGR else None
        self._secure_store = SecureStorage() if _HAVE_SECURE else None

        # ── 结构化日志 ──
        self._logger = None
        if _HAVE_LOGGING:
            try:
                install_logging()
                self._logger = get_logger("agent_bridge")
            except Exception:
                pass

        # ── 配置校验 ──
        self._config_validator = None
        if _HAVE_CONFIG_VALID:
            try:
                config_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "opcclaw", "data", "opcclaw_config.json"
                )
                self._config_validator = ConfigValidator(config_path)
            except Exception:
                pass

        # ── 模型配置注册 ──
        self._provider_registry = ModelConfig() if _HAVE_PROVIDER_REG else None

        # ── Token 统计与节省 ──
        self._token_stats = None
        self._token_saver = None
        if _HAVE_TOKEN_SAVER:
            try:
                self._token_stats = TokenStats()
                self._token_saver = TokenSaverOptimizer(self._token_stats)
            except Exception:
                pass

        # ── 云端同步 ──
        self._sync_bridge = SyncBridge() if _HAVE_SYNC_BRIDGE else None

        # ── Supabase 远程后端 ──
        self._supabase = SupabaseClient() if _HAVE_SUPABASE else None

        # ── 多人协作 ──
        self._collab_client = OPCclawHermesClient() if _HAVE_COLLAB else None

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
        """将项目上下文注入 System Prompt"""
        base = base_prompt or self.DEFAULT_SYSTEM_PROMPT
        ctx = self._project_context

        if not ctx or not ctx.get("cwd"):
            return base

        lines = [base, "", "## 当前项目环境"]
        lines.append(f"- 工作目录: `{ctx['cwd']}`")

        if ctx.get("has_git"):
            lines.append("- Git 仓库: 是")
        if ctx.get("package_managers"):
            lines.append(f"- 技术栈: {', '.join(ctx['package_managers'])}")
        if ctx.get("top_files"):
            top = ctx["top_files"][:15]
            lines.append(f"- 顶层文件: {', '.join(top)}")

        lines.append(
            "\n所有文件操作默认基于以上工作目录。"
            "如需访问其他目录，请使用绝对路径。"
        )
        return "\n".join(lines)

    # ═══════════════════════════════════════════
    # 对话持久化
    # ═══════════════════════════════════════════

    def save_session(self, messages: list = None, session_id: str = None) -> bool:
        """手动保存当前会话到磁盘。
        
        Args:
            messages: 消息列表，若为 None 则使用 engine 内的消息
            session_id: 会话ID，若为 None 则使用当前 session_id
        """
        try:
            msgs = messages if messages is not None else self._engine.messages
            sid = session_id if session_id is not None else self.session_id
            self._memory.save_session(msgs, sid)
            return True
        except Exception as e:
            traceback.print_exc()
            return False

    def load_session(self, session_id: str = None) -> list:
        """从磁盘恢复会话历史，返回消息列表。
        
        Args:
            session_id: 会话ID，若为 None 则使用当前 session_id
        """
        try:
            sid = session_id if session_id is not None else self.session_id
            msgs = self._memory.load_session(sid)
            return msgs
        except Exception:
            return []

    def append_message(self, role: str, content: str, session_id: str = "default") -> str:
        """实时追加单条消息到会话（增量保存，防止崩溃丢失）"""
        existing = self._memory.load_session(session_id)
        if existing is None:
            existing = []
        existing.append({"role": role, "content": content})
        # 记录最后一条消息，供 notify_message_added 使用
        self._last_message_info = (session_id, role, content)
        return self._memory.save_session(existing, session_id)

    def notify_message_added(self):
        """通知 session_ctx 的消息监听器（悬浮球等）有新消息"""
        if hasattr(self, '_last_message_info'):
            sid, role, content = self._last_message_info
            session_ctx.notify_message_added(sid, role, content)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有已保存的会话"""
        try:
            return self._memory.list_sessions()
        except Exception:
            return []

    def rename_session(self, session_id: str, new_title: str) -> bool:
        """重命名会话"""
        try:
            return self._memory.rename_session(session_id, new_title)
        except Exception:
            return False

    def toggle_pin_session(self, session_id: str) -> bool:
        """置顶/取消置顶会话。返回 True=已置顶, False=已取消"""
        try:
            return self._memory.toggle_pin_session(session_id)
        except Exception:
            return False

    def get_sessions_dir(self) -> str:
        """返回会话文件的存储目录路径"""
        return self._memory.get_sessions_dir()

    # ═══════════════════════════════════════════
    # 模型管理（统一配置入口，替代分散的 llm_config.json）
    # ═══════════════════════════════════════════

    # ── 统一配置路径 ──
    @staticmethod
    def _config_path() -> str:
        """opcclaw_config.json 的绝对路径"""
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "opcclaw_config.json"
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
            pass
        return {"cloud_providers": {}, "local_providers": {}}

    @staticmethod
    def _save_config(config_dict: dict):
        """持久化 opcclaw_config.json"""
        try:
            cfg_path = AgentBridge._config_path()
            os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[AgentBridge] 保存配置失败: {e}")

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

            # 本地 provider：通过 /v1/models 动态发现模型
            if base_url and "localhost" in base_url:
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
        """自动发现本地 llama.cpp 已加载的模型"""
        try:
            import urllib.request
            resp = urllib.request.urlopen("http://localhost:8080/v1/models", timeout=3)
            data = json.loads(resp.read())
            return [
                {"name": m["id"], "size": 0}
                for m in data.get("data", [])
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
            memory_store=self._memory,
            auto_save=True,
            session_id=self.session_id,
        )
        self._engine.messages = old_messages
        self._agent_loop = AgentLoop(
            engine=self._engine,
            max_iterations=50,
            max_retries=3,
            timeout_seconds=900,
            verbose=True,
        )

        # ── 持久化当前模型选择，重启后自动恢复 ──
        is_cloud = provider_id in config.get("cloud_providers", {})
        is_local = provider_id in config.get("local_providers", {})
        config["active_provider_id"] = provider_id
        if is_cloud:
            config["active_provider_type"] = "cloud"
            config["cloud_providers"][provider_id]["model"] = model
        elif is_local:
            config["active_provider_type"] = "local"
            config["local_providers"][provider_id]["model"] = model
        AgentBridge._save_config(config)

        print(f"[AgentBridge] 模型切换: {old_model} → {model} (供应商: {cfg.name})")
        return True

    # ═══════════════════════════════════════════
    # 流式输出（打字机效果，对标 Codex）
    # ═══════════════════════════════════════════

    def chat_stream(
        self,
        message: str,
        on_chunk: Callable[[str], None] = None,
        on_done: Callable[[str], None] = None,
        on_tool: Callable[[str, str], None] = None,
        on_error: Callable[[str], None] = None,
    ):
        """
        流式对话（逐字输出，打字机效果）。在后台线程执行，回调运行在主线程。

        Args:
            message: 用户输入
            on_chunk: 每收到一个文本块时回调 on_chunk(chunk_str)
            on_done: 流式完成后回调 on_done(full_text)
            on_tool: 工具调用时回调 on_tool(tool_name, status)
            on_error: 流式出错时回调 on_error(error_message)
        """
        # 终止前一次流式（如果还在运行），防止旧 finished 信号误杀新线程
        self._abort_stream()

        # 管线预处理（RAG / Token 压缩 / SuperIntelligence / 多模型路由）
        self._preprocess_stream(message)

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
        if on_error:
            self._stream_worker.stream_error.connect(on_error, Qt.QueuedConnection)

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
                pass
        if hasattr(self, '_stream_thread') and self._stream_thread:
            try:
                self._stream_thread.quit()
                self._stream_thread.wait(200)
            except Exception:
                pass
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
            return self._apply_engine_pipeline(message)
        except Exception as e:
            traceback.print_exc()
            return f"[AgentBridge 错误] {e}"

    def _clear_pipeline_blocks(self, engine):
        """移除 system message 中旧的管线注入块，防止重复追加导致膨胀"""
        if not engine.messages or engine.messages[0]['role'] != 'system':
            return
        content = engine.messages[0]['content']
        content = re.sub(
            r'\n<pipeline_rag>.*?</pipeline_rag>\n',
            '', content, flags=re.DOTALL
        )
        content = re.sub(
            r'\n<pipeline_si>.*?</pipeline_si>\n',
            '', content, flags=re.DOTALL
        )
        engine.messages[0]['content'] = content

    def _apply_engine_pipeline(self, message: str) -> str:
        """
        引擎管线：对 ChatEngine 调用前注入上下文压缩、RAG、SuperIntelligence。
        管线顺序：RAG 注入 → Token 压缩 → SuperIntelligence 提示词 → 路由判断 → LLM 调用
        """
        # 清理旧的管线注入块，防止 system prompt 无限增长
        self._clear_pipeline_blocks(self._engine)

        # 1. RAG 上下文注入（直接写入 messages[0] 确保 LLM 可见）
        if self._rag:
            try:
                rag_ctx = self._rag.inject_context(message)
                if rag_ctx:
                    self._engine.inject_context(
                        f'<pipeline_rag>\n[项目上下文]\n{rag_ctx}\n</pipeline_rag>'
                    )
            except Exception:
                pass

        # 2. Token 压缩（超长对话时裁剪上下文）
        if self._token_opt:
            try:
                self._engine.messages = self._token_opt.optimize_messages(self._engine.messages)
            except Exception:
                pass

        # 3. SuperIntelligence 推理链注入
        if self._super_intel:
            try:
                si_prompt = self._super_intel.inject_prompt(message)
                if si_prompt:
                    self._engine.inject_context(
                        f'<pipeline_si>\n{si_prompt}\n</pipeline_si>'
                    )
            except Exception:
                pass

        # 4. 多模型路由（按任务类型自动选择最优后端）
        if self._multi_model:
            try:
                route = self._multi_model.route(message)
                if route and route.get("model"):
                    self.switch_model(route.get("provider_id", ""), route["model"])
            except Exception:
                pass

        # 5. 调用 ChatEngine
        try:
            return self._engine.chat(message)
        except Exception as e:
            # 故障切换：如果当前模型失败且 model_mgr 可用，尝试备用模型
            if self._model_mgr:
                try:
                    fallback = self._model_mgr.get_fallback()
                    if fallback:
                        self.switch_model(fallback.provider_id, fallback.model)
                        return self._engine.chat(message)
                except Exception:
                    pass
            raise e

    def _preprocess_stream(self, message: str):
        """
        流式管线预处理（对标 _apply_engine_pipeline），
        在 ChatEngine.chat_stream() 被 _StreamWorker 调用前执行。
        """
        self._clear_pipeline_blocks(self._engine)

        # 1. RAG 上下文注入
        if self._rag:
            try:
                rag_ctx = self._rag.inject_context(message)
                if rag_ctx:
                    self._engine.inject_context(
                        f'<pipeline_rag>\n[项目上下文]\n{rag_ctx}\n</pipeline_rag>'
                    )
            except Exception:
                pass

        # 2. Token 压缩
        if self._token_opt:
            try:
                self._engine.messages = self._token_opt.optimize_messages(self._engine.messages)
            except Exception:
                pass

        # 3. SuperIntelligence 推理链注入
        if self._super_intel:
            try:
                si_prompt = self._super_intel.inject_prompt(message)
                if si_prompt:
                    self._engine.inject_context(
                        f'<pipeline_si>\n{si_prompt}\n</pipeline_si>'
                    )
            except Exception:
                pass

        # 4. 多模型路由
        if self._multi_model:
            try:
                route = self._multi_model.route(message)
                if route and route.get("model"):
                    self.switch_model(route.get("provider_id", ""), route["model"])
            except Exception:
                pass

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
        # ── Git ──
        self._reg_git_operation()
        # ── 网络 ──
        self._reg_web_search()
        self._reg_web_fetch_page()
        self._reg_web_scrape()
        self._reg_batch_scrape()
        # ── opcclaw 高级工具 ──
        self._reg_execute_python()
        self._reg_analyze_code()
        self._reg_search_codebase()
        self._reg_apply_patch()
        self._reg_todo()
        self._reg_task_scheduler()
        self._reg_search_sessions()

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

    # ── 10. git_operation ──
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

    # ── 12b. web_scrape（OPCclaw 智能爬虫）──
    def _reg_web_scrape(self):
        """OPCclaw 智能单页爬虫：JS 渲染 + 代理轮转 + 频率限制 + 重试"""
        def handler(url: str, use_selenium: bool = False, max_paragraphs: int = 20) -> dict:
            try:
                config = OPCclawConfig(
                    use_selenium=use_selenium,
                    output_format="dict",
                    timeout=30,
                )
                scraper = OPCclaw(config)
                result = scraper.scrape_url(url)
                scraper.close()
                if isinstance(result, dict) and "paragraphs" in result:
                    result["paragraphs"] = result["paragraphs"][:max_paragraphs]
                return result
            except Exception as e:
                return {"url": url, "error": str(e), "status": "failed"}

        self.registry.register(
            name="web_scrape",
            description="OPCclaw 智能网页爬虫：带 JS 渲染、代理轮转、频率限制、指数退避重试。返回标题/元描述/段落。适合需要 JS 渲染的动态页面。",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "目标网页 URL（含 https://）"},
                    "use_selenium": {"type": "boolean", "description": "是否启用 Selenium JS 渲染", "default": False},
                    "max_paragraphs": {"type": "integer", "description": "最大返回段落数", "default": 20},
                },
                "required": ["url"],
            },
            category="web",
        )(handler)

    # ── 12c. batch_scrape（OPCclaw 批量爬虫）──
    def _reg_batch_scrape(self):
        """OPCclaw 批量爬虫：一次抓取多个 URL"""
        def handler(urls: list, use_selenium: bool = False) -> dict:
            try:
                config = OPCclawConfig(
                    use_selenium=use_selenium,
                    output_format="dict",
                    timeout=30,
                )
                scraper = OPCclaw(config)
                results = scraper.batch_scrape(urls)
                scraper.close()
                success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
                return {
                    "total": len(urls),
                    "success": success_count,
                    "failed": len(urls) - success_count,
                    "results": results,
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="batch_scrape",
            description="OPCclaw 批量网页爬虫：一次性抓取多个 URL，返回汇总统计和逐页结果。",
            parameters={
                "type": "object",
                "properties": {
                    "urls": {"type": "array", "items": {"type": "string"}, "description": "目标网页 URL 列表"},
                    "use_selenium": {"type": "boolean", "description": "是否启用 Selenium JS 渲染", "default": False},
                },
                "required": ["urls"],
            },
            category="web",
        )(handler)

    # ── 13. execute_python ──
    def _reg_execute_python(self):
        """Python 沙箱执行（code_executor 模块）"""
        def handler(code: str, timeout: int = 30) -> dict:
            if not self._code_executor:
                return {"error": "Python 沙箱未启用（code_executor 模块缺失）"}
            try:
                result = self._code_executor.execute(code, timeout=timeout)
                return {
                    "success": result.success,
                    "output": result.output or "",
                    "error": result.error or "",
                    "duration_ms": result.duration_ms,
                }
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="execute_python",
            description="在安全沙箱中执行 Python 代码，返回标准输出和错误",
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的 Python 代码"},
                    "timeout": {"type": "integer", "description": "超时秒数，默认30", "default": 30},
                },
                "required": ["code"],
            },
            category="code",
        )(handler)

    # ── 14. analyze_code ──
    def _reg_analyze_code(self):
        """代码智能分析（code_intel 模块）"""
        def handler(file_path: str, action: str = "symbols") -> dict:
            if not os.path.exists(file_path):
                return {"error": f"文件不存在: {file_path}"}
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()
                if _HAVE_CODE_INTEL:
                    import ast
                    extractor = SymbolExtractor(source.split("\n"))
                    extractor.visit(ast.parse(source))
                    symbols = extractor._symbols if hasattr(extractor, '_symbols') else []
                    return {"file": file_path, "symbols": [s.__dict__ if hasattr(s, '__dict__') else str(s) for s in symbols], "total": len(symbols)}
                else:
                    return {"error": "代码智能引擎未启用（code_intel 模块缺失）"}
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="analyze_code",
            description="分析代码文件的符号结构（函数/类/变量定义）",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "要分析的代码文件绝对路径"},
                    "action": {
                        "type": "string",
                        "description": "分析类型: symbols（符号提取）/ usages（引用搜索）/ imports（依赖分析）/ refactor（重构建议）",
                        "enum": ["symbols", "usages", "imports", "refactor"],
                        "default": "symbols",
                    },
                },
                "required": ["file_path"],
            },
            category="code",
        )(handler)

    # ── 15. search_codebase ──
    def _reg_search_codebase(self):
        """代码库语义/全文搜索（workspace_indexer 模块）"""
        def handler(query: str, top_k: int = 10) -> dict:
            if _HAVE_INDEXER:
                try:
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    indexer = WorkspaceIndexer(project_root)
                    results = indexer.search(query, top_k=top_k)
                    return {
                        "query": query,
                        "results": [{"path": r.path, "score": round(r.score, 3), "snippet": r.snippet} for r in results],
                        "count": len(results),
                    }
                except Exception as e:
                    return {"error": str(e)}
            return {"error": "代码库索引器未启用（workspace_indexer 模块缺失）"}
        self.registry.register(
            name="search_codebase",
            description="在项目代码库中全文搜索，支持中文和英文关键词",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "top_k": {"type": "integer", "description": "返回结果数，默认10", "default": 10},
                },
                "required": ["query"],
            },
            category="code",
        )(handler)

    # ── 16. apply_patch ──
    def _reg_apply_patch(self):
        """文件补丁引擎（patch_engine 模块）"""
        def handler(file_path: str, pattern: str, replacement: str, dry_run: bool = True) -> dict:
            if not self._patch_engine:
                return {"error": "补丁引擎未启用（patch_engine 模块缺失）"}
            try:
                if dry_run:
                    result = self._patch_engine.preview(file_path, pattern, replacement)
                else:
                    result = self._patch_engine.apply(file_path, pattern, replacement)
                return {
                    "file": file_path,
                    "dry_run": dry_run,
                    "matches": result.get("matches", 0),
                    "changes": result.get("changes", []),
                    "success": result.get("success", False),
                }
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="apply_patch",
            description="对文件执行查找替换补丁（默认预览不写入）",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "目标文件绝对路径"},
                    "pattern": {"type": "string", "description": "要查找的文本模式"},
                    "replacement": {"type": "string", "description": "替换后的文本"},
                    "dry_run": {"type": "boolean", "description": "是否仅预览不实际修改，默认true", "default": True},
                },
                "required": ["file_path", "pattern", "replacement"],
            },
            category="code",
        )(handler)

    # ── 17. todo ──
    def _reg_todo(self):
        """任务清单（todo_system 模块）"""
        def handler(action: str = "list", title: str = "", status: str = "") -> dict:
            todo = self._todo
            if not todo:
                return {"error": "任务系统未启用（todo_system 模块缺失）"}
            try:
                if action == "add":
                    item = todo.add(title)
                    return {"action": "add", "item": item}
                elif action == "list":
                    items = todo.list()
                    return {"action": "list", "items": items, "total": len(items)}
                elif action == "done":
                    result = todo.mark_done(title)
                    return {"action": "done", "result": result}
                else:
                    return {"error": f"未知操作: {action}，支持 add/list/done"}
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="todo",
            description="管理任务清单：添加、查看、标记完成",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "操作: add（添加）/ list（查看）/ done（完成）", "default": "list"},
                    "title": {"type": "string", "description": "任务标题（add/done 时需要）"},
                    "status": {"type": "string", "description": "状态过滤（list 时可选）"},
                },
                "required": [],
            },
            category="productivity",
        )(handler)

    # ── 18. task_scheduler ──
    def _reg_task_scheduler(self):
        """定时任务（task_scheduler 模块）"""
        def handler(action: str = "list", title: str = "", schedule: str = "") -> dict:
            sched = self._task_scheduler
            if not sched:
                return {"error": "定时任务未启用（task_scheduler 模块缺失）"}
            try:
                if action == "add":
                    task = sched.add(title, schedule)
                    return {"action": "add", "task": task}
                elif action == "list":
                    tasks = sched.list()
                    return {"action": "list", "tasks": tasks}
                elif action == "remove":
                    sched.remove(title)
                    return {"action": "remove", "title": title, "success": True}
                else:
                    return {"error": f"未知操作: {action}，支持 add/list/remove"}
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="task_scheduler",
            description="管理定时任务：创建、查看、删除",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "操作: add（添加）/ list（查看）/ remove（删除）", "default": "list"},
                    "title": {"type": "string", "description": "任务标题"},
                    "schedule": {"type": "string", "description": "调度表达式（add 时需要），如 'daily 08:00'"},
                },
                "required": [],
            },
            category="productivity",
        )(handler)

    # ── 19. search_sessions ──
    def _reg_search_sessions(self):
        """历史会话搜索（session_search 模块）"""
        def handler(query: str, top_k: int = 10) -> dict:
            ss = self._session_search
            if not ss:
                return {"error": "会话搜索未启用（session_search 模块缺失）"}
            try:
                results = ss.search(query, top_k=top_k)
                return {"query": query, "results": results, "count": len(results)}
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="search_sessions",
            description="搜索历史对话会话，找到之前讨论过的内容",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "top_k": {"type": "integer", "description": "返回结果数，默认10", "default": 10},
                },
                "required": ["query"],
            },
            category="memory",
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
        import sys, datetime
        print(f"[DIAG][{datetime.datetime.now().strftime('%H:%M:%S')}] StreamWorker.run() START — engine={type(self._engine).__name__}, msg={self._message[:50]}", flush=True)
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

