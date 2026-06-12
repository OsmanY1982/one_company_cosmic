# `opcclaw/tools/project_management.py`

> 路径：`opcclaw/tools/project_management.py` | 行数：160


---


```python
"""项目管理工具 — 任务跟踪、进度监控、资源分配、风险预警"""

import os, json
from datetime import datetime, timedelta

class ProjectManagementTools:
    def __init__(self, data_dir): self.data_dir = data_dir
    
    def get_project_status(self, project_id=None) -> dict:
        """获取项目状态"""
        projects_file = os.path.join(self.data_dir, "projects.json")
        if not os.path.exists(projects_file):
            return {"error": "项目数据文件不存在"}
        
        with open(projects_file, 'r', encoding='utf-8') as f:
            projects = json.load(f)
        
        if project_id:
            project = next((p for p in projects if p.get("id") == project_id), None)
            if not project: return {"error": f"未找到项目 {project_id}"}
            return self._analyze_single_project(project)
        
        # 分析所有项目
        analysis = {
            "total_projects": len(projects),
            "by_status": {},
            "overdue_count": 0,
            "high_risk_count": 0,
            "summary": []
        }
        
        for p in projects:
            status = p.get("status", "进行中")
            analysis["by_status"][status] = analysis["by_status"].get(status, 0) + 1
            
            # 检查逾期
            end_date = p.get("end_date")
            if end_date and end_date < datetime.now().strftime("%Y-%m-%d"):
                if status != "已完成":
                    analysis["overdue_count"] += 1
            
            # 风险评估
            risk = self._calculate_risk(p)
            if risk > 0.7:
                analysis["high_risk_count"] += 1
        
        analysis["summary"] = [
            f"总项目数：{analysis['total_projects']}",
            f"进行中：{analysis['by_status'].get('进行中', 0)}",
            f"已完成：{analysis['by_status'].get('已完成', 0)}",
            f"逾期项目：{analysis['overdue_count']}",
            f"高风险项目：{analysis['high_risk_count']}"
        ]
        
        return analysis
    
    def _analyze_single_project(self, project):
        """分析单个项目"""
        start = project.get("start_date")
        end = project.get("end_date")
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 计算进度
        tasks = project.get("tasks", [])
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        progress = len(completed_tasks) / len(tasks) if tasks else 0
        
        # 计算时间进度
        if start and end:
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            end_dt = datetime.strptime(end, "%Y-%m-%d")
            total_days = (end_dt - start_dt).days
            elapsed_days = (datetime.now() - start_dt).days
            time_progress = min(elapsed_days / total_days, 1) if total_days > 0 else 0
        else:
            time_progress = 0
        
        # 风险评估
        risk_score = self._calculate_risk(project)
        risk_level = "🟢 低" if risk_score < 0.3 else "🟡 中" if risk_score < 0.7 else "🔴 高"
        
        # 关键路径（最晚完成的任务）
        incomplete_tasks = [t for t in tasks if t.get("status") != "completed"]
        if incomplete_tasks:
            latest_task = max(incomplete_tasks, key=lambda x: x.get("due_date", "2099-12-31"))
            critical_path = latest_task.get("name", "未知")
        else:
            critical_path = "无"
        
        return {
            "project_name": project.get("name"),
            "status": project.get("status"),
            "progress_pct": round(progress * 100, 1),
            "time_progress_pct": round(time_progress * 100, 1),
            "risk_level": risk_level,
            "risk_score": round(risk_score, 2),
            "critical_path": critical_path,
            "overdue": end and end < today and project.get("status") != "已完成",
            "team_size": len(project.get("team", [])),
            "budget_used": project.get("budget_used", 0),
            "total_budget": project.get("budget", 0),
            "recommendations": self._project_recommendations(project, progress, time_progress, risk_score)
        }
    
    def _calculate_risk(self, project):
        """计算项目风险分数 (0-1)"""
        score = 0.0
        
        # 进度落后
        tasks = project.get("tasks", [])
        if tasks:
            completed = len([t for t in tasks if t.get("status") == "completed"])
            progress = completed / len(tasks)
            if progress < 0.5:
                score += 0.3
        
        # 时间逾期
        end_date = project.get("end_date")
        if end_date and end_date < datetime.now().strftime("%Y-%m-%d"):
            if project.get("status") != "已完成":
                score += 0.4
        
        # 资源不足
        team_size = len(project.get("team", []))
        if team_size == 0:
            score += 0.2
        
        # 预算超支
        budget = project.get("budget", 0)
        used = project.get("budget_used", 0)
        if budget > 0 and used / budget > 1.2:
            score += 0.3
        
        return min(score, 1.0)
    
    def _project_recommendations(self, project, progress, time_progress, risk_score):
        recs = []
        
        if progress < time_progress - 0.2:
            recs.append("⚠️ 进度落后于时间计划，需加快执行")
        elif progress > time_progress + 0.2:
            recs.append("✅ 进度超前，可考虑优化资源分配")
        
        if risk_score > 0.7:
            recs.append("🚨 高风险项目，建议立即召开风险评估会议")
        elif risk_score > 0.4:
            recs.append("🟡 中等风险，需加强监控和沟通")
        
        if project.get("budget_used", 0) > project.get("budget", 0) * 0.9:
            recs.append("💰 预算接近上限，需控制后续支出")
        
        recs.append("📊 建议每周更新项目状态，及时调整计划")
        return recs


def register_project_management_tools(registry, data_dir):
    from opcclaw.core.tool_registry import ToolDefinition
    pm = ProjectManagementTools(data_dir)
    registry.add_tool(ToolDefinition(name="get_project_status", description="项目状态分析：进度/风险/预算/关键路径/优化建议", parameters={"type":"object","properties":{"project_id":{"type":"string"}}}, handler=lambda project_id="": pm.get_project_status(project_id)))


```
