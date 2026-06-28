# `core/module_manager.py`

> 路径：`core/module_manager.py` | 行数：139


---


```python
# -*- coding: utf-8 -*-

from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
from typing import Dict, Optional
from PyQt5.QtWidgets import QMessageBox
from core.event_bus import event_bus
from core.app_state import app_state

PROTECTED_MODULES = {
    "cloud_server": "cloud",
    "admin": "admin",
    "activation": "activation",
    "report": "report",
    "base_info": "base_info",
    "auth": "admin",  # 认证管理仅限管理员
}


class ModuleInfo:
    def __init__(self, module_id, name, icon=None):
        self.module_id = module_id
        self.name = name
        self.icon = icon
        self.window_class = None
        self.instance = None


class ModuleManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self._modules: Dict[str, ModuleInfo] = {}
        self._services: Dict[str, object] = {}  # 注册的服务实例
        self._project_root = BASE_DIR
        self._current_window = None  # 当前显示的窗口
        self._register_auth_services()

    def register_module(self, module_id, name, import_path, class_name, icon=None):
        info = ModuleInfo(module_id, name, icon)
        try:
            module = __import__(import_path, fromlist=[class_name])
            info.window_class = getattr(module, class_name)
        except Exception as e:
            print(f"注册模块失败: {module_id} - {e}")
            return
        self._modules[module_id] = info
        print(f"模块已注册: {module_id} - {name}")

    def get_module(self, module_id):
        return self._modules.get(module_id)

    def list_modules(self):
        return self._modules.copy()

    def create_window(self, module_id, parent=None):
        info = self._modules.get(module_id)
        if not info:
            print(f"模块不存在: {module_id}")
            return None
        try:
            window = info.window_class(parent=parent)
            info.instance = window
            return window
        except Exception as e:
            print(f"创建窗口失败: {module_id} - {e}")
            return None

    def switch_module(self, module_id, parent=None):
        # 权限检查
        required = PROTECTED_MODULES.get(module_id)
        if required:
            if not app_state.is_admin():
                msg = f"该模块仅限管理员使用"
                if parent:
                    QMessageBox.warning(parent, "权限不足", msg)
                else:
                    QMessageBox.warning(None, "权限不足", msg)
                return None

        # 关掉当前窗口
        if self._current_window:
            self._current_window.close()
            self._current_window = None

        # 创建新窗口
        window = self.create_window(module_id, parent)
        if window:
            self._current_window = window
            app_state.current_module = module_id
            event_bus.module_switched.emit(module_id)
            window.show()

        return window

    def register_service(self, service_id: str, import_path: str, class_name: str):
        """注册非 UI 服务模块（如 AuthService / SessionService 等）。
        服务通过 service_id 索引，跨模块可通过 module_manager.get_service() 获取。
        """
        try:
            module = __import__(import_path, fromlist=[class_name])
            service_cls = getattr(module, class_name)
            self._services[service_id] = service_cls
            print(f"服务已注册: {service_id} → {import_path}.{class_name}")
        except Exception as e:
            print(f"注册服务失败: {service_id} - {e}")

    def get_service(self, service_id: str):
        """获取已注册的服务类（非实例）。
        调用方自行实例化：module_manager.get_service('auth')( )
        """
        return self._services.get(service_id)

    def list_services(self):
        return self._services.copy()

    def _register_auth_services(self):
        """注册认证相关服务到模块管理器"""
        # AuthService — 核心认证服务
        self.register_service("auth", "modules.auth.auth_service", "AuthService")
        # SessionService 和 SyncAuthService 如存在则注册
        try:
            self.register_service("session", "modules.auth.service.session_service", "SessionService")
        except Exception:
            pass  # SessionService 可选
        try:
            self.register_service("sync_auth", "modules.auth.service.sync_auth_service", "SyncAuthService")
        except Exception:
            pass  # SyncAuthService 可选


module_manager = ModuleManager()

```
