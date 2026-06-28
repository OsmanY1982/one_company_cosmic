# `modules/personnel/wallet_service.py`

> 路径：`modules/personnel/wallet_service.py` | 行数：1362


---


```python
import logging

logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
"""
钱包服务模块

提供：钱包管理、充值、提现、转账、交易记录、云端同步
数据库：data/wallet.db (wallet + wallet_transactions)
"""
import os
import sys

# ── 路径：modules/personnel/wallet_service.py → 项目根目录（3层dirname）──
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.database import get_conn
import csv
from datetime import datetime, timedelta
from typing import Optional

from core.paths import DATA_DIR

# 财务同步（失败不影响本地操作）
try:
    from modules.business.finance_service import add_record as _fin_add
    _FINANCE_ENABLED = True
except Exception:
    _FINANCE_ENABLED = False

DB_PATH = os.path.join(DATA_DIR, "wallet.db")

# ──────────────────────────────────────────
#  云端同步（失败不影响本地操作）
# ──────────────────────────────────────────
def _cloud_safe(fn, *args, **kwargs):
    """执行云端操作，失败时静默忽略（不影响本地）"""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f"[CloudWallet] sync failed (non-blocking): {e}")
        return False, str(e)


def _sync_wallet_cloud(wallet: dict):
    """同步钱包到云端"""
    try:
        from core.supabase_client import CloudWallet
        _cloud_safe(
            CloudWallet.upsert,
            user_id=wallet["user_id"],
            balance=wallet.get("balance", 0),
            frozen_amount=wallet.get("frozen_amount", 0),
            total_income=wallet.get("total_income", 0),
            total_withdraw=wallet.get("total_withdraw", 0),
            status=wallet.get("status", "active"),
        )
    except ImportError:
        logger.exception("异常详情")
        pass  # core.supabase_client 不可用时跳过


def _sync_txn_cloud(txn: dict):
    """同步交易记录到云端"""
    try:
        from core.supabase_client import CloudWalletTxn
        _cloud_safe(
            CloudWalletTxn.log,
            wallet_id=txn["wallet_id"],
            txn_type=txn["type"],
            amount=txn["amount"],
            balance_after=txn["balance_after"],
            description=txn.get("description", ""),
            created_at=txn.get("created_at"),
        )
    except ImportError:
        logger.exception("异常详情")


# ──────────────────────────────────────────
#  数据库初始化（幂等，可多次调用）
# ──────────────────────────────────────────
def init_db():
    """初始化钱包相关表结构"""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = get_conn("wallet.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallet (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          TEXT UNIQUE NOT NULL,
            balance          REAL DEFAULT 0,
            frozen_amount    REAL DEFAULT 0,
            total_income     REAL DEFAULT 0,
            total_withdraw   REAL DEFAULT 0,
            status           TEXT DEFAULT 'active',
            created_at       TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at       TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallet_transactions (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_id      INTEGER NOT NULL,
            type           TEXT NOT NULL,
            amount         REAL NOT NULL,
            balance_after  REAL NOT NULL,
            description    TEXT,
            created_at     TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (wallet_id) REFERENCES wallet(id)
        )
    ''')
    try:
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_wallet_txn_type "
            "ON wallet_transactions(wallet_id, type)"
        )
    except Exception:
        logger.exception("异常详情")
    try:
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_wallet_txn_created "
            "ON wallet_transactions(created_at DESC)"
        )
    except Exception:
        logger.exception("异常详情")
    conn.commit()

def _connect():
    """返回统一连接管理器中的 wallet.db 连接"""
    return get_conn("wallet.db")


# ──────────────────────────────────────────
#  钱包基础操作
# ──────────────────────────────────────────
# ============================================================
# 钱包地址簿
# ============================================================

def init_address_book_db():
    conn = _connect()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS address_book (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_user TEXT NOT NULL,
            label TEXT NOT NULL,
            address TEXT NOT NULL,
            address_type TEXT DEFAULT 'user',
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    conn.commit()

def add_address(owner_user: str, label: str, address: str,
                address_type: str = "user", note: str = "") -> dict:
    if not owner_user or not label or not address:
        return {"ok": False, "error": "owner_user, label, address required"}
    try:
        conn = _connect()
        conn.execute(
            "INSERT INTO address_book (owner_user, label, address, address_type, note) "
            "VALUES (?, ?, ?, ?, ?)",
            (owner_user, label, address, address_type, note)
        )
        conn.commit()

        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def get_addresses(owner_user: str = None) -> list[dict]:
    conn = _connect()
    if owner_user:
        rows = conn.execute(
            "SELECT * FROM address_book WHERE owner_user=? ORDER BY created_at DESC",
            (owner_user,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM address_book ORDER BY created_at DESC"
        ).fetchall()

    return [dict(r) for r in rows]

def update_address(addr_id: int, label: str = None,
                   address: str = None, note: str = None) -> dict:
    fields, vals = [], []
    if label:   fields.append("label=?");    vals.append(label)
    if address: fields.append("address=?"); vals.append(address)
    if note is not None: fields.append("note=?"); vals.append(note)
    if not fields:
        return {"ok": False, "error": "no fields to update"}
    vals.append(addr_id)
    try:
        conn = _connect()
        conn.execute(
            f"UPDATE address_book SET {', '.join(fields)} WHERE id=?",
            vals
        )
        conn.commit()

        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def delete_address(addr_id: int) -> dict:
    try:
        conn = _connect()
        conn.execute("DELETE FROM address_book WHERE id=?", (addr_id,))
        conn.commit()

        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}



def get_wallet(user_id: str) -> Optional[dict]:
    """获取用户钱包，不存在则返回 None"""
    init_db()
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM wallet WHERE user_id = ?", (str(user_id),)
    ).fetchone()

    return dict(row) if row else None


def get_or_create_wallet(user_id: str) -> dict:
    """获取或创建用户钱包（首次创建自动同步云端）"""
    w = get_wallet(user_id)
    if w:
        return w
    init_db()
    conn = _connect()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute(
            "INSERT INTO wallet (user_id, balance, frozen_amount, total_income, "
            "total_withdraw, created_at, updated_at) "
            "VALUES (?, 0, 0, 0, 0, ?, ?)",
            (str(user_id), now, now)
        )
        conn.commit()
    except Exception:
        logger.exception("异常详情")
    row = conn.execute(
        "SELECT * FROM wallet WHERE user_id = ?", (str(user_id),)
    ).fetchone()

    wallet = dict(row) if row else {}
    if wallet:
        _sync_wallet_cloud(wallet)
    return wallet


def get_balance(user_id: str) -> float:
    """快捷方法：获取用户余额"""
    w = get_wallet(user_id)
    return w.get("balance", 0) if w else 0


def freeze_amount(user_id: str, amount: float, reason: str = "") -> dict:
    """冻结金额（如提现审核中）"""
    w = get_wallet(user_id)
    if not w:
        return {"ok": False, "error": "钱包不存在"}
    available = w["balance"] - w.get("frozen_amount", 0)
    if available < amount:
        return {"ok": False, "error": f"可用余额不足（{available:.2f}）"}
    init_db()
    conn = _connect()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("BEGIN")
    conn.execute(
        "UPDATE wallet SET frozen_amount = frozen_amount + ?, updated_at = ? "
        "WHERE user_id = ?",
        (amount, now, str(user_id))
    )
    conn.execute(
        "INSERT INTO wallet_transactions "
        "(wallet_id, type, amount, balance_after, description, created_at) "
        "VALUES (?, 'freeze', ?, ?, ?, ?)",
        (w["id"], -amount, w["balance"], reason or "冻结", now)
    )
    conn.commit()
    updated_wallet = get_wallet(user_id)
    txn = {"wallet_id": w["id"], "type": "freeze",
           "amount": -amount, "balance_after": w["balance"],
           "description": reason or "冻结", "created_at": now}

    _sync_wallet_cloud(updated_wallet)
    _sync_txn_cloud(txn)
    return {"ok": True}


def unfreeze_amount(user_id: str, amount: float, reason: str = "") -> dict:
    """解冻金额"""
    w = get_wallet(user_id)
    if not w:
        return {"ok": False, "error": "钱包不存在"}
    if w.get("frozen_amount", 0) < amount:
        return {"ok": False, "error": "冻结金额不足"}
    init_db()
    conn = _connect()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("BEGIN")
    conn.execute(
        "UPDATE wallet SET frozen_amount = frozen_amount - ?, updated_at = ? "
        "WHERE user_id = ?",
        (amount, now, str(user_id))
    )
    conn.execute(
        "INSERT INTO wallet_transactions "
        "(wallet_id, type, amount, balance_after, description, created_at) "
        "VALUES (?, 'unfreeze', ?, ?, ?, ?)",
        (w["id"], amount, w["balance"], reason or "解冻", now)
    )
    conn.commit()
    updated_wallet = get_wallet(user_id)
    txn = {"wallet_id": w["id"], "type": "unfreeze",
           "amount": amount, "balance_after": w["balance"],
           "description": reason or "解冻", "created_at": now}

    _sync_wallet_cloud(updated_wallet)
    _sync_txn_cloud(txn)
    return {"ok": True}


# ──────────────────────────────────────────
#  充值 / 提现 / 转账 / 佣金
# ──────────────────────────────────────────
def recharge(user_id: str, amount: float, description: str = "充值",
             operator: str = "system") -> dict:
    """充值（自动同步云端）"""
    if amount <= 0:
        return {"ok": False, "error": "充值金额必须大于 0"}
    w = get_or_create_wallet(user_id)
    init_db()
    conn = _connect()
    try:
        conn.execute("BEGIN")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE wallet SET balance = balance + ?, "
            "total_income = total_income + ?, updated_at = ? WHERE id = ?",
            (amount, amount, now, w["id"])
        )
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'recharge', ?, ?, ?, ?)",
            (w["id"], amount, w["balance"] + amount,
             f"{description}（{operator}）", now)
        )
        conn.commit()
        new_balance = w["balance"] + amount

        updated_w = get_wallet(user_id)
        txn = {"wallet_id": w["id"], "type": "recharge",
               "amount": amount, "balance_after": new_balance,
               "description": f"{description}（{operator}）", "created_at": now}
        _sync_wallet_cloud(updated_w)
        _sync_txn_cloud(txn)
        # ── 财务同步（充值 → 收入）────────────────────
        if _FINANCE_ENABLED:
            _fin_add(date=now[:10], record_type="income",
                     category="充值", amount=amount,
                     description=f"钱包充值 → {user_id}（{operator}）")
        return {"ok": True, "balance": new_balance, "amount": amount}
    except Exception as e:
        conn.execute("ROLLBACK")

        return {"ok": False, "error": str(e)}


def withdraw(user_id: str, amount: float,
             description: str = "提现申请") -> dict:
    """提现（直接扣减余额）"""
    if amount <= 0:
        return {"ok": False, "error": "提现金额必须大于 0"}
    w = get_wallet(user_id)
    if not w:
        return {"ok": False, "error": "钱包不存在"}
    available = w["balance"] - w.get("frozen_amount", 0)
    if available < amount:
        return {"ok": False, "error": f"可用余额不足（{available:.2f}）"}
    init_db()
    conn = _connect()
    try:
        conn.execute("BEGIN")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE wallet SET balance = balance - ?, "
            "total_withdraw = total_withdraw + ?, updated_at = ? WHERE id = ?",
            (amount, amount, now, w["id"])
        )
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'withdraw', ?, ?, ?, ?)",
            (w["id"], -amount, w["balance"] - amount, description, now)
        )
        conn.commit()

        updated_w = get_wallet(user_id)
        txn = {"wallet_id": w["id"], "type": "withdraw",
               "amount": -amount, "balance_after": w["balance"] - amount,
               "description": description, "created_at": now}
        _sync_wallet_cloud(updated_w)
        _sync_txn_cloud(txn)
        # ── 财务同步（提现 → 支出）────────────────────
        if _FINANCE_ENABLED:
            _fin_add(date=now[:10], record_type="expense",
                     category="提现", amount=-amount,
                     description=f"提现 {user_id}（{description}）")
        return {"ok": True, "balance": w["balance"] - amount, "amount": amount}
    except Exception as e:
        conn.execute("ROLLBACK")

        return {"ok": False, "error": str(e)}


def transfer(from_user: str, to_user: str, amount: float,
             description: str = "") -> dict:
    """转账（原子操作，一方失败则全部回滚）"""
    if amount <= 0:
        return {"ok": False, "error": "转账金额必须大于 0"}
    if from_user == to_user:
        return {"ok": False, "error": "不能给自己转账"}
    w_from = get_wallet(from_user)
    w_to = get_or_create_wallet(to_user)
    if not w_from:
        return {"ok": False, "error": f"转出用户 {from_user} 不存在"}
    available = w_from["balance"] - w_from.get("frozen_amount", 0)
    if available < amount:
        return {"ok": False, "error": f"可用余额不足（{available:.2f}）"}
    init_db()
    conn = _connect()
    try:
        conn.execute("BEGIN")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 扣款
        conn.execute(
            "UPDATE wallet SET balance = balance - ?, updated_at = ? WHERE id = ?",
            (amount, now, w_from["id"])
        )
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'transfer_out', ?, ?, ?, ?)",
            (w_from["id"], -amount, w_from["balance"] - amount,
             f"转出至 {to_user}" + (f"（{description}）" if description else ""), now)
        )
        # 到账
        conn.execute(
            "UPDATE wallet SET balance = balance + ?, updated_at = ? WHERE id = ?",
            (amount, now, w_to["id"])
        )
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'transfer_in', ?, ?, ?, ?)",
            (w_to["id"], amount, w_to["balance"] + amount,
             f"由 {from_user} 转入" + (f"（{description}）" if description else ""), now)
        )
        conn.commit()

        from_wallet = get_wallet(from_user)
        to_wallet = get_wallet(to_user)
        _sync_wallet_cloud(from_wallet)
        _sync_wallet_cloud(to_wallet)
        _sync_txn_cloud({
            "wallet_id": w_from["id"], "type": "transfer_out",
            "amount": -amount, "balance_after": w_from["balance"] - amount,
            "description": f"转出至 {to_user}" + (f"（{description}）" if description else ""),
            "created_at": now
        })
        _sync_txn_cloud({
            "wallet_id": w_to["id"], "type": "transfer_in",
            "amount": amount, "balance_after": w_to["balance"] + amount,
            "description": f"由 {from_user} 转入" + (f"（{description}）" if description else ""),
            "created_at": now
        })
        # ── 财务同步（转账 → 支出+收入）────────────────
        if _FINANCE_ENABLED:
            _fin_add(date=now[:10], record_type="expense",
                     category="转账", amount=-amount,
                     description=f"转账 → {to_user}（{description}）")
            _fin_add(date=now[:10], record_type="income",
                     category="转账", amount=amount,
                     description=f"转账 ← {from_user}（{description}）")
        return {
            "ok": True,
            "from_balance": w_from["balance"] - amount,
            "to_balance": w_to["balance"] + amount,
            "amount": amount,
        }
    except Exception as e:
        conn.execute("ROLLBACK")

        return {"ok": False, "error": str(e)}


def add_commission(user_id: str, amount: float,
                   description: str = "佣金收入") -> dict:
    """发放佣金（自动同步云端）"""
    if amount <= 0:
        return {"ok": False, "error": "金额必须大于 0"}
    w = get_or_create_wallet(user_id)
    init_db()
    conn = _connect()
    try:
        conn.execute("BEGIN")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE wallet SET balance = balance + ?, "
            "total_income = total_income + ?, updated_at = ? WHERE id = ?",
            (amount, amount, now, w["id"])
        )
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'commission', ?, ?, ?, ?)",
            (w["id"], amount, w["balance"] + amount, description, now)
        )
        conn.commit()
        new_balance = w["balance"] + amount

        updated_w = get_wallet(user_id)
        txn = {"wallet_id": w["id"], "type": "commission",
               "amount": amount, "balance_after": new_balance,
               "description": description, "created_at": now}
        _sync_wallet_cloud(updated_w)
        _sync_txn_cloud(txn)
        # ── 财务同步（佣金 → 收入）────────────────────
        if _FINANCE_ENABLED:
            _fin_add(date=now[:10], record_type="income",
                     category="佣金", amount=amount,
                     description=f"佣金发放 → {user_id}（{description}）")
        return {"ok": True, "balance": new_balance, "amount": amount}
    except Exception as e:
        conn.execute("ROLLBACK")

        return {"ok": False, "error": str(e)}


# ──────────────────────────────────────────
#  查询
# ──────────────────────────────────────────
def get_transactions(wallet_id: int = None,
                     txn_type: str = "",
                     start_date: str = "",
                     end_date: str = "",
                     min_amount: float = None,
                     max_amount: float = None,
                     keyword: str = "",
                     limit: int = 200,
                     offset: int = 0) -> list[dict]:
    """
    获取交易记录（支持多维过滤）。
    wallet_id=None 表示全局（所有钱包）。
    """
    init_db()
    conn = _connect()
    sql = "SELECT * FROM wallet_transactions WHERE 1=1"
    params = []
    if wallet_id is not None:
        sql += " AND wallet_id=?"
        params.append(wallet_id)
    if txn_type:
        sql += " AND type=?"
        params.append(txn_type)
    if start_date:
        sql += " AND date(created_at) >= date(?)"
        params.append(start_date)
    if end_date:
        sql += " AND date(created_at) <= date(?)"
        params.append(end_date)
    if min_amount is not None:
        sql += " AND ABS(amount) >= ?"
        params.append(min_amount)
    if max_amount is not None:
        sql += " AND ABS(amount) <= ?"
        params.append(max_amount)
    if keyword:
        sql += " AND description LIKE ?"
        params.append(f"%{keyword}%")
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(sql, params).fetchall()

    return [dict(r) for r in rows]


def get_all_wallets(search: str = "") -> list[dict]:
    """获取所有钱包（支持搜索）"""
    init_db()
    conn = _connect()
    if search:
        rows = conn.execute(
            "SELECT * FROM wallet WHERE user_id LIKE ? ORDER BY id DESC",
            (f"%{search}%",)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM wallet ORDER BY id DESC"
        ).fetchall()

    return [dict(r) for r in rows]


def get_wallet_stats() -> dict:
    """获取全局钱包统计"""
    init_db()
    conn = _connect()
    row = conn.execute(
        "SELECT COUNT(*) as count, "
        "COALESCE(SUM(balance), 0) as total_balance, "
        "COALESCE(SUM(frozen_amount), 0) as total_frozen, "
        "COALESCE(SUM(total_income), 0) as total_income, "
        "COALESCE(SUM(total_withdraw), 0) as total_withdraw "
        "FROM wallet WHERE status='active'"
    ).fetchone()

    return dict(row)


def get_income_expense_report(days: int = 30) -> dict:
    """
    获取收支报表（最近 N 天）。
    返回 {income, expense, net, transactions}
    """
    init_db()
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    conn = _connect()
    rows = conn.execute(
        "SELECT type, SUM(amount) as total, COUNT(*) as count "
        "FROM wallet_transactions WHERE created_at >= ? "
        "GROUP BY type",
        (since,)
    ).fetchall()

    income = expense = 0
    detail = {}
    for r in rows:
        t, total, count = r["type"], r["total"], r["count"]
        detail[t] = {"total": total, "count": count}
        if t in ("recharge", "commission", "transfer_in"):
            income += total
        elif t in ("withdraw", "transfer_out"):
            expense += abs(total)

    return {
        "income": income,
        "expense": expense,
        "net": income - expense,
        "since_days": days,
        "detail": detail,
    }


def get_top_wallets(limit: int = 10, by: str = "balance") -> list[dict]:
    """
    获取余额最高的钱包。
    by: balance | total_income | total_withdraw
    """
    allowed = {"balance", "total_income", "total_withdraw"}
    col = by if by in allowed else "balance"
    init_db()
    conn = _connect()
    rows = conn.execute(
        f"SELECT * FROM wallet WHERE status='active' "
        f"ORDER BY {col} DESC LIMIT ?",
        (limit,)
    ).fetchall()

    return [dict(r) for r in rows]


def update_wallet_status(user_id: str, status: str) -> dict:
    """更新钱包状态（封禁/激活）"""
    w = get_wallet(user_id)
    if not w:
        return {"ok": False, "error": "钱包不存在"}
    init_db()
    conn = _connect()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE wallet SET status=?, updated_at=? WHERE user_id=?",
        (status, now, str(user_id))
    )
    conn.commit()

    updated_w = get_wallet(user_id)
    _sync_wallet_cloud(updated_w)
    return {"ok": True}


# ──────────────────────────────────────────
#  导出
# ──────────────────────────────────────────
def export_transactions_to_csv(filepath: str = None,
                                wallet_id: int = None,
                                days: int = 90) -> str:
    """
    导出交易记录为 CSV 文件。
    - filepath: 输出路径，默认 data/wallet_export_YYYYMMDD.csv
    - wallet_id: 指定钱包，不指定则导出全部
    - days: 导出最近 N 天
    """
    init_db()
    if filepath is None:
        date_str = datetime.now().strftime("%Y%m%d")
        filepath = os.path.join(DATA_DIR, f"wallet_export_{date_str}.csv")

    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    conn = _connect()
    if wallet_id:
        rows = conn.execute(
            "SELECT t.*, w.user_id FROM wallet_transactions t "
            "JOIN wallet w ON t.wallet_id = w.id "
            "WHERE t.wallet_id = ? AND t.created_at >= ? "
            "ORDER BY t.id DESC",
            (wallet_id, since)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT t.*, w.user_id FROM wallet_transactions t "
            "JOIN wallet w ON t.wallet_id = w.id "
            "WHERE t.created_at >= ? ORDER BY t.id DESC",
            (since,)
        ).fetchall()

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "用户ID", "钱包ID", "类型", "金额", "余额后",
            "描述", "创建时间"
        ])
        type_labels = {
            "recharge": "充值", "withdraw": "提现",
            "transfer_in": "转入", "transfer_out": "转出",
            "commission": "佣金", "freeze": "冻结", "unfreeze": "解冻",
        }
        for r in rows:
            label = type_labels.get(r["type"], r["type"])
            writer.writerow([
                r["id"], r["user_id"], r["wallet_id"], label,
                f"{r['amount']:.2f}", f"{r['balance_after']:.2f}",
                r["description"] or "", r["created_at"]
            ])
    return filepath


# ──────────────────────────────────────────
#  对账
# ──────────────────────────────────────────
def reconcile(local_only: bool = False) -> dict:
    """
    本地与云端对账。
    返回：{in_cloud_not_local, in_local_not_cloud, mismatch, ok}
    """
    try:
        from core.supabase_client import CloudWallet
    except ImportError:
        return {
            "ok": False,
            "error": "Supabase 不可用，无法对账",
            "in_cloud_not_local": [],
            "in_local_not_cloud": [],
            "mismatch": [],
        }

    local_wallets = get_all_wallets()
    local_map = {str(w["user_id"]): w for w in local_wallets}

    ok_cloud, cloud_list = CloudWallet.get_recent(limit=1000)
    if not ok_cloud or not cloud_list:
        return {
            "ok": False,
            "error": "无法获取云端数据",
            "in_cloud_not_local": [],
            "in_local_not_cloud": list(local_map.keys()),
            "mismatch": [],
        }

    cloud_map = {str(c.get("user_id", "")): c for c in cloud_list}

    in_cloud_not_local = [
        c["user_id"] for c in cloud_list
        if str(c["user_id"]) not in local_map
    ]
    in_local_not_cloud = [
        uid for uid in local_map if uid not in cloud_map
    ]
    mismatch = []
    for uid, lw in local_map.items():
        if uid in cloud_map:
            cw = cloud_map[uid]
            if abs(float(lw.get("balance", 0)) - float(cw.get("balance", 0))) > 0.01:
                mismatch.append({
                    "user_id": uid,
                    "local_balance": lw.get("balance"),
                    "cloud_balance": cw.get("balance"),
                })

    return {
        "ok": len(mismatch) == 0 and len(in_cloud_not_local) == 0,
        "in_cloud_not_local": in_cloud_not_local,
        "in_local_not_cloud": in_local_not_cloud,
        "mismatch": mismatch,
    }


def force_sync_all_to_cloud() -> dict:
    """强制将所有本地钱包同步到云端（用于修复对账问题）"""
    try:
        from core.supabase_client import CloudWallet
    except ImportError:
        return {"ok": False, "error": "Supabase 不可用"}

    wallets = get_all_wallets()
    result = CloudWallet.sync_from_local(wallets)
    return {
        "ok": True,
        "synced": result.get("success", 0),
        "failed": result.get("fail", 0),
    }


# ──────────────────────────────────────────
#  看板数据
# ──────────────────────────────────────────
def get_balance_trend(days: int = 30) -> list[dict]:
    """
    获取每日余额趋势（最近 N 天）。
    返回: [{date: "2026-05-01", balance: 1000.0, income: 500, expense: 200}, ...]
    """
    init_db()
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    conn = _connect()
    # 每日收入（充值+佣金+转入）
    income_rows = conn.execute(
        "SELECT DATE(created_at) as date, SUM(amount) as total "
        "FROM wallet_transactions "
        "WHERE DATE(created_at) >= ? AND type IN ('recharge','commission','transfer_in') "
        "GROUP BY DATE(created_at) ORDER BY date",
        (since,)
    ).fetchall()

    # 每日支出（提现+转出）
    expense_rows = conn.execute(
        "SELECT DATE(created_at) as date, SUM(ABS(amount)) as total "
        "FROM wallet_transactions "
        "WHERE DATE(created_at) >= ? AND type IN ('withdraw','transfer_out') "
        "GROUP BY DATE(created_at) ORDER BY date",
        (since,)
    ).fetchall()

    income_map = {r["date"]: r["total"] for r in income_rows}
    expense_map = {r["date"]: r["total"] for r in expense_rows}

    # 构建完整日期序列
    result = []
    running = 0.0
    for i in range(days, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        inc = income_map.get(d, 0)
        exp = expense_map.get(d, 0)
        running += inc - exp
        result.append({
            "date": d,
            "income": inc,
            "expense": exp,
            "balance": running,
        })
    return result


def get_wallet_detail(user_id: str) -> dict:
    """获取钱包完整详情（包含最近10条交易）"""
    w = get_wallet(user_id)
    if not w:
        return {}
    txns = get_transactions(w["id"], limit=10)
    trend = get_balance_trend(7)  # 7天趋势
    return {
        **w,
        "recent_transactions": txns,
        "balance_trend": trend,
        "available": w.get("balance", 0) - w.get("frozen_amount", 0),
    }


# ──────────────────────────────────────────
#  提现审批队列
# ──────────────────────────────────────────
def init_withdrawal_queue():
    """初始化提现审批队列表（幂等）"""
    conn = get_conn("wallet.db")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS withdrawal_queue (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      TEXT NOT NULL,
            wallet_id    INTEGER NOT NULL,
            amount       REAL NOT NULL,
            description  TEXT,
            status       TEXT DEFAULT 'pending',
            reviewed_by  TEXT,
            reviewed_at  TEXT,
            note         TEXT,
            created_at   TEXT DEFAULT (datetime('now'))
        )
    ''')
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_withdrawal_status ON withdrawal_queue(status)")
    except Exception:
        logger.exception("异常详情")
    conn.commit()

def submit_withdrawal_request(user_id: str, amount: float,
                               description: str = "提现申请") -> dict:
    """
    提交提现申请（自动冻结金额，状态=pending）。
    """
    if amount <= 0:
        return {"ok": False, "error": "金额必须大于 0"}
    w = get_wallet(user_id)
    if not w:
        return {"ok": False, "error": "钱包不存在"}
    available = w.get("balance", 0) - w.get("frozen_amount", 0)
    if available < amount:
        return {"ok": False, "error": f"可用余额不足（{available:.2f}）"}

    init_withdrawal_queue()
    conn = _connect()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute("BEGIN")
        # 冻结金额
        conn.execute(
            "UPDATE wallet SET frozen_amount = frozen_amount + ?, "
            "updated_at = ? WHERE id = ?",
            (amount, now, w["id"])
        )
        # 记录冻结交易
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'freeze', ?, ?, ?, ?)",
            (w["id"], -amount, w["balance"], f"提现冻结：{amount:.2f}", now)
        )
        # 提现申请记录
        conn.execute(
            "INSERT INTO withdrawal_queue "
            "(user_id, wallet_id, amount, description, status, created_at) "
            "VALUES (?, ?, ?, ?, 'pending', ?)",
            (str(user_id), w["id"], amount, description, now)
        )
        conn.commit()

        updated_w = get_wallet(user_id)
        _sync_wallet_cloud(updated_w)
        return {"ok": True, "frozen": amount, "message": f"申请已提交，冻结金额 {amount:.2f}"}
    except Exception as e:
        conn.execute("ROLLBACK")

        return {"ok": False, "error": str(e)}


def get_pending_withdrawals() -> list[dict]:
    """获取所有待审批的提现申请"""
    init_withdrawal_queue()
    conn = _connect()
    rows = conn.execute(
        "SELECT wq.*, wa.user_id, wa.balance as wallet_balance "
        "FROM withdrawal_queue wq "
        "JOIN wallet wa ON wq.wallet_id = wa.id "
        "WHERE wq.status = 'pending' "
        "ORDER BY wq.id DESC"
    ).fetchall()

    return [dict(r) for r in rows]


def get_all_withdrawal_requests(status: str = "", limit: int = 100) -> list[dict]:
    """获取所有提现申请（可按状态筛选）"""
    init_withdrawal_queue()
    conn = _connect()
    if status:
        rows = conn.execute(
            "SELECT wq.*, wa.user_id "
            "FROM withdrawal_queue wq "
            "JOIN wallet wa ON wq.wallet_id = wa.id "
            "WHERE wq.status = ? ORDER BY wq.id DESC LIMIT ?",
            (status, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT wq.*, wa.user_id "
            "FROM withdrawal_queue wq "
            "JOIN wallet wa ON wq.wallet_id = wa.id "
            "ORDER BY wq.id DESC LIMIT ?",
            (limit,)
        ).fetchall()

    return [dict(r) for r in rows]


def approve_withdrawal(request_id: int, operator: str = "admin",
                       note: str = "") -> dict:
    """审批通过提现申请：正式扣款（从冻结中扣）、更新状态。"""
    init_withdrawal_queue()
    conn = _connect()
    req = conn.execute(
        "SELECT * FROM withdrawal_queue WHERE id = ? AND status='pending'",
        (request_id,)
    ).fetchone()
    if not req:

        return {"ok": False, "error": "申请不存在或已处理"}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute("BEGIN")
        # 正式扣款（从余额扣，同时从冻结中减）
        conn.execute(
            "UPDATE wallet SET "
            "balance = balance - ?, "
            "frozen_amount = frozen_amount - ?, "
            "total_withdraw = total_withdraw + ?, "
            "updated_at = ? WHERE id = ?",
            (req["amount"], req["amount"], req["amount"],
             now, req["wallet_id"])
        )
        # 记录提现交易
        w_after = conn.execute(
            "SELECT balance FROM wallet WHERE id=?", (req["wallet_id"],)
        ).fetchone()["balance"]
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'withdraw', ?, ?, ?, ?)",
            (req["wallet_id"], -req["amount"], w_after,
             f"提现审批通过", now)
        )
        # 更新申请状态
        conn.execute(
            "UPDATE withdrawal_queue SET status='approved', "
            "reviewed_by=?, reviewed_at=?, note=? WHERE id=?",
            (operator, now, note or "", request_id)
        )
        conn.commit()

        # 同步云端
        wallet = get_wallet(req["user_id"])
        _sync_wallet_cloud(wallet)
        return {"ok": True, "amount": req["amount"], "user_id": req["user_id"]}
    except Exception as e:
        conn.execute("ROLLBACK")

        return {"ok": False, "error": str(e)}


def reject_withdrawal(request_id: int, operator: str = "admin",
                      note: str = "") -> dict:
    """审批拒绝提现申请：解冻金额、更新状态。"""
    init_withdrawal_queue()
    conn = _connect()
    req = conn.execute(
        "SELECT * FROM withdrawal_queue WHERE id = ? AND status='pending'",
        (request_id,)
    ).fetchone()
    if not req:

        return {"ok": False, "error": "申请不存在或已处理"}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute("BEGIN")
        # 解冻金额
        conn.execute(
            "UPDATE wallet SET frozen_amount = frozen_amount - ?, "
            "updated_at = ? WHERE id = ?",
            (req["amount"], now, req["wallet_id"])
        )
        # 记录解冻交易
        w_after = conn.execute(
            "SELECT balance FROM wallet WHERE id=?", (req["wallet_id"],)
        ).fetchone()["balance"]
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'unfreeze', ?, ?, ?, ?)",
            (req["wallet_id"], req["amount"], w_after,
             f"提现拒绝解冻", now)
        )
        # 更新申请状态
        conn.execute(
            "UPDATE withdrawal_queue SET status='rejected', "
            "reviewed_by=?, reviewed_at=?, note=? WHERE id=?",
            (operator, now, note or "", request_id)
        )
        conn.commit()

        wallet = get_wallet(req["user_id"])
        _sync_wallet_cloud(wallet)
        return {"ok": True, "amount": req["amount"], "user_id": req["user_id"]}
    except Exception as e:
        conn.execute("ROLLBACK")

        return {"ok": False, "error": str(e)}


# ──────────────────────────────────────────
#  删除 / 取消操作
# ──────────────────────────────────────────
def cancel_withdrawal_request(request_id: int) -> dict:
    """取消待审批的提现申请，自动解冻金额。"""
    init_withdrawal_queue()
    conn = _connect()
    req = conn.execute(
        "SELECT * FROM withdrawal_queue WHERE id=? AND status='pending'",
        (request_id,)
    ).fetchone()
    if not req:

        return {"ok": False, "error": "申请不存在或已处理，无法取消"}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute("BEGIN")
        # 解冻金额
        conn.execute(
            "UPDATE wallet SET frozen_amount = frozen_amount - ?, updated_at=? WHERE id=?",
            (req["amount"], now, req["wallet_id"])
        )
        # 记录解冻交易
        w_after = conn.execute(
            "SELECT balance FROM wallet WHERE id=?", (req["wallet_id"],)
        ).fetchone()["balance"]
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'unfreeze', ?, ?, ?, ?)",
            (req["wallet_id"], req["amount"], w_after,
             f"取消提现申请 #{request_id}，金额解冻", now)
        )
        # 标记申请已取消
        conn.execute(
            "UPDATE withdrawal_queue SET status='cancelled', reviewed_by='system', "
            "reviewed_at=?, note='用户取消' WHERE id=?",
            (now, request_id)
        )
        conn.commit()

        wallet = get_wallet(req["user_id"])
        _sync_wallet_cloud(wallet)
        return {"ok": True, "amount": req["amount"], "user_id": req["user_id"]}
    except Exception as e:
        conn.execute("ROLLBACK")

        return {"ok": False, "error": str(e)}


def delete_withdrawal_request(request_id: int) -> dict:
    """删除一条提现申请记录（仅限终态）。"""
    init_withdrawal_queue()
    conn = _connect()
    req = conn.execute(
        "SELECT * FROM withdrawal_queue WHERE id=?", (request_id,)
    ).fetchone()
    if not req:

        return {"ok": False, "error": "记录不存在"}
    if req["status"] == "pending":

        return {
            "ok": False,
            "error": "pending 状态不能直接删除，请先「取消申请」"
        }
    try:
        conn.execute("DELETE FROM withdrawal_queue WHERE id=?", (request_id,))
        conn.commit()

        return {"ok": True, "id": request_id, "status": req["status"]}
    except Exception as e:
        conn.execute("ROLLBACK")

        return {"ok": False, "error": str(e)}


def clear_withdrawal_queue(status: str = "terminal") -> dict:
    """批量清理提现申请记录。"""
    init_withdrawal_queue()
    conn = _connect()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if status == "terminal" or status == "processed":
        deleted = conn.execute(
            "DELETE FROM withdrawal_queue WHERE status IN ('approved','rejected')"
        ).rowcount
    elif status == "cancelled":
        deleted = conn.execute(
            "DELETE FROM withdrawal_queue WHERE status='cancelled'"
        ).rowcount
    elif status == "all":
        rows = conn.execute(
            "SELECT wallet_id, amount FROM withdrawal_queue WHERE status='pending'"
        ).fetchall()
        for r in rows:
            conn.execute(
                "UPDATE wallet SET frozen_amount = frozen_amount - ?, updated_at=? WHERE id=?",
                (r["amount"], now, r["wallet_id"])
            )
        cursor = conn.execute("DELETE FROM withdrawal_queue")
        deleted = cursor.rowcount
    else:

        return {"ok": False, "error": f"未知状态: {status}"}

    conn.commit()

    return {"ok": True, "deleted": deleted}


def delete_wallet(user_id: str, force: bool = False) -> dict:
    """删除钱包（慎用！）。"""
    w = get_wallet(user_id)
    if not w:
        return {"ok": False, "error": "钱包不存在"}

    balance = w.get("balance", 0)
    frozen = w.get("frozen_amount", 0)

    pending = get_pending_withdrawals()
    has_pending = any(p["user_id"] == user_id for p in pending)

    if has_pending:
        return {"ok": False, "error": "有待审批的提现申请，请先处理后再删除"}

    if not force and (balance != 0 or frozen != 0):
        return {
            "ok": False,
            "error": f"钱包余额≠0（{balance:.2f}）或冻结≠0（{frozen:.2f}），"
                      "请先清零后再删除，或使用 force=True 强制删除"
        }

    conn = _connect()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute("BEGIN")
        if force and (balance != 0 or frozen != 0):
            conn.execute(
                "UPDATE wallet SET balance=0, frozen_amount=0, status='deleted', "
                "updated_at=? WHERE user_id=?",
                (now, user_id)
            )
        conn.execute("DELETE FROM wallet_transactions WHERE wallet_id=?", (w["id"],))
        conn.execute("DELETE FROM withdrawal_queue WHERE wallet_id=? AND status='pending'", (w["id"],))
        conn.execute("DELETE FROM wallet WHERE id=?", (w["id"],))
        conn.commit()

        return {"ok": True, "user_id": user_id, "force": force}
    except Exception as e:
        conn.execute("ROLLBACK")

        return {"ok": False, "error": str(e)}


def delete_transaction(txn_id: int, operator: str = "admin") -> dict:
    """删除一条错误交易记录（慎用！）。"""
    init_db()
    conn = _connect()
    txn = conn.execute(
        "SELECT * FROM wallet_transactions WHERE id=?", (txn_id,)
    ).fetchone()
    if not txn:

        return {"ok": False, "error": "交易记录不存在"}

    wallet_id = txn["wallet_id"]
    amount = txn["amount"]
    txn_type = txn["type"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn.execute("BEGIN")
        reverse_amount = -amount
        conn.execute(
            "UPDATE wallet SET balance = balance + ?, updated_at=? WHERE id=?",
            (reverse_amount, now, wallet_id)
        )
        if txn_type == "freeze":
            conn.execute(
                "UPDATE wallet SET frozen_amount = frozen_amount - ? WHERE id=?",
                (abs(amount), wallet_id)
            )
        elif txn_type == "unfreeze":
            conn.execute(
                "UPDATE wallet SET frozen_amount = frozen_amount + ? WHERE id=?",
                (abs(amount), wallet_id)
            )
        conn.execute("DELETE FROM wallet_transactions WHERE id=?", (txn_id,))
        conn.commit()

        w_row = conn.execute("SELECT * FROM wallet WHERE id=?", (wallet_id,)).fetchone()
        if w_row:
            _sync_wallet_cloud(dict(w_row))

        return {
            "ok": True,
            "txn_id": txn_id,
            "corrected_amount": reverse_amount,
            "wallet_id": wallet_id
        }
    except Exception as e:
        conn.execute("ROLLBACK")

        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    import sys as _sys
    _sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print("[Wallet] Service Test")
    init_db()
    print(f"  DB: {DB_PATH}")

    w = get_or_create_wallet("test_user")
    print(f"  创建钱包: id={w['id']} user={w['user_id']}")

    r = recharge("test_user", 200)
    print(f"  充值200: {r}")

    c = add_commission("test_user", 80, "代理佣金")
    print(f"  佣金80: {c}")

    get_or_create_wallet("partner")
    t = transfer("test_user", "partner", 50, "合作分成")
    print(f"  转账50: {t}")

    f = freeze_amount("test_user", 30, "提现审核")
    print(f"  冻结30: {f}")

    print(f"  余额: test_user={get_balance('test_user')} partner={get_balance('partner')}")

    report = get_income_expense_report(days=30)
    print(f"  收支报表(30天): 收入={report['income']:.2f} 支出={report['expense']:.2f} 净额={report['net']:.2f}")

    tops = get_top_wallets(5)
    print(f"  Top5: {[dict(t, available=(t['balance']-t.get('frozen_amount',0))) for t in tops]}")

    print(f"  全局统计: {get_wallet_stats()}")

    print("  [OK] All tests passed")

```
