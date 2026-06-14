# `opcclaw/plugins/code_executor/__init__.py`

> 路径：`opcclaw/plugins/code_executor/__init__.py` | 行数：200


---


```python
"""
代码执行插件
支持多种编程语言的代码执行和验证
"""

import os
import subprocess
import tempfile
import json
from typing import Dict, Any, Optional
from pathlib import Path


class CodeExecutorPlugin:
    """代码执行插件"""
    
    SUPPORTED_LANGUAGES = {
        "python": {
            "extension": ".py",
            "command": "python",
            "timeout": 30
        },
        "javascript": {
            "extension": ".js", 
            "command": "node",
            "timeout": 30
        },
        "bash": {
            "extension": ".sh",
            "command": "bash",
            "timeout": 15
        },
        "powershell": {
            "extension": ".ps1",
            "command": "powershell",
            "timeout": 30
        }
    }
    
    def __init__(self):
        self.temp_dir = os.path.expanduser("~/.opcclaw/code_exec")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.execution_history = []
    
    def execute(self, code: str, language: str = "python", 
                timeout: int = None) -> Dict[str, Any]:
        """
        执行代码
        
        Args:
            code: 代码内容
            language: 编程语言
            timeout: 超时时间（秒）
        
        Returns:
            执行结果
        """
        if language not in self.SUPPORTED_LANGUAGES:
            return {
                "success": False, 
                "error": f"不支持的语言: {language}. 支持: {list(self.SUPPORTED_LANGUAGES.keys())}"
            }
        
        lang_config = self.SUPPORTED_LANGUAGES[language]
        timeout = timeout or lang_config["timeout"]
        
        # 创建临时文件
        temp_file = os.path.join(
            self.temp_dir, 
            f"exec_{language}_{os.urandom(4).hex()}{lang_config['extension']}"
        )
        
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(code)
            
            # 执行代码
            cmd = [lang_config["command"], temp_file]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.temp_dir
            )
            
            execution_result = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "language": language
            }
            
            # 记录历史
            self.execution_history.append({
                "code": code[:200],
                "language": language,
                "result": execution_result
            })
            
            return execution_result
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"代码执行超时（>{timeout}秒）",
                "stdout": "",
                "stderr": ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": ""
            }
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    def validate_syntax(self, code: str, language: str = "python") -> Dict[str, Any]:
        """验证代码语法"""
        if language == "python":
            return self._validate_python(code)
        elif language == "javascript":
            return self._validate_javascript(code)
        else:
            return {"valid": True, "message": "该语言暂不支持语法检查"}
    
    def _validate_python(self, code: str) -> Dict[str, Any]:
        """验证 Python 语法"""
        import ast
        try:
            ast.parse(code)
            return {"valid": True, "message": "语法正确"}
        except SyntaxError as e:
            return {
                "valid": False,
                "message": f"语法错误 (行 {e.lineno}): {e.msg}"
            }
    
    def _validate_javascript(self, code: str) -> Dict[str, Any]:
        """验证 JavaScript 语法"""
        try:
            # 使用 node --check
            result = subprocess.run(
                ["node", "--check", "-"],
                input=code,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return {"valid": True, "message": "语法正确"}
            else:
                return {"valid": False, "message": result.stderr}
        except Exception as e:
            return {"valid": False, "message": str(e)}
    
    def install_package(self, package: str, language: str = "python") -> Dict[str, Any]:
        """安装依赖包"""
        try:
            if language == "python":
                result = subprocess.run(
                    ["pip", "install", package],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
            elif language == "javascript":
                result = subprocess.run(
                    ["npm", "install", package],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=self.temp_dir
                )
            else:
                return {"success": False, "error": f"不支持 {language} 的包管理"}
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


def initialize(plugin_manager):
    """插件初始化"""
    plugin = CodeExecutorPlugin()
    plugin_manager.code_executor = plugin
    print("[CodeExecutor] Plugin loaded")

```
