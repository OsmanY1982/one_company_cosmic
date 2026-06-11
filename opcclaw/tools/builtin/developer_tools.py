# -*- coding: utf-8 -*-
"""
OPCclaw 开发者工具 — Claude Code 对标工具集

shell_execute / file_list / file_search / edit_file / project_map
让 OPCclaw 具备 Terminal + Grep + Edit + LS + Project Map 的完整开发能力
"""

import os
import subprocess
from opcclaw.core.tool_registry import ToolDefinition


def register_developer_tools(registry) -> None:
    """将所有开发者工具注册到给定的 ToolRegistry"""

    # ── 项目根目录 ──
    _project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    def _resolve_path(rel_path: str) -> str:
        if os.path.isabs(rel_path):
            return rel_path
        return os.path.abspath(os.path.join(_project_root, rel_path))

    # ── 1. Shell 命令 ──
    def shell_execute(command: str, cwd: str = "", timeout: int = 60) -> dict:
        try:
            work_dir = _resolve_path(cwd) if cwd else _project_root
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=work_dir,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            return {
                "stdout": result.stdout[:8000],
                "stderr": result.stderr[:4000],
                "returncode": result.returncode,
                "cwd": work_dir,
            }
        except subprocess.TimeoutExpired:
            return {"error": f"命令超时（{timeout}秒）"}
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(
        ToolDefinition(
            name="shell_execute",
            description="执行 Shell 命令。可用于 git 操作、npm/pip 包管理、运行测试/构建/格式化/lint、系统命令等所有终端操作。命令在项目根目录执行",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的 Shell 命令"},
                    "cwd": {"type": "string", "description": "工作目录", "default": ""},
                    "timeout": {"type": "integer", "description": "超时秒数", "default": 60},
                },
                "required": ["command"],
            },
            handler=shell_execute,
        ),
        category="developer",
    )

    # ── 2. 文件列表 ──
    def file_list(path: str = ".", pattern: str = "*", recursive: bool = False, max_depth: int = 3) -> dict:
        import fnmatch as _fnm

        try:
            abs_path = _resolve_path(path)
            if not os.path.exists(abs_path):
                return {"error": f"路径不存在: {abs_path}"}
            entries = []
            if recursive:
                for root, dirs, files in os.walk(abs_path):
                    depth = root[len(abs_path) :].count(os.sep)
                    if depth >= max_depth:
                        dirs.clear()
                        continue
                    for f in files:
                        if _fnm.fnmatch(f, pattern):
                            entries.append(os.path.relpath(os.path.join(root, f), abs_path))
            else:
                for f in sorted(os.listdir(abs_path)):
                    if _fnm.fnmatch(f, pattern):
                        p = os.path.relpath(os.path.join(abs_path, f), abs_path)
                        entries.append(p + ("/" if os.path.isdir(os.path.join(abs_path, f)) else ""))
            return {"path": abs_path, "entries": entries[:200], "count": len(entries), "truncated": len(entries) > 200}
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(
        ToolDefinition(
            name="file_list",
            description="列出目录内容，支持文件名匹配和递归。用于了解项目结构、查找文件",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "目录路径", "default": "."},
                    "pattern": {"type": "string", "description": "文件名匹配模式", "default": "*"},
                    "recursive": {"type": "boolean", "description": "是否递归", "default": False},
                    "max_depth": {"type": "integer", "description": "递归最大深度", "default": 3},
                },
            },
            handler=file_list,
        ),
        category="developer",
    )

    # ── 3. 文件搜索 ──
    def file_search(query: str, path: str = ".", file_pattern: str = "*", max_results: int = 30) -> dict:
        import fnmatch as _fnm

        try:
            abs_path = _resolve_path(path)
            if not os.path.exists(abs_path):
                return {"error": f"路径不存在: {abs_path}"}
            results = []
            skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".next"}
            for root, dirs, files in os.walk(abs_path):
                dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
                for f in files:
                    if not _fnm.fnmatch(f, file_pattern):
                        continue
                    if len(results) >= max_results:
                        break
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                            for i, line in enumerate(fh, 1):
                                if query.lower() in line.lower():
                                    results.append(
                                        {"file": os.path.relpath(fp, abs_path), "line": i, "content": line.strip()[:200]}
                                    )
                                    if len(results) >= max_results:
                                        break
                    except Exception:
                        continue
                if len(results) >= max_results:
                    break
            return {"query": query, "matches": results[:max_results], "count": len(results), "truncated": len(results) >= max_results}
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(
        ToolDefinition(
            name="file_search",
            description="在文件中搜索文本内容。用于查找函数定义、变量引用、TODO 注释、错误信息等",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "path": {"type": "string", "description": "搜索目录", "default": "."},
                    "file_pattern": {"type": "string", "description": "限定文件类型", "default": "*"},
                    "max_results": {"type": "integer", "description": "最大结果数", "default": 30},
                },
                "required": ["query"],
            },
            handler=file_search,
        ),
        category="developer",
    )

    # ── 4. 文件编辑 ──
    def edit_file(path: str, old_str: str, new_str: str, replace_all: bool = False) -> dict:
        try:
            abs_path = _resolve_path(path)
            if not os.path.exists(abs_path):
                return {"error": f"文件不存在: {abs_path}"}
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
            count = content.count(old_str)
            if count == 0:
                return {"error": "未找到要替换的文本片段（old_str 在文件中不存在）"}
            if count > 1 and not replace_all:
                return {
                    "error": f"找到 {count} 处匹配，需要替换多少处？请设置 replace_all=true 替换全部，或缩小 old_str 范围确保唯一匹配",
                    "count": count,
                }
            new_content = content.replace(old_str, new_str) if replace_all else content.replace(old_str, new_str, 1)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return {"success": True, "path": abs_path, "replacements": count if replace_all else 1}
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(
        ToolDefinition(
            name="edit_file",
            description="精确替换文件中的文本片段。old_str 必须与文件中内容完全一致（含缩进和换行）",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "old_str": {"type": "string", "description": "要被替换的原始文本"},
                    "new_str": {"type": "string", "description": "替换后的新文本"},
                    "replace_all": {"type": "boolean", "description": "是否替换所有匹配项", "default": False},
                },
                "required": ["path", "old_str", "new_str"],
            },
            handler=edit_file,
        ),
        category="developer",
    )

    # ── 5. 项目结构映射 ──
    def project_map(depth: int = 4, focus: str = "") -> dict:
        try:
            root = _project_root
            skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".next", ".DS_Store", "logs"}
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
                dirs = [e for e in entries if os.path.isdir(os.path.join(dir_path, e)) and e not in skip_dirs and not e.startswith(".")]
                files = [e for e in entries if os.path.isfile(os.path.join(dir_path, e)) and not e.startswith(".")]
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
            return {"root": root, "tree": "\n".join(lines[:600]), "file_count": file_count, "max_depth": depth}
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(
        ToolDefinition(
            name="project_map",
            description="生成项目目录树，了解项目整体结构。用于快速掌握代码仓库布局",
            parameters={
                "type": "object",
                "properties": {
                    "depth": {"type": "integer", "description": "目录展开深度", "default": 4},
                    "focus": {"type": "string", "description": "优先聚焦的目录名", "default": ""},
                },
            },
            handler=project_map,
        ),
        category="developer",
    )
