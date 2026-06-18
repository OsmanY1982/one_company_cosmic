"""
大模型配置对话框 — LLMConfigDialog v2
v2 新增：Ollama 自动发现模型、测试连接后自动填充可用模型列表
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QComboBox, QDialogButtonBox,
    QMessageBox, QHBoxLayout,
)
from PyQt5.QtCore import Qt

from core.llm_client import LLMClient, ModelConfig, PROVIDERS
from modules.intelligence.ai_chat_styles import INPUT_STYLE, BTN_SETTINGS, BTN_PRIMARY


def _discover_local_models() -> list:
    """自动发现本地 llama.cpp 已加载的模型"""
    try:
        import urllib.request, json
        resp = urllib.request.urlopen("http://localhost:8080/v1/models", timeout=3)
        data = json.loads(resp.read())
        return [m["id"] for m in data.get("data", [])]
    except Exception:
        return []


class LLMConfigDialog(QDialog):
    """大模型配置对话框 v2 — 支持自动模型发现"""

    def __init__(self, config: ModelConfig, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LLM 配置 v2")
        self.setMinimumWidth(500)
        self.setStyleSheet("background: rgba(15,8,25,245); color: #ccbbdd; font-size: 12px;")
        self._config = config
        self._discovered_models = []
        self._build_ui()

    def _build_ui(self):
        l = QVBoxLayout(self)
        l.setSpacing(12)
        l.setContentsMargins(20, 16, 20, 16)

        form = QFormLayout()
        form.setSpacing(10)

        # 提供商选择
        self.cb_provider = QComboBox()
        self.cb_provider.setStyleSheet(INPUT_STYLE)
        for key, info in PROVIDERS.items():
            self.cb_provider.addItem(f"{info['name']} — {info['description']}", key)
        idx = self.cb_provider.findData(self._config.provider)
        if idx >= 0:
            self.cb_provider.setCurrentIndex(idx)
        self.cb_provider.currentIndexChanged.connect(self._on_provider_changed)
        form.addRow("提供商:", self.cb_provider)

        # API 地址
        self.le_url = QLineEdit(self._config.base_url)
        self.le_url.setStyleSheet(INPUT_STYLE)
        form.addRow("API 地址:", self.le_url)

        # API Key
        self.le_key = QLineEdit(self._config.api_key)
        self.le_key.setStyleSheet(INPUT_STYLE)
        self.le_key.setEchoMode(QLineEdit.Password)
        self.le_key.setPlaceholderText("本地 Ollama 无需 Key")
        form.addRow("API Key:", self.le_key)

        # 模型名称 — 对 Ollama 使用下拉框 + 刷新按钮
        model_row = QHBoxLayout()
        self.cb_model = QComboBox()
        self.cb_model.setEditable(True)
        self.cb_model.setStyleSheet(INPUT_STYLE)
        self.cb_model.setMinimumWidth(260)

        # 如果当前是 llama_proxy，填充发现模型
        if self._config.provider == "llama_proxy":
            self._discovered_models = _discover_local_models()
            for m in self._discovered_models:
                self.cb_model.addItem(m)
            self.cb_model.setCurrentText(self._config.model_name)

        self._refresh_model_btn = QPushButton("发现")
        self._refresh_model_btn.setToolTip("从本地 llama.cpp / 远程 API 拉取可用模型列表")
        self._refresh_model_btn.setFixedSize(50, 28)
        self._refresh_model_btn.setStyleSheet("""
            QPushButton {
                background: rgba(100,140,200,35); color: #99bbee;
                border: 1px solid rgba(100,140,200,55); border-radius: 8px;
                font-size: 10px;
            }
            QPushButton:hover { background: rgba(120,160,220,60); }
        """)
        self._refresh_model_btn.clicked.connect(self._discover_models)
        model_row.addWidget(self.cb_model, 1)
        model_row.addWidget(self._refresh_model_btn)
        form.addRow("模型名称:", model_row)

        # Temperature
        self.le_temp = QLineEdit(str(self._config.temperature))
        self.le_temp.setStyleSheet(INPUT_STYLE)
        form.addRow("Temperature:", self.le_temp)

        # Max Tokens
        self.le_max_tokens = QLineEdit(str(self._config.max_tokens))
        self.le_max_tokens.setStyleSheet(INPUT_STYLE)
        form.addRow("Max Tokens:", self.le_max_tokens)

        l.addLayout(form)

        # 测试连接按钮
        test_btn = QPushButton("测试连接")
        test_btn.setStyleSheet(BTN_SETTINGS)
        test_btn.clicked.connect(self._test_connection)
        l.addWidget(test_btn)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #888; font-size: 11px;")
        self.lbl_status.setWordWrap(True)
        l.addWidget(self.lbl_status)

        # 确定/取消
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.setStyleSheet("""
            QPushButton {
                background: rgba(150,60,220,40); color: #ddaaff;
                border: 1px solid rgba(170,80,240,60); border-radius: 12px;
                padding: 6px 20px; font-size: 12px;
            }
            QPushButton:hover { background: rgba(170,80,240,70); }
        """)
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        l.addWidget(btns)

        self._on_provider_changed()

    def _on_provider_changed(self):
        provider = self.cb_provider.currentData()
        info = PROVIDERS.get(provider, {})
        self.le_key.setEnabled(info.get("needs_key", False))
        if not info.get("needs_key", False):
            self.le_key.setPlaceholderText("无需 API Key")
        else:
            self.le_key.setPlaceholderText("请输入 API Key")

        # 预设 API 地址
        base_url = info.get("base_url", "")
        if base_url:
            self.le_url.setText(base_url)

        # llama_proxy 提供商：显示刷新按钮；其他隐藏或弱化
        self._refresh_model_btn.setVisible(provider == "llama_proxy")

    def _discover_models(self):
        """手动触发模型发现"""
        self.lbl_status.setText("正在发现模型...")
        try:
            provider = self.cb_provider.currentData()
            if provider == "llama_proxy":
                models = _discover_local_models()
                self.cb_model.clear()
                if models:
                    for m in models:
                        self.cb_model.addItem(m)
                    self.lbl_status.setText(
                        f'<span style="color:#44cc66;">✓ 发现 {len(models)} 个本地模型</span>'
                    )
                else:
                    self.cb_model.setEditText(self._config.model_name)
                    self.lbl_status.setText(
                        '<span style="color:#ffaa44;">⚠ 未发现本地模型，请确认 llama.cpp 已启动</span>'
                    )
            else:
                # 对其他提供商，尝试通过测试连接获取
                self._test_connection()
        except Exception as e:
            self.lbl_status.setText(f'<span style="color:#ff6644;">✗ {e}</span>')

    def _on_accept(self):
        provider = self.cb_provider.currentData()
        try:
            temp = float(self.le_temp.text())
            max_tokens = int(self.le_max_tokens.text())
        except ValueError:
            QMessageBox.warning(self, "输入错误", "Temperature 和 Max Tokens 需为数字")
            return
        self._config = ModelConfig(
            provider=provider,
            api_key=self.le_key.text().strip(),
            base_url=self.le_url.text().strip(),
            model_name=self.cb_model.currentText().strip(),
            temperature=temp,
            max_tokens=max_tokens,
        )
        self.accept()

    def _test_connection(self):
        provider = self.cb_provider.currentData()
        try:
            temp = float(self.le_temp.text())
            max_tokens = int(self.le_max_tokens.text())
        except ValueError:
            self.lbl_status.setText(
                '<span style="color:#ff6644;">Temperature / Max Tokens 需为数字</span>'
            )
            return

        cfg = ModelConfig(
            provider=provider,
            api_key=self.le_key.text().strip(),
            base_url=self.le_url.text().strip(),
            model_name=self.cb_model.currentText().strip(),
            temperature=temp,
            max_tokens=max_tokens,
        )
        self.lbl_status.setText("测试中...")
        try:
            client = LLMClient(cfg)
            result = client.test_connection()
            if result.get("ok"):
                models = result.get("models", [])
                model_info = f"，可用模型: {', '.join(models[:8])}" if models else ""

                # 自动填充发现模型到下拉框
                if models and provider == "llama_proxy":
                    self.cb_model.clear()
                    for m in models:
                        self.cb_model.addItem(m)

                self.lbl_status.setText(
                    f'<span style="color:#44cc66;">✓ 连接成功{model_info}</span>'
                )
            else:
                self.lbl_status.setText(
                    f'<span style="color:#ff6644;">✗ {result.get("message", "连接失败")}</span>'
                )
        except Exception as e:
            self.lbl_status.setText(f'<span style="color:#ff6644;">✗ {e}</span>')

    def get_config(self) -> ModelConfig:
        return self._config
