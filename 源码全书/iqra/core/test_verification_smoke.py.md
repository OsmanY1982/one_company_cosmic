# `iqra/core/test_verification_smoke.py`

> 路径：`iqra/core/test_verification_smoke.py` | 行数：130


---


```python
#!/usr/bin/env python3
"""verification_hook 模块烟雾测试"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.verification_hook import (
    VerificationHook, ReviewResult, Finding, FindingSeverity,
    format_findings_context,
)

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name}")
        failed += 1


# ── Test 1: ReviewResult defaults ──
print("Test 1: ReviewResult defaults")
r = ReviewResult()
check("verdict=''", r.verdict == "")
check("findings=[]", r.findings == [])
check("summary=''", r.summary == "")

# ── Test 2: Finding dataclass ──
print("Test 2: Finding dataclass")
f = Finding(severity=FindingSeverity.WARNING, desc="文件未关闭", file_path="/tmp/a.txt", suggestion="加 with 语句")
check("severity", f.severity == FindingSeverity.WARNING)
check("desc", f.desc == "文件未关闭")
check("file_path", f.file_path == "/tmp/a.txt")
check("suggestion", f.suggestion == "加 with 语句")

# ── Test 3: parse JSON response ──
print("Test 3: Parse LLM JSON response")
hook = VerificationHook(chat_fn=None, enabled=False)
result = hook._parse_review_response('''
```json
{
  "verdict": "warn",
  "summary": "修改了 3 个文件但未检查调用方",
  "findings": [
    {"severity": "warning", "desc": "未检查调用方", "file_path": "/src/auth.py", "suggestion": "搜索全局引用"},
    {"severity": "info", "desc": "代码风格建议", "file_path": "", "suggestion": "使用 f-string"}
  ]
}
```
''')
check("parse verdict", result.verdict == "warn")
check("parse summary", "未检查调用方" in result.summary)
check("parse findings count", len(result.findings) == 2)
check("parse finding[0] severity", result.findings[0].severity == FindingSeverity.WARNING)
check("parse finding[0] file_path", result.findings[0].file_path == "/src/auth.py")
check("parse finding[1] severity", result.findings[1].severity == FindingSeverity.INFO)
check("parse finding[1] suggestion", result.findings[1].suggestion == "使用 f-string")

# ── Test 4: Parse without code block ──
print("Test 4: Parse raw JSON")
result2 = hook._parse_review_response('{"verdict": "pass", "summary": "一切正常", "findings": []}')
check("raw json verdict", result2.verdict == "pass")
check("raw json findings", result2.findings == [])

# ── Test 5: Parse invalid JSON ──
print("Test 5: Parse invalid JSON")
result3 = hook._parse_review_response("这是一段非 JSON 的文本回复")
check("invalid json verdict=pass", result3.verdict == "pass")
check("invalid json summary", "解析失败" in result3.summary)

# ── Test 6: format_findings_context ──
print("Test 6: format_findings_context")
findings = [
    Finding(FindingSeverity.ERROR, "修改了受保护文件", "/src/chat_engine.py", "撤销修改"),
    Finding(FindingSeverity.WARNING, "未检查调用方", "/src/tools.py", "搜索全局引用"),
    Finding(FindingSeverity.INFO, "建议添加类型标注", "", ""),
]
ctx = format_findings_context(findings)
check("context has 严重问题", "严重问题" in ctx)
check("context has 潜在问题", "潜在问题" in ctx)
check("context has chat_engine.py", "chat_engine.py" in ctx)
check("context has 撤销修改", "撤销修改" in ctx)
check("info not in context", "类型标注" not in ctx)  # info 级别不输出

# ── Test 7: format_findings_context empty ──
print("Test 7: format_findings_context empty")
ctx2 = format_findings_context([])
check("empty context", ctx2 == "")

# ── Test 8: VerificationHook disabled ──
print("Test 8: VerificationHook disabled")
hook2 = VerificationHook(chat_fn=None, enabled=False)
result4 = hook2.review([], [], [], "")
check("disabled returns pass", result4.verdict == "pass")
check("disabled summary", "未启用" in result4.summary)

# ── Test 9: VerificationHook stats ──
print("Test 9: VerificationHook stats")
hook3 = VerificationHook(chat_fn=None, enabled=False)
stats = hook3.stats
check("stats has enabled", "enabled" in stats)
check("stats review_count=0", stats["review_count"] == 0)
check("stats total_findings=0", stats["total_findings"] == 0)

# ── Test 10: Review context builder ──
print("Test 10: Review context builder")
ctx = hook3._build_review_context(
    tools_called=["read_file", "write_file"],
    tool_results=[
        {"tool": "read_file", "success": True, "output": "def foo(): pass"},
        {"tool": "write_file", "success": False, "error": "权限不足"},
    ],
    user_query="重构登录模块",
)
check("context has tools list", "read_file, write_file" in ctx)
check("context has user query", "重构登录模块" in ctx)
check("context has success emoji", "✅" in ctx)
check("context has fail emoji", "❌" in ctx)
check("context has error output", "权限不足" in ctx)

# ── Summary ──
print(f"\n{'='*40}")
print(f"  Passed: {passed}  Failed: {failed}")
print(f"{'='*40}")
sys.exit(0 if failed == 0 else 1)

```
