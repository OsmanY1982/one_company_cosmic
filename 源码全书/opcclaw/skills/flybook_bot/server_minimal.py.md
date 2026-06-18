# `opcclaw/skills/flybook_bot/server_minimal.py`

> 路径：`opcclaw/skills/flybook_bot/server_minimal.py` | 行数：204


---


```python
"""
OPCclaw HTTP API Server - 最小测试版
====================================

用于快速测试 /chat 端点
"""

from flask import Flask, request, jsonify
import json
import time
import os
import sys
from datetime import datetime

# 添加项目根目录到路径
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))

from opcclaw.core.tool_registry import ToolRegistry
from opcclaw.core.llm_backend import ProviderConfig, OpenAICompatibleBackend

app = Flask(__name__)

# 全局状态
registry = None
backend = None
messages = []


def init_system():
    """初始化系统"""
    global registry, backend
    
    # 创建工具注册表
    registry = ToolRegistry()
    
    # 注册测试工具
    @registry.register("hello", "打招呼工具", {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "人名"}
        },
        "required": ["name"]
    })
    def hello(name: str) -> dict:
        return {"message": f"你好，{name}！"}
    
    # 创建 LLM 后端
    config = ProviderConfig(
        name="Ollama",
        provider_type="openai_compatible",
        base_url="http://localhost:8080/v1",
        model="qwen3.6-35b-iq2m",
        temperature=0.7,
        max_tokens=2048
    )
    
    backend = OpenAICompatibleBackend(config)
    
    print(f"✅ 系统初始化完成")
    print(f"   工具数量：{registry.count()}")


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "tools_count": registry.count() if registry else 0
    })


@app.route('/chat', methods=['POST'])
def chat():
    """AI 对话端点"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "error": "缺少 message 字段"
            }), 400
        
        user_message = data['message']
        clear_history = data.get('clear_history', False)
        
        if clear_history:
            messages.clear()
        
        # 添加用户消息
        messages.append({"role": "user", "content": user_message})
        
        # 构建请求
        system_prompt = "你是一个友好的 AI 助手。你有以下工具可用："
        if registry:
            tools_desc = registry.get_tool_descriptions()
            system_prompt += "\n" + tools_desc
        
        api_messages = [
            {"role": "system", "content": system_prompt},
            *messages
        ]
        
        # 获取工具定义
        tools = registry.to_openai_tools() if registry else []
        
        # 调用 LLM
        print(f"📤 调用 LLM: {user_message}")
        response = backend.chat(api_messages, tools=tools)
        
        # 处理响应
        if response.tool_calls:
            # 需要调用工具
            tool_results = []
            for tc in response.tool_calls:
                print(f"🔧 执行工具：{tc.name}({tc.arguments})")
                result = registry.execute(tc)
                tool_results.append(result)
                print(f"✅ 工具结果：{result}")
            
            # 添加工具调用到历史
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
                } for tc in response.tool_calls]
            })
            
            # 添加工具结果
            for i, result in enumerate(tool_results):
                messages.append({
                    "role": "tool",
                    "tool_call_id": response.tool_calls[i].id,
                    "content": json.dumps(result, ensure_ascii=False)
                })
            
            # 再次调用 LLM 获取最终回复
            api_messages = [
                {"role": "system", "content": system_prompt},
                *messages
            ]
            final_response = backend.chat(api_messages, tools=tools)
            assistant_message = final_response.content or "任务完成"
        else:
            assistant_message = response.content or "你好！"
        
        # 添加 AI 回复到历史
        messages.append({"role": "assistant", "content": assistant_message})
        
        execution_time = time.time() - start_time
        
        return jsonify({
            "success": True,
            "response": assistant_message,
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
    tools = registry.to_openai_tools() if registry else []
    return jsonify({
        "success": True,
        "tools": tools,
        "count": len(tools)
    })


if __name__ == '__main__':
    print("=" * 60)
    print("OPCclaw HTTP API Server (最小测试版)")
    print("=" * 60)
    print(f"📍 监听地址：http://127.0.0.1:8080")
    print(f"🔧 可用端点:")
    print(f"   - GET  /health  健康检查")
    print(f"   - POST /chat    AI 对话")
    print(f"   - GET  /tools   工具列表")
    print("=" * 60)
    
    # 初始化
    init_system()
    
    # 启动服务器
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)

```
