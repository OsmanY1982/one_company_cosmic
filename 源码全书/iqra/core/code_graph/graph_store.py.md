# `iqra/core/code_graph/graph_store.py`

> 路径：`iqra/core/code_graph/graph_store.py` | 行数：558


---


```python
# -*- coding: utf-8 -*-
"""
图存储 — 基于 networkx 有向图存储代码元素及其关系

节点类型:
  - ModuleNode:   文件/模块
  - ClassNode:    类定义
  - FunctionNode: 函数/方法定义
  - ImportNode:   导入语句

边类型:
  - CONTAINS:   Module → Class / Function
  - INHERITS:   Class → Class（子类 → 父类）
  - IMPORTS:    Module → Module
  - CALLS:      Function → Function / Class.method

磁盘持久化: save_graph() / load_graph()
"""

import os
import json
import pickle
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple, Any

from .ast_parser import (
    ParseResult, ClassNode, FunctionNode, ImportNode, CallNode,
)


# ═══════════════════════════════════════════
# 图节点
# ═══════════════════════════════════════════

@dataclass
class ModuleGraphNode:
    """模块节点"""
    module_path: str                                    # 文件绝对路径
    module_name: str = ""                               # 模块名（去掉根目录和 .py）
    docstring: str = ""
    class_count: int = 0
    function_count: int = 0
    import_count: int = 0


@dataclass
class ClassGraphNode:
    """类节点"""
    name: str
    file_path: str
    line_number: int
    end_line: int = 0
    bases: List[str] = field(default_factory=list)
    docstring: str = ""
    method_names: List[str] = field(default_factory=list)


@dataclass
class FunctionGraphNode:
    """函数/方法节点"""
    name: str
    file_path: str
    line_number: int
    end_line: int = 0
    params: List[str] = field(default_factory=list)
    docstring: str = ""
    parent_class: str = ""                              # 所属类（空=顶层函数）
    is_async: bool = False
    return_annotation: str = ""


# ═══════════════════════════════════════════
# 边类型常量
# ═══════════════════════════════════════════

class EdgeType:
    CONTAINS  = "CONTAINS"       # Module → Class / Function
    INHERITS  = "INHERITS"       # Class → Class
    IMPORTS   = "IMPORTS"        # Module → Module
    CALLS     = "CALLS"          # Function → Function


# ═══════════════════════════════════════════
# CodeGraphStore
# ═══════════════════════════════════════════

class CodeGraphStore:
    """
    有向图存储 — 代码元素关系图

    使用 networkx.DiGraph 存储节点和边，节点 ID 格式:
      - module:<abs_path>
      - class:<abs_path>::<ClassName>
      - function:<abs_path>::<func_name>          （顶层函数）
      - function:<abs_path>::<ClassName>.<method_name>  （方法）
    """

    def __init__(self, nx_module=None):
        """初始化图存储

        Args:
            nx_module: networkx 模块（用于依赖注入测试），None 则自动导入
        """
        if nx_module is None:
            try:
                import networkx as nx
                nx_module = nx
            except ImportError:
                raise ImportError(
                    "CodeGraphStore requires networkx>=3.0. "
                    "Install with: pip install networkx"
                )
        self._nx = nx_module
        self._graph = nx_module.DiGraph()

    # ── 属性 ──

    @property
    def node_count(self) -> int:
        return self._graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self._graph.number_of_edges()

    @property
    def graph(self):
        """返回底层 networkx DiGraph"""
        return self._graph

    # ── 构建 ──

    def build_from_parse_results(self, parse_results: List[ParseResult], project_root: str) -> int:
        """
        将 AST 解析结果批量写入图

        Args:
            parse_results: parse_file/scan_project 返回的 ParseResult 列表
            project_root: 项目根目录（用于计算模块名）

        Returns:
            添加的节点总数
        """
        node_count_before = self._graph.number_of_nodes()

        for pr in parse_results:
            self._add_module_node(pr, project_root)

        return self._graph.number_of_nodes() - node_count_before

    def _add_module_node(self, pr: ParseResult, project_root: str):
        """将单个 ParseResult 写入图"""
        module_id = self._make_module_id(pr.file_path)
        module_name = self._compute_module_name(pr.file_path, project_root)

        # ModuleNode
        self._graph.add_node(
            module_id,
            type="module",
            data=ModuleGraphNode(
                module_path=pr.file_path,
                module_name=module_name,
                docstring=pr.module_docstring,
                class_count=len(pr.classes),
                function_count=len(pr.functions),
                import_count=len(pr.imports),
            ),
        )

        # ClassNode + CONTAINS
        for cls in pr.classes:
            class_id = self._make_class_id(pr.file_path, cls.name)
            self._graph.add_node(
                class_id,
                type="class",
                data=ClassGraphNode(
                    name=cls.name,
                    file_path=pr.file_path,
                    line_number=cls.line_number,
                    end_line=cls.end_line,
                    bases=cls.bases,
                    docstring=cls.docstring,
                    method_names=cls.methods,
                ),
            )
            self._graph.add_edge(module_id, class_id, type=EdgeType.CONTAINS)

            # INHERITS
            for base in cls.bases:
                # 只记录父类名（可能跨文件，解析时会在 query 阶段查找）
                base_id = self._make_class_id(pr.file_path, base)
                self._graph.add_node(
                    base_id,
                    type="class",
                    data=ClassGraphNode(
                        name=base,
                        file_path="__unknown__",
                        line_number=0,
                        bases=[],
                    ),
                )
                self._graph.add_edge(class_id, base_id, type=EdgeType.INHERITS)

        # FunctionNode + CONTAINS
        for fn in pr.functions:
            func_id = self._make_function_id(pr.file_path, fn.name, fn.parent_class)
            self._graph.add_node(
                func_id,
                type="function",
                data=FunctionGraphNode(
                    name=fn.name,
                    file_path=pr.file_path,
                    line_number=fn.line_number,
                    end_line=fn.end_line,
                    params=fn.params,
                    docstring=fn.docstring,
                    parent_class=fn.parent_class,
                    is_async=fn.is_async,
                    return_annotation=fn.return_annotation,
                ),
            )
            self._graph.add_edge(module_id, func_id, type=EdgeType.CONTAINS)

        # ImportNode → IMPORTS
        for imp in pr.imports:
            # 记录导入的模块名（非 stdlib 时尝试解析为项目内模块）
            target_module = imp.module.split(".")[0] if imp.module else ""
            if target_module and not target_module.startswith("_"):
                # 尝试匹配项目中同名模块
                for other_module_id in self._graph.nodes():
                    other_data = self._graph.nodes[other_module_id].get("data")
                    if other_data and isinstance(other_data, ModuleGraphNode):
                        if other_data.module_name == target_module:
                            self._graph.add_edge(module_id, other_module_id, type=EdgeType.IMPORTS)
                            break

        # CallNode → CALLS
        for call in pr.calls:
            caller_id = self._make_function_id(
                pr.file_path, call.caller_name, call.caller_parent_class
            )
            # 尝试找被调用函数
            callee_id = self._resolve_callee_id(call.callee_name, pr.file_path)
            if callee_id and callee_id != caller_id:
                self._graph.add_edge(
                    caller_id, callee_id,
                    type=EdgeType.CALLS,
                    line=call.line_number,
                )

    def _resolve_callee_id(self, callee_name: str, caller_file: str) -> Optional[str]:
        """在图中查找被调用函数节点 ID"""
        # 方法调用 Class.method
        if "." in callee_name:
            parts = callee_name.split(".")
            class_name = ".".join(parts[:-1])
            method_name = parts[-1]
            # 搜索所有可能的文件路径
            for node_id, node_data in self._graph.nodes(data=True):
                if node_data.get("type") == "function":
                    fn_data = node_data.get("data")
                    if fn_data and fn_data.name == method_name and fn_data.parent_class == class_name:
                        return node_id

        # 顶层函数调用
        for node_id, node_data in self._graph.nodes(data=True):
            if node_data.get("type") == "function":
                fn_data = node_data.get("data")
                if fn_data and fn_data.name == callee_name and not fn_data.parent_class:
                    return node_id

        # 同文件方法
        for node_id, node_data in self._graph.nodes(data=True):
            if node_data.get("type") == "function":
                fn_data = node_data.get("data")
                if fn_data and fn_data.name == callee_name and fn_data.file_path == caller_file:
                    return node_id

        return None

    # ── 查询 ──

    def get_callers(self, func_name: str) -> List[Dict[str, Any]]:
        """
        返回所有调用指定函数的代码位置

        Returns:
            [{"caller": str, "file_path": str, "line": int}, ...]
        """
        results = []
        for node_id, node_data in self._graph.nodes(data=True):
            if node_data.get("type") != "function":
                continue
            fn_data = node_data.get("data")
            if not fn_data or fn_data.name != func_name:
                continue

            # 找所有指向该节点的 CALLS 边
            for pred_id in self._graph.predecessors(node_id):
                edge_data = self._graph.get_edge_data(pred_id, node_id)
                if edge_data and edge_data.get("type") == EdgeType.CALLS:
                    pred_data = self._graph.nodes[pred_id].get("data")
                    if pred_data:
                        results.append({
                            "caller": pred_data.name,
                            "parent_class": getattr(pred_data, "parent_class", ""),
                            "file_path": pred_data.file_path,
                            "line": pred_data.line_number,
                            "call_line": edge_data.get("line", 0),
                        })
        return results

    def get_callees(self, func_name: str) -> List[Dict[str, Any]]:
        """
        返回指定函数调用的所有其他函数

        Returns:
            [{"callee": str, "file_path": str, "line": int}, ...]
        """
        results = []
        for node_id, node_data in self._graph.nodes(data=True):
            if node_data.get("type") != "function":
                continue
            fn_data = node_data.get("data")
            if not fn_data or fn_data.name != func_name:
                continue

            # 找所有从该节点出发的 CALLS 边
            for succ_id in self._graph.successors(node_id):
                edge_data = self._graph.get_edge_data(node_id, succ_id)
                if edge_data and edge_data.get("type") == EdgeType.CALLS:
                    succ_data = self._graph.nodes[succ_id].get("data")
                    if succ_data:
                        results.append({
                            "callee": succ_data.name,
                            "parent_class": getattr(succ_data, "parent_class", ""),
                            "file_path": succ_data.file_path,
                            "line": succ_data.line_number,
                            "call_line": edge_data.get("line", 0),
                        })
        return results

    def get_class_hierarchy(self, class_name: str) -> Dict[str, Any]:
        """
        返回类的完整继承链

        Returns:
            {"class": str, "file_path": str, "parents": [...], "children": [...], "methods": [...]}
        """
        result = {
            "class": class_name,
            "file_path": "",
            "line": 0,
            "parents": [],
            "children": [],
            "methods": [],
        }

        # 找到主节点
        main_class_id = None
        for node_id, node_data in self._graph.nodes(data=True):
            if node_data.get("type") != "class":
                continue
            cls_data = node_data.get("data")
            if cls_data and cls_data.name == class_name:
                if cls_data.file_path != "__unknown__":
                    main_class_id = node_id
                    result["file_path"] = cls_data.file_path
                    result["line"] = cls_data.line_number
                    result["methods"] = cls_data.method_names
                    break

        if not main_class_id:
            # 至少返回收集到的信息（可能来自 unknown 节点）
            for node_id, node_data in self._graph.nodes(data=True):
                if node_data.get("type") == "class":
                    cls_data = node_data.get("data")
                    if cls_data and cls_data.name == class_name:
                        result["methods"] = cls_data.method_names or result["methods"]

        # 递归收集父类
        if main_class_id:
            self._collect_parents(main_class_id, result["parents"])

        # 找子类
        for node_id, node_data in self._graph.nodes(data=True):
            if node_data.get("type") != "class":
                continue
            for succ_id in self._graph.successors(node_id):
                succ_data = self._graph.nodes[succ_id].get("data")
                if succ_data and succ_data.name == class_name:
                    cls_data = node_data.get("data")
                    if cls_data:
                        result["children"].append({
                            "class": cls_data.name,
                            "file_path": cls_data.file_path,
                            "line": cls_data.line_number,
                        })

        return result

    def _collect_parents(self, class_id: str, collected: List[Dict], depth: int = 0):
        """递归收集父类链"""
        if depth > 10:  # 安全上限
            return
        for succ_id in self._graph.successors(class_id):
            edge_data = self._graph.get_edge_data(class_id, succ_id)
            if edge_data and edge_data.get("type") == EdgeType.INHERITS:
                succ_data = self._graph.nodes[succ_id].get("data")
                if succ_data:
                    collected.append({
                        "class": succ_data.name,
                        "file_path": succ_data.file_path,
                        "line": succ_data.line_number,
                    })
                self._collect_parents(succ_id, collected, depth + 1)

    def get_module_deps(self, module_name: str) -> Dict[str, Any]:
        """
        返回模块的 import 依赖图

        Returns:
            {"module": str, "file_path": str, "imports": [...], "imported_by": [...]}
        """
        result = {
            "module": module_name,
            "file_path": "",
            "imports": [],
            "imported_by": [],
        }

        # 找模块节点
        module_id = None
        for node_id, node_data in self._graph.nodes(data=True):
            if node_data.get("type") != "module":
                continue
            mod_data = node_data.get("data")
            if mod_data and mod_data.module_name == module_name:
                module_id = node_id
                result["file_path"] = mod_data.module_path
                break

        if not module_id:
            return result

        # IMPORTS 出边
        for succ_id in self._graph.successors(module_id):
            edge_data = self._graph.get_edge_data(module_id, succ_id)
            if edge_data and edge_data.get("type") == EdgeType.IMPORTS:
                succ_data = self._graph.nodes[succ_id].get("data")
                if succ_data:
                    result["imports"].append({
                        "module": succ_data.module_name,
                        "file_path": succ_data.module_path,
                    })

        # IMPORTS 入边（谁导入了我）
        for pred_id in self._graph.predecessors(module_id):
            edge_data = self._graph.get_edge_data(pred_id, module_id)
            if edge_data and edge_data.get("type") == EdgeType.IMPORTS:
                pred_data = self._graph.nodes[pred_id].get("data")
                if pred_data:
                    result["imported_by"].append({
                        "module": pred_data.module_name,
                        "file_path": pred_data.module_path,
                    })

        return result

    def get_stats(self) -> Dict[str, int]:
        """返回图统计"""
        node_types = {"module": 0, "class": 0, "function": 0}
        edge_types = {EdgeType.CONTAINS: 0, EdgeType.INHERITS: 0,
                      EdgeType.IMPORTS: 0, EdgeType.CALLS: 0}
        for _, data in self._graph.nodes(data=True):
            t = data.get("type", "unknown")
            node_types[t] = node_types.get(t, 0) + 1
        for _, _, data in self._graph.edges(data=True):
            t = data.get("type", "unknown")
            edge_types[t] = edge_types.get(t, 0) + 1

        return {
            "total_nodes": self._graph.number_of_nodes(),
            "total_edges": self._graph.number_of_edges(),
            "modules": node_types.get("module", 0),
            "classes": node_types.get("class", 0),
            "functions": node_types.get("function", 0),
            "contains_edges": edge_types.get(EdgeType.CONTAINS, 0),
            "inherits_edges": edge_types.get(EdgeType.INHERITS, 0),
            "imports_edges": edge_types.get(EdgeType.IMPORTS, 0),
            "calls_edges": edge_types.get(EdgeType.CALLS, 0),
        }

    # ── 持久化 ──

    def save_graph(self, path: str) -> bool:
        """
        使用 pickle 将 networkx 图序列化到磁盘

        Args:
            path: 文件路径（通常以 .pkl 结尾）

        Returns:
            是否成功
        """
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "wb") as f:
                pickle.dump(self._graph, f, protocol=pickle.HIGHEST_PROTOCOL)
            return True
        except Exception:
            return False

    def load_graph(self, path: str) -> bool:
        """
        从磁盘加载 pickle 序列化的 networkx 图

        Args:
            path: 文件路径

        Returns:
            是否成功
        """
        if not os.path.isfile(path):
            return False
        try:
            with open(path, "rb") as f:
                self._graph = pickle.load(f)
            return True
        except Exception:
            return False

    # ── 工具函数 ──

    @staticmethod
    def _make_module_id(file_path: str) -> str:
        return f"module:{file_path}"

    @staticmethod
    def _make_class_id(file_path: str, class_name: str) -> str:
        return f"class:{file_path}::{class_name}"

    @staticmethod
    def _make_function_id(file_path: str, func_name: str, parent_class: str = "") -> str:
        if parent_class:
            return f"function:{file_path}::{parent_class}.{func_name}"
        return f"function:{file_path}::{func_name}"

    @staticmethod
    def _compute_module_name(file_path: str, project_root: str) -> str:
        """计算模块名（去掉项目根目录和 .py 后缀，路径分隔符替换为 .）"""
        try:
            rel = os.path.relpath(file_path, project_root)
        except ValueError:
            rel = file_path
        if rel.endswith(".py"):
            rel = rel[:-3]
        return rel.replace(os.sep, ".")

```
