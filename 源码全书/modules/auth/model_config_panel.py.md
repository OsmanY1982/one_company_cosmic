# `modules/auth/model_config_panel.py`

> 路径：`modules/auth/model_config_panel.py` | 行数：937


---


```python
import logging

logger = logging.getLogger(__name__)

"""
模型配置面板 — 可复用于登录后模型设置、智能中心AI对话、悬浮球对话框
三种模式：预设云端模型 / 自定义端点 / 本地推理

与 iqra 共享配置格式（iqra_config.json）
"""
import os, json, re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox,
    QDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread

# ── 预设供应商模板 ──
PRESET_PROVIDERS = [
    {"id": "deepseek",        "name": "DeepSeek",         "base_url": "https://api.deepseek.com/v1",                "model": "deepseek-chat",     "desc": "DeepSeek-V3 通用大模型，性价比极高",           "local": False, "models": ["deepseek-chat", "deepseek-reasoner"]},
    {"id": "openai",          "name": "OpenAI",            "base_url": "https://api.openai.com/v1",                  "model": "gpt-4o",            "desc": "GPT-4o / GPT-4 / GPT-3.5 系列",              "local": False, "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini"]},
    {"id": "claude",          "name": "Anthropic Claude",  "base_url": "https://api.anthropic.com/v1",               "model": "claude-sonnet-4-20250514", "desc": "Claude Sonnet 4 / Opus 4 系列",          "local": False, "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514"]},
    {"id": "tongyi",          "name": "通义千问 (阿里云)",   "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus",   "desc": "阿里云通义千问 Qwen 系列",                     "local": False, "models": ["qwen-plus", "qwen-max", "qwen-turbo", "qwen3-235b-a22b"]},
    # ⚠️ bailian 已移除（含共享管理员 Key / MaaS 端点）
    {"id": "zhipu",           "name": "智谱 GLM",          "base_url": "https://open.bigmodel.cn/api/paas/v4",       "model": "glm-4-plus",       "desc": "智谱 GLM-4 系列",                              "local": False, "models": ["glm-4-plus", "glm-4-flash", "glm-4v-plus"]},
    {"id": "moonshot",        "name": "Moonshot (月之暗面)", "base_url": "https://api.moonshot.cn/v1",                 "model": "moonshot-v1-8k",   "desc": "月之暗面 Kimi / Moonshot",                    "local": False, "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]},
    {"id": "groq",            "name": "Groq",              "base_url": "https://api.groq.com/openai/v1",              "model": "llama-3.3-70b-versatile", "desc": "Groq LPU 高速推理",                    "local": False, "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]},
    {"id": "together",        "name": "Together AI",       "base_url": "https://api.together.xyz/v1",                 "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo", "desc": "Together AI 多模型托管", "local": False, "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo"]},
    {"id": "openrouter",      "name": "OpenRouter",        "base_url": "https://openrouter.ai/api/v1",                "model": "openai/gpt-4o",    "desc": "OpenRouter 多模型聚合网关",                   "local": False, "models": ["openai/gpt-4o", "anthropic/claude-sonnet-4-20250514"]},
    {"id": "siliconflow",     "name": "SiliconFlow",       "base_url": "https://api.siliconflow.cn/v1",               "model": "deepseek-ai/DeepSeek-V3", "desc": "硅基流动 多模型推理平台",             "local": False, "models": ["deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-72B-Instruct"]},
    {"id": "mistral",         "name": "Mistral AI",        "base_url": "https://api.mistral.ai/v1",                   "model": "mistral-large-latest", "desc": "Mistral Large / Small / Codestral",     "local": False, "models": ["mistral-large-latest", "codestral-latest"]},
    {"id": "minimax",         "name": "MiniMax (海螺AI)",   "base_url": "https://api.minimax.chat/v1",                "model": "abab6.5s-chat",    "desc": "MiniMax 海螺AI - ABAB 系列",                "local": False, "models": ["abab6.5s-chat", "abab6.5-chat"]},
    {"id": "cohere",          "name": "Cohere",            "base_url": "https://api.cohere.com/v1",                   "model": "command-r-plus",   "desc": "Cohere Command R/R+ 企业级 RAG",             "local": False, "models": ["command-r-plus", "command-r"]},
    {"id": "stepfun",         "name": "阶跃星辰 StepFun",   "base_url": "https://api.stepfun.com/v1",                  "model": "step-2-16k",       "desc": "阶跃星辰 Step 系列大模型",                   "local": False, "models": ["step-2-16k", "step-1-flash"]},
]

# ── 硬编码供应商模型列表（无需网络即可显示）──
PROVIDER_MODELS = {
    "OpenAI": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "o4-mini", "o3", "o3-mini"],
    "DeepSeek": ["deepseek-chat", "deepseek-reasoner"],
    "Google": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
    "Anthropic Claude": ["claude-sonnet-4-20250514", "claude-3.5-sonnet", "claude-3.5-haiku"],
    "Groq": ["llama-4-scout-17b-16e", "llama-3.3-70b", "deepseek-r1-distill-llama-70b"],
    "Together AI": ["meta-llama/Llama-4-Maverick-17B", "meta-llama/Llama-3.3-70B-Instruct-Turbo", "deepseek-ai/DeepSeek-R1"],
    "智谱 GLM": ["glm-4-plus", "glm-4-flash", "glm-4-air"],
    "Moonshot (月之暗面)": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
    "通义千问 (阿里云)": ["qwen-plus", "qwen-max", "qwen-turbo", "qwen3-235b-a22b"],
    "MiniMax (海螺AI)": ["abab7-chat", "abab6.5s-chat"],
    "SiliconFlow": ["Qwen/Qwen3-235B-A22B", "Qwen/Qwen2.5-72B-Instruct", "deepseek-ai/DeepSeek-V3"],
    "OpenRouter": ["openai/gpt-4o", "anthropic/claude-sonnet-4", "google/gemini-2.5-pro", "meta-llama/llama-4-maverick"],
    "Mistral AI": ["mistral-large-latest", "codestral-latest"],
    "Cohere": ["command-r-plus", "command-r"],
    "阶跃星辰 StepFun": ["step-2-16k", "step-1-flash"],
}

LOCAL_SERVICES = [
    {"id": "ollama",    "name": "Ollama",     "base_url": "http://localhost:11434/v1", "desc": "本地开源大模型运行平台，完全离线",                  "models": []},
    {"id": "lmstudio",  "name": "LM Studio",  "base_url": "http://localhost:1234/v1",  "desc": "图形界面管理模型，开箱即用",                       "models": ["local-model"]},
    {"id": "vllm",      "name": "vLLM",       "base_url": "http://localhost:8000/v1",  "desc": "高性能推理引擎，适合生产环境",                      "models": ["default"]},
    {"id": "llamacpp",  "name": "llama.cpp",  "base_url": "http://localhost:8080/v1",  "desc": "轻量 GGUF 模型推理",                              "models": ["local"]},
]

# ── 配置路径 ──
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "iqra", "data")
IQRA_CONFIG_PATH = os.path.join(DATA_DIR, "iqra_config.json")


def _save_iqra_config(config_dict: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(IQRA_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2, ensure_ascii=False)


def _load_iqra_config() -> dict:
    try:
        if os.path.exists(IQRA_CONFIG_PATH):
            with open(IQRA_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[model_config_panel] 加载配置失败: {e}")
    return {}


# ── 模型过滤 ──

# 已知废弃模型前缀（自动排除，不显示在下拉列表中）
_DEPRECATED_PREFIXES = [
    "text-davinci", "text-ada", "text-babbage", "text-curie",
    "code-davinci", "code-cushman",
    "gpt-3.5-turbo-instruct", "davinci", "curie", "babbage", "ada",
]


def _filter_usable_models(models: list[str]) -> list[str]:
    """过滤掉过期/快照/废弃/非对话模型，只保留可用的对话模型。

    规则:
    1. 移除含4位日期后缀的快照模型 (如 gpt-4-0314, gpt-3.5-turbo-0301)
       注: 8位日期后缀(如 claude-sonnet-4-20250514)是版本号，不杀
    2. 移除已知废弃前缀的模型 (如 text-davinci-*, gpt-3.5-turbo-instruct)
    3. 移除音频/TTS 模型 (whisper-, tts-)
    4. 移除 embedding 模型 (text-embedding-, bge-, embedding-)
    5. 移除 moderation 模型 (text-moderation-, omni-moderation-)
    6. 移除已知非对话/过时模型后缀
    """
    # 4位日期快照后缀: gpt-4-0314, gpt-3.5-turbo-0301, gpt-3.5-turbo-1106, etc.
    date_pattern = re.compile(r'-\d{4}$')

    # 非对话模型的前缀黑名单
    _NON_CHAT_PREFIXES = [
        "text-embedding-", "bge-", "embedding-",
        "text-moderation-", "omni-moderation-",
        "tts-", "whisper-", "text-to-speech",
    ]
    # 非对话模型关键词（包含即排除）
    _NON_CHAT_KEYWORDS = [
        "-tts-", "embedding", "moderation", "whisper",
        "dall-e", "dalle",
        "-edit",  # text-edit-001 等
        "-similarity", "-search-",
    ]
    # 已知应排除的精确后缀
    _BLACKLIST_SUFFIXES = [
        "-search-doc", "-search-query", "-code-search-",
        "-similarity", "-insert", 
    ]

    result = []
    for m in models:
        # 废弃前缀
        if any(m.startswith(p) or m == p for p in _DEPRECATED_PREFIXES):
            continue
        # 4位日期快照
        if date_pattern.search(m):
            continue
        # 非对话前缀
        if any(m.startswith(p) for p in _NON_CHAT_PREFIXES):
            continue
        # 非对话关键词
        m_lower = m.lower()
        if any(kw in m_lower for kw in _NON_CHAT_KEYWORDS):
            continue
        # 黑名单后缀
        if any(m_lower.endswith(s) for s in _BLACKLIST_SUFFIXES):
            continue
        result.append(m)

    return result


def _populate_model_combo(combo: QComboBox, models: list[str], saved_model: str = ""):
    """用模型列表填充下拉框，并尝试恢复之前选中的模型。"""
    combo.clear()
    if not models:
        combo.addItem("（无可用的活跃模型）", "")
        if saved_model:
            combo.setEditText(saved_model)
        return
    for m in models:
        combo.addItem(m, m)
    # 恢复已保存的模型
    if saved_model:
        idx = combo.findText(saved_model)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        else:
            combo.setEditText(saved_model)


# ── 手动模型获取线程（仅用于自定义/本地模式的按钮触发）──

class _ManualModelFetcher(QThread):
    """后台线程：手动触发从 OpenAI 兼容端点获取可用模型列表。"""
    finished = pyqtSignal(list, str)  # (model_list, error_msg)

    def __init__(self, base_url: str, api_key: str = "", timeout: int = 15):
        super().__init__()
        self._base_url = base_url
        self._api_key = api_key
        self._timeout = timeout

    def run(self):
        try:
            from iqra.core.llm_backend import get_available_models
            raw = get_available_models(self._base_url, self._api_key, timeout=self._timeout)
            usable = _filter_usable_models(raw)
            self.finished.emit(usable, "")
        except Exception as e:
            self.finished.emit([], str(e))


class _OllamaModelFetcher(QThread):
    """后台线程：从 Ollama /api/tags 端点获取本地模型列表。"""
    finished = pyqtSignal(list, str)  # (model_list, error_msg)

    def __init__(self, base_url: str, timeout: int = 15):
        super().__init__()
        self._base_url = base_url
        self._timeout = timeout

    def run(self):
        import urllib.request
        import urllib.parse
        import ssl
        try:
            parsed = urllib.parse.urlparse(self._base_url)
            origin = f"{parsed.scheme}://{parsed.hostname}:{parsed.port or 11434}"
            endpoint = urllib.parse.urljoin(origin + "/", "api/tags")

            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(endpoint, method="GET")
            with urllib.request.urlopen(req, context=ctx, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            models = []
            for m in data.get("models", []):
                name = m.get("name", "")
                if name:
                    size = m.get("size", 0)
                    size_str = f" ({size / 1024 / 1024 / 1024:.1f}GB)" if size else ""
                    models.append(f"{name}{size_str}")
            self.finished.emit(models, "")
        except Exception as e:
            self.finished.emit([], str(e))


# ── 样式 ──
INPUT_STYLE = """
    QLineEdit {
        background: rgba(8, 16, 32, 220);
        color: #99ccff;
        border: 1px solid rgba(60, 140, 240, 45);
        border-radius: 18px;
        padding: 10px 18px;
        font-size: 13px;
    }
    QLineEdit:focus {
        border: 1px solid rgba(0, 200, 255, 160);
        background: rgba(10, 20, 40, 240);
    }
    QLineEdit::placeholder {
        color: #334466;
    }
"""

COMBO_STYLE = """
    QComboBox {
        background: rgba(8, 16, 32, 220);
        color: #99ccff;
        border: 1px solid rgba(60, 140, 240, 45);
        border-radius: 18px;
        padding: 10px 18px;
        font-size: 13px;
    }
    QComboBox:hover { border: 1px solid rgba(0, 200, 255, 140); }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: rgba(10, 18, 36, 245);
        color: #99ccff;
        selection-background-color: rgba(40, 100, 200, 80);
        border: 1px solid rgba(60, 140, 240, 50);
        outline: none;
    }
"""

LABEL_STYLE = "color: #6688aa; font-size: 11px; letter-spacing: 2px; background: transparent;"

BTN_PRIMARY = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0055cc, stop:1 #0088ff);
        color: white; border: none; border-radius: 22px;
        padding: 10px 40px; font-size: 14px; font-weight: 700;
        letter-spacing: 4px;
    }
    QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0077ee, stop:1 #00aaff); }
    QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0044aa, stop:1 #0066cc); }
"""

BTN_SECONDARY = """
    QPushButton {
        background: rgba(30, 40, 60, 200);
        color: #8899aa; border: 1px solid rgba(70, 90, 120, 50);
        border-radius: 22px; padding: 9px 32px; font-size: 13px;
        font-weight: 600; letter-spacing: 3px;
    }
    QPushButton:hover { background: rgba(40, 55, 80, 220); color: #aaccee; }
"""


# ═══════════════════════════════════════════
# ModelConfigDialog — 弹窗包装（非独立模式）
# ═══════════════════════════════════════════

class ModelConfigDialog(QWidget):
    """模型设置弹窗，嵌入 ModelConfigPanel。用于 AIChatWindow / FloatingPlanet 的「⚙ 引擎设置」按钮"""

    accepted = pyqtSignal()

    def __init__(self, parent=None, bridge=None):
        super().__init__(parent)
        self._bridge = bridge
        self.setWindowFlags(
            Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint
        )
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("引 擎 设 置")
        self.setMinimumSize(620, 580)
        self.setStyleSheet("""
            ModelConfigDialog {
                background: rgba(5, 10, 24, 248);
                border: 1px solid rgba(0, 180, 255, 60);
                border-radius: 16px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._panel = ModelConfigPanel(self, standalone=False)
        self._panel.config_saved.connect(self._on_config_saved)
        layout.addWidget(self._panel)

    def closeEvent(self, event):
        """弹窗关闭时清理正在运行的模型拉取线程"""
        if hasattr(self._panel, '_model_fetcher') and self._panel._model_fetcher:
            try:
                self._panel._model_fetcher.quit()
                self._panel._model_fetcher.wait(2000)
            except Exception:
                logger.exception("异常详情")
        super().closeEvent(event)

    def _on_config_saved(self, config: dict):
        """保存后自动切换引擎模型"""
        provider_id = config.get("active_provider_id", "")
        provider_type = config.get("active_provider_type", "")
        model = ""

        if provider_type == "cloud":
            prov = config.get("cloud_providers", {}).get(provider_id, {})
            model = prov.get("model", "")
        elif provider_type == "local":
            prov = config.get("local_providers", {}).get(provider_id, {})
            model = prov.get("model", "")
            if not model and prov.get("models"):
                model = prov["models"][0]

        if self._bridge and provider_id and model:
            try:
                self._bridge.switch_model(provider_id, model)
            except Exception as e:
                print(f"[ModelConfigDialog] 切换模型失败: {e}")

        self.accepted.emit()
        self.close()


# ═══════════════════════════════════════════
# ModelConfigPanel — 可复用的模型配置面板
# ═══════════════════════════════════════════

class ModelConfigPanel(QWidget):
    """
    可复用模型配置面板，用于:
      - 登录后模型设置（ModelSetupWindow 嵌入，standalone=True）
      - 智能中心 AI 对话窗口（AIChatWindow 弹窗，standalone=False）
      - 悬浮球对话框（FloatingPlanet 弹窗，standalone=False）
    
    standalone=True:  显示"点火"/"跳过配置"按钮，保存后发射 config_saved → ModelSetupWindow 创建 AgentBridge
    standalone=False: 显示"保存并切换"按钮，保存后发射 config_saved → ModelConfigDialog 调用 bridge.switch_model()
    模型切换统一通过 AgentBridge.switch_model() + _BridgeSignals.model_changed 全局信号广播
    """

    config_saved = pyqtSignal(dict)  # 配置保存后发射，携带 config dict

    def __init__(self, parent=None, standalone: bool = False):
        super().__init__(parent)
        self._standalone = standalone
        self._existing = _load_iqra_config()
        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(0)
        main.setContentsMargins(0, 0, 0, 0)

        # 标题
        title = QLabel("启 动 引 擎")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: #aaccee; font-size: 20px; font-weight: 900; "
            "letter-spacing: 12px; background: transparent; padding: 22px 0 10px 0;"
        )
        main.addWidget(title)

        sub = QLabel("选择 AI 模型提供商以激活智能中心")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #446688; font-size: 11px; background: transparent; padding-bottom: 14px;")
        main.addWidget(sub)

        # ── 三个 Tab ──
        self._tab_bar = QWidget()
        tab_layout = QHBoxLayout(self._tab_bar)
        tab_layout.setSpacing(0)
        tab_layout.setContentsMargins(40, 0, 40, 0)

        self._tab_preset = QPushButton("预设模型")
        self._tab_custom = QPushButton("自定义端点")
        self._tab_local = QPushButton("本地推理")
        self._tabs = [self._tab_preset, self._tab_custom, self._tab_local]
        for t in self._tabs:
            t.setCheckable(True)
            t.setCursor(Qt.PointingHandCursor)
            t.setFixedHeight(36)
            t.clicked.connect(lambda checked, btn=t: self._switch_tab(btn))
        self._tab_preset.setChecked(True)
        self._update_tab_styles()

        tab_layout.addWidget(self._tab_preset)
        tab_layout.addWidget(self._tab_custom)
        tab_layout.addWidget(self._tab_local)
        main.addWidget(self._tab_bar)
        main.addSpacing(8)

        # ── 内容栈 ──
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent;")
        self._stack.addWidget(self._build_preset_panel())
        self._stack.addWidget(self._build_custom_panel())
        self._stack.addWidget(self._build_local_panel())
        main.addWidget(self._stack, 1)

        # ── 底部按钮 ──
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(40, 12, 40, 20)
        btn_row.setSpacing(16)

        if self._standalone:
            skip_btn = QPushButton("跳过配置 (离线模式)")
            skip_btn.setStyleSheet(BTN_SECONDARY)
            skip_btn.setCursor(Qt.PointingHandCursor)
            skip_btn.clicked.connect(self._skip)
            btn_row.addWidget(skip_btn)

        btn_row.addStretch()

        if self._standalone:
            self._action_btn = QPushButton("点 火")
        else:
            self._action_btn = QPushButton("保存并切换")
        self._action_btn.setStyleSheet(BTN_PRIMARY)
        self._action_btn.setCursor(Qt.PointingHandCursor)
        self._action_btn.clicked.connect(self._on_action)
        btn_row.addWidget(self._action_btn)

        main.addLayout(btn_row)

    # ─── Tab 切换逻辑 ───

    def _tab_style(self, active: bool) -> str:
        if active:
            return """
                QPushButton {
                    background: rgba(20, 60, 140, 180);
                    color: #ddeeff; border: 1px solid rgba(0, 180, 255, 140);
                    border-bottom: none; border-radius: 14px 14px 0 0;
                    font-size: 12px; font-weight: 700;
                    padding: 8px 20px;
                }
            """
        return """
            QPushButton {
                background: transparent; color: #557799;
                border: 1px solid transparent;
                border-bottom: 1px solid rgba(50, 100, 180, 30);
                border-radius: 14px 14px 0 0;
                font-size: 12px; font-weight: 500;
                padding: 8px 20px;
            }
            QPushButton:hover { color: #88aacc; background: rgba(15, 30, 60, 100); }
        """

    def _update_tab_styles(self):
        for t in self._tabs:
            t.setStyleSheet(self._tab_style(t.isChecked()))

    def _switch_tab(self, btn):
        for t in self._tabs:
            t.setChecked(t == btn)
        self._update_tab_styles()
        idx = self._tabs.index(btn)
        self._stack.setCurrentIndex(idx)

    # ─── 预设模式面板 ───

    def _build_preset_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        v = QVBoxLayout(panel)
        v.setSpacing(14)
        v.setContentsMargins(50, 10, 50, 10)

        lbl1 = QLabel("模型提供商")
        lbl1.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl1)

        self._preset_provider = QComboBox()
        self._preset_provider.setStyleSheet(COMBO_STYLE)
        self._preset_provider.setMinimumHeight(42)
        for p in PRESET_PROVIDERS:
            icon = "🏠" if p["local"] else "☁️"
            self._preset_provider.addItem(f"{icon}  {p['name']} — {p['desc']}", p["id"])
        self._preset_provider.currentIndexChanged.connect(self._on_preset_provider_changed)
        v.addWidget(self._preset_provider)

        lbl2 = QLabel("模型")
        lbl2.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl2)

        self._preset_model = QComboBox()
        self._preset_model.setStyleSheet(COMBO_STYLE)
        self._preset_model.setEditable(True)
        self._preset_model.setMinimumHeight(42)
        v.addWidget(self._preset_model)

        lbl3 = QLabel("API Key")
        lbl3.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl3)

        self._preset_key = QLineEdit()
        self._preset_key.setStyleSheet(INPUT_STYLE)
        self._preset_key.setEchoMode(QLineEdit.Password)
        self._preset_key.setPlaceholderText("输入 API Key（安全存储，不外传）")
        v.addWidget(self._preset_key)

        v.addStretch()
        self._on_preset_provider_changed()
        return panel

    def _on_preset_provider_changed(self):
        idx = self._preset_provider.currentIndex()
        if idx < 0:
            return
        pid = self._preset_provider.currentData()
        provider = next((p for p in PRESET_PROVIDERS if p["id"] == pid), None)
        if not provider:
            return

        # 用硬编码字典填充模型列表（即时显示，无需网络）
        self._preset_model.clear()
        hardcoded = PROVIDER_MODELS.get(provider["name"], [])
        if hardcoded:
            for m in hardcoded:
                self._preset_model.addItem(m, m)

        # 恢复已保存的 key 和 model
        cloud = self._existing.get("cloud_providers", {})
        if pid in cloud:
            existing_key = cloud[pid].get("api_key", "")
            existing_model = cloud[pid].get("model", "")
            if existing_model:
                idx_m = self._preset_model.findText(existing_model)
                if idx_m >= 0:
                    self._preset_model.setCurrentIndex(idx_m)
                else:
                    self._preset_model.setEditText(existing_model)
            if existing_key:
                self._preset_key.setText(existing_key)

    # ─── 自定义模式面板 ───

    def _build_custom_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        v = QVBoxLayout(panel)
        v.setSpacing(14)
        v.setContentsMargins(50, 10, 50, 10)

        # URL 和 Key 保持 QLineEdit
        lines = [
            ("API Base URL", "custom_url", "https://api.example.com/v1", False),
            ("API Key", "custom_key", "sk-...", True),
        ]
        self._custom_inputs = {}
        for label_text, attr, placeholder, is_pass in lines:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(LABEL_STYLE)
            v.addWidget(lbl)

            le = QLineEdit()
            le.setStyleSheet(INPUT_STYLE)
            le.setPlaceholderText(placeholder)
            if is_pass:
                le.setEchoMode(QLineEdit.Password)
            v.addWidget(le)
            self._custom_inputs[attr] = le

        # URL 改变时自动尝试拉取模型列表
        self._custom_inputs["custom_url"].editingFinished.connect(self._on_custom_url_changed)

        # 模型名称 → QComboBox (editable) + "获取模型" 按钮
        model_label = QLabel("模型名称 (Model Name)")
        model_label.setStyleSheet(LABEL_STYLE)
        v.addWidget(model_label)

        model_row = QHBoxLayout()
        model_row.setSpacing(8)

        self._custom_model_combo = QComboBox()
        self._custom_model_combo.setStyleSheet(COMBO_STYLE)
        self._custom_model_combo.setEditable(True)
        self._custom_model_combo.setMinimumHeight(42)
        self._custom_model_combo.setPlaceholderText("输入模型名或点击获取模型")
        model_row.addWidget(self._custom_model_combo, 1)

        fetch_btn = QPushButton("获取模型")
        fetch_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0, 160, 240, 25);
                color: #66bbff;
                border: 1px solid rgba(0, 160, 240, 50);
                border-radius: 18px;
                padding: 10px 18px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(0, 180, 255, 40);
                border-color: rgba(0, 200, 255, 140);
            }
            QPushButton:disabled {
                color: rgba(102, 187, 255, 40);
                border-color: rgba(0, 160, 240, 20);
            }
        """)
        fetch_btn.clicked.connect(self._on_fetch_custom_models)
        model_row.addWidget(fetch_btn)
        v.addLayout(model_row)

        self._custom_inputs["custom_model"] = self._custom_model_combo

        v.addStretch()

        existing_custom = self._existing.get("cloud_providers", {}).get("custom", {})
        if existing_custom:
            self._custom_inputs["custom_url"].setText(existing_custom.get("base_url", ""))
            self._custom_inputs["custom_key"].setText(existing_custom.get("api_key", ""))
            existing_model = existing_custom.get("model", "")
            if existing_model:
                idx = self._custom_model_combo.findText(existing_model)
                if idx >= 0:
                    self._custom_model_combo.setCurrentIndex(idx)
                else:
                    self._custom_model_combo.setEditText(existing_model)

        return panel

    def _on_custom_url_changed(self):
        """自定义端点 URL 变更后记录，不自动拉取模型列表（由用户手动点击"获取模型"触发）。"""
        pass

    def _on_fetch_custom_models(self):
        """手动点击"获取模型"按钮时拉取模型列表。"""
        url = self._custom_inputs["custom_url"].text().strip()
        key = self._custom_inputs["custom_key"].text().strip()

        if not url:
            QMessageBox.warning(self, "缺少URL", "请先填写 API Base URL")
            return

        btn = self.sender()
        if btn:
            btn.setEnabled(False)
            btn.setText("获取中...")

        saved_model = self._custom_inputs["custom_model"].currentText().strip()
        combo = self._custom_model_combo

        # 插入加载指示器
        loading_label = "⏳ 刷新模型列表中..."
        old_idx = combo.findText(loading_label)
        if old_idx >= 0:
            combo.removeItem(old_idx)
        combo.insertItem(0, loading_label, "")
        combo.setCurrentIndex(0)

        self._model_fetcher = _ManualModelFetcher(url, key, timeout=15)

        def on_finished(models, error):
            try:
                lidx = combo.findText(loading_label)
                if lidx >= 0:
                    combo.removeItem(lidx)
                if error:
                    print(f"[ModelConfigPanel] 获取模型列表失败: {error}")
                    if saved_model and combo.findText(saved_model) < 0:
                        combo.setEditText(saved_model)
                elif models:
                    _populate_model_combo(combo, models, saved_model)
                if btn:
                    btn.setEnabled(True)
                    btn.setText("获取模型")
            except RuntimeError:
                logger.exception("异常详情")
                pass  # widget 已销毁
            finally:
                self._model_fetcher = None

        self._model_fetcher.finished.connect(on_finished)
        self._model_fetcher.start()

    # ─── 本地模式面板 ───

    def _build_local_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        v = QVBoxLayout(panel)
        v.setSpacing(14)
        v.setContentsMargins(50, 10, 50, 10)

        lbl1 = QLabel("本地推理服务")
        lbl1.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl1)

        self._local_service = QComboBox()
        self._local_service.setStyleSheet(COMBO_STYLE)
        self._local_service.setMinimumHeight(42)
        for s in LOCAL_SERVICES:
            self._local_service.addItem(f"🖥  {s['name']} — {s['desc']}", s["id"])
        self._local_service.currentIndexChanged.connect(self._on_local_service_changed)
        v.addWidget(self._local_service)

        lbl2 = QLabel("Base URL")
        lbl2.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl2)

        self._local_url = QLineEdit()
        self._local_url.setStyleSheet(INPUT_STYLE)
        self._local_url.setPlaceholderText("自动填充")
        v.addWidget(self._local_url)

        lbl3 = QLabel("模型名称")
        lbl3.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl3)

        model_row = QHBoxLayout()
        model_row.setSpacing(8)

        self._local_model = QComboBox()
        self._local_model.setStyleSheet(COMBO_STYLE)
        self._local_model.setEditable(True)
        self._local_model.setMinimumHeight(42)
        model_row.addWidget(self._local_model, stretch=1)

        self._refresh_btn = QPushButton("刷新模型")
        self._refresh_btn.setStyleSheet(BTN_SECONDARY)
        self._refresh_btn.setFixedWidth(100)
        self._refresh_btn.setFixedHeight(42)
        self._refresh_btn.setCursor(Qt.PointingHandCursor)
        self._refresh_btn.clicked.connect(self._refresh_local_models)
        model_row.addWidget(self._refresh_btn)

        v.addLayout(model_row)
        v.addStretch()

        self._on_local_service_changed()

        local = self._existing.get("local_providers", {})
        if local:
            first_key = list(local.keys())[0] if local else None
            if first_key:
                idx = self._local_service.findData(first_key)
                if idx >= 0:
                    self._local_service.setCurrentIndex(idx)
                cfg = local[first_key]
                if cfg.get("base_url"):
                    self._local_url.setText(cfg["base_url"])
                if cfg.get("model"):
                    midx = self._local_model.findText(cfg["model"])
                    if midx >= 0:
                        self._local_model.setCurrentIndex(midx)
                    else:
                        self._local_model.setEditText(cfg["model"])

        return panel

    def _on_local_service_changed(self):
        sid = self._local_service.currentData()
        svc = next((s for s in LOCAL_SERVICES if s["id"] == sid), None)
        if not svc:
            return
        self._local_url.setText(svc["base_url"])

        # 用硬编码列表填充（不自动远程拉取，由用户手动点击"刷新模型"触发）
        self._local_model.clear()
        hardcoded = svc.get("models", [])
        if hardcoded:
            for m in hardcoded:
                self._local_model.addItem(m, m)

    def _refresh_local_models(self):
        """手动刷新：从本地服务端点重新拉取模型列表。"""
        url = self._local_url.text().strip()
        sid = self._local_service.currentData()
        saved_model = self._local_model.currentText().strip()
        self._refresh_btn.setEnabled(False)
        self._refresh_btn.setText("获取中...")

        combo = self._local_model
        loading_label = "⏳ 刷新模型列表中..."
        old_idx = combo.findText(loading_label)
        if old_idx >= 0:
            combo.removeItem(old_idx)
        combo.insertItem(0, loading_label, "")
        combo.setCurrentIndex(0)

        # Ollama 使用 /api/tags 端点（非 OpenAI 兼容 /v1/models）
        if sid == "ollama" or "11434" in url:
            self._model_fetcher = _OllamaModelFetcher(url, timeout=15)
        else:
            self._model_fetcher = _ManualModelFetcher(url, "", timeout=15)

        def on_finished(models, error):
            try:
                lidx = combo.findText(loading_label)
                if lidx >= 0:
                    combo.removeItem(lidx)
                if error:
                    print(f"[ModelConfigPanel] 获取本地模型列表失败: {error}")
                    if saved_model and combo.findText(saved_model) < 0:
                        combo.setEditText(saved_model)
                elif models:
                    _populate_model_combo(combo, models, saved_model)
                self._refresh_btn.setEnabled(True)
                self._refresh_btn.setText("刷新模型")
            except RuntimeError:
                logger.exception("异常详情")
                pass  # widget 已销毁
            finally:
                self._model_fetcher = None

        self._model_fetcher.finished.connect(on_finished)
        self._model_fetcher.start()

    # ─── 配置构建 ───

    def _get_config(self) -> dict:
        active_tab = self._stack.currentIndex()
        config = {
            "active_provider_id": "",
            "active_provider_type": "",
            "cloud_providers": {},
            "local_providers": {},
        }
        if active_tab == 0:  # 预设模式
            pid = self._preset_provider.currentData()
            key = self._preset_key.text().strip()
            model = self._preset_model.currentText().strip() or self._preset_model.currentData() or ""
            provider = next((p for p in PRESET_PROVIDERS if p["id"] == pid), None)
            if not provider:
                return None
            config["active_provider_id"] = pid
            config["active_provider_type"] = "cloud"
            config["cloud_providers"][pid] = {
                "name": provider["name"],
                "provider_type": "openai_compatible",
                "base_url": provider["base_url"],
                "api_key": key,
                "model": model,
            }
        elif active_tab == 1:  # 自定义模式
            url = self._custom_inputs["custom_url"].text().strip()
            key = self._custom_inputs["custom_key"].text().strip()
            model = self._custom_inputs["custom_model"].currentText().strip()
            if not url or not model:
                QMessageBox.warning(self, "参数缺失", "请填写 API Base URL 和模型名称")
                return None
            config["active_provider_id"] = "custom"
            config["active_provider_type"] = "cloud"
            config["cloud_providers"]["custom"] = {
                "name": "自定义 OpenAI 兼容",
                "provider_type": "openai_compatible",
                "base_url": url,
                "api_key": key,
                "model": model,
            }
        elif active_tab == 2:  # 本地模式
            sid = self._local_service.currentData()
            url = self._local_url.text().strip()
            model = self._local_model.currentData() or self._local_model.currentText().strip() or ""
            svc = next((s for s in LOCAL_SERVICES if s["id"] == sid), None)
            if not svc:
                return None
            config["active_provider_id"] = sid
            config["active_provider_type"] = "local"
            config["local_providers"][sid] = {
                "name": svc["name"],
                "provider_type": "openai_compatible",
                "base_url": url,
                "model": model,
                "api_key": "",
            }
        return config

    # ─── 操作 ───

    def _on_action(self):
        config = self._get_config()
        if config is None:
            return
        _save_iqra_config(config)

        # standalone 模式：仅保存，由外部（ModelSetupWindow）处理引擎初始化
        # 非 standalone 模式：仅保存，由外部（ModelConfigDialog/AIChatWindow/FloatingPlanet）调用 switch_model 处理

        self.config_saved.emit(config)

    def _skip(self):
        """跳过配置（仅 standalone 模式）"""
        config = {"active_provider_id": "", "active_provider_type": "none"}
        self.config_saved.emit(config)

    def _reinit_engine(self, config: dict):
        """
        已废弃 — 旧版通过创建新 AgentBridge 初始化引擎，存在以下问题：
        1. 创建新 bridge 会导致 AIChatWindow / FloatingPlanet / IqraChatDialog 持有旧引用
        2. 新 bridge 的 model_changed signal 广播后无人监听
        3. 线程状态（chat_stream / AgentLoop）未迁移

        当前架构：
        - AgentBridge.switch_model() 不更换实例，仅替换后端
        - model_changed 全局信号通过 _BridgeSignals 单例广播
        - 所有窗口监听 model_changed 自动同步 UI
        """
        pass

```
