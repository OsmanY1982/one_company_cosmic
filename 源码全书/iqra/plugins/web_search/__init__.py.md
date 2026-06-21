# `iqra/plugins/web_search/__init__.py`

> 路径：`iqra/plugins/web_search/__init__.py` | 行数：175


---


```python
"""
网络搜索插件
集成多个搜索引擎，支持实时搜索
"""

import os
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    snippet: str
    source: str


class WebSearchPlugin:
    """网络搜索插件"""
    
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY", "")
        self.default_engine = "serper"  # 或 bing, google
    
    def search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        执行网络搜索
        
        Args:
            query: 搜索关键词
            num_results: 返回结果数量
        
        Returns:
            搜索结果字典
        """
        if not query.strip():
            return {"success": False, "error": "搜索关键词不能为空"}
        
        try:
            # 使用 Serper API (Google Search API)
            if self.api_key:
                return self._search_serper(query, num_results)
            else:
                # 降级：使用 DuckDuckGo 或 Bing
                return self._search_duckduckgo(query, num_results)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _search_serper(self, query: str, num: int) -> Dict[str, Any]:
        """使用 Serper API 搜索"""
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query, "num": num}).encode()
        
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
        
        results = []
        for item in data.get("organic", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                source="google"
            ))
        
        return {
            "success": True,
            "results": [
                {"title": r.title, "url": r.url, "snippet": r.snippet}
                for r in results
            ],
            "query": query
        }
    
    def _search_duckduckgo(self, query: str, num: int) -> Dict[str, Any]:
        """使用 DuckDuckGo 搜索（无需API Key）"""
        try:
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                results = []
                for r in ddgs.text(query, max_results=num):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")
                    })
                
                return {"success": True, "results": results, "query": query}
        except ImportError:
            return {
                "success": False, 
                "error": "未安装 duckduckgo-search，请运行: pip install duckduckgo-search"
            }
    
    def fetch_url(self, url: str) -> Dict[str, Any]:
        """获取网页内容"""
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode("utf-8", errors="ignore")
            
            # 简单提取文本
            text = self._extract_text_from_html(html)
            
            return {
                "success": True,
                "url": url,
                "title": self._extract_title(html),
                "content": text[:5000]  # 限制长度
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_text_from_html(self, html: str) -> str:
        """从HTML提取纯文本"""
        try:
            from html.parser import HTMLParser
            
            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text = []
                    self.skip_tags = {"script", "style", "nav", "footer", "header"}
                    self.current_tag = None
                
                def handle_starttag(self, tag, attrs):
                    self.current_tag = tag
                
                def handle_endtag(self, tag):
                    self.current_tag = None
                
                def handle_data(self, data):
                    if self.current_tag not in self.skip_tags:
                        self.text.append(data.strip())
            
            extractor = TextExtractor()
            extractor.feed(html)
            return "\n".join(extractor.text)
        except:
            # 降级：简单正则
            import re
            text = re.sub(r"<[^>]+>", "", html)
            return re.sub(r"\s+", " ", text).strip()
    
    def _extract_title(self, html: str) -> str:
        """提取网页标题"""
        import re
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""


def initialize(plugin_manager):
    """插件初始化"""
    plugin = WebSearchPlugin()
    plugin_manager.web_search = plugin
    print("[WebSearch] Plugin loaded")

```
