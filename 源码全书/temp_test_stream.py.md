# `temp_test_stream.py`

> 路径：`temp_test_stream.py` | 行数：37


---


```python
import sys, os, json
PROJECT = "/Volumes/D盘工作区/一人公司/one_company_cosmic"
sys.path.insert(0, PROJECT)

with open(f"{PROJECT}/opcclaw/data/opcclaw_config.json") as f:
    cfg = json.load(f)

from opcclaw.core.llm_backend import ProviderConfig, BackendFactory
prov = cfg["local_providers"]["ollama"]
pc = ProviderConfig(name=prov["name"], provider_type=prov["provider_type"],
    base_url=prov["base_url"], api_key=prov.get("api_key",""), model=prov["model"])
backend = BackendFactory.create(pc)
print(f"[1] Backend OK: {prov['model']} @ {prov['base_url']}")

from modules.intelligence.agent_bridge import AgentBridge
bridge = AgentBridge(backend)
print(f"[2] AgentBridge OK")

print(f"\n[3] 调用 chat_stream_generator('你好') …")
gen = bridge.chat_stream_generator("你好，用一句话介绍你自己")
chunks = []; usage = 0
try:
    for i, chunk in enumerate(gen):
        if chunk.startswith('{"usage"'):
            usage += 1; continue
        chunks.append(chunk)
        print(f"    [{i:02d}]: {repr(chunk[:60])}")
        if i > 80: print("    …(截断)"); break
except Exception as e:
    print(f"\n[FAIL] 生成器迭代失败: {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)

full = "".join(chunks)
print(f"\n[4] {len(chunks)} text chunks, {usage} usage blocks, {len(full)} chars")
print(f"    回复: {full[:200]}")
print("\n[OK] 流式链路正常" if full.strip() else "\n[FAIL] 回复为空")

```
