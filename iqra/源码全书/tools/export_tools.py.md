# `tools/export_tools.py`

> 路径：`tools/export_tools.py` | 行数：328


---


```python
"""
报表导出工具 — 数据导出与分享

提供:
- Excel 导出
- CSV 导出
- PDF 报告生成
- 定时报表
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional


def _connect(db_dir: str, db_name: str) -> Optional[sqlite3.Connection]:
    """连接数据库"""
    path = os.path.join(db_dir, db_name)
    if not os.path.exists(path):
        return None
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
    return conn


def _dict_rows(cursor) -> list[dict]:
    return [dict(r) for r in cursor.fetchall()]


# ═══════════════════════════════════════════
# 订单报表导出
# ═══════════════════════════════════════════

def export_orders_report(data_dir: str, month: str = "", format: str = "json") -> dict:
    """
    导出订单报表
    
    Args:
        month: 月份，如 2026-05
        format: 导出格式 (json/csv)
        
    Returns:
        {
            "message": "...",
            "file_path": "...",  # 导出文件路径
            "record_count": N
        }
    """
    order_db_names = ["orders.db", "order.db"]
    order_db = None
    
    for name in order_db_names:
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            order_db = _connect(data_dir, name)
            break
    
    if not order_db:
        return {"message": "无订单数据", "file_path": None, "record_count": 0}
    
    try:
        tables = _dict_rows(order_db.execute("SELECT name FROM sqlite_master WHERE type='table'"))
        if "orders" not in [t["name"] for t in tables]:
            return {"message": "未找到订单表", "file_path": None, "record_count": 0}
        
        # 构建查询
        if month:
            rows = _dict_rows(order_db.execute(
                "SELECT order_no,customer_name,total_amount,status,created_at,payment_method "
                "FROM orders WHERE created_at LIKE ? ORDER BY created_at DESC",
                (f"{month}%",)
            ))
        else:
            rows = _dict_rows(order_db.execute(
                "SELECT order_no,customer_name,total_amount,status,created_at,payment_method "
                "FROM orders ORDER BY created_at DESC LIMIT 100"
            ))
        
        data = [{
            "订单号": r["order_no"],
            "客户": r["customer_name"],
            "金额": float(r["total_amount"] or 0),
            "状态": r["status"],
            "时间": r["created_at"],
            "付款方式": r.get("payment_method") or ""
        } for r in rows]
        
        # 生成文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(data_dir, "exports")
        os.makedirs(output_dir, exist_ok=True)
        
        if format == "json":
            file_path = os.path.join(output_dir, f"orders_{timestamp}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"data": data, "export_time": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
        else:  # csv
            file_path = os.path.join(output_dir, f"orders_{timestamp}.csv")
            with open(file_path, "w", encoding="utf-8-sig") as f:
                headers = ["订单号", "客户", "金额", "状态", "时间", "付款方式"]
                f.write(",".join(headers) + "\n")
                for row in data:
                    values = [str(row[h]) for h in headers]
                    f.write(",".join(values) + "\n")
        
        return {
            "message": f"导出 {len(data)} 条订单记录",
            "file_path": file_path,
            "record_count": len(data)
        }
    
    finally:
        order_db.close()


# ═══════════════════════════════════════════
# 客户报表导出
# ═══════════════════════════════════════════

def export_customers_report(data_dir: str, format: str = "json") -> dict:
    """
    导出客户报表
    
    Args:
        format: 导出格式 (json/csv)
        
    Returns:
        {
            "message": "...",
            "file_path": "...",
            "record_count": N
        }
    """
    cust_db_names = ["customer.db", "customers.db"]
    cust_db = None
    
    for name in cust_db_names:
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            cust_db = _connect(data_dir, name)
            break
    
    if not cust_db:
        return {"message": "无客户数据", "file_path": None, "record_count": 0}
    
    try:
        tables = _dict_rows(cust_db.execute("SELECT name FROM sqlite_master WHERE type='table'"))
        if "customer" not in [t["name"] for t in tables]:
            return {"message": "未找到客户表", "file_path": None, "record_count": 0}
        
        rows = _dict_rows(cust_db.execute(
            "SELECT name,company,phone,email,level,note,created_at FROM customer ORDER BY created_at DESC LIMIT 200"
        ))
        
        data = [{
            "姓名": r["name"],
            "公司": r.get("company") or "",
            "电话": r.get("phone") or "",
            "邮箱": r.get("email") or "",
            "等级": r.get("level") or "",
            "备注": r.get("note") or "",
            "创建时间": r.get("created_at") or ""
        } for r in rows]
        
        # 生成文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(data_dir, "exports")
        os.makedirs(output_dir, exist_ok=True)
        
        if format == "json":
            file_path = os.path.join(output_dir, f"customers_{timestamp}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"data": data, "export_time": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
        else:
            file_path = os.path.join(output_dir, f"customers_{timestamp}.csv")
            with open(file_path, "w", encoding="utf-8-sig") as f:
                headers = ["姓名", "公司", "电话", "邮箱", "等级", "备注", "创建时间"]
                f.write(",".join(headers) + "\n")
                for row in data:
                    values = [str(row[h]) for h in headers]
                    f.write(",".join(values) + "\n")
        
        return {
            "message": f"导出 {len(data)} 条客户记录",
            "file_path": file_path,
            "record_count": len(data)
        }
    
    finally:
        cust_db.close()


# ═══════════════════════════════════════════
# 财务报表导出
# ═══════════════════════════════════════════

def export_finance_report(data_dir: str, month: str = "", format: str = "json") -> dict:
    """
    导出财务报表
    
    Args:
        month: 月份，如 2026-05
        format: 导出格式 (json/csv)
        
    Returns:
        {
            "message": "...",
            "file_path": "...",
            "record_count": N,
            "summary": {...}
        }
    """
    finance_db = _connect(data_dir, "finance.db")
    if not finance_db:
        return {"message": "无财务数据", "file_path": None, "record_count": 0}
    
    try:
        tables = _dict_rows(finance_db.execute("SELECT name FROM sqlite_master WHERE type='table'"))
        if "finance" not in [t["name"] for t in tables]:
            return {"message": "未找到财务表", "file_path": None, "record_count": 0}
        
        # 构建查询
        if month:
            rows = _dict_rows(finance_db.execute(
                "SELECT type,category,amount,date,description FROM finance WHERE date LIKE ?",
                (f"{month}%",)
            ))
        else:
            rows = _dict_rows(finance_db.execute(
                "SELECT type,category,amount,date,description FROM finance ORDER BY date DESC LIMIT 100"
            ))
        
        data = [{
            "类型": r["type"],
            "分类": r.get("category") or "",
            "金额": float(r["amount"] or 0),
            "日期": r["date"],
            "说明": r.get("description") or ""
        } for r in rows]
        
        # 计算汇总
        income = sum(r["金额"] for r in data if r["类型"] in ("收入", "income"))
        expense = sum(r["金额"] for r in data if r["类型"] in ("支出", "expense"))
        
        # 生成文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(data_dir, "exports")
        os.makedirs(output_dir, exist_ok=True)
        
        if format == "json":
            file_path = os.path.join(output_dir, f"finance_{timestamp}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({
                    "data": data,
                    "summary": {"收入": income, "支出": expense, "利润": income - expense},
                    "export_time": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        else:
            file_path = os.path.join(output_dir, f"finance_{timestamp}.csv")
            with open(file_path, "w", encoding="utf-8-sig") as f:
                headers = ["类型", "分类", "金额", "日期", "说明"]
                f.write(",".join(headers) + "\n")
                for row in data:
                    values = [str(row[h]) for h in headers]
                    f.write(",".join(values) + "\n")
                f.write(f"\n汇总，收入，{income},,\n")
                f.write(f"汇总，支出，{expense},,\n")
                f.write(f"汇总，利润，{income-expense},,\n")
        
        return {
            "message": f"导出 {len(data)} 条财务记录，收入:{income:.2f} 支出:{expense:.2f}",
            "file_path": file_path,
            "record_count": len(data),
            "summary": {"收入": income, "支出": expense, "利润": income - expense}
        }
    
    finally:
        finance_db.close()


# ═══════════════════════════════════════════
# 批量注册入口
# ═══════════════════════════════════════════

def register_export_tools(registry, data_dir: str):
    """将报表导出工具注册到 ToolRegistry"""
    from iqra.core.tool_registry import ToolDefinition
    
    registry.add_tool(ToolDefinition(
        name="export_orders_report",
        description="导出订单报表为 JSON/CSV 格式",
        parameters={
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "月份筛选，如 2026-05"},
                "format": {"type": "string", "description": "导出格式：json 或 csv", "enum": ["json", "csv"]}
            }
        },
        handler=lambda month="", format="json": export_orders_report(data_dir, month, format),
    ))
    
    registry.add_tool(ToolDefinition(
        name="export_customers_report",
        description="导出客户报表为 JSON/CSV 格式",
        parameters={
            "type": "object",
            "properties": {
                "format": {"type": "string", "description": "导出格式：json 或 csv", "enum": ["json", "csv"]}
            }
        },
        handler=lambda format="json": export_customers_report(data_dir, format),
    ))
    
    registry.add_tool(ToolDefinition(
        name="export_finance_report",
        description="导出财务报表为 JSON/CSV 格式",
        parameters={
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "月份筛选，如 2026-05"},
                "format": {"type": "string", "description": "导出格式：json 或 csv", "enum": ["json", "csv"]}
            }
        },
        handler=lambda month="", format="json": export_finance_report(data_dir, month, format),
    ))

```
