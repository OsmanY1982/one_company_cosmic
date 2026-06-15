# `opcclaw/core/multi_channel/content_optimizer.py`

> 路径：`opcclaw/core/multi_channel/content_optimizer.py` | 行数：279


---


```python
# -*- coding: utf-8 -*-
"""
内容优化器
==========
按平台规则自动优化/改写内容，支持 LLM 辅助改写。

平台规则:
    微信: 保留 HTML 排版，外链转底部引用
    微博: 截断至 140 字 + 长图文提示
    知乎: 标题优化，添加话题标签
    Twitter/X: 截断至 280 字符，添加 hashtag
    LinkedIn: 保持专业风格，添加结构化列表
"""

import os
import traceback
from typing import Dict, Any, Optional

try:
    import re as _re
except ImportError:
    _re = None

# 平台字数限制
PLATFORM_LIMITS = {
    "wechat": {"title": 64, "content": 20000},
    "weibo": {"text": 140},
    "zhihu": {"title": 100, "content": 50000},
    "twitter": {"text": 280},
    "x": {"text": 280},
    "linkedin": {"text": 3000},
}


def optimize_for_platform(content: str, platform: str,
                          title: str = "",
                          use_llm: bool = False,
                          llm_backend=None,
                          extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    按平台规则优化内容

    Args:
        content: 原始内容
        platform: 目标平台
        title: 原始标题
        use_llm: 是否使用 LLM 辅助改写
        llm_backend: LLM 后端实例
        extra: 额外参数

    Returns:
        {"optimized_content": str, "optimized_title": str, "warnings": list, "actions": list}
    """
    optimizer = ContentOptimizer()
    result = optimizer.optimize(content=content, platform=platform, title=title, extra=extra)

    if use_llm and llm_backend:
        try:
            llm_cfg = extra or {}
            if llm_cfg.get("mode") == "full_rewrite":
                result = _llm_full_rewrite(content, platform, title, llm_backend)
            else:
                # 默认只对标题做 LLM 优化
                llm_title = _llm_title_optimize(title, platform, llm_backend)
                if llm_title:
                    result["optimized_title"] = llm_title
                    result["actions"].append(f"[LLM] 标题已优化为: {llm_title}")
        except Exception:
            traceback.print_exc()
            result["warnings"].append("LLM 优化失败，使用规则优化结果")

    return result


class ContentOptimizer:
    """内容优化器 — 规则引擎"""

    def optimize(self, content: str, platform: str,
                 title: str = "",
                 extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        result = {
            "optimized_content": content,
            "optimized_title": title,
            "warnings": [],
            "actions": [],
        }

        method_name = f"_optimize_{platform}"
        if hasattr(self, method_name):
            getattr(self, method_name)(content, title, result, extra or {})
        else:
            result["warnings"].append(f"平台 '{platform}' 无专属优化规则，使用原始内容")
            result = self._optimize_generic(content, title, result)

        return result

    # ── 微信优化 ──

    def _optimize_wechat(self, content: str, title: str,
                         result: Dict, extra: Dict) -> None:
        """微信：保留 HTML 排版，处理外链"""
        # 1. 检测外链并转为底部引用
        import re
        urls = re.findall(r'(https?://[^\s<>"]+)', content)
        if urls:
            result["optimized_content"] = _convert_links_to_references(content, urls)
            result["actions"].append(f"已将 {len(urls)} 个外链转为底部引用")

        # 2. 标题截断
        if len(title) > 64:
            result["optimized_title"] = title[:62] + ".."
            result["actions"].append(f"标题从 {len(title)} 字截断至 64 字")

        # 3. 确保有封面图提示
        result["hints"] = ["建议添加封面图（900x383 像素比例）"]

    # ── 微博优化 ──

    def _optimize_weibo(self, content: str, title: str,
                        result: Dict, extra: Dict) -> None:
        """微博：截断至 140 字，建议制作长图"""
        text = content.strip()
        if len(text) > 140:
            result["optimized_content"] = text[:137] + "..."
            result["actions"].append(f"内容从 {len(text)} 字截断至 140 字")
            result["warnings"].append("内容超过 140 字，建议制作长图或链接到原文")

        # 微博不需要标题
        result["optimized_title"] = ""

    # ── 知乎优化 ──

    def _optimize_zhihu(self, content: str, title: str,
                        result: Dict, extra: Dict) -> None:
        """知乎：标题优化，话题标签"""
        # 1. 标题优化（去除标点堆积）
        import re
        if title:
            cleaned = re.sub(r'[！!？?]{2,}', lambda m: m.group()[0], title)
            cleaned = re.sub(r'[~～]{1,}', '', cleaned)
            if cleaned != title:
                result["optimized_title"] = cleaned
                result["actions"].append("已清理标题中的重复标点")

        # 2. 检测话题标签
        tags = extra.get("topic_tags", [])
        if not tags:
            # 自动从内容提取关键词作为话题建议
            words = re.findall(r'[\u4e00-\u9fff\w]{2,8}', content[:500])
            word_freq = {}
            for w in words:
                if len(w) >= 2:
                    word_freq[w] = word_freq.get(w, 0) + 1
            top_words = sorted(word_freq, key=word_freq.get, reverse=True)[:5]
            result["hints"] = [f"建议添加话题标签: {', '.join(top_words)}"]

        # 3. 内容格式调整
        result["hints"] = (result.get("hints") or []) + [
            "知乎文章建议使用 Markdown 排版，善用标题和列表",
        ]

    # ── Twitter/X 优化 ──

    def _optimize_twitter(self, content: str, title: str,
                          result: Dict, extra: Dict) -> None:
        """Twitter/X：截断至 280 字符"""
        text = content.strip()
        if len(text) > 280:
            result["optimized_content"] = text[:277] + "..."
            result["actions"].append(f"内容从 {len(text)} 字符截断至 280 字符")

        # 自动添加 hashtag
        import re
        hashtags = extra.get("hashtags", [])
        if not hashtags:
            words = re.findall(r'[\u4e00-\u9fff\w]{3,12}', content[:200])
            if words:
                hashtags = [f"#{w}" for w in words[:2]]
        if hashtags:
            optimized = result["optimized_content"]
            tag_str = " " + " ".join(hashtags)
            if len(optimized) + len(tag_str) <= 280:
                result["optimized_content"] = optimized + tag_str
            result["actions"].append(f"已添加 hashtag: {tag_str.strip()}")

        result["optimized_title"] = ""

    def _optimize_x(self, content, title, result, extra):
        """X 同 Twitter"""
        return self._optimize_twitter(content, title, result, extra)

    # ── LinkedIn 优化 ──

    def _optimize_linkedin(self, content: str, title: str,
                           result: Dict, extra: Dict) -> None:
        """LinkedIn：保持专业风格，添加结构化"""
        result["actions"].append("LinkedIn 动态建议使用 bullet points 和关键词")

    # ── 通用优化 ──

    def _optimize_generic(self, content: str, title: str,
                          result: Dict) -> Dict:
        """通用优化（不做处理）"""
        return result


# ═══════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════

def _convert_links_to_references(content: str, urls: list) -> str:
    """将正文中的外链转换为底部引用"""
    import re
    refs = []
    for i, url in enumerate(urls, 1):
        ref_marker = f"[{i}]"
        content = content.replace(url, f'<a href="{url}">{ref_marker}</a>', 1)
        refs.append(f'<p>{ref_marker} <a href="{url}">{url}</a></p>')
    if refs:
        content += "\n\n<hr>\n<p><strong>参考文献</strong></p>\n" + "\n".join(refs)
    return content


def _llm_title_optimize(title: str, platform: str, llm_backend) -> Optional[str]:
    """使用 LLM 优化标题"""
    if not title or not llm_backend:
        return None

    prompts = {
        "wechat": "优化以下微信公众号文章标题，使其更具吸引力（25字以内）：",
        "zhihu": "将以下标题改写为知乎风格，添加问句或悬念（30字以内）：",
        "weibo": "将以下内容精简为一句话，适合微博传播：",
    }
    prompt = prompts.get(platform, f"优化以下标题使其更适合 {platform} 平台：")
    full_prompt = f"{prompt}\n\n{title}"

    try:
        response = llm_backend.chat(full_prompt)
        if response:
            return response.strip().strip('"').strip("'")
    except Exception:
        pass
    return None


def _llm_full_rewrite(content: str, platform: str, title: str, llm_backend) -> Dict[str, Any]:
    """使用 LLM 全量改写内容"""
    limits = PLATFORM_LIMITS.get(platform, {})
    rules = {
        "wechat": f"将以下内容改写为微信公众号文章。保留 HTML 排版，外链改为底部引用。标题不超过{limits.get('title', 64)}字。",
        "weibo": f"将以下内容精简为一条微博，不超过{limits.get('text', 140)}字。",
        "zhihu": "将以下内容改写为知乎文章。优化标题，添加话题标签，使用 Markdown 排版。",
        "twitter": f"将以下内容精简为一条推文，不超过{limits.get('text', 280)}字符。添加合适 hashtag。",
        "linkedin": "将以下内容改写为 LinkedIn 动态，保持专业风格。",
    }

    prompt = rules.get(platform, f"将以下内容改写为适合 {platform} 发布的格式：")
    if title:
        prompt += f"\n原标题：{title}"
    prompt += f"\n\n{content}"

    try:
        response = llm_backend.chat(prompt)
        if response:
            return {
                "optimized_content": response,
                "optimized_title": title,
                "warnings": [],
                "actions": [f"[LLM] 已完成 {platform} 平台全量改写"],
            }
    except Exception:
        pass

    return {
        "optimized_content": content,
        "optimized_title": title,
        "warnings": ["LLM 改写失败"],
        "actions": [],
    }

```
