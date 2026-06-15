"""
可观测性模块自检脚本（轻量版 — 跳过 SmartMemoryStore 完整初始化）
验证：TokenObserver / TraceManager / CostTracker 核心逻辑 + ObservableBridge 聚合
"""
import sys, os, json, time
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, _project_root)

from opcclaw.core.observability.schema import TokenRecord, TraceRecord, CostRecord, estimate_cost, MODEL_PRICING
from opcclaw.core.observability.token_observer import TokenObserver
from opcclaw.core.observability.trace_manager import TraceManager
from opcclaw.core.observability.cost_tracker import CostTracker
from opcclaw.core.observability import ObservableBridge

# ── 1. Schema & Pricing ──
print(f"[1/5] MODEL_PRICING entries: {len(MODEL_PRICING)}")
cost = estimate_cost("gpt-4o", 500, 300)
print(f"      gpt-4o cost for 500in+300out = ${cost:.6f}")

# ── 2. TokenObserver ──
obs = TokenObserver()
class FakeResponse:
    def __init__(self, content, usage=None, tool_calls=None):
        self.content = content
        self.usage = usage
        self.tool_calls = tool_calls

class FakeBackend:
    def __init__(self):
        self.chat = lambda msgs, tools=None, tool_choice=None: FakeResponse("OK", {"prompt_tokens": 10, "completion_tokens": 20})
        self.chat_stream = lambda msgs: iter([FakeResponse("OK", {"prompt_tokens": 10, "completion_tokens": 20})])

obs.wrap_backend(FakeBackend())
print(f"[2/5] TokenObserver wrap OK, totals={obs.totals}")

# ── 3. TraceManager ──
tm = TraceManager()
tid = tm.start_trace("session_1", "Hello world")
s0 = tm.step_begin("user_input", {"msg": "Hello"})
tm.step_end(s0)
s1 = tm.step_begin("llm_call", {"model": "gpt-4o"})
tm.step_end(s1)
tm.set_token_usage(100, 200)
tm.end_trace()
print(f"[3/5] TraceManager OK, trace_id={tid}")

# ── 4. CostTracker ──
ct = CostTracker()
ct.record("gpt-4o", "openai", 100, 200, "session_1")
ct.record("gpt-4o", "openai", 50, 80, "session_1")
report = ct.full_report()
print(f"[4/5] CostTracker OK, total_cost=${report.get('total_cost', 'N/A'):.6f}")

# ── 5. ObservableBridge（不传 memory_store，测试纯内存模式）──
bridge = ObservableBridge()  # no memory_store → 不持久化
bridge.attach_to(FakeBackend())
tid2 = bridge.trace_begin("s2", "test")
bridge.step_begin("llm_call")
bridge.step_end()
bridge.trace_end()
print(f"[5/5] ObservableBridge OK (memory-only mode)")

# ── 成本报告 ──
print(f"\n--- Cost Report ---")
print(json.dumps(bridge.get_cost_report(), indent=2, ensure_ascii=False))

print("\n=== ALL 5 CHECKS PASSED ===")
