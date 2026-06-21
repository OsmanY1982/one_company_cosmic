# `iqra/core/code_graph/__init__.py`

> 路径：`iqra/core/code_graph/__init__.py` | 行数：456


---


```python
# -*- coding: utf-8 -*-
"""
CodeGraph — 代码知识图谱

让开发者用自然语言查询代码结构:
  - 类继承关系   → get_class_hierarchy("MemoryStore")
  - 函数调用链   → get_callers("chat") / get_callees("chat")
  - 模块依赖     → get_module_deps("chat_engine")
  - 语义搜索     → query("记忆系统")

架构:
  AST 解析 (ast_parser) → 图存储 (graph_store) → 语义搜索 (SemanticSearcher)

依赖: networkx>=3.0（可选，缺失时图存储降级）
      sentence-transformers + faiss-cpu（可选，缺失时 query() 仅用名称匹配）

用法:
    from iqra.core.code_graph import CodeGraph

    cg = CodeGraph()
    cg.build_graph("/path/to/project")
    results = cg.query("记忆系统")
    callers = cg.get_callers("chat")
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

# ── 尝试导入依赖 ──
try:
    from .graph_store import CodeGraphStore
    _HAVE_NETWORKX = True
except ImportError:
    _HAVE_NETWORKX = False
    CodeGraphStore = None

try:
    from .ast_parser import scan_project, parse_file, ParseResult
    _HAVE_AST_PARSER = True
except ImportError:
    _HAVE_AST_PARSER = False
    scan_project = None
    parse_file = None
    ParseResult = None

try:
    from ..semantic_search import SemanticSearcher
    _HAVE_SEMANTIC_SEARCH = True
except ImportError:
    _HAVE_SEMANTIC_SEARCH = False
    SemanticSearcher = None


# ═══════════════════════════════════════════
# CodeGraph
# ═══════════════════════════════════════════

class CodeGraph:
    """
    代码知识图谱 — 对代码库的结构化探索

    将 AST 解析结果加载到 networkx 有向图，
    支持自然语言查询、调用链分析、继承链分析、模块依赖分析。
    """

    def __init__(self):
        self._store = CodeGraphStore() if _HAVE_NETWORKX else None
        self._searcher = None         # SemanticSearcher（lazy init）
        self._parse_results: List = []  # 原始 ParseResult 列表
        self._project_root: str = ""
        self._built: bool = False

        # embedding 文本索引
        self._element_texts: List[str] = []        # "function:name — docstring"
        self._element_nodes: List[dict] = []       # {"type", "name", "file_path", "line"}

    # ── 属性 ──

    @property
    def is_built(self) -> bool:
        return self._built

    @property
    def node_count(self) -> int:
        return self._store.node_count if self._store else 0

    @property
    def edge_count(self) -> int:
        return self._store.edge_count if self._store else 0

    # ── 构建 ──

    def build_graph(self, root_dir: str) -> Dict[str, int]:
        """
        扫描项目中所有 .py 文件，提取代码元素并构建知识图谱

        Args:
            root_dir: 项目根目录（绝对路径）

        Returns:
            统计信息: {"files": N, "classes": N, "functions": N, "calls": N, ...}
        """
        if not _HAVE_AST_PARSER or not scan_project:
            raise ImportError("AST parser not available")

        self._project_root = os.path.abspath(root_dir)
        self._parse_results = scan_project(self._project_root)

        stats = {
            "files": len(self._parse_results),
            "classes": 0,
            "functions": 0,
            "calls": 0,
            "imports": 0,
        }
        for pr in self._parse_results:
            stats["classes"] += len(pr.classes)
            stats["functions"] += len(pr.functions)
            stats["calls"] += len(pr.calls)
            stats["imports"] += len(pr.imports)

        # 构建图存储
        if self._store:
            self._store.build_from_parse_results(self._parse_results, self._project_root)
            graph_stats = self._store.get_stats()
            stats.update(graph_stats)

        # 构建 embedding 文本索引
        self._build_text_index()

        self._built = True
        return stats

    def _build_text_index(self) -> None:
        """构建文本索引，用于 embedding 搜索"""
        self._element_texts = []
        self._element_nodes = []

        for pr in self._parse_results:
            # 类
            for cls in pr.classes:
                text = f"class {cls.name}"
                if cls.docstring:
                    text += f" — {cls.docstring}"
                if cls.bases:
                    text += f" (inherits: {', '.join(cls.bases)})"
                self._element_texts.append(text)
                self._element_nodes.append({
                    "type": "class",
                    "name": cls.name,
                    "file_path": pr.file_path,
                    "line": cls.line_number,
                    "bases": cls.bases,
                    "docstring": cls.docstring,
                })

            # 函数/方法
            for fn in pr.functions:
                prefix = f"{fn.parent_class}." if fn.parent_class else ""
                text = f"function {prefix}{fn.name}"
                if fn.docstring:
                    text += f" — {fn.docstring}"
                if fn.params:
                    text += f" (params: {', '.join(fn.params)})"
                self._element_texts.append(text)
                self._element_nodes.append({
                    "type": "function",
                    "name": fn.name,
                    "file_path": pr.file_path,
                    "line": fn.line_number,
                    "parent_class": fn.parent_class,
                    "params": fn.params,
                    "docstring": fn.docstring,
                })

    # ── 自然语言查询 ──

    def query(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        用自然语言查询代码知识图谱

        优先使用 SemanticSearcher 做 embedding 搜索，
        缺失时降级为名称关键词匹配。

        Args:
            query_text: 自然语言查询（如 "记忆系统"、"消息发送流程"）
            top_k: 返回前 k 个结果

        Returns:
            [{"type": "class"/"function", "name": str, "file_path": str,
              "line": int, "score": float, "docstring": str}, ...]
        """
        if not self._built or not self._element_texts:
            return []

        # 尝试语义搜索
        if _HAVE_SEMANTIC_SEARCH and SemanticSearcher:
            return self._semantic_query(query_text, top_k)

        # 降级：名称关键词匹配
        return self._keyword_query(query_text, top_k)

    def _semantic_query(self, query_text: str, top_k: int) -> List[Dict[str, Any]]:
        """向量语义搜索"""
        try:
            if self._searcher is None:
                self._searcher = SemanticSearcher()
            if not self._searcher.is_ready:
                self._searcher.build_index(self._element_texts)

            hits = self._searcher.search_with_metadata(query_text, top_k)
            results = []
            for h in hits:
                idx = h["index"]
                if idx < len(self._element_nodes):
                    node = dict(self._element_nodes[idx])
                    node["score"] = h["score"]
                    results.append(node)
            return results
        except Exception:
            return self._keyword_query(query_text, top_k)

    def _keyword_query(self, query_text: str, top_k: int) -> List[Dict[str, Any]]:
        """名称关键词匹配（降级方案）"""
        query_lower = query_text.lower()
        scored = []
        for i, text in enumerate(self._element_texts):
            text_lower = text.lower()
            score = 0.0
            # 精确名称匹配
            name = self._element_nodes[i]["name"].lower()
            if query_lower in name:
                score += 1.0
            elif name in query_lower:
                score += 0.8
            # 文本包含匹配
            if query_lower in text_lower:
                score += 0.5
            # 部分词匹配
            words = query_lower.split()
            for w in words:
                if w in text_lower:
                    score += 0.2

            if score > 0:
                node = dict(self._element_nodes[i])
                node["score"] = round(score, 3)
                scored.append(node)

        scored.sort(key=lambda x: -x["score"])
        return scored[:top_k]

    # ── 调用链查询 ──

    def get_callers(self, func_name: str) -> List[Dict[str, Any]]:
        """
        返回所有调用指定函数的代码位置

        Args:
            func_name: 函数名

        Returns:
            [{"caller": "xxx", "parent_class": "...", "file_path": "...", "line": N}, ...]
        """
        if not self._store:
            return self._fallback_callers(func_name)
        return self._store.get_callers(func_name)

    def _fallback_callers(self, func_name: str) -> List[Dict[str, Any]]:
        """无 networkx 时的降级调用者查找"""
        results = []
        for pr in self._parse_results:
            for call in pr.calls:
                if call.callee_name == func_name:
                    results.append({
                        "caller": call.caller_name,
                        "parent_class": call.caller_parent_class,
                        "file_path": call.caller_file,
                        "line": call.caller_line,
                        "call_line": call.line_number,
                    })
        return results

    def get_callees(self, func_name: str) -> List[Dict[str, Any]]:
        """
        返回该函数调用的所有其他函数

        Returns:
            [{"callee": "xxx", "parent_class": "...", "file_path": "...", "line": N}, ...]
        """
        if not self._store:
            return self._fallback_callees(func_name)
        return self._store.get_callees(func_name)

    def _fallback_callees(self, func_name: str) -> List[Dict[str, Any]]:
        """无 networkx 时的降级被调用者查找"""
        results = []
        for pr in self._parse_results:
            for call in pr.calls:
                if call.caller_name == func_name:
                    # 尝试在 parse results 中找被调用函数位置
                    callee_file = pr.file_path
                    callee_line = call.line_number
                    # 搜索其他 parse result
                    for other_pr in self._parse_results:
                        for fn in other_pr.functions:
                            if fn.name == call.callee_name:
                                callee_file = fn.file_path
                                callee_line = fn.line_number
                                break
                    results.append({
                        "callee": call.callee_name,
                        "parent_class": call.caller_parent_class,
                        "file_path": callee_file,
                        "line": callee_line,
                        "call_line": call.line_number,
                    })
        return results

    # ── 继承链查询 ──

    def get_class_hierarchy(self, class_name: str) -> Dict[str, Any]:
        """
        返回类的完整继承链

        Returns:
            {"class": str, "file_path": str, "parents": [...], "children": [...], "methods": [...]}
        """
        if not self._store:
            return self._fallback_class_hierarchy(class_name)
        return self._store.get_class_hierarchy(class_name)

    def _fallback_class_hierarchy(self, class_name: str) -> Dict[str, Any]:
        """无 networkx 时的降级继承链查找"""
        result = {
            "class": class_name,
            "file_path": "",
            "line": 0,
            "parents": [],
            "children": [],
            "methods": [],
        }
        for pr in self._parse_results:
            for cls in pr.classes:
                if cls.name == class_name:
                    result["file_path"] = pr.file_path
                    result["line"] = cls.line_number
                    result["methods"] = cls.methods
                    result["parents"] = [{"class": b, "file_path": "__unknown__", "line": 0} for b in cls.bases]
                # 子类
                for base in cls.bases:
                    if base == class_name:
                        result["children"].append({
                            "class": cls.name,
                            "file_path": pr.file_path,
                            "line": cls.line_number,
                        })
        return result

    # ── 模块依赖查询 ──

    def get_module_deps(self, module_name: str) -> Dict[str, Any]:
        """
        返回模块的 import 依赖图

        Returns:
            {"module": str, "file_path": str, "imports": [...], "imported_by": [...]}
        """
        if not self._store:
            return self._fallback_module_deps(module_name)
        return self._store.get_module_deps(module_name)

    def _fallback_module_deps(self, module_name: str) -> Dict[str, Any]:
        """无 networkx 时的降级模块依赖查找"""
        result = {
            "module": module_name,
            "file_path": "",
            "imports": [],
            "imported_by": [],
        }
        for pr in self._parse_results:
            mod_name = self._make_mod_name(pr.file_path)
            if mod_name == module_name:
                result["file_path"] = pr.file_path
                for imp in pr.imports:
                    result["imports"].append({
                        "module": imp.module,
                        "names": imp.names,
                    })
            # 谁导入了此模块
            for imp in pr.imports:
                if imp.module == module_name or module_name in imp.names:
                    result["imported_by"].append({
                        "module": self._make_mod_name(pr.file_path),
                        "file_path": pr.file_path,
                    })
        return result

    def _make_mod_name(self, file_path: str) -> str:
        try:
            rel = os.path.relpath(file_path, self._project_root)
        except ValueError:
            rel = file_path
        if rel.endswith(".py"):
            rel = rel[:-3]
        return rel.replace(os.sep, ".")

    # ── 图统计 ──

    def get_stats(self) -> Dict[str, Any]:
        """返回代码图谱统计信息"""
        base = {
            "project_root": self._project_root,
            "files": len(self._parse_results),
            "elements": len(self._element_nodes),
            "has_graph_store": self._store is not None,
            "has_semantic_search": _HAVE_SEMANTIC_SEARCH,
            "built": self._built,
        }
        if self._store:
            base.update(self._store.get_stats())
        return base

    # ── 持久化 ──

    def save_graph(self, path: str) -> bool:
        """保存图到磁盘"""
        if self._store:
            return self._store.save_graph(path)
        return False

    def load_graph(self, path: str) -> bool:
        """从磁盘加载图"""
        if self._store:
            success = self._store.load_graph(path)
            if success:
                self._built = True
            return success
        return False

    def save_index(self, path: str) -> bool:
        """保存 embedding 索引到磁盘"""
        if self._searcher and self._searcher.is_ready:
            return self._searcher.save_index(path)
        return False

    def load_index(self, path: str) -> bool:
        """从磁盘加载 embedding 索引"""
        if _HAVE_SEMANTIC_SEARCH and SemanticSearcher:
            try:
                self._searcher = SemanticSearcher()
                return self._searcher.load_index(path)
            except Exception:
                return False
        return False

```
