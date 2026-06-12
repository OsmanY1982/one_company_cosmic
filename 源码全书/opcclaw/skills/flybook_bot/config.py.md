# `opcclaw/skills/flybook_bot/config.py`

> 路径：`opcclaw/skills/flybook_bot/config.py` | 行数：31


---


```python
# 飞书机器人配置
# 1. 创建飞书机器人：
#    - 打开飞书群聊 -> 右上角菜单 -> 添加机器人
#    - 选择「自定义」-> 填写名称 -> 生成Webhook URL
#    - 复制URL并填入下方

webhook_url = "https://open.feishu.cn/webhook/dPVn8BuIxKlFDnWoN2hiQgZbUD2aYx4o"

# 2. 设置机器人权限（可选）
#    - 群聊可见性：所有成员
#    - 消息类型：文本、卡片、Markdown

# 3. 发送消息函数
import requests

def send_message(text):
    payload = {
        "msg_type": "text",
        "content": {
            "text": text
        }
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(webhook_url, json=payload, headers=headers)
    return response.status_code == 200

# 4. 测试发送
if __name__ == "__main__":
    send_message("测试飞书机器人连接成功！")
```
