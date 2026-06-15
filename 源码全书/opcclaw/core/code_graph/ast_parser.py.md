# `opcclaw/core/code_graph/ast_parser.py`

> 路径：`opcclaw/core/code_graph/ast_parser.py` | 行数：341


---


```python
# -*- coding: utf-8 -*-
"""
AST 解析器 — 遍历 Python 源文件提取结构化代码元素

提取节点类型:
  - ClassNode:     类定义（含继承链）
  - FunctionNode:  函数/方法定义（含参数、docstring、父类）
  - ImportNode:    导入语句（模块/符号/别名）
  - CallNode:      函数调用（调用者→被调用者关系）

每个节点记录 file_path + line_number + parent 关系。
仅处理 .py 文件，跳过 tests/ 和 venv/ 目录。
"""

import ast
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Set
from pathlib import Path


# ═══════════════════════════════════════════
# 节点数据结构
# ═══════════════════════════════════════════

@dataclass
class ClassNode:
    name: str
    file_path: str
    line_number: int
    end_line: int = 0
    bases: List[str] = field(default_factory=list)        # 继承的父类名
    docstring: str = ""
    decorators: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)       # 方法名列表


@dataclass
class FunctionNode:
    name: str
    file_path: str
    line_number: int
    end_line: int = 0
    params: List[str] = field(default_factory=list)        # 参数名列表
    docstring: str = ""
    decorators: List[str] = field(default_factory=list)
    parent_class: str = ""                                  # 所属类名（方法）
    is_async: bool = False
    return_annotation: str = ""


@dataclass
class ImportNode:
    module: str
    file_path: str
    line_number: int
    names: List[str] = field(default_factory=list)         # 导入的符号名
    alias: str = ""
    is_relative: bool = False                               # from .xxx import y


@dataclass
class CallNode:
    caller_name: str                                        # 发起调用的函数名
    caller_file: str
    callee_name: str                                        # 被调用的函数名
    line_number: int
    caller_line: int = 0                                    # caller 函数的起始行
    caller_parent_class: str = ""                            # caller 的父类


@dataclass
class ParseResult:
    """单文件解析结果"""
    file_path: str
    classes: List[ClassNode] = field(default_factory=list)
    functions: List[FunctionNode] = field(default_factory=list)
    imports: List[ImportNode] = field(default_factory=list)
    calls: List[CallNode] = field(default_factory=list)
    module_docstring: str = ""


# ═══════════════════════════════════════════
# 跳过目录
# ═══════════════════════════════════════════

SKIP_DIRS = {
    "tests", "test", "__pycache__", "venv", ".venv", "env", ".env",
    "node_modules", ".git", ".svn", "dist", "build", ".tox",
    ".egg-info", ".mypy_cache", ".pytest_cache", ".ruff_cache",
}


def _should_skip_path(path: str, root_dir: str) -> bool:
    """判断某路径是否应跳过"""
    rel = os.path.relpath(path, root_dir)
    parts = Path(rel).parts
    for part in parts:
        if part in SKIP_DIRS or part.startswith("."):
            return True
    return False


# ═══════════════════════════════════════════
# AST 节点提取器
# ═══════════════════════════════════════════

class CodeGraphASTVisitor(ast.NodeVisitor):
    """增强版 AST 遍历器 — 提取类/函数/导入/调用 + 父子关系"""

    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self._lines = source_lines

        # 提取结果
        self.classes: List[ClassNode] = []
        self.functions: List[FunctionNode] = []
        self.imports: List[ImportNode] = []
        self.calls: List[CallNode] = []

        # 上下文栈
        self._current_class: str = ""
        self._current_function: str = ""
        self._current_function_line: int = 0

    # ── 函数/方法 ──

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._handle_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._handle_function(node, is_async=True)

    def _handle_function(self, node, is_async: bool):
        # 提取参数
        params = [arg.arg for arg in node.args.args]
        if node.args.vararg:
            params.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            params.append(f"**{node.args.kwarg.arg}")

        # 返回类型
        returns = ""
        if node.returns:
            try:
                returns = ast.unparse(node.returns)
            except Exception:
                pass

        fn = FunctionNode(
            name=node.name,
            file_path=self.file_path,
            line_number=node.lineno,
            end_line=node.end_lineno or node.lineno,
            params=params,
            docstring=ast.get_docstring(node) or "",
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            parent_class=self._current_class,
            is_async=is_async,
            return_annotation=returns,
        )
        self.functions.append(fn)

        # 进入函数体，遍历调用
        prev_fn = self._current_function
        prev_fn_line = self._current_function_line
        self._current_function = node.name
        self._current_function_line = node.lineno
        self.generic_visit(node)
        self._current_function = prev_fn
        self._current_function_line = prev_fn_line

    # ── 类 ──

    def visit_ClassDef(self, node: ast.ClassDef):
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                try:
                    bases.append(ast.unparse(base))
                except Exception:
                    bases.append(f"...{base.attr}")

        cls = ClassNode(
            name=node.name,
            file_path=self.file_path,
            line_number=node.lineno,
            end_line=node.end_lineno or node.lineno,
            bases=bases,
            docstring=ast.get_docstring(node) or "",
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
        )
        self.classes.append(cls)

        # 进入类体，收集方法名
        prev_class = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        cls.methods = [
            f.name for f in self.functions
            if f.parent_class == node.name and f.file_path == self.file_path
        ]
        self._current_class = prev_class

    # ── 调用 ──

    def visit_Call(self, node: ast.Call):
        if not self._current_function:
            self.generic_visit(node)
            return

        callee = self._resolve_callee(node.func)
        if callee:
            self.calls.append(CallNode(
                caller_name=self._current_function,
                caller_file=self.file_path,
                callee_name=callee,
                line_number=node.lineno,
                caller_line=self._current_function_line,
                caller_parent_class=self._current_class,
            ))
        self.generic_visit(node)

    def _resolve_callee(self, func_node) -> Optional[str]:
        """解析被调用函数名"""
        if isinstance(func_node, ast.Name):
            return func_node.id
        if isinstance(func_node, ast.Attribute):
            # obj.method() → 记录 method，忽略 obj
            return func_node.attr
        if isinstance(func_node, ast.Call):
            # decorator()() → 递归
            return self._resolve_callee(func_node.func)
        # 忽略 lambda / 字面量调用
        return None

    # ── 导入 ──

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(ImportNode(
                module=alias.name,
                file_path=self.file_path,
                line_number=node.lineno,
                names=[alias.asname or alias.name],
                alias=alias.asname or "",
                is_relative=False,
            ))

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            self.imports.append(ImportNode(
                module=module,
                file_path=self.file_path,
                line_number=node.lineno,
                names=[alias.asname or alias.name],
                alias=alias.asname or "",
                is_relative=node.level > 0,
            ))

    # ── 辅助 ──

    @staticmethod
    def _get_decorator_name(node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            try:
                return ast.unparse(node)
            except Exception:
                return f"...{node.attr}"
        if isinstance(node, ast.Call):
            return CodeGraphASTVisitor._get_decorator_name(node.func)
        return "..."


# ═══════════════════════════════════════════
# 文件解析器
# ═══════════════════════════════════════════

def parse_file(file_path: str) -> Optional[ParseResult]:
    """解析单个 .py 文件，返回结构化的 ParseResult"""
    if not file_path.endswith(".py"):
        return None
    if not os.path.isfile(file_path):
        return None

    try:
        source = Path(file_path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError:
        return None

    lines = source.split("\n")
    visitor = CodeGraphASTVisitor(file_path, lines)
    visitor.visit(tree)

    module_doc = ast.get_docstring(tree) or ""

    return ParseResult(
        file_path=file_path,
        classes=visitor.classes,
        functions=visitor.functions,
        imports=visitor.imports,
        calls=visitor.calls,
        module_docstring=module_doc,
    )


def scan_project(root_dir: str) -> List[ParseResult]:
    """
    扫描项目中的所有 .py 文件并解析

    自动跳过 tests/ / venv/ / __pycache__/ 等目录。
    """
    results: List[ParseResult] = []
    root_dir = os.path.abspath(root_dir)

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # 过滤目录
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.startswith(".")
        ]

        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(dirpath, fname)
            parsed = parse_file(fpath)
            if parsed and (parsed.classes or parsed.functions or parsed.imports or parsed.calls):
                results.append(parsed)

    return results

```
