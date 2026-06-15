"""
工作流预设模板库

提供 3 个开箱即用的工作流模板，用户可加载后在此基础上修改。
"""

from typing import Dict, Any, List

# ── 节点类型常量 ──
NODE_INPUT = "InputNode"
NODE_LLM = "LLMNode"
NODE_TOOL = "ToolNode"
NODE_CONDITIONAL = "ConditionalNode"
NODE_LOOP = "LoopNode"
NODE_OUTPUT = "OutputNode"

# ── 模板定义 ──

TEMPLATE_DOC_QA: Dict[str, Any] = {
    "name": "文档问答",
    "description": "用户输入问题 → LLM(RAG)检索文档并回答 → 输出结果",
    "nodes": [
        {
            "id": "input_1",
            "type": NODE_INPUT,
            "label": "用户输入",
            "x": 100, "y": 200,
            "config": {"input_type": "text"}
        },
        {
            "id": "llm_1",
            "type": NODE_LLM,
            "label": "LLM 问答 (RAG)",
            "x": 400, "y": 200,
            "config": {
                "model": "gpt-4o",
                "temperature": 0.3,
                "prompt": "基于以下文档内容回答问题：\n{context}\n\n问题：{input}\n\n请用中文回答，引用原文段落。",
                "use_rag": True
            }
        },
        {
            "id": "output_1",
            "type": NODE_OUTPUT,
            "label": "输出答案",
            "x": 700, "y": 200,
            "config": {"output_format": "markdown"}
        }
    ],
    "edges": [
        {"source": "input_1", "target": "llm_1", "source_port": "output", "target_port": "input"},
        {"source": "llm_1", "target": "output_1", "source_port": "output", "target_port": "input"}
    ]
}

TEMPLATE_COMPETITOR_MONITOR: Dict[str, Any] = {
    "name": "竞品监控",
    "description": "用户输入竞品名 → 网络搜索最新动态 → LLM分析 → 输出分析报告",
    "nodes": [
        {
            "id": "input_1",
            "type": NODE_INPUT,
            "label": "输入竞品名称",
            "x": 100, "y": 200,
            "config": {"input_type": "text"}
        },
        {
            "id": "tool_1",
            "type": NODE_TOOL,
            "label": "Web 搜索",
            "x": 400, "y": 200,
            "config": {
                "tool_name": "web_search",
                "params": {"query": "{input}", "num_results": 10}
            }
        },
        {
            "id": "llm_1",
            "type": NODE_LLM,
            "label": "竞品分析",
            "x": 700, "y": 200,
            "config": {
                "model": "gpt-4o",
                "temperature": 0.5,
                "prompt": "你是竞品分析专家。基于以下搜索结果，分析竞品最新动态：\n{search_results}\n\n竞品名称：{input}\n\n请从以下维度分析：\n1. 最新发布的功能/产品\n2. 市场策略变化\n3. 融资/人事变动\n4. 优劣势对比\n5. 对我方的影响与建议"
            }
        },
        {
            "id": "output_1",
            "type": NODE_OUTPUT,
            "label": "输出分析报告",
            "x": 1000, "y": 200,
            "config": {"output_format": "markdown"}
        }
    ],
    "edges": [
        {"source": "input_1", "target": "tool_1", "source_port": "output", "target_port": "input"},
        {"source": "tool_1", "target": "llm_1", "source_port": "output", "target_port": "input"},
        {"source": "llm_1", "target": "output_1", "source_port": "output", "target_port": "input"}
    ]
}

TEMPLATE_CODE_REVIEW: Dict[str, Any] = {
    "name": "代码审查",
    "description": "输入代码 → LLM审查 → 条件判断(通过/修改/拒绝) → 分级输出",
    "nodes": [
        {
            "id": "input_1",
            "type": NODE_INPUT,
            "label": "输入代码",
            "x": 100, "y": 250,
            "config": {"input_type": "code"}
        },
        {
            "id": "llm_1",
            "type": NODE_LLM,
            "label": "LLM 代码审查",
            "x": 400, "y": 150,
            "config": {
                "model": "gpt-4o",
                "temperature": 0.2,
                "prompt": "请审查以下代码，从正确性、性能、安全性、可维护性四个维度评分（1-10），并给出分级：\n- PASS: 总分 ≥ 32\n- REVISE: 总分 20-31\n- REJECT: 总分 < 20\n\n代码：\n{input}\n\n输出格式：\n评分：C={correctness} P={performance} S={security} M={maintainability}\n分级：{{grade}}\n详细建议：..."
            }
        },
        {
            "id": "cond_1",
            "type": NODE_CONDITIONAL,
            "label": "质量分级",
            "x": 700, "y": 150,
            "config": {
                "condition": "grade",
                "branches": {
                    "PASS": "output_pass",
                    "REVISE": "output_revise",
                    "REJECT": "output_reject"
                }
            }
        },
        {
            "id": "output_pass",
            "type": NODE_OUTPUT,
            "label": "通过 ✓",
            "x": 400, "y": 400,
            "config": {"output_format": "text", "style": "success"}
        },
        {
            "id": "output_revise",
            "type": NODE_OUTPUT,
            "label": "需修改 ⚠",
            "x": 700, "y": 400,
            "config": {"output_format": "text", "style": "warning"}
        },
        {
            "id": "output_reject",
            "type": NODE_OUTPUT,
            "label": "拒绝 ✗",
            "x": 1000, "y": 400,
            "config": {"output_format": "text", "style": "error"}
        }
    ],
    "edges": [
        {"source": "input_1", "target": "llm_1", "source_port": "output", "target_port": "input"},
        {"source": "llm_1", "target": "cond_1", "source_port": "output", "target_port": "input"},
        {"source": "cond_1", "target": "output_pass", "source_port": "branch_PASS", "target_port": "input"},
        {"source": "cond_1", "target": "output_revise", "source_port": "branch_REVISE", "target_port": "input"},
        {"source": "cond_1", "target": "output_reject", "source_port": "branch_REJECT", "target_port": "input"}
    ]
}

# ── 模板注册表 ──
ALL_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "doc_qa": TEMPLATE_DOC_QA,
    "competitor_monitor": TEMPLATE_COMPETITOR_MONITOR,
    "code_review": TEMPLATE_CODE_REVIEW,
}


def list_templates() -> List[Dict[str, str]]:
    """列出所有可用模板"""
    return [
        {"id": tid, "name": t["name"], "description": t["description"]}
        for tid, t in ALL_TEMPLATES.items()
    ]


def get_template(template_id: str) -> Dict[str, Any]:
    """获取指定模板"""
    template = ALL_TEMPLATES.get(template_id)
    if template is None:
        raise KeyError(f"模板 '{template_id}' 不存在，可用: {list(ALL_TEMPLATES.keys())}")
    return template
