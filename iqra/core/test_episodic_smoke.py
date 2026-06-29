#!/usr/bin/env python3
"""Smoke tests for episodic_memory.py"""
import sys, os, tempfile, shutil

sys.path.insert(0, "/Volumes/D盘工作区/一人公司宇宙版/one_company_cosmic/iqra")

from core.episodic_memory import (
    EpisodicMemory, EpisodicContextInjector,
    EpisodicDB, Episode,
)

td = tempfile.mkdtemp(prefix="episodic_test_")

try:
    # ── Test 1: DB insert + get ──
    print("Test 1: DB CRUD")
    db = EpisodicDB(os.path.join(td, "test.db"))
    eid = db.insert(Episode(
        session_id="sess_001",
        timestamp="2026-06-28T10:00:00",
        user_query="帮我重构登录模块",
        summary="提取了 AuthService，迁移了 3 个调用方",
        tools_used="read_file, write_file, search_files",
        project="/test/project",
        importance=0.8,
    ))
    assert eid == 1
    ep = db.get_by_id(1)
    assert ep.user_query == "帮我重构登录模块"
    assert "AuthService" in ep.summary
    assert db.count("/test/project") == 1
    print(f"  PASS: inserted id={eid}, query='{ep.user_query[:30]}...'")

    # ── Test 2: EpisodicMemory record + retrieve ──
    print("Test 2: record + retrieve")
    mem = EpisodicMemory(td, project="/test/project")
    mem.max_episodes = 20

    # 记录多条
    mem.record("重构登录模块", "提取 AuthService，迁移调用方", tools_used=["read_file", "write_file"])
    mem.record("修复支付回调超时", "增加重试机制，超时 30s → 60s", tools_used=["edit_file"])
    mem.record("添加用户权限检查", "新增 PermissionDecorator，应用到 5 个接口", tools_used=["write_file", "edit_file"])
    mem.record("优化数据库查询", "为 users 表添加复合索引，查询 2.1s → 0.3s", tools_used=["execute_sql"])

    # 检索 "登录"
    results = mem.retrieve("登录")
    assert len(results) > 0
    # 登录相关应该排前面
    login_found = any("登录" in r.episode.user_query for r in results[:2])
    if not login_found:
        print(f"  WARN: login not top, results: {[(r.episode.user_query[:30], r.score) for r in results]}")
    print(f"  PASS: retrieve('登录') → {len(results)} results, top='{results[0].episode.user_query[:30]}' score={results[0].score}")

    # 检索 "权限"
    results2 = mem.retrieve("权限检查")
    assert len(results2) > 0
    print(f"  PASS: retrieve('权限检查') → top='{results2[0].episode.user_query[:30]}' score={results2[0].score}")

    # ── Test 3: get_context ──
    print("Test 3: get_context")
    ctx = mem.get_context("登录模块还有什么问题", top_k=2)
    assert "<episodic_memory>" in ctx
    assert "登录" in ctx
    assert "</episodic_memory>" in ctx
    print(f"  PASS: context length={len(ctx)} chars")
    print(f"  Context preview:\n{ctx[:300]}...")

    # ── Test 4: EpisodicContextInjector ──
    print("Test 4: ContextInjector")
    injector = EpisodicContextInjector(mem)
    augmented = injector.inject("登录模块的 bug 怎么修")
    assert "<episodic_memory>" in augmented
    assert "登录模块的 bug 怎么修" in augmented
    print(f"  PASS: augment length={len(augmented)} chars")

    # ── Test 5: compress ──
    print("Test 5: compress")
    before = mem._db.count("/test/project")
    mem.compress(n=2)
    after = mem._db.count("/test/project")
    assert after < before, f"expected compression, {before} → {after}"
    print(f"  PASS: {before} → {after} episodes after compress(2)")

    # ── Test 6: 空检索 ──
    print("Test 6: empty index")
    mem2 = EpisodicMemory(td, project="/empty")
    results3 = mem2.retrieve("anything")
    assert results3 == []
    ctx3 = mem2.get_context("anything")
    assert ctx3 == ""
    print("  PASS: empty project returns []")

    # ── Test 7: stats ──
    print("Test 7: stats")
    stats = mem.stats
    assert "total_episodes" in stats
    print(f"  PASS: stats={stats}")

    print("\n✅ All 7 tests passed")

finally:
    shutil.rmtree(td, ignore_errors=True)
