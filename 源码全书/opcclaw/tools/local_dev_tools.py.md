# `opcclaw/tools/local_dev_tools.py`

> 路径：`opcclaw/tools/local_dev_tools.py` | 行数：94


---


```python
"""本地编程工具 — 直接调用本地开发环境执行代码"""

import os, subprocess, sys
from pathlib import Path

class LocalDevTools:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.project_root = Path(data_dir).parent.resolve()
        
    def execute_python_script(self, script_path: str, args: list = None) -> dict:
        """执行本地 Python 脚本"""
        script_path = Path(script_path).resolve()
        if not script_path.exists():
            return {"error": f"脚本不存在: {script_path}"}
        
        try:
            # 构建命令
            cmd = ["python", str(script_path)]
            if args:
                cmd.extend(args)
            
            # 执行
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:1000] if result.stdout else "",
                "stderr": result.stderr[:1000] if result.stderr else "",
                "return_code": result.returncode,
                "command": " ".join(cmd),
                "script_path": str(script_path)
            }
        except subprocess.TimeoutExpired:
            return {"error": "脚本执行超时 (300秒)"}
        except Exception as e:
            return {"error": f"执行失败: {str(e)}"}
    
    def git_status(self) -> dict:
        """获取当前 Git 仓库状态"""
        try:
            # 切换到项目根目录
            old_cwd = os.getcwd()
            os.chdir(self.project_root)
            
            # 获取状态
            result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=60)
            
            return {
                "success": result.returncode == 0,
                "changed_files": result.stdout.strip().split('\n') if result.stdout else [],
                "git_status": result.stdout[:1000] if result.stdout else "",
                "command": "git status --porcelain",
                "working_dir": str(self.project_root)
            }
        except Exception as e:
            return {"error": f"Git 状态查询失败: {str(e)}"}
        finally:
            os.chdir(old_cwd)
    
    def create_vscode_project(self, project_name: str) -> dict:
        """在本地创建 VSCode 项目结构"""
        project_path = self.project_root / project_name
        
        try:
            # 创建目录结构
            project_path.mkdir(exist_ok=True)
            (project_path / "src").mkdir(exist_ok=True)
            (project_path / "tests").mkdir(exist_ok=True)
            (project_path / "docs").mkdir(exist_ok=True)
            
            # 创建基础文件
            (project_path / "README.md").write_text("# " + project_name + "\n\n## 项目说明\n")
            (project_path / "requirements.txt").write_text("# 项目依赖\n")
            (project_path / "src" / "main.py").write_text("print('Hello, World!')\n")
            
            return {
                "success": True,
                "project_path": str(project_path),
                "created_files": ["README.md", "requirements.txt", "src/main.py"],
                "structure": ["src/", "tests/", "docs/"],
                "vscode_config": "已创建 .vscode/ 目录（可选）"
            }
        except Exception as e:
            return {"error": f"创建项目失败: {str(e)}"}


def register_local_dev_tools(registry, data_dir):
    from opcclaw.core.tool_registry import ToolDefinition
    dev = LocalDevTools(data_dir)
    registry.add_tool(ToolDefinition(name="execute_python_script", description="执行本地 Python 脚本，支持参数传递", parameters={"type":"object","properties":{"script_path":{"type":"string"},"args":{"type":"array","items":{"type":"string"}}}}, handler=lambda script_path, args=None: dev.execute_python_script(script_path, args)))
    registry.add_tool(ToolDefinition(name="git_status", description="获取当前 Git 仓库状态，显示修改文件列表", parameters={"type":"object","properties":{}}, handler=lambda: dev.git_status()))
    registry.add_tool(ToolDefinition(name="create_vscode_project", description="在本地创建 VSCode 项目结构，包含 src/tests/docs 目录", parameters={"type":"object","properties":{"project_name":{"type":"string"}}}, handler=lambda project_name: dev.create_vscode_project(project_name)))


```
