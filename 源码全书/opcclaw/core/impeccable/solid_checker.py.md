# `opcclaw/core/impeccable/solid_checker.py`

> 路径：`opcclaw/core/impeccable/solid_checker.py` | 行数：336


---


```python
"""
SOLID 原则检查器 — 检测面向对象设计中的五大原则违规。

S — 单一职责：类方法数 > 15 标记违规，分析方法名语义聚类
O — 开闭原则：检测大量 if/elif 类型判断（应使用多态）
L — 里氏替换：检测子类重写方法抛出 NotImplementedError
I — 接口隔离：检测类有过多抽象方法（> 8 个）
D — 依赖倒置：检测直接 import 具体类而非接口/抽象类
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


def _name_clusters(method_names: List[str]) -> List[List[str]]:
    """按方法名的语义前缀聚类（如 get_*, set_*, process_* 等）。"""
    clusters: Dict[str, List[str]] = {}
    for name in method_names:
        prefix = name.split("_")[0] if "_" in name else name
        prefix_lower = prefix.lower()
        if prefix_lower not in clusters:
            clusters[prefix_lower] = []
        clusters[prefix_lower].append(name)
    return [v for v in clusters.values() if len(v) >= 2]


def check_single_responsibility(root_dir: str) -> List[Dict[str, Any]]:
    """
    检查单一职责违规。

    Returns:
        违规列表，每项: {file, class, method_count, clusters: [[method_names], ...]}
    """
    violations = []
    for fp in _get_py_files(root_dir):
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read(), filename=fp)
        except (SyntaxError, Exception):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            methods = [
                n.name for n in ast.iter_child_nodes(node)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not n.name.startswith("__")
            ]
            if len(methods) > 15:
                clusters = _name_clusters(methods)
                violations.append({
                    "file": fp,
                    "class": node.name,
                    "method_count": len(methods),
                    "clusters": clusters,
                })

    violations.sort(key=lambda x: x["method_count"], reverse=True)
    return violations


def _count_if_elif_type_checks(tree: ast.AST) -> int:
    """统计函数中的 if/elif 分支数量。"""
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            # 检查是否是比较类型的 if 语句
            if isinstance(node.test, ast.Compare):
                count += 1
            elif isinstance(node.test, ast.Call):
                func = node.test.func
                if isinstance(func, ast.Name) and func.id == "isinstance":
                    count += 1
                elif isinstance(func, ast.Attribute) and func.attr == "type":
                    count += 1
            else:
                count += 1  # 普通 if 也算
    return count


def check_open_closed(root_dir: str) -> List[Dict[str, Any]]:
    """
    检查开闭原则违规 — 检测函数内有大量 if/elif 类型判断（> 5 个分支）。
    """
    violations = []
    for fp in _get_py_files(root_dir):
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read(), filename=fp)
        except (SyntaxError, Exception):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            branch_count = _count_if_elif_type_checks(node)
            if branch_count > 5:
                violations.append({
                    "file": fp,
                    "function": node.name,
                    "line": node.lineno,
                    "branch_count": branch_count,
                })

    violations.sort(key=lambda x: x["branch_count"], reverse=True)
    return violations[:30]  # 只保留 TOP 30


def check_liskov(root_dir: str) -> List[Dict[str, Any]]:
    """
    检查里氏替换违规 — 检测子类方法抛出 NotImplementedError 或空实现。
    """
    violations = []

    # 第一遍：收集类的继承关系
    class_info: Dict[str, Dict[str, Any]] = {}
    for fp in _get_py_files(root_dir):
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read(), filename=fp)
        except (SyntaxError, Exception):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(base.attr)
            class_info[node.name] = {"bases": bases, "file": fp}

    # 第二遍：检查方法体中是否有 NotImplementedError
    for fp in _get_py_files(root_dir):
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read(), filename=fp)
        except (SyntaxError, Exception):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bases = [b.id if isinstance(b, ast.Name) else b.attr if isinstance(b, ast.Attribute) else ""
                     for b in node.bases]
            if not bases:
                continue

            for child in ast.iter_child_nodes(node):
                if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if child.name.startswith("__"):
                    continue
                # 检查方法体是否只是 raise NotImplementedError 或 pass
                body = child.body
                is_empty = True
                has_not_impl = False
                for stmt in body:
                    if isinstance(stmt, ast.Pass):
                        continue
                    if isinstance(stmt, ast.Raise):
                        if isinstance(stmt.exc, ast.Call):
                            exc_func = stmt.exc.func
                            exc_name = ""
                            if isinstance(exc_func, ast.Name):
                                exc_name = exc_func.id
                            elif isinstance(exc_func, ast.Attribute):
                                exc_name = exc_func.attr
                            if exc_name == "NotImplementedError":
                                has_not_impl = True
                        continue
                    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                        if stmt.value.value == "" or "not" in stmt.value.value.lower():
                            continue
                    is_empty = False

                if has_not_impl or (is_empty and len(body) <= 1):
                    violations.append({
                        "file": fp,
                        "class": node.name,
                        "parent_classes": bases,
                        "method": child.name,
                        "line": child.lineno,
                        "issue": "NotImplementedError" if has_not_impl else "空实现",
                    })

    return violations


def check_interface_segregation(root_dir: str) -> List[Dict[str, Any]]:
    """
    检查接口隔离违规 — 检测抽象类/基类有过多抽象方法（> 8 个）。
    """
    violations = []
    for fp in _get_py_files(root_dir):
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read(), filename=fp)
        except (SyntaxError, Exception):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            # 判断是否为抽象类/基类：名称含 Base/Abstract 或继承 ABC
            is_base = (
                node.name.startswith("Base") or
                node.name.startswith("Abstract") or
                "Interface" in node.name
            )
            if not is_base:
                for base in node.bases:
                    base_name = base.id if isinstance(base, ast.Name) else ""
                    if "ABC" in base_name or "Base" in base_name:
                        is_base = True
                        break
            if not is_base:
                continue

            abstract_methods = []
            for child in ast.iter_child_nodes(node):
                if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if child.name.startswith("__"):
                    continue
                # 检查是否包含 raise NotImplementedError 或 @abstractmethod
                is_abstract = False
                for decorator in child.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "abstractmethod":
                        is_abstract = True
                        break
                if not is_abstract:
                    for stmt in ast.walk(child):
                        if isinstance(stmt, ast.Raise):
                            if isinstance(stmt.exc, ast.Call):
                                exc_func = stmt.exc.func
                                if isinstance(exc_func, ast.Name) and exc_func.id == "NotImplementedError":
                                    is_abstract = True
                                    break

                if is_abstract:
                    abstract_methods.append(child.name)

            if len(abstract_methods) > 8:
                violations.append({
                    "file": fp,
                    "class": node.name,
                    "abstract_method_count": len(abstract_methods),
                    "abstract_methods": abstract_methods[:15],
                })

    violations.sort(key=lambda x: x["abstract_method_count"], reverse=True)
    return violations


def check_dependency_inversion(root_dir: str) -> List[Dict[str, Any]]:
    """
    检查依赖倒置违规 — 检测是否直接 import 具体类而非抽象。
    策略：检测 import 的模块名是否包含具体实现字样（如 Service、Manager、Handler 等）。
    """
    concrete_suffixes = {"Service", "Manager", "Handler", "Controller", "Repository",
                         "Dao", "Util", "Helper", "Impl", "Concrete"}
    violations = []

    for fp in _get_py_files(root_dir):
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read(), filename=fp)
        except (SyntaxError, Exception):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            # 检查函数内的 import 和实参类型注解
            for child in ast.walk(node):
                if isinstance(child, ast.ImportFrom):
                    if child.module:
                        parts = child.module.split(".")
                        for p in parts:
                            for suffix in concrete_suffixes:
                                if p.endswith(suffix):
                                    violations.append({
                                        "file": fp,
                                        "function": node.name,
                                        "line": node.lineno,
                                        "imported": child.module,
                                        "issue": f"直接导入具体类: {child.module}",
                                    })
                                    break

    # 去重
    seen = set()
    unique = []
    for v in violations:
        key = (v["file"], v["function"], v.get("imported", ""))
        if key not in seen:
            seen.add(key)
            unique.append(v)

    return unique[:30]


def check_solid(root_dir: str) -> Dict[str, Any]:
    """
    运行所有 SOLID 检查。

    Returns:
        dict: {"s": [...], "o": [...], "l": [...], "i": [...], "d": [...]}
    """
    root_dir = os.path.abspath(root_dir)
    return {
        "s": check_single_responsibility(root_dir),
        "o": check_open_closed(root_dir),
        "l": check_liskov(root_dir),
        "i": check_interface_segregation(root_dir),
        "d": check_dependency_inversion(root_dir),
    }

```
