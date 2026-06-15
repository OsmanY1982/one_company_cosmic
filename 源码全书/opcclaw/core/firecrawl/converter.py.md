# `opcclaw/core/firecrawl/converter.py`

> 路径：`opcclaw/core/firecrawl/converter.py` | 行数：384


---


```python
"""
HTML → Markdown 转换器

基于 BeautifulSoup 的纯 Python 实现，不依赖外部 markdownify 库。

特性:
- 去广告：移除常见广告 class/id（ad, banner, sidebar, popup）
- 提取正文：优先 <article>, <main>, .content, .post-content
- 保留代码块（<pre><code>）、表格、图片链接
- 代码块标记语言（```python, ```bash 等）
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# ── 广告/噪音选择器 ──
_AD_CLASS_PATTERNS = [
    "ad", "ads", "advert", "advertisement", "banner", "banner-ad",
    "sidebar", "sidebar-ad", "side-ad", "popup", "pop-up", "overlay",
    "modal-ad", "sponsored", "promoted", "promo", "social-share",
    "share-buttons", "nav", "navigation", "footer", "header",
    "comment", "comments", "related-posts", "recommended",
]
_AD_ID_PATTERNS = [
    "ad", "ads", "banner", "sidebar", "popup", "modal", "overlay",
    "footer", "header", "nav", "comments", "related",
]

# ── 正文容器优先级 ──
_CONTENT_SELECTORS = [
    "article",
    'main',
    '[role="main"]',
    ".post-content",
    ".article-content",
    ".entry-content",
    ".content",
    ".post-body",
    ".article-body",
    "#content",
    "#main-content",
    "#article",
    "#post",
]


def html_to_markdown(
    html: str,
    *,
    strip_ads: bool = True,
    extract_main: bool = True,
    base_url: Optional[str] = None,
) -> str:
    """
    将 HTML 转换为 Markdown。

    参数:
        html: 原始 HTML 字符串
        strip_ads: 是否去除广告/噪音元素
        extract_main: 是否优先提取正文容器
        base_url: 基础 URL，用于补全相对链接

    返回:
        Markdown 字符串
    """
    try:
        from bs4 import BeautifulSoup, NavigableString, Tag
    except ImportError:
        logger.warning("beautifulsoup4 未安装，回退到简单文本提取")
        return _fallback_text_extract(html)

    soup = BeautifulSoup(html, "html.parser")

    # ── 移除 script / style / noscript ──
    for tag in soup.find_all(["script", "style", "noscript", "iframe", "svg", "canvas"]):
        tag.decompose()

    # ── 去广告 ──
    if strip_ads:
        _remove_ads(soup)

    # ── 提取正文容器 ──
    if extract_main:
        main = _extract_main_content(soup)
        if main is not None:
            soup = main

    # ── 正文容器仍然可能是 Tag ──
    if isinstance(soup, Tag):
        body = soup
    elif hasattr(soup, "body") and soup.body:
        body = soup.body
    else:
        body = soup

    return _convert_node(body, base_url=base_url).strip()


# ─────────────────────────────────────────────
# 内部辅助
# ─────────────────────────────────────────────

def _remove_ads(soup) -> None:
    """移除广告/噪音元素。"""
    for pattern in _AD_CLASS_PATTERNS:
        for tag in soup.find_all(class_=re.compile(pattern, re.I)):
            tag.decompose()
    for pattern in _AD_ID_PATTERNS:
        for tag in soup.find_all(id=re.compile(pattern, re.I)):
            tag.decompose()


def _extract_main_content(soup):
    """尝试提取正文容器，失败返回 None。"""
    from bs4 import Tag

    for selector in _CONTENT_SELECTORS:
        if selector.startswith("."):
            result = soup.find(class_=selector[1:])
        elif selector.startswith("#"):
            result = soup.find(id=selector[1:])
        elif selector.startswith("["):
            import re
            m = re.match(r'\[([^=]+)="([^"]+)"\]', selector)
            if m:
                result = soup.find(attrs={m.group(1): m.group(2)})
            else:
                result = None
        else:
            result = soup.find(selector)

        if result is not None and isinstance(result, Tag):
            # 确保容器有足够的内容
            text = result.get_text(strip=True)
            if len(text) > 100:
                return result

    return None


# ── 块级标签（前后加换行）──
_BLOCK_TAGS = {
    "p", "div", "section", "article", "aside", "header", "footer",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "li", "blockquote", "figure", "figcaption",
    "form", "fieldset", "details", "summary",
}

# ── 内联标签 ──
_INLINE_TAGS = {
    "a", "span", "em", "i", "strong", "b", "u", "s", "del",
    "code", "kbd", "small", "sub", "sup", "mark", "abbr", "cite",
    "time", "label", "br",
}

# ── 标题映射 ──
_HEADING_TAGS = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}

# ── 列表标签 ──
_LIST_TAGS = {"ul", "ol", "li"}

# ── 表格标签 ──
_TABLE_TAGS = {"table", "thead", "tbody", "tfoot", "tr", "th", "td"}


def _convert_node(
    node,
    *,
    base_url: Optional[str] = None,
    list_depth: int = 0,
    table_mode: bool = False,
) -> str:
    """递归转换 DOM 节点为 Markdown。"""
    from bs4 import NavigableString, Tag

    if isinstance(node, NavigableString):
        text = node.get_text()
        # 压缩空白
        text = re.sub(r"\s+", " ", text)
        return text

    if not isinstance(node, Tag):
        return ""

    tag_name = node.name.lower() if node.name else ""

    # ── 代码块 ──
    if tag_name == "pre":
        code_tag = node.find("code")
        if code_tag:
            lang = ""
            if code_tag.get("class"):
                for cls in code_tag.get("class", []):
                    if cls.startswith("language-") or cls.startswith("lang-"):
                        lang = cls.split("-", 1)[1]
                        break
            code_text = code_tag.get_text()
            return f"\n\n```{lang}\n{code_text.strip()}\n```\n\n"
        else:
            return f"\n\n```\n{node.get_text().strip()}\n```\n\n"

    # ── 行内代码 ──
    if tag_name == "code" and not _has_parent(node, "pre"):
        return f"`{node.get_text()}`"

    # ── 图片 ──
    if tag_name == "img":
        src = node.get("src", "")
        alt = node.get("alt", "")
        if base_url and src and not src.startswith(("http://", "https://", "data:")):
            from urllib.parse import urljoin
            src = urljoin(base_url, src)
        return f"![{alt}]({src})"

    # ── 链接 ──
    if tag_name == "a":
        href = node.get("href", "")
        if base_url and href and not href.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
            from urllib.parse import urljoin
            href = urljoin(base_url, href)
        text = "".join(_convert_node(c, base_url=base_url) for c in node.children).strip()
        if not text:
            text = href
        return f"[{text}]({href})"

    # ── 换行 ──
    if tag_name == "br":
        return "\n"

    # ── 水平线 ──
    if tag_name == "hr":
        return "\n\n---\n\n"

    # ── 标题 ──
    if tag_name in _HEADING_TAGS:
        prefix = _HEADING_TAGS[tag_name]
        text = "".join(_convert_node(c, base_url=base_url) for c in node.children).strip()
        return f"\n\n{prefix} {text}\n\n"

    # ── 段落 ──
    if tag_name == "p":
        text = "".join(_convert_node(c, base_url=base_url) for c in node.children).strip()
        if text:
            return f"\n\n{text}\n\n"
        return "\n\n"

    # ── 粗体 / 斜体 ──
    if tag_name in ("strong", "b"):
        text = "".join(_convert_node(c, base_url=base_url) for c in node.children).strip()
        return f"**{text}**"
    if tag_name in ("em", "i"):
        text = "".join(_convert_node(c, base_url=base_url) for c in node.children).strip()
        return f"*{text}*"
    if tag_name in ("s", "del", "strike"):
        text = "".join(_convert_node(c, base_url=base_url) for c in node.children).strip()
        return f"~~{text}~~"

    # ── 引用块 ──
    if tag_name == "blockquote":
        text = "".join(_convert_node(c, base_url=base_url) for c in node.children).strip()
        lines = text.split("\n")
        quoted = "\n".join(f"> {line}" for line in lines if line.strip())
        return f"\n\n{quoted}\n\n"

    # ── 无序列表 ──
    if tag_name == "ul":
        items = []
        for li in node.find_all("li", recursive=False):
            item_text = "".join(
                _convert_node(c, base_url=base_url, list_depth=list_depth + 1)
                for c in li.children
            ).strip()
            indent = "  " * list_depth
            items.append(f"{indent}- {item_text}")
        if items:
            return "\n" + "\n".join(items) + "\n"
        return ""

    # ── 有序列表 ──
    if tag_name == "ol":
        items = []
        for idx, li in enumerate(node.find_all("li", recursive=False), 1):
            item_text = "".join(
                _convert_node(c, base_url=base_url, list_depth=list_depth + 1)
                for c in li.children
            ).strip()
            indent = "  " * list_depth
            items.append(f"{indent}{idx}. {item_text}")
        if items:
            return "\n" + "\n".join(items) + "\n"
        return ""

    # ── 列表项（在 ul/ol 内时递归处理子节点）──
    if tag_name == "li":
        return "".join(_convert_node(c, base_url=base_url, list_depth=list_depth) for c in node.children)

    # ── 表格 ──
    if tag_name == "table":
        return _convert_table(node, base_url=base_url)

    # ── 块级元素 ──
    if tag_name in _BLOCK_TAGS:
        parts = []
        for child in node.children:
            parts.append(_convert_node(child, base_url=base_url))
        result = "".join(parts)
        return result

    # ── 内联元素（默认）──
    parts = []
    for child in node.children:
        parts.append(_convert_node(child, base_url=base_url))
    return "".join(parts)


def _convert_table(table, *, base_url: Optional[str] = None) -> str:
    """转换 HTML 表格为 Markdown 表格。"""
    from bs4 import Tag

    rows = table.find_all("tr")
    if not rows:
        return ""

    md_rows: list[list[str]] = []

    for row in rows:
        cells = row.find_all(["th", "td"])
        md_cells = [
            "".join(_convert_node(c, base_url=base_url) for c in cell.children).strip().replace("\n", " ")
            for cell in cells
        ]
        if md_cells:
            md_rows.append(md_cells)

    if not md_rows:
        return ""

    # 对齐到最大列数
    max_cols = max(len(r) for r in md_rows)
    for r in md_rows:
        while len(r) < max_cols:
            r.append("")

    lines: list[str] = []
    # Header
    lines.append("| " + " | ".join(md_rows[0]) + " |")
    # Separator
    lines.append("| " + " | ".join(["---"] * max_cols) + " |")
    # Body
    for row in md_rows[1:]:
        lines.append("| " + " | ".join(row) + " |")

    return "\n\n" + "\n".join(lines) + "\n\n"


def _has_parent(node, parent_tag: str) -> bool:
    """检查节点是否有特定父标签。"""
    from bs4 import Tag
    p = node.parent
    while p is not None:
        if isinstance(p, Tag) and p.name and p.name.lower() == parent_tag:
            return True
        p = p.parent
    return False


def _fallback_text_extract(html: str) -> str:
    """无 BeautifulSoup 时的回退纯文本提取。"""
    # 移除 script / style
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.I)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.I)
    # 移除标签
    text = re.sub(r"<[^>]+>", " ", html)
    # 解码实体
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    # 压缩空白
    text = re.sub(r"\s+", " ", text)
    # 按行整理
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n\n".join(lines)

```
