# -*- coding: utf-8 -*-
"""
Supabase 认证增强模块 — sessions / permissions / admin_config 云端 CRUD

为三端同步提供认证相关表的云端侧 API。
直接复用 core.supabase_client 中的 _request() 基础设施。
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from core.supabase_client import _request, SUPABASE_URL, SUPABASE_SERVICE_KEY

# ══════════════════════════════════════════════════════
#  CloudAuthSessions — 会话表云端 CRUD
# ══════════════════════════════════════════════════════


class CloudAuthSessions:
    """sessions 表云端管理：用户登录会话记录"""

    TABLE = "sessions"

    @classmethod
    def upsert(cls, username: str, device_id: str,
               session_token: str, device_type: str = "desktop",
               ip_address: str = "", status: str = "active") -> tuple:
        """创建或更新会话记录（upsert by username+device_id）"""
        payload = {
            "username": username,
            "device_id": device_id,
            "session_token": session_token,
            "device_type": device_type,
            "ip_address": ip_address,
            "status": status,
            "last_active_at": datetime.now().isoformat(),
        }
        ok, result = _request(
            "POST",
            f"/rest/v1/{cls.TABLE}",
            payload,
            service_key=True,
            prefer="resolution=merge-duplicates",
        )
        if not ok:
            return False, str(result)
        return True, "会话已同步云端"

    @classmethod
    def get_active(cls, username: str) -> tuple:
        """获取用户当前活跃会话列表"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?username=eq.{username}"
            f"&status=eq.active&order=last_active_at.desc",
            service_key=True,
        )
        if not ok:
            return False, []
        return True, result if isinstance(result, list) else []

    @classmethod
    def invalidate(cls, username: str, device_id: str = None) -> tuple:
        """使会话失效（logout / 被踢）"""
        if device_id:
            ok, result = _request(
                "PATCH",
                f"/rest/v1/{cls.TABLE}?username=eq.{username}"
                f"&device_id=eq.{device_id}",
                {"status": "inactive"},
                service_key=True,
            )
        else:
            ok, result = _request(
                "PATCH",
                f"/rest/v1/{cls.TABLE}?username=eq.{username}",
                {"status": "inactive"},
                service_key=True,
            )
        return ok, "会话已失效" if ok else str(result)

    @classmethod
    def delete_user_sessions(cls, username: str) -> tuple:
        """删除用户所有会话记录"""
        ok, result = _request(
            "DELETE",
            f"/rest/v1/{cls.TABLE}?username=eq.{username}",
            service_key=True,
        )
        return ok, "已清除" if ok else str(result)

    @classmethod
    def get_all(cls, limit: int = 200) -> tuple:
        """获取最近会话列表"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?order=last_active_at.desc&limit={limit}",
            service_key=True,
        )
        if not ok:
            return False, []
        return True, result if isinstance(result, list) else []

    @classmethod
    def heartbeat(cls, username: str, device_id: str) -> tuple:
        """更新会话心跳时间"""
        ok, result = _request(
            "PATCH",
            f"/rest/v1/{cls.TABLE}?username=eq.{username}"
            f"&device_id=eq.{device_id}",
            {"last_active_at": datetime.now().isoformat()},
            service_key=True,
        )
        return ok, "心跳已更新" if ok else str(result)


# ══════════════════════════════════════════════════════
#  CloudAuthPermissions — 权限表云端 CRUD
# ══════════════════════════════════════════════════════


class CloudAuthPermissions:
    """permissions 表云端管理：角色权限配置"""

    TABLE = "permissions"

    @classmethod
    def upsert(cls, role: str, module: str,
               can_read: bool = True, can_write: bool = False,
               can_delete: bool = False, can_export: bool = False) -> tuple:
        """创建或更新角色模块权限（upsert by role+module）"""
        payload = {
            "role": role,
            "module": module,
            "can_read": can_read,
            "can_write": can_write,
            "can_delete": can_delete,
            "can_export": can_export,
            "updated_at": datetime.now().isoformat(),
        }
        ok, result = _request(
            "POST",
            f"/rest/v1/{cls.TABLE}",
            payload,
            service_key=True,
            prefer="resolution=merge-duplicates",
        )
        if not ok:
            return False, str(result)
        return True, "权限已同步云端"

    @classmethod
    def get_role_permissions(cls, role: str) -> tuple:
        """获取指定角色的所有模块权限"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?role=eq.{role}&select=*",
            service_key=True,
        )
        if not ok:
            return False, []
        return True, result if isinstance(result, list) else []

    @classmethod
    def get_module_access(cls, module: str, role: str) -> tuple:
        """检查某角色对某模块是否有读权限"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?module=eq.{module}"
            f"&role=eq.{role}&can_read=eq.true&select=id&limit=1",
            service_key=True,
        )
        if not ok:
            return False, False
        has_access = isinstance(result, list) and len(result) > 0
        return True, has_access

    @classmethod
    def batch_upsert(cls, entries: list[dict]) -> dict:
        """批量同步权限条目，返回 {success_count, fail_count}"""
        success = fail = 0
        for e in entries:
            ok, _ = cls.upsert(
                role=e["role"],
                module=e["module"],
                can_read=e.get("can_read", True),
                can_write=e.get("can_write", False),
                can_delete=e.get("can_delete", False),
                can_export=e.get("can_export", False),
            )
            if ok:
                success += 1
            else:
                fail += 1
        return {"success": success, "fail": fail}

    @classmethod
    def delete_role(cls, role: str) -> tuple:
        """删除某角色的所有权限条目"""
        ok, result = _request(
            "DELETE",
            f"/rest/v1/{cls.TABLE}?role=eq.{role}",
            service_key=True,
        )
        return ok, "已清除" if ok else str(result)

    @classmethod
    def get_all(cls, limit: int = 500) -> tuple:
        """获取所有权限配置"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?order=role.asc,module.asc&limit={limit}",
            service_key=True,
        )
        if not ok:
            return False, []
        return True, result if isinstance(result, list) else []


# ══════════════════════════════════════════════════════
#  CloudAuthAdminConfig — 管理配置表云端 CRUD
# ══════════════════════════════════════════════════════


class CloudAuthAdminConfig:
    """admin_config 表云端管理：管理员配置键值对"""

    TABLE = "admin_config"

    @classmethod
    def set(cls, key: str, value: str, updated_by: str = "system") -> tuple:
        """设置配置项（upsert by key）"""
        payload = {
            "key": key,
            "value": value,
            "updated_by": updated_by,
            "updated_at": datetime.now().isoformat(),
        }
        ok, result = _request(
            "POST",
            f"/rest/v1/{cls.TABLE}",
            payload,
            service_key=True,
            prefer="resolution=merge-duplicates",
        )
        if not ok:
            return False, str(result)
        return True, "配置已同步云端"

    @classmethod
    def get(cls, key: str) -> tuple:
        """获取单个配置项"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?key=eq.{key}&select=*&limit=1",
            service_key=True,
        )
        if not ok or not isinstance(result, list) or len(result) == 0:
            return False, None
        return True, result[0]

    @classmethod
    def get_all(cls, limit: int = 200) -> tuple:
        """获取所有配置项"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?order=key.asc&limit={limit}",
            service_key=True,
        )
        if not ok:
            return False, []
        return True, result if isinstance(result, list) else []

    @classmethod
    def delete(cls, key: str) -> tuple:
        """删除配置项"""
        ok, result = _request(
            "DELETE",
            f"/rest/v1/{cls.TABLE}?key=eq.{key}",
            service_key=True,
        )
        return ok, "已删除" if ok else str(result)

    @classmethod
    def batch_set(cls, entries: list[dict], updated_by: str = "system") -> dict:
        """批量设置配置项，返回 {success_count, fail_count}"""
        success = fail = 0
        for e in entries:
            ok, _ = cls.set(
                key=e["key"],
                value=e["value"],
                updated_by=e.get("updated_by", updated_by),
            )
            if ok:
                success += 1
            else:
                fail += 1
        return {"success": success, "fail": fail}

    @classmethod
    def sync_admin_config(cls, config_dict: dict, updated_by: str = "admin") -> dict:
        """将完整的 admin 配置字典同步到云端"""
        entries = [
            {"key": k, "value": str(v), "updated_by": updated_by}
            for k, v in config_dict.items()
        ]
        return cls.batch_set(entries, updated_by)
