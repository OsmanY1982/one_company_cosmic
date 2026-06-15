# `opcclaw/core/semantic_search/__init__.py`

> 路径：`opcclaw/core/semantic_search/__init__.py` | 行数：226


---


```python
# -*- coding: utf-8 -*-
"""
SemanticSearcher — Embedding 向量语义搜索（sentence-transformers + FAISS）

职责:
  1. 将文档块编码为向量并构建 FAISS 索引
  2. 对查询做向量相似度搜索
  3. 索引磁盘持久化（save/load）

可选依赖（不安装自动跳过，不影响引擎主流程）：
  - sentence-transformers>=2.2.0
  - faiss-cpu>=1.7.0
"""

import os
import pickle
from typing import List, Tuple, Optional, Dict, Any

try:
    from sentence_transformers import SentenceTransformer
    _HAVE_ST = True
except ImportError:
    _HAVE_ST = False
    SentenceTransformer = None

try:
    import faiss
    import numpy as np
    _HAVE_FAISS = True
except ImportError:
    _HAVE_FAISS = False
    faiss = None
    np = None


class SemanticSearcher:
    """向量语义搜索器 — FAISS 索引 + sentence-transformers embedding"""

    # 默认模型（轻量、384 维、本地运行）
    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(self, model_name: str = ""):
        """
        Args:
            model_name: sentence-transformers 模型名，空则使用默认模型
        """
        if not _HAVE_ST or not _HAVE_FAISS:
            raise ImportError(
                "SemanticSearcher requires sentence-transformers and faiss-cpu. "
                "Install with: pip install sentence-transformers faiss-cpu"
            )

        self._model_name = model_name or self.DEFAULT_MODEL
        self._model: Optional[SentenceTransformer] = None
        self._index: Optional[faiss.Index] = None
        self._documents: List[str] = []
        self._metadatas: List[dict] = []
        self._dimension: int = 0

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def is_ready(self) -> bool:
        return self._model is not None and self._index is not None

    @property
    def doc_count(self) -> int:
        return len(self._documents)

    # ── 模型加载 ──

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        self._model = SentenceTransformer(self._model_name)
        self._dimension = self._model.get_sentence_embedding_dimension()

    # ── 索引构建 ──

    def build_index(self, documents: List[str], metadatas: Optional[List[dict]] = None) -> int:
        """
        构建 FAISS 索引

        Args:
            documents: 文档块列表（字符串）
            metadatas: 对应元数据列表，需与 documents 等长

        Returns:
            索引中的文档数量
        """
        if not documents:
            return 0

        self._ensure_model()

        embeddings = self._model.encode(
            documents,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,  # L2 归一化 → 内积 = 余弦相似度
        )

        self._dimension = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(self._dimension)  # Inner Product（余弦相似度）
        self._index.add(embeddings.astype("float32"))

        self._documents = documents
        self._metadatas = metadatas or [{}] * len(documents)

        return len(documents)

    # ── 搜索 ──

    def search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        向量相似度搜索

        Args:
            query: 查询字符串
            top_k: 返回前 k 个结果

        Returns:
            [(doc_index, similarity_score), ...]  分数 0~1，越大越相关
        """
        if not self.is_ready or not self._documents:
            return []

        self._ensure_model()
        q_vec = self._model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        scores, indices = self._index.search(q_vec.astype("float32"), min(top_k, len(self._documents)))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self._documents):
                results.append((int(idx), float(score)))

        return results

    def search_with_metadata(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索并返回带元数据的结果

        Returns:
            [{"index": int, "score": float, "content": str, "metadata": dict}, ...]
        """
        hits = self.search(query, top_k)
        return [
            {
                "index": idx,
                "score": score,
                "content": self._documents[idx] if idx < len(self._documents) else "",
                "metadata": self._metadatas[idx] if idx < len(self._metadatas) else {},
            }
            for idx, score in hits
        ]

    # ── 磁盘持久化 ──

    def save_index(self, path: str) -> bool:
        """
        将 FAISS 索引 + 文档 + 元数据保存到磁盘

        Args:
            path: 索引文件路径（不含扩展名，会生成 .faiss + .pkl）

        Returns:
            是否成功
        """
        if not self.is_ready:
            return False

        try:
            faiss.write_index(self._index, f"{path}.faiss")
            with open(f"{path}.pkl", "wb") as f:
                pickle.dump({
                    "model_name": self._model_name,
                    "dimension": self._dimension,
                    "documents": self._documents,
                    "metadatas": self._metadatas,
                }, f)
            return True
        except Exception:
            return False

    def load_index(self, path: str) -> bool:
        """
        从磁盘加载 FAISS 索引

        Args:
            path: 索引文件路径（不含扩展名）

        Returns:
            是否成功
        """
        faiss_path = f"{path}.faiss"
        pkl_path = f"{path}.pkl"
        if not os.path.isfile(faiss_path) or not os.path.isfile(pkl_path):
            return False

        try:
            self._ensure_model()
            self._index = faiss.read_index(faiss_path)

            with open(pkl_path, "rb") as f:
                data = pickle.load(f)
                self._model_name = data.get("model_name", self._model_name)
                self._dimension = data.get("dimension", self._dimension)
                self._documents = data.get("documents", [])
                self._metadatas = data.get("metadatas", [])

            return True
        except Exception:
            return False

    def clear(self) -> None:
        """清空索引"""
        self._index = None
        self._documents = []
        self._metadatas = []

```
