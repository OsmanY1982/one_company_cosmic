# -*- coding: utf-8 -*-
import json
import os
import re as _re_module
from typing import Optional, Iterator, Callable
from PyQt5.QtCore import QObject, pyqtSignal
from .llm_backend import (BaseLLMBackend, LLMResponse, ToolCall, ProviderConfig, create_backend)
from .tool_registry import ToolRegistry
from .memory_store import MemoryStore
from .smart_memory_adapter import SmartMemoryStore
from .opcclaw_logging import logger
from .rag_context import RAGContextInjector

class ChatEngine(QObject):
    on_tool_start = pyqtSignal(str, dict)
    on_tool_result = pyqtSignal(str, bool, str)
    MAX_TOOL_ROUNDS = 5
    MAX_CONTEXT_MSGS = 40

    def __init__(self, backend, registry=None, system_prompt='', skill_loader=None,
                 memory_store=None, auto_save=True, session_id='default'):
        super().__init__()
        self.backend = backend
        self.registry = registry or ToolRegistry()
        self.system_prompt = system_prompt
        self.skill_loader = skill_loader
        if isinstance(memory_store, SmartMemoryStore):
            self.memory_store = memory_store
            self.smart_memory = memory_store.smart
        elif memory_store is not None:
            self.memory_store = memory_store
            self.smart_memory = None
        else:
            self.memory_store = None
            self.smart_memory = None
        self.auto_save = auto_save
        self.session_id = session_id
        self.obs = None  # ObservableBridge，由 agent_bridge 注入
        self.messages = []
        if self.memory_store:
            self.messages = self.memory_store.load_session(self.session_id)
        self._save_counter = 0
        self.on_thinking = None
        self.initialize_session()
        logger.debug(f'ChatEngine initialized session={session_id} msgs={len(self.messages)}')

    def initialize_session(self) -> None:
        """初始化会话上下文（公开方法，替代原来的私有方法）"""
        if not (self.system_prompt or self.registry.count() > 0 or self.skill_loader):
            return
        parts = []
        if self.system_prompt:
            parts.append(self.system_prompt)
        if self.registry.count() > 0 and not self.system_prompt:
            # 只有在没有外部传入 system_prompt 时才添加默认提示
            tool_names = self.registry.list_tools()
            tool_summary = ', '.join(sorted(tool_names))
            intro = (
                '你是 OPCclaw，一人公司的全能数字员工。\n'
                '\n'
                '核心规则：\n'
                '1. 永远用工具完成任务，不要只是聊天或给建议\n'
                '2. 读写文件用 read_file/write_file，执行代码用 execute_code，搜索用 web_search\n'
                '3. 用户要求做具体操作时，立刻调用对应工具，不要先解释\n'
                '4. 工具返回结果后，基于结果给出分析或下一步行动\n'
                f'5. 可用工具({len(tool_names)}个): {tool_summary}\n'
                '\n'
                '回复风格：中文、简洁、直接、带Emoji。'
            )
            parts.append(intro)
        # 技能索引（仅列技能名，不注入完整内容以节省 token）
        if self.skill_loader:
            try:
                all_skills = self.skill_loader.list_skills()
                if all_skills:
                    skill_names = sorted([s['name'] for s in all_skills])
                    total = len(skill_names)
                    skills_index = (
                        f"[可用技能索引 - 共 {total} 个]\n"
                        f"{', '.join(skill_names)}\n\n"
                        "💡 需要某个技能的详细内容时，调用 inject_skill(技能名) 即可加载。"
                    )
                    parts.append(skills_index)
            except Exception:
                pass
        if self.memory_store:
            personalized = self.memory_store.get_personalized_context()
            if personalized:
                parts.append(f'[User Preferences]\n{personalized}')
        if parts:
            new_sys = {'role': 'system', 'content': '\n\n'.join(parts)}
            if self.messages and self.messages[0]['role'] == 'system':
                self.messages[0] = new_sys
            else:
                self.messages.insert(0, new_sys)
        self._trim_context()

    def _trim_context(self) -> int:
        if len(self.messages) <= self.MAX_CONTEXT_MSGS:
            return 0
        sys_msg = self.messages[0] if (self.messages and self.messages[0]['role'] == 'system') else None
        if sys_msg:
            trimmed = len(self.messages) - self.MAX_CONTEXT_MSGS
            self.messages = [sys_msg] + self.messages[-(self.MAX_CONTEXT_MSGS - 1):]
        else:
            trimmed = len(self.messages) - self.MAX_CONTEXT_MSGS
            self.messages = self.messages[-self.MAX_CONTEXT_MSGS:]
        return trimmed

    def save(self) -> bool:
        if self.memory_store:
            self.memory_store.save_session(self.messages, self.session_id)
            return True
        return False

    def inject_context(self, text: str) -> None:
        if self.messages and self.messages[0]['role'] == 'system':
            self.messages[0]['content'] += f'\n\n{text}'
        else:
            self.messages.insert(0, {'role': 'system', 'content': text})

    def inject_skill(self, skill_name: str) -> bool:
        if not self.skill_loader:
            return False
        ctx = self.skill_loader.get_skill_context(skill_name, include_full=True)
        if ctx and not ctx.startswith('❌'):
            self.inject_context(ctx)
            return True
        return False

    def inject_relevant_skills(self, user_query: str, max_count: int = 5) -> int:
        """根据用户输入自动注入最相关的技能（节省 token 的按需加载）"""
        if not self.skill_loader:
            return 0
        # 先移除之前注入的技能上下文，防止 system prompt 无限增长
        if self.messages and self.messages[0]['role'] == 'system':
            content = self.messages[0]['content']
            # 移除之前注入的技能块（以 ## 📖 开头）
            import re
            content = re.sub(r'\n## 📖 技能：.*?(?=\n## |\Z)', '', content, flags=re.DOTALL)
            self.messages[0]['content'] = content
        skills = self.skill_loader.auto_select_skills_for_query(user_query, max_count=max_count)
        injected = 0
        for s in skills:
            name = s.get('name', '')
            ctx = self.skill_loader.get_skill_context(name, include_full=False)
            if ctx and not ctx.startswith('❌'):
                self.inject_context(ctx)
                injected += 1
        return injected

    def inject_workspace_context(self, user_message: str) -> bool:
        """自动注入工作区代码上下文 + 项目规则（Phase 2 RAG + OPCCLAW.md）"""
        injector = RAGContextInjector()
        if not injector.enabled or not injector.has_project:
            return False
        try:
            context = injector.indexer.get_context(user_message, max_chars=4000, top_k=5)

            # 注入项目规则（OPCCLAW.md — 对标 CLAUDE.md）
            rules = injector.get_project_rules()
            if rules:
                context = rules + "\n\n" + context if context else rules

            if not context:
                return False
            # 清除旧的 workspace 上下文块，然后注入新的
            if self.messages and self.messages[0]['role'] == 'system':
                content = self.messages[0]['content']
                content = _re_module.sub(
                    r'\n<workspace_context>.*?</workspace_context>\n', '', content, flags=_re_module.DOTALL
                )
                self.messages[0]['content'] = content
            self.inject_context(f'<workspace_context>\n{context}\n</workspace_context>')
            return True
        except Exception as e:
            logger.warning(f'Workspace context injection failed: {e}')
            return False

    def refresh_skills(self) -> int:
        if not self.skill_loader:
            return 0
        all_skills = self.skill_loader.list_skills()
        count = len(all_skills)
        if count > 0 and self.messages and self.messages[0]['role'] == 'system':
            skill_names = sorted([s['name'] for s in all_skills])
            skills_index = (
                f"[可用技能索引 - 共 {count} 个]\n"
                f"{', '.join(skill_names)}\n\n"
                "💡 需要某个技能的详细内容时，调用 inject_skill(技能名) 即可加载。"
            )
            base = self.messages[0]['content']
            marker = '[可用技能索引'
            if marker in base:
                base = base[:base.index(marker)]
            self.messages[0]['content'] = base.strip() + '\n\n' + skills_index
        return count

    def chat(self, user_message: str) -> str:
        logger.debug(f'chat() called msg_len={len(user_message)}')
        if self.memory_store:
            self.memory_store.on_turn_start(turn_number=len(self.messages), message=user_message)
        if self.obs:
            self.obs.trace_begin(session_id=self.session_id, user_message=user_message)
        self.messages.append({'role': 'user', 'content': user_message})
        self._trim_context()
        # 自动注入与当前问题最相关的技能（按需加载，节省 token）
        if self.skill_loader:
            try:
                self.inject_relevant_skills(user_message, max_count=5)
            except Exception as e:
                logger.warning(f'Skill auto-inject failed: {e}')
        # 自动注入工作区代码上下文（Phase 2 RAG）
        self.inject_workspace_context(user_message)
        tools = self.registry.to_openai_tools() if self.registry.count() > 0 else None
        
        # 强制使用工具：如果用户消息包含操作关键词，强制 tool_choice="required"
        force_tools = self._should_force_tools(user_message)
        
        for _ in range(self.MAX_TOOL_ROUNDS):
            try:
                if force_tools and tools:
                    response = self.backend.chat(self.messages, tools, tool_choice="required")
                else:
                    response = self.backend.chat(self.messages, tools)
            except Exception as e:
                logger.error(f'LLM API failed: {e}', exc_info=True)
                self.messages.append({'role': 'assistant', 'content': f'Sorry, AI service unavailable: {e}'})
                self._maybe_save()
                if self.obs:
                    self.obs.trace_end()
                return f'Sorry, AI service unavailable: {e}'
            if not response.tool_calls:
                # 如果强制使用工具但 LLM 没调用，添加提示并重试
                if force_tools and tools:
                    self.messages.append({'role': 'system', 'content': '你必须使用工具来完成用户的请求。不要只是聊天，请调用合适的工具。'})
                    continue
                assistant_msg = response.content or ''
                self.messages.append({'role': 'assistant', 'content': assistant_msg})
                if self.auto_save and self.memory_store:
                    self.memory_store.save_session(self.messages, self.session_id)
                if self.obs:
                    self.obs.trace_end()
                return assistant_msg
            assistant_msg = {'role': 'assistant', 'content': None, 'tool_calls': []}
            for tc in response.tool_calls:
                self.on_tool_start.emit(tc.name, tc.arguments)
                try:
                    result = self.registry.execute(tc)
                except Exception as e:
                    logger.error(f'Tool failed {tc.name}: {e}', exc_info=True)
                    result = {'success': False, 'error': f'Tool error: {e}'}
                self.on_tool_result.emit(tc.name, result['success'],
                    str(result.get('result', result.get('error', '')))[:200])
                try:
                    assistant_msg['tool_calls'].append({'id': tc.id, 'type': 'function',
                        'function': {'name': tc.name, 'arguments': json.dumps(tc.arguments, ensure_ascii=False)}})
                except (TypeError, ValueError) as e:
                    logger.warning(f'Serialization failed: {e}')
                    continue
                try:
                    tool_msg = {'role': 'tool', 'tool_call_id': tc.id,
                        'content': json.dumps(result, ensure_ascii=False)}
                    self.messages.append(tool_msg)
                except (TypeError, ValueError) as e:
                    logger.warning(f'Result serialization failed: {e}')
                    self.messages.append({'role': 'tool', 'tool_call_id': tc.id,
                        'content': json.dumps({'success': False, 'error': 'Result cannot be serialized'}, ensure_ascii=False)})
            self.messages.append(assistant_msg)
        if self.auto_save and self.memory_store:
            self.memory_store.save_session(self.messages, self.session_id)
        if self.obs:
            self.obs.trace_end()
        return 'Sorry, processing encountered a loop. Please try a different approach.'

    def _should_force_tools(self, user_message: str) -> bool:
        """判断是否应该强制使用工具。跳过纯能力询问（以"吗？"/"吗"/"？"结尾的寒暄句）"""
        msg_stripped = user_message.strip()
        # 纯元问题（"你能...吗？""你支持...?"）不强制工具，交给 LLM 自然决策
        if msg_stripped.endswith(('吗？', '吗', '？')) or msg_stripped.endswith('?'):
            return False
        force_keywords = [
            '执行', '运行', '调用', '使用', '打开', '关闭', '创建', '删除',
            '读取', '写入', '修改', '搜索', '查询', '分析', '计算',
            'file', 'read', 'write', 'execute', 'run', 'search', 'query',
            'create', 'delete', 'open', 'close', 'modify', 'analyze',
        ]
        msg_lower = user_message.lower()
        return any(kw in msg_lower for kw in force_keywords)

    def chat_stream(self, user_message: str) -> Iterator[str]:
        logger.debug(f'chat_stream() called msg_len={len(user_message)} tools={self.registry.count()}')
        if self.memory_store:
            self.memory_store.on_turn_start(turn_number=len(self.messages), message=user_message)
        if self.obs:
            self.obs.trace_begin(session_id=self.session_id, user_message=user_message)
        self.messages.append({'role': 'user', 'content': user_message})
        self._trim_context()
        # 自动注入与当前问题最相关的技能
        if self.skill_loader:
            try:
                self.inject_relevant_skills(user_message, max_count=5)
            except Exception as e:
                logger.warning(f'Skill auto-inject failed: {e}')
        # 自动注入工作区代码上下文（Phase 2 RAG）
        self.inject_workspace_context(user_message)
        self._save_counter += 1
        tools = self.registry.to_openai_tools() if self.registry.count() > 0 else None
        force_tools = self._should_force_tools(user_message)
        
        for round_idx in range(self.MAX_TOOL_ROUNDS):
            if self.on_thinking:
                self.on_thinking()
            if tools:
                try:
                    import datetime, sys
                    print(f"[DIAG][{datetime.datetime.now().strftime('%H:%M:%S')}] ChatEngine.chat_stream round={round_idx} calling backend.chat()...", flush=True)
                    if force_tools:
                        check_response = self.backend.chat(self.messages, tools, tool_choice="required")
                    else:
                        check_response = self.backend.chat(self.messages, tools)
                    print(f"[DIAG][{datetime.datetime.now().strftime('%H:%M:%S')}] ChatEngine.chat_stream round={round_idx} backend.chat() returned — content_len={len(check_response.content or '')}, tool_calls={'YES' if check_response.tool_calls else 'NO'}", flush=True)
                except Exception as e:
                    logger.error(f'LLM API failed: {e}', exc_info=True)
                    self._maybe_save()
                    if self.obs:
                        self.obs.trace_end()
                    yield '\nSorry, AI service unavailable: {}\n'.format(e)
                    return
                if check_response.tool_calls:
                    for tc in check_response.tool_calls:
                        self.on_tool_start.emit(tc.name, tc.arguments)
                        yield f'\n[Calling tool: {tc.name}...]\n'
                        try:
                            result = self.registry.execute(tc)
                        except Exception as e:
                            logger.error(f'Tool failed {tc.name}: {e}', exc_info=True)
                            result = {'success': False, 'error': f'Tool error: {e}'}
                        self.on_tool_result.emit(tc.name, result['success'],
                            str(result.get('result', result.get('error', '')))[:200])
                        status = 'OK' if result['success'] else 'Failed'
                        yield f'[{tc.name}: {status}]\n'
                        try:
                            assistant_msg = {'role': 'assistant', 'content': None, 'tool_calls': [{
                                'id': tc.id, 'type': 'function',
                                'function': {'name': tc.name, 'arguments': json.dumps(tc.arguments, ensure_ascii=False)}
                            }]}
                            tool_msg = {'role': 'tool', 'tool_call_id': tc.id,
                                'content': json.dumps(result, ensure_ascii=False)}
                            self.messages.append(assistant_msg)
                            self.messages.append(tool_msg)
                        except (TypeError, ValueError) as e:
                            logger.warning(f'Serialization failed: {e}')
                    continue
                return_text = check_response.content or ''
                self.messages.append({'role': 'assistant', 'content': return_text})
                self._maybe_save()
                if self.obs:
                    self.obs.trace_end()
                yield return_text
                if check_response.usage:
                    yield json.dumps({'usage': check_response.usage}, ensure_ascii=False)
                return
            try:
                accumulated = ''
                last_usage = {}
                for chunk in self.backend.chat_stream(self.messages):
                    if chunk.content:
                        accumulated += chunk.content
                        yield chunk.content
                    if hasattr(chunk, 'usage') and chunk.usage:
                        last_usage = chunk.usage
                # Fallback: streaming 返回空时降级到非 streaming 调用（某些本地模型上下文较长时 stream 会直接返回 0 chunk）
                if not accumulated:
                    try:
                        fallback_resp = self.backend.chat(self.messages, None)
                        if fallback_resp.content:
                            accumulated = fallback_resp.content
                            yield accumulated
                            if fallback_resp.usage:
                                last_usage = fallback_resp.usage
                    except Exception:
                        pass
                self.messages.append({'role': 'assistant', 'content': accumulated})
                self._maybe_save()
                if self.obs:
                    self.obs.trace_end()
                if last_usage:
                    yield json.dumps({'usage': last_usage}, ensure_ascii=False)
                return
            except Exception as e:
                logger.error(f'Streaming failed: {e}', exc_info=True)
                self.messages.append({'role': 'assistant', 'content': f'Sorry, AI service unavailable: {e}'})
                self._maybe_save()
                if self.obs:
                    self.obs.trace_end()
                yield f'\nSorry, AI service unavailable: {e}\n'
                return
        self._maybe_save()
        self._trim_context()
        yield '\n[Max processing rounds reached, please simplify your question]'

    def _maybe_save(self):
        if self.auto_save and self.memory_store:
            self.memory_store.save_session(self.messages, self.session_id)

    def reset(self) -> None:
        if self.auto_save and self.memory_store:
            self.memory_store.on_session_end(self.session_id)
            self.memory_store.save_session([], self.session_id)
        self.messages = []
        self.initialize_session()

    def get_history(self) -> list[dict]:
        return list(self.messages)

    def message_count(self) -> int:
        return len(self.messages)
