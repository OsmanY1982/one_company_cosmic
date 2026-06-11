# `tools/procurement_tools.py`

> 路径：`tools/procurement_tools.py` | 行数：73


---


```python
"""采购供应链工具 — 供应商管理、采购订单、物流跟踪"""

import os, sqlite3
from datetime import datetime, timedelta

class ProcurementTools:
    def __init__(self, data_dir): self.data_dir = data_dir
    def _connect(self, db_name):
        path = os.path.join(self.data_dir, db_name)
        if not os.path.exists(path): return None
        conn = sqlite3.connect(path); conn.row_factory = sqlite3.Row; conn.text_factory = lambda x: str(x,'utf-8','replace')
        return conn

    def inventory_alert_report(self) -> dict:
        """库存预警报告"""
        db = self._connect("products.db")
        if not db: return {"error": "产品库不存在"}
        try:
            products = [dict(r) for r in db.execute("SELECT * FROM products").fetchall()]
            
            low_stock = [p for p in products if int(p.get("stock",999)) < 20]
            out_of_stock = [p for p in products if int(p.get("stock",0)) == 0]
            over_stock = [p for p in products if int(p.get("stock",0)) > 500]
            
            total_value = sum(float(p.get("price",0)) * int(p.get("stock",0)) for p in products)
            
            alerts = []
            for p in out_of_stock[:5]:
                alerts.append(f"🚫 [{p['name']}] 已断货！需紧急补货")
            for p in low_stock[:5]:
                alerts.append(f"⚠️ [{p['name']}] 库存仅剩{p['stock']}件")
            
            return {
                "total_products": len(products),
                "out_of_stock": len(out_of_stock),
                "low_stock": len(low_stock),
                "over_stock": len(over_stock),
                "total_inventory_value": round(total_value, 2),
                "alerts": alerts[:10],
                "recommendations": [f"📦 当前库存总值¥{total_value:.2f}",
                    f"⚡ 需优先处理{len(out_of_stock)}个断货商品",
                    "🔄 建议设置自动补货触发阈值"]
            }
        finally: db.close()

    def supplier_analysis(self) -> dict:
        """供应商分析（基于产品类别推断）"""
        db = self._connect("products.db")
        if not db: return {"error": "产品库不存在"}
        try:
            products = [dict(r) for r in db.execute("SELECT category, COUNT(*) as cnt FROM products GROUP BY category").fetchall()]
            
            categories = {}
            for p in products:
                cat = p.get("category","其他") or "其他"
                categories[cat] = categories.get(cat,0) + int(p["cnt"])
            
            return {
                "categories": categories,
                "category_count": len(categories),
                "recommendations": ["📋 按品类建立专属供应商库",
                    f"🏷️ 共{len(categories)}个品类，建议每个品类2-3家备用供应商",
                    "📊 定期评估供应商交货准时率和质量合格率"]
            }
        finally: db.close()


def register_procurement_tools(registry, data_dir):
    from opcclaw.core.tool_registry import ToolDefinition
    pm = ProcurementTools(data_dir)
    registry.add_tool(ToolDefinition(name="inventory_alert_report", description="库存预警报告：断货/低库存/滞销商品统计及补货建议", parameters={"type":"object","properties":{}}, handler=lambda: pm.inventory_alert_report()))
    registry.add_tool(ToolDefinition(name="supplier_analysis", description="供应商分析：按品类统计供应商覆盖情况", parameters={"type":"object","properties":{}}, handler=lambda: pm.supplier_analysis()))


```
