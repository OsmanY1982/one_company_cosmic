# -*- coding: utf-8 -*-
"""
会话服务模块 — SessionService
管理用户登录会话的生命周期：创建/验证/失效/清理。
依赖 SessionDAO（数据层）和 AuthService（认证校验）。
"""
import uuid
import logging
from datetime import datetime

from modules.auth.dao.session_dao import SessionDAO, SESSION_EXPIRE_DAYS

logger = logging.getLogger(__name__)


class SessionService:
    """会话管理服务：单例模式，跨模块通过 module_manager.get_service('session') 获取。"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self._dao = SessionDAO()

    # ── 会话生命周期 ──

    def create_session(self, username: str, device_id: str = None,
                       device_type: str = "desktop",
                       ip_address: str = "") -> dict:
        """创建新会话，返回包含 session_token 的会话信息。"""
        if not username:
            return {"ok": False, "msg": "用户名不能为空", "session": None}

        if not device_id:
            device_id = f"{username}-{uuid.uuid4().hex[:8]}"

        session_token = uuid.uuid4().hex
        ok = self._dao.create_session(
            username=username,
            device_id=device_id,
            session_token=session_token,
            device_type=device_type,
            ip_address=ip_address,
        )
        if not ok:
            return {"ok": False, "msg": "会话创建失败", "session": None}

        self._dao.log_session_event(username, "login", device_id, ip_address)

        return {
            "ok": True,
            "msg": "会话创建成功",
            "session": {
                "username": username,
                "device_id": device_id,
                "session_token": session_token,
                "device_type": device_type,
            }
        }

    def validate_session(self, username: str, session_token: str,
                         device_id: str = None) -> dict:
        """验证会话是否有效，自动续期。"""
        if not username or not session_token:
            return {"ok": False, "msg": "参数不完整"}

        session = None
        if device_id:
            session = self._dao.get_session(username, device_id)
        else:
            sessions = self._dao.get_user_sessions(username)
            for s in sessions:
                if s.get("session_token") == session_token:
                    session = s
                    break

        if not session:
            return {"ok": False, "msg": "会话不存在或已失效"}

        if session.get("status") != "active":
            return {"ok": False, "msg": "会话已过期"}

        # 续期
        self._dao.update_activity(username, session["device_id"])

        return {"ok": True, "msg": "会话有效", "session": session}

    def invalidate_session(self, username: str, device_id: str = None) -> dict:
        """失效指定会话（device_id 为空则失效该用户全部会话）。"""
        count = self._dao.invalidate_session(username, device_id)
        self._dao.log_session_event(
            username, "logout",
            device_id=device_id or "",
        )
        return {"ok": True, "msg": f"已失效 {count} 个会话", "count": count}

    def get_active_sessions(self, username: str) -> list:
        """获取用户所有活跃会话列表。"""
        return self._dao.get_user_sessions(username)

    def cleanup_expired(self) -> dict:
        """清理过期会话。"""
        count = self._dao.cleanup_expired_sessions()
        return {"ok": True, "msg": f"已清理 {count} 个过期会话", "count": count}

    def get_session_count(self, username: str = None) -> int:
        """获取活跃会话数。"""
        if username:
            return len(self._dao.get_user_sessions(username))
        return 0  # 按需扩展全量统计
