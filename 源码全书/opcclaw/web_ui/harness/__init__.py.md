# `opcclaw/web_ui/harness/__init__.py`

> 路径：`opcclaw/web_ui/harness/__init__.py` | 行数：346


---


```python
"""
Harness Agent 设计器 — Web UI / API 路由注册

基于 Python 内置 http.server，零第三方依赖。
- GET  /harness                     — 渲染设计器页面
- GET  /api/harness/agents          — 列出所有 Agent
- GET  /api/harness/agent/<id>      — 获取单个 Agent 配置
- PUT  /api/harness/agent/<id>      — 保存/更新 Agent 配置
- DELETE /api/harness/agent/<id>    — 删除 Agent
- POST /api/harness/agent/<id>/clone   — 克隆 Agent
- PUT  /api/harness/agent/<id>/apply   — 应用 Agent 配置
- GET  /api/harness/tools           — 列出可用工具
- GET  /api/harness/skills          — 列出可用技能
"""

import json
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from typing import Optional

# ── 设计器 HTML 路径 ──
_DESIGNER_HTML = os.path.join(os.path.dirname(__file__), "designer.html")

# ── 全局状态 ──
_server: Optional[HTTPServer] = None
_server_thread: Optional[threading.Thread] = None

# ── 延迟导入核心模块 ──
_harness_core = None


def _get_harness():
    global _harness_core
    if _harness_core is None:
        try:
            from opcclaw.core.harness import (
                load_agent_config, save_agent_config, apply_config,
                list_agents, delete_agent, clone_agent, validate_config,
                get_available_tools, get_available_skills,
            )
            _harness_core = {
                "load_agent_config": load_agent_config,
                "save_agent_config": save_agent_config,
                "apply_config": apply_config,
                "list_agents": list_agents,
                "delete_agent": delete_agent,
                "clone_agent": clone_agent,
                "validate_config": validate_config,
                "get_available_tools": get_available_tools,
                "get_available_skills": get_available_skills,
            }
        except ImportError:
            _harness_core = None
    return _harness_core


# ═══════════════════════════════════════════
# HTTP 请求处理器
# ═══════════════════════════════════════════

class HarnessHandler(BaseHTTPRequestHandler):
    """Agent 设计器 HTTP 请求处理器"""

    def log_message(self, format, *args):
        pass  # 抑制默认日志

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/harness":
            self._serve_designer()
        elif path == "/api/harness/agents":
            self._handle_list_agents()
        elif path.startswith("/api/harness/agent/"):
            # /api/harness/agent/<id>
            parts = path.split("/")
            agent_id = parts[4] if len(parts) >= 5 else None
            if agent_id:
                self._handle_get_agent(agent_id)
            else:
                self._json_response({"error": "缺少 agent_id"}, 400)
        elif path == "/api/harness/tools":
            self._handle_list_tools()
        elif path == "/api/harness/skills":
            self._handle_list_skills()
        else:
            self._json_response({"error": "Not Found"}, 404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}

        if path.startswith("/api/harness/agent/"):
            parts = path.split("/")
            agent_id = parts[4] if len(parts) >= 5 else None
            if not agent_id:
                self._json_response({"error": "缺少 agent_id"}, 400)
                return
            if len(parts) >= 6 and parts[5] == "apply":
                self._handle_apply(agent_id, data)
            else:
                self._handle_save(agent_id, data)
        else:
            self._json_response({"error": "Not Found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}

        if path.startswith("/api/harness/agent/"):
            parts = path.split("/")
            if len(parts) >= 6 and parts[5] == "clone":
                agent_id = parts[4]
                self._handle_clone(agent_id, data)
            else:
                self._json_response({"error": "Not Found"}, 404)
        else:
            self._json_response({"error": "Not Found"}, 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.startswith("/api/harness/agent/"):
            parts = path.split("/")
            agent_id = parts[4] if len(parts) >= 5 else None
            if agent_id:
                self._handle_delete(agent_id)
            else:
                self._json_response({"error": "缺少 agent_id"}, 400)
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
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json_response(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    # ── 页面渲染 ──

    def _serve_designer(self):
        if not os.path.exists(_DESIGNER_HTML):
            self._json_response({"error": "designer.html not found"}, 500)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self._cors_headers()
        self.end_headers()
        with open(_DESIGNER_HTML, "rb") as f:
            self.wfile.write(f.read())

    # ── API: 列出 Agent ──

    def _handle_list_agents(self):
        h = _get_harness()
        if h is None:
            self._json_response({"error": "Harness 核心模块未加载"}, 500)
            return
        try:
            agents = h["list_agents"]()
            self._json_response({"agents": agents, "count": len(agents)})
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    # ── API: 获取 Agent ──

    def _handle_get_agent(self, agent_id: str):
        h = _get_harness()
        if h is None:
            self._json_response({"error": "Harness 核心模块未加载"}, 500)
            return
        try:
            config = h["load_agent_config"](agent_id)
            if config is None:
                self._json_response({"error": f"Agent '{agent_id}' 不存在"}, 404)
                return
            self._json_response(config.to_dict())
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    # ── API: 保存 Agent ──

    def _handle_save(self, agent_id: str, data: dict):
        h = _get_harness()
        if h is None:
            self._json_response({"error": "Harness 核心模块未加载"}, 500)
            return
        try:
            from opcclaw.core.harness.config_schema import AgentConfig
            config = AgentConfig.from_dict(data)
            # 以 URL 中的 agent_id 覆盖表单中的（防止不一致）
            config.agent_name = agent_id
            h["save_agent_config"](config)
            self._json_response({"status": "ok", "agent_id": agent_id})
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    # ── API: 删除 Agent ──

    def _handle_delete(self, agent_id: str):
        h = _get_harness()
        if h is None:
            self._json_response({"error": "Harness 核心模块未加载"}, 500)
            return
        try:
            ok = h["delete_agent"](agent_id)
            if not ok:
                self._json_response({"error": f"Agent '{agent_id}' 不存在"}, 404)
                return
            self._json_response({"status": "ok", "agent_id": agent_id})
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    # ── API: 克隆 Agent ──

    def _handle_clone(self, agent_id: str, data: dict):
        h = _get_harness()
        if h is None:
            self._json_response({"error": "Harness 核心模块未加载"}, 500)
            return
        new_name = data.get("new_name", "")
        if not new_name:
            self._json_response({"error": "缺少 new_name 参数"}, 400)
            return
        try:
            config = h["clone_agent"](agent_id, new_name)
            if config is None:
                self._json_response({"error": f"源 Agent '{agent_id}' 不存在"}, 404)
                return
            self._json_response({"status": "ok", "agent_id": new_name})
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    # ── API: 应用 Agent ──

    def _handle_apply(self, agent_id: str, data: dict):
        h = _get_harness()
        if h is None:
            self._json_response({"error": "Harness 核心模块未加载"}, 500)
            return
        try:
            from opcclaw.core.harness.config_schema import AgentConfig
            config = AgentConfig.from_dict(data)
            config.agent_name = agent_id
            result = h["apply_config"](agent_id, config)
            if result.get("status") == "error":
                self._json_response(result, 400)
            else:
                self._json_response(result)
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    # ── API: 列出工具 ──

    def _handle_list_tools(self):
        h = _get_harness()
        if h is None:
            self._json_response({"tools": []})
            return
        try:
            tools = h["get_available_tools"]()
            self._json_response({"tools": tools, "count": len(tools)})
        except Exception as e:
            self._json_response({"error": str(e), "tools": []}, 500)

    # ── API: 列出技能 ──

    def _handle_list_skills(self):
        h = _get_harness()
        if h is None:
            self._json_response({"skills": []})
            return
        try:
            skills = h["get_available_skills"]()
            self._json_response({"skills": skills, "count": len(skills)})
        except Exception as e:
            self._json_response({"error": str(e), "skills": []}, 500)


# ═══════════════════════════════════════════
# 服务器启动 / 管理
# ═══════════════════════════════════════════

def start_server(port: int = 8551) -> str:
    """启动 Harness 设计器 HTTP 服务器（后台线程）。

    Args:
        port: 监听端口，默认 8551

    Returns:
        URL 字符串，如 "http://localhost:8551/harness"
    """
    global _server, _server_thread

    if _server is not None:
        return f"http://localhost:{port}/harness"

    _server = HTTPServer(("127.0.0.1", port), HarnessHandler)
    _server_thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _server_thread.start()

    return f"http://localhost:{port}/harness"


def stop_server():
    """停止 Harness 设计器服务器"""
    global _server, _server_thread
    if _server is not None:
        _server.shutdown()
        _server = None
        _server_thread = None


def get_server_url(port: int = 8551) -> str:
    return f"http://localhost:{port}/harness"

```
