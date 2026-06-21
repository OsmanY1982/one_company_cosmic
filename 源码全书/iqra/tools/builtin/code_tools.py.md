# `iqra/tools/builtin/code_tools.py`

> 路径：`iqra/tools/builtin/code_tools.py` | 行数：286


---


```python
# -*- coding: utf-8 -*-
"""
代码智能工具 — Agent 可调用的代码分析/理解/重构工具

对标 Claude Code 的代码理解能力。
"""

import os
from iqra.core.tool_registry import ToolDefinition
from iqra.core.code_intel import CodeIntel


def _get_project_root() -> str:
    """向上查找项目根目录（包含 .git 或 setup.py 等标志）"""
    current = os.getcwd()
    for _ in range(10):
        if os.path.isdir(os.path.join(current, ".git")) or os.path.exists(os.path.join(current, "main.py")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return os.getcwd()


def register_code_tools(registry) -> None:
    """注册所有代码智能工具"""

    project_root = _get_project_root()

    def _get_intel() -> CodeIntel:
        return CodeIntel(project_root)

    # ── code_symbols ──
    def code_symbols(file_path: str) -> dict:
        """提取文件的符号表（函数/类/变量/导入）"""
        try:
            ci = _get_intel()
            symbols = ci.extract_symbols(file_path)
            return {
                "file": file_path,
                "total": len(symbols),
                "symbols": [
                    {
                        "name": s.name,
                        "kind": s.kind,
                        "line": s.line,
                        "signature": s.signature if s.signature else None,
                        "parent_class": s.parent_class if s.parent_class else None,
                        "docstring": s.docstring[:100] if s.docstring else None,
                    }
                    for s in symbols
                ],
            }
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(ToolDefinition(
        name="code_symbols",
        description="提取代码文件的符号表：列出所有函数、类、方法、变量、导入。用于快速理解文件结构",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径（绝对路径或相对项目根目录的路径）"},
            },
            "required": ["file_path"],
        },
        handler=code_symbols,
        category="code",
    ))

    # ── code_usages ──
    def code_usages(symbol_name: str, file_path: str = "") -> dict:
        """搜索符号在项目中的所有引用"""
        try:
            ci = _get_intel()
            usages = ci.find_usages(symbol_name, file_path)
            # 按文件分组
            by_file = {}
            for u in usages:
                f = u["file"]
                if f not in by_file:
                    by_file[f] = []
                by_file[f].append({"line": u["line"], "text": u["text"]})

            return {
                "symbol": symbol_name,
                "total_usages": len(usages),
                "files": len(by_file),
                "by_file": {f: refs for f, refs in list(by_file.items())[:20]},
            }
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(ToolDefinition(
        name="code_usages",
        description="搜索符号在项目中的所有引用位置。用于重命名前确认影响范围、或理解某个函数被哪些地方调用",
        parameters={
            "type": "object",
            "properties": {
                "symbol_name": {"type": "string", "description": "要搜索的符号名（如 'login_user'）"},
                "file_path": {"type": "string", "description": "限定搜索范围的文件/目录（可选）", "default": ""},
            },
            "required": ["symbol_name"],
        },
        handler=code_usages,
        category="code",
    ))

    # ── code_imports ──
    def code_imports(file_path: str) -> dict:
        """分析文件的导入依赖"""
        try:
            ci = _get_intel()
            dep = ci.analyze_imports(file_path)
            return {
                "file": file_path,
                "total_imports": len(dep.imports),
                "stdlib_count": sum(1 for i in dep.imports if i.is_stdlib),
                "third_party_count": sum(1 for i in dep.imports if not i.is_stdlib and not i.is_relative),
                "imports": [
                    {
                        "module": i.module,
                        "names": i.names,
                        "line": i.line,
                        "is_stdlib": i.is_stdlib,
                        "is_relative": i.is_relative,
                    }
                    for i in dep.imports
                ],
            }
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(ToolDefinition(
        name="code_imports",
        description="分析文件的导入依赖：列出所有 import 语句，区分标准库/第三方/项目内导入",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
            },
            "required": ["file_path"],
        },
        handler=code_imports,
        category="code",
    ))

    # ── code_metrics ──
    def code_metrics(file_path: str) -> dict:
        """计算代码度量（行数/复杂度/函数统计）"""
        try:
            ci = _get_intel()
            m = ci.code_metrics(file_path)
            return {
                "file": file_path,
                "total_lines": m.total_lines,
                "code_lines": m.code_lines,
                "comment_lines": m.comment_lines,
                "blank_lines": m.blank_lines,
                "functions": m.functions,
                "classes": m.classes,
                "imports": m.imports_count,
                "avg_function_length": round(m.avg_function_length, 1),
                "max_function_length": m.max_function_length,
                "max_complexity": m.max_complexity,
                "todos": m.todos,
                "fixmes": m.fixmes,
            }
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(ToolDefinition(
        name="code_metrics",
        description="计算代码度量：总行数/代码行/注释行、函数数与平均长度、圈复杂度、TODO/FIXME 数量",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
            },
            "required": ["file_path"],
        },
        handler=code_metrics,
        category="code",
    ))

    # ── code_refactor ──
    def code_refactor(file_path: str) -> dict:
        """分析代码并给出重构建议"""
        try:
            ci = _get_intel()
            suggestions = ci.suggest_refactor(file_path)
            return {
                "file": file_path,
                "total_suggestions": len(suggestions),
                "suggestions": [
                    {
                        "line": s.line,
                        "severity": s.severity,
                        "category": s.category,
                        "message": s.message,
                    }
                    for s in suggestions
                ],
            }
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(ToolDefinition(
        name="code_refactor",
        description="分析代码质量并给出重构建议：长函数、高复杂度、文件过大、技术债标记",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
            },
            "required": ["file_path"],
        },
        handler=code_refactor,
        category="code",
    ))

    # ── code_project_metrics ──
    def code_project_metrics() -> dict:
        """全项目代码统计"""
        try:
            ci = _get_intel()
            return ci.project_metrics()
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(ToolDefinition(
        name="code_project_metrics",
        description="统计整个项目的代码度量：总文件数/总代码行/总函数数/超长文件/超长函数",
        parameters={"type": "object", "properties": {}, "required": []},
        handler=code_project_metrics,
        category="code",
    ))

    # ── code_dep_graph ──
    def code_dep_graph(file_path: str = "") -> dict:
        """分析依赖关系"""
        try:
            ci = _get_intel()
            if file_path:
                dep = ci.analyze_imports(file_path)
                return {
                    "file": file_path,
                    "total_imports": len(dep.imports),
                    "imports": [
                        {"module": i.module, "names": i.names}
                        for i in dep.imports
                    ],
                }
            else:
                graph = ci.build_dep_graph()
                # 摘要
                total_deps = sum(len(d.imports) for d in graph.values())
                most_imported = sorted(
                    [(k, len(v.imports)) for k, v in graph.items()],
                    key=lambda x: x[1], reverse=True
                )[:10]
                return {
                    "files_analyzed": len(graph),
                    "total_dependencies": total_deps,
                    "most_imports": [
                        {"file": os.path.relpath(k, project_root), "count": c}
                        for k, c in most_imported
                    ],
                }
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(ToolDefinition(
        name="code_dep_graph",
        description="分析项目依赖关系。传入 file_path 查看单个文件导入，留空则构建全项目依赖图摘要",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径（可选，留空分析全项目）", "default": ""},
            },
            "required": [],
        },
        handler=code_dep_graph,
        category="code",
    ))

```
