"""
OPCclaw HTTP API Server - 支持浏览器操作
==========================================

提供以下端点:
- POST /chat - AI 对话（支持工具调用）
- POST /browser/action - 浏览器操作
- GET /health - 健康检查

功能:
- 浏览器自动化（打开网页、点击、输入、截图等）
- AI 对话（集成 OPCclaw 核心引擎）
- 数据库查询
"""

from flask import Flask, request, jsonify
import json
import threading
import time
import os
import sys
from datetime import datetime

# 添加 OPCclaw 到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opcclaw.core.core_engine import OPCclawCoreEngine, ToolRegistry
from opcclaw.core.llm_backend import ProviderConfig
from opcclaw.tools.business_tools import register_all_tools

# 尝试导入浏览器自动化工具
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright 未安装，浏览器功能不可用。运行：pip install playwright")

app = Flask(__name__)

# 全局状态
conversations = {}
engine = None
browser_context = None


# ═══════════════════════════════════════════
# 浏览器管理
# ═══════════════════════════════════════════

class BrowserManager:
    """浏览器管理器 - 单例模式"""
    
    _instance = None
    _playwright = None
    _browser = None
    _context = None
    _page = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright 未安装")
        
        self._playwright = sync_playwright().start()
        self._browser = None
        self._context = None
        self._page = None
        self._initialized = True
    
    def launch(self, headless=True):
        """启动浏览器"""
        if self._browser is None:
            self._browser = self._playwright.chromium.launch(headless=headless)
            self._context = self._browser.new_context(
                viewport={"width": 1280, "height": 720}
            )
            self._page = self._context.new_page()
        return {"success": True, "message": "浏览器已启动"}
    
    def navigate(self, url: str):
        """打开网页"""
        if self._page is None:
            self.launch()
        
        try:
            response = self._page.goto(url, wait_until="networkidle", timeout=30000)
            return {
                "success": True,
                "url": url,
                "status": response.status,
                "title": self._page.title()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def click(self, selector: str):
        """点击元素"""
        if self._page is None:
            return {"success": False, "error": "浏览器未启动"}
        
        try:
            self._page.click(selector, timeout=5000)
            return {"success": True, "message": f"已点击：{selector}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def fill(self, selector: str, value: str):
        """填充输入框"""
        if self._page is None:
            return {"success": False, "error": "浏览器未启动"}
        
        try:
            self._page.fill(selector, value, timeout=5000)
            return {"success": True, "message": f"已输入：{value} 到 {selector}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def screenshot(self, path: str = None):
        """截图"""
        if self._page is None:
            return {"success": False, "error": "浏览器未启动"}
        
        try:
            if path is None:
                path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "logs",
                    f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                )
            
            self._page.screenshot(path=path)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_content(self):
        """获取页面内容"""
        if self._page is None:
            return {"success": False, "error": "浏览器未启动"}
        
        try:
            content = self._page.content()
            title = self._page.title()
            url = self._page.url
            return {
                "success": True,
                "url": url,
                "title": title,
                "content_length": len(content)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def evaluate(self, javascript: str):
        """执行 JavaScript"""
        if self._page is None:
            return {"success": False, "error": "浏览器未启动"}
        
        try:
            result = self._page.evaluate(javascript)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def close(self):
        """关闭浏览器"""
        if self._browser:
            self._browser.close()
            self._browser = None
            self._context = None
            self._page = None
        return {"success": True, "message": "浏览器已关闭"}


# 全局浏览器实例
browser_manager = None


def get_browser_manager():
    """获取浏览器管理器实例"""
    global browser_manager
    if browser_manager is None:
        if PLAYWRIGHT_AVAILABLE:
            browser_manager = BrowserManager()
        else:
            return None
    return browser_manager


# ═══════════════════════════════════════════
# 浏览器工具函数
# ═══════════════════════════════════════════

def browser_open(url: str, headless: bool = True) -> dict:
    """打开网页"""
    mgr = get_browser_manager()
    if not mgr:
        return {"error": "浏览器不可用，请安装 playwright: pip install playwright && playwright install"}
    
    try:
        mgr.launch(headless=headless)
        return mgr.navigate(url)
    except Exception as e:
        return {"error": str(e)}


def browser_click(selector: str) -> dict:
    """点击元素"""
    mgr = get_browser_manager()
    if not mgr:
        return {"error": "浏览器不可用"}
    return mgr.click(selector)


def browser_fill(selector: str, value: str) -> dict:
    """填充输入框"""
    mgr = get_browser_manager()
    if not mgr:
        return {"error": "浏览器不可用"}
    return mgr.fill(selector, value)


def browser_screenshot(path: str = None) -> dict:
    """截图"""
    mgr = get_browser_manager()
    if not mgr:
        return {"error": "浏览器不可用"}
    return mgr.screenshot(path)


def browser_get_content() -> dict:
    """获取页面内容"""
    mgr = get_browser_manager()
    if not mgr:
        return {"error": "浏览器不可用"}
    return mgr.get_content()


def browser_execute_js(javascript: str) -> dict:
    """执行 JavaScript"""
    mgr = get_browser_manager()
    if not mgr:
        return {"error": "浏览器不可用"}
    return mgr.evaluate(javascript)


def browser_close() -> dict:
    """关闭浏览器"""
    mgr = get_browser_manager()
    if not mgr:
        return {"error": "浏览器不可用"}
    return mgr.close()


# ═══════════════════════════════════════════
# 初始化 OPCclaw 引擎
# ═══════════════════════════════════════════

def init_engine():
    """初始化 OPCclaw 引擎"""
    global engine
    
    # 使用 Ollama 本地模型
    config = ProviderConfig(
        name="Ollama",
        provider_type="openai_compatible",
        base_url="http://localhost:8080/v1",
        model="qwen3.6-35b-iq2m",
        temperature=0.7,
        max_tokens=4096
    )
    
    engine = OPCclawCoreEngine(config)
    
    # 注册业务工具
    data_dir = "D:/one_company_desktop/data"
    if os.path.exists(data_dir):
        register_all_tools(engine.registry, data_dir)
    
    # 注册浏览器工具
    if PLAYWRIGHT_AVAILABLE:
        engine.registry.register(
            name="browser_open",
            description="打开网页：使用浏览器访问指定 URL",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "要访问的网址"},
                    "headless": {"type": "boolean", "description": "是否无头模式", "default": True}
                },
                "required": ["url"]
            },
            handler=browser_open
        )
        
        engine.registry.register(
            name="browser_click",
            description="点击网页元素：使用 CSS 选择器点击指定元素",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS 选择器，如 '#login-btn', '.submit', 'input[name=username]'"}
                },
                "required": ["selector"]
            },
            handler=browser_click
        )
        
        engine.registry.register(
            name="browser_fill",
            description="填充输入框：在指定输入框中输入文本",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS 选择器"},
                    "value": {"type": "string", "description": "要输入的文本"}
                },
                "required": ["selector", "value"]
            },
            handler=browser_fill
        )
        
        engine.registry.register(
            name="browser_screenshot",
            description="网页截图：保存当前页面为 PNG 图片",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "保存路径（可选，默认自动生成）"}
                }
            },
            handler=browser_screenshot
        )
        
        engine.registry.register(
            name="browser_get_content",
            description="获取页面内容：返回当前页面的 HTML 内容和标题",
            parameters={
                "type": "object",
                "properties": {}
            },
            handler=browser_get_content
        )
        
        engine.registry.register(
            name="browser_execute_js",
            description="执行 JavaScript：在页面中运行自定义 JS 代码",
            parameters={
                "type": "object",
                "properties": {
                    "javascript": {"type": "string", "description": "要执行的 JavaScript 代码"}
                },
                "required": ["javascript"]
            },
            handler=browser_execute_js
        )
        
        engine.registry.register(
            name="browser_close",
            description="关闭浏览器：关闭当前浏览器实例",
            parameters={
                "type": "object",
                "properties": {}
            },
            handler=browser_close
        )
        
        print(f"✅ 浏览器工具已注册（共 7 个）")
    
    print(f"✅ OPCclaw 引擎初始化完成，可用工具：{len(engine.registry._tools)}")


# ═══════════════════════════════════════════
# API 端点
# ═══════════════════════════════════════════

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "engine_initialized": engine is not None,
        "browser_available": PLAYWRIGHT_AVAILABLE and get_browser_manager() is not None,
        "tools_count": len(engine.registry._tools) if engine else 0
    })


@app.route('/chat', methods=['POST'])
def chat():
    """
    AI 对话端点
    
    Request:
    {
        "message": "用户输入",
        "conversation_id": "可选的会话 ID",
        "clear_history": false  // 是否清空历史
    }
    
    Response:
    {
        "success": true,
        "response": "AI 回复",
        "conversation_id": "会话 ID",
        "tool_calls": [...],  // 工具调用记录
        "execution_time": 1.23
    }
    """
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "error": "缺少 message 字段"
            }), 400
        
        message = data['message']
        conversation_id = data.get('conversation_id', 'default')
        clear_history = data.get('clear_history', False)
        
        # 初始化引擎（如果还没初始化）
        if engine is None:
            init_engine()
        
        # 清空历史（如果要求）
        if clear_history:
            engine.clear_history()
        
        # 处理对话
        response_text = engine.chat(message, max_tool_iterations=5)
        
        # 获取工具调用记录
        tool_calls = []
        for msg in engine.messages[-10:]:  # 最近 10 条消息
            if msg.tool_calls:
                tool_calls.append({
                    "role": "assistant",
                    "tool_calls": msg.tool_calls
                })
            elif msg.role == "tool":
                tool_calls.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content
                })
        
        execution_time = time.time() - start_time
        
        return jsonify({
            "success": True,
            "response": response_text,
            "conversation_id": conversation_id,
            "tool_calls": tool_calls,
            "execution_time": round(execution_time, 2),
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/browser/action', methods=['POST'])
def browser_action():
    """
    浏览器操作端点（直接调用，不经过 AI）
    
    Request:
    {
        "action": "open|click|fill|screenshot|get_content|execute_js|close",
        "params": {...}  // 根据 action 不同而不同
    }
    
    Response:
    {
        "success": true/false,
        "result": {...},
        "error": "错误信息（如果有）"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'action' not in data:
            return jsonify({
                "success": False,
                "error": "缺少 action 字段"
            }), 400
        
        action = data['action']
        params = data.get('params', {})
        
        # 检查浏览器是否可用
        if not PLAYWRIGHT_AVAILABLE:
            return jsonify({
                "success": False,
                "error": "浏览器不可用，请安装 playwright: pip install playwright && playwright install"
            }), 503
        
        # 执行操作
        if action == 'open':
            url = params.get('url', '')
            headless = params.get('headless', True)
            if not url:
                return jsonify({"success": False, "error": "缺少 url 参数"})
            result = browser_open(url, headless)
        
        elif action == 'click':
            selector = params.get('selector', '')
            if not selector:
                return jsonify({"success": False, "error": "缺少 selector 参数"})
            result = browser_click(selector)
        
        elif action == 'fill':
            selector = params.get('selector', '')
            value = params.get('value', '')
            if not selector or not value:
                return jsonify({"success": False, "error": "缺少 selector 或 value 参数"})
            result = browser_fill(selector, value)
        
        elif action == 'screenshot':
            path = params.get('path', None)
            result = browser_screenshot(path)
        
        elif action == 'get_content':
            result = browser_get_content()
        
        elif action == 'execute_js':
            javascript = params.get('javascript', '')
            if not javascript:
                return jsonify({"success": False, "error": "缺少 javascript 参数"})
            result = browser_execute_js(javascript)
        
        elif action == 'close':
            result = browser_close()
        
        else:
            return jsonify({
                "success": False,
                "error": f"未知操作：{action}"
            }), 400
        
        return jsonify({
            "success": result.get('success', False),
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/tools', methods=['GET'])
def list_tools():
    """列出所有可用工具"""
    if engine is None:
        init_engine()
    
    tools = engine.registry.list_tools()
    return jsonify({
        "success": True,
        "tools": tools,
        "count": len(tools)
    })


# ═══════════════════════════════════════════
# 飞书 Webhook（保留原有功能）
# ═══════════════════════════════════════════

@app.route('/feishu/webhook', methods=['POST'])
def receive_message():
    """飞书消息 Webhook"""
    data = request.get_json()
    
    # 提取消息内容
    msg_type = data.get('msg_type')
    content = data.get('text', '')
    
    # 处理文本消息
    if msg_type == 'text':
        user_id = data.get('sender_id', {}).get('user_id', 'unknown')
        conversation_id = data.get('chat_id', 'unknown')
        
        # 记录对话
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        conversations[conversation_id].append({
            'user': user_id,
            'message': content,
            'timestamp': time.time()
        })
        
        # 使用 OPCclaw 引擎回复
        if engine is None:
            init_engine()
        
        response_text = engine.chat(content)
        
        # 回复消息（这里需要集成飞书 SDK）
        # send_message(response_text)
        
        return jsonify({
            "status": "success",
            "response": response_text
        })
    
    return jsonify({"status": "unsupported message type"})


# ═══════════════════════════════════════════
# 启动服务器
# ═══════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 60)
    print("OPCclaw HTTP API Server")
    print("=" * 60)
    print(f"📍 监听地址：http://0.0.0.0:8080")
    print(f"🔧 可用端点:")
    print(f"   - GET  /health          健康检查")
    print(f"   - POST /chat            AI 对话")
    print(f"   - POST /browser/action  浏览器操作")
    print(f"   - GET  /tools           工具列表")
    print(f"   - POST /feishu/webhook  飞书 Webhook")
    print("=" * 60)
    
    # 预初始化引擎
    init_engine()
    
    # 启动服务器
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
