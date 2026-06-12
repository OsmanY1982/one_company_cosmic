# `opcclaw/tools/web_search_tools.py`

> 路径：`opcclaw/tools/web_search_tools.py` | 行数：149


---


```python
"""
OPCclaw 网络搜索工具 — 信息采集与网络查询

提供 AI 助手搜索互联网信息的能力。
依赖: requests (一人公司项目已安装)
"""

import requests
import json
import re
from datetime import datetime
from typing import Dict, List, Optional


def web_search_baidu(query: str, count: int = 10) -> dict:
    """百度搜索（简易版，抓取搜索结果标题和摘要）"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        url = f"https://www.baidu.com/s?wd={query}&rn={count}"
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"
        
        # 提取搜索结果
        results = []
        # 简易解析：提取 <h3> 标题和摘要
        titles = re.findall(r'<h3[^>]*>(.*?)</h3>', resp.text, re.DOTALL)
        for i, title_html in enumerate(titles[:count]):
            # 清除HTML标签
            title = re.sub(r'<[^>]+>', '', title_html).strip()
            if title:
                results.append({"序号": i+1, "标题": title})
        
        return {"message": f"搜索'{query}'得到 {len(results)} 条结果", "data": results}
    except Exception as e:
        return {"message": f"搜索失败: {e}", "data": []}


def fetch_webpage(url: str, max_length: int = 5000) -> dict:
    """抓取网页内容（纯文本提取）"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = resp.apparent_encoding or "utf-8"
        
        # 去除HTML标签，提取纯文本
        text = re.sub(r'<script[^>]*>.*?</script>', '', resp.text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) > max_length:
            text = text[:max_length] + "...(截断)"
        
        return {"message": f"抓取成功，内容长度 {len(text)} 字符", "data": {
            "url": url, "title": re.search(r'<title>(.*?)</title>', resp.text, re.DOTALL),
            "content": text
        }}
    except Exception as e:
        return {"message": f"抓取失败: {e}", "data": {}}


def search_news(query: str) -> dict:
    """搜索新闻资讯（通过百度新闻）"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        url = f"https://www.baidu.com/s?wd={query}&tn=news&rn=10"
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"
        
        titles = re.findall(r'<h3[^>]*>(.*?)</h3>', resp.text, re.DOTALL)
        results = []
        for i, title_html in enumerate(titles[:10]):
            title = re.sub(r'<[^>]+>', '', title_html).strip()
            if title:
                results.append({"序号": i+1, "标题": title, "时间": datetime.now().strftime("%Y-%m-%d")})
        
        return {"message": f"新闻搜索'{query}'得到 {len(results)} 条", "data": results}
    except Exception as e:
        return {"message": f"新闻搜索失败: {e}", "data": []}


def check_website_status(url: str) -> dict:
    """检查网站可用状态"""
    try:
        resp = requests.get(url, timeout=10, allow_redirects=True)
        return {"message": "网站正常", "data": {
            "url": url,
            "status_code": resp.status_code,
            "response_time_ms": round(resp.elapsed.total_seconds() * 1000),
            "content_type": resp.headers.get("Content-Type", ""),
            "server": resp.headers.get("Server", ""),
        }}
    except requests.exceptions.Timeout:
        return {"message": "网站超时", "data": {"url": url, "status": "timeout"}}
    except Exception as e:
        return {"message": f"网站异常: {e}", "data": {"url": url, "status": "error"}}


# ═══════════════════════════════════════════
# 注册入口
# ═══════════════════════════════════════════

def register_web_search_tools(registry):
    """注册网络搜索工具"""
    from opcclaw.core.tool_registry import ToolDefinition
    
    registry.add_tool(ToolDefinition(
        name="web_search",
        description="搜索互联网信息（百度搜索）",
        parameters={"type": "object", "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
            "count": {"type": "integer", "description": "结果数量，默认10"}
        }},
        handler=lambda query="", count=10: web_search_baidu(query, count),
    ))
    
    registry.add_tool(ToolDefinition(
        name="fetch_webpage",
        description="抓取网页内容，提取纯文本",
        parameters={"type": "object", "properties": {
            "url": {"type": "string", "description": "网页URL"},
            "max_length": {"type": "integer", "description": "最大文本长度，默认5000"}
        }},
        handler=lambda url="", max_length=5000: fetch_webpage(url, max_length),
    ))
    
    registry.add_tool(ToolDefinition(
        name="search_news",
        description="搜索新闻资讯",
        parameters={"type": "object", "properties": {
            "query": {"type": "string", "description": "新闻关键词"}
        }},
        handler=lambda query="": search_news(query),
    ))
    
    registry.add_tool(ToolDefinition(
        name="check_website",
        description="检查网站是否可访问及响应速度",
        parameters={"type": "object", "properties": {
            "url": {"type": "string", "description": "要检查的网站URL"}
        }},
        handler=lambda url="": check_website_status(url),
    ))
```
