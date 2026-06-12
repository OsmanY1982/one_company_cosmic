# `opcclaw/core/workspace_indexer.py`

> 路径：`opcclaw/core/workspace_indexer.py` | 行数：825


---


```python
# -*- coding: utf-8 -*-
"""
WorkspaceIndexer — 工作区代码库索引与语义检索（对标 Codex 的代码库感知）

特性:
  - 扫描项目目录，自动跳过 .gitignore / node_modules / __pycache__ 等
  - 智能分块：代码按函数/类边界，文档按段落/标题
  - BM25 全文检索（纯 Python，零依赖）
  - SQLite 持久化索引，重启不丢失
  - mtime 增量更新：只重新索引变更文件
  - 上下文注入：根据查询自动提取最相关的文件内容

用法:
    from opcclaw.core.workspace_indexer import WorkspaceIndexer

    indexer = WorkspaceIndexer("/path/to/project")
    indexer.build()  # 首次构建（或 indexer.update() 增量更新）

    results = indexer.search("用户登录逻辑", top_k=5)
    # → [SearchResult(path=..., score=0.87, snippet="..."), ...]

    results = indexer.search_semantic("支付接口", top_k=5)  # 语义搜索
    # → BM25 召回 + IDF 余弦重排序，能匹配到"支付宝集成"

    context = indexer.get_context("重构认证模块", max_tokens=2000)
    # → "## /src/auth.py\n...\n## /src/login.py\n..."
"""

import os
import re
import json
import sqlite3
import fnmatch
import hashlib
import time
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Iterator
from collections import defaultdict


# ═══════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════

@dataclass
class SearchResult:
    """搜索结果"""
    file_path: str           # 文件绝对路径
    chunk_index: int         # 块序号
    score: float             # BM25 分数
    snippet: str             # 匹配内容摘要（前 300 字符）
    file_type: str = ""      # 文件类型（py/js/ts/md/...）


@dataclass
class IndexStats:
    """索引统计"""
    total_files: int = 0
    total_chunks: int = 0
    total_size_bytes: int = 0
    last_build_time: float = 0.0
    skipped_patterns: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════

# 默认跳过的目录/文件模式
DEFAULT_SKIP_PATTERNS = [
    # VCS
    ".git", ".svn", ".hg",
    # 依赖
    "node_modules", "vendor", "bower_components",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "venv", ".venv", "env", ".env", "virtualenv",
    ".tox", ".eggs", "*.egg-info",
    # 构建产物
    "dist", "build", "target", "out", ".next", ".nuxt",
    "*.pyc", "*.pyo", "*.class", "*.o", "*.so", "*.dylib",
    "*.exe", "*.dll",
    # 缓存
    ".cache", ".npm", ".yarn",
    # IDE
    ".idea", ".vscode", ".vs", "*.sublime-*",
    # 大文件
    "*.zip", "*.tar.gz", "*.7z", "*.rar",
    "*.jpg", "*.jpeg", "*.png", "*.gif", "*.svg", "*.ico",
    "*.mp3", "*.mp4", "*.wav", "*.avi", "*.mov",
    "*.pdf", "*.docx", "*.xlsx", "*.pptx",
    "*.ttf", "*.woff", "*.woff2", "*.eot",
    "*.lock", "package-lock.json", "yarn.lock",
    # 数据文件
    "*.csv", "*.tsv", "*.jsonl",
]

# 需要索引的代码文件扩展名
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs",
    ".java", ".kt", ".kts", ".scala",
    ".c", ".cpp", ".h", ".hpp", ".cc", ".cxx",
    ".go", ".rs", ".rb", ".php",
    ".swift", ".m", ".mm",
    ".sh", ".bash", ".zsh", ".fish",
    ".sql", ".r", ".lua",
}

# 需要索引的文本文档扩展名
DOC_EXTENSIONS = {
    ".md", ".markdown", ".rst", ".txt",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".json", ".xml", ".html", ".css", ".scss", ".less",
    ".dockerfile", ".makefile", ".cmake",
}

# 分块大小（字符数）
DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 200

# 最大文件大小（字节），超过此大小不分块索引
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


# ═══════════════════════════════════════════
# 分词器
# ═══════════════════════════════════════════

class Tokenizer:
    """中英文混合分词器（轻量级，零依赖）"""

    # 中文 + 英文单词 + 标识符
    _CHINESE_RE = re.compile(r'[\u4e00-\u9fff]+')
    _WORD_RE = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')
    _NUMBER_RE = re.compile(r'\d+')

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """将文本分词为 token 列表"""
        tokens = []

        # 提取中文连续序列
        for m in cls._CHINESE_RE.finditer(text):
            chars = m.group()
            # 中文按单字 + 双字 + 三字 n-gram
            tokens.extend(cls._chinese_ngrams(chars))

        # 提取英文标识符
        for m in cls._WORD_RE.finditer(text):
            word = m.group().lower()
            if len(word) > 1:  # 跳过单字母
                tokens.append(word)
                # 驼峰拆分: getUserInfo → [get, user, info]
                subtokens = cls._split_camel(word)
                if len(subtokens) > 1:
                    tokens.extend([t for t in subtokens if len(t) > 1])

        # 去重保持顺序（用于 IDF 计算）
        return list(dict.fromkeys(tokens))

    @classmethod
    def _chinese_ngrams(cls, text: str) -> List[str]:
        """中文分词：单字 + 双字 + 三字 n-gram"""
        result = []
        for ch in text:
            result.append(ch)
        for i in range(len(text) - 1):
            result.append(text[i:i+2])
        for i in range(len(text) - 2):
            result.append(text[i:i+3])
        return result

    @classmethod
    def _split_camel(cls, word: str) -> List[str]:
        """拆分驼峰命名：getUserInfo → ['get', 'User', 'Info']"""
        parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\b)', word)
        return [p.lower() for p in parts if len(p) > 1]


# ═══════════════════════════════════════════
# 代码分块器
# ═══════════════════════════════════════════

class CodeChunker:
    """智能代码分块：按函数/类边界分割"""

    # 函数/类定义模式（多种语言）
    _DEF_PATTERNS = [
        # Python
        re.compile(r'^\s*(def |class |async def )', re.MULTILINE),
        # JavaScript/TypeScript
        re.compile(r'^\s*(function |class |const \w+ = \(.*\) =>|export (default )?(function|class) )', re.MULTILINE),
        # Java/Kotlin/Scala
        re.compile(r'^\s*(public |private |protected )?(class |interface |enum |fun |def )', re.MULTILINE),
        # Go
        re.compile(r'^\s*func ', re.MULTILINE),
        # Rust
        re.compile(r'^\s*(pub )?fn |^\s*(pub )?struct |^\s*(pub )?impl |^\s*(pub )?trait ', re.MULTILINE),
        # C/C++
        re.compile(r'^\s*\w[\w:*&<>\s]+\s+\w+\s*\([^)]*\)\s*\{', re.MULTILINE),
    ]

    # 文档标题模式
    _HEADING_RE = re.compile(r'^#{1,6}\s+.+$', re.MULTILINE)

    @classmethod
    def chunk_file(cls, content: str, file_path: str, 
                   chunk_size: int = DEFAULT_CHUNK_SIZE,
                   overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[str]:
        """将文件内容分块"""
        ext = Path(file_path).suffix.lower()
        name = Path(file_path).name.lower()

        # 代码文件：尝试按函数/类边界分块
        if ext in CODE_EXTENSIONS:
            return cls._chunk_by_boundaries(content, chunk_size, overlap)

        # Markdown：按标题分块
        if ext in {".md", ".markdown", ".rst"}:
            return cls._chunk_by_headings(content, chunk_size)

        # 默认：固定大小分块
        return cls._chunk_fixed(content, chunk_size, overlap)

    @classmethod
    def _chunk_by_boundaries(cls, content: str, chunk_size: int, overlap: int) -> List[str]:
        """按代码结构边界分块"""
        # 合并所有定义模式匹配位置
        boundaries = {0}  # 起始位置
        for pattern in cls._DEF_PATTERNS:
            for m in pattern.finditer(content):
                boundaries.add(m.start())
        boundaries = sorted(boundaries)

        chunks = []
        for i in range(len(boundaries)):
            start = boundaries[i]
            end = boundaries[i + 1] if i + 1 < len(boundaries) else len(content)
            block = content[start:end]

            # 如果块太大，递归拆分
            if len(block) > chunk_size * 2:
                sub_chunks = cls._chunk_fixed(block, chunk_size, overlap)
                chunks.extend(sub_chunks)
            else:
                chunks.append(block.strip())

        # 去空
        return [c for c in chunks if len(c) > 50]

    @classmethod
    def _chunk_by_headings(cls, content: str, chunk_size: int) -> List[str]:
        """按 Markdown 标题分块"""
        sections = cls._HEADING_RE.split(content)
        chunks = []
        current = ""
        for section in sections:
            if len(current) + len(section) > chunk_size and current:
                chunks.append(current.strip())
                current = section
            else:
                current += "\n" + section
        if current.strip():
            chunks.append(current.strip())
        return [c for c in chunks if len(c) > 30]

    @classmethod
    def _chunk_fixed(cls, content: str, chunk_size: int, overlap: int) -> List[str]:
        """固定大小滑动窗口分块"""
        if len(content) <= chunk_size:
            return [content] if content.strip() else []

        chunks = []
        start = 0
        while start < len(content):
            end = min(start + chunk_size, len(content))
            # 尽量在换行处截断
            if end < len(content):
                nl = content.rfind('\n', start, end)
                if nl > start + chunk_size // 2:
                    end = nl + 1
            chunk = content[start:end].strip()
            if len(chunk) > 50:
                chunks.append(chunk)
            start = end - overlap if end < len(content) else end
        return chunks


# ═══════════════════════════════════════════
# BM25 检索引擎
# ═══════════════════════════════════════════

class BM25:
    """BM25 全文检索（纯 Python 实现）"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._doc_tokens: List[List[str]] = []   # 每篇文档的 token 列表
        self._doc_lengths: List[int] = []         # 每篇文档的 token 数量
        self._avg_doc_len: float = 0.0
        self._df: Dict[str, int] = {}             # document frequency
        self._idf: Dict[str, float] = {}          # IDF cache
        self._num_docs: int = 0

    def index(self, documents: List[str]) -> None:
        """
        索引文档集合

        Args:
            documents: 字符串列表，每个元素为一个文档（块）
        """
        self._doc_tokens = []
        self._doc_lengths = []
        self._df = defaultdict(int)

        for doc in documents:
            tokens = Tokenizer.tokenize(doc)
            self._doc_tokens.append(tokens)
            self._doc_lengths.append(len(tokens))
            for token in set(tokens):
                self._df[token] += 1

        self._num_docs = len(documents)
        self._avg_doc_len = (sum(self._doc_lengths) / self._num_docs) if self._num_docs > 0 else 0

        # 预计算 IDF
        self._idf = {}
        for token, df in self._df.items():
            self._idf[token] = math.log(1 + (self._num_docs - df + 0.5) / (df + 0.5))

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        搜索并返回 (doc_index, score) 列表

        Args:
            query: 查询字符串
            top_k: 返回前 k 个结果
        """
        if not self._doc_tokens:
            return []

        query_tokens = Tokenizer.tokenize(query)
        scores = []

        for doc_idx in range(self._num_docs):
            score = self._score(query_tokens, doc_idx)
            if score > 0:
                scores.append((doc_idx, score))

        # 按分数降序排序
        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]

    def _score(self, query_tokens: List[str], doc_idx: int) -> float:
        """计算单个文档的 BM25 分数"""
        doc_tokens = self._doc_tokens[doc_idx]
        doc_len = self._doc_lengths[doc_idx]

        # 词频
        tf = defaultdict(int)
        for t in doc_tokens:
            tf[t] += 1

        score = 0.0
        for token in query_tokens:
            if token not in tf:
                continue
            idf = self._idf.get(token, 0)
            term_freq = tf[token]
            numerator = term_freq * (self.k1 + 1)
            denominator = term_freq + self.k1 * (1 - self.b + self.b * doc_len / self._avg_doc_len)
            score += idf * numerator / denominator

        return score


# ═══════════════════════════════════════════
# 工作区索引器
# ═══════════════════════════════════════════

class WorkspaceIndexer:
    """
    工作区索引器 — 核心类

    用法:
        indexer = WorkspaceIndexer("/path/to/project")
        indexer.build()                      # 首次全量索引
        indexer.update()                     # 增量更新（只索引变更文件）
        results = indexer.search("登录逻辑")  # 搜索
    """

    def __init__(self, root_path: str, db_path: str = ""):
        """
        Args:
            root_path: 项目根目录（绝对路径）
            db_path: SQLite 索引数据库路径，默认为 root_path/.opcclaw_index.db
        """
        self.root_path = os.path.abspath(root_path)
        self.db_path = db_path or os.path.join(self.root_path, ".opcclaw_index.db")
        self._bm25 = BM25()
        self._chunks: List[dict] = []   # [{file_path, chunk_index, content}, ...]
        self._file_hashes: Dict[str, str] = {}  # file_path → content hash
        self._skipped_patterns: List[str] = []

        self._init_db()
        self._load_skip_patterns()

    # ── 数据库 ──

    def _init_db(self) -> None:
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                file_type TEXT DEFAULT '',
                content_hash TEXT DEFAULT ''
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS file_meta (
                file_path TEXT PRIMARY KEY,
                mtime REAL DEFAULT 0,
                size INTEGER DEFAULT 0,
                content_hash TEXT DEFAULT ''
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS skip_patterns (
                pattern TEXT PRIMARY KEY
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(file_path)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_hash ON chunks(content_hash)")
        self._conn.commit()

    def _load_skip_patterns(self) -> None:
        rows = self._conn.execute("SELECT pattern FROM skip_patterns").fetchall()
        self._skipped_patterns = [r[0] for r in rows]
        if not self._skipped_patterns:
            self._skipped_patterns = list(DEFAULT_SKIP_PATTERNS)

    # ── 文件扫描 ──

    def _should_skip(self, rel_path: str, is_dir: bool = False) -> bool:
        """判断是否应跳过某个文件/目录"""
        parts = Path(rel_path).parts
        name = Path(rel_path).name

        for pattern in self._skipped_patterns:
            # 精确匹配目录名
            if is_dir and pattern == name:
                return True
            # glob 模式匹配
            if fnmatch.fnmatch(name, pattern):
                return True
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            # 匹配路径中的任意部分
            for part in parts:
                if fnmatch.fnmatch(part, pattern):
                    return True

        return False

    def _scan_files(self) -> Iterator[Path]:
        """扫描项目目录，返回需要索引的文件"""
        for root, dirs, files in os.walk(self.root_path):
            # 过滤目录
            dirs[:] = [
                d for d in dirs
                if not self._should_skip(os.path.relpath(os.path.join(root, d), self.root_path), is_dir=True)
            ]

            for fname in files:
                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, self.root_path)

                if self._should_skip(rel):
                    continue

                ext = Path(fname).suffix.lower()
                if ext in CODE_EXTENSIONS or ext in DOC_EXTENSIONS:
                    try:
                        if os.path.getsize(fpath) <= MAX_FILE_SIZE:
                            yield Path(fpath)
                    except OSError:
                        continue

    def _hash_content(self, content: str) -> str:
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    # ── 构建 / 更新 ──

    def build(self) -> IndexStats:
        """
        全量构建索引（清空旧数据）

        Returns:
            IndexStats: 索引统计
        """
        start_time = time.time()
        self._conn.execute("DELETE FROM chunks")
        self._conn.execute("DELETE FROM file_meta")
        self._conn.commit()

        total_files = 0
        total_chunks = 0
        total_size = 0

        files = list(self._scan_files())

        for fpath in files:
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            total_files += 1
            total_size += len(content.encode("utf-8"))

            ext = fpath.suffix.lower()
            chunks = CodeChunker.chunk_file(content, str(fpath))
            file_hash = self._hash_content(content)

            for i, chunk in enumerate(chunks):
                chunk_hash = self._hash_content(chunk)
                self._conn.execute(
                    "INSERT INTO chunks (file_path, chunk_index, content, file_type, content_hash) VALUES (?, ?, ?, ?, ?)",
                    (str(fpath), i, chunk, ext, chunk_hash),
                )
                total_chunks += 1

            self._conn.execute(
                "INSERT OR REPLACE INTO file_meta (file_path, mtime, size, content_hash) VALUES (?, ?, ?, ?)",
                (str(fpath), fpath.stat().st_mtime, len(content.encode("utf-8")), file_hash),
            )

        self._conn.commit()

        # 加载到 BM25
        self._load_to_bm25()

        stats = IndexStats(
            total_files=total_files,
            total_chunks=total_chunks,
            total_size_bytes=total_size,
            last_build_time=time.time() - start_time,
            skipped_patterns=self._skipped_patterns,
        )
        return stats

    def update(self) -> IndexStats:
        """
        增量更新：只重新索引变更或新增的文件

        Returns:
            IndexStats
        """
        start_time = time.time()
        total_files = 0
        total_chunks = 0
        total_size = 0

        # 获取已有文件元数据
        existing = {}
        for row in self._conn.execute("SELECT file_path, mtime, content_hash FROM file_meta"):
            existing[row[0]] = (row[1], row[2])

        files = list(self._scan_files())
        current_paths = set()

        for fpath in files:
            path_str = str(fpath)
            current_paths.add(path_str)

            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            file_hash = self._hash_content(content)
            mtime = fpath.stat().st_mtime

            # 检查是否需要更新
            if path_str in existing:
                old_mtime, old_hash = existing[path_str]
                if old_mtime == mtime and old_hash == file_hash:
                    continue  # 未变更，跳过

            # 删除旧数据
            self._conn.execute("DELETE FROM chunks WHERE file_path = ?", (path_str,))

            # 插入新数据
            ext = fpath.suffix.lower()
            chunks = CodeChunker.chunk_file(content, path_str)

            for i, chunk in enumerate(chunks):
                chunk_hash = self._hash_content(chunk)
                self._conn.execute(
                    "INSERT INTO chunks (file_path, chunk_index, content, file_type, content_hash) VALUES (?, ?, ?, ?, ?)",
                    (path_str, i, chunk, ext, chunk_hash),
                )
                total_chunks += 1

            self._conn.execute(
                "INSERT OR REPLACE INTO file_meta (file_path, mtime, size, content_hash) VALUES (?, ?, ?, ?)",
                (path_str, mtime, len(content.encode("utf-8")), file_hash),
            )

            total_files += 1
            total_size += len(content.encode("utf-8"))

        # 删除已不存在的文件
        for old_path in existing:
            if old_path not in current_paths:
                self._conn.execute("DELETE FROM chunks WHERE file_path = ?", (old_path,))
                self._conn.execute("DELETE FROM file_meta WHERE file_path = ?", (old_path,))

        self._conn.commit()

        # 重新加载 BM25
        self._load_to_bm25()

        stats = IndexStats(
            total_files=total_files,
            total_chunks=total_chunks,
            total_size_bytes=total_size,
            last_build_time=time.time() - start_time,
            skipped_patterns=self._skipped_patterns,
        )
        return stats

    def _load_to_bm25(self) -> None:
        """将数据库中的块加载到 BM25 引擎"""
        self._chunks = []
        documents = []

        for row in self._conn.execute("SELECT file_path, chunk_index, content, file_type FROM chunks ORDER BY id"):
            self._chunks.append({
                "file_path": row[0],
                "chunk_index": row[1],
                "content": row[2],
                "file_type": row[3],
            })
            documents.append(row[2])

        self._bm25 = BM25()
        if documents:
            self._bm25.index(documents)

    # ── 搜索 ──

    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        搜索工作区代码库

        Args:
            query: 中文或英文查询
            top_k: 返回前 k 个结果

        Returns:
            SearchResult 列表（按相关性降序）
        """
        if not self._chunks:
            self._load_to_bm25()

        if not self._chunks:
            return []

        results = self._bm25.search(query, top_k)
        return self._build_results(results)

    def search_semantic(self, query: str, top_k: int = 5, recall_k: int = 30, alpha: float = 0.3) -> List[SearchResult]:
        """
        语义搜索：BM25 召回 + IDF 加权余弦重排序

        能匹配到 BM25 词匹配漏掉的语义相关文档（如"支付接口"→"支付宝集成"）

        Args:
            query: 查询字符串
            top_k: 最终返回数量
            recall_k: BM25 召回候选数（越大召回越全但越慢）
            alpha: 语义权重（0=纯BM25, 1=纯余弦, 默认0.3）

        Returns:
            SearchResult 列表
        """
        if not self._chunks:
            self._load_to_bm25()

        if not self._chunks:
            return []

        # Phase 1: BM25 召回
        query_tokens = Tokenizer.tokenize(query)
        bm25_candidates = self._bm25.search(query, recall_k)

        if len(bm25_candidates) <= top_k:
            return self._build_results(bm25_candidates[:top_k])

        # Phase 2: 语义重排序
        from .semantic_search import SemanticReranker

        reranker = SemanticReranker()
        reranker.fit(
            self._bm25._doc_tokens,
            self._bm25._df,
            self._bm25._num_docs,
        )
        merged = reranker.rerank(query_tokens, bm25_candidates, top_k=top_k, alpha=alpha)
        return self._build_results(merged)

    def _build_results(self, scored_docs: List[Tuple[int, float]]) -> List[SearchResult]:
        """将 (doc_idx, score) 列表转为 SearchResult 列表"""
        output = []
        for doc_idx, score in scored_docs:
            chunk = self._chunks[doc_idx]
            snippet = chunk["content"][:300].replace("\n", " ")
            output.append(SearchResult(
                file_path=chunk["file_path"],
                chunk_index=chunk["chunk_index"],
                score=round(score, 4),
                snippet=snippet,
                file_type=chunk.get("file_type", ""),
            ))
        return output

    def get_context(self, query: str, max_chars: int = 4000, top_k: int = 5, semantic: bool = True) -> str:
        """
        获取与查询最相关的文件上下文（用于注入到 LLM prompt）

        Args:
            query: 用户查询
            max_chars: 最大返回字符数
            top_k: 最多返回文件数
            semantic: 是否语义搜索（默认开启）

        Returns:
            格式化的上下文字符串
        """
        if semantic:
            results = self.search_semantic(query, top_k=max(top_k, 10))
        else:
            results = self.search(query, top_k=max(top_k, 10))

        if not results:
            return ""

        # 按文件去重，取分数最高的 top_k 个文件
        seen_files = set()
        top_files = []
        for r in results:
            if r.file_path not in seen_files and len(top_files) < top_k:
                seen_files.add(r.file_path)
                top_files.append(r)

        # 提取完整文件内容（如果不超过限制）或前 N 字符
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

    def add_skip_pattern(self, pattern: str) -> None:
        """添加跳过模式"""
        if pattern not in self._skipped_patterns:
            self._skipped_patterns.append(pattern)
            self._conn.execute("INSERT OR IGNORE INTO skip_patterns VALUES (?)", (pattern,))
            self._conn.commit()

    def remove_skip_pattern(self, pattern: str) -> None:
        """移除跳过模式"""
        if pattern in self._skipped_patterns:
            self._skipped_patterns.remove(pattern)
            self._conn.execute("DELETE FROM skip_patterns WHERE pattern = ?", (pattern,))
            self._conn.commit()

    def get_stats(self) -> IndexStats:
        """获取索引统计"""
        chunk_row = self._conn.execute("SELECT COUNT(*) FROM chunks").fetchone()
        meta_row = self._conn.execute("SELECT COUNT(*), COALESCE(SUM(size), 0) FROM file_meta").fetchone()
        total_chunks = chunk_row[0] if chunk_row else 0
        total_files = meta_row[0] if meta_row else 0
        total_size = meta_row[1] if meta_row else 0

        return IndexStats(
            total_files=total_files,
            total_chunks=total_chunks,
            total_size_bytes=total_size,
            skipped_patterns=self._skipped_patterns,
        )

    def clear(self) -> None:
        """清空索引"""
        self._conn.execute("DELETE FROM chunks")
        self._conn.execute("DELETE FROM file_meta")
        self._conn.commit()
        self._chunks = []
        self._bm25 = BM25()

    def close(self) -> None:
        self._conn.close()

```
