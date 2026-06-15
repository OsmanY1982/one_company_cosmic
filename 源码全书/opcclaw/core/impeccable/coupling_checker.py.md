# `opcclaw/core/impeccable/coupling_checker.py`

> 路径：`opcclaw/core/impeccable/coupling_checker.py` | 行数：225


---


```python
"""
耦合度检查器 — 分析模块间的 import 依赖关系。

检测指标：
- 传入耦合 (Ca)、传出耦合 (Ce)
- 不稳定指数 I = Ce/(Ca+Ce)
- 循环依赖检测
- 上帝对象检测（单文件 > 1000 行且方法 > 30 个）
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict

try:
    import networkx as nx
    _HAS_NX = True
except ImportError:
    _HAS_NX = False


def _get_py_files(root_dir: str, skip_dirs: Optional[Set[str]] = None) -> List[str]:
    """获取项目下所有 .py 文件，跳过 tests/ 和 venv/。"""
    if skip_dirs is None:
        skip_dirs = {"tests", "venv", ".venv", "__pycache__", ".git", "node_modules"}
    py_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]
        for f in filenames:
            if f.endswith(".py"):
                py_files.append(os.path.join(dirpath, f))
    return py_files


def _module_name(file_path: str, root_dir: str) -> str:
    """从文件路径提取模块名（相对路径，去掉 .py 和 __init__）。"""
    rel = os.path.relpath(file_path, root_dir)
    parts = list(Path(rel).parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
        if not parts:
            return "root"
    else:
        parts[-1] = Path(parts[-1]).stem
    return ".".join(parts)


def _parse_imports(file_path: str, root_dir: str) -> Tuple[str, Set[str]]:
    """解析文件的 import 语句，返回 (自身模块名, 被导入模块名集合)。"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except (SyntaxError, Exception):
        return (_module_name(file_path, root_dir), set())

    self_mod = _module_name(file_path, root_dir)
    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    return (self_mod, imports)


def _is_project_module(module_name: str, root_dir: str) -> bool:
    """判断模块名是否属于本项目（而非标准库/第三方包）。"""
    stdlib = {
        "os", "sys", "re", "json", "time", "abc", "ast", "asyncio", "base64",
        "collections", "concurrent", "contextlib", "copy", "csv", "ctypes",
        "dataclasses", "datetime", "decimal", "enum", "fnmatch", "functools",
        "glob", "hashlib", "html", "http", "importlib", "inspect", "io",
        "itertools", "logging", "math", "multiprocessing", "operator", "pathlib",
        "pickle", "platform", "pprint", "queue", "random", "shutil", "signal",
        "socket", "sqlite3", "ssl", "statistics", "string", "struct", "subprocess",
        "tempfile", "textwrap", "threading", "tokenize", "traceback", "types",
        "typing", "unittest", "urllib", "uuid", "warnings", "weakref", "xml", "zipfile",
    }
    root = module_name.split(".")[0].lower()
    if root in stdlib:
        return False
    # 检查项目中是否存在同名顶级目录/包
    candidate = os.path.join(root_dir, root)
    if os.path.exists(candidate):
        return True
    return False


def _count_methods(file_path: str) -> int:
    """统计文件中的方法/函数数量。"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read(), filename=file_path)
    except (SyntaxError, Exception):
        return 0
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            count += 1
    return count


def _count_lines(file_path: str) -> int:
    """统计文件行数。"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def check_coupling(root_dir: str) -> Dict[str, Any]:
    """
    分析项目模块耦合度。

    Returns:
        dict: {
            "modules": {module_name: {"ca": int, "ce": int, "instability": float}},
            "unstable": [(module_name, instability), ...],  # I > 0.7
            "god_objects": [(file_path, lines, methods), ...],  # >1000 行 && >30 方法
            "cyclic_deps": [[cycle], ...],  # 循环依赖列表
        }
    """
    root_dir = os.path.abspath(root_dir)
    py_files = _get_py_files(root_dir, skip_dirs={"tests", "venv", ".venv", "__pycache__", ".git", "node_modules"})

    # 建立模块 → 文件路径映射
    mod_to_file: Dict[str, str] = {}
    for fp in py_files:
        mod_to_file[_module_name(fp, root_dir)] = fp

    # 收集所有 import 关系
    imports_map: Dict[str, Set[str]] = {}  # 模块 → 本模块实际用到的（被解析到的在项目中的其他模块）
    all_module_names: Set[str] = set()

    for fp in py_files:
        self_mod, raw_imports = _parse_imports(fp, root_dir)
        all_module_names.add(self_mod)
        project_imports = set()
        for imp in raw_imports:
            if _is_project_module(imp, root_dir) and imp != self_mod:
                project_imports.add(imp)
        imports_map[self_mod] = project_imports

    # 建立反向映射：被哪些模块依赖
    dependents: Dict[str, Set[str]] = defaultdict(set)
    for mod, imps in imports_map.items():
        for imp in imps:
            dependents[imp].add(mod)

    # 计算 Ca / Ce / I
    modules: Dict[str, Dict[str, Any]] = {}
    unstable: List[Tuple[str, float]] = []

    for mod_name in sorted(all_module_names):
        ce = len(imports_map.get(mod_name, set()))
        ca = len(dependents.get(mod_name, set()))
        total = ca + ce
        instability = ce / total if total > 0 else 0.0
        modules[mod_name] = {"ca": ca, "ce": ce, "instability": round(instability, 4)}
        if instability > 0.7 and total > 0:
            unstable.append((mod_name, round(instability, 4)))

    # 检测上帝对象
    god_objects: List[Tuple[str, int, int]] = []
    for mod_name, file_path in mod_to_file.items():
        lines = _count_lines(file_path)
        methods = _count_methods(file_path)
        if lines > 1000 and methods > 30:
            god_objects.append((file_path, lines, methods))

    # 检测循环依赖
    cyclic_deps: List[List[str]] = []
    if _HAS_NX:
        G = nx.DiGraph()
        for mod in all_module_names:
            G.add_node(mod)
        for mod, imps in imports_map.items():
            for imp in imps:
                G.add_edge(mod, imp)
        try:
            cycles = list(nx.simple_cycles(G))
            cyclic_deps = [list(c) for c in cycles]
        except Exception:
            cyclic_deps = []
    else:
        # 兜底：简单 DFS 检测环
        visited = set()
        stack = set()
        cycles_list = []

        def _dfs(node, path):
            visited.add(node)
            stack.add(node)
            for neighbor in imports_map.get(node, set()):
                if neighbor not in visited:
                    _dfs(neighbor, path + [neighbor])
                elif neighbor in stack:
                    idx = path.index(neighbor) if neighbor in path else len(path) - 1
                    cycle = path[idx:] + [neighbor]
                    if cycle not in cycles_list:
                        cycles_list.append(cycle)
            stack.discard(node)

        for mod in all_module_names:
            if mod not in visited:
                _dfs(mod, [mod])
        cyclic_deps = cycles_list

    unstable.sort(key=lambda x: x[1], reverse=True)
    god_objects.sort(key=lambda x: x[1], reverse=True)

    return {
        "modules": modules,
        "unstable": unstable,
        "god_objects": god_objects,
        "cyclic_deps": cyclic_deps,
    }

```
