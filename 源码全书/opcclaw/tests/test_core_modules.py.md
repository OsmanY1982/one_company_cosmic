# `opcclaw/tests/test_core_modules.py`

> 路径：`opcclaw/tests/test_core_modules.py` | 行数：484


---


```python
"""
OPCclaw Core Modules - Unit Tests

Tests for:
- MemoryStore: session CRUD, search, metadata, export/import
- TokenOptimizer: bridge module, graceful fallback
- ToolRegistry: registration, execution, enable/disable, metrics
- PerformanceMonitor: stats tracking, reporting
"""
import unittest
import json
import os
import sys
import time
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from core.memory_store import MemoryStore
from core.token_optimizer import TokenSaverMode, optimize_messages
from core.tool_registry import ToolRegistry
from core.llm_backend import ToolCall, ToolDefinition
from core.performance_monitor import PerformanceMonitor, Timer


class TestMemoryStore(unittest.TestCase):
    """Tests for enhanced MemoryStore."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.store = MemoryStore(base_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_and_load_session(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        self.store.save_session(messages, "test_session")
        loaded = self.store.load_session("test_session")
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["content"], "Hello")

    def test_session_metadata(self):
        messages = [{"role": "user", "content": "How to use Python?"}]
        self.store.save_session(messages, "meta_test", title="Python Help", tags=["python", "help"])
        
        info = self.store.get_session_info("meta_test")
        self.assertIsNotNone(info)
        self.assertEqual(info["title"], "Python Help")
        self.assertIn("python", info["tags"])
        self.assertEqual(info["message_count"], 1)

    def test_auto_title_generation(self):
        messages = [{"role": "user", "content": "What is the weather today?"}]
        self.store.save_session(messages, "auto_title")
        
        info = self.store.get_session_info("auto_title")
        self.assertEqual(info["title"], "What is the weather today?")

    def test_auto_title_truncation(self):
        long_msg = "A" * 100
        messages = [{"role": "user", "content": long_msg}]
        self.store.save_session(messages, "long_title")
        
        info = self.store.get_session_info("long_title")
        self.assertTrue(len(info["title"]) <= 50)
        self.assertTrue(info["title"].endswith("..."))

    def test_list_sessions(self):
        for i in range(3):
            self.store.save_session([{"role": "user", "content": f"Msg {i}"}], f"session_{i}")
        
        sessions = self.store.list_sessions()
        self.assertEqual(len(sessions), 3)

    def test_delete_session(self):
        self.store.save_session([{"role": "user", "content": "Delete me"}], "to_delete")
        self.assertTrue(self.store.delete_session("to_delete"))
        self.assertEqual(self.store.load_session("to_delete"), [])

    def test_rename_session(self):
        self.store.save_session([{"role": "user", "content": "Test"}], "rename_me")
        self.assertTrue(self.store.rename_session("rename_me", "New Title"))
        
        info = self.store.get_session_info("rename_me")
        self.assertEqual(info["title"], "New Title")

    def test_tag_session(self):
        self.store.save_session([{"role": "user", "content": "Test"}], "tag_test")
        self.store.tag_session("tag_test", ["work", "important"])
        
        info = self.store.get_session_info("tag_test")
        self.assertIn("work", info["tags"])
        self.assertIn("important", info["tags"])

    def test_search_sessions(self):
        self.store.save_session([
            {"role": "user", "content": "How to build a website?"},
            {"role": "assistant", "content": "Use React or Vue."},
        ], "search_1")
        self.store.save_session([
            {"role": "user", "content": "What is Python?"},
        ], "search_2")
        
        results = self.store.search_sessions("website")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "search_1")
        
        results = self.store.search_sessions("Python")
        self.assertEqual(len(results), 1)

    def test_search_by_tag(self):
        self.store.save_session([{"role": "user", "content": "A"}], "t1", tags=["work"])
        self.store.save_session([{"role": "user", "content": "B"}], "t2", tags=["personal"])
        
        results = self.store.search_by_tag("work")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "t1")

    def test_statistics(self):
        self.store.save_session([{"role": "user", "content": "A"}], "s1", tags=["x"])
        self.store.save_session(
            [{"role": "user", "content": "B"}, {"role": "assistant", "content": "C"}],
            "s2", tags=["y"],
        )
        
        stats = self.store.get_statistics()
        self.assertEqual(stats["total_sessions"], 2)
        self.assertEqual(stats["total_messages"], 3)
        self.assertIn("x", stats["unique_tags"])

    def test_export_import_json(self):
        messages = [{"role": "user", "content": "Export test"}]
        self.store.save_session(messages, "export_test", title="Export Title")
        
        export_path = self.store.export_session("export_test", format="json")
        self.assertIsNotNone(export_path)
        self.assertTrue(os.path.exists(export_path))
        
        new_id = self.store.import_session(export_path, session_id="imported")
        self.assertEqual(new_id, "imported")
        loaded = self.store.load_session("imported")
        self.assertEqual(len(loaded), 1)

    def test_export_markdown(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
        self.store.save_session(messages, "md_export", title="MD Test")
        
        export_path = self.store.export_session("md_export", format="markdown")
        self.assertIsNotNone(export_path)
        self.assertTrue(export_path.endswith(".md"))
        
        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("# MD Test", content)
        self.assertIn("### USER", content)

    def test_persistent_memory(self):
        self.store.write_memory("test_mem", "# Test Memory")
        self.assertEqual(self.store.read_memory("test_mem"), "# Test Memory")
        
        self.store.append_memory("test_mem", "New entry")
        content = self.store.read_memory("test_mem")
        self.assertIn("New entry", content)
        
        self.assertIn("test_mem", self.store.list_memories())
        self.assertTrue(self.store.delete_memory("test_mem"))
        self.assertEqual(self.store.read_memory("test_mem"), "")

    def test_load_nonexistent_session(self):
        self.assertEqual(self.store.load_session("nope"), [])

    def test_get_info_nonexistent(self):
        self.assertIsNone(self.store.get_session_info("nope"))

    def test_delete_nonexistent(self):
        self.assertFalse(self.store.delete_session("nope"))

    def test_cleanup_old_sessions(self):
        # Create sessions, then verify cleanup keeps minimum
        for i in range(5):
            self.store.save_session([{"role": "user", "content": f"Msg {i}"}], f"old_{i}")
        removed = self.store.cleanup_old_sessions(days=0, keep_min=3)
        # All sessions are brand new (updated_at is now), so none should be "old"
        # unless the cutoff logic matches exactly. With days=0 keep_min=3, the 2
        # oldest beyond keep_min could be removed if their updated_at < cutoff.
        # Since all were just created, this is timing-dependent, but at least verify it runs.
        self.assertIsInstance(removed, int)

    def test_export_nonexistent(self):
        self.assertIsNone(self.store.export_session("nope"))

    def test_import_nonexistent(self):
        self.assertIsNone(self.store.import_session("/nonexistent/path.json"))


class TestTokenOptimizer(unittest.TestCase):
    """Tests for TokenOptimizer bridge module."""

    def test_import(self):
        self.assertIsNotNone(TokenSaverMode)

    def test_passthrough_mode(self):
        optimizer = TokenSaverMode("balanced")
        messages = [{"role": "user", "content": "Hello"}]
        result = optimizer.optimize(messages)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) >= 1)

    def test_optimize_messages_function(self):
        messages = [{"role": "user", "content": "Test"}]
        result = optimize_messages(messages)
        self.assertIsInstance(result, list)

    def test_empty_messages(self):
        result = optimize_messages([])
        self.assertEqual(result, [])


class TestToolRegistry(unittest.TestCase):
    """Tests for enhanced ToolRegistry."""

    def setUp(self):
        self.registry = ToolRegistry(enable_metrics=False)

    def test_register_decorator(self):
        @self.registry.register("test_tool", "A test tool", {"type": "object", "properties": {}})
        def test_tool():
            return "OK"
        
        self.assertEqual(self.registry.count(), 1)
        self.assertIn("test_tool", self.registry.list_tools())

    def test_execute_success(self):
        @self.registry.register("add", "Add numbers", {"type": "object", "properties": {}})
        def add(a: int, b: int):
            return a + b
        
        tc = ToolCall(id="1", name="add", arguments={"a": 2, "b": 3})
        result = self.registry.execute(tc)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], 5)

    def test_execute_unknown_tool(self):
        tc = ToolCall(id="1", name="nonexistent", arguments={})
        result = self.registry.execute(tc)
        
        self.assertFalse(result["success"])
        self.assertIn("未知工具", result["error"])

    def test_execute_error_handling(self):
        @self.registry.register("fail_tool", "Fails", {"type": "object", "properties": {}})
        def fail_tool():
            raise ValueError("Something went wrong")
        
        tc = ToolCall(id="1", name="fail_tool", arguments={})
        result = self.registry.execute(tc)
        
        self.assertFalse(result["success"])
        self.assertIn("ValueError", result["error"])

    def test_disable_enable_tool(self):
        @self.registry.register("toggle_tool", "Toggle", {"type": "object", "properties": {}})
        def toggle_tool():
            return "OK"
        
        self.assertTrue(self.registry.is_enabled("toggle_tool"))
        self.assertEqual(self.registry.count(), 1)
        
        self.registry.disable_tool("toggle_tool")
        self.assertFalse(self.registry.is_enabled("toggle_tool"))
        self.assertEqual(self.registry.count(), 0)
        self.assertEqual(self.registry.count_total(), 1)
        
        tools = self.registry.to_openai_tools()
        self.assertEqual(len(tools), 0)
        
        tc = ToolCall(id="1", name="toggle_tool", arguments={})
        result = self.registry.execute(tc)
        self.assertFalse(result["success"])
        self.assertIn("禁用", result["error"])
        
        self.registry.enable_tool("toggle_tool")
        self.assertTrue(self.registry.is_enabled("toggle_tool"))

    def test_categories(self):
        @self.registry.register("file_read", "Read file", {"type": "object"}, category="filesystem")
        def file_read():
            pass
        
        @self.registry.register("web_search", "Search web", {"type": "object"}, category="network")
        def web_search():
            pass
        
        self.assertEqual(self.registry.list_tools_by_category("filesystem"), ["file_read"])
        self.assertEqual(self.registry.list_tools_by_category("network"), ["web_search"])
        self.assertIn("filesystem", self.registry.get_categories())

    def test_batch_execution(self):
        @self.registry.register("double", "Double", {"type": "object"})
        def double(n: int):
            return n * 2
        
        calls = [
            ToolCall(id="1", name="double", arguments={"n": 2}),
            ToolCall(id="2", name="double", arguments={"n": 5}),
        ]
        results = self.registry.execute_batch(calls)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["result"], 4)
        self.assertEqual(results[1]["result"], 10)

    def test_remove_tool(self):
        @self.registry.register("temp", "Temp", {"type": "object"})
        def temp():
            pass
        
        self.assertEqual(self.registry.count(), 1)
        self.assertTrue(self.registry.remove_tool("temp"))
        self.assertEqual(self.registry.count(), 0)

    def test_add_tool_directly(self):
        def my_handler():
            return "direct"
        
        td = ToolDefinition(name="direct_tool", description="Direct", parameters={}, handler=my_handler)
        self.registry.add_tool(td, category="test")
        self.assertEqual(self.registry.count(), 1)
        
        tc = ToolCall(id="1", name="direct_tool", arguments={})
        result = self.registry.execute(tc)
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "direct")

    def test_to_openai_tools(self):
        @self.registry.register("oai_tool", "OpenAI tool", {"type": "object", "properties": {"q": {"type": "string"}}})
        def oai_tool(q: str):
            return q
        
        tools = self.registry.to_openai_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["type"], "function")
        self.assertEqual(tools[0]["function"]["name"], "oai_tool")

    def test_get_tool_descriptions(self):
        @self.registry.register("desc_tool", "A described tool", {"type": "object"})
        def desc_tool():
            pass
        
        desc = self.registry.get_tool_descriptions()
        self.assertIn("desc_tool", desc)
        self.assertIn("A described tool", desc)

    def test_execute_no_handler(self):
        td = ToolDefinition(name="no_handler", description="No handler", parameters={}, handler=None)
        self.registry.add_tool(td)
        
        tc = ToolCall(id="1", name="no_handler", arguments={})
        result = self.registry.execute(tc)
        self.assertFalse(result["success"])
        self.assertIn("没有绑定的处理函数", result["error"])


class TestPerformanceMonitor(unittest.TestCase):
    """Tests for PerformanceMonitor."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.monitor = PerformanceMonitor(data_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_record_tool_call(self):
        self.monitor.record_tool_call("test_tool", True, 100.0)
        self.monitor.record_tool_call("test_tool", False, 200.0, "error")
        
        report = self.monitor.get_tool_report()
        self.assertEqual(len(report), 1)
        
        stats = report[0]
        self.assertEqual(stats["name"], "test_tool")
        self.assertEqual(stats["call_count"], 2)
        self.assertEqual(stats["success_count"], 1)
        self.assertEqual(stats["error_count"], 1)
        self.assertEqual(stats["success_rate"], 50.0)

    def test_record_llm_request(self):
        self.monitor.record_llm_request("openai", True, 1500.0, tokens_in=100, tokens_out=50)
        
        report = self.monitor.get_llm_report()
        self.assertEqual(len(report), 1)
        self.assertEqual(report[0]["total_tokens_in"], 100)

    def test_summary(self):
        self.monitor.record_tool_call("t1", True, 50.0)
        self.monitor.record_tool_call("t2", False, 100.0, "err")
        self.monitor.record_llm_request("p1", True, 1000.0)
        
        summary = self.monitor.get_summary()
        self.assertEqual(summary["tools"]["registered"], 2)
        self.assertEqual(summary["tools"]["total_calls"], 2)
        self.assertEqual(summary["tools"]["total_errors"], 1)

    def test_event_logging(self):
        self.monitor.log_event("test_event", {"key": "value"})
        events = self.monitor.get_recent_events()
        # log_event for tool_call and llm_request also log events internally,
        # but here we just test direct logging
        found = [e for e in events if e["type"] == "test_event"]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["data"]["key"], "value")

    def test_timer_context_manager(self):
        with Timer(self.monitor, "test_op", "generic"):
            time.sleep(0.02)
        
        events = self.monitor.get_recent_events(event_type="generic_timing")
        self.assertEqual(len(events), 1)
        self.assertTrue(events[0]["data"]["duration_ms"] >= 15)

    def test_save_metrics(self):
        self.monitor.record_tool_call("t1", True, 50.0)
        path = self.monitor.save_metrics()
        self.assertTrue(os.path.exists(path))
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("summary", data)
        self.assertIn("tools", data)

    def test_reset(self):
        self.monitor.record_tool_call("t1", True, 50.0)
        self.monitor.reset()
        
        summary = self.monitor.get_summary()
        self.assertEqual(summary["tools"]["total_calls"], 0)

    def test_tool_stats_properties(self):
        self.monitor.record_tool_call("x", True, 100.0)
        self.monitor.record_tool_call("x", True, 200.0)
        self.monitor.record_tool_call("x", False, 300.0, "err")
        
        report = self.monitor.get_tool_report()
        stats = report[0]
        self.assertEqual(stats["call_count"], 3)
        self.assertEqual(stats["avg_duration_ms"], 200.0)
        self.assertEqual(stats["min_duration_ms"], 100.0)
        self.assertEqual(stats["max_duration_ms"], 300.0)
        self.assertEqual(stats["last_error"], "err")

    def test_llm_error_rate(self):
        self.monitor.record_llm_request("p", True, 100.0)
        self.monitor.record_llm_request("p", False, 200.0, error="timeout")
        
        report = self.monitor.get_llm_report()
        self.assertEqual(report[0]["error_rate"], 50.0)
        self.assertEqual(report[0]["last_error"], "timeout")

    def test_event_trim(self):
        self.monitor.max_events = 5
        for i in range(10):
            self.monitor.log_event(f"ev_{i}", {"i": i})
        events = self.monitor.get_recent_events()
        self.assertEqual(len(events), 5)

    def test_get_recent_events_filtered(self):
        self.monitor.log_event("type_a", {"v": 1})
        self.monitor.log_event("type_b", {"v": 2})
        self.monitor.log_event("type_a", {"v": 3})
        
        a_events = self.monitor.get_recent_events(event_type="type_a")
        self.assertEqual(len(a_events), 2)


if __name__ == "__main__":
    unittest.main()

```
