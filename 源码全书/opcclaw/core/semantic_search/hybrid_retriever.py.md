# `opcclaw/core/semantic_search/hybrid_retriever.py`

> 路径：`opcclaw/core/semantic_search/hybrid_retriever.py` | 行数：242


---


```python
# -*- coding: utf-8 -*-
"""
HybridRetriever — BM25 + Embedding 向量混合检索器

策略:
  1. BM25 做初筛（top_k × 3 召回），保证召回率
  2. Embedding 向量搜索做精排（top_k），提升语义匹配精度
  3. 如果 SemanticSearcher 为 None（依赖未安装），自动降级为纯 BM25

用法:
    from opcclaw.core.workspace_indexer import WorkspaceIndexer, BM25
    from opcclaw.core.semantic_search import SemanticSearcher
    from opcclaw.core.semantic_search.hybrid_retriever import HybridRetriever

    bm25_retriever = indexer  # WorkspaceIndexer 实例
    semantic = SemanticSearcher()

    hr = HybridRetriever(bm25_retriever, semantic_searcher=semantic)
    results = hr.search("如何处理用户登录的安全问题", top_k=5)
"""

from typing import List, Tuple, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from opcclaw.core.workspace_indexer import WorkspaceIndexer, SearchResult
    from opcclaw.core.semantic_search import SemanticSearcher


# BM25 召回倍数（初筛阶段用 BM25 召回 top_k × RECALL_MULTIPLIER 结果）
RECALL_MULTIPLIER = 3


class HybridRetriever:
    """
    BM25 + 向量语义混合检索器

    如果 SemanticSearcher 不可用（依赖未安装），自动降级为纯 BM25，对外接口不变。
    """

    def __init__(self, bm25_retriever, semantic_searcher=None):
        """
        Args:
            bm25_retriever: WorkspaceIndexer 实例（提供 search() 方法返回 List[SearchResult]）
            semantic_searcher: SemanticSearcher 实例，None 则降级为纯 BM25
        """
        self._bm25 = bm25_retriever
        self._semantic = semantic_searcher

    @property
    def has_semantic(self) -> bool:
        return self._semantic is not None and self._semantic.is_ready

    @property
    def mode(self) -> str:
        """'hybrid' 或 'bm25_only'"""
        return "hybrid" if self.has_semantic else "bm25_only"

    # ── 搜索 ──

    def search(
        self,
        query: str,
        top_k: int = 5,
        use_semantic: bool = True,
    ):
        """
        混合检索 — BM25 初筛 → Embedding 精排

        Args:
            query: 查询字符串
            top_k: 最终返回数量
            use_semantic: 是否启用语义精排（设 False 可强制纯 BM25）

        Returns:
            List[SearchResult] 按相关性降序
        """
        recall_k = top_k * RECALL_MULTIPLIER

        # Phase 1: BM25 初筛
        bm25_results = self._bm25.search(query, top_k=recall_k)

        if not bm25_results:
            return []

        # 如果语义搜索不可用或用户关闭，直接返回 BM25 结果
        if not self.has_semantic or not use_semantic:
            return bm25_results[:top_k]

        # Phase 2: Embedding 精排
        return self._semantic_rerank(query, bm25_results, top_k)

    def _semantic_rerank(self, query: str, candidates, top_k: int):
        """
        对 BM25 召回候选做向量相似度精排

        Args:
            query: 查询字符串
            candidates: BM25 返回的 SearchResult 列表
            top_k: 返回前 k 个

        Returns:
            重排后的 SearchResult 列表
        """
        from opcclaw.core.workspace_indexer import SearchResult

        # 收集候选文档内容
        candidate_docs = []
        for r in candidates:
            content = getattr(r, "snippet", "")
            if hasattr(r, "chunk_index"):
                # 从 indexer 内部 chunks 获取完整内容
                chunk_key = (r.file_path, r.chunk_index)
                candidate_docs.append((r, chunk_key, content))
            else:
                candidate_docs.append((r, None, content))

        # 向量检索
        if len(candidate_docs) <= top_k:
            return candidates[:top_k]

        # 构建临时索引并搜索
        contents = [c[2] for c in candidate_docs]
        temp_scores = self._compute_similarities(query, contents)

        # 按相似度排序
        ranked = sorted(
            zip(candidate_docs, temp_scores),
            key=lambda x: x[1],
            reverse=True,
        )

        # 更新分数并返回
        results = []
        for (sr, _, _), sim_score in ranked[:top_k]:
            # 混合分数：BM25 占 30%，向量占 70%
            combined_score = 0.3 * sr.score + 0.7 * sim_score
            results.append(SearchResult(
                file_path=sr.file_path,
                chunk_index=sr.chunk_index,
                score=round(combined_score, 4),
                snippet=sr.snippet,
                file_type=getattr(sr, "file_type", ""),
            ))

        return results

    def _compute_similarities(self, query: str, documents: List[str]) -> List[float]:
        """计算查询与文档列表的向量相似度"""
        if not self._semantic or not self._semantic.is_ready:
            return [0.0] * len(documents)

        if not documents:
            return []

        try:
            self._semantic._ensure_model()
            q_vec = self._semantic._model.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            doc_vecs = self._semantic._model.encode(
                documents,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )

            import numpy as np
            similarities = np.dot(doc_vecs, q_vec.T).flatten()
            # 将 [-1, 1] 映射到 [0, 1]
            return [max(0.0, float(s)) for s in similarities]
        except Exception:
            return [0.0] * len(documents)

    # ── 上下文注入 ──

    def get_context(
        self,
        query: str,
        max_chars: int = 4000,
        top_k: int = 5,
        use_semantic: bool = True,
    ) -> str:
        """
        获取与查询最相关的文件上下文（用于注入到 LLM prompt）

        转发到 WorkspaceIndexer.get_context()，但使用混合检索结果作为文件候选。

        Args:
            query: 查询字符串
            max_chars: 最大返回字符数
            top_k: 最多返回文件数
            use_semantic: 是否启用语义搜索

        Returns:
            格式化的上下文字符串
        """
        # 使用混合检索获取结果，再提取上下文
        search_results = self.search(query, top_k=max(top_k, 10), use_semantic=use_semantic)

        if not search_results:
            return ""

        # 按文件去重，取分数最高的 top_k 个文件
        seen_files = set()
        top_files = []
        for r in search_results:
            if r.file_path not in seen_files and len(top_files) < top_k:
                seen_files.add(r.file_path)
                top_files.append(r)

        import os
        context_parts = []
        total_chars = 0
        char_budget = max_chars // max(len(top_files), 1)

        for sr in top_files:
            try:
                with open(sr.file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception:
                continue

            if total_chars + len(content) <= max_chars:
                context_parts.append(f"## {sr.file_path}\n```\n{content}\n```\n")
                total_chars += len(content)
            else:
                trimmed = content[:char_budget]
                context_parts.append(f"## {sr.file_path} (preview)\n```\n{trimmed}\n...\n```\n")
                total_chars += len(trimmed)

        return "\n".join(context_parts)

    # ── 管理 ──

    def set_semantic(self, searcher) -> None:
        """设置/替换 SemanticSearcher 实例"""
        self._semantic = searcher

    def clear(self) -> None:
        if self._semantic:
            self._semantic.clear()

```
