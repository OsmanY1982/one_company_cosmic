"""
工作流编译器

输入工作流 JSON（nodes + edges），输出可运行的 Python 脚本。

管线类型：
  - 线性管线：拓扑排序后顺序执行
  - 条件分支：基于 LLM 输出执行不同分支（if/elif/else）
  - 循环管线：while 循环直到满足退出条件

依赖：networkx（已在 deps/requirements.txt 中声明）
"""

import json
import os
import sys
from typing import Dict, Any, List, Optional, Tuple

import networkx as nx

# ── 节点类型 ──
NODE_INPUT = "InputNode"
NODE_LLM = "LLMNode"
NODE_TOOL = "ToolNode"
NODE_CONDITIONAL = "ConditionalNode"
NODE_LOOP = "LoopNode"
NODE_OUTPUT = "OutputNode"

# ── AgentBridge 方法映射 ──
NODE_METHOD_MAP = {
    NODE_LLM: "bridge.chat",
    NODE_TOOL: "bridge.call_tool",
    NODE_OUTPUT: "print",
}


def _build_dag(nodes: List[Dict], edges: List[Dict]) -> nx.DiGraph:
    """从节点和边构建有向图"""
    G = nx.DiGraph()
    for node in nodes:
        G.add_node(node["id"], **node)
    for edge in edges:
        G.add_edge(edge["source"], edge["target"],
                   source_port=edge.get("source_port", "output"),
                   target_port=edge.get("target_port", "input"))
    return G


def _topological_order(G: nx.DiGraph, nodes: List[Dict]) -> List[str]:
    """拓扑排序，返回线性执行顺序。条件节点仅保留主分支做拓扑。"""
    try:
        order = list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible:
        # 有环 → 用 DFS 后序遍历近似
        order = list(nx.dfs_postorder_nodes(G))
        order.reverse()
    return order


def _compile_linear(G: nx.DiGraph, order: List[str]) -> Tuple[str, List[str]]:
    """编译线性（无分支/无循环）工作流。

    Returns:
        (code_str, import_lines) — 生成的代码和所需的 import。
    """
    lines = []
    imports = set()
    var_counter = 0

    # 找到 InputNode → 第一个节点的映射
    input_vars = {}
    for nid in order:
        node = G.nodes[nid]
        if node["type"] == NODE_INPUT:
            var_name = f"user_input"
            input_vars[nid] = var_name

    # 按拓扑序生成代码
    for nid in order:
        node = G.nodes[nid]
        ntype = node["type"]
        config = node.get("config", {})
        label = node.get("label", nid)
        var_counter += 1
        var_name = f"result_{var_counter}"

        if ntype == NODE_INPUT:
            lines.append(f"# {label}")
            lines.append(f"{var_name} = input(\"请输入: \")")
            input_vars[nid] = var_name

        elif ntype == NODE_LLM:
            preds = list(G.predecessors(nid))
            input_val = _resolve_input(preds, input_vars, f"result_{var_counter - 1}")
            model = config.get("model", "gpt-4o")
            temp = config.get("temperature", 0.7)
            prompt = config.get("prompt", "{input}")
            prompt_escaped = prompt.replace('"', '\\"').replace('\n', '\\n')

            lines.append(f"# {label}")
            if config.get("use_rag"):
                imports.add("from iqra.core.rag_context import RAGContextInjector")
                lines.append(f"rag = RAGContextInjector()")
                lines.append(f"context = rag.retrieve({input_val})")
                lines.append(f'prompt = "{prompt_escaped}".format(input={input_val}, context=context)')
            else:
                lines.append(f'prompt = "{prompt_escaped}".format(input={input_val})')
            lines.append(f'{var_name} = bridge.chat(')
            lines.append(f'    prompt,')
            lines.append(f'    model="{model}",')
            lines.append(f'    temperature={temp}')
            lines.append(f')')
            input_vars[nid] = var_name

        elif ntype == NODE_TOOL:
            preds = list(G.predecessors(nid))
            input_val = _resolve_input(preds, input_vars, f"result_{var_counter - 1}")
            tool_name = config.get("tool_name", "echo")
            params = config.get("params", {})

            lines.append(f"# {label}")
            params_str = json.dumps(params).replace('"{input}"', input_val)
            lines.append(f'{var_name} = bridge.call_tool("{tool_name}", **{params_str})')
            input_vars[nid] = var_name

        elif ntype == NODE_OUTPUT:
            preds = list(G.predecessors(nid))
            input_val = _resolve_input(preds, input_vars, f"result_{var_counter - 1}")
            fmt = config.get("output_format", "text")

            lines.append(f"# {label}")
            if fmt == "markdown":
                imports.add("from rich.markdown import Markdown")
                imports.add("from rich.console import Console")
                lines.append(f"console = Console()")
                lines.append(f"console.print(Markdown(str({input_val})))")
            else:
                lines.append(f"print({input_val})")
            input_vars[nid] = var_name

    return "\n".join(lines), sorted(imports)


def _resolve_input(preds: List[str], input_vars: Dict[str, str],
                   fallback: str) -> str:
    """解析节点的输入变量名"""
    for pred in preds:
        if pred in input_vars:
            return input_vars[pred]
    return fallback


def compile_workflow(workflow_json: Dict[str, Any]) -> str:
    """将工作流 JSON 编译为完整的 Python 脚本。

    Args:
        workflow_json: {"nodes": [...], "edges": [...], "name": "..."}

    Returns:
        完整的 Python 脚本字符串
    """
    nodes = workflow_json.get("nodes", [])
    edges = workflow_json.get("edges", [])
    name = workflow_json.get("name", "workflow")

    if not nodes:
        return '# (空工作流)'

    G = _build_dag(nodes, edges)

    # 检查是否有条件/循环节点
    has_conditional = any(G.nodes[n]["type"] == NODE_CONDITIONAL for n in G.nodes)
    has_loop = any(G.nodes[n]["type"] == NODE_LOOP for n in G.nodes)

    if has_conditional:
        return _compile_conditional(G, nodes, edges, name)
    elif has_loop:
        return _compile_loop(G, nodes, edges, name)
    else:
        order = _topological_order(G, nodes)
        body, imports = _compile_linear(G, order)
        return _wrap_script(body, imports, name)


def _compile_conditional(G: nx.DiGraph, nodes: List[Dict],
                         edges: List[Dict], name: str) -> str:
    """编译含条件分支的工作流"""
    imports = set()
    lines = []
    order = _topological_order(G, nodes)
    input_vars = {}
    var_counter = 0

    for nid in order:
        node = G.nodes[nid]
        ntype = node["type"]
        config = node.get("config", {})
        label = node.get("label", nid)
        var_counter += 1
        var_name = f"result_{var_counter}"

        if ntype == NODE_INPUT:
            lines.append(f"# {label}")
            lines.append(f'{var_name} = input("请输入: ")')
            input_vars[nid] = var_name

        elif ntype == NODE_LLM:
            preds = list(G.predecessors(nid))
            input_val = _resolve_input(preds, input_vars, f"result_{var_counter - 1}")
            model = config.get("model", "gpt-4o")
            temp = config.get("temperature", 0.7)
            prompt = config.get("prompt", "{input}")
            prompt_escaped = prompt.replace('"', '\\"').replace('\n', '\\n')

            lines.append(f"# {label}")
            lines.append(f'prompt = "{prompt_escaped}".format(input={input_val})')
            lines.append(f'{var_name} = bridge.chat(prompt, model="{model}", temperature={temp})')
            input_vars[nid] = var_name

        elif ntype == NODE_CONDITIONAL:
            preds = list(G.predecessors(nid))
            input_val = _resolve_input(preds, input_vars, f"result_{var_counter - 1}")
            condition_field = config.get("condition", "grade")
            branches = config.get("branches", {})

            # 提取条件节点的 LLM 输出中的 grade 字段
            imports.add("import re")
            lines.append(f"# {label}")
            lines.append(f"_raw = str({input_val})")
            lines.append(f'_match = re.search(r"分级[：:]\\s*(\\w+)", _raw)')
            lines.append(f'{var_name} = _match.group(1) if _match else "UNKNOWN"')

            # 为每个分支生成处理逻辑
            branch_items = list(branches.items())
            for i, (branch_val, target_nid) in enumerate(branch_items):
                target_node = G.nodes[target_nid]
                target_label = target_node.get("label", target_nid)
                prefix = "if" if i == 0 else "elif"
                lines.append(f'{prefix} {var_name} == "{branch_val}":')
                lines.append(f'    print("[分支: {branch_val}] {target_label}")')
                if target_node["type"] == NODE_OUTPUT:
                    lines.append(f'    print({input_val})')
            if branches:
                lines.append(f'else:')
                lines.append(f'    print(f"[未知分级: {{{var_name}}}]")')

            input_vars[nid] = var_name

        elif ntype == NODE_OUTPUT:
            preds = list(G.predecessors(nid))
            input_val = _resolve_input(preds, input_vars, f"result_{var_counter - 1}")
            fmt = config.get("output_format", "text")
            lines.append(f"# {label}")
            lines.append(f"print({input_val})")
            input_vars[nid] = var_name

    return _wrap_script("\n".join(lines), imports, name)


def _compile_loop(G: nx.DiGraph, nodes: List[Dict],
                  edges: List[Dict], name: str) -> str:
    """编译含循环的工作流"""
    imports = set()
    lines = []
    order = _topological_order(G, nodes)
    input_vars = {}
    var_counter = 0

    loop_nid = None
    for nid in order:
        if G.nodes[nid]["type"] == NODE_LOOP:
            loop_nid = nid
            break

    for nid in order:
        node = G.nodes[nid]
        ntype = node["type"]
        config = node.get("config", {})
        label = node.get("label", nid)
        var_counter += 1
        var_name = f"result_{var_counter}"

        if ntype == NODE_INPUT:
            lines.append(f"# {label}")
            lines.append(f'{var_name} = input("请输入: ")')
            input_vars[nid] = var_name

        elif ntype == NODE_LLM:
            preds = list(G.predecessors(nid))
            input_val = _resolve_input(preds, input_vars, f"result_{var_counter - 1}")
            model = config.get("model", "gpt-4o")
            temp = config.get("temperature", 0.7)
            prompt = config.get("prompt", "{input}")
            prompt_escaped = prompt.replace('"', '\\"').replace('\n', '\\n')

            lines.append(f"# {label}")
            lines.append(f'prompt = "{prompt_escaped}".format(input={input_val})')
            lines.append(f'{var_name} = bridge.chat(prompt, model="{model}", temperature={temp})')
            input_vars[nid] = var_name

        elif ntype == NODE_LOOP:
            preds = list(G.predecessors(nid))
            input_val = _resolve_input(preds, input_vars, f"result_{var_counter - 1}")
            max_iter = config.get("max_iterations", 10)
            condition = config.get("condition", "True")

            lines.append(f"# {label}")
            lines.append(f"_loop_count = 0")
            lines.append(f"while _loop_count < {max_iter}:")
            lines.append(f"    _loop_count += 1")
            lines.append(f"    _loop_result = bridge.chat(")
            lines.append(f'        f"第{{_loop_count}}轮: {input_val}",')
            lines.append(f'        model="gpt-4o"')
            lines.append(f"    )")
            lines.append(f'    if "STOP" in str(_loop_result):')
            lines.append(f"        break")
            lines.append(f"    {input_val} = _loop_result")
            lines.append(f'{var_name} = {input_val}')
            input_vars[nid] = var_name

        elif ntype == NODE_OUTPUT:
            preds = list(G.predecessors(nid))
            input_val = _resolve_input(preds, input_vars, f"result_{var_counter - 1}")
            lines.append(f"# {label}")
            lines.append(f"print({input_val})")
            input_vars[nid] = var_name

    return _wrap_script("\n".join(lines), imports, name)


def _wrap_script(body: str, imports: List[str], name: str) -> str:
    """包裹生成的代码为完整脚本"""
    header = f'''"""
工作流: {name}
由 iqra Workflow Compiler 自动生成
"""

import os
import sys
import json
'''
    if imports:
        header += "\n" + "\n".join(imports) + "\n"

    main_block = f'''
# ── 初始化 AgentBridge ──
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from modules.intelligence.agent_bridge import AgentBridge
bridge = AgentBridge()

# ── 工作流执行 ──
def run():
{_indent(body, "    ")}

if __name__ == "__main__":
    run()
'''
    return header + main_block


def _indent(text: str, prefix: str) -> str:
    """给多行文本添加缩进前缀"""
    return "\n".join(prefix + line if line.strip() else line
                     for line in text.split("\n"))


def validate_workflow(workflow_json: Dict[str, Any]) -> Tuple[bool, str]:
    """验证工作流 JSON 的有效性。

    Returns:
        (is_valid, error_message)
    """
    nodes = workflow_json.get("nodes", [])
    edges = workflow_json.get("edges", [])

    if not nodes:
        return False, "工作流至少需要一个节点"

    node_ids = {n["id"] for n in nodes}
    valid_types = {NODE_INPUT, NODE_LLM, NODE_TOOL, NODE_CONDITIONAL,
                   NODE_LOOP, NODE_OUTPUT}

    for node in nodes:
        if node.get("type") not in valid_types:
            return False, f"未知节点类型: {node.get('type')} (节点 {node.get('id')})"

    for edge in edges:
        if edge["source"] not in node_ids:
            return False, f"边引用了不存在的源节点: {edge['source']}"
        if edge["target"] not in node_ids:
            return False, f"边引用了不存在的目标节点: {edge['target']}"
        if edge["source"] == edge["target"]:
            return False, f"不能连线到自身: {edge['source']}"

    return True, "OK"


# ── 自检 ──
if __name__ == "__main__":
    from .templates import TEMPLATE_DOC_QA, TEMPLATE_CODE_REVIEW

    for tmpl in [TEMPLATE_DOC_QA, TEMPLATE_CODE_REVIEW]:
        valid, err = validate_workflow(tmpl)
        print(f"[{tmpl['name']}] 验证: {'PASS' if valid else 'FAIL: ' + err}")
        if valid:
            code = compile_workflow(tmpl)
            try:
                compile(code, "<workflow>", "exec")
                print(f"  编译: PASS ({len(code)} 字符)")
            except SyntaxError as e:
                print(f"  编译: FAIL — {e}")
