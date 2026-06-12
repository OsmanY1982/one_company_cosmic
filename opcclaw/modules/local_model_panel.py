"""
OPCclaw - 本地模型配置面板 (Ollama / LM Studio)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QGroupBox, QMessageBox, QApplication, QPushButton,
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer, QObject
from PyQt5.QtGui import QFont

from ._shared import COLORS, _styled_btn, _styled_input

try:
    from modules.intelligence._model_manager import OllamaManager
    _OLLAMA_MGR = True
except ImportError:
    _OLLAMA_MGR = False


class LocalModelPanel(QWidget):
    """管理本地 LLM (Ollama / LM Studio)"""

    providers_changed = pyqtSignal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._ollama_model_data = {}
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
        ollama_hint = QLabel("Ollama 默认地址: http://localhost:11434/v1")
        ollama_hint.setStyleSheet(f"color: {COLORS['text_light']}; font-size: 12px;")
        ollama_layout.addWidget(ollama_hint)

        ollama_row = QHBoxLayout()
        self.ollama_model = QComboBox()
        self.ollama_model.setEditable(True)
        self.ollama_model.setMinimumWidth(220)
        ollama_row.addWidget(QLabel("模型:"))
        ollama_row.addWidget(self.ollama_model, stretch=1)

        self.ollama_url = QLineEdit("http://localhost:11434/v1")
        self.ollama_url.setMinimumHeight(32)
        ollama_row.addWidget(QLabel("地址:"))
        ollama_row.addWidget(self.ollama_url)

        ollama_btn = _styled_btn("连接", COLORS["success"])
        ollama_btn.setToolTip("添加当前选中的模型为独立本地服务")
        ollama_btn.clicked.connect(self._connect_ollama)
        ollama_row.addWidget(ollama_btn)

        refresh_btn = QPushButton("刷新")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['card']}; color: {COLORS['text']};
                border: 1px solid {COLORS['border']}; border-radius: 6px;
                padding: 6px 10px; font-size: 12px;
            }}
            QPushButton:hover {{ background: {COLORS['primary']}; color: white; }}
        """)
        refresh_btn.clicked.connect(self._refresh_ollama_models)
        ollama_row.addWidget(refresh_btn)
        ollama_layout.addLayout(ollama_row)

        # 一键添加全部
        add_all_btn = QPushButton("一键添加全部模型")
        add_all_btn.setCursor(Qt.PointingHandCursor)
        add_all_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']}; color: white;
                border: none; border-radius: 6px;
                padding: 6px 12px; font-size: 12px;
            }}
            QPushButton:hover {{ opacity: 0.85; }}
        """)
        add_all_btn.clicked.connect(self._add_all_ollama_models)
        ollama_layout.addWidget(add_all_btn)

        layout.addWidget(ollama_group)

        # 动态拉取已安装的模型（异步，不阻塞 UI）
        QTimer(self).singleShot(100, self._refresh_ollama_models)

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

    def _connect_ollama(self):
        self._add_local("Ollama", self.ollama_url.text().strip(),
                        self.ollama_model.currentText().strip())

    def _refresh_ollama_models(self):
        """后台线程拉取 Ollama 已安装模型，填充下拉框（不阻塞 UI）"""
        if not _OLLAMA_MGR:
            self.ollama_model.clear()
            self.ollama_model.addItem("（Ollama 管理模块不可用）")
            return

        self.ollama_model.clear()
        self.ollama_model.addItem("（获取中...）")

        class _FetchWorker(QObject):
            finished = pyqtSignal(list)  # list of (display_text, model_name)

            def run(self):
                results = []
                try:
                    if not OllamaManager.is_running():
                        results.append(("（Ollama 未启动）", ""))
                        self.finished.emit(results)
                        return
                    models = OllamaManager.list_models()
                    if not models:
                        results.append(("（无已安装模型，请先 pull）", ""))
                        self.finished.emit(results)
                        return
                    for m in models:
                        name = m.get("name", "")
                        size = m.get("size", 0)
                        size_str = f" ({size / 1024 / 1024 / 1024:.1f}GB)" if size else ""
                        results.append((f"{name}{size_str}", name))
                except Exception as e:
                    results.append((f"（获取失败: {e}）", ""))
                finally:
                    self.finished.emit(results)

        self._ollama_fetch_thread = QThread()
        self._ollama_fetch_worker = _FetchWorker()
        self._ollama_fetch_worker.moveToThread(self._ollama_fetch_thread)
        self._ollama_fetch_thread.started.connect(self._ollama_fetch_worker.run)
        self._ollama_fetch_worker.finished.connect(self._on_ollama_models_ready)
        self._ollama_fetch_worker.finished.connect(self._ollama_fetch_thread.quit)
        self._ollama_fetch_thread.finished.connect(self._ollama_fetch_thread.deleteLater)
        self._ollama_fetch_worker.finished.connect(self._ollama_fetch_worker.deleteLater)
        self._ollama_fetch_thread.start()

    def _on_ollama_models_ready(self, results: list):
        """后台拉取完成后填入下拉框"""
        self.ollama_model.clear()
        self._ollama_model_data = {}  # display_text -> model_name
        for display_text, model_name in results:
            self.ollama_model.addItem(display_text, model_name)
            self._ollama_model_data[display_text] = model_name

    def _add_all_ollama_models(self):
        """一键将全部已安装的 Ollama 模型添加为独立本地服务"""
        if not _OLLAMA_MGR:
            QMessageBox.warning(self, "不可用", "Ollama 管理模块不可用")
            return

        base_url = self.ollama_url.text().strip()
        model_names = []
        for i in range(self.ollama_model.count()):
            name = self.ollama_model.itemData(i)
            if name and "（" not in str(name):
                model_names.append(name)

        if not model_names:
            QMessageBox.warning(self, "提示", "未检测到已安装的模型，请先刷新")
            return

        added = 0
        for model_name in model_names:
            pid = "ollama_" + model_name.replace(":", "_").replace("-", "_").replace(".", "_")
            self.config.add_provider("local", pid, {
                "name": f"Ollama-{model_name}",
                "provider_type": "openai_compatible",
                "base_url": base_url,
                "api_key": "local",
                "model": model_name,
            })
            added += 1

        self._refresh()
        self.providers_changed.emit()
        QMessageBox.information(self, "完成", f"已添加 {added} 个模型作为本地服务\n请在下方列表双击切换到想要使用的模型")

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
