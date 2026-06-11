"""
自动化工作流工具 — 一键执行复杂业务流程

提供:
- 批量邮件发送
- 数据备份
- 定时任务模拟
- 报表自动导出
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional


class AutomationTools:
    """自动化工作流工具集"""
    
    def __init__(self, data_dir: str, templates_dir: str = None):
        self.data_dir = data_dir
        self.templates_dir = templates_dir or os.path.join(data_dir, "templates")
        os.makedirs(self.templates_dir, exist_ok=True)
    
    def _connect(self, db_name: str) -> Optional[sqlite3.Connection]:
        path = os.path.join(self.data_dir, db_name)
        if not os.path.exists(path):
            return None
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
        return conn
    
    def batch_email_customers(self, email_template: str, filter_type: str = "all", 
                              customer_level: str = None) -> Dict[str, Any]:
        """
        批量生成客户邮件
        
        Args:
            email_template: 邮件模板（使用 {name}, {company}, {product} 等占位符）
            filter_type: all|vip|recent 筛选类型
            customer_level: VIP|普通|潜在
        
        Returns:
            {"generated_count": int, "emails": [...], "preview": str}
        """
        db = self._connect("customer.db")
        if not db:
            return {"error": "客户数据库不存在"}
        
        try:
            # 构建查询条件
            if filter_type == "vip" or customer_level == "VIP":
                cursor = db.execute("SELECT * FROM customer WHERE level='VIP' LIMIT 50")
            elif filter_type == "recent":
                cursor = db.execute("SELECT * FROM customer ORDER BY created_at DESC LIMIT 20")
            else:
                cursor = db.execute("SELECT * FROM customer LIMIT 100")
            
            customers = [dict(row) for row in cursor]
            generated_emails = []
            
            for cust in customers:
                try:
                    email_content = email_template.format(
                        name=cust.get("name", "尊敬的客户"),
                        company=cust.get("company", "") or "",
                        phone=cust.get("phone", ""),
                        email=cust.get("email", ""),
                        level=cust.get("level", "") or "普通",
                        note=cust.get("note", ""),
                        greeting=self._get_personalized_greeting(cust.get("name", "")),
                    )
                    
                    filename = f"email_{cust.get('name', 'customer')}_{datetime.now().strftime('%Y%m%d')}.txt"
                    filepath = os.path.join(self.templates_dir, filename)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(email_content)
                    
                    generated_emails.append({
                        "customer": cust.get("name"),
                        "company": cust.get("company"),
                        "filepath": filepath,
                        "status": "success"
                    })
                except Exception as e:
                    generated_emails.append({
                        "customer": cust.get("name"),
                        "error": str(e),
                        "status": "failed"
                    })
            
            # 生成预览
            preview = generated_emails[0]["filepath"] if generated_emails else ""
            
            return {
                "total_customers": len(customers),
                "generated_count": sum(1 for e in generated_emails if e["status"] == "success"),
                "failed_count": sum(1 for e in generated_emails if e["status"] == "failed"),
                "output_dir": self.templates_dir,
                "emails": generated_emails[:10],  # 限制返回数量
                "preview_path": preview
            }
        finally:
            db.close()
    
    def _get_personalized_greeting(self, name: str) -> str:
        """根据时间获取个性化问候语"""
        hour = datetime.now().hour
        if hour < 6:
            return "祝您晚安"
        elif hour < 9:
            return "早上好"
        elif hour < 12:
            return "上午好"
        elif hour < 14:
            return "中午好"
        elif hour < 18:
            return "下午好"
        else:
            return "晚上好"
    
    def backup_all_databases(self, backup_dir: str = None) -> Dict[str, Any]:
        """
        备份所有数据库
        
        Returns:
            {"backed_up": [...], "failed": [...], "backup_path": str}
        """
        if backup_dir is None:
            backup_dir = os.path.join(self.data_dir, "backups", 
                                     datetime.now().strftime("%Y%m%d_%H%M%S"))
        
        os.makedirs(backup_dir, exist_ok=True)
        
        # 扫描 data 目录所有 .db 文件
        db_files = [f for f in os.listdir(self.data_dir) if f.endswith('.db')]
        
        backed_up = []
        failed = []
        
        for db_file in db_files:
            src_path = os.path.join(self.data_dir, db_file)
            dst_path = os.path.join(backup_dir, db_file)
            
            try:
                import shutil
                shutil.copy2(src_path, dst_path)
                backed_up.append({
                    "file": db_file,
                    "size": os.path.getsize(dst_path),
                    "dest": dst_path
                })
            except Exception as e:
                failed.append({
                    "file": db_file,
                    "error": str(e)
                })
        
        return {
            "total_databases": len(db_files),
            "backed_up_count": len(backed_up),
            "failed_count": len(failed),
            "backup_path": backup_dir,
            "files": backed_up,
            "errors": failed
        }
    
    def export_data_to_csv(self, db_name: str, table: str, 
                           output_dir: str = None) -> Dict[str, Any]:
        """
        导出数据为 CSV
        
        Returns:
            {"success": bool, "file_path": str, "row_count": int}
        """
        db = self._connect(db_name)
        if not db:
            return {"success": False, "error": f"数据库 {db_name} 不存在"}
        
        try:
            # 检查表是否存在
            cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not cursor.fetchone():
                return {"success": False, "error": f"表 {table} 不存在"}
            
            # 读取数据
            cursor = db.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            if output_dir is None:
                output_dir = self.data_dir
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table}_{timestamp}.csv"
            filepath = os.path.join(output_dir, filename)
            
            # 写入 CSV
            import csv
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                for row in rows:
                    writer.writerow(row)
            
            return {
                "success": True,
                "file_path": filepath,
                "row_count": len(rows),
                "columns": columns
            }
        finally:
            db.close()
    
    def generate_daily_summary(self) -> Dict[str, Any]:
        """
        生成每日摘要（多数据源综合）
        
        Returns:
            包含各模块今日数据的摘要字典
        """
        today = datetime.now().strftime('%Y-%m-%d')
        summary = {
            "date": today,
            "orders": {},
            "finance": {},
            "customers": {}
        }
        
        # 今日订单
        order_db = self._connect("orders.db")
        if order_db:
            try:
                cursor = order_db.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COALESCE(SUM(CASE WHEN status='paid' THEN total_amount ELSE 0 END), 0) as revenue
                    FROM orders 
                    WHERE DATE(created_at) = ?
                """, (today,))
                stats = cursor.fetchone()
                if stats:
                    summary["orders"] = {
                        "count": int(stats["total"]),
                        "revenue": float(stats["revenue"])
                    }
            finally:
                order_db.close()
        
        # 今日财务
        fin_db = self._connect("finance.db")
        if fin_db:
            try:
                cursor = fin_db.execute("""
                    SELECT 
                        SUM(CASE WHEN type='income' THEN amount ELSE 0 END) as income,
                        SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense
                    FROM finance 
                    WHERE DATE(date) = ?
                """, (today,))
                stats = cursor.fetchone()
                if stats:
                    summary["finance"] = {
                        "income": float(stats["income"] or 0),
                        "expense": float(stats["expense"] or 0),
                        "net": float((stats["income"] or 0) - (stats["expense"] or 0))
                    }
            finally:
                fin_db.close()
        
        # 今日新增客户
        cust_db = self._connect("customer.db")
        if cust_db:
            try:
                cursor = cust_db.execute("SELECT COUNT(*) FROM customer WHERE DATE(created_at) = ?", (today,))
                count = cursor.fetchone()[0]
                summary["customers"] = {"new_today": count}
            finally:
                cust_db.close()
        
        return summary
    
    def cleanup_old_records(self, days_threshold: int = 90, dry_run: bool = True) -> Dict[str, Any]:
        """
        清理过期记录（慎用！）
        
        Args:
            days_threshold: 保留最近多少天的数据
            dry_run: True 则只统计不删除
        
        Returns:
            {"to_delete": {...}, "action_taken": str}
        """
        cutoff_date = (datetime.now() - timedelta(days=days_threshold)).strftime('%Y-%m-%d')
        
        stats = {}
        
        # 查询可删除的订单（已取消且超过阈值）
        order_db = self._connect("orders.db")
        if order_db:
            try:
                cursor = order_db.execute("""
                    SELECT COUNT(*) FROM orders 
                    WHERE status='cancelled' AND DATE(created_at) < ?
                """, (cutoff_date,))
                stats["cancelled_orders"] = cursor.fetchone()[0]
            finally:
                order_db.close()
        
        if dry_run:
            return {
                "mode": "dry_run",
                "cutoff_date": cutoff_date,
                "would_delete": stats,
                "message": f"如需真正删除，请设置 dry_run=False"
            }
        else:
            # 真正的删除操作（需要额外确认）
            return {
                "mode": "execution",
                "message": "⚠️ 此操作不可逆！建议先备份数据"
            }


def register_automation_tools(registry, data_dir: str):
    """注册自动化工具到 ToolRegistry"""
    from opcclaw.core.tool_registry import ToolDefinition
    
    automator = AutomationTools(data_dir)
    
    registry.add_tool(ToolDefinition(
        name="batch_email_customers",
        description="批量生成客户邮件：基于模板和筛选条件生成多个客户邮件草稿",
        parameters={
            "type": "object",
            "properties": {
                "email_template": {"type": "string", "description": "邮件模板内容，支持占位符：{name}, {company}, {greeting}"},
                "filter_type": {"type": "string", "description": "筛选类型：all(全部)|vip(仅 VIP)|recent(最近)", "enum": ["all", "vip", "recent"]},
                "customer_level": {"type": "string", "description": "客户等级过滤：VIP|普通|潜在"}
            },
            "required": ["email_template"]
        },
        handler=lambda email_template, filter_type="all", customer_level=None: 
            automator.batch_email_customers(email_template, filter_type, customer_level),
    ))
    
    registry.add_tool(ToolDefinition(
        name="backup_all_databases",
        description="备份所有业务数据库到指定目录",
        parameters={
            "type": "object",
            "properties": {
                "backup_dir": {"type": "string", "description": "备份目录路径（可选，默认自动生成带时间戳的目录）"}
            }
        },
        handler=lambda backup_dir=None: automator.backup_all_databases(backup_dir),
    ))
    
    registry.add_tool(ToolDefinition(
        name="export_data_to_csv",
        description="将指定数据库表导出为 CSV 文件",
        parameters={
            "type": "object",
            "properties": {
                "db_name": {"type": "string", "description": "数据库文件名，如 orders.db"},
                "table": {"type": "string", "description": "表名"},
                "output_dir": {"type": "string", "description": "输出目录（可选）"}
            },
            "required": ["db_name", "table"]
        },
        handler=lambda db_name, table, output_dir=None: automator.export_data_to_csv(db_name, table, output_dir),
    ))
    
    registry.add_tool(ToolDefinition(
        name="generate_daily_summary",
        description="生成当日业务数据摘要：订单/财务/客户概览",
        parameters={
            "type": "object",
            "properties": {}
        },
        handler=lambda: automator.generate_daily_summary(),
    ))


# 辅助导入
from datetime import timedelta
