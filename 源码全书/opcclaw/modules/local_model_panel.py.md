# `opcclaw/modules/local_model_panel.py`

> 路径：`opcclaw/modules/local_model_panel.py` | 行数：259


---


```python
"""
OPCclaw - 本地模型配置面板 (Ollama / LM Studio)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QGroupBox, QMessageBox, QApplication,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ._shared import COLORS, _styled_btn, _styled_input


class LocalModelPanel(QWidget):
    """管理本地 LLM (Ollama / LM Studio)"""

    providers_changed = pyqtSignal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("🖥️ 本地模型管理")
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text']};")
        layout.addWidget(title)

        desc = QLabel("连接本地大模型 (Ollama / LM Studio / vLLM)\n无需联网, 数据安全, 零成本")
        desc.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 13px; line-height: 1.5;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(8)

        # 当前活跃状态
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # 快捷添加: Ollama
        ollama_group = QGroupBox("Ollama (推荐)")
        ollama_layout = QVBoxLayout(ollama_group)
        ollama_hint = QLabel("llama.cpp 默认地址: http://localhost:8080/v1")
        ollama_hint.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        ollama_layout.addWidget(ollama_hint)

        ollama_row = QHBoxLayout()
        self.ollama_model = QComboBox()
        self.ollama_model.setEditable(True)
        self.ollama_model.setMinimumWidth(200)
        ollama_row.addWidget(QLabel("模型:"))
        ollama_row.addWidget(self.ollama_model, stretch=1)

        self.ollama_url = QLineEdit("http://localhost:8080/v1")
        self.ollama_url.setMinimumHeight(32)
        ollama_row.addWidget(QLabel("地址:"))
        ollama_row.addWidget(self.ollama_url)

        refresh_ollama_btn = _styled_btn("刷新", COLORS["primary"])
        refresh_ollama_btn.clicked.connect(self._refresh_ollama_models)
        ollama_row.addWidget(refresh_ollama_btn)

        ollama_btn = _styled_btn("连接 Ollama", COLORS["success"])
        ollama_btn.clicked.connect(self._connect_ollama)
        ollama_row.addWidget(ollama_btn)
        ollama_layout.addLayout(ollama_row)
        layout.addWidget(ollama_group)

        # 快捷添加: LM Studio
        lm_group = QGroupBox("LM Studio")
        lm_layout = QVBoxLayout(lm_group)
        lm_hint = QLabel("LM Studio 默认地址: http://localhost:1234/v1")
        lm_hint.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        lm_layout.addWidget(lm_hint)

        lm_row = QHBoxLayout()
        self.lm_model = QComboBox()
        self.lm_model.setEditable(True)
        self.lm_model.addItems(["local-model", "qwen2.5", "deepseek-r1-distill-qwen"])
        self.lm_model.setMinimumWidth(200)
        lm_row.addWidget(QLabel("模型:"))
        lm_row.addWidget(self.lm_model, stretch=1)

        self.lm_url = QLineEdit("http://localhost:1234/v1")
        self.lm_url.setMinimumHeight(32)
        lm_row.addWidget(QLabel("地址:"))
        lm_row.addWidget(self.lm_url)

        lm_btn = _styled_btn("连接 LM Studio", COLORS["success"])
        lm_btn.clicked.connect(self._connect_lm_studio)
        lm_row.addWidget(lm_btn)
        lm_layout.addLayout(lm_row)
        layout.addWidget(lm_group)

        # 自定义
        custom_group = QGroupBox("自定义本地服务")
        custom_layout = QFormLayout(custom_group)
        custom_name = _styled_input("服务名称 (如: vLLM, text-gen-webui)")
        custom_url = _styled_input("服务地址 (如: http://localhost:8000/v1)")
        custom_model = _styled_input("模型名称")
        custom_layout.addRow("名称:", custom_name)
        custom_layout.addRow("地址:", custom_url)
        custom_layout.addRow("模型:", custom_model)

        custom_btn = _styled_btn("添加自定义服务", COLORS["primary"])
        custom_btn.clicked.connect(lambda: self._add_custom(
            custom_name.text(), custom_url.text(), custom_model.text()
        ))
        custom_layout.addRow("", custom_btn)
        layout.addWidget(custom_group)

        # 已连接的本地服务列表
        self.provider_list = QListWidget()
        self.provider_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                background: {COLORS['card']};
                font-size: 13px;
            }}
            QListWidget::item {{ padding: 10px 14px; border-bottom: 1px solid {COLORS['border']}; }}
            QListWidget::item:selected {{ background: {COLORS['primary']}; color: white; }}
        """)
        self.provider_list.itemDoubleClicked.connect(self._use_local_selected)
        layout.addWidget(self.provider_list, stretch=1)

        btn_row = QHBoxLayout()
        use_btn = _styled_btn("设为活跃", COLORS["primary"])
        use_btn.clicked.connect(self._use_local_selected)
        btn_row.addWidget(use_btn)
        del_btn = _styled_btn("删除", COLORS["danger"])
        del_btn.clicked.connect(self._delete_local_selected)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.custom_name = custom_name
        self.custom_url = custom_url
        self.custom_model = custom_model
        self._refresh()
        # 初始化时自动从 Ollama 拉取已安装模型列表
        self._refresh_ollama_models()

    def _connect_ollama(self):
        self._add_local("Ollama", self.ollama_url.text().strip(),
                        self.ollama_model.currentText().strip())

    def _connect_lm_studio(self):
        self._add_local("LM Studio", self.lm_url.text().strip(),
                        self.lm_model.currentText().strip())

    def _add_custom(self, name: str, url: str, model: str):
        if not name or not url:
            QMessageBox.warning(self, "提示", "请填写名称和地址")
            return
        self._add_local(name, url, model)

    def _add_local(self, name: str, url: str, model: str):
        from opcclaw.core.llm_backend import BackendFactory, ProviderConfig

        try:
            cfg = ProviderConfig(
                name=name, provider_type="openai_compatible",
                base_url=url, api_key="local", model=model,
            )
            backend = BackendFactory.create(cfg)
            resp = backend.chat([{"role": "user", "content": "hi"}])
            QMessageBox.information(self, "连接成功", f"{name} 已连接!\n模型: {resp.model}")
        except Exception as e:
            QMessageBox.warning(self, "连接失败",
                               f"无法连接到 {name}: {e}\n请确保服务已启动。")
            return

        pid = name.lower().replace(" ", "_")
        self.config.add_provider("local", pid, {
            "name": name, "provider_type": "openai_compatible",
            "base_url": url, "api_key": "local", "model": model,
        })
        self._refresh()
        self.providers_changed.emit()

    def _refresh(self):
        self.provider_list.clear()
        providers = self.config.list_providers("local")
        active_id = self.config._data["active_provider_id"]
        active_type = self.config._data["active_provider_type"]

        for pid, pdata in providers.items():
            name = pdata.get("name", pid)
            model = pdata.get("model", "")
            url = pdata.get("base_url", "")
            active_mark = " ★" if (active_type == "local" and active_id == pid) else ""
            item = QListWidgetItem(f"{name}{active_mark}  |  {model}  |  {url}")
            item.setData(Qt.UserRole, pid)
            self.provider_list.addItem(item)

        if active_type == "local" and active_id:
            active_p = providers.get(active_id, {})
            self.status_label.setText(
                f"当前活跃: {active_p.get('name', active_id)} "
                f"({active_p.get('model', '')}) [本地]"
            )
            self.status_label.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold; font-size: 13px;")
        else:
            self.status_label.setText("ℹ️ 未使用本地模型, 可在此配置")

    def _use_local_selected(self):
        item = self.provider_list.currentItem()
        if not item:
            return
        pid = item.data(Qt.UserRole)
        self.config.set_active_provider(pid, "local")
        self._refresh()
        self.providers_changed.emit()

    def _delete_local_selected(self):
        item = self.provider_list.currentItem()
        if not item:
            return
        pid = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "确认", f"确定要删除 \"{pid}\" 吗?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.config.remove_provider("local", pid)
            self._refresh()
            self.providers_changed.emit()

    def _refresh_ollama_models(self):
        """从 Ollama API 动态获取已安装的模型列表"""
        import urllib.request
        import json

        current_text = self.ollama_model.currentText()
        self.ollama_model.clear()

        try:
            url = "http://localhost:8080/v1/models"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                models = [m["id"] for m in data.get("data", [])]
            if models:
                self.ollama_model.addItems(models)
                idx = self.ollama_model.findText(current_text)
                if idx >= 0:
                    self.ollama_model.setCurrentIndex(idx)
            else:
                self.ollama_model.addItem("(未找到模型)")
        except Exception:
            self.ollama_model.addItem("(llama.cpp 未运行)")

```
