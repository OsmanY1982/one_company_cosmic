#!/usr/bin/env python3
"""Smoke tests for a2a_tool.py -- verify imports, AgentCard, client/server instantiation."""
import sys, os, json, threading, time

sys.path.insert(0, "/Volumes/D盘工作区/一人公司宇宙版/one_company_cosmic/iqra")

from tools.a2a_tool import (
    AgentCard, AgentCapabilities, AgentSkill, AgentProvider,
    AgentCardBuilder, A2AServer, A2AClient, A2ATaskHandler,
    A2ATask, TaskStatus,
    _make_jsonrpc_request, _send_jsonrpc, _dataclass_to_dict,
    register_a2a_tools,
)

# ── Test 1: Dataclass construction ──
print("Test 1: AgentCard construction")
card = AgentCard(
    name="TestAgent",
    description="A test agent",
    url="http://localhost:9100",
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=False),
    skills=[AgentSkill(id="test", name="Test Skill", description="Does test things", tags=["test"])],
    provider=AgentProvider(organization="TestCorp", url="https://test.com"),
)
d = card.to_dict()
assert d["name"] == "TestAgent"
assert d["url"] == "http://localhost:9100"
assert len(d["skills"]) == 1
print("  PASS: to_dict() correct")

# ── Test 2: JSON-RPC request builder ──
print("Test 2: JSON-RPC request")
req = _make_jsonrpc_request("tasks/send", {"message": "hello"})
assert req["jsonrpc"] == "2.0"
assert req["method"] == "tasks/send"
assert req["params"] == {"message": "hello"}
assert "id" in req
print("  PASS: JSON-RPC 2.0 format correct")

# ── Test 3: AgentCardBuilder ──
print("Test 3: AgentCardBuilder")
builder = AgentCardBuilder(tool_registry=None, skill_loader=None)
card = builder.build(name="Iqra", description="Test", url="http://localhost:9100")
d = card.to_dict()
assert len(d["skills"]) >= 2  # at least core.agent_loop + core.mcp
assert any(s["id"] == "core.agent_loop" for s in d["skills"])
assert any(s["id"] == "core.mcp" for s in d["skills"])
print(f"  PASS: {len(d['skills'])} skills collected")

# ── Test 4: A2AServer start/stop ──
print("Test 4: A2AServer lifecycle")
server = A2AServer()
task_handler = A2ATaskHandler(agent_loop_factory=None)
server.start(agent_card=card, task_handler=task_handler, host="127.0.0.1", port=0)
assert server.port is not None
assert server._running

# Verify Agent Card endpoint via HTTP
import urllib.request
url = f"http://127.0.0.1:{server.port}/.well-known/agent.json"
resp = urllib.request.urlopen(url, timeout=5)
data = json.loads(resp.read().decode())
assert data["name"] == "Iqra"
print(f"  PASS: Agent Card served at {url}")

# Verify health endpoint
resp2 = urllib.request.urlopen(f"http://127.0.0.1:{server.port}/health", timeout=5)
health = json.loads(resp2.read().decode())
assert health["status"] == "ok"
print("  PASS: Health endpoint")

# Verify tasks/send via JSON-RPC
import urllib.request as ur
req_body = json.dumps(_make_jsonrpc_request("tasks/send", {"message": {"parts": [{"type": "text", "text": "hello"}]}})).encode()
http_req = ur.Request(url, data=req_body, headers={"Content-Type": "application/json"}, method="POST")
resp3 = ur.urlopen(http_req, timeout=5)
rpc_result = json.loads(resp3.read().decode())
assert rpc_result["result"]["status"]["state"] == "working"
task_id = rpc_result["result"]["id"]
print(f"  PASS: tasks/send → task_id={task_id}")

# Check task status
time.sleep(0.5)
req_body2 = json.dumps(_make_jsonrpc_request("tasks/get", {"id": task_id})).encode()
http_req2 = ur.Request(url, data=req_body2, headers={"Content-Type": "application/json"}, method="POST")
resp4 = ur.urlopen(http_req2, timeout=5)
task_status = json.loads(resp4.read().decode())
assert task_status["result"]["id"] == task_id
print(f"  PASS: tasks/get → state={task_status['result']['status']['state']}")

server.stop()
print("  PASS: Server stopped cleanly")

# ── Test 5: A2AClient ──
print("Test 5: A2AClient")
client = A2AClient()
client.configure_agent("test_agent", "http://127.0.0.1:9100/.well-known/agent.json", timeout=30)
agents = client.list_agents()
assert len(agents) == 1
assert agents[0]["name"] == "test_agent"
print("  PASS: Client configure/list")

# ── Test 6: A2ATaskHandler ──
print("Test 6: A2ATaskHandler")
handler = A2ATaskHandler()
task = handler.create_task({"message": {"parts": [{"type": "text", "text": "test task"}]}})
assert task["status"]["state"] == "working"
status = handler.get_task(task["id"])
assert status["id"] == task["id"]
handler.cancel_task(task["id"])
status2 = handler.get_task(task["id"])
assert status2["status"]["state"] == "cancelled"
print("  PASS: Task lifecycle (create→get→cancel)")

# ── Test 7: Custom AgentLoop factory ──
print("Test 7: A2ATaskHandler with AgentLoop factory")
from dataclasses import dataclass as dc

@dc
class MockResult:
    success: bool = True
    summary: str = ""
    steps_taken: int = 0
    tools_called: list = None
    errors: list = None
    events: list = None
    duration_seconds: float = 0

class MockAgent:
    def run(self, msg):
        return MockResult(success=True, summary=f"Processed: {msg}")

handler2 = A2ATaskHandler(agent_loop_factory=lambda: MockAgent())
task2 = handler2.create_task({"message": {"parts": [{"type": "text", "text": "hello world"}]}})
time.sleep(0.3)
status3 = handler2.get_task(task2["id"])
assert status3["status"]["state"] == "completed"
assert "hello world" in status3["artifacts"][0]["parts"][0]["text"]
print("  PASS: AgentLoop factory integration")

print("\n✅ All 7 tests passed")
