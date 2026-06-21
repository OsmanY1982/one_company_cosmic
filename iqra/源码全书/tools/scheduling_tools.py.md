# `tools/scheduling_tools.py`

> 路径：`tools/scheduling_tools.py` | 行数：75


---


```python
"""日程管理工具 — 会议安排、提醒、日历统计"""

import os, sqlite3, json
from datetime import datetime, timedelta
from collections import Counter

class SchedulingTools:
    def __init__(self, data_dir): self.data_dir = data_dir
    
    def get_upcoming_events(self, days_ahead=7) -> dict:
        """获取未来日程"""
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        events_file = os.path.join(self.data_dir, "schedule.json")
        events = []
        
        if os.path.exists(events_file):
            with open(events_file, 'r', encoding='utf-8') as f:
                try:
                    events = json.load(f)
                except: events = []
        
        # 过滤未来日程
        upcoming = [e for e in events 
                   if isinstance(e.get("date"), str) 
                   and e["date"][:10] >= today.isoformat()
                   and e["date"][:10] <= end_date.isoformat()]
        
        return {
            "period": f"{today.isoformat()} ~ {end_date.isoformat()}",
            "total_events": len(upcoming),
            "events": sorted(upcoming, key=lambda x: x.get("date", ""))[:10],
            "empty_days": self._find_empty_days(events, today, end_date)
        }
    
    def _find_empty_days(self, events, start, end):
        all_dates = [(start + timedelta(days=i)).isoformat() for i in range((end-start).days+1)]
        busy_dates = set(e["date"][:10] for e in events if e.get("date"))
        return [d for d in all_dates if d not in busy_dates][:5]
    
    def schedule_summary(self) -> dict:
        """周/月日程概览"""
        events_file = os.path.join(self.data_dir, "schedule.json")
        events = []
        
        if os.path.exists(events_file):
            with open(events_file, 'r', encoding='utf-8') as f:
                try: events = json.load(f)
                except: pass
        
        # 分类统计
        by_type = Counter(e.get("type", "其他") for e in events if e.get("date", "").startswith(datetime.now().strftime("%Y-%m")))
        by_priority = Counter(e.get("priority", "中") for e in events)
        
        urgent = [e for e in events if e.get("priority") == "高" and e.get("date", "")[:10] >= datetime.now().strftime("%Y-%m-%d")]
        
        return {
            "total_scheduled": len([e for e in events if e.get("date", "").startswith(datetime.now().strftime("%Y-%m"))]),
            "by_type": dict(by_type),
            "by_priority": dict(by_priority),
            "urgent_tasks": len(urgent),
            "urgent_list": [{"title": e.get("title",""), "date": e["date"][:10]} for e in urgent[:5]],
            "recommendations": ["📅 建议每天早上查看今日日程",
                f"⚠️ 有{len(urgent)}项高优先级任务待处理",
                "📊 建议每周一制定本周计划"]
        }


def register_scheduling_tools(registry, data_dir):
    from iqra.core.tool_registry import ToolDefinition
    s = SchedulingTools(data_dir)
    registry.add_tool(ToolDefinition(name="get_upcoming_events", description="获取未来几天日程安排", parameters={"type":"object","properties":{"days_ahead":{"type":"integer","default":7}}}, handler=lambda days_ahead=7: s.get_upcoming_events(days_ahead)))
    registry.add_tool(ToolDefinition(name="schedule_summary", description="日程概览：本周事件/类型分布/紧急事项提醒", parameters={"type":"object","properties":{}}, handler=lambda: s.schedule_summary()))


```
