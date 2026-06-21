# `iqra/skills/flybook_bot/flybook_skill.py`

> 路径：`iqra/skills/flybook_bot/flybook_skill.py` | 行数：15


---


```python
# 飞书机器人技能
# 用于通过飞书机器人发送消息

def send_flybook_message(text):
    """通过飞书机器人发送消息"""
    try:
        from .config import send_message
        return send_message(text)
    except Exception as e:
        print(f"飞书机器人发送失败: {e}")
        return False

# 测试函数
if __name__ == "__main__":
    send_flybook_message("Hello, 飞书！")
```
