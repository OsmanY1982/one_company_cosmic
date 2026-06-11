"""
OPCclaw 智能提醒工具 — 主动预警与到期提醒

已有self_monitor只检测系统健康，此文件补充业务层面的主动提醒。
"""

import os, sqlite3
from datetime import datetime, timedelta


def check_expiring_members(data_dir: str, days: int = 7) -> dict:
    """检查即将到期的会员"""
    db_path = os.path.join(data_dir, "users.db")
    if not os.path.exists(db_path):
        return {"message": "无会员数据", "data": [], "alert": False}

    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in db.execute(
            "SELECT u.username, um.membership_type, um.expires_at "
            "FROM users u LEFT JOIN user_memberships um ON u.username=um.username "
            "WHERE um.membership_type IS NOT NULL "
            f"AND date(um.expires_at) <= date('now','+{days} days') "
            "ORDER BY um.expires_at ASC"
        ).fetchall()]
        alert = len(rows) > 0
        return {"message": f"{len(rows)} 位会员即将在{days}天内到期", "data": rows, "alert": alert}
    except Exception:
        return {"message": "会员查询异常", "data": [], "alert": False}
    finally:
        db.close()


def check_low_stock(data_dir: str, threshold: int = 10) -> dict:
    """检查低库存产品"""
    db_path = os.path.join(data_dir, "products.db")
    if not os.path.exists(db_path):
        return {"message": "无产品数据", "data": [], "alert": False}

    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in db.execute(
            f"SELECT name, price, stock, category FROM products WHERE stock <= {threshold} "
            "ORDER BY stock ASC"
        ).fetchall()]
        alert = len(rows) > 0
        return {"message": f"{len(rows)} 件产品库存低于{threshold}", "data": rows, "alert": alert}
    finally:
        db.close()


def check_pending_orders(data_dir: str, days: int = 3) -> dict:
    """检查超时未处理订单"""
    db_path = os.path.join(data_dir, "orders.db")
    if not os.path.exists(db_path):
        return {"message": "无订单数据", "data": [], "alert": False}

    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in db.execute(
            "SELECT order_no, customer_name, total_amount, status, created_at "
            f"FROM orders WHERE status='pending' AND created_at <= date('now','-{days} days') "
            "ORDER BY created_at ASC LIMIT 20"
        ).fetchall()]
        alert = len(rows) > 0
        return {"message": f"{len(rows)} 笔订单超{days}天未处理", "data": rows, "alert": alert}
    finally:
        db.close()


def check_overdue_payments(data_dir: str) -> dict:
    """检查逾期应收款"""
    db_path = os.path.join(data_dir, "orders.db")
    if not os.path.exists(db_path):
        return {"message": "无订单数据", "data": [], "alert": False}

    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in db.execute(
            "SELECT order_no, customer_name, total_amount, created_at "
            "FROM orders WHERE status NOT IN ('paid','completed','cancelled') "
            "AND total_amount > 0 AND created_at <= date('now','-30 days') "
            "ORDER BY created_at ASC LIMIT 20"
        ).fetchall()]
        total_due = sum(float(r.get("total_amount", 0)) for r in rows)
        alert = len(rows) > 0
        return {"message": f"{len(rows)}笔逾期应收，总计¥{total_due:.2f}", "data": rows, "alert": alert}
    finally:
        db.close()


def full_alert_scan(data_dir: str) -> dict:
    """一键扫描所有预警项"""
    alerts = []
    has_alert = False

    for check_fn in [check_expiring_members, check_low_stock, check_pending_orders, check_overdue_payments]:
        result = check_fn(data_dir)
        if result.get("alert"):
            has_alert = True
            alerts.append({"类型": result["message"], "数量": len(result.get("data", []))})

    return {"message": f"扫描完成: {'有' if has_alert else '无'}预警", "data": alerts, "alert": has_alert}


def register_alert_tools(registry, data_dir: str):
    from opcclaw.core.tool_registry import ToolDefinition

    registry.add_tool(ToolDefinition(
        name="check_expiring_members",
        description="检查即将到期会员（默认7天内）",
        parameters={"type": "object", "properties": {"days": {"type": "integer", "description": "天数，默认7"}}},
        handler=lambda days=7: check_expiring_members(data_dir, days),
    ))

    registry.add_tool(ToolDefinition(
        name="check_low_stock",
        description="检查低库存产品（默认库存<=10）",
        parameters={"type": "object", "properties": {"threshold": {"type": "integer", "description": "库存阈值，默认10"}}},
        handler=lambda threshold=10: check_low_stock(data_dir, threshold),
    ))

    registry.add_tool(ToolDefinition(
        name="check_pending_orders",
        description="检查超时未处理订单（默认超3天）",
        parameters={"type": "object", "properties": {"days": {"type": "integer", "description": "超时天数，默认3"}}},
        handler=lambda days=3: check_pending_orders(data_dir, days),
    ))

    registry.add_tool(ToolDefinition(
        name="check_overdue_payments",
        description="检查逾期应收款（超30天未付款）",
        parameters={"type": "object", "properties": {}},
        handler=lambda: check_overdue_payments(data_dir),
    ))

    registry.add_tool(ToolDefinition(
        name="full_alert_scan",
        description="一键扫描所有预警：会员到期/库存/订单/应收款",
        parameters={"type": "object", "properties": {}},
        handler=lambda: full_alert_scan(data_dir),
    ))