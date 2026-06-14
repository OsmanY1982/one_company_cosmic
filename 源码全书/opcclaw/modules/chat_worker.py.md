# `opcclaw/modules/chat_worker.py`

> 路径：`opcclaw/modules/chat_worker.py` | 行数：35


---


```python
"""
OPCclaw - 后台 LLM 调用工作线程
"""

from PyQt5.QtCore import QThread, pyqtSignal


class ChatWorker(QThread):
    """后台 LLM 调用, 通过信号更新 UI"""
    text_chunk = pyqtSignal(str)
    finished = pyqtSignal(str, dict)  # text, usage_info
    error = pyqtSignal(str)

    def __init__(self, engine, user_message: str):
        super().__init__()
        self.engine = engine
        self.user_message = user_message

    def run(self):
        try:
            usage_info = {}
            for chunk in self.engine.chat_stream(self.user_message):
                # 检查是否是 usage 信息（JSON 格式）
                if chunk.startswith('{"usage":'):
                    try:
                        import json
                        data = json.loads(chunk)
                        usage_info = data.get("usage", {})
                    except (json.JSONDecodeError, ValueError, AttributeError):
                        pass  # usage 信息是可选的，解析失败不影响主功能
                else:
                    self.text_chunk.emit(chunk)
            self.finished.emit("", usage_info)
        except Exception as e:
            self.error.emit(str(e))

```
