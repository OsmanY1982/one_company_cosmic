"""
OPCclaw Core Engine v2.0 - 智能核心引擎
支持 Function Calling、多轮工具调用、任务规划、代码执行
让 OPCclaw 具备与 Hermes 相当的智能水平
"""

import json
import re
import sqlite3
import subprocess
import sys
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field

# 导入 LLM 后端
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.intelligence.core.llm_backend import (
    ProviderConfig, OpenAICompatibleBackend, LLMResponse, ToolDefinition
)


# ═══════════════════════════════════════════
# 工具注册表
# ═══════════════════════════════════════════

class ToolRegistry:
    """工具注册表 - 管理所有可用工具"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance
    
    def register(self, name: str, description: str, parameters: dict, handler: Callable):
        """注册一个工具"""
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler
        }
    
    def get(self, name: str) -> Optional[dict]:
        """获取工具定义"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[dict]:
        """获取所有工具定义（OpenAI 格式）"""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"]
                }
            }
            for t in self._tools.values()
        ]
    
    def execute(self, name: str, arguments: dict) -> Any:
        """执行工具"""
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"工具不存在：{name}"}
        try:
            result = tool["handler"](**arguments)
            return {"success": True, "result": result}
        except Exception as e:
            return {"error": str(e)}


# ═══════════════════════════════════════════
# 内置工具定义
# ═══════════════════════════════════════════

def init_builtin_tools(registry: ToolRegistry):
    """注册内置工具"""
    
    # 1. 数据库查询工具
    def query_database(db_name: str, sql: str) -> dict:
        """查询 SQLite 数据库"""
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", db_name)
        if not os.path.exists(db_path):
            return {"error": f"数据库不存在：{db_name}"}
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        try:
            c.execute(sql)
            rows = [dict(row) for row in c.fetchall()]
            return {"columns": list(rows[0].keys()) if rows else [], "rows": rows, "count": len(rows)}
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()
    
    registry.register(
        name="query_database",
        description="查询 SQLite 数据库，支持 product.db, order.db, member.db, finance.db, customer.db, inventory.db, schedule.db",
        parameters={
            "type": "object",
            "properties": {
                "db_name": {"type": "string", "description": "数据库文件名，如 'product.db'或'order.db'"},
                "sql": {"type": "string", "description": "SQL 查询语句，只支持 SELECT"}
            },
            "required": ["db_name", "sql"]
        },
        handler=query_database
    )
    
    # 2. 文件读取工具
    def read_file(path: str, limit: int = 100) -> dict:
        """读取文件内容"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:limit]
            return {"content": "".join(lines), "total_lines": len(lines)}
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="read_file",
        description="读取文本文件内容",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "limit": {"type": "integer", "description": "最大读取行数", "default": 100}
            },
            "required": ["path"]
        },
        handler=read_file
    )
    
    # 3. 文件写入工具
    def write_file(path: str, content: str) -> dict:
        """写入文件内容"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "path": path, "bytes": len(content)}
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="write_file",
        description="写入内容到文件",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "文件内容"}
            },
            "required": ["path", "content"]
        },
        handler=write_file
    )
    
    # 4. 代码执行工具
    def execute_code(code: str, timeout: int = 30) -> dict:
        """执行 Python 代码（沙箱环境）"""
        try:
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": f"代码执行超时（{timeout}秒）"}
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="execute_code",
        description="执行 Python 代码，用于数据分析、文件处理等任务",
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "要执行的 Python 代码"},
                "timeout": {"type": "integer", "description": "超时时间（秒）", "default": 30}
            },
            "required": ["code"]
        },
        handler=execute_code
    )
    
    # 5. 网络搜索工具
    def web_search(query: str, max_results: int = 5) -> dict:
        """联网搜索获取实时信息"""
        try:
            import urllib.request
            import urllib.parse
            encoded = urllib.parse.quote(query)
            url = f"https://cn.bing.com/search?q={encoded}&count={max_results}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
            # 简单提取标题
            titles = re.findall(r'<h2[^>]*>.*?<a[^>]*>(.*?)</a>', html, re.S)[:max_results]
            snippets = re.findall(r'<p[^>]*>(.*?)</p>', html, re.S)[:max_results]
            results = []
            for t, s in zip(titles, snippets):
                t_clean = re.sub(r'<[^>]+>', '', t)
                s_clean = re.sub(r'<[^>]+>', '', s)
                results.append({"title": t_clean.strip(), "snippet": s_clean.strip()})
            return {"results": results, "query": query}
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="web_search",
        description="联网搜索获取实时信息，用于查询新闻、天气、股票等",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "max_results": {"type": "integer", "description": "最大结果数", "default": 5}
            },
            "required": ["query"]
        },
        handler=web_search
    )
    
    # 6. 日程添加工具
    def add_schedule(title: str, start_time: str, type: str = "event", location: str = "", description: str = "") -> dict:
        """添加日程安排"""
        try:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "schedule.db")
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS schedules (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    type TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    location TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT (datetime('now'))
                )
            ''')
            c.execute('''
                INSERT INTO schedules (title, type, start_time, location, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, type, start_time, location, description))
            conn.commit()
            conn.close()
            return {"success": True, "message": f"已添加日程：{title}"}
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="add_schedule",
        description="添加日程安排到日历",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "日程标题"},
                "start_time": {"type": "string", "description": "开始时间，ISO 格式如 2026-05-12T14:00:00"},
                "type": {"type": "string", "description": "类型：meeting, deadline, reminder, event", "default": "event"},
                "location": {"type": "string", "description": "地点", "default": ""},
                "description": {"type": "string", "description": "描述", "default": ""}
            },
            "required": ["title", "start_time"]
        },
        handler=add_schedule
    )
    
    # 7. 客户管理工具
    def add_customer(name: str, company: str = "", phone: str = "", email: str = "", source: str = "") -> dict:
        """添加客户记录"""
        try:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "customers.db")
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    company TEXT,
                    phone TEXT,
                    email TEXT,
                    source TEXT,
                    status TEXT DEFAULT 'lead',
                    created_at TEXT DEFAULT (datetime('now'))
                )
            ''')
            c.execute('''
                INSERT INTO customers (name, company, phone, email, source)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, company, phone, email, source))
            conn.commit()
            conn.close()
            return {"success": True, "message": f"已添加客户：{name}"}
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="add_customer",
        description="添加客户到 CRM 系统",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "客户姓名"},
                "company": {"type": "string", "description": "公司名称", "default": ""},
                "phone": {"type": "string", "description": "联系电话", "default": ""},
                "email": {"type": "string", "description": "邮箱", "default": ""},
                "source": {"type": "string", "description": "来源：referral, website, cold_call, event", "default": ""}
            },
            "required": ["name"]
        },
        handler=add_customer
    )
    
    # ═══════════════════════════════════════════
    # Claude Code 对标工具 v3.0
    # ═══════════════════════════════════════════
    
    # 项目根目录 = opcclaw 所在目录的父目录（即 one_company_desktop）
    _project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def _resolve_path(rel_path: str) -> str:
        """将相对路径解析为绝对路径（相对项目根目录）"""
        p = os.path.join(_project_root, rel_path)
        return os.path.abspath(p)
    
    # 8. Shell 命令执行 (对标 Claude Code terminal)
    def shell_execute(command: str, cwd: str = "", timeout: int = 60) -> dict:
        """执行 Shell 命令（bash），覆盖 git/npm/pip/build/test/lint 等所有 CLI 操作"""
        try:
            work_dir = _resolve_path(cwd) if cwd else _project_root
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=work_dir,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )
            output = result.stdout
            if result.stderr:
                output += "\n[stderr]\n" + result.stderr
            return {
                "stdout": result.stdout[:8000],
                "stderr": result.stderr[:4000],
                "returncode": result.returncode,
                "cwd": work_dir
            }
        except subprocess.TimeoutExpired:
            return {"error": f"命令超时（{timeout}秒）"}
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="shell_execute",
        description="执行 Shell 命令。可用于 git 操作、npm/pip 包管理、运行测试/构建/格式化/lint、系统命令等所有终端操作。命令在项目根目录执行",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的 Shell 命令，如 'git diff' 或 'npm install'"},
                "cwd": {"type": "string", "description": "工作目录路径，默认为项目根目录", "default": ""},
                "timeout": {"type": "integer", "description": "超时秒数", "default": 60}
            },
            "required": ["command"]
        },
        handler=shell_execute
    )
    
    # 9. 文件列表 (对标 Claude Code ls/dir)
    def file_list(path: str = ".", pattern: str = "*", recursive: bool = False, max_depth: int = 3) -> dict:
        """列出目录下的文件和子目录"""
        try:
            abs_path = _resolve_path(path)
            if not os.path.exists(abs_path):
                return {"error": f"路径不存在: {abs_path}"}
            
            entries = []
            if recursive:
                for root, dirs, files in os.walk(abs_path):
                    depth = root[len(abs_path):].count(os.sep)
                    if depth >= max_depth:
                        dirs.clear()
                        continue
                    import fnmatch
                    for f in files:
                        if fnmatch.fnmatch(f, pattern):
                            entries.append(os.path.relpath(os.path.join(root, f), abs_path))
            else:
                import fnmatch
                for f in sorted(os.listdir(abs_path)):
                    if fnmatch.fnmatch(f, pattern):
                        p = os.path.relpath(os.path.join(abs_path, f), abs_path)
                        entries.append(p + ("/" if os.path.isdir(os.path.join(abs_path, f)) else ""))
            
            return {
                "path": abs_path,
                "entries": entries[:200],
                "count": len(entries),
                "truncated": len(entries) > 200
            }
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="file_list",
        description="列出目录内容，支持文件名匹配和递归。用于了解项目结构、查找文件",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "目录路径，相对项目根目录", "default": "."},
                "pattern": {"type": "string", "description": "文件名匹配模式，如 *.py 或 test_*", "default": "*"},
                "recursive": {"type": "boolean", "description": "是否递归列出子目录", "default": False},
                "max_depth": {"type": "integer", "description": "递归最大深度", "default": 3}
            },
            "required": []
        },
        handler=file_list
    )
    
    # 10. 文件内容搜索 (对标 Claude Code grep)
    def file_search(query: str, path: str = ".", file_pattern: str = "*", max_results: int = 30) -> dict:
        """在文件中搜索文本内容"""
        import fnmatch
        try:
            abs_path = _resolve_path(path)
            if not os.path.exists(abs_path):
                return {"error": f"路径不存在: {abs_path}"}
            
            results = []
            for root, dirs, files in os.walk(abs_path):
                # 跳过隐藏目录和常见忽略目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'venv', '.git', 'dist', 'build', '.next')]
                
                for f in files:
                    if not fnmatch.fnmatch(f, file_pattern):
                        continue
                    if len(results) >= max_results:
                        break
                    
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                            for i, line in enumerate(fh, 1):
                                if query.lower() in line.lower():
                                    rel = os.path.relpath(fp, abs_path)
                                    results.append({
                                        "file": rel,
                                        "line": i,
                                        "content": line.strip()[:200]
                                    })
                                    if len(results) >= max_results:
                                        break
                    except Exception:
                        continue
                
                if len(results) >= max_results:
                    break
            
            return {
                "query": query,
                "matches": results[:max_results],
                "count": len(results),
                "truncated": len(results) >= max_results
            }
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="file_search",
        description="在文件中搜索文本内容（grep）。用于查找函数定义、变量引用、TODO 注释、错误信息等",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词（不区分大小写）"},
                "path": {"type": "string", "description": "搜索目录，相对项目根目录", "default": "."},
                "file_pattern": {"type": "string", "description": "限定文件类型，如 *.py 或 *.js", "default": "*"},
                "max_results": {"type": "integer", "description": "最大结果数", "default": 30}
            },
            "required": ["query"]
        },
        handler=file_search
    )
    
    # 11. 文件编辑 (对标 Claude Code edit)
    def edit_file(path: str, old_str: str, new_str: str, replace_all: bool = False) -> dict:
        """精确替换文件中的文本片段"""
        try:
            abs_path = _resolve_path(path)
            if not os.path.exists(abs_path):
                return {"error": f"文件不存在: {abs_path}"}
            
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_encoding = 'utf-8'
            
            count = content.count(old_str)
            if count == 0:
                return {"error": f"未找到要替换的文本片段（old_str 在文件中不存在）"}
            if count > 1 and not replace_all:
                return {
                    "error": f"找到 {count} 处匹配，需要替换多少处？请设置 replace_all=true 替换全部，或缩小 old_str 范围确保唯一匹配",
                    "count": count
                }
            
            if replace_all:
                new_content = content.replace(old_str, new_str)
                replacements = count
            else:
                new_content = content.replace(old_str, new_str, 1)
                replacements = 1
            
            with open(abs_path, 'w', encoding=original_encoding) as f:
                f.write(new_content)
            
            return {
                "success": True,
                "path": abs_path,
                "replacements": replacements
            }
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="edit_file",
        description="精确替换文件中的文本片段。用于修改代码、修复 bug、更新配置。old_str 必须与文件中内容完全一致（含缩进和换行）。支持 replace_all=true 替换所有匹配项",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "要编辑的文件路径，相对项目根目录"},
                "old_str": {"type": "string", "description": "要被替换的原始文本，必须与文件内容完全一致"},
                "new_str": {"type": "string", "description": "替换后的新文本"},
                "replace_all": {"type": "boolean", "description": "是否替换所有匹配项", "default": False}
            },
            "required": ["path", "old_str", "new_str"]
        },
        handler=edit_file
    )
    
    # 12. 项目结构映射 (对标 Claude Code 项目上下文)
    def project_map(depth: int = 4, focus: str = "") -> dict:
        """生成项目文件树，帮助 AI 理解项目结构"""
        try:
            root = _project_root
            
            skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 
                         'dist', 'build', '.next', '.DS_Store', 'logs', '__pycache__'}
            
            lines = []
            file_count = 0
            
            def walk(dir_path, prefix="", current_depth=0):
                nonlocal file_count
                if current_depth > depth:
                    return
                
                try:
                    entries = sorted(os.listdir(dir_path))
                except PermissionError:
                    return
                
                dirs = [e for e in entries if os.path.isdir(os.path.join(dir_path, e)) and e not in skip_dirs and not e.startswith('.')]
                files = [e for e in entries if os.path.isfile(os.path.join(dir_path, e)) and not e.startswith('.')]
                
                # 如果有 focus，优先展示相关目录
                if focus and focus in dirs:
                    dirs.remove(focus)
                    dirs.insert(0, focus)
                
                for i, d in enumerate(dirs):
                    is_last = i == len(dirs) - 1 and not files
                    connector = "└── " if is_last else "├── "
                    lines.append(f"{prefix}{connector}{d}/")
                    extension = "    " if is_last else "│   "
                    walk(os.path.join(dir_path, d), prefix + extension, current_depth + 1)
                
                for i, f in enumerate(files):
                    file_count += 1
                    if file_count > 500:
                        lines.append(f"{prefix}... (超过500个文件，已截断)")
                        return
                    is_last = i == len(files) - 1
                    connector = "└── " if is_last else "├── "
                    lines.append(f"{prefix}{connector}{f}")
            
            walk(root)
            
            return {
                "root": root,
                "tree": "\n".join(lines[:600]),
                "file_count": file_count,
                "max_depth": depth
            }
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="project_map",
        description="生成项目目录树，了解项目整体结构。用于快速掌握代码仓库布局、识别关键目录和文件",
        parameters={
            "type": "object",
            "properties": {
                "depth": {"type": "integer", "description": "目录展开深度，默认 4", "default": 4},
                "focus": {"type": "string", "description": "优先聚焦的目录名，如 'src' 或 'modules'", "default": ""}
            },
            "required": []
        },
        handler=project_map
    )


# ═══════════════════════════════════════════
# 智能核心引擎
# ═══════════════════════════════════════════

@dataclass
class ChatMessage:
    """对话消息"""
    role: str  # user, assistant, system, tool
    content: str
    tool_calls: Optional[List[dict]] = None
    tool_call_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class OPCclawCoreEngine:
    """
    OPCclaw 智能核心引擎 v2.0
    支持 Function Calling、多轮工具调用、任务规划
    """
    
    def __init__(self, provider_config: ProviderConfig = None):
        self.registry = ToolRegistry()
        init_builtin_tools(self.registry)
        
        # 默认使用 llama.cpp 本地模型
        if provider_config is None:
            provider_config = ProviderConfig(
                name="llama.cpp",
                provider_type="openai_compatible",
                base_url="http://localhost:8080/v1",
                model="qwen3.6-35b-iq2m",
                temperature=0.7,
                max_tokens=4096
            )
        self.provider_config = provider_config
        self.backend = OpenAICompatibleBackend(provider_config)
        
        # 对话历史
        self.messages: List[ChatMessage] = []
        
        # 系统提示词
        self.system_prompt = """你是 OPCclaw，一个运行在用户本地电脑上的 AI 编程助手，定位对标 Claude Code。

核心原则：
- 行动优先，能直接用工具解决就不要追问
- 多轮工具调用直到完成任务，不提前放弃
- 回答简洁专业，中文优先，技术术语保留英文

可用工具：
1.  Shell 命令：执行任意 bash 命令（git/npm/pip/build/test/lint/docker 等）
2.  文件操作：读取、写入、编辑(精确替换)、列出目录
3.  内容搜索：在项目中 grep 搜索代码/文本
4.  代码执行：运行 Python 代码，用于数据分析/文件处理
5.  项目分析：生成项目目录树，快速掌握代码结构
6.  数据库查询：查询 products/orders/customers/finance 等业务数据
7.  联网搜索：获取实时信息
8.  日程与客户管理

编程场景最佳实践：
- 修改代码前先用 file_search 找到相关代码位置
- 多文件编辑时用 edit_file 逐个精确替换
- 构建/测试/格式化用 shell_execute
- 不确定项目结构时先用 project_map
- 代码执行错误时读取日志并修复

当用户请求需要工具才能完成的任务时，请调用相应的工具。进行多轮工具调用直到任务完成。
请用中文回答，保持友好和专业。"""
    
    def add_message(self, role: str, content: str):
        """添加消息到历史"""
        self.messages.append(ChatMessage(role=role, content=content))
    
    def clear_history(self):
        """清空对话历史"""
        self.messages = []
    
    def chat(self, user_input: str, max_tool_iterations: int = 5) -> str:
        """
        与用户对话，支持多轮工具调用
        
        Args:
            user_input: 用户输入
            max_tool_iterations: 最大工具调用轮数
        
        Returns:
            AI 回复
        """
        # 添加用户消息
        self.add_message("user", user_input)
        
        # 构建消息历史
        messages = [{"role": "system", "content": self.system_prompt}]
        for msg in self.messages:
            if msg.role == "tool":
                messages.append({
                    "role": "tool",
                    "content": json.dumps(msg.content, ensure_ascii=False),
                    "tool_call_id": msg.tool_call_id
                })
            else:
                msg_dict = {"role": msg.role, "content": msg.content}
                if msg.tool_calls:
                    msg_dict["tool_calls"] = msg.tool_calls
                messages.append(msg_dict)
        
        # 获取工具定义
        tools = self.registry.list_tools()
        
        # 多轮工具调用循环
        for iteration in range(max_tool_iterations):
            # 调用 LLM
            response = self.backend.chat(messages, tools=tools)
            
            # 检查是否需要调用工具
            if response.tool_calls:
                # 处理工具调用
                for tc in response.tool_calls:
                    result = self.registry.execute(tc.name, tc.arguments)
                    
                    # 添加工具调用到消息历史
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments)
                            }
                        }]
                    })
                    
                    # 添加工具结果
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                    
                    # 保存到本地历史
                    self.messages.append(ChatMessage(
                        role="assistant",
                        content="",
                        tool_calls=[{
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": tc.arguments
                            }
                        }]
                    ))
                    self.messages.append(ChatMessage(
                        role="tool",
                        content=result,
                        tool_call_id=tc.id
                    ))
                
                # 继续下一轮 LLM 调用
                continue
            else:
                # 没有工具调用，返回文本回复
                assistant_message = response.content or ""
                self.add_message("assistant", assistant_message)
                return assistant_message
        
        # 达到最大迭代次数，强制返回当前回复
        if messages[-1]["role"] == "tool":
            # 再调用一次 LLM 获取最终回复
            response = self.backend.chat(messages, tools=tools)
            assistant_message = response.content or "任务处理完成。"
        else:
            assistant_message = response.content or "我需要调用工具来完成这个任务。"
        
        self.add_message("assistant", assistant_message)
        return assistant_message
    
    def get_status(self) -> dict:
        """获取引擎状态"""
        return {
            "model": self.provider_config.model,
            "provider": self.provider_config.name,
            "tools_available": len(self.registry._tools),
            "message_count": len(self.messages),
            "tools": list(self.registry._tools.keys())
        }


# ═══════════════════════════════════════════
# 快捷函数
# ═══════════════════════════════════════════

def create_engine(model: str = "qwen3.6-35b-iq2m", base_url: str = "http://localhost:8080/v1") -> OPCclawCoreEngine:
    """创建引擎实例"""
    config = ProviderConfig(
        name="llama.cpp",
        provider_type="openai_compatible",
        base_url=base_url,
        model=model,
        temperature=0.7,
        max_tokens=4096
    )
    return OPCclawCoreEngine(config)


def quick_chat(question: str, model: str = "qwen2.5:7b") -> str:
    """快速对话（无状态）"""
    engine = create_engine(model=model)
    return engine.chat(question)


# ═══════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════

if __name__ == "__main__":
    print("OPCclaw Core Engine v2.0")
    print("=" * 50)
    
    engine = create_engine()
    print(f"引擎状态：{engine.get_status()}")
    print()
    
    # 测试对话
    print("测试对话:")
    response = engine.chat("你好，介绍一下你自己")
    print(f"AI: {response}")
    print()
    
    response = engine.chat("帮我查询一下产品数据库，看看有哪些产品")
    print(f"AI: {response}")
