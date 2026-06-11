# 飞书双向对话系统

## 1. 安装依赖
```bash
pip install flask requests
```

## 2. 创建接收服务 (server.py)
```python
from flask import Flask, request, jsonify
import json
import threading
import time
from flybook_bot.config import send_message

app = Flask(__name__)

# 存储对话历史
conversations = {}

@app.route('/feishu/webhook', methods=['POST'])
def receive_message():
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
        
        # 回复消息
        response_text = f"收到消息：{content}"
        send_message(response_text)
        
        return jsonify({"status": "success"})
    
    return jsonify({"status": "unsupported message type"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
```

## 3. 配置飞书机器人回调地址
1. 登录飞书开发者后台
2. 找到您的机器人设置
3. 在「事件订阅」中配置回调地址：
   ```
   http://您的公网IP:8080/feishu/webhook
   ```

## 4. 启动服务
```bash
python server.py
```

## 5. 使用示例
```python
# 发送消息
from flybook_bot.config import send_message
send_message("你好，飞书！")

# 接收消息（通过回调）
# 机器人会在群聊中自动回复
```

## 注意事项
- 需要公网IP或内网穿透服务（如ngrok）
- 飞书回调地址必须支持HTTPS
- 建议使用企业微信替代，更稳定