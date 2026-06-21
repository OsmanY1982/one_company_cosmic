"""AgentBridge 工具注册 Mixin（从 agent_bridge.py 拆出）

提供 19 个 _reg_* 工具注册方法 + _register_tools 调度器。
AgentBridge 继承本 Mixin 后即可通过 registry.register() 注册全部 LLM 工具。
"""

import os
import sys
import json
import subprocess
import fnmatch
import traceback
import time


class AgentBridgeToolsMixin:
    """工具注册：文件/代码/系统/Git/网络/Iqra 高级工具"""

    def _register_tools(self):
        """注册全部 19 个 LLM 工具"""
        # ── 文件系统工具 ──
        self._reg_read_file()
        self._reg_write_file()
        self._reg_edit_file()
        self._reg_list_directory()
        self._reg_search_files()
        # ── 代码工具 ──
        self._reg_search_code()
        self._reg_run_tests()
        # ── 系统工具 ──
        self._reg_execute_shell()
        self._reg_desktop_control()
        # ── Git ──
        self._reg_git_operation()
        # ── 网络 ──
        self._reg_web_search()
        self._reg_web_fetch_page()
        self._reg_web_scrape()
        self._reg_batch_scrape()
        # ── iqra 高级工具 ──
        self._reg_execute_python()
        self._reg_analyze_code()
        self._reg_search_codebase()
        self._reg_apply_patch()
        self._reg_todo()
        self._reg_task_scheduler()
        self._reg_search_sessions()

    # ── 1. read_file ──
    def _reg_read_file(self):
        def handler(path: str, limit: int = 200) -> dict:
            try:
                if not os.path.exists(path):
                    return {"error": f"文件不存在: {path}"}
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()[:limit]
                return {
                    "content": "".join(lines),
                    "total_lines": len(lines),
                    "truncated": len(lines) >= limit,
                    "path": path,
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="read_file",
            description="读取文本文件内容，返回行数和全文",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件绝对路径"},
                    "limit": {"type": "integer", "description": "最大读取行数，默认200", "default": 200},
                },
                "required": ["path"],
            },
            category="file",
        )(handler)

    # ── 2. write_file ──
    def _reg_write_file(self):
        def handler(path: str, content: str) -> dict:
            try:
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"success": True, "path": path, "bytes": len(content)}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="write_file",
            description="创建或覆盖写入文件（自动创建目录）",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件绝对路径"},
                    "content": {"type": "string", "description": "要写入的全部内容"},
                },
                "required": ["path", "content"],
            },
            category="file",
        )(handler)

    # ── 3. edit_file（精准行级编辑，对标 Claude Code）──
    def _reg_edit_file(self):
        def handler(path: str, old_str: str, new_str: str, replace_all: bool = False) -> dict:
            try:
                if not os.path.exists(path):
                    return {"error": f"文件不存在: {path}"}
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                count = content.count(old_str)
                if count == 0:
                    return {"error": f"未找到匹配文本。请确认 old_str 与文件中内容完全一致（含空格/换行）"}
                if not replace_all and count > 1:
                    return {
                        "error": f"找到 {count} 处匹配，请设置 replace_all=true 或提供更精确的 old_str",
                        "matches": count,
                    }
                new_content = content.replace(old_str, new_str) if replace_all else content.replace(old_str, new_str, 1)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return {
                    "success": True,
                    "path": path,
                    "replacements": count if replace_all else 1,
                    "old_bytes": len(content),
                    "new_bytes": len(new_content),
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="edit_file",
            description="精准替换文件中的文本片段（行级编辑）。old_str 必须与文件内容完全一致（含空格/换行）",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件绝对路径"},
                    "old_str": {"type": "string", "description": "要替换的原始文本，必须完全匹配"},
                    "new_str": {"type": "string", "description": "替换后的新文本"},
                    "replace_all": {"type": "boolean", "description": "是否替换所有匹配项", "default": False},
                },
                "required": ["path", "old_str", "new_str"],
            },
            category="file",
        )(handler)

    # ── 4. list_directory ──
    def _reg_list_directory(self):
        def handler(path: str, pattern: str = "*") -> dict:
            try:
                if not os.path.isdir(path):
                    return {"error": f"不是有效目录: {path}"}
                items = []
                for entry in sorted(os.listdir(path)):
                    full = os.path.join(path, entry)
                    is_dir = os.path.isdir(full)
                    items.append({
                        "name": entry,
                        "type": "dir" if is_dir else "file",
                        "size": os.path.getsize(full) if not is_dir else 0,
                    })
                if pattern != "*":
                    items = [i for i in items if fnmatch.fnmatch(i["name"], pattern)]
                return {"path": path, "count": len(items), "items": items[:200]}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="list_directory",
            description="列出目录内容。支持 fnmatch 过滤（如 *.py, test_*）",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "目录绝对路径"},
                    "pattern": {"type": "string", "description": "文件名通配符，默认 *", "default": "*"},
                },
                "required": ["path"],
            },
            category="file",
        )(handler)

    # ── 5. search_files（glob 搜索）──
    def _reg_search_files(self):
        def handler(directory: str, pattern: str, recursive: bool = True) -> dict:
            import glob
            try:
                if recursive:
                    search_pattern = os.path.join(directory, "**", pattern)
                else:
                    search_pattern = os.path.join(directory, pattern)
                results = glob.glob(search_pattern, recursive=recursive)
                return {"pattern": pattern, "count": len(results), "files": results[:100]}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="search_files",
            description="按通配符模式搜索文件（如 **/*.py 递归搜索所有 .py 文件）",
            parameters={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "搜索根目录"},
                    "pattern": {"type": "string", "description": "glob 模式（如 *.py, test_*.py, **/*.json）"},
                    "recursive": {"type": "boolean", "description": "是否递归子目录", "default": True},
                },
                "required": ["directory", "pattern"],
            },
            category="file",
        )(handler)

    # ── 6. search_code（ripgrep 代码搜索）──
    def _reg_search_code(self):
        def handler(query: str, directory: str = ".", file_pattern: str = "*", max_results: int = 50) -> dict:
            try:
                cmd = ["rg", "--line-number", "--max-count", str(max_results), query]
                if file_pattern != "*":
                    cmd.extend(["--glob", file_pattern])
                cmd.append(directory)
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                                       cwd=os.path.expanduser("~"))
                if result.returncode == 1:
                    return {"query": query, "count": 0, "matches": [], "note": "未找到匹配"}
                lines = result.stdout.strip().split("\n")[:max_results]
                return {"query": query, "count": len(lines), "matches": lines}
            except FileNotFoundError:
                # 回退到 grep
                try:
                    cmd = ["grep", "-rn", "--include=" + file_pattern if file_pattern != "*" else "-r", query, directory]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    lines = result.stdout.strip().split("\n")[:max_results]
                    return {"query": query, "count": len(lines), "matches": lines, "backend": "grep"}
                except Exception as e:
                    return {"error": f"ripgrep 和 grep 均不可用: {e}"}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="search_code",
            description="在代码库中搜索文本（ripgrep）。支持正则、文件类型过滤",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词或正则表达式"},
                    "directory": {"type": "string", "description": "搜索目录，默认当前目录", "default": "."},
                    "file_pattern": {"type": "string", "description": "文件类型过滤（如 *.py, *.js）", "default": "*"},
                    "max_results": {"type": "integer", "description": "最大结果数", "default": 50},
                },
                "required": ["query"],
            },
            category="code",
        )(handler)

    # ── 7. run_tests ──
    def _reg_run_tests(self):
        def handler(test_path: str = "", framework: str = "auto") -> dict:
            try:
                if not test_path:
                    return {"error": "请指定测试文件或目录路径"}
                if framework == "auto":
                    if "pytest" in test_path.lower() or os.path.exists("pytest.ini") or os.path.exists("pyproject.toml"):
                        framework = "pytest"
                    else:
                        framework = "unittest"

                if framework == "pytest":
                    result = subprocess.run(
                        [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"],
                        capture_output=True, text=True, timeout=120,
                        cwd=os.path.expanduser("~"),
                    )
                else:
                    result = subprocess.run(
                        [sys.executable, "-m", "unittest", test_path, "-v"],
                        capture_output=True, text=True, timeout=120,
                        cwd=os.path.expanduser("~"),
                    )
                return {
                    "framework": framework,
                    "returncode": result.returncode,
                    "passed": result.returncode == 0,
                    "stdout": result.stdout[-3000:],
                    "stderr": result.stderr[-1000:],
                }
            except subprocess.TimeoutExpired:
                return {"error": "测试超时（120秒）"}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="run_tests",
            description="运行测试套件（自动检测 pytest/unittest）",
            parameters={
                "type": "object",
                "properties": {
                    "test_path": {"type": "string", "description": "测试文件或目录路径"},
                    "framework": {"type": "string", "description": "pytest / unittest / auto", "default": "auto"},
                },
                "required": ["test_path"],
            },
            category="code",
        )(handler)

    # ── 8. execute_shell ──
    def _reg_execute_shell(self):
        def handler(command: str, timeout: int = 60) -> dict:
            try:
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True, timeout=timeout,
                    cwd=os.path.expanduser("~"),
                )
                return {
                    "stdout": result.stdout[:8000],
                    "stderr": result.stderr[:4000],
                    "returncode": result.returncode,
                }
            except subprocess.TimeoutExpired:
                return {"error": f"命令超时 ({timeout}s)", "stdout": "", "stderr": ""}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="execute_shell",
            description="在 macOS 终端执行 shell 命令。适用：安装依赖、运行脚本、系统查询",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "shell 命令"},
                    "timeout": {"type": "integer", "description": "超时秒数", "default": 60},
                },
                "required": ["command"],
            },
            category="system",
        )(handler)

    # ── 9. desktop_control（AppleScript 桌面操控）──
    def _reg_desktop_control(self):
        def handler(action: str, target: str = "", text: str = "") -> dict:
            try:
                scripts = {
                    "open_app": f'tell application "{target}" to activate',
                    "close_app": f'tell application "{target}" to quit',
                    "type_text": f'tell application "System Events" to keystroke "{text}"',
                    "press_keys": f'tell application "System Events" to keystroke "{text}"',
                    "get_frontmost": 'tell application "System Events" to get name of first application process whose frontmost is true',
                    "switch_app": f'tell application "{target}" to activate',
                    "open_url": f'open location "{target}"',
                    "volume_up": "set volume output volume (output volume of (get volume settings) + 10)",
                    "volume_down": "set volume output volume (output volume of (get volume settings) - 10)",
                    "mute": "set volume with output muted",
                    "sleep": 'tell application "System Events" to sleep',
                    "screenshot": 'do shell script "screencapture -i ~/Desktop/screenshot.png"',
                }
                if action not in scripts:
                    return {"error": f"不支持的操作: {action}。可用: {list(scripts.keys())}"}
                script = scripts[action]
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15)
                if result.returncode != 0:
                    return {"error": result.stderr.strip()}
                return {"success": True, "action": action, "output": result.stdout.strip()}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="desktop_control",
            description="macOS 桌面操控：打开/关闭应用、模拟输入、系统控制",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "操作: open_app/close_app/type_text/press_keys/switch_app/volume_up/volume_down/mute/sleep/screenshot"},
                    "target": {"type": "string", "description": "目标应用名/按键/URL", "default": ""},
                    "text": {"type": "string", "description": "要输入的文本（type_text/press_keys 时使用）", "default": ""},
                },
                "required": ["action"],
            },
            category="system",
        )(handler)

    # ── 10. git_operation ──
    def _reg_git_operation(self):
        def handler(operation: str, repo_path: str = ".", args: str = "") -> dict:
            try:
                valid_ops = ["status", "diff", "log", "branch", "add", "commit", "pull", "push", "stash", "checkout"]
                if operation not in valid_ops:
                    return {"error": f"不支持的 Git 操作: {operation}。可用: {valid_ops}"}

                cmd = ["git", "-C", repo_path, operation]
                if args:
                    cmd.extend(args.split())

                if operation == "commit":
                    cmd.append("-m")
                    cmd.append(args)

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                return {
                    "operation": operation,
                    "repo": repo_path,
                    "returncode": result.returncode,
                    "stdout": result.stdout[:4000],
                    "stderr": result.stderr[:2000],
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="git_operation",
            description="Git 版本控制：查看状态、diff、log、提交等",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "description": "Git 操作: status/diff/log/branch/add/commit/pull/push/stash/checkout"},
                    "repo_path": {"type": "string", "description": "仓库路径", "default": "."},
                    "args": {"type": "string", "description": "额外参数（如文件路径、commit message）", "default": ""},
                },
                "required": ["operation"],
            },
            category="code",
        )(handler)

    # ── 11. web_search ──
    def _reg_web_search(self):
        def handler(query: str, max_results: int = 8) -> dict:
            try:
                import urllib.request, urllib.parse
                url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                })
                with urllib.request.urlopen(req, timeout=10) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                from html.parser import HTMLParser

                class P(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.results = []
                        self._cur = {}
                        self._in_result = self._in_link = self._in_snippet = False
                    def handle_starttag(self, tag, attrs):
                        d = dict(attrs)
                        cls = d.get("class", "")
                        if tag == "div" and "result" in cls:
                            self._in_result = True
                            self._cur = {"title": "", "link": "", "snippet": ""}
                        if self._in_result and tag == "a" and "result__a" in cls:
                            self._in_link = True
                            self._cur["link"] = d.get("href", "")
                        if self._in_result and tag == "a" and "result__snippet" in cls:
                            self._in_snippet = True
                    def handle_endtag(self, tag):
                        if tag == "div" and self._cur:
                            self.results.append(self._cur)
                            self._cur = {}
                            self._in_result = False
                        if tag == "a":
                            self._in_link = self._in_snippet = False
                    def handle_data(self, data):
                        if self._in_link:
                            self._cur["title"] += data
                        if self._in_snippet:
                            self._cur["snippet"] += data

                parser = P()
                parser.feed(html)
                return {"query": query, "count": len(parser.results[:max_results]), "results": parser.results[:max_results]}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="web_search",
            description="DuckDuckGo 网页搜索，获取实时信息",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "max_results": {"type": "integer", "description": "最大结果数", "default": 8},
                },
                "required": ["query"],
            },
            category="web",
        )(handler)

    # ── 12. web_fetch_page ──
    def _reg_web_fetch_page(self):
        def handler(url: str) -> dict:
            try:
                import urllib.request
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")
                # 简易正文提取
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
                return {"url": url, "chars": len(content), "content": content[:8000]}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="web_fetch_page",
            description="抓取网页正文内容（提取纯文本）",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "网页 URL（含 https://）"},
                },
                "required": ["url"],
            },
            category="web",
        )(handler)

    # ── 12b. web_scrape（Iqra 智能爬虫）──
    def _reg_web_scrape(self):
        """Iqra 智能单页爬虫：JS 渲染 + 代理轮转 + 频率限制 + 重试"""
        def handler(url: str, use_selenium: bool = False, max_paragraphs: int = 20) -> dict:
            try:
                from iqra import Iqra, IqraConfig
                config = IqraConfig(
                    use_selenium=use_selenium,
                    output_format="dict",
                    timeout=30,
                )
                scraper = Iqra(config)
                result = scraper.scrape_url(url)
                scraper.close()
                if isinstance(result, dict) and "paragraphs" in result:
                    result["paragraphs"] = result["paragraphs"][:max_paragraphs]
                return result
            except Exception as e:
                return {"url": url, "error": str(e), "status": "failed"}

        self.registry.register(
            name="web_scrape",
            description="Iqra 智能网页爬虫：带 JS 渲染、代理轮转、频率限制、指数退避重试。返回标题/元描述/段落。适合需要 JS 渲染的动态页面。",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "目标网页 URL（含 https://）"},
                    "use_selenium": {"type": "boolean", "description": "是否启用 Selenium JS 渲染", "default": False},
                    "max_paragraphs": {"type": "integer", "description": "最大返回段落数", "default": 20},
                },
                "required": ["url"],
            },
            category="web",
        )(handler)

    # ── 12c. batch_scrape（Iqra 批量爬虫）──
    def _reg_batch_scrape(self):
        """Iqra 批量爬虫：一次抓取多个 URL"""
        def handler(urls: list, use_selenium: bool = False) -> dict:
            try:
                from iqra import Iqra, IqraConfig
                config = IqraConfig(
                    use_selenium=use_selenium,
                    output_format="dict",
                    timeout=30,
                )
                scraper = Iqra(config)
                results = scraper.batch_scrape(urls)
                scraper.close()
                success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
                return {
                    "total": len(urls),
                    "success": success_count,
                    "failed": len(urls) - success_count,
                    "results": results,
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="batch_scrape",
            description="Iqra 批量网页爬虫：一次性抓取多个 URL，返回汇总统计和逐页结果。",
            parameters={
                "type": "object",
                "properties": {
                    "urls": {"type": "array", "items": {"type": "string"}, "description": "目标网页 URL 列表"},
                    "use_selenium": {"type": "boolean", "description": "是否启用 Selenium JS 渲染", "default": False},
                },
                "required": ["urls"],
            },
            category="web",
        )(handler)

    # ── 13. execute_python ──
    def _reg_execute_python(self):
        """Python 沙箱执行（code_executor 模块）"""
        def handler(code: str, timeout: int = 30) -> dict:
            if not self._code_executor:
                return {"error": "Python 沙箱未启用（code_executor 模块缺失）"}
            try:
                result = self._code_executor.execute(code, timeout=timeout)
                return {
                    "success": result.success,
                    "output": result.output or "",
                    "error": result.error or "",
                    "duration_ms": result.duration_ms,
                }
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="execute_python",
            description="在安全沙箱中执行 Python 代码，返回标准输出和错误",
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的 Python 代码"},
                    "timeout": {"type": "integer", "description": "超时秒数，默认30", "default": 30},
                },
                "required": ["code"],
            },
            category="code",
        )(handler)

    # ── 14. analyze_code ──
    def _reg_analyze_code(self):
        """代码智能分析（code_intel 模块）"""
        def handler(file_path: str, action: str = "symbols") -> dict:
            if not os.path.exists(file_path):
                return {"error": f"文件不存在: {file_path}"}
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()
                # 复用 agent_bridge 模块级 _HAVE_CODE_INTEL
                from modules.intelligence.agent_bridge import _HAVE_CODE_INTEL
                if _HAVE_CODE_INTEL:
                    import ast
                    from iqra.core.code_intel import SymbolExtractor
                    extractor = SymbolExtractor(source.split("\n"))
                    extractor.visit(ast.parse(source))
                    symbols = extractor._symbols if hasattr(extractor, '_symbols') else []
                    return {"file": file_path, "symbols": [s.__dict__ if hasattr(s, '__dict__') else str(s) for s in symbols], "total": len(symbols)}
                else:
                    return {"error": "代码智能引擎未启用（code_intel 模块缺失）"}
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="analyze_code",
            description="分析代码文件的符号结构（函数/类/变量定义）",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "要分析的代码文件绝对路径"},
                    "action": {
                        "type": "string",
                        "description": "分析类型: symbols（符号提取）/ usages（引用搜索）/ imports（依赖分析）/ refactor（重构建议）",
                        "enum": ["symbols", "usages", "imports", "refactor"],
                        "default": "symbols",
                    },
                },
                "required": ["file_path"],
            },
            category="code",
        )(handler)

    # ── 15. search_codebase ──
    def _reg_search_codebase(self):
        """代码库语义/全文搜索（workspace_indexer 模块）"""
        def handler(query: str, top_k: int = 10) -> dict:
            from modules.intelligence.agent_bridge import _HAVE_INDEXER
            if _HAVE_INDEXER:
                try:
                    from iqra.core.workspace_indexer import WorkspaceIndexer
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    indexer = WorkspaceIndexer(project_root)
                    results = indexer.search(query, top_k=top_k)
                    return {
                        "query": query,
                        "results": [{"path": r.path, "score": round(r.score, 3), "snippet": r.snippet} for r in results],
                        "count": len(results),
                    }
                except Exception as e:
                    return {"error": str(e)}
            return {"error": "代码库索引器未启用（workspace_indexer 模块缺失）"}
        self.registry.register(
            name="search_codebase",
            description="在项目代码库中全文搜索，支持中文和英文关键词",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "top_k": {"type": "integer", "description": "返回结果数，默认10", "default": 10},
                },
                "required": ["query"],
            },
            category="code",
        )(handler)

    # ── 16. apply_patch ──
    def _reg_apply_patch(self):
        """文件补丁引擎（patch_engine 模块）"""
        def handler(file_path: str, pattern: str, replacement: str, dry_run: bool = True) -> dict:
            if not self._patch_engine:
                return {"error": "补丁引擎未启用（patch_engine 模块缺失）"}
            try:
                if dry_run:
                    result = self._patch_engine.preview(file_path, pattern, replacement)
                else:
                    result = self._patch_engine.apply(file_path, pattern, replacement)
                return {
                    "file": file_path,
                    "dry_run": dry_run,
                    "matches": result.get("matches", 0),
                    "changes": result.get("changes", []),
                    "success": result.get("success", False),
                }
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="apply_patch",
            description="对文件执行查找替换补丁（默认预览不写入）",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "目标文件绝对路径"},
                    "pattern": {"type": "string", "description": "要查找的文本模式"},
                    "replacement": {"type": "string", "description": "替换后的文本"},
                    "dry_run": {"type": "boolean", "description": "是否仅预览不实际修改，默认true", "default": True},
                },
                "required": ["file_path", "pattern", "replacement"],
            },
            category="code",
        )(handler)

    # ── 17. todo ──
    def _reg_todo(self):
        """任务清单（todo_system 模块）"""
        def handler(action: str = "list", title: str = "", status: str = "") -> dict:
            todo = self._todo
            if not todo:
                return {"error": "任务系统未启用（todo_system 模块缺失）"}
            try:
                if action == "add":
                    item = todo.add(title)
                    return {"action": "add", "item": item}
                elif action == "list":
                    items = todo.list()
                    return {"action": "list", "items": items, "total": len(items)}
                elif action == "done":
                    result = todo.mark_done(title)
                    return {"action": "done", "result": result}
                else:
                    return {"error": f"未知操作: {action}，支持 add/list/done"}
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="todo",
            description="管理任务清单：添加、查看、标记完成",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "操作: add（添加）/ list（查看）/ done（完成）", "default": "list"},
                    "title": {"type": "string", "description": "任务标题（add/done 时需要）"},
                    "status": {"type": "string", "description": "状态过滤（list 时可选）"},
                },
                "required": [],
            },
            category="productivity",
        )(handler)

    # ── 18. task_scheduler ──
    def _reg_task_scheduler(self):
        """定时任务（task_scheduler 模块）"""
        def handler(action: str = "list", title: str = "", schedule: str = "") -> dict:
            sched = self._task_scheduler
            if not sched:
                return {"error": "定时任务未启用（task_scheduler 模块缺失）"}
            try:
                if action == "add":
                    task = sched.add(title, schedule)
                    return {"action": "add", "task": task}
                elif action == "list":
                    tasks = sched.list()
                    return {"action": "list", "tasks": tasks}
                elif action == "remove":
                    sched.remove(title)
                    return {"action": "remove", "title": title, "success": True}
                else:
                    return {"error": f"未知操作: {action}，支持 add/list/remove"}
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="task_scheduler",
            description="管理定时任务：创建、查看、删除",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "操作: add（添加）/ list（查看）/ remove（删除）", "default": "list"},
                    "title": {"type": "string", "description": "任务标题"},
                    "schedule": {"type": "string", "description": "调度表达式（add 时需要），如 'daily 08:00'"},
                },
                "required": [],
            },
            category="productivity",
        )(handler)

    # ── 19. search_sessions ──
    def _reg_search_sessions(self):
        """历史会话搜索（session_search 模块）"""
        def handler(query: str, top_k: int = 10) -> dict:
            ss = self._session_search
            if not ss:
                return {"error": "会话搜索未启用（session_search 模块缺失）"}
            try:
                results = ss.search(query, top_k=top_k)
                return {"query": query, "results": results, "count": len(results)}
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="search_sessions",
            description="搜索历史对话会话，找到之前讨论过的内容",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "top_k": {"type": "integer", "description": "返回结果数，默认10", "default": 10},
                },
                "required": ["query"],
            },
            category="memory",
        )(handler)
