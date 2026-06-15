# `opcclaw/core/impeccable/__init__.py`

> 路径：`opcclaw/core/impeccable/__init__.py` | 行数：190


---


```python
"""
Impeccable — opcclaw 设计审计引擎

自动审查代码架构质量：模块耦合度、循环依赖、SOLID 原则违规、复杂度热点。

Usage:
    from opcclaw.core.impeccable import audit, AuditReport

    report = audit("/path/to/project")
    print(report.get_grade())          # "B"
    print(report.get_violations()[:3]) # TOP 3 违规
    report.generate_report("markdown") # 生成 Markdown 报告
"""

import os
import sys
from typing import Dict, Any, List, Optional


class AuditReport:
    """审计报告对象。"""

    def __init__(self, root_dir: str,
                 complexity_data: Dict[str, Any],
                 coupling_data: Dict[str, Any],
                 solid_data: Optional[Dict[str, Any]] = None):
        self.root_dir = root_dir
        self.complexity_data = complexity_data
        self.coupling_data = coupling_data
        self.solid_data = solid_data or {}

        # 计算评分
        self.score = self._compute_score()
        self.violations = self._collect_violations()
        self.suggestions = self._generate_suggestions()

    def _compute_score(self) -> float:
        score = 100.0
        hotspots = self.complexity_data.get("hotspots", [])
        score -= min(len(hotspots) * 2, 30)
        cycles = self.coupling_data.get("cyclic_deps", [])
        score -= min(len(cycles) * 8, 24)
        unstable = self.coupling_data.get("unstable", [])
        score -= min(len(unstable) * 3, 15)
        gods = self.coupling_data.get("god_objects", [])
        score -= min(len(gods) * 5, 10)
        for key, weight in [("s", 1), ("o", 1), ("l", 1), ("i", 1), ("d", 0.5)]:
            viols = self.solid_data.get(key, [])
            score -= min(len(viols) * weight, 10)
        return max(0.0, round(score, 1))

    def get_grade(self) -> str:
        if self.score >= 90:
            return "A"
        elif self.score >= 80:
            return "B"
        elif self.score >= 70:
            return "C"
        elif self.score >= 60:
            return "D"
        elif self.score >= 40:
            return "E"
        else:
            return "F"

    def _collect_violations(self) -> List[Dict[str, Any]]:
        violations = []

        # 复杂度热点
        for h in self.complexity_data.get("hotspots", []):
            violations.append({
                "type": "complexity_hotspot",
                "severity": "high" if h["cyclomatic"] > 20 else "medium",
                "file": h["file"],
                "location": f"{h['name']} (line {h['line']})",
                "detail": f"圈复杂度 {h['cyclomatic']}，认知复杂度 {h['cognitive']}",
            })

        # 循环依赖
        for cycle in self.coupling_data.get("cyclic_deps", []):
            violations.append({
                "type": "cyclic_dependency",
                "severity": "high",
                "location": " → ".join(cycle),
                "detail": f"循环依赖环: {len(cycle)} 个模块",
            })

        # 不稳定模块
        for mod_name, inst in self.coupling_data.get("unstable", []):
            violations.append({
                "type": "unstable_module",
                "severity": "medium",
                "location": mod_name,
                "detail": f"不稳定指数 I={inst}",
            })

        # 上帝对象
        for fp, lines, methods in self.coupling_data.get("god_objects", []):
            violations.append({
                "type": "god_object",
                "severity": "medium",
                "file": fp,
                "detail": f"{lines} 行，{methods} 个方法",
            })

        return violations

    def _generate_suggestions(self) -> List[str]:
        suggestions = []
        hotspots = self.complexity_data.get("hotspots", [])
        if hotspots:
            suggestions.append(f"降低复杂度: {len(hotspots)} 个函数圈复杂度 > 15，考虑拆分大函数")
        cycles = self.coupling_data.get("cyclic_deps", [])
        if cycles:
            suggestions.append(f"打破循环依赖: 发现 {len(cycles)} 个循环依赖环")
        unstable = self.coupling_data.get("unstable", [])
        if unstable:
            suggestions.append(f"稳定化模块: {len(unstable)} 个模块 I > 0.7")
        gods = self.coupling_data.get("god_objects", [])
        if gods:
            suggestions.append(f"拆分上帝对象: {len(gods)} 个文件 > 1000 行且 > 30 方法")
        if not suggestions:
            suggestions.append("当前代码架构质量良好")
        return suggestions

    def get_violations(self, sort_by: str = "severity") -> List[Dict[str, Any]]:
        severity_order = {"high": 0, "medium": 1, "low": 2}
        if sort_by == "severity":
            return sorted(self.violations, key=lambda v: severity_order.get(v.get("severity", "low"), 99))
        return self.violations

    def generate_report(self, fmt: str = "markdown") -> str:
        if fmt == "markdown":
            from .report_generator import generate_report
            return generate_report(
                complexity_data=self.complexity_data,
                coupling_data=self.coupling_data,
                solid_data=self.solid_data,
            )
        return ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "grade": self.get_grade(),
            "violations": self.violations,
            "suggestions": self.suggestions,
        }


def audit(root_dir: str) -> AuditReport:
    """
    对指定项目目录执行全量设计审计。

    Args:
        root_dir: 项目根目录绝对路径

    Returns:
        AuditReport 对象，包含 violations、scores、suggestions
    """
    root_dir = os.path.abspath(root_dir)

    # 子模块延迟导入，确保 try/except 在外部调用者层面生效
    from .coupling_checker import check_coupling
    from .solid_checker import check_solid
    from .complexity_checker import analyze_complexity

    complexity_data = analyze_complexity(root_dir)
    coupling_data = check_coupling(root_dir)
    solid_data = check_solid(root_dir)

    return AuditReport(
        root_dir=root_dir,
        complexity_data=complexity_data,
        coupling_data=coupling_data,
        solid_data=solid_data,
    )


def audit_module(module_path: str) -> AuditReport:
    """
    对单个模块目录执行审计。

    Args:
        module_path: 模块目录

    Returns:
        AuditReport 对象
    """
    return audit(module_path)

```
