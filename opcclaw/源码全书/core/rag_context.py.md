# `core/rag_context.py`

> 路径：`core/rag_context.py` | 行数：197


---


```python
# -*- coding: utf-8 -*-
"""
RAGContextInjector — 工作区上下文自动注入（对标 Codex 的 Context Engine）

职责:
  1. 管理 WorkspaceIndexer 实例（单例）
  2. 在用户消息前自动注入相关代码上下文
  3. 提供 set_project / unset 切换项目
"""

import os
import threading
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .workspace_indexer import WorkspaceIndexer, SearchResult


def _get_indexer_cls():
    """延迟导入，避免 opcclaw/__init__.py 的 requests 依赖阻塞"""
    from .workspace_indexer import WorkspaceIndexer, SearchResult
    return WorkspaceIndexer, SearchResult


# 上下文注入提示词模板
CONTEXT_PROMPT_PREFIX = """<workspace_context>
以下是当前项目工作区的相关代码文件，请在回答时参考：

{context}

</workspace_context>

"""


class RAGContextInjector:
    """RAG 上下文注入器（线程安全单例）"""

    _instance: Optional["RAGContextInjector"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._indexer = None  # WorkspaceIndexer instance
        self._project_path: str = ""
        self._auto_context_chars: int = 4000  # 自动注入最大字符数
        self._enabled: bool = True

    # ── 项目管理 ──

    def set_project(self, project_path: str, build: bool = False) -> bool:
        """
        设置/切换项目工作区

        Args:
            project_path: 项目根目录路径
            build: 是否立即构建索引

        Returns:
            是否设置成功
        """
        if not os.path.isdir(project_path):
            return False

        self._project_path = os.path.abspath(project_path)
        WSCls, _ = _get_indexer_cls()
        self._indexer = WSCls(self._project_path)

        if build:
            self._indexer.build()

        return True

    @property
    def has_project(self) -> bool:
        return self._indexer is not None and os.path.isdir(self._project_path)

    @property
    def project_path(self) -> str:
        return self._project_path

    @property
    def indexer(self):  # → WorkspaceIndexer | None
        return self._indexer

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, val: bool) -> None:
        self._enabled = val

    # ── 配置 ──

    def get_config(self) -> dict:
        return {
            "project_path": self._project_path,
            "enabled": self._enabled,
            "auto_context_chars": self._auto_context_chars,
            "has_indexer": self._indexer is not None,
        }

    def load_config(self, cfg: dict) -> None:
        self._enabled = cfg.get("enabled", True)
        self._auto_context_chars = cfg.get("auto_context_chars", 4000)
        if cfg.get("project_path"):
            self.set_project(cfg["project_path"])

    # ── 上下文注入 ──

    def inject_context(self, user_message: str, max_chars: int = 0) -> str:
        """
        在用户消息前注入工作区上下文 + 项目规则（OPCCLAW.md）

        Args:
            user_message: 原始用户消息
            max_chars: 上下文最大字符数，0 使用默认值

        Returns:
            注入后的完整消息（或无变更的原始消息）
        """
        if not self._enabled or not self._indexer:
            return user_message

        chars = max_chars or self._auto_context_chars
        context = self._indexer.get_context(user_message, max_chars=chars, top_k=5)

        # 注入项目规则（OPCCLAW.md）
        rules = self.get_project_rules()
        if rules:
            context = rules + "\n\n" + context if context else rules

        if not context:
            return user_message

        return CONTEXT_PROMPT_PREFIX.format(context=context) + user_message

    # ── 项目规则 ──

    def get_project_rules(self) -> str:
        """
        读取项目根目录的 OPCCLAW.md（对标 Claude Code 的 CLAUDE.md）

        Returns:
            OPCCLAW.md 内容（含标记），或空字符串
        """
        if not self._project_path:
            return ""

        rules_paths = [
            os.path.join(self._project_path, "OPCCLAW.md"),
            os.path.join(self._project_path, "opcclaw", "OPCCLAW.md"),
        ]
        for path in rules_paths:
            if os.path.isfile(path):
                try:
                    content = open(path, encoding="utf-8").read()
                    return f"<project_rules>\n{content.strip()}\n</project_rules>"
                except Exception:
                    pass
        return ""

    def search(self, query: str, top_k: int = 10) -> list:
        """直接搜索工作区"""
        if not self._indexer:
            return []
        return self._indexer.search(query, top_k)

    def build_index(self) -> Optional[object]:
        """构建/重建索引"""
        if not self._indexer:
            return None
        return self._indexer.build()

    def update_index(self) -> Optional[object]:
        """增量更新索引"""
        if not self._indexer:
            return None
        return self._indexer.update()

    def clear(self) -> None:
        """清空当前项目"""
        self._project_path = ""
        if self._indexer:
            self._indexer.clear()
            self._indexer = None

```
