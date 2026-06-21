# `core/test_phase2.py`

> 路径：`core/test_phase2.py` | 行数：87


---


```python
"""Phase 2 集成测试 — 独立于 iqra 包导入"""
import sys, os, tempfile

# Direct module loading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load workspace_indexer without triggering iqra/__init__.py
import importlib.util
spec = importlib.util.spec_from_file_location(
    'workspace_indexer',
    os.path.join(os.path.dirname(__file__), 'workspace_indexer.py')
)
ws = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ws)

# Load rag_context (need to handle relative import)
spec2 = importlib.util.spec_from_file_location(
    'rag_context',
    os.path.join(os.path.dirname(__file__), 'rag_context.py')
)
rag = importlib.util.module_from_spec(spec2)
# Mock .workspace_indexer → ws
rag.WorkspaceIndexer = ws.WorkspaceIndexer
rag.SearchResult = ws.SearchResult
spec2.loader.exec_module(rag)

# ── Test 1: Index Iqra codebase ──
print("=" * 60)
print("Test 1: Full index of Iqra")
opc_path = os.path.join(os.path.dirname(os.path.dirname(__file__)))
with tempfile.TemporaryDirectory() as tmp:
    db = os.path.join(tmp, '.phase2_test.db')
    indexer = ws.WorkspaceIndexer(opc_path, db_path=db)
    stats = indexer.build()
    print(f"  Files: {stats.total_files}, Chunks: {stats.total_chunks}, Size: {stats.total_size_bytes/1024:.0f} KB")
    assert stats.total_files > 100, f"Expected >100 files, got {stats.total_files}"

    # ── Test 2: Search ──
    print("\nTest 2: Chinese search")
    r = indexer.search("聊天窗口多模型路由", top_k=3)
    assert len(r) > 0, "No results for Chinese search"
    matches = [x for x in r if "test_phase2" not in x.file_path]
    assert len(matches) > 0, f"No non-test results for Chinese search"
    print(f"  Top hit: {os.path.basename(matches[0].file_path)} (score={matches[0].score:.2f})")

    print("\nTest 3: English search")
    r = indexer.search("BM25 tokenizer workspace indexer", top_k=3)
    assert len(r) > 0, "No results for English search"
    matches = [x for x in r if "test_phase2" not in x.file_path]
    if matches:
        print(f"  Top hit: {os.path.basename(matches[0].file_path)} (score={matches[0].score:.2f})")
    else:
        print(f"  Top hit: N/A (test file filtered)")

    # ── Test 4: get_context ──
    print("\nTest 4: Context extraction")
    ctx = indexer.get_context("Agent 自主执行循环 ReAct", max_chars=2000, top_k=3)
    assert len(ctx) > 100, f"Context too short: {len(ctx)}"
    assert "agent_loop" in ctx, f"Expected agent_loop in context:\n{ctx[:200]}"
    print(f"  Context length: {len(ctx)} chars")

    # ── Test 5: RAGContextInjector ──
    print("\nTest 5: RAGContextInjector")
    injector = rag.RAGContextInjector()
    injector._indexer = indexer
    injector._project_path = opc_path
    injector._enabled = True
    result = injector.inject_context("帮我修改登录功能")
    assert "<workspace_context>" in result, "Missing workspace_context tag"
    print(f"  Injection: +{len(result) - len('帮我修改登录功能')} chars of context")

    # ── Test 6: IndexStats ──
    print("\nTest 6: IndexStats")
    s = indexer.get_stats()
    print(f"  build: {stats.total_files} files, stats: {s.total_files} files")
    assert s.total_files == stats.total_files, f"Stats mismatch: build={stats.total_files}, get_stats={s.total_files}"
    print(f"  Stats: {s.total_files} files, {s.total_chunks} chunks, {s.total_size_bytes/1024:.0f} KB")

    # ── Test 7: Incremental update ──
    print("\nTest 7: Incremental update (no changes)")
    s2 = indexer.update()
    assert s2.total_files == 0, f"Expected 0 changed files, got {s2.total_files}"
    print(f"  Changed files: {s2.total_files} (expected 0)")

print("\n" + "=" * 60)
print("ALL 7 TESTS PASSED")
print("=" * 60)

```
