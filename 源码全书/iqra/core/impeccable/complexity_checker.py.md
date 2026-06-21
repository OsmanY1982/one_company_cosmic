# `iqra/core/impeccable/complexity_checker.py`

> 路径：`iqra/core/impeccable/complexity_checker.py` | 行数：176


---


```python
"""
复杂度分析器 — 计算圈复杂度与认知复杂度。

- 圈复杂度：统计每个函数的 if/for/while/except/and/or 数量
- 认知复杂度：嵌套层级 + 逻辑运算符权重
- 标记复杂度 > 15 的函数为热点
- 生成 TOP 20 最复杂函数列表
"""

import ast
import os
from typing import Dict, List, Tuple, Any, Set, Optional


def _get_py_files(root_dir: str, skip_dirs: Optional[Set[str]] = None) -> List[str]:
    if skip_dirs is None:
        skip_dirs = {"tests", "venv", ".venv", "__pycache__", ".git", "node_modules"}
    py_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]
        for f in filenames:
            if f.endswith(".py"):
                py_files.append(os.path.join(dirpath, f))
    return py_files


# ── 圈复杂度计算 ──

_CYCLOMATIC_NODES = (
    ast.If, ast.For, ast.While, ast.ExceptHandler,
    ast.BoolOp,  # and/or
    ast.Try,
)

def _cyclomatic_complexity(func_node: ast.AST) -> int:
    """计算函数/方法的圈复杂度。起始值为 1，每遇到一个分支节点 +1。"""
    count = 1
    for node in ast.walk(func_node):
        if isinstance(node, _CYCLOMATIC_NODES):
            if isinstance(node, ast.BoolOp):
                count += len(node.values) - 1  # 多个条件用 and/or 连接
            else:
                count += 1
    return count


# ── 认知复杂度计算 ──

def _cognitive_complexity(func_node: ast.AST) -> int:
    """
    计算认知复杂度。
    规则：
    - 基础 +1：if/for/while/except/and/or
    - 嵌套权重：每深入一层嵌套，额外 +1
    - 逻辑运算符 and/or：每个额外条件 +1
    """
    total = 0
    nesting = 0

    def _walk(node, nesting_level):
        nonlocal total
        if isinstance(node, ast.If):
            total += 1 + nesting_level
            for child in ast.iter_child_nodes(node):
                _walk(child, nesting_level + 1)
        elif isinstance(node, (ast.For, ast.While)):
            total += 1 + nesting_level
            for child in ast.iter_child_nodes(node):
                _walk(child, nesting_level + 1)
        elif isinstance(node, ast.ExceptHandler):
            total += 1 + nesting_level
            for child in ast.iter_child_nodes(node):
                _walk(child, nesting_level + 1)
        elif isinstance(node, ast.Try):
            for child in ast.iter_child_nodes(node):
                _walk(child, nesting_level)  # try 本身不增加嵌套
        elif isinstance(node, ast.BoolOp):
            # and/or 运算符
            total += (len(node.values) - 1) + nesting_level
            for child in ast.iter_child_nodes(node):
                _walk(child, nesting_level + 1)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # 嵌套函数/方法
            for child in ast.iter_child_nodes(node):
                _walk(child, nesting_level + 1)
        else:
            for child in ast.iter_child_nodes(node):
                _walk(child, nesting_level)

    _walk(func_node, 0)
    return total


# ── 主分析函数 ──

def analyze_complexity(root_dir: str) -> Dict[str, Any]:
    """
    分析项目代码复杂度。

    Returns:
        dict: {
            "functions": [{"file": str, "name": str, "line": int, "cyclomatic": int, "cognitive": int}, ...],
            "hotspots": [同上],  # 圈复杂度 > 15
            "top20_cyclomatic": [...],
            "top20_cognitive": [...],
            "summary": {"total_functions": int, "avg_cyclomatic": float, "avg_cognitive": float, "max_cyclomatic": int, "max_cognitive": int}
        }
    """
    root_dir = os.path.abspath(root_dir)
    all_functions: List[Dict[str, Any]] = []

    for fp in _get_py_files(root_dir):
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read(), filename=fp)
        except (SyntaxError, Exception):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            cyclo = _cyclomatic_complexity(node)
            cogn = _cognitive_complexity(node)

            # 获取所属类名
            class_name = ""
            for parent in ast.iter_child_nodes(tree):
                if isinstance(parent, ast.ClassDef):
                    for child in ast.iter_child_nodes(parent):
                        if child is node:
                            class_name = parent.name
                            break

            display_name = f"{class_name}.{node.name}" if class_name else node.name

            all_functions.append({
                "file": fp,
                "name": display_name,
                "line": node.lineno,
                "cyclomatic": cyclo,
                "cognitive": cogn,
            })

    # 排序
    all_functions.sort(key=lambda x: x["cyclomatic"], reverse=True)
    top20_cyclo = all_functions[:20]

    by_cognitive = sorted(all_functions, key=lambda x: x["cognitive"], reverse=True)
    top20_cognitive = by_cognitive[:20]

    hotspots = [f for f in all_functions if f["cyclomatic"] > 15]

    # 汇总统计
    total_funcs = len(all_functions)
    if total_funcs > 0:
        avg_cyclo = sum(f["cyclomatic"] for f in all_functions) / total_funcs
        avg_cogn = sum(f["cognitive"] for f in all_functions) / total_funcs
        max_cyclo = max(f["cyclomatic"] for f in all_functions)
        max_cogn = max(f["cognitive"] for f in all_functions)
    else:
        avg_cyclo = avg_cogn = max_cyclo = max_cogn = 0.0

    return {
        "functions": all_functions,
        "hotspots": hotspots,
        "top20_cyclomatic": top20_cyclo,
        "top20_cognitive": top20_cognitive,
        "summary": {
            "total_functions": total_funcs,
            "avg_cyclomatic": round(avg_cyclo, 2),
            "avg_cognitive": round(avg_cogn, 2),
            "max_cyclomatic": max_cyclo,
            "max_cognitive": max_cogn,
        },
    }

```
