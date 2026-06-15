"""
OPCclaw 配置管理器
管理 OPCclaw 全部配置: 云端模型 + 本地模型 + 技能状态 + 通用设置

安全特性:
- API Key 使用 Windows DPAPI 加密存储，不保存在明文 config.json 中
- 加密文件绑定当前 Windows 用户账户
"""

import os
import json
import secrets
import string
from typing import Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QHBoxLayout, QApplication
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from opcclaw.core.llm_backend import ProviderConfig
from opcclaw.core.opcclaw_logging import logger

from ._shared import COLORS, _styled_btn, _styled_input


class ConfigManager:
    """管理 OPCclaw 全部配置: 云端模型 + 本地模型 + 技能状态 + 通用设置

    安全特性:
    - API Key 使用 Windows DPAPI 加密存储，不保存在明文 config.json 中
    - 加密文件绑定当前 Windows 用户账户
    """

    def _force_set_admin_password(self):
        """首次运行时自动生成管理员密码（仅显示一次）"""
        storage = SecureStorage()
        if storage.is_admin_configured():
            return  # 已设置，无需初始化

        # 自动生成随机 16 位密码
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(chars) for _ in range(16))
        storage.set_admin_password(password)

        dlg = QDialog(self)
        dlg.setWindowTitle("管理员密码已生成")
        dlg.setFixedSize(420, 320)
        dlg.setModal(True)

        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)

        info = QLabel("你的管理员密码已自动生成\\n仅显示一次，请立即保存！")
        info.setWordWrap(True)
        info.setStyleSheet("font-size: 13px; padding: 8px; color: #e67e22; font-weight: bold;")
        layout.addWidget(info)

        pwd_display = QLineEdit(password)
        pwd_display.setReadOnly(True)
        pwd_display.setAlignment(Qt.AlignCenter)
        pwd_display.setStyleSheet("""
            QLineEdit {
                font-size: 20px;
                font-family: 'Consolas', 'Courier New', monospace;
                letter-spacing: 2px;
                padding: 12px;
                background: #2c3e50;
                color: #2ecc71;
                border: 2px solid #2ecc71;
                border-radius: 6px;
            }
        """)
        pwd_display.setMinimumHeight(50)
        layout.addWidget(pwd_display)

        btn_row = QHBoxLayout()

        copy_btn = QPushButton("复制密码")
        copy_btn.setMinimumHeight(38)
        copy_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover { background: #2980b9; }
        """)
        def do_copy():
            QApplication.clipboard().setText(password)
            copy_btn.setText(" 已复制")
        copy_btn.clicked.connect(do_copy)
        btn_row.addWidget(copy_btn)

        ok_btn = QPushButton("我已保存")
        ok_btn.setMinimumHeight(38)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background: #2980b9; }
        """)
        ok_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(ok_btn)

        layout.addLayout(btn_row)

        hint = QLabel("密码使用 Windows 加密存储，不会保存在代码中\\n可随时在设置中修改密码")
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size: 11px; color: #7f8c8d; padding: 4px;")
        layout.addWidget(hint)

        dlg.exec_()

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.config_path = os.path.join(data_dir, "opcclaw_config.json")
        self._data = self._load_defaults()
        self._secure = self._init_secure_storage()
        self._load()

    def _load_defaults(self) -> dict:
        return {
            "active_provider_id": "",
            "active_provider_type": "cloud",  # "cloud" | "local"
            "cloud_providers": {},
            "local_providers": {},
            "disabled_skills": [],
            "general": {
                "theme": "light",
                "auto_save": True,
                "max_tool_rounds": 5,
                "font_size": 14,
            },
        }

    def _init_secure_storage(self):
        """初始化安全存储（延迟导入避免循环依赖）"""
        try:
            import sys
            core_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core")
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)
            from secure_storage import SecureStorage
            return SecureStorage(app_name="opcclaw")
        except Exception as e:
            logger.error(f"[ConfigManager] 安全存储初始化失败: {e}")
            return None

    def _load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data.update(saved)
                # 从安全存储恢复 API Key
                self._restore_api_keys()
            except Exception:
                pass
    
    def _restore_api_keys(self):
        """从安全存储恢复 API Key 到内存配置"""
        if not self._secure:
            return
        try:
            for ptype in ["cloud", "local"]:
                providers = self._data.get(f"{ptype}_providers", {})
                for pid, config in providers.items():
                    if not config.get("api_key"):
                        # 尝试从安全存储读取
                        secure_key = self._secure.load_api_key(f"{ptype}:{pid}")
                        if secure_key:
                            config["api_key"] = secure_key
                            logger.info(f"[ConfigManager] 已恢复 {ptype}:{pid} 的 API Key")
        except Exception as e:
            logger.error(f"[ConfigManager] 恢复 API Key 失败: {e}")
    
    def _secure_save_keys(self):
        """将 API Key 保存到安全存储，config.json 中留空"""
        if not self._secure:
            return
        try:
            for ptype in ["cloud", "local"]:
                providers = self._data.get(f"{ptype}_providers", {})
                for pid, config in providers.items():
                    key = config.get("api_key", "").strip()
                    if key:
                        # 保存到安全存储
                        self._secure.save_api_key(f"{ptype}:{pid}", key)
                        # 清空明文 config 中的 key
                        config["api_key"] = ""
                        logger.info(f"[ConfigManager] 已加密保存 {ptype}:{pid} 的 API Key")
        except Exception as e:
            logger.error(f"[ConfigManager] 加密保存失败: {e}")

    def save(self):
        os.makedirs(self.data_dir, exist_ok=True)
        # 先加密保存 API Key
        self._secure_save_keys()
        # 再保存明文配置（此时 api_key 已被清空）
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
        # 保存后恢复内存中的 Key（不影响运行）
        self._restore_api_keys()

    def get_active_provider(self) -> Optional[ProviderConfig]:
        pid = self._data["active_provider_id"]
        ptype = self._data["active_provider_type"]
        providers = self._data.get(f"{ptype}_providers", {})
        if pid and pid in providers:
            return ProviderConfig(**providers[pid])
        return None

    def set_active_provider(self, pid: str, ptype: str):
        self._data["active_provider_id"] = pid
        self._data["active_provider_type"] = ptype
        self.save()

    def add_provider(self, ptype: str, pid: str, config: dict):
        self._data[f"{ptype}_providers"][pid] = config
        self.save()

    def remove_provider(self, ptype: str, pid: str):
        providers = self._data[f"{ptype}_providers"]
        if pid in providers:
            del providers[pid]
            if self._data["active_provider_id"] == pid:
                self._data["active_provider_id"] = ""
            self.save()

    def list_providers(self, ptype: str) -> dict:
        return self._data.get(f"{ptype}_providers", {})

    def toggle_skill(self, skill_name: str, disabled: bool):
        if disabled:
            if skill_name not in self._data["disabled_skills"]:
                self._data["disabled_skills"].append(skill_name)
        else:
            if skill_name in self._data["disabled_skills"]:
                self._data["disabled_skills"].remove(skill_name)
        self.save()

    def is_skill_disabled(self, skill_name: str) -> bool:
        return skill_name in self._data["disabled_skills"]

    def get_general(self, key: str, default=None):
        return self._data["general"].get(key, default)

    def set_general(self, key: str, value):
        self._data["general"][key] = value
        self.save()
