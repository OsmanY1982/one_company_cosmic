# `tools/builtin/git_tools.py`

> 路径：`tools/builtin/git_tools.py` | 行数：288


---


```python
# -*- coding: utf-8 -*-
"""
Git 工具集 — Agent 可直接调用的 Git 操作

安全设计:
  - 所有写操作默认 dry_run 预览
  - commit/push/merge 需要 explicit confirm
  - 自动记录操作日志
"""

import os
from opcclaw.core.tool_registry import ToolDefinition
from opcclaw.core.git_ops import GitOps


# 项目根目录（自动发现 .git）
def _find_git_root() -> str:
    """向上查找 .git 目录"""
    current = os.getcwd()
    for _ in range(10):
        if os.path.isdir(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return os.getcwd()


def register_git_tools(registry) -> None:
    """注册所有 Git 工具"""

    def _get_git() -> GitOps:
        root = _find_git_root()
        return GitOps(root)

    # ── git_status ──
    def git_status() -> dict:
        """查看 Git 仓库状态"""
        try:
            g = _get_git()
            s = g.status()
            return {
                "branch": s.branch,
                "ahead": s.ahead,
                "behind": s.behind,
                "is_clean": s.is_clean,
                "has_conflicts": s.has_conflicts,
                "staged": s.staged,
                "modified": s.modified,
                "untracked": s.untracked,
                "deleted": s.deleted,
                "renamed": s.renamed,
                "repo": g.get_repo_name(),
            }
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(ToolDefinition(
        name="git_status",
        description="查看 Git 仓库状态：当前分支、已暂存/已修改/未跟踪文件、冲突状态",
        parameters={"type": "object", "properties": {}, "required": []},
        handler=git_status,
        category="git",
    ))

    # ── git_diff ──
    def git_diff(file_path: str = "", staged: bool = False) -> dict:
        """查看文件差异"""
        try:
            g = _get_git()
            diff = g.diff(file_path=file_path, staged=staged)
            return {"diff": diff}
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(ToolDefinition(
        name="git_diff",
        description="查看 Git 差异。不传 file_path 查看所有变更，传 staged=true 查看暂存区差异",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径（可选）", "default": ""},
                "staged": {"type": "boolean", "description": "是否查看暂存区", "default": False},
            },
            "required": [],
        },
        handler=git_diff,
        category="git",
    ))

    # ── git_log ──
    def git_log(count: int = 15, file_path: str = "") -> dict:
        """查看提交历史"""
        try:
            g = _get_git()
            commits = g.log(max_count=count, file_path=file_path)
            return {
                "commits": [
                    {"hash": c.short_hash, "author": c.author, "date": c.date, "message": c.message}
                    for c in commits
                ],
            }
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(ToolDefinition(
        name="git_log",
        description="查看 Git 提交历史。返回最近 N 条提交的 hash/作者/日期/消息",
        parameters={
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "返回条数", "default": 15},
                "file_path": {"type": "string", "description": "限定文件（可选）", "default": ""},
            },
            "required": [],
        },
        handler=git_log,
        category="git",
    ))

    # ── git_stage ──
    def git_stage(files: list, dry_run: bool = True) -> dict:
        """暂存文件"""
        try:
            g = _get_git()
            result = g.stage(files, dry_run=dry_run)
            return {"success": result.success, "output": result.output, "error": result.error, "dry_run": result.dry_run}
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(ToolDefinition(
        name="git_stage",
        description="暂存文件到 Git 暂存区。默认 dry_run 预览，设置 dry_run=false 执行",
        parameters={
            "type": "object",
            "properties": {
                "files": {"type": "array", "items": {"type": "string"}, "description": "文件路径列表"},
                "dry_run": {"type": "boolean", "description": "预览模式（默认 true）", "default": True},
            },
            "required": ["files"],
        },
        handler=git_stage,
        category="git",
    ))

    # ── git_commit ──
    def git_commit(message: str, dry_run: bool = True) -> dict:
        """提交变更"""
        try:
            g = _get_git()
            result = g.commit(message, dry_run=dry_run)
            return {"success": result.success, "output": result.output, "error": result.error, "dry_run": result.dry_run}
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(ToolDefinition(
        name="git_commit",
        description="提交暂存区变更。默认 dry_run 预览，设置 dry_run=false 执行",
        parameters={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "提交信息（如 'feat: add login page'）"},
                "dry_run": {"type": "boolean", "description": "预览模式（默认 true）", "default": True},
            },
            "required": ["message"],
        },
        handler=git_commit,
        category="git",
    ))

    # ── git_branch ──
    def git_branch(action: str = "list", name: str = "", dry_run: bool = True) -> dict:
        """分支管理"""
        try:
            g = _get_git()
            if action == "list":
                branches = g.branch_list()
                return {"branches": branches}
            elif action == "create":
                result = g.branch_create(name, dry_run=dry_run)
                return {"success": result.success, "output": result.output, "error": result.error, "dry_run": result.dry_run}
            elif action == "switch":
                result = g.checkout(name, dry_run=dry_run)
                return {"success": result.success, "output": result.output, "error": result.error, "dry_run": result.dry_run}
            else:
                return {"error": f"Unknown action: {action}. Use list/create/switch"}
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(ToolDefinition(
        name="git_branch",
        description="Git 分支管理：list（列出）/ create（创建）/ switch（切换）",
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "操作：list/create/switch", "default": "list"},
                "name": {"type": "string", "description": "分支名（create/switch 时使用）", "default": ""},
                "dry_run": {"type": "boolean", "description": "预览模式（默认 true，create/switch 时适用）", "default": True},
            },
            "required": [],
        },
        handler=git_branch,
        category="git",
    ))

    # ── git_stash ──
    def git_stash(action: str = "push", message: str = "") -> dict:
        """暂存/恢复工作区"""
        try:
            g = _get_git()
            if action == "push":
                result = g.stash_push(message)
                return {"success": result.success, "output": result.output, "error": result.error}
            elif action == "pop":
                result = g.stash_pop()
                return {"success": result.success, "output": result.output, "error": result.error}
            elif action == "list":
                return {"stashes": g.stash_list()}
            else:
                return {"error": f"Unknown action: {action}. Use push/pop/list"}
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(ToolDefinition(
        name="git_stash",
        description="Git stash：push（暂存当前工作）/ pop（恢复）/ list（列出）",
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "push/pop/list", "default": "push"},
                "message": {"type": "string", "description": "stash 备注（push 时使用）", "default": ""},
            },
            "required": [],
        },
        handler=git_stash,
        category="git",
    ))

    # ── git_restore ──
    def git_restore(files: list, staged: bool = False, dry_run: bool = True) -> dict:
        """恢复文件"""
        try:
            g = _get_git()
            result = g.restore(files, staged=staged, dry_run=dry_run)
            return {"success": result.success, "output": result.output, "error": result.error, "dry_run": result.dry_run}
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(ToolDefinition(
        name="git_restore",
        description="恢复文件到最近提交状态。默认 dry_run 预览。staged=true 取消暂存",
        parameters={
            "type": "object",
            "properties": {
                "files": {"type": "array", "items": {"type": "string"}, "description": "文件路径列表"},
                "staged": {"type": "boolean", "description": "取消暂存（而非恢复工作区）", "default": False},
                "dry_run": {"type": "boolean", "description": "预览模式（默认 true）", "default": True},
            },
            "required": ["files"],
        },
        handler=git_restore,
        category="git",
    ))

    # ── git_pull ──
    def git_pull(dry_run: bool = True) -> dict:
        """拉取远程更新"""
        try:
            g = _get_git()
            result = g.pull(dry_run=dry_run)
            return {"success": result.success, "output": result.output, "error": result.error, "dry_run": result.dry_run}
        except Exception as e:
            return {"error": str(e)}

    registry.add_tool(ToolDefinition(
        name="git_pull",
        description="拉取远程更新（git pull --rebase）。默认 dry_run 预览",
        parameters={
            "type": "object",
            "properties": {
                "dry_run": {"type": "boolean", "description": "预览模式（默认 true）", "default": True},
            },
            "required": [],
        },
        handler=git_pull,
        category="git",
    ))

```
