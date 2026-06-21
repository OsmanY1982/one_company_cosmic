"""
iqra 可视化工作流编辑器 — Web UI 路由注册

基于 Python 内置 http.server，零第三方依赖。
- GET  /workflow           — 渲染编辑器页面
- POST /api/workflow/save  — 保存工作流 JSON
- GET  /api/workflow/load  — 加载工作流
- POST /api/workflow/compile — 编译为 Python 代码
- POST /api/workflow/run   — 在沙箱中执行已编译代码
"""

import json
import os
import sys
import subprocess
import tempfile
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, Callable

from .compiler import compile_workflow, validate_workflow
from .templates import list_templates, get_template

# ── 编辑器 HTML 路径 ──
_EDITOR_HTML = os.path.join(os.path.dirname(__file__), "editor.html")

# ── 工作流持久化路径 ──  
_SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                          "data", "workflows")
os.makedirs(_SAVE_DIR, exist_ok=True)

# ── 全局状态 ──
_server: Optional[HTTPServer] = None
_server_thread: Optional[threading.Thread] = None


# ═══════════════════════════════════════════
# HTTP 请求处理器
# ═══════════════════════════════════════════

class WorkflowHandler(BaseHTTPRequestHandler):
    """工作流编辑器 HTTP 请求处理器"""

    def log_message(self, format, *args):
        """抑制默认日志"""
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/workflow" or path == "/workflow/":
            self._serve_editor()
        elif path == "/api/workflow/load":
            self._handle_load(params)
        elif path == "/api/workflow/templates":
            self._handle_list_templates()
        elif path == "/api/workflow/template":
            self._handle_get_template(params)
        else:
            self._json_response({"error": "Not Found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}

        if path == "/api/workflow/save":
            self._handle_save(data)
        elif path == "/api/workflow/compile":
            self._handle_compile(data)
        elif path == "/api/workflow/run":
            self._handle_run(data)
        else:
            self._json_response({"error": "Not Found"}, 404)

    def do_OPTIONS(self):
        """CORS preflight"""
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    # ── 响应工具 ──

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json_response(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    # ── 页面渲染 ──

    def _serve_editor(self):
        if not os.path.exists(_EDITOR_HTML):
            self._json_response({"error": "editor.html not found"}, 500)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self._cors_headers()
        self.end_headers()
        with open(_EDITOR_HTML, "rb") as f:
            self.wfile.write(f.read())

    # ── API: 保存 ──

    def _handle_save(self, data: dict):
        workflow_name = data.get("name", "untitled")
        filepath = os.path.join(_SAVE_DIR, f"{workflow_name}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._json_response({"status": "ok", "path": filepath})
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    # ── API: 加载 ──

    def _handle_load(self, params: dict):
        name = params.get("name", ["untitled"])[0]
        filepath = os.path.join(_SAVE_DIR, f"{name}.json")
        if not os.path.exists(filepath):
            self._json_response({"error": f"工作流 '{name}' 不存在"}, 404)
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._json_response(data)
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    # ── API: 模板列表 ──

    def _handle_list_templates(self):
        templates = list_templates()
        self._json_response({"templates": templates})

    # ── API: 获取模板 ──

    def _handle_get_template(self, params: dict):
        template_id = params.get("id", [None])[0]
        if not template_id:
            self._json_response({"error": "缺少 id 参数"}, 400)
            return
        try:
            template = get_template(template_id)
            self._json_response(template)
        except KeyError as e:
            self._json_response({"error": str(e)}, 404)

    # ── API: 编译 ──

    def _handle_compile(self, data: dict):
        valid, err = validate_workflow(data)
        if not valid:
            self._json_response({"error": err}, 400)
            return
        try:
            code = compile_workflow(data)
            # 验证语法
            compile(code, "<workflow>", "exec")
            self._json_response({"status": "ok", "code": code})
        except SyntaxError as e:
            self._json_response({"error": f"语法错误: {e}"}, 400)
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    # ── API: 运行 ──

    def _handle_run(self, data: dict):
        code = data.get("code", "")
        if not code:
            self._json_response({"error": "没有代码可执行"}, 400)
            return
        try:
            # 写入临时文件
            tmpdir = tempfile.gettempdir()
            script_path = os.path.join(tmpdir, "_iqra_workflow_run.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            # 在子进程中执行（沙箱）
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.dirname(__file__))))
            )
            os.unlink(script_path)
            self._json_response({
                "status": "ok",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            })
        except subprocess.TimeoutExpired:
            self._json_response({"error": "执行超时（60s）"}, 408)
        except Exception as e:
            self._json_response({"error": str(e)}, 500)


# ═══════════════════════════════════════════
# 服务器启动/管理
# ═══════════════════════════════════════════

def start_server(port: int = 8550) -> str:
    """启动工作流编辑器 HTTP 服务器（后台线程）。

    Args:
        port: 监听端口，默认 8550

    Returns:
        URL 字符串，如 "http://localhost:8550/workflow"
    """
    global _server, _server_thread

    if _server is not None:
        return f"http://localhost:{port}/workflow"

    _server = HTTPServer(("127.0.0.1", port), WorkflowHandler)
    _server_thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _server_thread.start()

    return f"http://localhost:{port}/workflow"


def stop_server():
    """停止工作流编辑器服务器"""
    global _server, _server_thread
    if _server is not None:
        _server.shutdown()
        _server = None
        _server_thread = None


def get_server_url(port: int = 8550) -> str:
    return f"http://localhost:{port}/workflow"
