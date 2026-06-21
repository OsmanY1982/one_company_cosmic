# -*- coding: utf-8 -*-
"""
每日早报生成器 — 自动汇总经营数据、异常告警、知识库状态
"""

from datetime import datetime
from typing import Dict, Optional


def generate_briefing() -> Dict:
    """
    生成当日早报。

    Returns:
        {
            "title": str,
            "date": str,
            "sections": [{"title": str, "lines": [str], "icon": str}],
            "plain_text": str,
            "has_alerts": bool,
        }
    """
    now = datetime.now()
    sections = []
    has_alerts = False

    # ── 1. 经营摘要 ──
    sales_lines = []
    inv_lines = []
    fin_lines = []
    try:
        from modules.intelligence.report_generator import ReportGenerator
        gen = ReportGenerator()
        sales = gen.generate_sales_report("daily")
        inventory = gen.generate_inventory_report()
        finance = gen.generate_finance_report("monthly")

        s = sales.get("summary", {})
        sales_lines.append(f'今日订单 {s.get("total_orders",0)} 单 · 金额 ¥{s.get("total_amount",0):,.0f}')

        inv = inventory.get("summary", {})
        low = inv.get("low_stock_count", 0)
        inv_lines.append(f'{inv.get("total_products",0)} 款在售')
        if low > 0:
            inv_lines.append(f'低库存预警 {low} 款')
        for item in inventory.get("low_stock_items", [])[:3]:
            inv_lines.append(f'  {item.get("name","?")} — 仅剩 {item.get("stock",0)} 件')

        f_sum = finance.get("summary", {})
        profit = f_sum.get("income", 0) - f_sum.get("expense", 0)
        fin_lines.append(f'本月收入 ¥{f_sum.get("income",0):,.0f} · 支出 ¥{f_sum.get("expense",0):,.0f}')
        fin_lines.append(f'本月利润 ¥{profit:,.0f}')

        sections.append({"title": "经营", "lines": sales_lines + inv_lines + fin_lines, "icon": "chart"})
    except Exception:
        sections.append({"title": "经营", "lines": ["数据暂不可用"], "icon": "chart"})

    # ── 2. 异常告警 ──
    alert_lines = []
    try:
        from modules.intelligence.anomaly_detector import AnomalyDetector
        detector = AnomalyDetector()
        anomalies = detector.detect_all()
        all_items = anomalies.get("anomalies", [])
        critical = [a for a in all_items if a.get("severity") == "critical"]
        warnings = [a for a in all_items if a.get("severity") == "warning"]
        for a in critical[:5]:
            alert_lines.append(f'[严重] {a.get("type","")}: {a.get("message", a.get("description",""))}')
        for a in warnings[:5]:
            alert_lines.append(f'[预警] {a.get("type","")}: {a.get("message", a.get("description",""))}')
        if critical:
            has_alerts = True
        if not alert_lines:
            alert_lines.append("无异常")
    except Exception:
        alert_lines.append("检测服务不可用")

    sections.append({"title": "异常", "lines": alert_lines, "icon": "alert"})

    # ── 3. 知识库状态 ──
    kb_lines = []
    try:
        from modules.intelligence.knowledge_base import knowledge_base
        doc_count = len(knowledge_base.documents)
        vocab = len(knowledge_base.vector_store.vocabulary) if knowledge_base.vector_store else 0
        kb_lines.append(f'{doc_count} 篇文档 · {vocab} 词向量')
    except Exception:
        kb_lines.append("不可用")
    sections.append({"title": "知识库", "lines": kb_lines, "icon": "book"})

    # ── 生成纯文本 ──
    plain_lines = [f"iqra 每日早报 · {now.strftime('%Y-%m-%d %A')}", "=" * 36]
    for sec in sections:
        plain_lines.append(f"\n  {sec['title']}:")
        for line in sec["lines"]:
            plain_lines.append(f"    {line}")

    return {
        "title": f"每日早报 · {now.strftime('%m/%d %A')}",
        "date": now.strftime("%Y-%m-%d %H:%M"),
        "sections": sections,
        "plain_text": "\n".join(plain_lines),
        "has_alerts": has_alerts,
    }


def generate_briefing_html() -> str:
    """生成 HTML 格式早报，适合悬浮球弹窗展示"""
    data = generate_briefing()
    lines = [
        f'<div style="font-size:13px;font-weight:bold;color:#88ccff;margin-bottom:4px;">{data["title"]}</div>',
    ]
    for sec in data["sections"]:
        icon_map = {"chart": "chart", "alert": "alert", "book": "book"}
        ico = icon_map.get(sec.get("icon", ""), "")
        lines.append(
            f'<div style="color:#ccaaff;font-size:10px;font-weight:bold;margin:6px 0 2px;">{sec["title"]}</div>'
        )
        for line in sec["lines"]:
            color = "#ddccff"
            if "[严重]" in line:
                color = "#ff6644"
            elif "[预警]" in line:
                color = "#ffaa44"
            lines.append(
                f'<div style="color:{color};font-size:9px;margin:0 0 0 6px;">{line}</div>'
            )
    lines.append(
        f'<div style="color:#666688;font-size:8px;margin-top:8px;">{data["date"]}</div>'
    )
    return "".join(lines)
