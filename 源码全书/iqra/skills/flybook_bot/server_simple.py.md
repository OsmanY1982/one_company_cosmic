# `iqra/skills/flybook_bot/server_simple.py`

> 路径：`iqra/skills/flybook_bot/server_simple.py` | 行数：182


---


```python
"""
Iqra HTTP API Server - 简化版（无浏览器）
==========================================

用于快速测试 /chat 端点，不需要 Playwright

端点:
- POST /chat - AI 对话
- GET /health - 健康检查
- GET /tools - 工具列表
"""

from flask import Flask, request, jsonify
import json
import time
import os
import sys
from datetime import datetime

# 添加 Iqra 到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from iqra.core.core_engine import IqraCoreEngine
from iqra.core.llm_backend import ProviderConfig
from iqra.tools.business_tools import register_all_tools

app = Flask(__name__)

# 全局引擎
engine = None


def init_engine():
    """初始化 Iqra 引擎"""
    global engine
    
    # 从 ConfigManager 读取当前激活的模型设置，fallback 到硬编码值
    from core.core_engine import _get_active_provider_config
    config = _get_active_provider_config()
    if config is None:
        config = ProviderConfig(
            name="Ollama",
            provider_type="openai_compatible",
            base_url="http://localhost:8080/v1",
            model="qwen2.5:7b",
            temperature=0.7,
            max_tokens=4096
        )
    
    engine = IqraCoreEngine(config)
    
    # 注册业务工具
    import os
    _data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data")
    data_dir = _data_dir
    if os.path.exists(data_dir):
        register_all_tools(engine.registry, data_dir)
    
    print(f"✅ Iqra 引擎初始化完成，可用工具：{len(engine.registry._tools)}")


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "engine_initialized": engine is not None,
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
        "clear_history": false
    }
    
    Response:
    {
        "success": true,
        "response": "AI 回复",
        "conversation_id": "会话 ID",
        "tool_calls": [...],
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
        for msg in engine.messages[-10:]:
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


if __name__ == '__main__':
    print("=" * 60)
    print("Iqra HTTP API Server (简化版)")
    print("=" * 60)
    print(f"📍 监听地址：http://127.0.0.1:8080")
    print(f"🔧 可用端点:")
    print(f"   - GET  /health  健康检查")
    print(f"   - POST /chat    AI 对话")
    print(f"   - GET  /tools   工具列表")
    print("=" * 60)
    
    # 预初始化引擎
    init_engine()
    
    # 启动服务器
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)

```
