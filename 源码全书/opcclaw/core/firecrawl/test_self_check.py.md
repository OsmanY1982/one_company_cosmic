# `opcclaw/core/firecrawl/test_self_check.py`

> 路径：`opcclaw/core/firecrawl/test_self_check.py` | 行数：199


---


```python
"""
Firecrawl 集成自检脚本

测试项目：
1. 模块导入不抛出异常（缺失 API key 也不阻塞）
2. converter.py HTML→Markdown 转换（代码块标记、表格、链接）
3. cache.py 读写命中
"""

import os
import sys
import tempfile

# ── 确保 opcclaw 在路径中 ──
_project_root = "/Volumes/D盘工作区/一人公司宇宙版/one_company_cosmic"
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, "opcclaw"))

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        print(f"  ✗ {name} — {detail}")


# ═══════════════════════════════════════════
# 测试 1: 模块导入
# ═══════════════════════════════════════════

print("=" * 60)
print("测试 1: 模块导入")
print("=" * 60)

try:
    from opcclaw.core.firecrawl import scrape_url, crawl_site, search_web, extract_structured
    check("firecrawl/__init__.py 导入成功", True)
except ImportError as e:
    check("firecrawl/__init__.py 导入成功", False, str(e))

try:
    from opcclaw.core.firecrawl.converter import html_to_markdown
    check("converter.py 导入成功", True)
except ImportError as e:
    check("converter.py 导入成功", False, str(e))

try:
    from opcclaw.core.firecrawl.cache import _get_cache, _set_cache
    check("cache.py 导入成功", True)
except ImportError as e:
    check("cache.py 导入成功", False, str(e))

# 验证 _HAVE_FIRECRAWL 标志
try:
    import importlib
    from modules.intelligence import agent_bridge
    importlib.reload(agent_bridge)
    flag = getattr(agent_bridge, "_HAVE_FIRECRAWL", None)
    check("_HAVE_FIRECRAWL 标志存在", flag is not None)
    check(f"_HAVE_FIRECRAWL = {flag}（缺失 API key 不应阻塞）", flag is True)
except Exception as e:
    check("_HAVE_FIRECRAWL 标志检查", False, str(e))


# ═══════════════════════════════════════════
# 测试 2: HTML → Markdown 转换
# ═══════════════════════════════════════════

print("\n" + "=" * 60)
print("测试 2: converter.py HTML→Markdown")
print("=" * 60)

# 测试代码块标记语言
html_with_code = """
<html><body>
<h1>Test Page</h1>
<p>This is a paragraph with <strong>bold</strong> and <em>italic</em>.</p>
<pre><code class="language-python">def hello():
    print("Hello, world!")</code></pre>
<pre><code class="lang-bash">echo "test"</code></pre>
</body></html>
"""

md = html_to_markdown(html_with_code)

check("标题转换 (# Test Page)", "# Test Page" in md)
check("粗体转换 (**bold**)", "**bold**" in md)
check("斜体转换 (*italic*)", "*italic*" in md)
check("Python 代码块标记 (```python)", "```python" in md)
check("Bash 代码块标记 (```bash)", "```bash" in md)
check("代码内容保留", 'def hello():' in md and 'print("Hello, world!")' in md)

# 测试表格
html_with_table = """
<html><body>
<table>
<tr><th>Name</th><th>Age</th></tr>
<tr><td>Alice</td><td>30</td></tr>
<tr><td>Bob</td><td>25</td></tr>
</table>
</body></html>
"""

md_table = html_to_markdown(html_with_table)
check("表格转换（Markdown 表格格式）", "| Name | Age |" in md_table)
check("表格数据行", "| Alice | 30 |" in md_table)

# 测试链接
html_with_link = '<html><body><a href="https://example.com">Example</a></body></html>'
md_link = html_to_markdown(html_with_link)
check("链接转换 [Example](https://example.com)", "[Example](https://example.com)" in md_link)

# 测试去广告
html_with_ad = """
<html><body>
<article><p>Main content here.</p></article>
<div class="ad">Ad content</div>
<div class="sidebar-ad">Sidebar ad</div>
<div id="popup">Popup</div>
</body></html>
"""

md_clean = html_to_markdown(html_with_ad, strip_ads=True, extract_main=True)
check("去广告 — 正文保留", "Main content here" in md_clean)
check("去广告 — 广告移除", "Ad content" not in md_clean)
check("去广告 — 侧栏移除", "Sidebar ad" not in md_clean)

# 测试正文提取
html_with_article = """
<html><body>
<header><nav>Nav links</nav></header>
<article><h1>Article Title</h1><p>Article body text here. This is the real content of the page that we want to extract and convert to markdown format.</p></article>
<footer>Footer text</footer>
</body></html>
"""

md_article = html_to_markdown(html_with_article, extract_main=True)
check("正文提取 — 标题保留", "Article Title" in md_article)
check("正文提取 — 内容保留", "Article body text here" in md_article)
check("正文提取 — 导航移除", "Nav links" not in md_article)


# ═══════════════════════════════════════════
# 测试 3: 缓存读写
# ═══════════════════════════════════════════

print("\n" + "=" * 60)
print("测试 3: cache.py 缓存")
print("=" * 60)

test_url = "https://example.com/test-cache-page"

# 清理旧缓存
from opcclaw.core.firecrawl.cache import _cache_path
cache_file = _cache_path(test_url)
if os.path.exists(cache_file):
    os.remove(cache_file)

# 第一次请求（未命中）
result1 = _get_cache(test_url)
check("缓存未命中返回 None", result1 is None)

# 写入缓存
test_content = {
    "url": test_url,
    "markdown": "# Test Cache\n\nContent here.",
    "html": "<h1>Test</h1>",
    "title": "Test",
    "cached": False,
}
_set_cache(test_url, test_content)

# 第二次请求（命中）
result2 = _get_cache(test_url)
check("缓存命中返回 dict", result2 is not None)
if result2:
    check("缓存内容一致（markdown）", result2.get("markdown") == "# Test Cache\n\nContent here.")
    check("缓存内容一致（title）", result2.get("title") == "Test")

# 清理
if os.path.exists(cache_file):
    os.remove(cache_file)


# ═══════════════════════════════════════════
# 汇总
# ═══════════════════════════════════════════

print("\n" + "=" * 60)
print(f"结果: {passed} 通过 / {failed} 失败 / {passed + failed} 总计")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)

```
