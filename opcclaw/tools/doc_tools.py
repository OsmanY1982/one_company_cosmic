"""文档处理工具 — 报告生成、模板填充、数据导出"""

import os, json, csv, sqlite3
from datetime import datetime

class DocTools:
    def __init__(self, data_dir): self.data_dir = data_dir
    def _connect(self, db_name):
        path = os.path.join(self.data_dir, db_name)
        if not os.path.exists(path): return None
        conn = sqlite3.connect(path); conn.row_factory = sqlite3.Row; conn.text_factory = lambda x: str(x,'utf-8','replace')
        return conn

    def generate_monthly_report(self, month=None) -> str:
        """生成月度业务总结报告（Markdown）"""
        if not month: month = datetime.now().strftime("%Y-%m")
        lines = [f"# 📊 {month}月度业务报告", f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
        
        # 订单数据
        orders_db = self._connect("orders.db")
        if orders_db:
            try:
                row = orders_db.execute("""SELECT COUNT(*) as c, COALESCE(SUM(total_amount),0) as rev 
                    FROM orders WHERE created_at LIKE ?""", (f"{month}%",)).fetchone()
                if row:
                    lines.append(f"## 1️⃣ 销售数据\n- 订单数：{row['c']}\n- 营收：¥{float(row['rev']) or 0:.2f}")
            finally: orders_db.close()
        
        # 客户数据
        cust_db = self._connect("customer.db")
        if cust_db:
            try:
                cnt = cust_db.execute("SELECT COUNT(*) FROM customer WHERE created_at LIKE ?", (f"{month}%",)).fetchone()[0]
                lines.append(f"\n## 2️⃣ 客户增长\n- 新增客户：{cnt}人")
            finally: cust_db.close()
        
        # 产品库存
        prod_db = self._connect("products.db")
        if prod_db:
            try:
                total = prod_db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
                low = prod_db.execute("SELECT COUNT(*) FROM products WHERE stock < 20").fetchone()[0]
                lines.append(f"\n## 3️⃣ 库存状况\n- 商品总数：{total}\n- 低库存预警：{low}款")
            finally: prod_db.close()
        
        # 财务数据
        fin_db = self._connect("finance.db")
        if fin_db:
            try:
                rows = fin_db.execute("""SELECT COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE 0 END),0) as inc,
                    COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END),0) as exp
                    FROM finance WHERE date LIKE ?""", (f"{month}%",)).fetchone()
                inc = float(rows["inc"]) if rows else 0
                exp = float(rows["exp"]) if rows else 0
                lines.append(f"\n## 4️⃣ 财务状况\n- 收入：¥{inc:.2f}\n- 支出：¥{exp:.2f}\n- 利润：¥{inc-exp:.2f}")
            finally: fin_db.close()
        
        lines.extend(["\n---\n*OPCclaw AI自动生成*"])
        return "\n".join(lines)

    def export_table_to_csv(self, table: str, output_path: str = None) -> dict:
        """导出数据库表为CSV"""
        for db in ["products","orders","customer","staff"]:
            con = self._connect(db)
            if not con: continue
            try:
                curs = con.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if not curs.fetchone(): continue
                
                curs = con.execute(f"SELECT * FROM {table}")
                cols = [d[0] for d in curs.description]
                rows = curs.fetchall()
                
                if not output_path:
                    output_path = os.path.join(self.data_dir, f"{table}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
                
                with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                    w = csv.writer(f); w.writerow(cols)
                    for r in rows: w.writerow(r)
                
                return {"success": True, "path": output_path, "rows": len(rows), "columns": cols}
            finally: con.close()
        
        return {"error": f"未找到表 '{table}'"}


def register_doc_tools(registry, data_dir):
    from opcclaw.core.tool_registry import ToolDefinition
    dt = DocTools(data_dir)
    registry.add_tool(ToolDefinition(name="generate_monthly_report", description="生成月度业务报告(Markdown格式)，包含销售/客户/库存/财务四大部分", parameters={"type":"object","properties":{"month":{"type":"string"}}}, handler=lambda month="": dt.generate_monthly_report(month)))
    registry.add_tool(ToolDefinition(name="export_table_to_csv", description="导出指定数据库表为CSV文件", parameters={"type":"object","properties":{"table":{"type":"string"},"output_path":{"type":"string"}}}, handler=lambda table="", output_path="": dt.export_table_to_csv(table, output_path)))

