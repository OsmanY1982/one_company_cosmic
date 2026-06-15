# -*- coding: utf-8 -*-
"""
semantic_search 模块验证脚本

测试：
  1. 模块导入是否正常（BM25 降级路径）
  2. HybridRetriever 初始化
  3. RAGContextInjector 集成不报错
  4. agent_bridge.py 标志存活
"""

import sys
import os

# 添加项目路径
PROJECT = "/Volumes/D盘工作区/一人公司/one_company_cosmic"
sys.path.insert(0, PROJECT)

print("=" * 60)
print("opcclaw Semantic Search — 模块验证")
print("=" * 60)

# ── Test 1: semantic_search 包导入 ──
print("\n[Test 1] semantic_search 包导入")
try:
    from opcclaw.core.semantic_search import SemanticSearcher
    from opcclaw.core.semantic_search.hybrid_retriever import HybridRetriever
    print("  ✅ SemanticSearcher + HybridRetriever 导入成功")
    _HAVE_SS = True
except ImportError as e:
    print(f"  ⚠️  导入失败（预期，若未安装 sentence-transformers/faiss）: {e}")
    _HAVE_SS = False

# ── Test 2: agent_bridge.py 标志 ──
print("\n[Test 2] agent_bridge.py 标志")
try:
    # 直接检查 rag_context 中的标志（agent_bridge 相同）
    from opcclaw.core.rag_context import _HAVE_SEMANTIC_SEARCH as bridge_ss
    print(f"  _HAVE_SEMANTIC_SEARCH = {bridge_ss}")
    print(f"  状态: {'✅ 可用' if bridge_ss else '⚠️  不可用（依赖缺失，BM25 后备可用）'}")

    # 验证 agent_bridge.py 中的导入路径
    ag_bridge_path = os.path.join(PROJECT, "modules", "intelligence", "agent_bridge.py")
    with open(ag_bridge_path) as f:
        content = f.read()
    assert "SemanticSearcher" in content, "agent_bridge.py 中应有 SemanticSearcher 导入"
    assert "HybridRetriever" in content, "agent_bridge.py 中应有 HybridRetriever 导入"
    assert "_HAVE_SEMANTIC_SEARCH" in content, "agent_bridge.py 中应有 _HAVE_SEMANTIC_SEARCH"
    print("  ✅ agent_bridge.py 标志代码确认存在")
except Exception as e:
    print(f"  ❌ 导入失败: {e}")

# ── Test 3: RAGContextInjector 集成 ──
print("\n[Test 3] RAGContextInjector 集成")
try:
    from opcclaw.core.rag_context import RAGContextInjector, _HAVE_SEMANTIC_SEARCH as rag_ss

    rag = RAGContextInjector()
    assert rag._hybrid is None, "初始状态 _hybrid 应为 None"

    # 检查 _HAVE_SEMANTIC_SEARCH 标志
    print(f"  rag_context._HAVE_SEMANTIC_SEARCH = {rag_ss}")

    # 检查配置
    cfg = rag.get_config()
    print(f"  has_semantic = {cfg.get('has_semantic')}")
    print(f"  search_mode = {cfg.get('search_mode')}")
    assert cfg["search_mode"] == "bm25_only", f"expected bm25_only, got {cfg['search_mode']}"

    print("  ✅ RAGContextInjector 集成正常，BM25 降级路径完好")
except Exception as e:
    print(f"  ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# ── Test 4: HybridRetriever 初始化（BM25 降级） ──
print("\n[Test 4] HybridRetriever 初始化")
try:
    from opcclaw.core.workspace_indexer import WorkspaceIndexer
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        texts = {
            "auth.py": (
                "def authenticate_user(username, password):\n"
                "    \"\"\"用户认证模块，处理登录、注册、密码重置\"\"\"\n"
                "    if not username or not password:\n"
                "        raise ValueError('用户名和密码不能为空')\n"
                "    user = find_user_by_name(username)\n"
                "    if user and verify_password(password, user.hashed_pwd):\n"
                "        return generate_token(user)\n"
                "    raise AuthenticationError('用户名或密码错误')\n"
                "\n"
                "def login(username, password):\n"
                "    return authenticate_user(username, password)\n"
                "\n"
                "def logout(token):\n"
                "    invalidate_token(token)\n"
            ),
            "payment.py": (
                "\"\"\"支付模块 — 处理订单支付、退款、账单查询\"\"\"\n"
                "def process_payment(order_id, amount, currency='CNY'):\n"
                "    \"\"\"处理支付请求\"\"\"\n"
                "    order = get_order(order_id)\n"
                "    if not order:\n"
                "        raise OrderNotFoundError(f'订单 {order_id} 不存在')\n"
                "    charge = payment_gateway.create_charge(\n"
                "        amount=amount,\n"
                "        currency=currency,\n"
                "        description=f'订单 {order_id} 支付'\n"
                "    )\n"
                "    if charge.status == 'success':\n"
                "        update_order_status(order_id, 'paid')\n"
                "        send_receipt(order.user_email, charge)\n"
                "    return charge\n"
                "\n"
                "def request_refund(order_id, reason=''):\n"
                "    \"\"\"申请退款\"\"\"\n"
                "    order = get_order(order_id)\n"
                "    if order.status != 'paid':\n"
                "        raise InvalidStateError('仅已支付订单可退款')\n"
                "    refund = payment_gateway.create_refund(order.charge_id, reason)\n"
                "    update_order_status(order_id, 'refunded')\n"
                "    return refund\n"
            ),
            "config.md": (
                "# 系统配置\n\n"
                "## 数据库\n"
                "- 主数据库: PostgreSQL 14 @ 127.0.0.1:5432\n"
                "- 缓存: Redis 7 @ 127.0.0.1:6379\n\n"
                "## 支付网关\n"
                "- Stripe API (国际支付)\n"
                "- 支付宝 (中国区)\n"
                "- 微信支付 (中国区)\n\n"
                "## 性能优化\n"
                "- 数据库连接池: 20 连接\n"
                "- Redis 缓存 TTL: 3600 秒\n"
                "- API 限流: 100 req/min\n"
            ),
        }
        for fname, content in texts.items():
            with open(os.path.join(tmpdir, fname), "w") as f:
                f.write(content)

        indexer = WorkspaceIndexer(tmpdir)
        indexer.build()

        # 尝试初始化语义搜索
        semantic = None
        if _HAVE_SS:
            try:
                semantic = SemanticSearcher()
                documents = [c for c in texts.values()]
                semantic.build_index(documents)
                print("  SemanticSearcher 初始化成功")
            except ImportError:
                print("  ⚠️  SemanticSearcher 导入成功但依赖缺失（sentence-transformers/faiss），将走 BM25 降级")

        hr = HybridRetriever(indexer, semantic_searcher=semantic)
        print(f"  mode = {hr.mode}")
        print(f"  has_semantic = {hr.has_semantic}")

        # 搜索测试
        results = hr.search("处理支付", top_k=2)
        print(f"  搜索结果: {len(results)} 条")
        for r in results:
            print(f"    [{r.score:.4f}] {r.file_path} — {r.snippet[:50]}")

        # 验证降级：至少能找到 payment.py
        found_payment = any("payment" in r.file_path for r in results)
        if found_payment:
            print("  ✅ HybridRetriever 搜索正常，正确匹配 '处理支付' → payment.py")
        else:
            print("  ❌ 未找到 payment.py")

except Exception as e:
    print(f"  ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

# ── Summary ──
print("\n" + "=" * 60)
print("验证完成")
print("=" * 60)
