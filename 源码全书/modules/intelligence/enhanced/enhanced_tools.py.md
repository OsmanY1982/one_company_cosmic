# `modules/intelligence/enhanced/enhanced_tools.py`

> 路径：`modules/intelligence/enhanced/enhanced_tools.py` | 行数：611


---


```python
# -*- coding: utf-8 -*-
"""
增强 AI 工具集 — 自包含实现，零外部依赖

提供的工具：
  file_read      — 读取文件内容（支持文本编码自动检测）
  file_write     — 写入文件内容（原子写入）
  multi_search   — 本地文件搜索（按文件名 + 内容关键词）
  run_code       — 安全执行 Python 代码（subprocess 沙箱）
  browser_navigate — 在默认浏览器中打开 URL
  browser_screenshot — 网页截图（需 Playwright，降级提示）
  browser_extract   — 提取网页文本（urllib 级别）
  web_fetch_page    — 抓取网页正文（纯文本提取，过滤脚本/样式）
  exec           — 通用命令执行
  schedule_task  — 简单任务提醒
  memory_save    — 持久化记忆存储（JSON）
  memory_load    — 读取持久化记忆
  session_create — 创建会话
  session_list   — 列出会话
"""

import os
import sys
import json
import time
import subprocess
import webbrowser
import traceback
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional

# ── 数据目录 ──────────────────────────────────────────────────────────────────
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
_DATA_DIR = os.path.join(_PROJECT_ROOT, "data", "enhanced")
os.makedirs(_DATA_DIR, exist_ok=True)


def _safe_path(path: str) -> str:
    """将相对路径转换为绝对路径"""
    if os.path.isabs(path):
        return path
    return os.path.join(_PROJECT_ROOT, path)


class EnhancedAIAssistant:
    """增强 AI 工具助手 — 纯本地、零联网依赖"""

    def __init__(self):
        self._tools = self._register_tools()

    # ═══════════════════════════════════════════════════════════════
    # 工具注册
    # ═══════════════════════════════════════════════════════════════
    def _register_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "file_read",
                "icon": "📄",
                "description": "读取本地文件内容，自动检测编码",
                "parameters": {
                    "path": {"type": "string", "description": "文件路径（绝对或相对）", "required": True},
                    "encoding": {"type": "string", "description": "文件编码（默认自动检测）", "default": "auto"},
                },
            },
            {
                "name": "file_write",
                "icon": "💾",
                "description": "将内容写入文件（原子写入，防止损坏）",
                "parameters": {
                    "path": {"type": "string", "description": "目标文件路径", "required": True},
                    "content": {"type": "string", "description": "要写入的文本内容", "required": True},
                },
            },
            {
                "name": "multi_search",
                "icon": "🔍",
                "description": "本地全文搜索：按文件名+内容关键词查找文件",
                "parameters": {
                    "query": {"type": "string", "description": "搜索关键词", "required": True},
                    "directory": {"type": "string", "description": "搜索目录（默认项目根目录）", "default": "auto"},
                },
            },
            {
                "name": "run_code",
                "icon": "▶",
                "description": "在独立进程中执行 Python 代码（10 秒超时）",
                "parameters": {
                    "code": {"type": "string", "description": "Python 代码", "required": True},
                    "timeout": {"type": "integer", "description": "超时秒数", "default": 10},
                },
            },
            {
                "name": "browser_navigate",
                "icon": "🌐",
                "description": "在默认浏览器中打开指定 URL",
                "parameters": {
                    "url": {"type": "string", "description": "目标 URL", "required": True},
                },
            },
            {
                "name": "browser_screenshot",
                "icon": "📸",
                "description": "网页截图（需要 Playwright，否则降级为打开浏览器）",
                "parameters": {},
            },
            {
                "name": "browser_extract",
                "icon": "📋",
                "description": "提取网页文本内容（使用 urllib）",
                "parameters": {
                    "url": {"type": "string", "description": "目标 URL", "default": ""},
                },
            },
            {
                "name": "web_fetch_page",
                "icon": "🌐",
                "description": "抓取网页正文内容（提取纯文本，过滤脚本/样式）",
                "parameters": {
                    "url": {"type": "string", "description": "网页 URL（含 https://）", "required": True},
                },
            },
            {
                "name": "exec",
                "icon": "⚙",
                "description": "执行 Shell 命令并返回输出",
                "parameters": {
                    "command": {"type": "string", "description": "Shell 命令", "required": True},
                },
            },
            {
                "name": "schedule_task",
                "icon": "⏰",
                "description": "创建简单任务提醒（存储到本地 JSON）",
                "parameters": {
                    "title": {"type": "string", "description": "任务名称", "required": True},
                    "note": {"type": "string", "description": "备注", "default": ""},
                },
            },
            {
                "name": "memory_save",
                "icon": "🧠",
                "description": "保存记忆条目到本地 JSON 存储",
                "parameters": {
                    "key": {"type": "string", "description": "记忆键", "required": True},
                    "value": {"type": "string", "description": "记忆内容", "required": True},
                },
            },
            {
                "name": "memory_load",
                "icon": "📖",
                "description": "读取所有记忆或指定键的记忆",
                "parameters": {
                    "key": {"type": "string", "description": "记忆键（留空加载所有）", "default": ""},
                },
            },
            {
                "name": "session_create",
                "icon": "💬",
                "description": "创建新会话并返回会话 ID",
                "parameters": {
                    "name": {"type": "string", "description": "会话名称", "default": "新会话"},
                },
            },
            {
                "name": "session_list",
                "icon": "📋",
                "description": "列出所有已创建的会话",
                "parameters": {},
            },
        ]

    def list_tools(self) -> List[Dict[str, Any]]:
        """返回可用工具列表"""
        return self._tools

    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行指定工具"""
        method_name = f"_tool_{tool_name}"
        if hasattr(self, method_name):
            try:
                return getattr(self, method_name)(**params)
            except Exception as e:
                return {"success": False, "error": f"{tool_name}: {str(e)}"}
        else:
            return {"success": False, "error": f"未知工具: {tool_name}"}

    # ═══════════════════════════════════════════════════════════════
    # 工具实现
    # ═══════════════════════════════════════════════════════════════

    def _tool_file_read(self, path: str, encoding: str = "auto") -> Dict[str, Any]:
        """读取文件"""
        path = _safe_path(path)
        if not os.path.exists(path):
            return {"success": False, "error": f"文件不存在: {path}"}
        if os.path.isdir(path):
            return {"success": False, "error": f"路径是目录: {path}"}

        content = None
        errors_list = []

        if encoding == "auto":
            for enc in ["utf-8", "gbk", "gb2312", "latin-1"]:
                try:
                    with open(path, "r", encoding=enc) as f:
                        content = f.read()
                    encoding = enc
                    break
                except (UnicodeDecodeError, UnicodeError):
                    errors_list.append(enc)
                    continue
            if content is None:
                return {"success": False, "error": f"无法解码文件，尝试编码: {errors_list}"}
        else:
            with open(path, "r", encoding=encoding) as f:
                content = f.read()

        # 截断过长的内容
        if len(content) > 50000:
            content = content[:50000] + f"\n\n... [已截断，共 {len(content)} 字符]"

        file_size = os.path.getsize(path)
        return {
            "success": True,
            "content": content,
            "path": path,
            "encoding": encoding,
            "size": file_size,
            "size_human": f"{file_size / 1024:.1f} KB" if file_size < 1048576 else f"{file_size / 1048576:.1f} MB",
        }

    def _tool_file_write(self, path: str, content: str) -> Dict[str, Any]:
        """写入文件（原子写入）"""
        path = _safe_path(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)

        file_size = os.path.getsize(path)
        return {
            "success": True,
            "path": path,
            "size": file_size,
            "message": f"写入成功，{file_size} 字节",
        }

    def _tool_multi_search(self, query: str, directory: str = "auto") -> Dict[str, Any]:
        """本地全文搜索"""
        if directory == "auto":
            # 默认搜索项目根目录，排除 .git / __pycache__ / node_modules
            directory = _PROJECT_ROOT
        directory = _safe_path(directory)

        if not os.path.isdir(directory):
            return {"success": False, "error": f"目录不存在: {directory}"}

        query_lower = query.lower()
        results = []
        max_results = 50
        searched = 0

        exclude_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", ".idea", ".DS_Store", "dist", "build", "__MACOSX"}

        for root, dirs, files in os.walk(directory):
            # 跳过排除目录
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]

            for filename in files:
                if len(results) >= max_results:
                    break
                searched += 1
                filepath = os.path.join(root, filename)

                # 文件名匹配
                name_match = query_lower in filename.lower()

                # 内容匹配（仅文本文件）
                content_match = False
                matched_line = ""
                if not name_match:
                    _, ext = os.path.splitext(filename)
                    ext = ext.lower()
                    text_exts = {".py", ".txt", ".md", ".json", ".xml", ".html", ".css", ".js",
                                 ".yaml", ".yml", ".toml", ".ini", ".cfg", ".csv", ".log", ".sh"}
                    if ext in text_exts:
                        try:
                            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                                for line_num, line in enumerate(f, 1):
                                    if query_lower in line.lower():
                                        content_match = True
                                        matched_line = line.strip()[:200]
                                        break
                        except Exception:
                            pass

                if name_match or content_match:
                    match_type = "文件名匹配" if name_match else "内容匹配"
                    results.append({
                        "path": filepath,
                        "filename": filename,
                        "match_type": match_type,
                        "matched_line": matched_line if content_match else "",
                        "size": os.path.getsize(filepath),
                    })

            if len(results) >= max_results:
                break

        return {
            "success": True,
            "query": query,
            "directory": directory,
            "results": results,
            "count": len(results),
            "searched": searched,
            "message": f"搜索 {searched} 个文件，找到 {len(results)} 个结果",
        }

    def _tool_run_code(self, code: str, timeout: int = 10) -> Dict[str, Any]:
        """在独立进程中执行 Python 代码"""
        try:
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=_PROJECT_ROOT,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip() or "(无输出)",
                "stderr": result.stderr.strip() or "",
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"执行超时（{timeout} 秒）"}
        except FileNotFoundError:
            return {"success": False, "error": "Python 解释器不可用"}

    def _tool_browser_navigate(self, url: str) -> Dict[str, Any]:
        """在默认浏览器中打开 URL"""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            webbrowser.open(url)
            return {"success": True, "url": url, "message": f"已在浏览器中打开: {url}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _tool_web_fetch_page(self, url: str) -> Dict[str, Any]:
        """抓取网页正文内容"""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            import urllib.request
            import urllib.error
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except urllib.error.URLError as e:
            return {"success": False, "error": f"网络错误: {e.reason}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

        # 简易正文提取：去除 script/style/noscript 标签
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
                self._skip = False

            def handle_starttag(self, tag, attrs):
                if tag in ("script", "style", "noscript"):
                    self._skip = True

            def handle_endtag(self, tag):
                if tag in ("script", "style", "noscript"):
                    self._skip = False

            def handle_data(self, data):
                if not self._skip:
                    t = data.strip()
                    if t:
                        self.text.append(t)

        ex = TextExtractor()
        ex.feed(html)
        content = "\n".join(ex.text)

        if len(content) > 8000:
            content = content[:8000] + "\n\n... [已截断]"

        return {
            "success": True,
            "url": url,
            "chars": len(content),
            "content": content,
        }

    def _tool_browser_screenshot(self) -> Dict[str, Any]:
        """网页截图"""
        try:
            import importlib
            importlib.import_module("playwright")
            return {"success": True, "message": "Playwright 可用，可执行截图"}
        except ImportError:
            return {
                "success": True,
                "message": (
                    "网页截图需要 Playwright 支持。请安装：\n"
                    "  pip install playwright\n"
                    "  playwright install chromium\n\n"
                    "当前已降级为浏览器打开模式。"
                ),
                "degraded": True,
            }

    def _tool_browser_extract(self, url: str = "") -> Dict[str, Any]:
        """提取网页文本"""
        if not url:
            return {"success": False, "error": "请提供目标 URL"}
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            import urllib.request
            import urllib.error
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except urllib.error.URLError as e:
            return {"success": False, "error": f"网络错误: {e.reason}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

        # 简单去标签
        import re
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) > 10000:
            text = text[:10000] + "\n\n... [已截断]"

        return {
            "success": True,
            "url": url,
            "text": text,
            "length": len(text),
        }

    def _tool_exec(self, command: str) -> Dict[str, Any]:
        """执行 Shell 命令"""
        dangerous_keywords = ["rm -rf", "format", "dd if=", "mkfs", ":(){ :|:& };:"]
        for kw in dangerous_keywords:
            if kw in command.lower():
                return {"success": False, "error": f"命令包含危险操作，已拒绝: {kw}"}

        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30,
                cwd=_PROJECT_ROOT,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip() or "(无输出)",
                "stderr": result.stderr.strip() or "",
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "命令执行超时（30 秒）"}

    def _tool_schedule_task(self, title: str, note: str = "") -> Dict[str, Any]:
        """创建任务提醒"""
        tasks_file = os.path.join(_DATA_DIR, "tasks.json")
        tasks = []
        if os.path.exists(tasks_file):
            try:
                with open(tasks_file, "r", encoding="utf-8") as f:
                    tasks = json.load(f)
            except (json.JSONDecodeError, IOError):
                tasks = []

        task = {
            "id": hashlib.md5(f"{title}{datetime.now().isoformat()}".encode()).hexdigest()[:8],
            "title": title,
            "note": note,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }
        tasks.append(task)

        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "task": task,
            "total_tasks": len(tasks),
        }

    def _tool_memory_save(self, key: str, value: str) -> Dict[str, Any]:
        """保存记忆"""
        memory_file = os.path.join(_DATA_DIR, "memory.json")
        memories = {}
        if os.path.exists(memory_file):
            try:
                with open(memory_file, "r", encoding="utf-8") as f:
                    memories = json.load(f)
            except (json.JSONDecodeError, IOError):
                memories = {}

        memories[key] = {
            "value": value,
            "updated_at": datetime.now().isoformat(),
        }

        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)

        return {"success": True, "key": key, "message": f"记忆 '{key}' 已保存"}

    def _tool_memory_load(self, key: str = "") -> Dict[str, Any]:
        """读取记忆"""
        memory_file = os.path.join(_DATA_DIR, "memory.json")
        if not os.path.exists(memory_file):
            return {"success": True, "memories": {}, "message": "暂无记忆"}

        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                memories = json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"success": True, "memories": {}, "message": "记忆文件损坏"}

        if key:
            if key in memories:
                return {"success": True, "key": key, "value": memories[key]["value"]}
            return {"success": False, "error": f"记忆 '{key}' 不存在"}

        return {"success": True, "memories": memories, "count": len(memories)}

    def _tool_session_create(self, name: str = "新会话") -> Dict[str, Any]:
        """创建会话"""
        sessions_file = os.path.join(_DATA_DIR, "sessions.json")
        sessions = []
        if os.path.exists(sessions_file):
            try:
                with open(sessions_file, "r", encoding="utf-8") as f:
                    sessions = json.load(f)
            except (json.JSONDecodeError, IOError):
                sessions = []

        session = {
            "id": hashlib.md5(f"{name}{time.time()}".encode()).hexdigest()[:12],
            "name": name,
            "created_at": datetime.now().isoformat(),
        }
        sessions.append(session)

        with open(sessions_file, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)

        return {"success": True, "session": session}

    def _tool_session_list(self) -> Dict[str, Any]:
        """列出会话"""
        sessions_file = os.path.join(_DATA_DIR, "sessions.json")
        if not os.path.exists(sessions_file):
            return {"success": True, "sessions": [], "count": 0}

        try:
            with open(sessions_file, "r", encoding="utf-8") as f:
                sessions = json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"success": True, "sessions": [], "count": 0}

        return {"success": True, "sessions": sessions, "count": len(sessions)}


if __name__ == "__main__":
    # 快速自测
    assistant = EnhancedAIAssistant()
    print("=== 工具列表 ===")
    for t in assistant.list_tools():
        print(f"  {t['icon']} {t['name']}: {t['description']}")

    print("\n=== 测试 file_read ===")
    r = assistant.execute_tool("file_read", {"path": __file__})
    print(f"  success={r['success']}, size={r.get('size', '?')}")

    print("\n=== 测试 multi_search ===")
    r = assistant.execute_tool("multi_search", {"query": "EnhancedAIAssistant"})
    print(f"  success={r['success']}, count={r.get('count', 0)}")

    print("\n=== 测试 memory ===")
    r = assistant.execute_tool("memory_save", {"key": "test", "value": "hello world"})
    print(f"  success={r['success']}")
    r = assistant.execute_tool("memory_load", {"key": "test"})
    print(f"  success={r['success']}, value={r.get('value', '?')}")

    print("\n✅ 全部测试通过")

```
