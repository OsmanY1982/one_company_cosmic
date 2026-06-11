# OPCclaw 源码全书
> 自动生成于 2026-06-11 13:00
> 共 179 个模块，每个 `.py` 文件独立为一个文档

---

## 目录结构

```
.
├── agent/
│   ├── transports/
│   │   ├── __init__.py
│   │   ├── anthropic.py
│   │   ├── base.py
│   │   ├── bedrock.py
│   │   ├── chat_completions.py
│   │   ├── codex.py
│   │   └── types.py
│   ├── __init__.py
│   ├── account_usage.py
│   ├── anthropic_adapter.py
│   ├── auxiliary_client.py
│   ├── bedrock_adapter.py
│   ├── codex_responses_adapter.py
│   ├── context_compressor.py
│   ├── context_engine.py
│   ├── context_references.py
│   ├── copilot_acp_client.py
│   ├── credential_pool.py
│   ├── credential_sources.py
│   ├── curator.py
│   ├── curator_backup.py
│   ├── display.py
│   ├── error_classifier.py
│   ├── file_safety.py
│   ├── gemini_cloudcode_adapter.py
│   ├── gemini_native_adapter.py
│   ├── gemini_schema.py
│   ├── google_code_assist.py
│   ├── google_oauth.py
│   ├── i18n.py
│   ├── image_gen_provider.py
│   ├── image_gen_registry.py
│   ├── image_routing.py
│   ├── insights.py
│   ├── lmstudio_reasoning.py
│   ├── manual_compression_feedback.py
│   ├── memory_manager.py
│   ├── memory_provider.py
│   ├── model_metadata.py
│   ├── models_dev.py
│   ├── moonshot_schema.py
│   ├── nous_rate_guard.py
│   ├── onboarding.py
│   ├── prompt_builder.py
│   ├── prompt_caching.py
│   ├── rate_limit_tracker.py
│   ├── redact.py
│   ├── retry_utils.py
│   ├── shell_hooks.py
│   ├── skill_commands.py
│   ├── skill_preprocessing.py
│   ├── skill_utils.py
│   ├── subdirectory_hints.py
│   ├── think_scrubber.py
│   ├── title_generator.py
│   ├── tool_guardrails.py
│   ├── trajectory.py
│   └── usage_pricing.py
├── ai_tools/
├── core/
│   ├── __init__.py
│   ├── agent_delegate.py
│   ├── agent_loop.py
│   ├── chat_engine.py
│   ├── clarify_system.py
│   ├── cloud_sync.py
│   ├── code_executor.py
│   ├── code_intel.py
│   ├── collaboration_client.py
│   ├── config_validator.py
│   ├── core_engine.py
│   ├── enhanced_core.py
│   ├── enhanced_hermes_bridge.py
│   ├── git_ops.py
│   ├── llm_backend.py
│   ├── memory.py
│   ├── memory_store.py
│   ├── model_status.py
│   ├── model_status_manager.py
│   ├── multi_model.py
│   ├── multi_model_chat_engine.py
│   ├── opcclaw_logging.py
│   ├── patch_engine.py
│   ├── performance_monitor.py
│   ├── process_manager.py
│   ├── rag_context.py
│   ├── secure_storage.py
│   ├── semantic_search.py
│   ├── session_search.py
│   ├── skill_loader.py
│   ├── skill_system.py
│   ├── smart_memory.py
│   ├── smart_memory_adapter.py
│   ├── supabase_client.py
│   ├── super_intelligence.py
│   ├── sync_bridge.py
│   ├── task_scheduler.py
│   ├── test_phase2.py
│   ├── todo_system.py
│   ├── token_optimizer.py
│   ├── token_saver.py
│   ├── tool_registry.py
│   ├── web_search.py
│   └── workspace_indexer.py
├── data/
│   ├── opcclaw/
│   │   ├── exports/
│   │   ├── memory/
│   │   ├── metrics/
│   │   ├── sessions/
│   │   ├── smart_memory/
│   │   │   ├── preferences/
│   │   │   ├── session_state/
│   │   │   ├── snapshots/
│   ├── process_logs/
│   ├── __init__.py
├── logs/
├── modules/
│   ├── __init__.py
│   ├── chat_window.py
│   ├── config_manager.py
│   ├── git_panel.py
│   ├── login_dialog.py
│   ├── message_bubble.py
│   ├── sidebar.py
│   ├── styled_widgets.py
│   ├── voice_manager.py
│   └── widgets.py
├── plugins/
│   ├── code_executor/
│   │   └── __init__.py
│   ├── context_engine/
│   │   └── __init__.py
│   ├── disk-cleanup/
│   │   ├── __init__.py
│   │   ├── disk_cleanup.py
│   ├── example-dashboard/
│   │   └── dashboard/
│   │       └── plugin_api.py
│   ├── file_handler/
│   │   └── __init__.py
│   ├── google_meet/
│   │   ├── node/
│   │   │   ├── __init__.py
│   │   │   ├── cli.py
│   │   │   ├── client.py
│   │   │   ├── protocol.py
│   │   │   ├── registry.py
│   │   │   └── server.py
│   │   ├── realtime/
│   │   │   ├── __init__.py
│   │   │   └── openai_client.py
│   │   ├── __init__.py
│   │   ├── audio_bridge.py
│   │   ├── cli.py
│   │   ├── meet_bot.py
│   │   ├── process_manager.py
│   │   └── tools.py
│   ├── hermes-achievements/
│   │   ├── dashboard/
│   │   │   └── plugin_api.py
│   │   ├── docs/
│   │   │   ├── assets/
│   │   ├── tests/
│   │   │   └── test_achievement_engine.py
│   ├── image_gen/
│   │   ├── openai/
│   │   │   ├── __init__.py
│   │   ├── openai-codex/
│   │   │   ├── __init__.py
│   │   └── xai/
│   │       ├── __init__.py
│   ├── image_vision/
│   │   └── __init__.py
│   ├── kanban/
│   │   ├── dashboard/
│   │   │   └── plugin_api.py
│   │   └── systemd/
│   ├── memory/
│   │   ├── byterover/
│   │   │   ├── __init__.py
│   │   ├── hindsight/
│   │   │   ├── __init__.py
│   │   ├── holographic/
│   │   │   ├── __init__.py
│   │   │   ├── holographic.py
│   │   │   ├── retrieval.py
│   │   │   └── store.py
│   │   ├── honcho/
│   │   │   ├── __init__.py
│   │   │   ├── cli.py
│   │   │   ├── client.py
│   │   │   └── session.py
│   │   ├── mem0/
│   │   │   ├── __init__.py
│   │   ├── openviking/
│   │   │   ├── __init__.py
│   │   ├── retaindb/
│   │   │   ├── __init__.py
│   │   ├── supermemory/
│   │   │   ├── __init__.py
│   │   └── __init__.py
│   ├── model-providers/
│   │   ├── ai-gateway/
│   │   │   ├── __init__.py
│   │   ├── alibaba/
│   │   │   ├── __init__.py
│   │   ├── alibaba-coding-plan/
│   │   │   ├── __init__.py
│   │   ├── anthropic/
│   │   │   ├── __init__.py
│   │   ├── arcee/
│   │   │   ├── __init__.py
│   │   ├── azure-foundry/
│   │   │   ├── __init__.py
│   │   ├── bedrock/
│   │   │   ├── __init__.py
│   │   ├── copilot/
│   │   │   ├── __init__.py
│   │   ├── copilot-acp/
│   │   │   ├── __init__.py
│   │   ├── custom/
│   │   │   ├── __init__.py
│   │   ├── deepseek/
│   │   │   ├── __init__.py
│   │   ├── gemini/
│   │   │   ├── __init__.py
│   │   ├── gmi/
│   │   │   ├── __init__.py
│   │   ├── huggingface/
│   │   │   ├── __init__.py
│   │   ├── kilocode/
│   │   │   ├── __init__.py
│   │   ├── kimi-coding/
│   │   │   ├── __init__.py
│   │   ├── minimax/
│   │   │   ├── __init__.py
│   │   ├── nous/
│   │   │   ├── __init__.py
│   │   ├── nvidia/
│   │   │   ├── __init__.py
│   │   ├── ollama-cloud/
│   │   │   ├── __init__.py
│   │   ├── openai-codex/
│   │   │   ├── __init__.py
│   │   ├── opencode-zen/
│   │   │   ├── __init__.py
│   │   ├── openrouter/
│   │   │   ├── __init__.py
│   │   ├── qwen-oauth/
│   │   │   ├── __init__.py
│   │   ├── stepfun/
│   │   │   ├── __init__.py
│   │   ├── xai/
│   │   │   ├── __init__.py
│   │   ├── xiaomi/
│   │   │   ├── __init__.py
│   │   ├── zai/
│   │   │   ├── __init__.py
│   ├── multi_model/
│   │   └── __init__.py
│   ├── observability/
│   │   └── langfuse/
│   │       ├── __init__.py
│   ├── platforms/
│   │   ├── google_chat/
│   │   │   ├── __init__.py
│   │   │   ├── adapter.py
│   │   │   ├── oauth.py
│   │   ├── irc/
│   │   │   ├── __init__.py
│   │   │   ├── adapter.py
│   │   └── teams/
│   │       ├── __init__.py
│   │       ├── adapter.py
│   ├── spotify/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── tools.py
│   ├── strike-freedom-cockpit/
│   │   ├── dashboard/
│   │   ├── theme/
│   ├── teams_pipeline/
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── meetings.py
│   │   ├── models.py
│   │   ├── pipeline.py
│   │   ├── runtime.py
│   │   ├── store.py
│   │   └── subscriptions.py
│   ├── web_search/
│   │   └── __init__.py
│   ├── __init__.py
├── providers/
│   ├── __init__.py
│   ├── base.py
├── skills/
│   ├── apple/
│   │   ├── apple-notes/
│   │   ├── apple-reminders/
│   │   ├── findmy/
│   │   ├── imessage/
│   │   ├── macos-computer-use/
│   ├── autonomous-ai-agents/
│   │   ├── claude-code/
│   │   ├── codex/
│   │   ├── hermes-agent/
│   │   ├── opencode/
│   ├── check-code-changes/
│   ├── creative/
│   │   ├── architecture-diagram/
│   │   │   ├── templates/
│   │   ├── ascii-art/
│   │   ├── ascii-video/
│   │   │   ├── references/
│   │   ├── baoyu-comic/
│   │   │   ├── references/
│   │   │   │   ├── art-styles/
│   │   │   │   ├── layouts/
│   │   │   │   ├── presets/
│   │   │   │   ├── tones/
│   │   ├── baoyu-infographic/
│   │   │   ├── references/
│   │   │   │   ├── layouts/
│   │   │   │   ├── styles/
│   │   ├── claude-design/
│   │   ├── comfyui/
│   │   │   ├── references/
│   │   │   ├── scripts/
│   │   │   │   ├── _common.py
│   │   │   │   ├── auto_fix_deps.py
│   │   │   │   ├── check_deps.py
│   │   │   │   ├── extract_schema.py
│   │   │   │   ├── fetch_logs.py
│   │   │   │   ├── hardware_check.py
│   │   │   │   ├── health_check.py
│   │   │   │   ├── run_batch.py
│   │   │   │   ├── run_workflow.py
│   │   │   │   └── ws_monitor.py
│   │   │   ├── tests/
│   │   │   │   ├── conftest.py
│   │   │   │   ├── test_check_deps.py
│   │   │   │   ├── test_cloud_integration.py
│   │   │   │   ├── test_common.py
│   │   │   │   ├── test_extract_schema.py
│   │   │   │   └── test_run_workflow.py
│   │   │   ├── workflows/
│   │   ├── creative-ideation/
│   │   │   ├── references/
│   │   ├── design-md/
│   │   │   ├── templates/
│   │   ├── excalidraw/
│   │   │   ├── references/
│   │   │   ├── scripts/
│   │   │   │   └── upload.py
│   │   ├── humanizer/
│   │   ├── manim-video/
│   │   │   ├── references/
│   │   │   ├── scripts/
│   │   ├── p5js/
│   │   │   ├── references/
│   │   │   ├── scripts/
│   │   │   ├── templates/
│   │   ├── pixel-art/
│   │   │   ├── references/
│   │   │   ├── scripts/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── palettes.py
│   │   │   │   ├── pixel_art.py
│   │   │   │   └── pixel_art_video.py
│   │   ├── popular-web-designs/
│   │   │   ├── templates/
│   │   ├── pretext/
│   │   │   ├── references/
│   │   │   ├── templates/
│   │   ├── sketch/
│   │   ├── songwriting-and-ai-music/
│   │   ├── touchdesigner-mcp/
│   │   │   ├── references/
│   │   │   ├── scripts/
│   ├── data-science/
│   │   ├── jupyter-live-kernel/
│   ├── devops/
│   │   ├── kanban-orchestrator/
│   │   ├── kanban-worker/
│   │   └── webhook-subscriptions/
│   ├── diagramming/
│   ├── dogfood/
│   │   ├── references/
│   │   ├── templates/
│   ├── domain/
│   ├── email/
│   │   ├── himalaya/
│   │   │   ├── references/
│   ├── flybook_bot/
│   │   ├── config.py
│   │   ├── flybook_skill.py
│   │   ├── server.py
│   │   ├── server_minimal.py
│   │   ├── server_simple.py
│   │   └── test_server.py
│   ├── gaming/
│   │   ├── minecraft-modpack-server/
│   │   ├── pokemon-player/
│   ├── gifs/
│   ├── git-commit/
│   ├── github/
│   │   ├── codebase-inspection/
│   │   ├── github-auth/
│   │   │   ├── scripts/
│   │   ├── github-code-review/
│   │   │   ├── references/
│   │   ├── github-issues/
│   │   │   ├── templates/
│   │   ├── github-pr-workflow/
│   │   │   ├── references/
│   │   │   ├── templates/
│   │   ├── github-repo-management/
│   │   │   ├── references/
│   ├── index-cache/
│   ├── inference-sh/
│   ├── mcp/
│   │   ├── native-mcp/
│   ├── media/
│   │   ├── gif-search/
│   │   ├── heartmula/
│   │   ├── songsee/
│   │   ├── spotify/
│   │   ├── youtube-content/
│   │   │   ├── references/
│   │   │   ├── scripts/
│   │   │   │   └── fetch_transcript.py
│   ├── mlops/
│   │   ├── evaluation/
│   │   │   ├── lm-evaluation-harness/
│   │   │   │   ├── references/
│   │   │   ├── weights-and-biases/
│   │   │   │   ├── references/
│   │   ├── huggingface-hub/
│   │   ├── inference/
│   │   │   ├── llama-cpp/
│   │   │   │   ├── references/
│   │   │   ├── obliteratus/
│   │   │   │   ├── references/
│   │   │   │   ├── templates/
│   │   │   ├── vllm/
│   │   │   │   ├── references/
│   │   ├── models/
│   │   │   ├── audiocraft/
│   │   │   │   ├── references/
│   │   │   ├── segment-anything/
│   │   │   │   ├── references/
│   │   ├── research/
│   │   │   ├── dspy/
│   │   │   │   ├── references/
│   │   ├── training/
│   │   ├── vector-databases/
│   ├── model-switch-automation/
│   ├── note-taking/
│   │   ├── obsidian/
│   ├── productivity/
│   │   ├── airtable/
│   │   ├── google-workspace/
│   │   │   ├── references/
│   │   │   ├── scripts/
│   │   │   │   ├── _hermes_home.py
│   │   │   │   ├── google_api.py
│   │   │   │   ├── gws_bridge.py
│   │   │   │   └── setup.py
│   │   ├── linear/
│   │   │   ├── scripts/
│   │   │   │   └── linear_api.py
│   │   ├── maps/
│   │   │   ├── scripts/
│   │   │   │   └── maps_client.py
│   │   ├── nano-pdf/
│   │   ├── notion/
│   │   │   ├── references/
│   │   ├── ocr-and-documents/
│   │   │   ├── scripts/
│   │   │   │   ├── extract_marker.py
│   │   │   │   └── extract_pymupdf.py
│   │   ├── powerpoint/
│   │   │   ├── scripts/
│   │   │   │   ├── office/
│   │   │   │   │   ├── helpers/
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   ├── merge_runs.py
│   │   │   │   │   │   └── simplify_redlines.py
│   │   │   │   │   ├── schemas/
│   │   │   │   │   │   ├── ecma/
│   │   │   │   │   │   │   └── fourth-edition/
│   │   │   │   │   │   ├── ISO-IEC29500-4_2016/
│   │   │   │   │   │   ├── mce/
│   │   │   │   │   │   └── microsoft/
│   │   │   │   │   └── pack.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── add_slide.py
│   │   │   │   └── clean.py
│   │   ├── teams-meeting-pipeline/
│   ├── qclaw_skills/
│   │   ├── aippt/
│   │   │   ├── scripts/
│   │   ├── baidu-search/
│   │   │   ├── references/
│   │   │   ├── scripts/
│   │   │   │   └── search.py
│   │   ├── file-manager/
│   │   │   ├── references/
│   │   │   ├── scripts/
│   │   │   │   ├── batch_rename.py
│   │   │   │   ├── deduplicate.py
│   │   │   │   ├── organize.py
│   │   │   │   ├── sync.py
│   │   │   │   └── utils.py
│   │   ├── git-workflow/
│   │   │   ├── references/
│   │   │   ├── scripts/
│   │   ├── kdocs/
│   │   │   ├── references/
│   │   │   │   ├── aippt/
│   │   │   │   ├── dbsheet/
│   │   │   │   ├── drive/
│   │   │   │   ├── kwiki/
│   │   │   │   ├── otl/
│   │   │   │   ├── pdf/
│   │   │   │   ├── sheet/
│   │   │   │   ├── workflows/
│   │   │   │   ├── wpp/
│   │   │   │   ├── wps/
│   │   │   ├── scripts/
│   │   ├── planning-with-files/
│   │   │   ├── references/
│   │   │   ├── scripts/
│   │   │   │   └── session-catchup.py
│   │   │   ├── templates/
│   │   ├── video-image-file-analysis/
│   │   │   ├── scripts/
│   │   │   │   ├── vision.py
│   │   │   │   └── vision_manager.py
│   │   ├── web-browsing/
│   │   │   ├── references/
│   │   │   ├── scripts/
│   │   │   │   └── search_web.py
│   │   ├── web-search/
│   │   │   ├── scripts/
│   │   │   │   └── search.py
│   │   ├── webscraper-v2/
│   │   │   └── webscraper.py
│   │   └── wecom-weisheng-scrm/
│   │       ├── references/
│   │       ├── scripts/
│   │       │   ├── api_client.py
│   │       │   ├── chat_mode.py
│   │       │   ├── claw_client.py
│   │       │   ├── environment.py
│   │       │   ├── file_utils.py
│   │       │   ├── get_access_token.py
│   │       │   ├── identity_manager.py
│   │       │   ├── raw_fetcher.py
│   │       │   ├── scrm.py
│   │       │   └── utils.py
│   ├── red-teaming/
│   │   └── godmode/
│   │       ├── references/
│   │       ├── scripts/
│   │       │   ├── auto_jailbreak.py
│   │       │   ├── godmode_race.py
│   │       │   ├── load_godmode.py
│   │       │   └── parseltongue.py
│   │       ├── templates/
│   ├── research/
│   │   ├── arxiv/
│   │   │   ├── scripts/
│   │   │   │   └── search_arxiv.py
│   │   ├── blogwatcher/
│   │   ├── llm-wiki/
│   │   ├── polymarket/
│   │   │   ├── references/
│   │   │   ├── scripts/
│   │   │   │   └── polymarket.py
│   │   ├── research-paper-writing/
│   │   │   ├── references/
│   │   │   ├── templates/
│   │   │   │   ├── aaai2026/
│   │   │   │   ├── acl/
│   │   │   │   ├── colm2025/
│   │   │   │   ├── iclr2026/
│   │   │   │   ├── icml2026/
│   │   │   │   ├── neurips2025/
│   ├── smart-home/
│   │   ├── openhue/
│   ├── smart_memory/
│   │   ├── package_skill.py
│   ├── social-media/
│   │   ├── xurl/
│   ├── software-development/
│   │   ├── debugging-hermes-tui-commands/
│   │   ├── hermes-agent-skill-authoring/
│   │   ├── node-inspect-debugger/
│   │   ├── plan/
│   │   ├── python-debugpy/
│   │   ├── requesting-code-review/
│   │   ├── spike/
│   │   ├── subagent-driven-development/
│   │   │   ├── references/
│   │   ├── systematic-debugging/
│   │   ├── test-driven-development/
│   │   └── writing-plans/
│   ├── yuanbao/
│   ├── __init__.py
│   └── dual_ai.py
├── tests/
│   ├── test_chat_data/
│   │   ├── memory/
│   │   ├── sessions/
│   │   └── smart_memory/
│   │       ├── preferences/
│   │       ├── session_state/
│   │       └── snapshots/
│   ├── test_mem_data/
│   │   ├── memory/
│   │   ├── sessions/
│   │   └── smart_memory/
│   │       ├── preferences/
│   │       ├── session_state/
│   │       ├── snapshots/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_core_modules.py
│   └── test_scraper.py
├── tools/
│   ├── browser_providers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── browser_use.py
│   │   ├── browserbase.py
│   │   └── firecrawl.py
│   ├── builtin/
│   │   ├── __init__.py
│   │   ├── code_tools.py
│   │   ├── developer_tools.py
│   │   ├── git_tools.py
│   │   └── system_tools.py
│   ├── computer_use/
│   │   ├── __init__.py
│   │   ├── backend.py
│   │   ├── cua_backend.py
│   │   ├── schema.py
│   │   └── tool.py
│   ├── environments/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── daytona.py
│   │   ├── docker.py
│   │   ├── file_sync.py
│   │   ├── local.py
│   │   ├── managed_modal.py
│   │   ├── modal.py
│   │   ├── modal_utils.py
│   │   ├── singularity.py
│   │   ├── ssh.py
│   │   └── vercel_sandbox.py
│   ├── neutts_samples/
│   ├── web_providers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── brave_free.py
│   │   ├── ddgs.py
│   │   └── searxng.py
│   ├── __init__.py
│   ├── alert_tools.py
│   ├── analysis_tools.py
│   ├── ansi_strip.py
│   ├── approval.py
│   ├── automation_tools.py
│   ├── binary_extensions.py
│   ├── browser_camofox.py
│   ├── browser_camofox_state.py
│   ├── browser_cdp_tool.py
│   ├── browser_dialog_tool.py
│   ├── browser_supervisor.py
│   ├── browser_tool.py
│   ├── budget_config.py
│   ├── business_tools.py
│   ├── checkpoint_manager.py
│   ├── clarify_tool.py
│   ├── code_execution_tool.py
│   ├── computer_use_tool.py
│   ├── credential_files.py
│   ├── crm_tools.py
│   ├── cronjob_tools.py
│   ├── data_import_tools.py
│   ├── debug_helpers.py
│   ├── delegate_tool.py
│   ├── discord_tool.py
│   ├── doc_tools.py
│   ├── env_passthrough.py
│   ├── export_tools.py
│   ├── feishu_doc_tool.py
│   ├── feishu_drive_tool.py
│   ├── file_operations.py
│   ├── file_state.py
│   ├── file_tools.py
│   ├── finance_analysis_tools.py
│   ├── fuzzy_match.py
│   ├── homeassistant_tool.py
│   ├── hr_tools.py
│   ├── image_generation_tool.py
│   ├── interrupt.py
│   ├── inventory_tools.py
│   ├── kanban_tools.py
│   ├── local_dev_tools.py
│   ├── managed_tool_gateway.py
│   ├── marketing_tools.py
│   ├── mcp_oauth.py
│   ├── mcp_oauth_manager.py
│   ├── mcp_tool.py
│   ├── memory_tool.py
│   ├── microsoft_graph_auth.py
│   ├── microsoft_graph_client.py
│   ├── mixture_of_agents_tool.py
│   ├── neutts_synth.py
│   ├── openrouter_client.py
│   ├── osv_check.py
│   ├── patch_parser.py
│   ├── path_security.py
│   ├── process_registry.py
│   ├── procurement_tools.py
│   ├── project_management.py
│   ├── registry.py
│   ├── rl_training_tool.py
│   ├── scheduling_tools.py
│   ├── schema_sanitizer.py
│   ├── self_monitor.py
│   ├── send_message_tool.py
│   ├── session_search_tool.py
│   ├── skill_manager_tool.py
│   ├── skill_provenance.py
│   ├── skill_usage.py
│   ├── skills_guard.py
│   ├── skills_hub.py
│   ├── skills_sync.py
│   ├── skills_tool.py
│   ├── slash_confirm.py
│   ├── smart_report_tools.py
│   ├── template_tools.py
│   ├── terminal_tool.py
│   ├── tirith_security.py
│   ├── todo_tool.py
│   ├── tool_backend_helpers.py
│   ├── tool_output_limits.py
│   ├── tool_result_storage.py
│   ├── transcription_tools.py
│   ├── tts_tool.py
│   ├── url_safety.py
│   ├── vision_tools.py
│   ├── voice_mode.py
│   ├── web_search_tools.py
│   ├── web_tools.py
│   ├── website_policy.py
│   ├── xai_http.py
│   └── yuanbao_tools.py
├── __init__.py
├── conftest.py
├── gen_book.py
├── init_db.py
├── main.py
├── start_opcclaw.py
├── test_opcclaw.py
├── verify_sync.py
```

---

## 模块列表

- [`core/__init__.py`](./core/__init__.py.md)
- [`core/agent_delegate.py`](./core/agent_delegate.py.md)
- [`core/agent_loop.py`](./core/agent_loop.py.md)
- [`core/chat_engine.py`](./core/chat_engine.py.md)
- [`core/clarify_system.py`](./core/clarify_system.py.md)
- [`core/cloud_sync.py`](./core/cloud_sync.py.md)
- [`core/code_executor.py`](./core/code_executor.py.md)
- [`core/code_intel.py`](./core/code_intel.py.md)
- [`core/collaboration_client.py`](./core/collaboration_client.py.md)
- [`core/config_validator.py`](./core/config_validator.py.md)
- [`core/core_engine.py`](./core/core_engine.py.md)
- [`core/enhanced_core.py`](./core/enhanced_core.py.md)
- [`core/enhanced_hermes_bridge.py`](./core/enhanced_hermes_bridge.py.md)
- [`core/git_ops.py`](./core/git_ops.py.md)
- [`core/llm_backend.py`](./core/llm_backend.py.md)
- [`core/memory.py`](./core/memory.py.md)
- [`core/memory_store.py`](./core/memory_store.py.md)
- [`core/model_status.py`](./core/model_status.py.md)
- [`core/model_status_manager.py`](./core/model_status_manager.py.md)
- [`core/multi_model.py`](./core/multi_model.py.md)
- [`core/multi_model_chat_engine.py`](./core/multi_model_chat_engine.py.md)
- [`core/opcclaw_logging.py`](./core/opcclaw_logging.py.md)
- [`core/patch_engine.py`](./core/patch_engine.py.md)
- [`core/performance_monitor.py`](./core/performance_monitor.py.md)
- [`core/process_manager.py`](./core/process_manager.py.md)
- [`core/rag_context.py`](./core/rag_context.py.md)
- [`core/secure_storage.py`](./core/secure_storage.py.md)
- [`core/semantic_search.py`](./core/semantic_search.py.md)
- [`core/session_search.py`](./core/session_search.py.md)
- [`core/skill_loader.py`](./core/skill_loader.py.md)
- [`core/skill_system.py`](./core/skill_system.py.md)
- [`core/smart_memory.py`](./core/smart_memory.py.md)
- [`core/smart_memory_adapter.py`](./core/smart_memory_adapter.py.md)
- [`core/supabase_client.py`](./core/supabase_client.py.md)
- [`core/super_intelligence.py`](./core/super_intelligence.py.md)
- [`core/sync_bridge.py`](./core/sync_bridge.py.md)
- [`core/task_scheduler.py`](./core/task_scheduler.py.md)
- [`core/test_phase2.py`](./core/test_phase2.py.md)
- [`core/todo_system.py`](./core/todo_system.py.md)
- [`core/token_optimizer.py`](./core/token_optimizer.py.md)
- [`core/token_saver.py`](./core/token_saver.py.md)
- [`core/tool_registry.py`](./core/tool_registry.py.md)
- [`core/web_search.py`](./core/web_search.py.md)
- [`core/workspace_indexer.py`](./core/workspace_indexer.py.md)
- [`modules/__init__.py`](./modules/__init__.py.md)
- [`modules/chat_window.py`](./modules/chat_window.py.md)
- [`modules/config_manager.py`](./modules/config_manager.py.md)
- [`modules/git_panel.py`](./modules/git_panel.py.md)
- [`modules/login_dialog.py`](./modules/login_dialog.py.md)
- [`modules/message_bubble.py`](./modules/message_bubble.py.md)
- [`modules/sidebar.py`](./modules/sidebar.py.md)
- [`modules/styled_widgets.py`](./modules/styled_widgets.py.md)
- [`modules/voice_manager.py`](./modules/voice_manager.py.md)
- [`modules/widgets.py`](./modules/widgets.py.md)
- [`tools/__init__.py`](./tools/__init__.py.md)
- [`tools/alert_tools.py`](./tools/alert_tools.py.md)
- [`tools/analysis_tools.py`](./tools/analysis_tools.py.md)
- [`tools/ansi_strip.py`](./tools/ansi_strip.py.md)
- [`tools/approval.py`](./tools/approval.py.md)
- [`tools/automation_tools.py`](./tools/automation_tools.py.md)
- [`tools/binary_extensions.py`](./tools/binary_extensions.py.md)
- [`tools/browser_camofox.py`](./tools/browser_camofox.py.md)
- [`tools/browser_camofox_state.py`](./tools/browser_camofox_state.py.md)
- [`tools/browser_cdp_tool.py`](./tools/browser_cdp_tool.py.md)
- [`tools/browser_dialog_tool.py`](./tools/browser_dialog_tool.py.md)
- [`tools/browser_providers/__init__.py`](./tools/browser_providers/__init__.py.md)
- [`tools/browser_providers/base.py`](./tools/browser_providers/base.py.md)
- [`tools/browser_providers/browser_use.py`](./tools/browser_providers/browser_use.py.md)
- [`tools/browser_providers/browserbase.py`](./tools/browser_providers/browserbase.py.md)
- [`tools/browser_providers/firecrawl.py`](./tools/browser_providers/firecrawl.py.md)
- [`tools/browser_supervisor.py`](./tools/browser_supervisor.py.md)
- [`tools/browser_tool.py`](./tools/browser_tool.py.md)
- [`tools/budget_config.py`](./tools/budget_config.py.md)
- [`tools/builtin/__init__.py`](./tools/builtin/__init__.py.md)
- [`tools/builtin/code_tools.py`](./tools/builtin/code_tools.py.md)
- [`tools/builtin/developer_tools.py`](./tools/builtin/developer_tools.py.md)
- [`tools/builtin/git_tools.py`](./tools/builtin/git_tools.py.md)
- [`tools/builtin/system_tools.py`](./tools/builtin/system_tools.py.md)
- [`tools/business_tools.py`](./tools/business_tools.py.md)
- [`tools/checkpoint_manager.py`](./tools/checkpoint_manager.py.md)
- [`tools/clarify_tool.py`](./tools/clarify_tool.py.md)
- [`tools/code_execution_tool.py`](./tools/code_execution_tool.py.md)
- [`tools/computer_use/__init__.py`](./tools/computer_use/__init__.py.md)
- [`tools/computer_use/backend.py`](./tools/computer_use/backend.py.md)
- [`tools/computer_use/cua_backend.py`](./tools/computer_use/cua_backend.py.md)
- [`tools/computer_use/schema.py`](./tools/computer_use/schema.py.md)
- [`tools/computer_use/tool.py`](./tools/computer_use/tool.py.md)
- [`tools/computer_use_tool.py`](./tools/computer_use_tool.py.md)
- [`tools/credential_files.py`](./tools/credential_files.py.md)
- [`tools/crm_tools.py`](./tools/crm_tools.py.md)
- [`tools/cronjob_tools.py`](./tools/cronjob_tools.py.md)
- [`tools/data_import_tools.py`](./tools/data_import_tools.py.md)
- [`tools/debug_helpers.py`](./tools/debug_helpers.py.md)
- [`tools/delegate_tool.py`](./tools/delegate_tool.py.md)
- [`tools/discord_tool.py`](./tools/discord_tool.py.md)
- [`tools/doc_tools.py`](./tools/doc_tools.py.md)
- [`tools/env_passthrough.py`](./tools/env_passthrough.py.md)
- [`tools/environments/__init__.py`](./tools/environments/__init__.py.md)
- [`tools/environments/base.py`](./tools/environments/base.py.md)
- [`tools/environments/daytona.py`](./tools/environments/daytona.py.md)
- [`tools/environments/docker.py`](./tools/environments/docker.py.md)
- [`tools/environments/file_sync.py`](./tools/environments/file_sync.py.md)
- [`tools/environments/local.py`](./tools/environments/local.py.md)
- [`tools/environments/managed_modal.py`](./tools/environments/managed_modal.py.md)
- [`tools/environments/modal.py`](./tools/environments/modal.py.md)
- [`tools/environments/modal_utils.py`](./tools/environments/modal_utils.py.md)
- [`tools/environments/singularity.py`](./tools/environments/singularity.py.md)
- [`tools/environments/ssh.py`](./tools/environments/ssh.py.md)
- [`tools/environments/vercel_sandbox.py`](./tools/environments/vercel_sandbox.py.md)
- [`tools/export_tools.py`](./tools/export_tools.py.md)
- [`tools/feishu_doc_tool.py`](./tools/feishu_doc_tool.py.md)
- [`tools/feishu_drive_tool.py`](./tools/feishu_drive_tool.py.md)
- [`tools/file_operations.py`](./tools/file_operations.py.md)
- [`tools/file_state.py`](./tools/file_state.py.md)
- [`tools/file_tools.py`](./tools/file_tools.py.md)
- [`tools/finance_analysis_tools.py`](./tools/finance_analysis_tools.py.md)
- [`tools/fuzzy_match.py`](./tools/fuzzy_match.py.md)
- [`tools/homeassistant_tool.py`](./tools/homeassistant_tool.py.md)
- [`tools/hr_tools.py`](./tools/hr_tools.py.md)
- [`tools/image_generation_tool.py`](./tools/image_generation_tool.py.md)
- [`tools/interrupt.py`](./tools/interrupt.py.md)
- [`tools/inventory_tools.py`](./tools/inventory_tools.py.md)
- [`tools/kanban_tools.py`](./tools/kanban_tools.py.md)
- [`tools/local_dev_tools.py`](./tools/local_dev_tools.py.md)
- [`tools/managed_tool_gateway.py`](./tools/managed_tool_gateway.py.md)
- [`tools/marketing_tools.py`](./tools/marketing_tools.py.md)
- [`tools/mcp_oauth.py`](./tools/mcp_oauth.py.md)
- [`tools/mcp_oauth_manager.py`](./tools/mcp_oauth_manager.py.md)
- [`tools/mcp_tool.py`](./tools/mcp_tool.py.md)
- [`tools/memory_tool.py`](./tools/memory_tool.py.md)
- [`tools/microsoft_graph_auth.py`](./tools/microsoft_graph_auth.py.md)
- [`tools/microsoft_graph_client.py`](./tools/microsoft_graph_client.py.md)
- [`tools/mixture_of_agents_tool.py`](./tools/mixture_of_agents_tool.py.md)
- [`tools/neutts_synth.py`](./tools/neutts_synth.py.md)
- [`tools/openrouter_client.py`](./tools/openrouter_client.py.md)
- [`tools/osv_check.py`](./tools/osv_check.py.md)
- [`tools/patch_parser.py`](./tools/patch_parser.py.md)
- [`tools/path_security.py`](./tools/path_security.py.md)
- [`tools/process_registry.py`](./tools/process_registry.py.md)
- [`tools/procurement_tools.py`](./tools/procurement_tools.py.md)
- [`tools/project_management.py`](./tools/project_management.py.md)
- [`tools/registry.py`](./tools/registry.py.md)
- [`tools/rl_training_tool.py`](./tools/rl_training_tool.py.md)
- [`tools/scheduling_tools.py`](./tools/scheduling_tools.py.md)
- [`tools/schema_sanitizer.py`](./tools/schema_sanitizer.py.md)
- [`tools/self_monitor.py`](./tools/self_monitor.py.md)
- [`tools/send_message_tool.py`](./tools/send_message_tool.py.md)
- [`tools/session_search_tool.py`](./tools/session_search_tool.py.md)
- [`tools/skill_manager_tool.py`](./tools/skill_manager_tool.py.md)
- [`tools/skill_provenance.py`](./tools/skill_provenance.py.md)
- [`tools/skill_usage.py`](./tools/skill_usage.py.md)
- [`tools/skills_guard.py`](./tools/skills_guard.py.md)
- [`tools/skills_hub.py`](./tools/skills_hub.py.md)
- [`tools/skills_sync.py`](./tools/skills_sync.py.md)
- [`tools/skills_tool.py`](./tools/skills_tool.py.md)
- [`tools/slash_confirm.py`](./tools/slash_confirm.py.md)
- [`tools/smart_report_tools.py`](./tools/smart_report_tools.py.md)
- [`tools/template_tools.py`](./tools/template_tools.py.md)
- [`tools/terminal_tool.py`](./tools/terminal_tool.py.md)
- [`tools/tirith_security.py`](./tools/tirith_security.py.md)
- [`tools/todo_tool.py`](./tools/todo_tool.py.md)
- [`tools/tool_backend_helpers.py`](./tools/tool_backend_helpers.py.md)
- [`tools/tool_output_limits.py`](./tools/tool_output_limits.py.md)
- [`tools/tool_result_storage.py`](./tools/tool_result_storage.py.md)
- [`tools/transcription_tools.py`](./tools/transcription_tools.py.md)
- [`tools/tts_tool.py`](./tools/tts_tool.py.md)
- [`tools/url_safety.py`](./tools/url_safety.py.md)
- [`tools/vision_tools.py`](./tools/vision_tools.py.md)
- [`tools/voice_mode.py`](./tools/voice_mode.py.md)
- [`tools/web_providers/__init__.py`](./tools/web_providers/__init__.py.md)
- [`tools/web_providers/base.py`](./tools/web_providers/base.py.md)
- [`tools/web_providers/brave_free.py`](./tools/web_providers/brave_free.py.md)
- [`tools/web_providers/ddgs.py`](./tools/web_providers/ddgs.py.md)
- [`tools/web_providers/searxng.py`](./tools/web_providers/searxng.py.md)
- [`tools/web_search_tools.py`](./tools/web_search_tools.py.md)
- [`tools/web_tools.py`](./tools/web_tools.py.md)
- [`tools/website_policy.py`](./tools/website_policy.py.md)
- [`tools/xai_http.py`](./tools/xai_http.py.md)
- [`tools/yuanbao_tools.py`](./tools/yuanbao_tools.py.md)
