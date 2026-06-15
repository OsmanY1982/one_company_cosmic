"""
报告生成器 — 生成 Markdown 格式的设计审计报告。

包含：总体评分（A-F）、模块耦合度热力图数据、TOP 违规列表、改进建议
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional


def _grade(score: float) -> str:
    """根据综合评分返回 A-F 等级。"""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    elif score >= 40:
        return "E"
    else:
        return "F"


def _compute_score(complexity_data: Dict[str, Any],
                   coupling_data: Dict[str, Any],
                   solid_data: Dict[str, Any]) -> float:
    """基于各项指标计算综合评分（0-100）。"""
    score = 100.0

    # 圈复杂度扣分：热点函数每个扣 2 分
    hotspots = complexity_data.get("hotspots", [])
    score -= min(len(hotspots) * 2, 30)

    # 循环依赖扣分：每个环扣 8 分
    cycles = coupling_data.get("cyclic_deps", [])
    score -= min(len(cycles) * 8, 24)

    # 不稳定模块扣分：每个扣 3 分
    unstable = coupling_data.get("unstable", [])
    score -= min(len(unstable) * 3, 15)

    # 上帝对象扣分：每个扣 5 分
    gods = coupling_data.get("god_objects", [])
    score -= min(len(gods) * 5, 10)

    # SOLID 违规扣分
    for key, weight in [("s", 1), ("o", 1), ("l", 1), ("i", 1), ("d", 0.5)]:
        viols = solid_data.get(key, []) if solid_data else []
        score -= min(len(viols) * weight, 10)

    return max(0.0, round(score, 1))


def generate_report(complexity_data: Dict[str, Any],
                    coupling_data: Dict[str, Any],
                    solid_data: Optional[Dict[str, Any]] = None,
                    output_dir: Optional[str] = None) -> str:
    """
    生成 Markdown 格式审计报告。

    Args:
        complexity_data: 复杂度分析结果
        coupling_data: 耦合度分析结果
        solid_data: SOLID 违规结果
        output_dir: 报告输出目录，默认为 reports/impeccable/

    Returns:
        str: 报告 Markdown 内容
    """
    if solid_data is None:
        solid_data = {}

    score = _compute_score(complexity_data, coupling_data, solid_data)
    grade = _grade(score)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── 统计汇总 ──
    comp_summary = complexity_data.get("summary", {})
    total_funcs = comp_summary.get("total_functions", 0)
    avg_cyclo = comp_summary.get("avg_cyclomatic", 0)
    avg_cogn = comp_summary.get("avg_cognitive", 0)
    max_cyclo = comp_summary.get("max_cyclomatic", 0)
    max_cogn = comp_summary.get("max_cognitive", 0)
    hotspots_count = len(complexity_data.get("hotspots", []))
    cycles_count = len(coupling_data.get("cyclic_deps", []))
    unstable_count = len(coupling_data.get("unstable", []))
    god_count = len(coupling_data.get("god_objects", []))

    lines = []
    lines.append("# Impeccable 设计审计报告")
    lines.append(f"**生成时间**: {now}")
    lines.append("")

    # ── 1. 总体评分 ──
    lines.append("## 1. 总体评分")
    lines.append("")
    lines.append(f"| 指标 | 值 |")
    lines.append(f"|---|---|")
    grade_desc = {"A": "优秀", "B": "良好", "C": "一般", "D": "较差", "E": "差", "F": "极差"}
    lines.append(f"| **综合评分** | **{score} / 100** |")
    lines.append(f"| **等级** | **{grade}（{grade_desc.get(grade, '未知')}）** |")
    lines.append("")
    lines.append("| 维度 | 统计 | 扣分 |")
    lines.append("|---|---|---|")
    lines.append(f"| 复杂度热点（>15） | {hotspots_count} 个 | -{min(hotspots_count * 2, 30)} |")
    lines.append(f"| 循环依赖 | {cycles_count} 个环 | -{min(cycles_count * 8, 24)} |")
    lines.append(f"| 不稳定模块（I>0.7） | {unstable_count} 个 | -{min(unstable_count * 3, 15)} |")
    lines.append(f"| 上帝对象 | {god_count} 个 | -{min(god_count * 5, 10)} |")
    for key, label, weight in [("s", "单一职责违规", 1), ("o", "开闭原则违规", 1),
                                ("l", "里氏替换违规", 1), ("i", "接口隔离违规", 1),
                                ("d", "依赖倒置违规", 0.5)]:
        viols = solid_data.get(key, [])
        lines.append(f"| {label} | {len(viols)} 个 | -{min(len(viols) * weight, 10)} |")
    lines.append("")

    # ── 2. 复杂度分析 ──
    lines.append("## 2. 复杂度分析")
    lines.append("")
    lines.append(f"- 总函数/方法数: {total_funcs}")
    lines.append(f"- 平均圈复杂度: {avg_cyclo}")
    lines.append(f"- 平均认知复杂度: {avg_cogn}")
    lines.append(f"- 最大圈复杂度: {max_cyclo}")
    lines.append(f"- 最大认知复杂度: {max_cogn}")
    lines.append(f"- 热点函数数（圈复杂度 > 15）: {hotspots_count}")
    lines.append("")

    if hotspots_count > 0:
        lines.append("### 热度 TOP 20（圈复杂度）")
        lines.append("")
        lines.append("| # | 函数 | 文件 | 行号 | 圈复杂度 | 认知复杂度 |")
        lines.append("|---|---|---|---|---|---|")
        top20 = complexity_data.get("top20_cyclomatic", [])
        for i, func in enumerate(top20, 1):
            rel_file = func["file"]
            lines.append(f"| {i} | `{func['name']}` | {rel_file} | {func['line']} | {func['cyclomatic']} | {func['cognitive']} |")
        lines.append("")
    else:
        lines.append("> 未发现复杂度热点（所有函数圈复杂度 ≤ 15）。")
        lines.append("")

    # ── 3. 耦合度分析 ──
    lines.append("## 3. 耦合度分析")
    lines.append("")

    if cycles_count > 0:
        lines.append(f"### 循环依赖（{cycles_count} 个）")
        lines.append("")
        for cycle in coupling_data.get("cyclic_deps", []):
            arrow = " → ".join(cycle)
            lines.append(f"- {arrow}")
        lines.append("")
    else:
        lines.append("> 未发现循环依赖。")
        lines.append("")

    if unstable_count > 0:
        lines.append(f"### 不稳定模块（I > 0.7，共 {unstable_count} 个）")
        lines.append("")
        lines.append("| 模块 | 不稳定指数 (I) | 传入耦合 (Ca) | 传出耦合 (Ce) |")
        lines.append("|---|---|---|---|")
        for mod_name, inst in coupling_data.get("unstable", [])[:20]:
            mod_info = coupling_data.get("modules", {}).get(mod_name, {})
            lines.append(f"| {mod_name} | {inst} | {mod_info.get('ca', '?')} | {mod_info.get('ce', '?')} |")
        lines.append("")
    else:
        lines.append("> 未发现不稳定模块（所有模块 I ≤ 0.7）。")
        lines.append("")

    if god_count > 0:
        lines.append(f"### 上帝对象（>1000 行 && >30 方法，共 {god_count} 个）")
        lines.append("")
        lines.append("| 文件 | 行数 | 方法数 |")
        lines.append("|---|---|---|")
        for fp, lns, mths in coupling_data.get("god_objects", []):
            lines.append(f"| {fp} | {lns} | {mths} |")
        lines.append("")
    else:
        lines.append("> 未发现上帝对象。")
        lines.append("")

    # ── 4. SOLID 违规 ──
    lines.append("## 4. SOLID 原则违规")
    lines.append("")
    for key, label, desc in [
        ("s", "S — 单一职责原则", "类方法数 > 15，建议拆分"),
        ("o", "O — 开闭原则", "函数内大量 if/elif 类型判断（>5），建议使用多态"),
        ("l", "L — 里氏替换原则", "子类重写方法抛 NotImplementedError 或空实现"),
        ("i", "I — 接口隔离原则", "抽象类/基类有过多抽象方法（>8）"),
        ("d", "D — 依赖倒置原则", "直接导入具体实现类而非依赖抽象"),
    ]:
        viols = solid_data.get(key, [])
        lines.append(f"### {label}")
        lines.append(f"> {desc} — 发现 **{len(viols)}** 处违规")
        lines.append("")
        if viols:
            if key == "s":
                lines.append("| 类 | 文件 | 方法数 | 语义聚类 |")
                lines.append("|---|---|---|---|")
                for v in viols[:15]:
                    clusters_str = ", ".join([f"[{', '.join(c)}]" for c in v.get("clusters", [])])
                    if not clusters_str:
                        clusters_str = "—"
                    lines.append(f"| `{v['class']}` | {v['file']} | {v['method_count']} | {clusters_str} |")
            elif key == "o":
                lines.append("| 函数 | 文件 | 行号 | 分支数 |")
                lines.append("|---|---|---|---|")
                for v in viols[:15]:
                    lines.append(f"| `{v['function']}` | {v['file']} | {v['line']} | {v['branch_count']} |")
            elif key == "l":
                lines.append("| 类 | 方法 | 父类 | 文件 | 问题 |")
                lines.append("|---|---|---|---|---|")
                for v in viols[:15]:
                    parents_str = ", ".join(v.get("parent_classes", []))
                    lines.append(f"| `{v['class']}` | `{v['method']}` | {parents_str} | {v['file']} | {v.get('issue', '')} |")
            elif key == "i":
                lines.append("| 类 | 文件 | 抽象方法数 |")
                lines.append("|---|---|---|")
                for v in viols[:15]:
                    lines.append(f"| `{v['class']}` | {v['file']} | {v['abstract_method_count']} |")
            elif key == "d":
                lines.append("| 函数 | 导入模块 | 文件 |")
                lines.append("|---|---|---|")
                for v in viols[:15]:
                    imp = v.get("imported", v.get("issue", ""))
                    lines.append(f"| `{v['function']}` | `{imp}` | {v['file']} |")
        lines.append("")

    # ── 5. 改进建议 ──
    lines.append("## 5. 改进建议")
    lines.append("")

    suggestions = []
    if hotspots_count > 0:
        suggestions.append(f"- **降低复杂度**: {hotspots_count} 个函数圈复杂度 > 15，考虑拆分大函数")
    if cycles_count > 0:
        suggestions.append(f"- **打破循环依赖**: 发现 {cycles_count} 个循环依赖环，引入依赖反转或提取共享接口")
    if unstable_count > 0:
        suggestions.append(f"- **稳定化模块**: {unstable_count} 个模块不稳定指数 > 0.7，需减少传出依赖或增加传入依赖")
    if god_count > 0:
        suggestions.append(f"- **拆分上帝对象**: {god_count} 个文件 > 1000 行且 > 30 方法，按职责拆分")
    s_viols = solid_data.get("s", [])
    o_viols = solid_data.get("o", [])
    if s_viols:
        suggestions.append(f"- **单一职责**: {len(s_viols)} 个类方法 > 15，按方法名语义聚类拆分")
    if o_viols:
        suggestions.append(f"- **开闭原则**: {len(o_viols)} 个函数含 > 5 个 if/elif 类型判断，用策略/多态模式替代")

    if not suggestions:
        suggestions.append("- 当前代码架构质量良好，暂无紧急改进项。")

    lines.extend(suggestions)
    lines.append("")
    lines.append("---")
    lines.append(f"*报告由 Impeccable 设计审计引擎自动生成*")

    report_md = "\n".join(lines)

    # 写入文件
    if output_dir is None:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(project_root, "reports", "impeccable")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(output_dir, f"audit_report_{timestamp}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    return report_md
