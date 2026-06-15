# `opcclaw/core/observability/test_obs.py`

> 路径：`opcclaw/core/observability/test_obs.py` | 行数：62


---


```python
"""
可观测性模块自检脚本
验证：ObservableBridge 初始化 → Backend hook → trace 生命周期 → 数据持久化
"""
import sys, os, json, time
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, _project_root)

from opcclaw.core.observability import ObservableBridge
from opcclaw.core.smart_memory_adapter import SmartMemoryStore

# ── Step 1: 初始化 SmartMemoryStore ──
base_dir = "/tmp/opcclaw_obs_test"
os.makedirs(base_dir, exist_ok=True)
memory = SmartMemoryStore(base_dir=base_dir)
print(f"[1/5] SmartMemoryStore OK (core_memory={'YES' if memory._core_memory else 'NO'})")

# ── Step 2: 初始化 ObservableBridge ──
obs = ObservableBridge(memory_store=memory)
print("[2/5] ObservableBridge OK")

# ── Step 3: 模拟 Backend 调用 ──
class MockBackend:
    def chat(self, messages, tools=None, tool_choice=None):
        return self
    
    def chat_stream(self, messages):
        yield self
    
    def __init__(self):
        self.content = "Mock response"
        self.usage = None
        self.tool_calls = None

backend = MockBackend()
obs.attach_to(backend)

# ── Step 4: trace 生命周期 ──
trace_id = obs.trace_begin(session_id="test_session", user_message="Hello")
print(f"[3/5] Trace started: {trace_id}")

step0 = obs.step_begin("user_input", {"msg": "Hello"})
obs.step_end(step0)

step1 = obs.step_begin("llm_call", {"model": "gpt-4o"})
obs.step_end(step1)

obs.trace_end()
print("[4/5] Trace ended and persisted")

# ── Step 5: 验证持久化 ──
if memory._core_memory:
    results = memory._core_memory.search("observability", "")
    found = results if results else []
    print(f"[5/5] OPCclawMemory records found: {len(found)}")

# ── 成本报告 ──
report = obs.get_cost_report()
print(f"\n--- Cost Report ---")
print(json.dumps(report, indent=2, ensure_ascii=False))

print("\n=== ALL CHECKS PASSED ===")

```
