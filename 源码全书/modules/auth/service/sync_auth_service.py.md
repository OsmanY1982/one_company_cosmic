# `modules/auth/service/sync_auth_service.py`

> 路径：`modules/auth/service/sync_auth_service.py` | 行数：152


---


```python
# -*- coding: utf-8 -*-
"""
认证同步服务 — SyncAuthService
统一三端同步通道：管理员增删用户 → 本地 JSON/SQLite → 云端 Supabase → 其他客户端拉取。

职责：
1. 管理员增删用户后触发三端同步
2. admin.json / admin.db 配置同步
3. 权限变更同步触发
"""
import os
import json
import sqlite3
import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from core.paths import DATA_DIR, CONFIG_DIR
except ImportError:
    BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    DATA_DIR = os.path.join(BASE, "data")
    CONFIG_DIR = os.path.join(BASE, "config")


class SyncAuthService:
    """认证同步服务：静态方法集合，供 AuthService / UserDAO / PermissionService 调用。"""

    @staticmethod
    def sync_user_to_cloud(username: str, user_data: dict = None):
        """将单个用户数据同步到云端。"""
        try:
            from core.cloud_sync import sync_users
            t = threading.Thread(target=sync_users, daemon=True)
            t.start()
            return True
        except Exception as e:
            logger.error(f"同步用户到云端失败: {e}")
            return False

    @staticmethod
    def sync_all_auth_tables():
        """同步全部认证相关表到云端。"""
        try:
            from core.cloud_sync import sync_all
            t = threading.Thread(target=sync_all, daemon=True)
            t.start()
            return True
        except Exception as e:
            logger.error(f"全量同步失败: {e}")
            return False

    @staticmethod
    def _init_admin_db():
        """初始化 admin.db（管理员配置数据库），用于云端同步桥接。"""
        admin_db = os.path.join(DATA_DIR, "admin.db")
        admin_json = os.path.join(CONFIG_DIR, "admin.json")

        os.makedirs(os.path.dirname(admin_db), exist_ok=True)

        # 从 admin.json 读取现有管理员列表
        admins = []
        if os.path.exists(admin_json):
            try:
                with open(admin_json, "r", encoding="utf-8") as f:
                    admins = json.load(f)
                    if not isinstance(admins, list):
                        admins = []
            except (json.JSONDecodeError, IOError):
                admins = []

        # 确保至少包含默认 admin
        has_admin = any(
            isinstance(a, dict) and a.get("username") == "admin" for a in admins
        )
        if not has_admin:
            admins.insert(0, {"username": "admin", "role": "admin", "active": True})

        conn = sqlite3.connect(admin_db)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS admin_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                role TEXT DEFAULT 'admin',
                active INTEGER DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for admin in admins:
            if isinstance(admin, dict):
                c.execute('''
                    INSERT OR REPLACE INTO admin_config
                    (username, role, active, created_at, updated_at)
                    VALUES (?,?,?,COALESCE((SELECT created_at FROM admin_config WHERE username=?),?),?)
                ''', (
                    admin.get("username", ""),
                    admin.get("role", "admin"),
                    1 if admin.get("active", True) else 0,
                    admin.get("username", ""),
                    now,
                    now,
                ))
        conn.commit()
        conn.close()

        # 回写 admin.json（双向同步）
        with open(admin_json, "w", encoding="utf-8") as f:
            json.dump(admins, f, ensure_ascii=False, indent=2)

        return True

    @staticmethod
    def sync_admin_config():
        """管理员配置同步：admin.json → admin.db → cloud_sync。"""
        SyncAuthService._init_admin_db()
        try:
            from core.cloud_sync import sync_admin_config
            t = threading.Thread(target=sync_admin_config, daemon=True)
            t.start()
            return True
        except Exception as e:
            logger.error(f"管理员配置同步失败: {e}")
            return False

    @staticmethod
    def trigger_permission_sync(username: str = None):
        """权限变更后触发三端同步。"""
        try:
            SyncAuthService.sync_user_to_cloud(username)
            SyncAuthService.sync_admin_config()
            return True
        except Exception as e:
            logger.error(f"权限同步触发失败: {e}")
            return False

    @staticmethod
    def trigger_full_sync(username: str = None):
        """用户增删后全量同步：先更新本地桥接，再推云端。"""
        SyncAuthService._init_admin_db()
        try:
            from core.cloud_sync import sync_all
            t = threading.Thread(target=sync_all, daemon=True)
            t.start()
            return True
        except Exception as e:
            logger.error(f"全量同步触发失败: {e}")
            return False

```
