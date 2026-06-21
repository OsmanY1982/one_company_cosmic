# `iqra/tools/builtin/system_tools.py`

> 路径：`iqra/tools/builtin/system_tools.py` | 行数：564


---


```python
"""
Iqra 内置系统工具

提供 Agent 操控计算机的核心能力:
- exec: 执行 Shell/PowerShell 命令
- read: 读取文件 (文本自动检测编码 + 图片 base64)
- write: 写入文件 (自动创建目录)
- web_search: 网页搜索 (DuckDuckGo)
- web_fetch: 抓取网页内容

设计原则:
- 纯标准库, 零额外依赖
- 所有工具返回统一的 {"success": bool, ...} 格式
- Windows: PowerShell 执行命令; Linux/Mac: bash
"""

import os
import sys
import json
import subprocess
from pathlib import Path


# ═══════════════════════════════════════════
# web_search — 网页搜索工具
# ═══════════════════════════════════════════

def web_search(query: str, count: int = 5) -> dict:
    """
    网页搜索，使用 Bing 搜索引擎。
    支持任何关键词搜索，返回标题、摘要、链接。

    Args:
        query: 搜索关键词
        count: 返回结果数 (默认 5, 最大 10)

    Returns:
        {"success": bool, "query": str, "results": [{"title", "snippet", "url"}, ...]}
    """
    import urllib.request
    import urllib.parse
    import urllib.error
    import ssl
    import re

    # 创建不验证 SSL 证书的上下文
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&count={count}&setlang=zh-cn"

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        results = []

        # 解析 b_algo 结果块
        algo_blocks = re.split(
            r'<li[^>]*class="[^"]*b_algo[^"]*"[^>]*>', html,
            flags=re.IGNORECASE
        )

        for block in algo_blocks[1:]:
            if len(results) >= count:
                break
            h2 = re.search(
                r'<h2[^>]*>\s*<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>',
                block, re.DOTALL | re.IGNORECASE
            )
            snippet_m = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
            cite_m = re.search(r'<cite>(.*?)</cite>', block, re.DOTALL)

            title = re.sub(r'<[^>]+>', '', h2.group(2)).strip() if h2 else ""
            result_url = h2.group(1) if h2 else ""
            snippet = re.sub(r'<[^>]+>', '', snippet_m.group(1)).strip() if snippet_m else ""

            if not result_url and cite_m:
                result_url = re.sub(r'<[^>]+>', '', cite_m.group(1)).strip()

            if title or result_url:
                results.append({
                    "title": title or query,
                    "url": result_url,
                    "snippet": snippet[:300] if snippet else ""
                })

        # 回退: 用 cite 和散落链接
        if not results:
            cites = re.findall(r'<cite>(.*?)</cite>', html, re.DOTALL)
            for i, c in enumerate(cites[:count]):
                clean = re.sub(r'<[^>]+>', '', c).strip()
                results.append({
                    "title": f"结果 {i+1}",
                    "url": "https://" + clean if not clean.startswith("http") else clean,
                    "snippet": ""
                })

        if not results:
            results.append({
                "title": f"搜索: {query}",
                "snippet": f'未找到网页结果。可尝试用 web_fetch 打开已知网页。',
                "url": f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
            })

        return {"success": True, "query": query, "results": results[:count]}

    except urllib.error.URLError as e:
        return {"success": False, "query": query, "error": f"网络请求失败: {e.reason}"}
    except Exception as e:
        return {"success": False, "query": query, "error": str(e)}


# ═══════════════════════════════════════════
# web_fetch — 网页抓取工具
# ═══════════════════════════════════════════

def web_fetch(url_text: str, max_chars: int = 5000) -> dict:
    """
    抓取指定 URL 的网页内容，去除 HTML 标签后返回纯文本。

    Args:
        url_text: 目标网页 URL
        max_chars: 最大返回字符数 (默认 5000)

    Returns:
        {"success": bool, "url": str, "content": str}
    """
    import urllib.request
    import urllib.error
    import re
    import ssl

    # 创建不验证 SSL 证书的上下文（Windows Python 缺少根证书）
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        # 自动补充 https://
        if not url_text.startswith("http://") and not url_text.startswith("https://"):
            url_text = "https://" + url_text

        req = urllib.request.Request(url_text, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            content = resp.read().decode("utf-8", errors="replace")

        # 移除 script/style 和 HTML 标签
        text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'[ \t]+\n', '\n', text)
        text = text.strip()

        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n... (内容截断，总长 {len(text)} 字符)"

        return {"success": True, "url": url_text, "content": text}
    except urllib.error.HTTPError as e:
        return {"success": False, "url": url_text, "error": f"HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"success": False, "url": url_text, "error": f"无法连接: {e.reason}"}
    except Exception as e:
        return {"success": False, "url": url_text, "error": str(e)}


# ═══════════════════════════════════════════
# exec — 命令执行工具
# ═══════════════════════════════════════════

def exec_command(command: str, workdir: str = "", timeout: int = 30) -> dict:
    """
    执行 Shell 命令并返回结果。

    Args:
        command: 要执行的命令
        workdir: 工作目录 (可选, 默认当前目录)
        timeout: 超时秒数 (默认 30)

    Returns:
        {"success": bool, "stdout": str, "stderr": str, "exit_code": int}
    """
    try:
        cwd = workdir if workdir and os.path.isdir(workdir) else os.getcwd()

        # Windows 用 PowerShell, 其他用 bash
        if sys.platform == "win32":
            shell_cmd = command
            executable = None
        else:
            shell_cmd = command
            executable = "/bin/bash"

        result = subprocess.run(
            shell_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            encoding='utf-8',
            errors='replace',
            executable=executable,
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        return {
            "success": result.returncode == 0,
            "stdout": stdout if stdout else "(无输出)",
            "stderr": stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"命令超时 ({timeout}s): {command[:150]}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"执行失败: {e}",
        }


EXEC_TOOL = {
    "type": "function",
    "function": {
        "name": "exec",
        "description": (
            "执行 Shell 命令。可以运行任意命令行工具、脚本、系统命令。\n"
            "Windows 系统使用 PowerShell 语法, Linux/Mac 使用 bash。\n"
            "可以用于: 读取文件列表、运行程序、管理系统进程、网络请求等。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的 Shell 命令",
                },
                "workdir": {
                    "type": "string",
                    "description": "可选的工作目录路径",
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时秒数 (默认 30)",
                },
            },
            "required": ["command"],
        },
    },
}


# ═══════════════════════════════════════════
# read — 文件读取工具
# ═══════════════════════════════════════════

def read_file(path: str, offset: int = 1, limit: int = 100) -> dict:
    """
    读取文本文件或图片文件。

    文本文件: 返回内容 (支持 offset/limit 分页, 自动检测编码)
    图片文件: 返回 base64 data URI (jpg/png/gif/webp/bmp)

    Args:
        path: 文件路径 (绝对或相对)
        offset: 起始行号 (默认 1)
        limit: 最大行数 (默认 100)

    Returns:
        成功: {"success": True, "type": "text"|"image", "content": str, ...}
        失败: {"success": False, "error": str}
    """
    if not os.path.isfile(path):
        return {"success": False, "error": f"文件不存在: {path}"}

    file_size = os.path.getsize(path)
    ext = os.path.splitext(path)[1].lower()

    # ── 图片文件 ──
    if ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.ico', '.svg'):
        try:
            import base64
            with open(path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('ascii')

            mime_map = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.gif': 'image/gif',
                '.webp': 'image/webp', '.bmp': 'image/bmp',
                '.ico': 'image/x-icon', '.svg': 'image/svg+xml',
            }
            mime = mime_map.get(ext, 'application/octet-stream')

            return {
                "success": True,
                "type": "image",
                "mime": mime,
                "base64": f"data:{mime};base64,{data}",
                "size": file_size,
                "path": os.path.abspath(path),
            }
        except Exception as e:
            return {"success": False, "error": f"读取图片失败: {e}"}

    # ── 文本文件 ──
    try:
        # 尝试多种编码
        content = None
        used_enc = "unknown"
        for enc in ('utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030', 'latin-1'):
            try:
                with open(path, 'r', encoding=enc) as f:
                    content = f.read()
                used_enc = enc
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if content is None:
            return {"success": False, "error": f"无法解码文件: {path}"}

        lines = content.split('\n')
        total_lines = len(lines)

        start = max(0, offset - 1)
        end = min(total_lines, start + limit)
        selected = lines[start:end]

        truncated = end < total_lines
        result_lines = '\n'.join(selected)

        # 截断过大输出
        max_chars = 50000
        if len(result_lines) > max_chars:
            result_lines = (
                result_lines[:max_chars]
                + f"\n\n... [输出被截断, 共 {total_lines} 行, "
                + f"仅显示 {start+1}-{end} 行的前 {max_chars} 字符]"
            )

        return {
            "success": True,
            "type": "text",
            "content": result_lines,
            "total_lines": total_lines,
            "shown_lines": f"{start+1}-{end}",
            "truncated": truncated,
            "encoding": used_enc,
            "size": file_size,
            "path": os.path.abspath(path),
        }
    except Exception as e:
        return {"success": False, "error": f"读取文件失败: {e}"}


READ_TOOL = {
    "type": "function",
    "function": {
        "name": "read",
        "description": (
            "读取文件内容。\n"
            "文本文件: 返回文本内容, 支持分页读取 (offset/limit), 自动检测编码。\n"
            "图片文件: 返回 base64 编码的 data URI (支持 jpg/png/gif/webp/bmp/svg)。\n"
            "可以用于: 查看代码、配置文件、日志、图片等。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "要读取的文件路径 (绝对或相对路径)",
                },
                "offset": {
                    "type": "integer",
                    "description": "起始行号 (默认 1, 仅文本文件)",
                },
                "limit": {
                    "type": "integer",
                    "description": "最大行数 (默认 100, 仅文本文件)",
                },
            },
            "required": ["path"],
        },
    },
}


# ═══════════════════════════════════════════
# write — 文件写入工具
# ═══════════════════════════════════════════

def write_file(path: str, content: str, encoding: str = "utf-8") -> dict:
    """
    写入内容到文件 (自动创建父目录)。

    Args:
        path: 目标文件路径
        content: 写入内容
        encoding: 编码 (默认 utf-8, 可选 gbk/utf-8-sig 等)

    Returns:
        成功: {"success": True, "path": str, "size": int, "encoding": str}
        失败: {"success": False, "error": str}
    """
    try:
        parent = os.path.dirname(os.path.abspath(path))
        if parent:
            os.makedirs(parent, exist_ok=True)

        with open(path, 'w', encoding=encoding) as f:
            f.write(content)

        return {
            "success": True,
            "path": os.path.abspath(path),
            "size": os.path.getsize(path),
            "encoding": encoding,
        }
    except Exception as e:
        return {"success": False, "error": f"写入失败: {e}"}


WRITE_TOOL = {
    "type": "function",
    "function": {
        "name": "write",
        "description": (
            "将内容写入文件。自动创建父目录。\n"
            "可以用于: 创建配置文件、保存脚本、生成报告、写入日志等。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "目标文件路径",
                },
                "content": {
                    "type": "string",
                    "description": "要写入的内容",
                },
                "encoding": {
                    "type": "string",
                    "description": "文件编码 (默认 utf-8, Windows 上含中文可选 gbk)",
                },
            },
            "required": ["path", "content"],
        },
    },
}


# ═══════════════════════════════════════════
# web_search — 网页搜索 (OpenAI format)
# ═══════════════════════════════════════════

WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "搜索互联网，获取实时信息。\n"
            "使用 Bing 搜索引擎，返回相关网页的标题、摘要和链接。\n"
            "适合: 查新闻、查技术文档、查百科、查最新动态等需要联网的场景。\n"
            "提示: 搜索到链接后，可以用 web_fetch 工具打开网页读取详细内容。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词",
                },
                "count": {
                    "type": "integer",
                    "description": "返回结果数 (默认 5, 最大 10)",
                },
            },
            "required": ["query"],
        },
    },
}


# ═══════════════════════════════════════════
# web_fetch — 网页抓取 (OpenAI format)
# ═══════════════════════════════════════════

WEB_FETCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_fetch",
        "description": (
            "打开并读取网页内容，返回纯文本。\n"
            "自动去除 HTML 标签、脚本和样式，保留可读文本。\n"
            "适合: 阅读文章、查看文档、获取网页详情。\n"
            "通常与 web_search 配合使用: 先搜索找到链接，再用本工具打开页面。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url_text": {
                    "type": "string",
                    "description": "目标网页 URL (会自动补充 https://)",
                },
                "max_chars": {
                    "type": "integer",
                    "description": "最大返回字符数 (默认 5000)",
                },
            },
            "required": ["url_text"],
        },
    },
}


# ═══════════════════════════════════════════
# 工具批量注册入口
# ═══════════════════════════════════════════

BUILTIN_TOOLS = [EXEC_TOOL, READ_TOOL, WRITE_TOOL, WEB_SEARCH_TOOL, WEB_FETCH_TOOL]

BUILTIN_HANDLERS = {
    "exec": exec_command,
    "read": read_file,
    "write": write_file,
    "web_search": web_search,
    "web_fetch": web_fetch,
}


def register_system_tools(registry):
    """
    将 exec/read/write/web_search/web_fetch 五个内置系统工具注册到 ToolRegistry。

    Args:
        registry: ToolRegistry 实例
    """
    from iqra.core.tool_registry import ToolDefinition

    for tool_def in BUILTIN_TOOLS:
        name = tool_def["function"]["name"]
        handler = BUILTIN_HANDLERS.get(name)
        if handler:
            registry.add_tool(ToolDefinition(
                name=name,
                description=tool_def["function"]["description"],
                parameters=tool_def["function"]["parameters"],
                handler=handler,
            ))

```
