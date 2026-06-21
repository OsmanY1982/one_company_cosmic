"""
认证服务模块 — 用户注册/登录/会员管理
数据持久化到 modules/auth/users.json + data/users.db (SQLite)
注册时双写：JSON（本地登录） + SQLite（云端同步）
登录时双读：JSON 优先，SQLite 兜底（跨机注册用户）
"""
import traceback
import json
import os
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Optional

from core.operation_log import log_action

USER_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
ACTIVATION_DB = os.path.join(DATA_DIR, "activation.db")
USERS_SQLITE_DB = os.path.join(DATA_DIR, "users.db")

# ── 会员类型定义 ──
MEMBERSHIP_TRIAL = "trial"       # 体验会员 7天 免费
MEMBERSHIP_VIP = "vip"           # VIP会员 1年 49元
MEMBERSHIP_PERMANENT = "permanent"  # 永久会员 99元

MEMBERSHIP_PRICES = {
    MEMBERSHIP_TRIAL: 0,
    MEMBERSHIP_VIP: 49,
    MEMBERSHIP_PERMANENT: 99,
}

MEMBERSHIP_LABELS = {
    MEMBERSHIP_TRIAL: "体验会员",
    MEMBERSHIP_VIP: "VIP会员",
    MEMBERSHIP_PERMANENT: "永久会员",
}

# ── 预设管理员 ──
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _load_users() -> dict:
    """加载用户数据，兼容旧格式自动迁移"""
    if not os.path.exists(USER_DB):
        # 初始化默认管理员
        users = {
            ADMIN_USERNAME: {
                "password": ADMIN_PASSWORD,
                "role": "admin",
                "membership": MEMBERSHIP_PERMANENT,
                "expire_at": None,
                "created_at": "2026-01-01 00:00:00",
            }
        }
        _save_users(users)
        return users

    try:
        with open(USER_DB, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # JSON 文件损坏：备份损坏文件，回退到默认管理员
        corrupted = USER_DB + ".corrupted"
        try:
            os.rename(USER_DB, corrupted)
            print(f"[auth] users.json 损坏，已备份到 {corrupted}：{e}")
        except Exception:
            pass  # gracefully degrade on I/O failure
        users = {
            ADMIN_USERNAME: {
                "password": ADMIN_PASSWORD,
                "role": "admin",
                "membership": MEMBERSHIP_PERMANENT,
                "expire_at": None,
                "created_at": "2026-01-01 00:00:00",
            }
        }
        _save_users(users)
        return users

    if not data:
        data = {
            ADMIN_USERNAME: {
                "password": ADMIN_PASSWORD,
                "role": "admin",
                "membership": MEMBERSHIP_PERMANENT,
                "expire_at": None,
                "created_at": "2026-01-01 00:00:00",
            }
        }
        _save_users(data)
        return data

    # 检测旧格式 {"username": "password"} → 自动迁移
    first_val = next(iter(data.values()), None)
    if isinstance(first_val, str):
        migrated = {}
        for username, password in data.items():
            if username == ADMIN_USERNAME:
                migrated[username] = {
                    "password": password,
                    "role": "admin",
                    "membership": MEMBERSHIP_PERMANENT,
                    "expire_at": None,
                    "created_at": "2026-01-01 00:00:00",
                }
            else:
                # 旧用户转为 member + trial
                migrated[username] = {
                    "password": password,
                    "role": "member",
                    "membership": MEMBERSHIP_TRIAL,
                    "expire_at": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"),
                    "created_at": _now(),
                }
        _save_users(migrated)
        return migrated

    # 确保 admin 存在
    if ADMIN_USERNAME not in data:
        data[ADMIN_USERNAME] = {
            "password": ADMIN_PASSWORD,
            "role": "admin",
            "membership": MEMBERSHIP_PERMANENT,
            "expire_at": None,
            "created_at": "2026-01-01 00:00:00",
        }
        _save_users(data)

    return data


def _save_users(users: dict):
    os.makedirs(os.path.dirname(USER_DB), exist_ok=True)
    tmp_path = USER_DB + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, USER_DB)  # 原子替换，防止写入中断导致文件损坏


class AuthService:
    """认证服务"""

    def __init__(self):
        self._users = _load_users()

    def _reload(self):
        self._users = _load_users()

    # ── SQLite 同步桥接 ──
    def _sync_user_to_sqlite(self, username: str):
        """将 users.json 中的用户同步到 data/users.db（SQLite），供 cloud_sync 上传"""
        user = self._users.get(username)
        if not user:
            return
        try:
            os.makedirs(os.path.dirname(USERS_SQLITE_DB), exist_ok=True)
            conn = sqlite3.connect(USERS_SQLITE_DB)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT DEFAULT '',
                user_id TEXT,
                role TEXT DEFAULT 'user',
                license_type TEXT,
                created_at TEXT,
                updated_at TEXT
            )''')
            c.execute('''INSERT OR REPLACE INTO users
                (username, password, role, license_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, datetime('now','localtime'))''',
                (username, user.get("password", ""),
                 user.get("role", "member"),
                 user.get("membership", "trial"),
                 user.get("created_at", _now())))
            conn.commit()
            conn.close()
        except Exception:
            traceback.print_exc()

    def _sync_membership_to_sqlite(self, username: str):
        """将 users.json 中的会员信息同步到 data/users.db 的 user_memberships"""
        user = self._users.get(username)
        if not user:
            return
        try:
            conn = sqlite3.connect(USERS_SQLITE_DB)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS user_memberships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                membership_type TEXT,
                activated_at TEXT,
                expires_at TEXT,
                activation_code TEXT
            )''')
            c.execute('''INSERT OR REPLACE INTO user_memberships
                (username, membership_type, expires_at, activated_at)
                VALUES (?, ?, ?, ?)''',
                (username, user.get("membership", "trial"),
                 user.get("expire_at", None),
                 _now()))
            conn.commit()
            conn.close()
        except Exception:
            traceback.print_exc()

    def _trigger_cloud_sync(self):
        """异步触发云端同步（不阻塞 UI）"""
        try:
            from core.cloud_sync import sync_users
            t = threading.Thread(target=sync_users, daemon=True)
            t.start()
        except Exception:
            traceback.print_exc()

    def _find_user_in_sqlite(self, username: str) -> Optional[dict]:
        """在 data/users.db 中查找用户（跨机注册兜底）"""
        if not os.path.exists(USERS_SQLITE_DB):
            return None
        try:
            conn = sqlite3.connect(USERS_SQLITE_DB)
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            conn.close()
            if row:
                return {
                    "password": row["password"] or "",
                    "role": row["role"] or "member",
                    "membership": row["license_type"] or MEMBERSHIP_TRIAL,
                    "expire_at": None,
                    "created_at": row["created_at"] or _now(),
                }
        except Exception:
            traceback.print_exc()
        return None

    def register(self, username: str, password: str) -> tuple:
        """
        注册新用户
        返回: (ok: bool, msg: str)
        """
        self._reload()
        if not username or not password:
            return False, "用户名和密码不能为空"
        if len(username) < 2:
            return False, "用户名至少2个字符"
        if len(password) < 3:
            return False, "密码至少3个字符"
        if username in self._users:
            return False, "该用户名已被占用"

        now = _now()
        expire_at = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        self._users[username] = {
            "password": password,
            "role": "member",
            "membership": MEMBERSHIP_TRIAL,
            "expire_at": expire_at,
            "created_at": now,
        }
        _save_users(self._users)
        # 双写：同步到 SQLite → 触发云端同步（异步，不阻塞 UI）
        self._sync_user_to_sqlite(username)
        self._sync_membership_to_sqlite(username)
        self._trigger_cloud_sync()
        try:
            log_action(username, "注册", "login", "新用户注册")
        except Exception:
            pass
        return True, "注册成功"

    def modify_password(self, username: str, old_password: str,
                        new_password: str, confirm_password: str) -> tuple:
        """
        用户自主修改密码
        返回: (ok: bool, msg: str)
        """
        self._reload()
        user = self._users.get(username)
        if not user:
            return False, "用户不存在"
        if user.get("password") != old_password:
            return False, "原密码错误"
        if not new_password or len(new_password) < 6:
            return False, "新密码至少6位"
        if new_password != confirm_password:
            return False, "两次输入的新密码不一致"
        if new_password == old_password:
            return False, "新密码不能与原密码相同"

        user["password"] = new_password
        _save_users(self._users)
        self._sync_user_to_sqlite(username)
        self._trigger_cloud_sync()
        try:
            log_action(username, "修改密码", "account", "密码修改成功")
        except Exception:
            pass
        return True, "密码修改成功，请重新登录"

    def login(self, username: str, password: str) -> dict:
        """
        登录验证，检查会员过期
        JSON 优先 → SQLite 兜底（跨机注册用户）
        返回: {"ok": bool, "msg": str, "user": dict|None}
        """
        self._reload()
        if not username or not password:
            return {"ok": False, "msg": "用户名和密码不能为空", "user": None}

        user = self._users.get(username)
        # JSON 未找到 → 尝试 SQLite 兜底（跨机 cloud_pull 拉取的用户）
        if not user:
            user = self._find_user_in_sqlite(username)

        if not user:
            return {"ok": False, "msg": "用户名或密码错误", "user": None}

        if user["password"] != password:
            return {"ok": False, "msg": "用户名或密码错误", "user": None}

        # 管理员无过期限制
        if user["role"] == "admin":
            try:
                log_action(username, "登录", "login", "管理员登录成功")
            except Exception:
                pass
            return {"ok": True, "msg": "管理员登录成功", "user": user}

        # 检查会员过期
        expire_str = user.get("expire_at")
        if expire_str:
            try:
                expire_dt = datetime.strptime(expire_str, "%Y-%m-%d %H:%M:%S")
                if datetime.now() > expire_dt:
                    return {
                        "ok": False,
                        "msg": f"会员已过期（{expire_str}），请续费后登录",
                        "user": user,
                    }
            except ValueError:
                traceback.print_exc()

        try:
            log_action(username, "登录", "login", "用户登录成功")
        except Exception:
            pass
        return {"ok": True, "msg": "登录成功", "user": user}

    def admin_login(self, password: str) -> dict:
        """管理员登录"""
        return self.login(ADMIN_USERNAME, password)

    def upgrade_membership(self, username: str, target_membership: str) -> tuple:
        """
        升级会员
        target_membership: vip / permanent
        返回: (ok: bool, msg: str)
        """
        self._reload()
        user = self._users.get(username)
        if not user:
            return False, "用户不存在"

        current = user.get("membership", MEMBERSHIP_TRIAL)

        if target_membership == MEMBERSHIP_PERMANENT:
            if current == MEMBERSHIP_PERMANENT:
                return False, "已是永久会员，无需升级"
            user["membership"] = MEMBERSHIP_PERMANENT
            user["expire_at"] = None
            _save_users(self._users)
            self._sync_user_to_sqlite(username)
            self._sync_membership_to_sqlite(username)
            self._trigger_cloud_sync()
            try:
                log_action(username, "升级会员", "membership", "升级为永久会员")
            except Exception:
                pass
            return True, "升级为永久会员成功"

        if target_membership == MEMBERSHIP_VIP:
            if current == MEMBERSHIP_VIP:
                return False, "已是VIP会员"
            if current == MEMBERSHIP_PERMANENT:
                return False, "永久会员无需降级"
            user["membership"] = MEMBERSHIP_VIP
            user["expire_at"] = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
            _save_users(self._users)
            self._sync_user_to_sqlite(username)
            self._sync_membership_to_sqlite(username)
            self._trigger_cloud_sync()
            try:
                log_action(username, "升级会员", "membership", "升级为VIP会员（有效期1年）")
            except Exception:
                pass
            return True, "升级为VIP会员成功（有效期1年）"

        return False, "未知的会员类型"

    def get_user_info(self, username: str) -> "Optional[dict]":
        """获取用户信息"""
        self._reload()
        return self._users.get(username)

    def is_admin(self, username: str) -> bool:
        """判断是否为管理员"""
        user = self._users.get(username)
        return user is not None and user.get("role") == "admin"

    def activate_member(self, username: str, code: str) -> tuple:
        """
        通过激活码升级会员
        返回: (ok: bool, msg: str)
        """
        self._reload()
        user = self._users.get(username)
        if not user:
            return False, "用户不存在"

        # 从 activation.db 查询激活码
        if not os.path.exists(ACTIVATION_DB):
            return False, "激活码系统未初始化"

        conn = sqlite3.connect(ACTIVATION_DB)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM activation WHERE code = ?", (code,)
        ).fetchone()

        if not row:
            conn.close()
            return False, "激活码无效"

        if row["is_used"]:
            conn.close()
            return False, "该激活码已被使用"

        code_type = row["code_type"]
        duration = row["duration_days"]

        # 确定目标会员等级
        if code_type == "永久" or duration >= 9999:
            target = MEMBERSHIP_PERMANENT
        elif duration >= 365:
            target = MEMBERSHIP_VIP
        elif duration > 0:
            target = MEMBERSHIP_VIP  # 短期卡也算 VIP
        else:
            conn.close()
            return False, "无效的激活码时长"

        # 检查是否已是更高等级
        current = user.get("membership", MEMBERSHIP_TRIAL)
        if current == MEMBERSHIP_PERMANENT:
            conn.close()
            return False, "已是永久会员，无需激活"

        # 执行升级
        if target == MEMBERSHIP_PERMANENT:
            user["membership"] = MEMBERSHIP_PERMANENT
            user["expire_at"] = None
        else:
            if current == MEMBERSHIP_VIP:
                # 已有 VIP，延长
                old_expire = user.get("expire_at")
                if old_expire:
                    try:
                        old_dt = datetime.strptime(old_expire, "%Y-%m-%d %H:%M:%S")
                        new_dt = max(old_dt, datetime.now()) + timedelta(days=duration)
                    except ValueError:
                        new_dt = datetime.now() + timedelta(days=duration)
                else:
                    new_dt = datetime.now() + timedelta(days=duration)
                user["expire_at"] = new_dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                user["membership"] = MEMBERSHIP_VIP
                user["expire_at"] = (datetime.now() + timedelta(days=duration)).strftime("%Y-%m-%d %H:%M:%S")

        # 标记激活码已使用
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE activation SET is_used = 1, used_by = ?, used_at = ? WHERE code = ?",
            (username, now, code)
        )
        conn.commit()
        conn.close()

        _save_users(self._users)
        self._sync_user_to_sqlite(username)
        self._sync_membership_to_sqlite(username)
        self._trigger_cloud_sync()
        try:
            log_action(username, "激活会员", "membership", f"激活码激活，类型={code_type}")
        except Exception:
            pass
        return True, "激活成功"

    def get_membership_info(self, username: str) -> dict:
        """获取会员信息摘要"""
        user = self._users.get(username)
        if not user:
            return {"username": username, "membership": MEMBERSHIP_TRIAL, "label": "体验会员",
                    "expire_at": None, "days_left": 0, "role": "member"}

        membership = user.get("membership", MEMBERSHIP_TRIAL)
        expire_at = user.get("expire_at")
        days_left = -1  # -1 表示永久

        if expire_at:
            try:
                expire_dt = datetime.strptime(expire_at, "%Y-%m-%d %H:%M:%S")
                delta = (expire_dt - datetime.now()).days
                days_left = max(delta, 0)
            except ValueError:
                days_left = 0

        return {
            "username": username,
            "membership": membership,
            "label": MEMBERSHIP_LABELS.get(membership, "体验会员"),
            "expire_at": expire_at,
            "days_left": days_left,  # -1=永久, >=0=剩余天数
            "role": user.get("role", "member"),
        }

    def admin_reset_password(self, username: str, new_password: str) -> tuple:
        """
        管理员重置用户密码（明文存储）
        返回: (ok: bool, msg: str)
        """
        self._reload()
        user = self._users.get(username)
        if not user:
            return False, "用户不存在"

        if not new_password or len(new_password) < 3:
            return False, "密码至少3个字符"

        user["password"] = new_password
        _save_users(self._users)
        self._sync_user_to_sqlite(username)
        self._trigger_cloud_sync()
        try:
            log_action("admin", "重置密码", "admin", f"重置用户 {username} 的密码")
        except Exception:
            pass
        return True, f"用户 {username} 的密码已重置"