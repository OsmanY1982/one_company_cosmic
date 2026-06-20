# 一人公司 · 宇宙版 — 源码全书
> 自动生成于 2026-06-20 16:40
> 共 863 个模块，每个 `.py` 文件独立为一个文档

---

## 目录结构

```
.
├── _archived/
│   ├── data_20260619_122853/
│   ├── dedup_20260619_170800/
│   │   └── deps.py
│   └── license_模块归档_20260619/
│       ├── license_crypto.py
│       ├── license_db.py
│       └── license_service.py
├── config/
│   ├── agents/
│   ├── __init__.py
│   ├── supabase_config.py
├── core/
│   ├── shapes/
│   │   ├── __init__.py
│   │   ├── alien.py
│   │   ├── black_hole.py
│   │   ├── classic.py
│   │   ├── classic_20260614_184255_598.py
│   │   ├── comet.py
│   │   ├── corvette.py
│   │   ├── crystal_alien.py
│   │   ├── destroyer.py
│   │   ├── dreadnought.py
│   │   ├── energy_being.py
│   │   ├── fighter.py
│   │   ├── gas_giant.py
│   │   ├── gas_giant_20260614_184255_426.py
│   │   ├── ghost_alien.py
│   │   ├── grey_alien.py
│   │   ├── ice_giant.py
│   │   ├── ice_giant_20260614_184255_207.py
│   │   ├── interceptor.py
│   │   ├── jellyfish_alien.py
│   │   ├── lava_planet.py
│   │   ├── lava_planet_20260614_184255_101.py
│   │   ├── mars.py
│   │   ├── mars_20260614_184255_257.py
│   │   ├── mercury.py
│   │   ├── nebula.py
│   │   ├── neutron_star.py
│   │   ├── octopus_alien.py
│   │   ├── pluto.py
│   │   ├── pulsar.py
│   │   ├── red_giant.py
│   │   ├── reptilian.py
│   │   ├── robot_alien.py
│   │   ├── saturn.py
│   │   ├── scout.py
│   │   ├── starship.py
│   │   ├── transporter.py
│   │   ├── uranus.py
│   │   ├── venus.py
│   │   ├── white_dwarf.py
│   │   └── wormhole.py
│   ├── __init__.py
│   ├── agent.py
│   ├── app_state.py
│   ├── auth_service.py
│   ├── backup.py
│   ├── business_service.py
│   ├── ceo_agent.py
│   ├── cloud_pull.py
│   ├── cloud_sync.py
│   ├── cloud_sync_v2.py
│   ├── conflict_resolver.py
│   ├── cosmic.py
│   ├── custom_fields.py
│   ├── dark_theme.py
│   ├── data.py
│   ├── data_20260619_111935_141.py
│   ├── data_sync.py
│   ├── database.py
│   ├── event_bus.py
│   ├── excel_export.py
│   ├── llm_client.py
│   ├── machine_code.py
│   ├── mobile_api.py
│   ├── module_manager.py
│   ├── notification_cron.py
│   ├── notification_service.py
│   ├── notification_toast.py
│   ├── operation_log.py
│   ├── oplog.py
│   ├── paths.py
│   ├── planet_painter.py
│   ├── planet_painter_20260614_151048_302.py
│   ├── reconciliation.py
│   ├── scheduled_tasks.py
│   ├── simple_sync.py
│   ├── smart_report.py
│   ├── storage.py
│   ├── supabase_client.py
│   ├── sync_bridge.py
│   ├── sync_decorator.py
│   ├── sync_integration.py
│   ├── sync_manager.py
│   ├── sync_optimized.py
│   ├── texture_mapper.py
│   ├── triple_sync.py
│   ├── user_dao.py
│   ├── voice.py
│   └── workflow_engine.py
├── data/
│   ├── drafts/
│   ├── enhanced/
│   ├── metrics/
│   ├── sync/
├── knowledge_base/
├── log/
├── modules/
│   ├── account/
│   │   ├── __init__.py
│   │   ├── account_activation.py
│   │   ├── account_update.py
│   │   ├── activation_service.py
│   │   ├── activation_stats.py
│   │   ├── activation_stats_service.py
│   │   └── license_local.py
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── admin_activation.py
│   │   ├── admin_backup.py
│   │   ├── admin_data.py
│   │   ├── admin_data_mgmt.py
│   │   ├── admin_finance.py
│   │   ├── admin_log.py
│   │   ├── admin_orders.py
│   │   ├── admin_product.py
│   │   ├── admin_service.py
│   │   ├── admin_settings.py
│   │   ├── admin_staff.py
│   │   ├── admin_strategy.py
│   │   ├── admin_user.py
│   │   ├── admin_window.py
│   │   ├── cascade_delete.py
│   │   └── strategy_dao.py
│   ├── astronomy/
│   │   ├── solar_system/
│   │   │   ├── planets/
│   │   │   │   ├── callisto/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── ceres/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── earth/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── enceladus/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── eris/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── europa/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── ganymede/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── haumea/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── io/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── jupiter/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── makemake/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── mars/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── mercury/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── moon/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── neptune/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── pluto/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── saturn/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── sun/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── titan/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   └── __init__.py
│   │   │   │   ├── uranus/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── venus/
│   │   │   │   │   ├── audio/
│   │   │   │   │   ├── knowledge/
│   │   │   │   │   ├── __init__.py
│   │   │   │   ├── __init__.py
│   │   │   │   └── _base.py
│   │   │   ├── __init__.py
│   │   │   ├── data.py
│   │   │   ├── renderer.py
│   │   │   └── window.py
│   │   ├── star_catalog/
│   │   │   ├── __init__.py
│   │   │   ├── catalog.py
│   │   │   ├── data_entries.py
│   │   │   ├── detail.py
│   │   │   ├── encyclopedia.py
│   │   │   └── voice.py
│   │   ├── __init__.py
│   │   └── hub.py
│   ├── auth/
│   │   ├── dao/
│   │   │   └── user_dao.py
│   │   ├── service/
│   │   │   └── cloud_api.py
│   │   ├── __init__.py
│   │   ├── activation_gate.py
│   │   ├── admin_login_dialog.py
│   │   ├── admin_login_window.py
│   │   ├── auth_service.py
│   │   ├── change_password_dialog.py
│   │   ├── connect_window.py
│   │   ├── login_window.py
│   │   ├── model_config_panel.py
│   │   ├── model_setup_window.py
│   │   ├── register_window.py
│   │   ├── select_mode_window.py
│   │   ├── upgrade_window.py
│   ├── business/
│   │   ├── __init__.py
│   │   ├── business_window.py
│   │   ├── customer_service.py
│   │   ├── customer_window.py
│   │   ├── finance_service.py
│   │   ├── finance_window.py
│   │   ├── order_service.py
│   │   ├── order_window.py
│   │   ├── product_service.py
│   │   └── product_window.py
│   ├── common/
│   │   ├── advanced_filter_window.py
│   │   └── custom_field_window.py
│   ├── dashboard/
│   │   ├── __init__.py
│   │   └── dashboard_window.py
│   ├── data/
│   │   └── smart_memory/
│   ├── data_center/
│   │   ├── __init__.py
│   │   ├── bi_window.py
│   │   ├── chart_window.py
│   │   ├── dashboard_window_v2.py
│   │   ├── dashboard_window_v3.py
│   │   ├── data_window.py
│   │   ├── report_service.py
│   │   ├── report_service_v2.py
│   │   ├── report_window.py
│   │   └── smart_report_window.py
│   ├── i18n/
│   │   └── i18n_window.py
│   ├── industry/
│   │   ├── industry_adapter.py
│   │   ├── industry_config.py
│   │   ├── industry_report.py
│   │   └── industry_window.py
│   ├── intelligence/
│   │   ├── _archived/
│   │   ├── backup_p02/
│   │   │   ├── agent_bridge.py
│   │   │   ├── ai_chat_window.py
│   │   │   ├── intelligence_window.py
│   │   │   └── opcclaw_floating_planet.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── llm_backend.py
│   │   ├── data/
│   │   │   ├── learning/
│   │   │   └── reflections/
│   │   ├── enhanced/
│   │   │   ├── __init__.py
│   │   │   └── enhanced_tools.py
│   │   ├── temp_backup/
│   │   ├── __init__.py
│   │   ├── _ai_shared.py
│   │   ├── _ai_widgets.py
│   │   ├── _ai_widgets_anomaly.py
│   │   ├── _ai_widgets_business.py
│   │   ├── _ai_widgets_core.py
│   │   ├── _ai_widgets_recommendation.py
│   │   ├── _ai_widgets_visualization.py
│   │   ├── _ai_widgets_workflow.py
│   │   ├── _chat_dialog.py
│   │   ├── _compat.py
│   │   ├── _model_manager.py
│   │   ├── _model_manager_download.py
│   │   ├── _model_manager_ollama.py
│   │   ├── _navigation_hud.py
│   │   ├── _shell_dialogs.py
│   │   ├── _stubs.py
│   │   ├── account_window.py
│   │   ├── agent_bridge.py
│   │   ├── agent_bridge_models.py
│   │   ├── agent_bridge_tools.py
│   │   ├── agent_bridge_workers.py
│   │   ├── ai_assistant_window.py
│   │   ├── ai_center_window.py
│   │   ├── ai_chat_styles.py
│   │   ├── ai_chat_window.py
│   │   ├── ai_dashboard_window.py
│   │   ├── ai_features_ai_dashboard.py
│   │   ├── ai_features_customer_ai.py
│   │   ├── ai_features_inventory_ai.py
│   │   ├── ai_features_pricing_ai.py
│   │   ├── ai_features_sales_ai.py
│   │   ├── analysis_tools.py
│   │   ├── anomaly_detector.py
│   │   ├── auto_task_executor.py
│   │   ├── batch_text.py
│   │   ├── business_ai_assistant.py
│   │   ├── business_tools.py
│   │   ├── chat_session_manager.py
│   │   ├── compress_tool.py
│   │   ├── crm_tools.py
│   │   ├── data_import_tools.py
│   │   ├── data_visualization.py
│   │   ├── db_helper.py
│   │   ├── download_dialog.py
│   │   ├── editor_window.py
│   │   ├── enhanced_chat.py
│   │   ├── event_trigger.py
│   │   ├── file_rename_tools.py
│   │   ├── finance_analysis_tools.py
│   │   ├── floating_planet_anim_mixin.py
│   │   ├── floating_planet_draw_mixin.py
│   │   ├── floating_planet_menu_mixin.py
│   │   ├── hr_tools.py
│   │   ├── img_converter.py
│   │   ├── intelligence_integration.py
│   │   ├── intelligence_window.py
│   │   ├── inventory_tools.py
│   │   ├── json_tools.py
│   │   ├── key_manager.py
│   │   ├── knowledge_base.py
│   │   ├── marketing_tools.py
│   │   ├── model_config.py
│   │   ├── monitor_dashboard.py
│   │   ├── offline_analyzer.py
│   │   ├── opcclaw_floating_planet.py
│   │   ├── password_tools.py
│   │   ├── performance_monitor.py
│   │   ├── predictor_window.py
│   │   ├── quick_actions.py
│   │   ├── rag_injector.py
│   │   ├── recommendation_engine.py
│   │   ├── report_generator.py
│   │   ├── sales_predictor.py
│   │   ├── scan_window.py
│   │   ├── screen_recorder.py
│   │   ├── self_monitor.py
│   │   ├── session_context.py
│   │   ├── smart_assistant.py
│   │   ├── smart_report_tools.py
│   │   ├── smart_workflow.py
│   │   ├── solar_system_data.py
│   │   ├── solar_system_window.py
│   │   ├── starship_painter.py
│   │   ├── super_intelligence.py
│   │   ├── system_hub_window.py
│   │   ├── system_monitor.py
│   │   ├── text_editor.py
│   │   ├── timestamp_tools.py
│   │   ├── tool_registry.py
│   │   ├── tools_window.py
│   │   ├── usb_scanner.py
│   │   ├── vault_window.py
│   │   ├── voice_interface.py
│   │   ├── whisper_recognizer.py
│   │   ├── window_top_tools.py
│   │   └── workflow_engine.py
│   ├── notification/
│   │   └── notification_window.py
│   ├── permission/
│   │   └── permission_window.py
│   ├── personnel/
│   │   ├── __init__.py
│   │   ├── distribution_service.py
│   │   ├── distribution_window.py
│   │   ├── member_service.py
│   │   ├── member_window.py
│   │   ├── personnel_window.py
│   │   ├── staff_service.py
│   │   ├── staff_window.py
│   │   ├── wallet_service.py
│   │   └── wallet_window.py
│   ├── startup/
│   │   └── startup_selector_window.py
│   ├── system/
│   │   ├── _archived/
│   │   │   ├── activation_window.py
│   │   │   ├── base_info_window.py
│   │   │   ├── cloud_window.py
│   │   │   ├── logs_window.py
│   │   │   ├── system_window.py
│   │   │   └── update_dialog.py
│   │   ├── __init__.py
│   │   ├── astronomy_hub_window.py
│   │   ├── audit_window.py
│   │   ├── base_info_window.py
│   │   ├── cloud_model_panel.py
│   │   ├── cloud_module.py
│   │   ├── cloud_server_window.py
│   │   ├── cloud_window.py
│   │   ├── logs_window.py
│   │   ├── system_hub_window.py
│   │   └── system_logs_service.py
│   ├── system_logs/
│   │   ├── system_logs_service.py
│   │   └── system_logs_window.py
│   ├── tools/
│   ├── workflow/
│   │   └── workflow_window.py
│   └── __init__.py
├── opcclaw/
│   ├── adapters/
│   │   ├── channels/
│   │   │   ├── __init__.py
│   │   │   ├── dingtalk.py
│   │   │   ├── discord.py
│   │   │   ├── feishu.py
│   │   │   ├── router.py
│   │   │   ├── slack.py
│   │   │   └── telegram.py
│   │   └── __init__.py
│   ├── agent/
│   │   ├── transports/
│   │   │   ├── __init__.py
│   │   │   ├── anthropic.py
│   │   │   ├── base.py
│   │   │   ├── bedrock.py
│   │   │   ├── chat_completions.py
│   │   │   ├── codex.py
│   │   │   └── types.py
│   │   ├── __init__.py
│   │   ├── account_usage.py
│   │   ├── anthropic_adapter.py
│   │   ├── auxiliary_client.py
│   │   ├── bedrock_adapter.py
│   │   ├── codex_responses_adapter.py
│   │   ├── context_compressor.py
│   │   ├── context_engine.py
│   │   ├── context_references.py
│   │   ├── copilot_acp_client.py
│   │   ├── credential_pool.py
│   │   ├── credential_sources.py
│   │   ├── curator.py
│   │   ├── curator_backup.py
│   │   ├── display.py
│   │   ├── error_classifier.py
│   │   ├── file_safety.py
│   │   ├── gemini_cloudcode_adapter.py
│   │   ├── gemini_native_adapter.py
│   │   ├── gemini_schema.py
│   │   ├── google_code_assist.py
│   │   ├── google_oauth.py
│   │   ├── i18n.py
│   │   ├── image_gen_provider.py
│   │   ├── image_gen_registry.py
│   │   ├── image_routing.py
│   │   ├── insights.py
│   │   ├── lmstudio_reasoning.py
│   │   ├── manual_compression_feedback.py
│   │   ├── memory_manager.py
│   │   ├── memory_provider.py
│   │   ├── model_metadata.py
│   │   ├── models_dev.py
│   │   ├── moonshot_schema.py
│   │   ├── nous_rate_guard.py
│   │   ├── onboarding.py
│   │   ├── prompt_builder.py
│   │   ├── prompt_caching.py
│   │   ├── rate_limit_tracker.py
│   │   ├── redact.py
│   │   ├── retry_utils.py
│   │   ├── shell_hooks.py
│   │   ├── skill_commands.py
│   │   ├── skill_preprocessing.py
│   │   ├── skill_utils.py
│   │   ├── subdirectory_hints.py
│   │   ├── think_scrubber.py
│   │   ├── title_generator.py
│   │   ├── tool_guardrails.py
│   │   ├── trajectory.py
│   │   └── usage_pricing.py
│   ├── cache/
│   │   └── firecrawl/
│   ├── config/
│   │   └── agents/
│   ├── core/
│   │   ├── code_graph/
│   │   │   ├── __init__.py
│   │   │   ├── ast_parser.py
│   │   │   └── graph_store.py
│   │   ├── firecrawl/
│   │   │   ├── __init__.py
│   │   │   ├── cache.py
│   │   │   ├── converter.py
│   │   │   └── test_self_check.py
│   │   ├── harness/
│   │   │   ├── __init__.py
│   │   │   └── config_schema.py
│   │   ├── impeccable/
│   │   │   ├── __init__.py
│   │   │   ├── complexity_checker.py
│   │   │   ├── coupling_checker.py
│   │   │   ├── report_generator.py
│   │   │   └── solid_checker.py
│   │   ├── multi_channel/
│   │   │   ├── platforms/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── linkedin.py
│   │   │   │   ├── twitter.py
│   │   │   │   ├── wechat.py
│   │   │   │   ├── weibo.py
│   │   │   │   └── zhihu.py
│   │   │   ├── __init__.py
│   │   │   ├── content_optimizer.py
│   │   │   └── draft_manager.py
│   │   ├── observability/
│   │   │   ├── __init__.py
│   │   │   ├── cost_tracker.py
│   │   │   ├── schema.py
│   │   │   ├── test_obs.py
│   │   │   ├── test_obs_20260615_143009_780.py
│   │   │   ├── token_observer.py
│   │   │   └── trace_manager.py
│   │   ├── semantic_search/
│   │   │   ├── __init__.py
│   │   │   └── hybrid_retriever.py
│   │   ├── __init__.py
│   │   ├── agent_delegate.py
│   │   ├── agent_loop.py
│   │   ├── chat_engine.py
│   │   ├── clarify_system.py
│   │   ├── cloud_sync.py
│   │   ├── code_executor.py
│   │   ├── code_intel.py
│   │   ├── collaboration_client.py
│   │   ├── config_validator.py
│   │   ├── core_engine.py
│   │   ├── enhanced_core.py
│   │   ├── enhanced_hermes_bridge.py
│   │   ├── git_ops.py
│   │   ├── llm_backend.py
│   │   ├── memory.py
│   │   ├── memory_store.py
│   │   ├── model_status.py
│   │   ├── model_status_manager.py
│   │   ├── multi_model.py
│   │   ├── multi_model_chat_engine.py
│   │   ├── opcclaw_logging.py
│   │   ├── patch_engine.py
│   │   ├── performance_monitor.py
│   │   ├── proactive_engine.py
│   │   ├── proactive_monitors.py
│   │   ├── process_manager.py
│   │   ├── provider_registry.py
│   │   ├── rag_context.py
│   │   ├── secure_storage.py
│   │   ├── semantic_search.py
│   │   ├── session_search.py
│   │   ├── skill_loader.py
│   │   ├── skill_system.py
│   │   ├── smart_memory.py
│   │   ├── smart_memory_adapter.py
│   │   ├── supabase_client.py
│   │   ├── super_intelligence.py
│   │   ├── sync_bridge.py
│   │   ├── task_scheduler.py
│   │   ├── todo_system.py
│   │   ├── token_optimizer.py
│   │   ├── token_saver.py
│   │   ├── tool_registry.py
│   │   ├── web_search.py
│   │   └── workspace_indexer.py
│   ├── cron/
│   │   ├── __init__.py
│   │   └── jobs.py
│   ├── data/
│   │   ├── opcclaw/
│   │   │   ├── data/
│   │   │   │   └── smart_memory/
│   │   │   ├── exports/
│   │   │   ├── memory/
│   │   │   ├── metrics/
│   │   │   ├── sessions/
│   │   │   ├── smart_memory/
│   │   │   │   ├── preferences/
│   │   │   │   ├── snapshots/
│   │   ├── process_logs/
│   │   ├── workflows/
│   │   ├── __init__.py
│   ├── hermes_cli/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── logs/
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── _shared.py
│   │   ├── agent_event_panel.py
│   │   ├── animations.py
│   │   ├── chat_window.py
│   │   ├── chat_window_core.py
│   │   ├── chat_worker.py
│   │   ├── cloud_model_panel.py
│   │   ├── config_manager.py
│   │   ├── general_settings_panel.py
│   │   ├── git_panel.py
│   │   ├── local_model_panel.py
│   │   ├── login_dialog.py
│   │   ├── message_bubble.py
│   │   ├── sidebar.py
│   │   ├── sidebar_panel.py
│   │   ├── skills_panel.py
│   │   ├── voice_manager.py
│   │   └── widgets.py
│   ├── plugins/
│   │   ├── code_executor/
│   │   │   └── __init__.py
│   │   ├── context_engine/
│   │   │   └── __init__.py
│   │   ├── disk-cleanup/
│   │   │   ├── __init__.py
│   │   │   ├── disk_cleanup.py
│   │   ├── example-dashboard/
│   │   │   └── dashboard/
│   │   │       └── plugin_api.py
│   │   ├── file_handler/
│   │   │   └── __init__.py
│   │   ├── google_meet/
│   │   │   ├── node/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── cli.py
│   │   │   │   ├── client.py
│   │   │   │   ├── protocol.py
│   │   │   │   ├── registry.py
│   │   │   │   └── server.py
│   │   │   ├── realtime/
│   │   │   │   ├── __init__.py
│   │   │   │   └── openai_client.py
│   │   │   ├── __init__.py
│   │   │   ├── audio_bridge.py
│   │   │   ├── cli.py
│   │   │   ├── meet_bot.py
│   │   │   ├── process_manager.py
│   │   │   └── tools.py
│   │   ├── hermes-achievements/
│   │   │   ├── dashboard/
│   │   │   │   └── plugin_api.py
│   │   │   ├── tests/
│   │   ├── image_gen/
│   │   │   ├── openai/
│   │   │   │   ├── __init__.py
│   │   │   ├── openai-codex/
│   │   │   │   ├── __init__.py
│   │   │   └── xai/
│   │   │       ├── __init__.py
│   │   ├── image_vision/
│   │   │   └── __init__.py
│   │   ├── kanban/
│   │   │   ├── dashboard/
│   │   │   │   └── plugin_api.py
│   │   │   └── systemd/
│   │   ├── memory/
│   │   │   ├── byterover/
│   │   │   │   ├── __init__.py
│   │   │   ├── hindsight/
│   │   │   │   ├── __init__.py
│   │   │   ├── holographic/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── holographic.py
│   │   │   │   ├── retrieval.py
│   │   │   │   └── store.py
│   │   │   ├── honcho/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── cli.py
│   │   │   │   ├── client.py
│   │   │   │   └── session.py
│   │   │   ├── mem0/
│   │   │   │   ├── __init__.py
│   │   │   ├── openviking/
│   │   │   │   ├── __init__.py
│   │   │   ├── retaindb/
│   │   │   │   ├── __init__.py
│   │   │   ├── supermemory/
│   │   │   │   ├── __init__.py
│   │   │   └── __init__.py
│   │   ├── model-providers/
│   │   │   ├── ai-gateway/
│   │   │   │   ├── __init__.py
│   │   │   ├── alibaba/
│   │   │   │   ├── __init__.py
│   │   │   ├── alibaba-coding-plan/
│   │   │   │   ├── __init__.py
│   │   │   ├── anthropic/
│   │   │   │   ├── __init__.py
│   │   │   ├── arcee/
│   │   │   │   ├── __init__.py
│   │   │   ├── azure-foundry/
│   │   │   │   ├── __init__.py
│   │   │   ├── bedrock/
│   │   │   │   ├── __init__.py
│   │   │   ├── copilot/
│   │   │   │   ├── __init__.py
│   │   │   ├── copilot-acp/
│   │   │   │   ├── __init__.py
│   │   │   ├── custom/
│   │   │   │   ├── __init__.py
│   │   │   ├── deepseek/
│   │   │   │   ├── __init__.py
│   │   │   ├── gemini/
│   │   │   │   ├── __init__.py
│   │   │   ├── gmi/
│   │   │   │   ├── __init__.py
│   │   │   ├── huggingface/
│   │   │   │   ├── __init__.py
│   │   │   ├── kilocode/
│   │   │   │   ├── __init__.py
│   │   │   ├── kimi-coding/
│   │   │   │   ├── __init__.py
│   │   │   ├── minimax/
│   │   │   │   ├── __init__.py
│   │   │   ├── nous/
│   │   │   │   ├── __init__.py
│   │   │   ├── nvidia/
│   │   │   │   ├── __init__.py
│   │   │   ├── ollama/
│   │   │   │   ├── __init__.py
│   │   │   ├── ollama-cloud/
│   │   │   │   ├── __init__.py
│   │   │   ├── openai-codex/
│   │   │   │   ├── __init__.py
│   │   │   ├── opencode-zen/
│   │   │   │   ├── __init__.py
│   │   │   ├── openrouter/
│   │   │   │   ├── __init__.py
│   │   │   ├── qwen-oauth/
│   │   │   │   ├── __init__.py
│   │   │   ├── stepfun/
│   │   │   │   ├── __init__.py
│   │   │   ├── xai/
│   │   │   │   ├── __init__.py
│   │   │   ├── xiaomi/
│   │   │   │   ├── __init__.py
│   │   │   ├── zai/
│   │   │   │   ├── __init__.py
│   │   ├── multi_model/
│   │   │   └── __init__.py
│   │   ├── observability/
│   │   │   └── langfuse/
│   │   │       ├── __init__.py
│   │   ├── platforms/
│   │   │   ├── google_chat/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── adapter.py
│   │   │   │   ├── oauth.py
│   │   │   ├── irc/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── adapter.py
│   │   │   └── teams/
│   │   │       ├── __init__.py
│   │   │       ├── adapter.py
│   │   ├── spotify/
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   └── tools.py
│   │   ├── strike-freedom-cockpit/
│   │   │   ├── dashboard/
│   │   │   ├── theme/
│   │   ├── teams_pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── cli.py
│   │   │   ├── meetings.py
│   │   │   ├── models.py
│   │   │   ├── pipeline.py
│   │   │   ├── runtime.py
│   │   │   ├── store.py
│   │   │   └── subscriptions.py
│   │   ├── web_search/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py
│   ├── reports/
│   │   └── impeccable/
│   ├── skills/
│   │   ├── apple/
│   │   │   ├── apple-notes/
│   │   │   ├── apple-reminders/
│   │   │   ├── findmy/
│   │   │   ├── imessage/
│   │   │   ├── macos-computer-use/
│   │   ├── autonomous-ai-agents/
│   │   │   ├── claude-code/
│   │   │   ├── codex/
│   │   │   ├── hermes-agent/
│   │   │   ├── opencode/
│   │   ├── check-code-changes/
│   │   ├── creative/
│   │   │   ├── architecture-diagram/
│   │   │   │   ├── templates/
│   │   │   ├── ascii-art/
│   │   │   ├── ascii-video/
│   │   │   │   ├── references/
│   │   │   ├── baoyu-comic/
│   │   │   │   ├── references/
│   │   │   │   │   ├── art-styles/
│   │   │   │   │   ├── layouts/
│   │   │   │   │   ├── presets/
│   │   │   │   │   ├── tones/
│   │   │   ├── baoyu-infographic/
│   │   │   │   ├── references/
│   │   │   │   │   ├── layouts/
│   │   │   │   │   ├── styles/
│   │   │   ├── claude-design/
│   │   │   ├── comfyui/
│   │   │   │   ├── references/
│   │   │   │   ├── scripts/
│   │   │   │   │   ├── _common.py
│   │   │   │   │   ├── auto_fix_deps.py
│   │   │   │   │   ├── check_deps.py
│   │   │   │   │   ├── extract_schema.py
│   │   │   │   │   ├── fetch_logs.py
│   │   │   │   │   ├── hardware_check.py
│   │   │   │   │   ├── health_check.py
│   │   │   │   │   ├── run_batch.py
│   │   │   │   │   ├── run_workflow.py
│   │   │   │   │   └── ws_monitor.py
│   │   │   │   ├── tests/
│   │   │   │   │   ├── conftest.py
│   │   │   │   ├── workflows/
│   │   │   ├── creative-ideation/
│   │   │   │   ├── references/
│   │   │   ├── design-md/
│   │   │   │   ├── templates/
│   │   │   ├── excalidraw/
│   │   │   │   ├── references/
│   │   │   │   ├── scripts/
│   │   │   │   │   └── upload.py
│   │   │   ├── humanizer/
│   │   │   ├── manim-video/
│   │   │   │   ├── references/
│   │   │   │   ├── scripts/
│   │   │   ├── p5js/
│   │   │   │   ├── references/
│   │   │   │   ├── scripts/
│   │   │   │   ├── templates/
│   │   │   ├── pixel-art/
│   │   │   │   ├── references/
│   │   │   │   ├── scripts/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── palettes.py
│   │   │   │   │   ├── pixel_art.py
│   │   │   │   │   └── pixel_art_video.py
│   │   │   ├── popular-web-designs/
│   │   │   │   ├── templates/
│   │   │   ├── pretext/
│   │   │   │   ├── references/
│   │   │   │   ├── templates/
│   │   │   ├── sketch/
│   │   │   ├── songwriting-and-ai-music/
│   │   │   ├── touchdesigner-mcp/
│   │   │   │   ├── references/
│   │   │   │   ├── scripts/
│   │   ├── data-science/
│   │   │   ├── jupyter-live-kernel/
│   │   ├── devops/
│   │   │   ├── kanban-orchestrator/
│   │   │   ├── kanban-worker/
│   │   │   └── webhook-subscriptions/
│   │   ├── diagramming/
│   │   ├── dogfood/
│   │   │   ├── references/
│   │   │   ├── templates/
│   │   ├── domain/
│   │   ├── email/
│   │   │   ├── himalaya/
│   │   │   │   ├── references/
│   │   ├── flybook_bot/
│   │   │   ├── config.py
│   │   │   ├── flybook_skill.py
│   │   │   ├── server.py
│   │   │   ├── server_minimal.py
│   │   │   └── server_simple.py
│   │   ├── gaming/
│   │   │   ├── minecraft-modpack-server/
│   │   │   ├── pokemon-player/
│   │   ├── gifs/
│   │   ├── git-commit/
│   │   ├── github/
│   │   │   ├── codebase-inspection/
│   │   │   ├── github-auth/
│   │   │   │   ├── scripts/
│   │   │   ├── github-code-review/
│   │   │   │   ├── references/
│   │   │   ├── github-issues/
│   │   │   │   ├── templates/
│   │   │   ├── github-pr-workflow/
│   │   │   │   ├── references/
│   │   │   │   ├── templates/
│   │   │   ├── github-repo-management/
│   │   │   │   ├── references/
│   │   ├── index-cache/
│   │   ├── inference-sh/
│   │   ├── macos_system/
│   │   ├── mcp/
│   │   │   ├── native-mcp/
│   │   ├── media/
│   │   │   ├── gif-search/
│   │   │   ├── heartmula/
│   │   │   ├── songsee/
│   │   │   ├── spotify/
│   │   │   ├── youtube-content/
│   │   │   │   ├── references/
│   │   │   │   ├── scripts/
│   │   │   │   │   └── fetch_transcript.py
│   │   ├── mlops/
│   │   │   ├── evaluation/
│   │   │   │   ├── lm-evaluation-harness/
│   │   │   │   │   ├── references/
│   │   │   │   ├── weights-and-biases/
│   │   │   │   │   ├── references/
│   │   │   ├── huggingface-hub/
│   │   │   ├── inference/
│   │   │   │   ├── llama-cpp/
│   │   │   │   │   ├── references/
│   │   │   │   ├── obliteratus/
│   │   │   │   │   ├── references/
│   │   │   │   │   ├── templates/
│   │   │   │   ├── vllm/
│   │   │   │   │   ├── references/
│   │   │   ├── models/
│   │   │   │   ├── audiocraft/
│   │   │   │   │   ├── references/
│   │   │   │   ├── segment-anything/
│   │   │   │   │   ├── references/
│   │   │   ├── research/
│   │   │   │   ├── dspy/
│   │   │   │   │   ├── references/
│   │   │   ├── training/
│   │   │   ├── vector-databases/
│   │   ├── model-switch-automation/
│   │   ├── note-taking/
│   │   │   ├── obsidian/
│   │   ├── one_company/
│   │   ├── productivity/
│   │   │   ├── airtable/
│   │   │   ├── google-workspace/
│   │   │   │   ├── references/
│   │   │   │   ├── scripts/
│   │   │   │   │   ├── _hermes_home.py
│   │   │   │   │   ├── google_api.py
│   │   │   │   │   ├── gws_bridge.py
│   │   │   │   │   └── setup.py
│   │   │   ├── linear/
│   │   │   │   ├── scripts/
│   │   │   │   │   └── linear_api.py
│   │   │   ├── maps/
│   │   │   │   ├── scripts/
│   │   │   │   │   └── maps_client.py
│   │   │   ├── nano-pdf/
│   │   │   ├── notion/
│   │   │   │   ├── references/
│   │   │   ├── ocr-and-documents/
│   │   │   │   ├── scripts/
│   │   │   │   │   ├── extract_marker.py
│   │   │   │   │   └── extract_pymupdf.py
│   │   │   ├── powerpoint/
│   │   │   │   ├── scripts/
│   │   │   │   │   ├── office/
│   │   │   │   │   │   ├── helpers/
│   │   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   │   ├── merge_runs.py
│   │   │   │   │   │   │   └── simplify_redlines.py
│   │   │   │   │   │   ├── schemas/
│   │   │   │   │   │   │   ├── ecma/
│   │   │   │   │   │   │   │   └── fourth-edition/
│   │   │   │   │   │   │   ├── ISO-IEC29500-4_2016/
│   │   │   │   │   │   │   ├── mce/
│   │   │   │   │   │   │   └── microsoft/
│   │   │   │   │   │   └── pack.py
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── add_slide.py
│   │   │   │   │   └── clean.py
│   │   │   ├── teams-meeting-pipeline/
│   │   ├── qclaw_skills/
│   │   │   ├── aippt/
│   │   │   │   ├── scripts/
│   │   │   ├── baidu-search/
│   │   │   │   ├── scripts/
│   │   │   │   │   └── search.py
│   │   │   ├── file-manager/
│   │   │   │   ├── references/
│   │   │   │   ├── scripts/
│   │   │   │   │   ├── batch_rename.py
│   │   │   │   │   ├── deduplicate.py
│   │   │   │   │   ├── organize.py
│   │   │   │   │   ├── sync.py
│   │   │   │   │   └── utils.py
│   │   │   ├── git-workflow/
│   │   │   │   ├── references/
│   │   │   │   ├── scripts/
│   │   │   ├── kdocs/
│   │   │   │   ├── references/
│   │   │   │   │   ├── aippt/
│   │   │   │   │   ├── dbsheet/
│   │   │   │   │   ├── drive/
│   │   │   │   │   ├── kwiki/
│   │   │   │   │   ├── otl/
│   │   │   │   │   ├── pdf/
│   │   │   │   │   ├── sheet/
│   │   │   │   │   ├── workflows/
│   │   │   │   │   ├── wpp/
│   │   │   │   │   ├── wps/
│   │   │   │   ├── scripts/
│   │   │   ├── planning-with-files/
│   │   │   │   ├── references/
│   │   │   │   ├── scripts/
│   │   │   │   │   └── session-catchup.py
│   │   │   │   ├── templates/
│   │   │   ├── video-image-file-analysis/
│   │   │   │   ├── scripts/
│   │   │   │   │   ├── vision.py
│   │   │   │   │   └── vision_manager.py
│   │   │   ├── web-browsing/
│   │   │   │   ├── references/
│   │   │   │   ├── scripts/
│   │   │   │   │   └── search_web.py
│   │   │   ├── web-search/
│   │   │   │   ├── scripts/
│   │   │   │   │   └── search.py
│   │   │   ├── webscraper-v2/
│   │   │   │   └── webscraper.py
│   │   │   └── wecom-weisheng-scrm/
│   │   │       ├── logs/
│   │   │       ├── references/
│   │   │       ├── scripts/
│   │   │       │   ├── api_client.py
│   │   │       │   ├── chat_mode.py
│   │   │       │   ├── claw_client.py
│   │   │       │   ├── environment.py
│   │   │       │   ├── file_utils.py
│   │   │       │   ├── get_access_token.py
│   │   │       │   ├── identity_manager.py
│   │   │       │   ├── raw_fetcher.py
│   │   │       │   ├── scrm.py
│   │   │       │   └── utils.py
│   │   ├── red-teaming/
│   │   │   └── godmode/
│   │   │       ├── references/
│   │   │       ├── scripts/
│   │   │       │   ├── auto_jailbreak.py
│   │   │       │   ├── godmode_race.py
│   │   │       │   ├── load_godmode.py
│   │   │       │   └── parseltongue.py
│   │   │       ├── templates/
│   │   ├── research/
│   │   │   ├── arxiv/
│   │   │   │   ├── scripts/
│   │   │   │   │   └── search_arxiv.py
│   │   │   ├── blogwatcher/
│   │   │   ├── llm-wiki/
│   │   │   ├── polymarket/
│   │   │   │   ├── references/
│   │   │   │   ├── scripts/
│   │   │   │   │   └── polymarket.py
│   │   │   ├── research-paper-writing/
│   │   │   │   ├── references/
│   │   │   │   ├── templates/
│   │   │   │   │   ├── aaai2026/
│   │   │   │   │   ├── acl/
│   │   │   │   │   ├── colm2025/
│   │   │   │   │   ├── iclr2026/
│   │   │   │   │   ├── icml2026/
│   │   │   │   │   ├── neurips2025/
│   │   ├── smart-home/
│   │   │   ├── openhue/
│   │   ├── smart_memory/
│   │   │   ├── package_skill.py
│   │   ├── social-media/
│   │   │   ├── xurl/
│   │   ├── software-development/
│   │   │   ├── debugging-hermes-tui-commands/
│   │   │   ├── hermes-agent-skill-authoring/
│   │   │   ├── node-inspect-debugger/
│   │   │   ├── plan/
│   │   │   ├── python-debugpy/
│   │   │   ├── requesting-code-review/
│   │   │   ├── spike/
│   │   │   ├── subagent-driven-development/
│   │   │   │   ├── references/
│   │   │   ├── systematic-debugging/
│   │   │   ├── test-driven-development/
│   │   │   └── writing-plans/
│   │   ├── test_anthropic_skill/
│   │   ├── yuanbao/
│   │   ├── __init__.py
│   │   └── dual_ai.py
│   ├── tools/
│   │   ├── browser_providers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── browser_use.py
│   │   │   ├── browserbase.py
│   │   │   └── firecrawl.py
│   │   ├── builtin/
│   │   │   ├── __init__.py
│   │   │   ├── code_tools.py
│   │   │   ├── developer_tools.py
│   │   │   ├── git_tools.py
│   │   │   └── system_tools.py
│   │   ├── computer_use/
│   │   │   ├── __init__.py
│   │   │   ├── backend.py
│   │   │   ├── cua_backend.py
│   │   │   ├── schema.py
│   │   │   └── tool.py
│   │   ├── environments/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── daytona.py
│   │   │   ├── docker.py
│   │   │   ├── file_sync.py
│   │   │   ├── local.py
│   │   │   ├── managed_modal.py
│   │   │   ├── modal.py
│   │   │   ├── modal_utils.py
│   │   │   ├── singularity.py
│   │   │   ├── ssh.py
│   │   │   └── vercel_sandbox.py
│   │   ├── neutts_samples/
│   │   ├── web_providers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── brave_free.py
│   │   │   ├── ddgs.py
│   │   │   └── searxng.py
│   │   ├── __init__.py
│   │   ├── alert_tools.py
│   │   ├── analysis_tools.py
│   │   ├── ansi_strip.py
│   │   ├── approval.py
│   │   ├── automation_tools.py
│   │   ├── binary_extensions.py
│   │   ├── browser_camofox.py
│   │   ├── browser_camofox_state.py
│   │   ├── browser_cdp_tool.py
│   │   ├── browser_dialog_tool.py
│   │   ├── browser_supervisor.py
│   │   ├── browser_tool.py
│   │   ├── budget_config.py
│   │   ├── business_tools.py
│   │   ├── checkpoint_manager.py
│   │   ├── clarify_tool.py
│   │   ├── code_execution_tool.py
│   │   ├── computer_use_tool.py
│   │   ├── credential_files.py
│   │   ├── crm_tools.py
│   │   ├── cronjob_tools.py
│   │   ├── data_import_tools.py
│   │   ├── debug_helpers.py
│   │   ├── delegate_tool.py
│   │   ├── discord_tool.py
│   │   ├── dispatch_tool.py
│   │   ├── doc_tools.py
│   │   ├── env_passthrough.py
│   │   ├── export_tools.py
│   │   ├── feishu_doc_tool.py
│   │   ├── feishu_drive_tool.py
│   │   ├── file_operations.py
│   │   ├── file_state.py
│   │   ├── file_tools.py
│   │   ├── finance_analysis_tools.py
│   │   ├── fuzzy_match.py
│   │   ├── homeassistant_tool.py
│   │   ├── hr_tools.py
│   │   ├── image_generation_tool.py
│   │   ├── interrupt.py
│   │   ├── inventory_tools.py
│   │   ├── kanban_tools.py
│   │   ├── local_dev_tools.py
│   │   ├── managed_tool_gateway.py
│   │   ├── marketing_tools.py
│   │   ├── markitdown_tool.py
│   │   ├── mcp_oauth.py
│   │   ├── mcp_oauth_manager.py
│   │   ├── mcp_tool.py
│   │   ├── memory_tool.py
│   │   ├── microsoft_graph_auth.py
│   │   ├── microsoft_graph_client.py
│   │   ├── mixture_of_agents_tool.py
│   │   ├── neutts_synth.py
│   │   ├── openrouter_client.py
│   │   ├── osv_check.py
│   │   ├── patch_parser.py
│   │   ├── path_security.py
│   │   ├── process_registry.py
│   │   ├── procurement_tools.py
│   │   ├── project_management.py
│   │   ├── registry.py
│   │   ├── rl_training_tool.py
│   │   ├── scheduling_tools.py
│   │   ├── schema_sanitizer.py
│   │   ├── self_monitor.py
│   │   ├── send_message_tool.py
│   │   ├── session_search_tool.py
│   │   ├── skill_manager_tool.py
│   │   ├── skill_provenance.py
│   │   ├── skill_usage.py
│   │   ├── skills_guard.py
│   │   ├── skills_hub.py
│   │   ├── skills_sync.py
│   │   ├── skills_tool.py
│   │   ├── slash_confirm.py
│   │   ├── smart_report_tools.py
│   │   ├── sub_agent.py
│   │   ├── template_tools.py
│   │   ├── terminal_tool.py
│   │   ├── tirith_security.py
│   │   ├── todo_tool.py
│   │   ├── tool_backend_helpers.py
│   │   ├── tool_output_limits.py
│   │   ├── tool_result_storage.py
│   │   ├── transcription_tools.py
│   │   ├── tts_tool.py
│   │   ├── url_safety.py
│   │   ├── vision_tools.py
│   │   ├── voice_mode.py
│   │   ├── web_search_tools.py
│   │   ├── web_tools.py
│   │   ├── website_policy.py
│   │   ├── xai_http.py
│   │   └── yuanbao_tools.py
│   ├── toolsets/
│   │   └── __init__.py
│   ├── web_ui/
│   │   ├── harness/
│   │   │   ├── __init__.py
│   │   ├── workflow/
│   │   │   ├── __init__.py
│   │   │   ├── compiler.py
│   │   │   └── templates.py
│   │   └── __init__.py
│   ├── __init__.py
│   ├── __init___20260613_080428_724.py
│   ├── conftest.py
│   ├── hermes_constants.py
│   ├── init_db.py
│   ├── main.py
│   ├── start_opcclaw.py
│   ├── utils.py
│   ├── verify_sync.py
├── rules_project/
├── services/
│   ├── __init__.py
│   ├── ai_chatbot_service.py
│   ├── audit_service.py
│   ├── backup_service.py
│   ├── backup_tool.py
│   ├── barcode_service.py
│   ├── bi_service.py
│   ├── cache_service.py
│   ├── chart_service.py
│   ├── database_optimizer.py
│   ├── encryption_service.py
│   ├── export_service.py
│   ├── hotkey_manager.py
│   ├── i18n_service.py
│   ├── image_cache_service.py
│   ├── import_export_service.py
│   ├── lazy_load_service.py
│   ├── license_service.py
│   ├── logistics_service.py
│   ├── memory_service.py
│   ├── nl_query_service.py
│   ├── notification_service.py
│   ├── offline_queue.py
│   ├── payment_service.py
│   ├── performance_service.py
│   ├── permission_service.py
│   ├── print_service.py
│   ├── realtime_service.py
│   ├── sales_prediction_service.py
│   ├── scheduler_service.py
│   ├── sms_service.py
│   ├── sync_manager.py
│   ├── system_service.py
│   ├── system_tray.py
│   ├── template_service.py
│   ├── theme_service.py
│   ├── update_service.py
│   └── workflow_service.py
├── solar_explorer/
│   ├── __init__.py
│   ├── body_data_entries.py
│   ├── body_detail_window.py
│   ├── body_encyclopedia.py
│   ├── star_catalog_window.py
│   └── voice_reader.py
├── tools/
│   ├── environments/
│   │   ├── __init__.py
│   │   └── file_sync.py
│   ├── __init__.py
│   └── skills_sync.py
├── gen_book.py
├── main.py
├── planet_daemon.py
├── rollback_control.py
├── siri_command_handler.py
```

---

## 模块列表

- [`_archived/dedup_20260619_170800/deps.py`](./_archived/dedup_20260619_170800/deps.py.md)
- [`_archived/license_模块归档_20260619/license_crypto.py`](./_archived/license_模块归档_20260619/license_crypto.py.md)
- [`_archived/license_模块归档_20260619/license_db.py`](./_archived/license_模块归档_20260619/license_db.py.md)
- [`_archived/license_模块归档_20260619/license_service.py`](./_archived/license_模块归档_20260619/license_service.py.md)
- [`config/__init__.py`](./config/__init__.py.md)
- [`config/supabase_config.py`](./config/supabase_config.py.md)
- [`core/__init__.py`](./core/__init__.py.md)
- [`core/agent.py`](./core/agent.py.md)
- [`core/app_state.py`](./core/app_state.py.md)
- [`core/auth_service.py`](./core/auth_service.py.md)
- [`core/backup.py`](./core/backup.py.md)
- [`core/business_service.py`](./core/business_service.py.md)
- [`core/ceo_agent.py`](./core/ceo_agent.py.md)
- [`core/cloud_pull.py`](./core/cloud_pull.py.md)
- [`core/cloud_sync.py`](./core/cloud_sync.py.md)
- [`core/cloud_sync_v2.py`](./core/cloud_sync_v2.py.md)
- [`core/conflict_resolver.py`](./core/conflict_resolver.py.md)
- [`core/cosmic.py`](./core/cosmic.py.md)
- [`core/custom_fields.py`](./core/custom_fields.py.md)
- [`core/dark_theme.py`](./core/dark_theme.py.md)
- [`core/data.py`](./core/data.py.md)
- [`core/data_20260619_111935_141.py`](./core/data_20260619_111935_141.py.md)
- [`core/data_sync.py`](./core/data_sync.py.md)
- [`core/database.py`](./core/database.py.md)
- [`core/event_bus.py`](./core/event_bus.py.md)
- [`core/excel_export.py`](./core/excel_export.py.md)
- [`core/llm_client.py`](./core/llm_client.py.md)
- [`core/machine_code.py`](./core/machine_code.py.md)
- [`core/mobile_api.py`](./core/mobile_api.py.md)
- [`core/module_manager.py`](./core/module_manager.py.md)
- [`core/notification_cron.py`](./core/notification_cron.py.md)
- [`core/notification_service.py`](./core/notification_service.py.md)
- [`core/notification_toast.py`](./core/notification_toast.py.md)
- [`core/operation_log.py`](./core/operation_log.py.md)
- [`core/oplog.py`](./core/oplog.py.md)
- [`core/paths.py`](./core/paths.py.md)
- [`core/planet_painter.py`](./core/planet_painter.py.md)
- [`core/planet_painter_20260614_151048_302.py`](./core/planet_painter_20260614_151048_302.py.md)
- [`core/reconciliation.py`](./core/reconciliation.py.md)
- [`core/scheduled_tasks.py`](./core/scheduled_tasks.py.md)
- [`core/shapes/__init__.py`](./core/shapes/__init__.py.md)
- [`core/shapes/alien.py`](./core/shapes/alien.py.md)
- [`core/shapes/black_hole.py`](./core/shapes/black_hole.py.md)
- [`core/shapes/classic.py`](./core/shapes/classic.py.md)
- [`core/shapes/classic_20260614_184255_598.py`](./core/shapes/classic_20260614_184255_598.py.md)
- [`core/shapes/comet.py`](./core/shapes/comet.py.md)
- [`core/shapes/corvette.py`](./core/shapes/corvette.py.md)
- [`core/shapes/crystal_alien.py`](./core/shapes/crystal_alien.py.md)
- [`core/shapes/destroyer.py`](./core/shapes/destroyer.py.md)
- [`core/shapes/dreadnought.py`](./core/shapes/dreadnought.py.md)
- [`core/shapes/energy_being.py`](./core/shapes/energy_being.py.md)
- [`core/shapes/fighter.py`](./core/shapes/fighter.py.md)
- [`core/shapes/gas_giant.py`](./core/shapes/gas_giant.py.md)
- [`core/shapes/gas_giant_20260614_184255_426.py`](./core/shapes/gas_giant_20260614_184255_426.py.md)
- [`core/shapes/ghost_alien.py`](./core/shapes/ghost_alien.py.md)
- [`core/shapes/grey_alien.py`](./core/shapes/grey_alien.py.md)
- [`core/shapes/ice_giant.py`](./core/shapes/ice_giant.py.md)
- [`core/shapes/ice_giant_20260614_184255_207.py`](./core/shapes/ice_giant_20260614_184255_207.py.md)
- [`core/shapes/interceptor.py`](./core/shapes/interceptor.py.md)
- [`core/shapes/jellyfish_alien.py`](./core/shapes/jellyfish_alien.py.md)
- [`core/shapes/lava_planet.py`](./core/shapes/lava_planet.py.md)
- [`core/shapes/lava_planet_20260614_184255_101.py`](./core/shapes/lava_planet_20260614_184255_101.py.md)
- [`core/shapes/mars.py`](./core/shapes/mars.py.md)
- [`core/shapes/mars_20260614_184255_257.py`](./core/shapes/mars_20260614_184255_257.py.md)
- [`core/shapes/mercury.py`](./core/shapes/mercury.py.md)
- [`core/shapes/nebula.py`](./core/shapes/nebula.py.md)
- [`core/shapes/neutron_star.py`](./core/shapes/neutron_star.py.md)
- [`core/shapes/octopus_alien.py`](./core/shapes/octopus_alien.py.md)
- [`core/shapes/pluto.py`](./core/shapes/pluto.py.md)
- [`core/shapes/pulsar.py`](./core/shapes/pulsar.py.md)
- [`core/shapes/red_giant.py`](./core/shapes/red_giant.py.md)
- [`core/shapes/reptilian.py`](./core/shapes/reptilian.py.md)
- [`core/shapes/robot_alien.py`](./core/shapes/robot_alien.py.md)
- [`core/shapes/saturn.py`](./core/shapes/saturn.py.md)
- [`core/shapes/scout.py`](./core/shapes/scout.py.md)
- [`core/shapes/starship.py`](./core/shapes/starship.py.md)
- [`core/shapes/transporter.py`](./core/shapes/transporter.py.md)
- [`core/shapes/uranus.py`](./core/shapes/uranus.py.md)
- [`core/shapes/venus.py`](./core/shapes/venus.py.md)
- [`core/shapes/white_dwarf.py`](./core/shapes/white_dwarf.py.md)
- [`core/shapes/wormhole.py`](./core/shapes/wormhole.py.md)
- [`core/simple_sync.py`](./core/simple_sync.py.md)
- [`core/smart_report.py`](./core/smart_report.py.md)
- [`core/storage.py`](./core/storage.py.md)
- [`core/supabase_client.py`](./core/supabase_client.py.md)
- [`core/sync_bridge.py`](./core/sync_bridge.py.md)
- [`core/sync_decorator.py`](./core/sync_decorator.py.md)
- [`core/sync_integration.py`](./core/sync_integration.py.md)
- [`core/sync_manager.py`](./core/sync_manager.py.md)
- [`core/sync_optimized.py`](./core/sync_optimized.py.md)
- [`core/texture_mapper.py`](./core/texture_mapper.py.md)
- [`core/triple_sync.py`](./core/triple_sync.py.md)
- [`core/user_dao.py`](./core/user_dao.py.md)
- [`core/voice.py`](./core/voice.py.md)
- [`core/workflow_engine.py`](./core/workflow_engine.py.md)
- [`gen_book.py`](./gen_book.py.md)
- [`main.py`](./main.py.md)
- [`modules/__init__.py`](./modules/__init__.py.md)
- [`modules/account/__init__.py`](./modules/account/__init__.py.md)
- [`modules/account/account_activation.py`](./modules/account/account_activation.py.md)
- [`modules/account/account_update.py`](./modules/account/account_update.py.md)
- [`modules/account/activation_service.py`](./modules/account/activation_service.py.md)
- [`modules/account/activation_stats.py`](./modules/account/activation_stats.py.md)
- [`modules/account/activation_stats_service.py`](./modules/account/activation_stats_service.py.md)
- [`modules/account/license_local.py`](./modules/account/license_local.py.md)
- [`modules/admin/__init__.py`](./modules/admin/__init__.py.md)
- [`modules/admin/admin_activation.py`](./modules/admin/admin_activation.py.md)
- [`modules/admin/admin_backup.py`](./modules/admin/admin_backup.py.md)
- [`modules/admin/admin_data.py`](./modules/admin/admin_data.py.md)
- [`modules/admin/admin_data_mgmt.py`](./modules/admin/admin_data_mgmt.py.md)
- [`modules/admin/admin_finance.py`](./modules/admin/admin_finance.py.md)
- [`modules/admin/admin_log.py`](./modules/admin/admin_log.py.md)
- [`modules/admin/admin_orders.py`](./modules/admin/admin_orders.py.md)
- [`modules/admin/admin_product.py`](./modules/admin/admin_product.py.md)
- [`modules/admin/admin_service.py`](./modules/admin/admin_service.py.md)
- [`modules/admin/admin_settings.py`](./modules/admin/admin_settings.py.md)
- [`modules/admin/admin_staff.py`](./modules/admin/admin_staff.py.md)
- [`modules/admin/admin_strategy.py`](./modules/admin/admin_strategy.py.md)
- [`modules/admin/admin_user.py`](./modules/admin/admin_user.py.md)
- [`modules/admin/admin_window.py`](./modules/admin/admin_window.py.md)
- [`modules/admin/cascade_delete.py`](./modules/admin/cascade_delete.py.md)
- [`modules/admin/strategy_dao.py`](./modules/admin/strategy_dao.py.md)
- [`modules/astronomy/__init__.py`](./modules/astronomy/__init__.py.md)
- [`modules/astronomy/hub.py`](./modules/astronomy/hub.py.md)
- [`modules/astronomy/solar_system/__init__.py`](./modules/astronomy/solar_system/__init__.py.md)
- [`modules/astronomy/solar_system/data.py`](./modules/astronomy/solar_system/data.py.md)
- [`modules/astronomy/solar_system/planets/__init__.py`](./modules/astronomy/solar_system/planets/__init__.py.md)
- [`modules/astronomy/solar_system/planets/_base.py`](./modules/astronomy/solar_system/planets/_base.py.md)
- [`modules/astronomy/solar_system/planets/callisto/__init__.py`](./modules/astronomy/solar_system/planets/callisto/__init__.py.md)
- [`modules/astronomy/solar_system/planets/ceres/__init__.py`](./modules/astronomy/solar_system/planets/ceres/__init__.py.md)
- [`modules/astronomy/solar_system/planets/earth/__init__.py`](./modules/astronomy/solar_system/planets/earth/__init__.py.md)
- [`modules/astronomy/solar_system/planets/enceladus/__init__.py`](./modules/astronomy/solar_system/planets/enceladus/__init__.py.md)
- [`modules/astronomy/solar_system/planets/eris/__init__.py`](./modules/astronomy/solar_system/planets/eris/__init__.py.md)
- [`modules/astronomy/solar_system/planets/europa/__init__.py`](./modules/astronomy/solar_system/planets/europa/__init__.py.md)
- [`modules/astronomy/solar_system/planets/ganymede/__init__.py`](./modules/astronomy/solar_system/planets/ganymede/__init__.py.md)
- [`modules/astronomy/solar_system/planets/haumea/__init__.py`](./modules/astronomy/solar_system/planets/haumea/__init__.py.md)
- [`modules/astronomy/solar_system/planets/io/__init__.py`](./modules/astronomy/solar_system/planets/io/__init__.py.md)
- [`modules/astronomy/solar_system/planets/jupiter/__init__.py`](./modules/astronomy/solar_system/planets/jupiter/__init__.py.md)
- [`modules/astronomy/solar_system/planets/makemake/__init__.py`](./modules/astronomy/solar_system/planets/makemake/__init__.py.md)
- [`modules/astronomy/solar_system/planets/mars/__init__.py`](./modules/astronomy/solar_system/planets/mars/__init__.py.md)
- [`modules/astronomy/solar_system/planets/mercury/__init__.py`](./modules/astronomy/solar_system/planets/mercury/__init__.py.md)
- [`modules/astronomy/solar_system/planets/moon/__init__.py`](./modules/astronomy/solar_system/planets/moon/__init__.py.md)
- [`modules/astronomy/solar_system/planets/neptune/__init__.py`](./modules/astronomy/solar_system/planets/neptune/__init__.py.md)
- [`modules/astronomy/solar_system/planets/pluto/__init__.py`](./modules/astronomy/solar_system/planets/pluto/__init__.py.md)
- [`modules/astronomy/solar_system/planets/saturn/__init__.py`](./modules/astronomy/solar_system/planets/saturn/__init__.py.md)
- [`modules/astronomy/solar_system/planets/sun/__init__.py`](./modules/astronomy/solar_system/planets/sun/__init__.py.md)
- [`modules/astronomy/solar_system/planets/titan/__init__.py`](./modules/astronomy/solar_system/planets/titan/__init__.py.md)
- [`modules/astronomy/solar_system/planets/uranus/__init__.py`](./modules/astronomy/solar_system/planets/uranus/__init__.py.md)
- [`modules/astronomy/solar_system/planets/venus/__init__.py`](./modules/astronomy/solar_system/planets/venus/__init__.py.md)
- [`modules/astronomy/solar_system/renderer.py`](./modules/astronomy/solar_system/renderer.py.md)
- [`modules/astronomy/solar_system/window.py`](./modules/astronomy/solar_system/window.py.md)
- [`modules/astronomy/star_catalog/__init__.py`](./modules/astronomy/star_catalog/__init__.py.md)
- [`modules/astronomy/star_catalog/catalog.py`](./modules/astronomy/star_catalog/catalog.py.md)
- [`modules/astronomy/star_catalog/data_entries.py`](./modules/astronomy/star_catalog/data_entries.py.md)
- [`modules/astronomy/star_catalog/detail.py`](./modules/astronomy/star_catalog/detail.py.md)
- [`modules/astronomy/star_catalog/encyclopedia.py`](./modules/astronomy/star_catalog/encyclopedia.py.md)
- [`modules/astronomy/star_catalog/voice.py`](./modules/astronomy/star_catalog/voice.py.md)
- [`modules/auth/__init__.py`](./modules/auth/__init__.py.md)
- [`modules/auth/activation_gate.py`](./modules/auth/activation_gate.py.md)
- [`modules/auth/admin_login_dialog.py`](./modules/auth/admin_login_dialog.py.md)
- [`modules/auth/admin_login_window.py`](./modules/auth/admin_login_window.py.md)
- [`modules/auth/auth_service.py`](./modules/auth/auth_service.py.md)
- [`modules/auth/change_password_dialog.py`](./modules/auth/change_password_dialog.py.md)
- [`modules/auth/connect_window.py`](./modules/auth/connect_window.py.md)
- [`modules/auth/dao/user_dao.py`](./modules/auth/dao/user_dao.py.md)
- [`modules/auth/login_window.py`](./modules/auth/login_window.py.md)
- [`modules/auth/model_config_panel.py`](./modules/auth/model_config_panel.py.md)
- [`modules/auth/model_setup_window.py`](./modules/auth/model_setup_window.py.md)
- [`modules/auth/register_window.py`](./modules/auth/register_window.py.md)
- [`modules/auth/select_mode_window.py`](./modules/auth/select_mode_window.py.md)
- [`modules/auth/service/cloud_api.py`](./modules/auth/service/cloud_api.py.md)
- [`modules/auth/upgrade_window.py`](./modules/auth/upgrade_window.py.md)
- [`modules/business/__init__.py`](./modules/business/__init__.py.md)
- [`modules/business/business_window.py`](./modules/business/business_window.py.md)
- [`modules/business/customer_service.py`](./modules/business/customer_service.py.md)
- [`modules/business/customer_window.py`](./modules/business/customer_window.py.md)
- [`modules/business/finance_service.py`](./modules/business/finance_service.py.md)
- [`modules/business/finance_window.py`](./modules/business/finance_window.py.md)
- [`modules/business/order_service.py`](./modules/business/order_service.py.md)
- [`modules/business/order_window.py`](./modules/business/order_window.py.md)
- [`modules/business/product_service.py`](./modules/business/product_service.py.md)
- [`modules/business/product_window.py`](./modules/business/product_window.py.md)
- [`modules/common/advanced_filter_window.py`](./modules/common/advanced_filter_window.py.md)
- [`modules/common/custom_field_window.py`](./modules/common/custom_field_window.py.md)
- [`modules/dashboard/__init__.py`](./modules/dashboard/__init__.py.md)
- [`modules/dashboard/dashboard_window.py`](./modules/dashboard/dashboard_window.py.md)
- [`modules/data_center/__init__.py`](./modules/data_center/__init__.py.md)
- [`modules/data_center/bi_window.py`](./modules/data_center/bi_window.py.md)
- [`modules/data_center/chart_window.py`](./modules/data_center/chart_window.py.md)
- [`modules/data_center/dashboard_window_v2.py`](./modules/data_center/dashboard_window_v2.py.md)
- [`modules/data_center/dashboard_window_v3.py`](./modules/data_center/dashboard_window_v3.py.md)
- [`modules/data_center/data_window.py`](./modules/data_center/data_window.py.md)
- [`modules/data_center/report_service.py`](./modules/data_center/report_service.py.md)
- [`modules/data_center/report_service_v2.py`](./modules/data_center/report_service_v2.py.md)
- [`modules/data_center/report_window.py`](./modules/data_center/report_window.py.md)
- [`modules/data_center/smart_report_window.py`](./modules/data_center/smart_report_window.py.md)
- [`modules/i18n/i18n_window.py`](./modules/i18n/i18n_window.py.md)
- [`modules/industry/industry_adapter.py`](./modules/industry/industry_adapter.py.md)
- [`modules/industry/industry_config.py`](./modules/industry/industry_config.py.md)
- [`modules/industry/industry_report.py`](./modules/industry/industry_report.py.md)
- [`modules/industry/industry_window.py`](./modules/industry/industry_window.py.md)
- [`modules/intelligence/__init__.py`](./modules/intelligence/__init__.py.md)
- [`modules/intelligence/_ai_shared.py`](./modules/intelligence/_ai_shared.py.md)
- [`modules/intelligence/_ai_widgets.py`](./modules/intelligence/_ai_widgets.py.md)
- [`modules/intelligence/_ai_widgets_anomaly.py`](./modules/intelligence/_ai_widgets_anomaly.py.md)
- [`modules/intelligence/_ai_widgets_business.py`](./modules/intelligence/_ai_widgets_business.py.md)
- [`modules/intelligence/_ai_widgets_core.py`](./modules/intelligence/_ai_widgets_core.py.md)
- [`modules/intelligence/_ai_widgets_recommendation.py`](./modules/intelligence/_ai_widgets_recommendation.py.md)
- [`modules/intelligence/_ai_widgets_visualization.py`](./modules/intelligence/_ai_widgets_visualization.py.md)
- [`modules/intelligence/_ai_widgets_workflow.py`](./modules/intelligence/_ai_widgets_workflow.py.md)
- [`modules/intelligence/_chat_dialog.py`](./modules/intelligence/_chat_dialog.py.md)
- [`modules/intelligence/_compat.py`](./modules/intelligence/_compat.py.md)
- [`modules/intelligence/_model_manager.py`](./modules/intelligence/_model_manager.py.md)
- [`modules/intelligence/_model_manager_download.py`](./modules/intelligence/_model_manager_download.py.md)
- [`modules/intelligence/_model_manager_ollama.py`](./modules/intelligence/_model_manager_ollama.py.md)
- [`modules/intelligence/_navigation_hud.py`](./modules/intelligence/_navigation_hud.py.md)
- [`modules/intelligence/_shell_dialogs.py`](./modules/intelligence/_shell_dialogs.py.md)
- [`modules/intelligence/_stubs.py`](./modules/intelligence/_stubs.py.md)
- [`modules/intelligence/account_window.py`](./modules/intelligence/account_window.py.md)
- [`modules/intelligence/agent_bridge.py`](./modules/intelligence/agent_bridge.py.md)
- [`modules/intelligence/agent_bridge_models.py`](./modules/intelligence/agent_bridge_models.py.md)
- [`modules/intelligence/agent_bridge_tools.py`](./modules/intelligence/agent_bridge_tools.py.md)
- [`modules/intelligence/agent_bridge_workers.py`](./modules/intelligence/agent_bridge_workers.py.md)
- [`modules/intelligence/ai_assistant_window.py`](./modules/intelligence/ai_assistant_window.py.md)
- [`modules/intelligence/ai_center_window.py`](./modules/intelligence/ai_center_window.py.md)
- [`modules/intelligence/ai_chat_styles.py`](./modules/intelligence/ai_chat_styles.py.md)
- [`modules/intelligence/ai_chat_window.py`](./modules/intelligence/ai_chat_window.py.md)
- [`modules/intelligence/ai_dashboard_window.py`](./modules/intelligence/ai_dashboard_window.py.md)
- [`modules/intelligence/ai_features_ai_dashboard.py`](./modules/intelligence/ai_features_ai_dashboard.py.md)
- [`modules/intelligence/ai_features_customer_ai.py`](./modules/intelligence/ai_features_customer_ai.py.md)
- [`modules/intelligence/ai_features_inventory_ai.py`](./modules/intelligence/ai_features_inventory_ai.py.md)
- [`modules/intelligence/ai_features_pricing_ai.py`](./modules/intelligence/ai_features_pricing_ai.py.md)
- [`modules/intelligence/ai_features_sales_ai.py`](./modules/intelligence/ai_features_sales_ai.py.md)
- [`modules/intelligence/analysis_tools.py`](./modules/intelligence/analysis_tools.py.md)
- [`modules/intelligence/anomaly_detector.py`](./modules/intelligence/anomaly_detector.py.md)
- [`modules/intelligence/auto_task_executor.py`](./modules/intelligence/auto_task_executor.py.md)
- [`modules/intelligence/backup_p02/agent_bridge.py`](./modules/intelligence/backup_p02/agent_bridge.py.md)
- [`modules/intelligence/backup_p02/ai_chat_window.py`](./modules/intelligence/backup_p02/ai_chat_window.py.md)
- [`modules/intelligence/backup_p02/intelligence_window.py`](./modules/intelligence/backup_p02/intelligence_window.py.md)
- [`modules/intelligence/backup_p02/opcclaw_floating_planet.py`](./modules/intelligence/backup_p02/opcclaw_floating_planet.py.md)
- [`modules/intelligence/batch_text.py`](./modules/intelligence/batch_text.py.md)
- [`modules/intelligence/business_ai_assistant.py`](./modules/intelligence/business_ai_assistant.py.md)
- [`modules/intelligence/business_tools.py`](./modules/intelligence/business_tools.py.md)
- [`modules/intelligence/chat_session_manager.py`](./modules/intelligence/chat_session_manager.py.md)
- [`modules/intelligence/compress_tool.py`](./modules/intelligence/compress_tool.py.md)
- [`modules/intelligence/core/__init__.py`](./modules/intelligence/core/__init__.py.md)
- [`modules/intelligence/core/llm_backend.py`](./modules/intelligence/core/llm_backend.py.md)
- [`modules/intelligence/crm_tools.py`](./modules/intelligence/crm_tools.py.md)
- [`modules/intelligence/data_import_tools.py`](./modules/intelligence/data_import_tools.py.md)
- [`modules/intelligence/data_visualization.py`](./modules/intelligence/data_visualization.py.md)
- [`modules/intelligence/db_helper.py`](./modules/intelligence/db_helper.py.md)
- [`modules/intelligence/download_dialog.py`](./modules/intelligence/download_dialog.py.md)
- [`modules/intelligence/editor_window.py`](./modules/intelligence/editor_window.py.md)
- [`modules/intelligence/enhanced/__init__.py`](./modules/intelligence/enhanced/__init__.py.md)
- [`modules/intelligence/enhanced/enhanced_tools.py`](./modules/intelligence/enhanced/enhanced_tools.py.md)
- [`modules/intelligence/enhanced_chat.py`](./modules/intelligence/enhanced_chat.py.md)
- [`modules/intelligence/event_trigger.py`](./modules/intelligence/event_trigger.py.md)
- [`modules/intelligence/file_rename_tools.py`](./modules/intelligence/file_rename_tools.py.md)
- [`modules/intelligence/finance_analysis_tools.py`](./modules/intelligence/finance_analysis_tools.py.md)
- [`modules/intelligence/floating_planet_anim_mixin.py`](./modules/intelligence/floating_planet_anim_mixin.py.md)
- [`modules/intelligence/floating_planet_draw_mixin.py`](./modules/intelligence/floating_planet_draw_mixin.py.md)
- [`modules/intelligence/floating_planet_menu_mixin.py`](./modules/intelligence/floating_planet_menu_mixin.py.md)
- [`modules/intelligence/hr_tools.py`](./modules/intelligence/hr_tools.py.md)
- [`modules/intelligence/img_converter.py`](./modules/intelligence/img_converter.py.md)
- [`modules/intelligence/intelligence_integration.py`](./modules/intelligence/intelligence_integration.py.md)
- [`modules/intelligence/intelligence_window.py`](./modules/intelligence/intelligence_window.py.md)
- [`modules/intelligence/inventory_tools.py`](./modules/intelligence/inventory_tools.py.md)
- [`modules/intelligence/json_tools.py`](./modules/intelligence/json_tools.py.md)
- [`modules/intelligence/key_manager.py`](./modules/intelligence/key_manager.py.md)
- [`modules/intelligence/knowledge_base.py`](./modules/intelligence/knowledge_base.py.md)
- [`modules/intelligence/marketing_tools.py`](./modules/intelligence/marketing_tools.py.md)
- [`modules/intelligence/model_config.py`](./modules/intelligence/model_config.py.md)
- [`modules/intelligence/monitor_dashboard.py`](./modules/intelligence/monitor_dashboard.py.md)
- [`modules/intelligence/offline_analyzer.py`](./modules/intelligence/offline_analyzer.py.md)
- [`modules/intelligence/opcclaw_floating_planet.py`](./modules/intelligence/opcclaw_floating_planet.py.md)
- [`modules/intelligence/password_tools.py`](./modules/intelligence/password_tools.py.md)
- [`modules/intelligence/performance_monitor.py`](./modules/intelligence/performance_monitor.py.md)
- [`modules/intelligence/predictor_window.py`](./modules/intelligence/predictor_window.py.md)
- [`modules/intelligence/quick_actions.py`](./modules/intelligence/quick_actions.py.md)
- [`modules/intelligence/rag_injector.py`](./modules/intelligence/rag_injector.py.md)
- [`modules/intelligence/recommendation_engine.py`](./modules/intelligence/recommendation_engine.py.md)
- [`modules/intelligence/report_generator.py`](./modules/intelligence/report_generator.py.md)
- [`modules/intelligence/sales_predictor.py`](./modules/intelligence/sales_predictor.py.md)
- [`modules/intelligence/scan_window.py`](./modules/intelligence/scan_window.py.md)
- [`modules/intelligence/screen_recorder.py`](./modules/intelligence/screen_recorder.py.md)
- [`modules/intelligence/self_monitor.py`](./modules/intelligence/self_monitor.py.md)
- [`modules/intelligence/session_context.py`](./modules/intelligence/session_context.py.md)
- [`modules/intelligence/smart_assistant.py`](./modules/intelligence/smart_assistant.py.md)
- [`modules/intelligence/smart_report_tools.py`](./modules/intelligence/smart_report_tools.py.md)
- [`modules/intelligence/smart_workflow.py`](./modules/intelligence/smart_workflow.py.md)
- [`modules/intelligence/solar_system_data.py`](./modules/intelligence/solar_system_data.py.md)
- [`modules/intelligence/solar_system_window.py`](./modules/intelligence/solar_system_window.py.md)
- [`modules/intelligence/starship_painter.py`](./modules/intelligence/starship_painter.py.md)
- [`modules/intelligence/super_intelligence.py`](./modules/intelligence/super_intelligence.py.md)
- [`modules/intelligence/system_hub_window.py`](./modules/intelligence/system_hub_window.py.md)
- [`modules/intelligence/system_monitor.py`](./modules/intelligence/system_monitor.py.md)
- [`modules/intelligence/text_editor.py`](./modules/intelligence/text_editor.py.md)
- [`modules/intelligence/timestamp_tools.py`](./modules/intelligence/timestamp_tools.py.md)
- [`modules/intelligence/tool_registry.py`](./modules/intelligence/tool_registry.py.md)
- [`modules/intelligence/tools_window.py`](./modules/intelligence/tools_window.py.md)
- [`modules/intelligence/usb_scanner.py`](./modules/intelligence/usb_scanner.py.md)
- [`modules/intelligence/vault_window.py`](./modules/intelligence/vault_window.py.md)
- [`modules/intelligence/voice_interface.py`](./modules/intelligence/voice_interface.py.md)
- [`modules/intelligence/whisper_recognizer.py`](./modules/intelligence/whisper_recognizer.py.md)
- [`modules/intelligence/window_top_tools.py`](./modules/intelligence/window_top_tools.py.md)
- [`modules/intelligence/workflow_engine.py`](./modules/intelligence/workflow_engine.py.md)
- [`modules/notification/notification_window.py`](./modules/notification/notification_window.py.md)
- [`modules/permission/permission_window.py`](./modules/permission/permission_window.py.md)
- [`modules/personnel/__init__.py`](./modules/personnel/__init__.py.md)
- [`modules/personnel/distribution_service.py`](./modules/personnel/distribution_service.py.md)
- [`modules/personnel/distribution_window.py`](./modules/personnel/distribution_window.py.md)
- [`modules/personnel/member_service.py`](./modules/personnel/member_service.py.md)
- [`modules/personnel/member_window.py`](./modules/personnel/member_window.py.md)
- [`modules/personnel/personnel_window.py`](./modules/personnel/personnel_window.py.md)
- [`modules/personnel/staff_service.py`](./modules/personnel/staff_service.py.md)
- [`modules/personnel/staff_window.py`](./modules/personnel/staff_window.py.md)
- [`modules/personnel/wallet_service.py`](./modules/personnel/wallet_service.py.md)
- [`modules/personnel/wallet_window.py`](./modules/personnel/wallet_window.py.md)
- [`modules/startup/startup_selector_window.py`](./modules/startup/startup_selector_window.py.md)
- [`modules/system/__init__.py`](./modules/system/__init__.py.md)
- [`modules/system/_archived/activation_window.py`](./modules/system/_archived/activation_window.py.md)
- [`modules/system/_archived/base_info_window.py`](./modules/system/_archived/base_info_window.py.md)
- [`modules/system/_archived/cloud_window.py`](./modules/system/_archived/cloud_window.py.md)
- [`modules/system/_archived/logs_window.py`](./modules/system/_archived/logs_window.py.md)
- [`modules/system/_archived/system_window.py`](./modules/system/_archived/system_window.py.md)
- [`modules/system/_archived/update_dialog.py`](./modules/system/_archived/update_dialog.py.md)
- [`modules/system/astronomy_hub_window.py`](./modules/system/astronomy_hub_window.py.md)
- [`modules/system/audit_window.py`](./modules/system/audit_window.py.md)
- [`modules/system/base_info_window.py`](./modules/system/base_info_window.py.md)
- [`modules/system/cloud_model_panel.py`](./modules/system/cloud_model_panel.py.md)
- [`modules/system/cloud_module.py`](./modules/system/cloud_module.py.md)
- [`modules/system/cloud_server_window.py`](./modules/system/cloud_server_window.py.md)
- [`modules/system/cloud_window.py`](./modules/system/cloud_window.py.md)
- [`modules/system/logs_window.py`](./modules/system/logs_window.py.md)
- [`modules/system/system_hub_window.py`](./modules/system/system_hub_window.py.md)
- [`modules/system/system_logs_service.py`](./modules/system/system_logs_service.py.md)
- [`modules/system_logs/system_logs_service.py`](./modules/system_logs/system_logs_service.py.md)
- [`modules/system_logs/system_logs_window.py`](./modules/system_logs/system_logs_window.py.md)
- [`modules/workflow/workflow_window.py`](./modules/workflow/workflow_window.py.md)
- [`opcclaw/__init__.py`](./opcclaw/__init__.py.md)
- [`opcclaw/__init___20260613_080428_724.py`](./opcclaw/__init___20260613_080428_724.py.md)
- [`opcclaw/adapters/__init__.py`](./opcclaw/adapters/__init__.py.md)
- [`opcclaw/adapters/channels/__init__.py`](./opcclaw/adapters/channels/__init__.py.md)
- [`opcclaw/adapters/channels/dingtalk.py`](./opcclaw/adapters/channels/dingtalk.py.md)
- [`opcclaw/adapters/channels/discord.py`](./opcclaw/adapters/channels/discord.py.md)
- [`opcclaw/adapters/channels/feishu.py`](./opcclaw/adapters/channels/feishu.py.md)
- [`opcclaw/adapters/channels/router.py`](./opcclaw/adapters/channels/router.py.md)
- [`opcclaw/adapters/channels/slack.py`](./opcclaw/adapters/channels/slack.py.md)
- [`opcclaw/adapters/channels/telegram.py`](./opcclaw/adapters/channels/telegram.py.md)
- [`opcclaw/agent/__init__.py`](./opcclaw/agent/__init__.py.md)
- [`opcclaw/agent/account_usage.py`](./opcclaw/agent/account_usage.py.md)
- [`opcclaw/agent/anthropic_adapter.py`](./opcclaw/agent/anthropic_adapter.py.md)
- [`opcclaw/agent/auxiliary_client.py`](./opcclaw/agent/auxiliary_client.py.md)
- [`opcclaw/agent/bedrock_adapter.py`](./opcclaw/agent/bedrock_adapter.py.md)
- [`opcclaw/agent/codex_responses_adapter.py`](./opcclaw/agent/codex_responses_adapter.py.md)
- [`opcclaw/agent/context_compressor.py`](./opcclaw/agent/context_compressor.py.md)
- [`opcclaw/agent/context_engine.py`](./opcclaw/agent/context_engine.py.md)
- [`opcclaw/agent/context_references.py`](./opcclaw/agent/context_references.py.md)
- [`opcclaw/agent/copilot_acp_client.py`](./opcclaw/agent/copilot_acp_client.py.md)
- [`opcclaw/agent/credential_pool.py`](./opcclaw/agent/credential_pool.py.md)
- [`opcclaw/agent/credential_sources.py`](./opcclaw/agent/credential_sources.py.md)
- [`opcclaw/agent/curator.py`](./opcclaw/agent/curator.py.md)
- [`opcclaw/agent/curator_backup.py`](./opcclaw/agent/curator_backup.py.md)
- [`opcclaw/agent/display.py`](./opcclaw/agent/display.py.md)
- [`opcclaw/agent/error_classifier.py`](./opcclaw/agent/error_classifier.py.md)
- [`opcclaw/agent/file_safety.py`](./opcclaw/agent/file_safety.py.md)
- [`opcclaw/agent/gemini_cloudcode_adapter.py`](./opcclaw/agent/gemini_cloudcode_adapter.py.md)
- [`opcclaw/agent/gemini_native_adapter.py`](./opcclaw/agent/gemini_native_adapter.py.md)
- [`opcclaw/agent/gemini_schema.py`](./opcclaw/agent/gemini_schema.py.md)
- [`opcclaw/agent/google_code_assist.py`](./opcclaw/agent/google_code_assist.py.md)
- [`opcclaw/agent/google_oauth.py`](./opcclaw/agent/google_oauth.py.md)
- [`opcclaw/agent/i18n.py`](./opcclaw/agent/i18n.py.md)
- [`opcclaw/agent/image_gen_provider.py`](./opcclaw/agent/image_gen_provider.py.md)
- [`opcclaw/agent/image_gen_registry.py`](./opcclaw/agent/image_gen_registry.py.md)
- [`opcclaw/agent/image_routing.py`](./opcclaw/agent/image_routing.py.md)
- [`opcclaw/agent/insights.py`](./opcclaw/agent/insights.py.md)
- [`opcclaw/agent/lmstudio_reasoning.py`](./opcclaw/agent/lmstudio_reasoning.py.md)
- [`opcclaw/agent/manual_compression_feedback.py`](./opcclaw/agent/manual_compression_feedback.py.md)
- [`opcclaw/agent/memory_manager.py`](./opcclaw/agent/memory_manager.py.md)
- [`opcclaw/agent/memory_provider.py`](./opcclaw/agent/memory_provider.py.md)
- [`opcclaw/agent/model_metadata.py`](./opcclaw/agent/model_metadata.py.md)
- [`opcclaw/agent/models_dev.py`](./opcclaw/agent/models_dev.py.md)
- [`opcclaw/agent/moonshot_schema.py`](./opcclaw/agent/moonshot_schema.py.md)
- [`opcclaw/agent/nous_rate_guard.py`](./opcclaw/agent/nous_rate_guard.py.md)
- [`opcclaw/agent/onboarding.py`](./opcclaw/agent/onboarding.py.md)
- [`opcclaw/agent/prompt_builder.py`](./opcclaw/agent/prompt_builder.py.md)
- [`opcclaw/agent/prompt_caching.py`](./opcclaw/agent/prompt_caching.py.md)
- [`opcclaw/agent/rate_limit_tracker.py`](./opcclaw/agent/rate_limit_tracker.py.md)
- [`opcclaw/agent/redact.py`](./opcclaw/agent/redact.py.md)
- [`opcclaw/agent/retry_utils.py`](./opcclaw/agent/retry_utils.py.md)
- [`opcclaw/agent/shell_hooks.py`](./opcclaw/agent/shell_hooks.py.md)
- [`opcclaw/agent/skill_commands.py`](./opcclaw/agent/skill_commands.py.md)
- [`opcclaw/agent/skill_preprocessing.py`](./opcclaw/agent/skill_preprocessing.py.md)
- [`opcclaw/agent/skill_utils.py`](./opcclaw/agent/skill_utils.py.md)
- [`opcclaw/agent/subdirectory_hints.py`](./opcclaw/agent/subdirectory_hints.py.md)
- [`opcclaw/agent/think_scrubber.py`](./opcclaw/agent/think_scrubber.py.md)
- [`opcclaw/agent/title_generator.py`](./opcclaw/agent/title_generator.py.md)
- [`opcclaw/agent/tool_guardrails.py`](./opcclaw/agent/tool_guardrails.py.md)
- [`opcclaw/agent/trajectory.py`](./opcclaw/agent/trajectory.py.md)
- [`opcclaw/agent/transports/__init__.py`](./opcclaw/agent/transports/__init__.py.md)
- [`opcclaw/agent/transports/anthropic.py`](./opcclaw/agent/transports/anthropic.py.md)
- [`opcclaw/agent/transports/base.py`](./opcclaw/agent/transports/base.py.md)
- [`opcclaw/agent/transports/bedrock.py`](./opcclaw/agent/transports/bedrock.py.md)
- [`opcclaw/agent/transports/chat_completions.py`](./opcclaw/agent/transports/chat_completions.py.md)
- [`opcclaw/agent/transports/codex.py`](./opcclaw/agent/transports/codex.py.md)
- [`opcclaw/agent/transports/types.py`](./opcclaw/agent/transports/types.py.md)
- [`opcclaw/agent/usage_pricing.py`](./opcclaw/agent/usage_pricing.py.md)
- [`opcclaw/conftest.py`](./opcclaw/conftest.py.md)
- [`opcclaw/core/__init__.py`](./opcclaw/core/__init__.py.md)
- [`opcclaw/core/agent_delegate.py`](./opcclaw/core/agent_delegate.py.md)
- [`opcclaw/core/agent_loop.py`](./opcclaw/core/agent_loop.py.md)
- [`opcclaw/core/chat_engine.py`](./opcclaw/core/chat_engine.py.md)
- [`opcclaw/core/clarify_system.py`](./opcclaw/core/clarify_system.py.md)
- [`opcclaw/core/cloud_sync.py`](./opcclaw/core/cloud_sync.py.md)
- [`opcclaw/core/code_executor.py`](./opcclaw/core/code_executor.py.md)
- [`opcclaw/core/code_graph/__init__.py`](./opcclaw/core/code_graph/__init__.py.md)
- [`opcclaw/core/code_graph/ast_parser.py`](./opcclaw/core/code_graph/ast_parser.py.md)
- [`opcclaw/core/code_graph/graph_store.py`](./opcclaw/core/code_graph/graph_store.py.md)
- [`opcclaw/core/code_intel.py`](./opcclaw/core/code_intel.py.md)
- [`opcclaw/core/collaboration_client.py`](./opcclaw/core/collaboration_client.py.md)
- [`opcclaw/core/config_validator.py`](./opcclaw/core/config_validator.py.md)
- [`opcclaw/core/core_engine.py`](./opcclaw/core/core_engine.py.md)
- [`opcclaw/core/enhanced_core.py`](./opcclaw/core/enhanced_core.py.md)
- [`opcclaw/core/enhanced_hermes_bridge.py`](./opcclaw/core/enhanced_hermes_bridge.py.md)
- [`opcclaw/core/firecrawl/__init__.py`](./opcclaw/core/firecrawl/__init__.py.md)
- [`opcclaw/core/firecrawl/cache.py`](./opcclaw/core/firecrawl/cache.py.md)
- [`opcclaw/core/firecrawl/converter.py`](./opcclaw/core/firecrawl/converter.py.md)
- [`opcclaw/core/firecrawl/test_self_check.py`](./opcclaw/core/firecrawl/test_self_check.py.md)
- [`opcclaw/core/git_ops.py`](./opcclaw/core/git_ops.py.md)
- [`opcclaw/core/harness/__init__.py`](./opcclaw/core/harness/__init__.py.md)
- [`opcclaw/core/harness/config_schema.py`](./opcclaw/core/harness/config_schema.py.md)
- [`opcclaw/core/impeccable/__init__.py`](./opcclaw/core/impeccable/__init__.py.md)
- [`opcclaw/core/impeccable/complexity_checker.py`](./opcclaw/core/impeccable/complexity_checker.py.md)
- [`opcclaw/core/impeccable/coupling_checker.py`](./opcclaw/core/impeccable/coupling_checker.py.md)
- [`opcclaw/core/impeccable/report_generator.py`](./opcclaw/core/impeccable/report_generator.py.md)
- [`opcclaw/core/impeccable/solid_checker.py`](./opcclaw/core/impeccable/solid_checker.py.md)
- [`opcclaw/core/llm_backend.py`](./opcclaw/core/llm_backend.py.md)
- [`opcclaw/core/memory.py`](./opcclaw/core/memory.py.md)
- [`opcclaw/core/memory_store.py`](./opcclaw/core/memory_store.py.md)
- [`opcclaw/core/model_status.py`](./opcclaw/core/model_status.py.md)
- [`opcclaw/core/model_status_manager.py`](./opcclaw/core/model_status_manager.py.md)
- [`opcclaw/core/multi_channel/__init__.py`](./opcclaw/core/multi_channel/__init__.py.md)
- [`opcclaw/core/multi_channel/content_optimizer.py`](./opcclaw/core/multi_channel/content_optimizer.py.md)
- [`opcclaw/core/multi_channel/draft_manager.py`](./opcclaw/core/multi_channel/draft_manager.py.md)
- [`opcclaw/core/multi_channel/platforms/__init__.py`](./opcclaw/core/multi_channel/platforms/__init__.py.md)
- [`opcclaw/core/multi_channel/platforms/linkedin.py`](./opcclaw/core/multi_channel/platforms/linkedin.py.md)
- [`opcclaw/core/multi_channel/platforms/twitter.py`](./opcclaw/core/multi_channel/platforms/twitter.py.md)
- [`opcclaw/core/multi_channel/platforms/wechat.py`](./opcclaw/core/multi_channel/platforms/wechat.py.md)
- [`opcclaw/core/multi_channel/platforms/weibo.py`](./opcclaw/core/multi_channel/platforms/weibo.py.md)
- [`opcclaw/core/multi_channel/platforms/zhihu.py`](./opcclaw/core/multi_channel/platforms/zhihu.py.md)
- [`opcclaw/core/multi_model.py`](./opcclaw/core/multi_model.py.md)
- [`opcclaw/core/multi_model_chat_engine.py`](./opcclaw/core/multi_model_chat_engine.py.md)
- [`opcclaw/core/observability/__init__.py`](./opcclaw/core/observability/__init__.py.md)
- [`opcclaw/core/observability/cost_tracker.py`](./opcclaw/core/observability/cost_tracker.py.md)
- [`opcclaw/core/observability/schema.py`](./opcclaw/core/observability/schema.py.md)
- [`opcclaw/core/observability/test_obs.py`](./opcclaw/core/observability/test_obs.py.md)
- [`opcclaw/core/observability/test_obs_20260615_143009_780.py`](./opcclaw/core/observability/test_obs_20260615_143009_780.py.md)
- [`opcclaw/core/observability/token_observer.py`](./opcclaw/core/observability/token_observer.py.md)
- [`opcclaw/core/observability/trace_manager.py`](./opcclaw/core/observability/trace_manager.py.md)
- [`opcclaw/core/opcclaw_logging.py`](./opcclaw/core/opcclaw_logging.py.md)
- [`opcclaw/core/patch_engine.py`](./opcclaw/core/patch_engine.py.md)
- [`opcclaw/core/performance_monitor.py`](./opcclaw/core/performance_monitor.py.md)
- [`opcclaw/core/proactive_engine.py`](./opcclaw/core/proactive_engine.py.md)
- [`opcclaw/core/proactive_monitors.py`](./opcclaw/core/proactive_monitors.py.md)
- [`opcclaw/core/process_manager.py`](./opcclaw/core/process_manager.py.md)
- [`opcclaw/core/provider_registry.py`](./opcclaw/core/provider_registry.py.md)
- [`opcclaw/core/rag_context.py`](./opcclaw/core/rag_context.py.md)
- [`opcclaw/core/secure_storage.py`](./opcclaw/core/secure_storage.py.md)
- [`opcclaw/core/semantic_search/__init__.py`](./opcclaw/core/semantic_search/__init__.py.md)
- [`opcclaw/core/semantic_search/hybrid_retriever.py`](./opcclaw/core/semantic_search/hybrid_retriever.py.md)
- [`opcclaw/core/semantic_search.py`](./opcclaw/core/semantic_search.py.md)
- [`opcclaw/core/session_search.py`](./opcclaw/core/session_search.py.md)
- [`opcclaw/core/skill_loader.py`](./opcclaw/core/skill_loader.py.md)
- [`opcclaw/core/skill_system.py`](./opcclaw/core/skill_system.py.md)
- [`opcclaw/core/smart_memory.py`](./opcclaw/core/smart_memory.py.md)
- [`opcclaw/core/smart_memory_adapter.py`](./opcclaw/core/smart_memory_adapter.py.md)
- [`opcclaw/core/supabase_client.py`](./opcclaw/core/supabase_client.py.md)
- [`opcclaw/core/super_intelligence.py`](./opcclaw/core/super_intelligence.py.md)
- [`opcclaw/core/sync_bridge.py`](./opcclaw/core/sync_bridge.py.md)
- [`opcclaw/core/task_scheduler.py`](./opcclaw/core/task_scheduler.py.md)
- [`opcclaw/core/todo_system.py`](./opcclaw/core/todo_system.py.md)
- [`opcclaw/core/token_optimizer.py`](./opcclaw/core/token_optimizer.py.md)
- [`opcclaw/core/token_saver.py`](./opcclaw/core/token_saver.py.md)
- [`opcclaw/core/tool_registry.py`](./opcclaw/core/tool_registry.py.md)
- [`opcclaw/core/web_search.py`](./opcclaw/core/web_search.py.md)
- [`opcclaw/core/workspace_indexer.py`](./opcclaw/core/workspace_indexer.py.md)
- [`opcclaw/cron/__init__.py`](./opcclaw/cron/__init__.py.md)
- [`opcclaw/cron/jobs.py`](./opcclaw/cron/jobs.py.md)
- [`opcclaw/data/__init__.py`](./opcclaw/data/__init__.py.md)
- [`opcclaw/hermes_cli/__init__.py`](./opcclaw/hermes_cli/__init__.py.md)
- [`opcclaw/hermes_cli/config.py`](./opcclaw/hermes_cli/config.py.md)
- [`opcclaw/hermes_constants.py`](./opcclaw/hermes_constants.py.md)
- [`opcclaw/init_db.py`](./opcclaw/init_db.py.md)
- [`opcclaw/main.py`](./opcclaw/main.py.md)
- [`opcclaw/modules/__init__.py`](./opcclaw/modules/__init__.py.md)
- [`opcclaw/modules/_shared.py`](./opcclaw/modules/_shared.py.md)
- [`opcclaw/modules/agent_event_panel.py`](./opcclaw/modules/agent_event_panel.py.md)
- [`opcclaw/modules/animations.py`](./opcclaw/modules/animations.py.md)
- [`opcclaw/modules/chat_window.py`](./opcclaw/modules/chat_window.py.md)
- [`opcclaw/modules/chat_window_core.py`](./opcclaw/modules/chat_window_core.py.md)
- [`opcclaw/modules/chat_worker.py`](./opcclaw/modules/chat_worker.py.md)
- [`opcclaw/modules/cloud_model_panel.py`](./opcclaw/modules/cloud_model_panel.py.md)
- [`opcclaw/modules/config_manager.py`](./opcclaw/modules/config_manager.py.md)
- [`opcclaw/modules/general_settings_panel.py`](./opcclaw/modules/general_settings_panel.py.md)
- [`opcclaw/modules/git_panel.py`](./opcclaw/modules/git_panel.py.md)
- [`opcclaw/modules/local_model_panel.py`](./opcclaw/modules/local_model_panel.py.md)
- [`opcclaw/modules/login_dialog.py`](./opcclaw/modules/login_dialog.py.md)
- [`opcclaw/modules/message_bubble.py`](./opcclaw/modules/message_bubble.py.md)
- [`opcclaw/modules/sidebar.py`](./opcclaw/modules/sidebar.py.md)
- [`opcclaw/modules/sidebar_panel.py`](./opcclaw/modules/sidebar_panel.py.md)
- [`opcclaw/modules/skills_panel.py`](./opcclaw/modules/skills_panel.py.md)
- [`opcclaw/modules/voice_manager.py`](./opcclaw/modules/voice_manager.py.md)
- [`opcclaw/modules/widgets.py`](./opcclaw/modules/widgets.py.md)
- [`opcclaw/plugins/__init__.py`](./opcclaw/plugins/__init__.py.md)
- [`opcclaw/plugins/code_executor/__init__.py`](./opcclaw/plugins/code_executor/__init__.py.md)
- [`opcclaw/plugins/context_engine/__init__.py`](./opcclaw/plugins/context_engine/__init__.py.md)
- [`opcclaw/plugins/disk-cleanup/__init__.py`](./opcclaw/plugins/disk-cleanup/__init__.py.md)
- [`opcclaw/plugins/disk-cleanup/disk_cleanup.py`](./opcclaw/plugins/disk-cleanup/disk_cleanup.py.md)
- [`opcclaw/plugins/example-dashboard/dashboard/plugin_api.py`](./opcclaw/plugins/example-dashboard/dashboard/plugin_api.py.md)
- [`opcclaw/plugins/file_handler/__init__.py`](./opcclaw/plugins/file_handler/__init__.py.md)
- [`opcclaw/plugins/google_meet/__init__.py`](./opcclaw/plugins/google_meet/__init__.py.md)
- [`opcclaw/plugins/google_meet/audio_bridge.py`](./opcclaw/plugins/google_meet/audio_bridge.py.md)
- [`opcclaw/plugins/google_meet/cli.py`](./opcclaw/plugins/google_meet/cli.py.md)
- [`opcclaw/plugins/google_meet/meet_bot.py`](./opcclaw/plugins/google_meet/meet_bot.py.md)
- [`opcclaw/plugins/google_meet/node/__init__.py`](./opcclaw/plugins/google_meet/node/__init__.py.md)
- [`opcclaw/plugins/google_meet/node/cli.py`](./opcclaw/plugins/google_meet/node/cli.py.md)
- [`opcclaw/plugins/google_meet/node/client.py`](./opcclaw/plugins/google_meet/node/client.py.md)
- [`opcclaw/plugins/google_meet/node/protocol.py`](./opcclaw/plugins/google_meet/node/protocol.py.md)
- [`opcclaw/plugins/google_meet/node/registry.py`](./opcclaw/plugins/google_meet/node/registry.py.md)
- [`opcclaw/plugins/google_meet/node/server.py`](./opcclaw/plugins/google_meet/node/server.py.md)
- [`opcclaw/plugins/google_meet/process_manager.py`](./opcclaw/plugins/google_meet/process_manager.py.md)
- [`opcclaw/plugins/google_meet/realtime/__init__.py`](./opcclaw/plugins/google_meet/realtime/__init__.py.md)
- [`opcclaw/plugins/google_meet/realtime/openai_client.py`](./opcclaw/plugins/google_meet/realtime/openai_client.py.md)
- [`opcclaw/plugins/google_meet/tools.py`](./opcclaw/plugins/google_meet/tools.py.md)
- [`opcclaw/plugins/hermes-achievements/dashboard/plugin_api.py`](./opcclaw/plugins/hermes-achievements/dashboard/plugin_api.py.md)
- [`opcclaw/plugins/image_gen/openai/__init__.py`](./opcclaw/plugins/image_gen/openai/__init__.py.md)
- [`opcclaw/plugins/image_gen/openai-codex/__init__.py`](./opcclaw/plugins/image_gen/openai-codex/__init__.py.md)
- [`opcclaw/plugins/image_gen/xai/__init__.py`](./opcclaw/plugins/image_gen/xai/__init__.py.md)
- [`opcclaw/plugins/image_vision/__init__.py`](./opcclaw/plugins/image_vision/__init__.py.md)
- [`opcclaw/plugins/kanban/dashboard/plugin_api.py`](./opcclaw/plugins/kanban/dashboard/plugin_api.py.md)
- [`opcclaw/plugins/memory/__init__.py`](./opcclaw/plugins/memory/__init__.py.md)
- [`opcclaw/plugins/memory/byterover/__init__.py`](./opcclaw/plugins/memory/byterover/__init__.py.md)
- [`opcclaw/plugins/memory/hindsight/__init__.py`](./opcclaw/plugins/memory/hindsight/__init__.py.md)
- [`opcclaw/plugins/memory/holographic/__init__.py`](./opcclaw/plugins/memory/holographic/__init__.py.md)
- [`opcclaw/plugins/memory/holographic/holographic.py`](./opcclaw/plugins/memory/holographic/holographic.py.md)
- [`opcclaw/plugins/memory/holographic/retrieval.py`](./opcclaw/plugins/memory/holographic/retrieval.py.md)
- [`opcclaw/plugins/memory/holographic/store.py`](./opcclaw/plugins/memory/holographic/store.py.md)
- [`opcclaw/plugins/memory/honcho/__init__.py`](./opcclaw/plugins/memory/honcho/__init__.py.md)
- [`opcclaw/plugins/memory/honcho/cli.py`](./opcclaw/plugins/memory/honcho/cli.py.md)
- [`opcclaw/plugins/memory/honcho/client.py`](./opcclaw/plugins/memory/honcho/client.py.md)
- [`opcclaw/plugins/memory/honcho/session.py`](./opcclaw/plugins/memory/honcho/session.py.md)
- [`opcclaw/plugins/memory/mem0/__init__.py`](./opcclaw/plugins/memory/mem0/__init__.py.md)
- [`opcclaw/plugins/memory/openviking/__init__.py`](./opcclaw/plugins/memory/openviking/__init__.py.md)
- [`opcclaw/plugins/memory/retaindb/__init__.py`](./opcclaw/plugins/memory/retaindb/__init__.py.md)
- [`opcclaw/plugins/memory/supermemory/__init__.py`](./opcclaw/plugins/memory/supermemory/__init__.py.md)
- [`opcclaw/plugins/model-providers/ai-gateway/__init__.py`](./opcclaw/plugins/model-providers/ai-gateway/__init__.py.md)
- [`opcclaw/plugins/model-providers/alibaba/__init__.py`](./opcclaw/plugins/model-providers/alibaba/__init__.py.md)
- [`opcclaw/plugins/model-providers/alibaba-coding-plan/__init__.py`](./opcclaw/plugins/model-providers/alibaba-coding-plan/__init__.py.md)
- [`opcclaw/plugins/model-providers/anthropic/__init__.py`](./opcclaw/plugins/model-providers/anthropic/__init__.py.md)
- [`opcclaw/plugins/model-providers/arcee/__init__.py`](./opcclaw/plugins/model-providers/arcee/__init__.py.md)
- [`opcclaw/plugins/model-providers/azure-foundry/__init__.py`](./opcclaw/plugins/model-providers/azure-foundry/__init__.py.md)
- [`opcclaw/plugins/model-providers/bedrock/__init__.py`](./opcclaw/plugins/model-providers/bedrock/__init__.py.md)
- [`opcclaw/plugins/model-providers/copilot/__init__.py`](./opcclaw/plugins/model-providers/copilot/__init__.py.md)
- [`opcclaw/plugins/model-providers/copilot-acp/__init__.py`](./opcclaw/plugins/model-providers/copilot-acp/__init__.py.md)
- [`opcclaw/plugins/model-providers/custom/__init__.py`](./opcclaw/plugins/model-providers/custom/__init__.py.md)
- [`opcclaw/plugins/model-providers/deepseek/__init__.py`](./opcclaw/plugins/model-providers/deepseek/__init__.py.md)
- [`opcclaw/plugins/model-providers/gemini/__init__.py`](./opcclaw/plugins/model-providers/gemini/__init__.py.md)
- [`opcclaw/plugins/model-providers/gmi/__init__.py`](./opcclaw/plugins/model-providers/gmi/__init__.py.md)
- [`opcclaw/plugins/model-providers/huggingface/__init__.py`](./opcclaw/plugins/model-providers/huggingface/__init__.py.md)
- [`opcclaw/plugins/model-providers/kilocode/__init__.py`](./opcclaw/plugins/model-providers/kilocode/__init__.py.md)
- [`opcclaw/plugins/model-providers/kimi-coding/__init__.py`](./opcclaw/plugins/model-providers/kimi-coding/__init__.py.md)
- [`opcclaw/plugins/model-providers/minimax/__init__.py`](./opcclaw/plugins/model-providers/minimax/__init__.py.md)
- [`opcclaw/plugins/model-providers/nous/__init__.py`](./opcclaw/plugins/model-providers/nous/__init__.py.md)
- [`opcclaw/plugins/model-providers/nvidia/__init__.py`](./opcclaw/plugins/model-providers/nvidia/__init__.py.md)
- [`opcclaw/plugins/model-providers/ollama/__init__.py`](./opcclaw/plugins/model-providers/ollama/__init__.py.md)
- [`opcclaw/plugins/model-providers/ollama-cloud/__init__.py`](./opcclaw/plugins/model-providers/ollama-cloud/__init__.py.md)
- [`opcclaw/plugins/model-providers/openai-codex/__init__.py`](./opcclaw/plugins/model-providers/openai-codex/__init__.py.md)
- [`opcclaw/plugins/model-providers/opencode-zen/__init__.py`](./opcclaw/plugins/model-providers/opencode-zen/__init__.py.md)
- [`opcclaw/plugins/model-providers/openrouter/__init__.py`](./opcclaw/plugins/model-providers/openrouter/__init__.py.md)
- [`opcclaw/plugins/model-providers/qwen-oauth/__init__.py`](./opcclaw/plugins/model-providers/qwen-oauth/__init__.py.md)
- [`opcclaw/plugins/model-providers/stepfun/__init__.py`](./opcclaw/plugins/model-providers/stepfun/__init__.py.md)
- [`opcclaw/plugins/model-providers/xai/__init__.py`](./opcclaw/plugins/model-providers/xai/__init__.py.md)
- [`opcclaw/plugins/model-providers/xiaomi/__init__.py`](./opcclaw/plugins/model-providers/xiaomi/__init__.py.md)
- [`opcclaw/plugins/model-providers/zai/__init__.py`](./opcclaw/plugins/model-providers/zai/__init__.py.md)
- [`opcclaw/plugins/multi_model/__init__.py`](./opcclaw/plugins/multi_model/__init__.py.md)
- [`opcclaw/plugins/observability/langfuse/__init__.py`](./opcclaw/plugins/observability/langfuse/__init__.py.md)
- [`opcclaw/plugins/platforms/google_chat/__init__.py`](./opcclaw/plugins/platforms/google_chat/__init__.py.md)
- [`opcclaw/plugins/platforms/google_chat/adapter.py`](./opcclaw/plugins/platforms/google_chat/adapter.py.md)
- [`opcclaw/plugins/platforms/google_chat/oauth.py`](./opcclaw/plugins/platforms/google_chat/oauth.py.md)
- [`opcclaw/plugins/platforms/irc/__init__.py`](./opcclaw/plugins/platforms/irc/__init__.py.md)
- [`opcclaw/plugins/platforms/irc/adapter.py`](./opcclaw/plugins/platforms/irc/adapter.py.md)
- [`opcclaw/plugins/platforms/teams/__init__.py`](./opcclaw/plugins/platforms/teams/__init__.py.md)
- [`opcclaw/plugins/platforms/teams/adapter.py`](./opcclaw/plugins/platforms/teams/adapter.py.md)
- [`opcclaw/plugins/spotify/__init__.py`](./opcclaw/plugins/spotify/__init__.py.md)
- [`opcclaw/plugins/spotify/client.py`](./opcclaw/plugins/spotify/client.py.md)
- [`opcclaw/plugins/spotify/tools.py`](./opcclaw/plugins/spotify/tools.py.md)
- [`opcclaw/plugins/teams_pipeline/__init__.py`](./opcclaw/plugins/teams_pipeline/__init__.py.md)
- [`opcclaw/plugins/teams_pipeline/cli.py`](./opcclaw/plugins/teams_pipeline/cli.py.md)
- [`opcclaw/plugins/teams_pipeline/meetings.py`](./opcclaw/plugins/teams_pipeline/meetings.py.md)
- [`opcclaw/plugins/teams_pipeline/models.py`](./opcclaw/plugins/teams_pipeline/models.py.md)
- [`opcclaw/plugins/teams_pipeline/pipeline.py`](./opcclaw/plugins/teams_pipeline/pipeline.py.md)
- [`opcclaw/plugins/teams_pipeline/runtime.py`](./opcclaw/plugins/teams_pipeline/runtime.py.md)
- [`opcclaw/plugins/teams_pipeline/store.py`](./opcclaw/plugins/teams_pipeline/store.py.md)
- [`opcclaw/plugins/teams_pipeline/subscriptions.py`](./opcclaw/plugins/teams_pipeline/subscriptions.py.md)
- [`opcclaw/plugins/web_search/__init__.py`](./opcclaw/plugins/web_search/__init__.py.md)
- [`opcclaw/providers/__init__.py`](./opcclaw/providers/__init__.py.md)
- [`opcclaw/providers/base.py`](./opcclaw/providers/base.py.md)
- [`opcclaw/skills/__init__.py`](./opcclaw/skills/__init__.py.md)
- [`opcclaw/skills/creative/comfyui/scripts/_common.py`](./opcclaw/skills/creative/comfyui/scripts/_common.py.md)
- [`opcclaw/skills/creative/comfyui/scripts/auto_fix_deps.py`](./opcclaw/skills/creative/comfyui/scripts/auto_fix_deps.py.md)
- [`opcclaw/skills/creative/comfyui/scripts/check_deps.py`](./opcclaw/skills/creative/comfyui/scripts/check_deps.py.md)
- [`opcclaw/skills/creative/comfyui/scripts/extract_schema.py`](./opcclaw/skills/creative/comfyui/scripts/extract_schema.py.md)
- [`opcclaw/skills/creative/comfyui/scripts/fetch_logs.py`](./opcclaw/skills/creative/comfyui/scripts/fetch_logs.py.md)
- [`opcclaw/skills/creative/comfyui/scripts/hardware_check.py`](./opcclaw/skills/creative/comfyui/scripts/hardware_check.py.md)
- [`opcclaw/skills/creative/comfyui/scripts/health_check.py`](./opcclaw/skills/creative/comfyui/scripts/health_check.py.md)
- [`opcclaw/skills/creative/comfyui/scripts/run_batch.py`](./opcclaw/skills/creative/comfyui/scripts/run_batch.py.md)
- [`opcclaw/skills/creative/comfyui/scripts/run_workflow.py`](./opcclaw/skills/creative/comfyui/scripts/run_workflow.py.md)
- [`opcclaw/skills/creative/comfyui/scripts/ws_monitor.py`](./opcclaw/skills/creative/comfyui/scripts/ws_monitor.py.md)
- [`opcclaw/skills/creative/comfyui/tests/conftest.py`](./opcclaw/skills/creative/comfyui/tests/conftest.py.md)
- [`opcclaw/skills/creative/excalidraw/scripts/upload.py`](./opcclaw/skills/creative/excalidraw/scripts/upload.py.md)
- [`opcclaw/skills/creative/pixel-art/scripts/__init__.py`](./opcclaw/skills/creative/pixel-art/scripts/__init__.py.md)
- [`opcclaw/skills/creative/pixel-art/scripts/palettes.py`](./opcclaw/skills/creative/pixel-art/scripts/palettes.py.md)
- [`opcclaw/skills/creative/pixel-art/scripts/pixel_art.py`](./opcclaw/skills/creative/pixel-art/scripts/pixel_art.py.md)
- [`opcclaw/skills/creative/pixel-art/scripts/pixel_art_video.py`](./opcclaw/skills/creative/pixel-art/scripts/pixel_art_video.py.md)
- [`opcclaw/skills/dual_ai.py`](./opcclaw/skills/dual_ai.py.md)
- [`opcclaw/skills/flybook_bot/config.py`](./opcclaw/skills/flybook_bot/config.py.md)
- [`opcclaw/skills/flybook_bot/flybook_skill.py`](./opcclaw/skills/flybook_bot/flybook_skill.py.md)
- [`opcclaw/skills/flybook_bot/server.py`](./opcclaw/skills/flybook_bot/server.py.md)
- [`opcclaw/skills/flybook_bot/server_minimal.py`](./opcclaw/skills/flybook_bot/server_minimal.py.md)
- [`opcclaw/skills/flybook_bot/server_simple.py`](./opcclaw/skills/flybook_bot/server_simple.py.md)
- [`opcclaw/skills/media/youtube-content/scripts/fetch_transcript.py`](./opcclaw/skills/media/youtube-content/scripts/fetch_transcript.py.md)
- [`opcclaw/skills/productivity/google-workspace/scripts/_hermes_home.py`](./opcclaw/skills/productivity/google-workspace/scripts/_hermes_home.py.md)
- [`opcclaw/skills/productivity/google-workspace/scripts/google_api.py`](./opcclaw/skills/productivity/google-workspace/scripts/google_api.py.md)
- [`opcclaw/skills/productivity/google-workspace/scripts/gws_bridge.py`](./opcclaw/skills/productivity/google-workspace/scripts/gws_bridge.py.md)
- [`opcclaw/skills/productivity/google-workspace/scripts/setup.py`](./opcclaw/skills/productivity/google-workspace/scripts/setup.py.md)
- [`opcclaw/skills/productivity/linear/scripts/linear_api.py`](./opcclaw/skills/productivity/linear/scripts/linear_api.py.md)
- [`opcclaw/skills/productivity/maps/scripts/maps_client.py`](./opcclaw/skills/productivity/maps/scripts/maps_client.py.md)
- [`opcclaw/skills/productivity/ocr-and-documents/scripts/extract_marker.py`](./opcclaw/skills/productivity/ocr-and-documents/scripts/extract_marker.py.md)
- [`opcclaw/skills/productivity/ocr-and-documents/scripts/extract_pymupdf.py`](./opcclaw/skills/productivity/ocr-and-documents/scripts/extract_pymupdf.py.md)
- [`opcclaw/skills/productivity/powerpoint/scripts/__init__.py`](./opcclaw/skills/productivity/powerpoint/scripts/__init__.py.md)
- [`opcclaw/skills/productivity/powerpoint/scripts/add_slide.py`](./opcclaw/skills/productivity/powerpoint/scripts/add_slide.py.md)
- [`opcclaw/skills/productivity/powerpoint/scripts/clean.py`](./opcclaw/skills/productivity/powerpoint/scripts/clean.py.md)
- [`opcclaw/skills/productivity/powerpoint/scripts/office/helpers/__init__.py`](./opcclaw/skills/productivity/powerpoint/scripts/office/helpers/__init__.py.md)
- [`opcclaw/skills/productivity/powerpoint/scripts/office/helpers/merge_runs.py`](./opcclaw/skills/productivity/powerpoint/scripts/office/helpers/merge_runs.py.md)
- [`opcclaw/skills/productivity/powerpoint/scripts/office/helpers/simplify_redlines.py`](./opcclaw/skills/productivity/powerpoint/scripts/office/helpers/simplify_redlines.py.md)
- [`opcclaw/skills/productivity/powerpoint/scripts/office/pack.py`](./opcclaw/skills/productivity/powerpoint/scripts/office/pack.py.md)
- [`opcclaw/skills/qclaw_skills/baidu-search/scripts/search.py`](./opcclaw/skills/qclaw_skills/baidu-search/scripts/search.py.md)
- [`opcclaw/skills/qclaw_skills/file-manager/scripts/batch_rename.py`](./opcclaw/skills/qclaw_skills/file-manager/scripts/batch_rename.py.md)
- [`opcclaw/skills/qclaw_skills/file-manager/scripts/deduplicate.py`](./opcclaw/skills/qclaw_skills/file-manager/scripts/deduplicate.py.md)
- [`opcclaw/skills/qclaw_skills/file-manager/scripts/organize.py`](./opcclaw/skills/qclaw_skills/file-manager/scripts/organize.py.md)
- [`opcclaw/skills/qclaw_skills/file-manager/scripts/sync.py`](./opcclaw/skills/qclaw_skills/file-manager/scripts/sync.py.md)
- [`opcclaw/skills/qclaw_skills/file-manager/scripts/utils.py`](./opcclaw/skills/qclaw_skills/file-manager/scripts/utils.py.md)
- [`opcclaw/skills/qclaw_skills/planning-with-files/scripts/session-catchup.py`](./opcclaw/skills/qclaw_skills/planning-with-files/scripts/session-catchup.py.md)
- [`opcclaw/skills/qclaw_skills/video-image-file-analysis/scripts/vision.py`](./opcclaw/skills/qclaw_skills/video-image-file-analysis/scripts/vision.py.md)
- [`opcclaw/skills/qclaw_skills/video-image-file-analysis/scripts/vision_manager.py`](./opcclaw/skills/qclaw_skills/video-image-file-analysis/scripts/vision_manager.py.md)
- [`opcclaw/skills/qclaw_skills/web-browsing/scripts/search_web.py`](./opcclaw/skills/qclaw_skills/web-browsing/scripts/search_web.py.md)
- [`opcclaw/skills/qclaw_skills/web-search/scripts/search.py`](./opcclaw/skills/qclaw_skills/web-search/scripts/search.py.md)
- [`opcclaw/skills/qclaw_skills/webscraper-v2/webscraper.py`](./opcclaw/skills/qclaw_skills/webscraper-v2/webscraper.py.md)
- [`opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/api_client.py`](./opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/api_client.py.md)
- [`opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/chat_mode.py`](./opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/chat_mode.py.md)
- [`opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/claw_client.py`](./opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/claw_client.py.md)
- [`opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/environment.py`](./opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/environment.py.md)
- [`opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/file_utils.py`](./opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/file_utils.py.md)
- [`opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/get_access_token.py`](./opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/get_access_token.py.md)
- [`opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/identity_manager.py`](./opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/identity_manager.py.md)
- [`opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/raw_fetcher.py`](./opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/raw_fetcher.py.md)
- [`opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/scrm.py`](./opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/scrm.py.md)
- [`opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/utils.py`](./opcclaw/skills/qclaw_skills/wecom-weisheng-scrm/scripts/utils.py.md)
- [`opcclaw/skills/red-teaming/godmode/scripts/auto_jailbreak.py`](./opcclaw/skills/red-teaming/godmode/scripts/auto_jailbreak.py.md)
- [`opcclaw/skills/red-teaming/godmode/scripts/godmode_race.py`](./opcclaw/skills/red-teaming/godmode/scripts/godmode_race.py.md)
- [`opcclaw/skills/red-teaming/godmode/scripts/load_godmode.py`](./opcclaw/skills/red-teaming/godmode/scripts/load_godmode.py.md)
- [`opcclaw/skills/red-teaming/godmode/scripts/parseltongue.py`](./opcclaw/skills/red-teaming/godmode/scripts/parseltongue.py.md)
- [`opcclaw/skills/research/arxiv/scripts/search_arxiv.py`](./opcclaw/skills/research/arxiv/scripts/search_arxiv.py.md)
- [`opcclaw/skills/research/polymarket/scripts/polymarket.py`](./opcclaw/skills/research/polymarket/scripts/polymarket.py.md)
- [`opcclaw/skills/smart_memory/package_skill.py`](./opcclaw/skills/smart_memory/package_skill.py.md)
- [`opcclaw/start_opcclaw.py`](./opcclaw/start_opcclaw.py.md)
- [`opcclaw/tools/__init__.py`](./opcclaw/tools/__init__.py.md)
- [`opcclaw/tools/alert_tools.py`](./opcclaw/tools/alert_tools.py.md)
- [`opcclaw/tools/analysis_tools.py`](./opcclaw/tools/analysis_tools.py.md)
- [`opcclaw/tools/ansi_strip.py`](./opcclaw/tools/ansi_strip.py.md)
- [`opcclaw/tools/approval.py`](./opcclaw/tools/approval.py.md)
- [`opcclaw/tools/automation_tools.py`](./opcclaw/tools/automation_tools.py.md)
- [`opcclaw/tools/binary_extensions.py`](./opcclaw/tools/binary_extensions.py.md)
- [`opcclaw/tools/browser_camofox.py`](./opcclaw/tools/browser_camofox.py.md)
- [`opcclaw/tools/browser_camofox_state.py`](./opcclaw/tools/browser_camofox_state.py.md)
- [`opcclaw/tools/browser_cdp_tool.py`](./opcclaw/tools/browser_cdp_tool.py.md)
- [`opcclaw/tools/browser_dialog_tool.py`](./opcclaw/tools/browser_dialog_tool.py.md)
- [`opcclaw/tools/browser_providers/__init__.py`](./opcclaw/tools/browser_providers/__init__.py.md)
- [`opcclaw/tools/browser_providers/base.py`](./opcclaw/tools/browser_providers/base.py.md)
- [`opcclaw/tools/browser_providers/browser_use.py`](./opcclaw/tools/browser_providers/browser_use.py.md)
- [`opcclaw/tools/browser_providers/browserbase.py`](./opcclaw/tools/browser_providers/browserbase.py.md)
- [`opcclaw/tools/browser_providers/firecrawl.py`](./opcclaw/tools/browser_providers/firecrawl.py.md)
- [`opcclaw/tools/browser_supervisor.py`](./opcclaw/tools/browser_supervisor.py.md)
- [`opcclaw/tools/browser_tool.py`](./opcclaw/tools/browser_tool.py.md)
- [`opcclaw/tools/budget_config.py`](./opcclaw/tools/budget_config.py.md)
- [`opcclaw/tools/builtin/__init__.py`](./opcclaw/tools/builtin/__init__.py.md)
- [`opcclaw/tools/builtin/code_tools.py`](./opcclaw/tools/builtin/code_tools.py.md)
- [`opcclaw/tools/builtin/developer_tools.py`](./opcclaw/tools/builtin/developer_tools.py.md)
- [`opcclaw/tools/builtin/git_tools.py`](./opcclaw/tools/builtin/git_tools.py.md)
- [`opcclaw/tools/builtin/system_tools.py`](./opcclaw/tools/builtin/system_tools.py.md)
- [`opcclaw/tools/business_tools.py`](./opcclaw/tools/business_tools.py.md)
- [`opcclaw/tools/checkpoint_manager.py`](./opcclaw/tools/checkpoint_manager.py.md)
- [`opcclaw/tools/clarify_tool.py`](./opcclaw/tools/clarify_tool.py.md)
- [`opcclaw/tools/code_execution_tool.py`](./opcclaw/tools/code_execution_tool.py.md)
- [`opcclaw/tools/computer_use/__init__.py`](./opcclaw/tools/computer_use/__init__.py.md)
- [`opcclaw/tools/computer_use/backend.py`](./opcclaw/tools/computer_use/backend.py.md)
- [`opcclaw/tools/computer_use/cua_backend.py`](./opcclaw/tools/computer_use/cua_backend.py.md)
- [`opcclaw/tools/computer_use/schema.py`](./opcclaw/tools/computer_use/schema.py.md)
- [`opcclaw/tools/computer_use/tool.py`](./opcclaw/tools/computer_use/tool.py.md)
- [`opcclaw/tools/computer_use_tool.py`](./opcclaw/tools/computer_use_tool.py.md)
- [`opcclaw/tools/credential_files.py`](./opcclaw/tools/credential_files.py.md)
- [`opcclaw/tools/crm_tools.py`](./opcclaw/tools/crm_tools.py.md)
- [`opcclaw/tools/cronjob_tools.py`](./opcclaw/tools/cronjob_tools.py.md)
- [`opcclaw/tools/data_import_tools.py`](./opcclaw/tools/data_import_tools.py.md)
- [`opcclaw/tools/debug_helpers.py`](./opcclaw/tools/debug_helpers.py.md)
- [`opcclaw/tools/delegate_tool.py`](./opcclaw/tools/delegate_tool.py.md)
- [`opcclaw/tools/discord_tool.py`](./opcclaw/tools/discord_tool.py.md)
- [`opcclaw/tools/dispatch_tool.py`](./opcclaw/tools/dispatch_tool.py.md)
- [`opcclaw/tools/doc_tools.py`](./opcclaw/tools/doc_tools.py.md)
- [`opcclaw/tools/env_passthrough.py`](./opcclaw/tools/env_passthrough.py.md)
- [`opcclaw/tools/environments/__init__.py`](./opcclaw/tools/environments/__init__.py.md)
- [`opcclaw/tools/environments/base.py`](./opcclaw/tools/environments/base.py.md)
- [`opcclaw/tools/environments/daytona.py`](./opcclaw/tools/environments/daytona.py.md)
- [`opcclaw/tools/environments/docker.py`](./opcclaw/tools/environments/docker.py.md)
- [`opcclaw/tools/environments/file_sync.py`](./opcclaw/tools/environments/file_sync.py.md)
- [`opcclaw/tools/environments/local.py`](./opcclaw/tools/environments/local.py.md)
- [`opcclaw/tools/environments/managed_modal.py`](./opcclaw/tools/environments/managed_modal.py.md)
- [`opcclaw/tools/environments/modal.py`](./opcclaw/tools/environments/modal.py.md)
- [`opcclaw/tools/environments/modal_utils.py`](./opcclaw/tools/environments/modal_utils.py.md)
- [`opcclaw/tools/environments/singularity.py`](./opcclaw/tools/environments/singularity.py.md)
- [`opcclaw/tools/environments/ssh.py`](./opcclaw/tools/environments/ssh.py.md)
- [`opcclaw/tools/environments/vercel_sandbox.py`](./opcclaw/tools/environments/vercel_sandbox.py.md)
- [`opcclaw/tools/export_tools.py`](./opcclaw/tools/export_tools.py.md)
- [`opcclaw/tools/feishu_doc_tool.py`](./opcclaw/tools/feishu_doc_tool.py.md)
- [`opcclaw/tools/feishu_drive_tool.py`](./opcclaw/tools/feishu_drive_tool.py.md)
- [`opcclaw/tools/file_operations.py`](./opcclaw/tools/file_operations.py.md)
- [`opcclaw/tools/file_state.py`](./opcclaw/tools/file_state.py.md)
- [`opcclaw/tools/file_tools.py`](./opcclaw/tools/file_tools.py.md)
- [`opcclaw/tools/finance_analysis_tools.py`](./opcclaw/tools/finance_analysis_tools.py.md)
- [`opcclaw/tools/fuzzy_match.py`](./opcclaw/tools/fuzzy_match.py.md)
- [`opcclaw/tools/homeassistant_tool.py`](./opcclaw/tools/homeassistant_tool.py.md)
- [`opcclaw/tools/hr_tools.py`](./opcclaw/tools/hr_tools.py.md)
- [`opcclaw/tools/image_generation_tool.py`](./opcclaw/tools/image_generation_tool.py.md)
- [`opcclaw/tools/interrupt.py`](./opcclaw/tools/interrupt.py.md)
- [`opcclaw/tools/inventory_tools.py`](./opcclaw/tools/inventory_tools.py.md)
- [`opcclaw/tools/kanban_tools.py`](./opcclaw/tools/kanban_tools.py.md)
- [`opcclaw/tools/local_dev_tools.py`](./opcclaw/tools/local_dev_tools.py.md)
- [`opcclaw/tools/managed_tool_gateway.py`](./opcclaw/tools/managed_tool_gateway.py.md)
- [`opcclaw/tools/marketing_tools.py`](./opcclaw/tools/marketing_tools.py.md)
- [`opcclaw/tools/markitdown_tool.py`](./opcclaw/tools/markitdown_tool.py.md)
- [`opcclaw/tools/mcp_oauth.py`](./opcclaw/tools/mcp_oauth.py.md)
- [`opcclaw/tools/mcp_oauth_manager.py`](./opcclaw/tools/mcp_oauth_manager.py.md)
- [`opcclaw/tools/mcp_tool.py`](./opcclaw/tools/mcp_tool.py.md)
- [`opcclaw/tools/memory_tool.py`](./opcclaw/tools/memory_tool.py.md)
- [`opcclaw/tools/microsoft_graph_auth.py`](./opcclaw/tools/microsoft_graph_auth.py.md)
- [`opcclaw/tools/microsoft_graph_client.py`](./opcclaw/tools/microsoft_graph_client.py.md)
- [`opcclaw/tools/mixture_of_agents_tool.py`](./opcclaw/tools/mixture_of_agents_tool.py.md)
- [`opcclaw/tools/neutts_synth.py`](./opcclaw/tools/neutts_synth.py.md)
- [`opcclaw/tools/openrouter_client.py`](./opcclaw/tools/openrouter_client.py.md)
- [`opcclaw/tools/osv_check.py`](./opcclaw/tools/osv_check.py.md)
- [`opcclaw/tools/patch_parser.py`](./opcclaw/tools/patch_parser.py.md)
- [`opcclaw/tools/path_security.py`](./opcclaw/tools/path_security.py.md)
- [`opcclaw/tools/process_registry.py`](./opcclaw/tools/process_registry.py.md)
- [`opcclaw/tools/procurement_tools.py`](./opcclaw/tools/procurement_tools.py.md)
- [`opcclaw/tools/project_management.py`](./opcclaw/tools/project_management.py.md)
- [`opcclaw/tools/registry.py`](./opcclaw/tools/registry.py.md)
- [`opcclaw/tools/rl_training_tool.py`](./opcclaw/tools/rl_training_tool.py.md)
- [`opcclaw/tools/scheduling_tools.py`](./opcclaw/tools/scheduling_tools.py.md)
- [`opcclaw/tools/schema_sanitizer.py`](./opcclaw/tools/schema_sanitizer.py.md)
- [`opcclaw/tools/self_monitor.py`](./opcclaw/tools/self_monitor.py.md)
- [`opcclaw/tools/send_message_tool.py`](./opcclaw/tools/send_message_tool.py.md)
- [`opcclaw/tools/session_search_tool.py`](./opcclaw/tools/session_search_tool.py.md)
- [`opcclaw/tools/skill_manager_tool.py`](./opcclaw/tools/skill_manager_tool.py.md)
- [`opcclaw/tools/skill_provenance.py`](./opcclaw/tools/skill_provenance.py.md)
- [`opcclaw/tools/skill_usage.py`](./opcclaw/tools/skill_usage.py.md)
- [`opcclaw/tools/skills_guard.py`](./opcclaw/tools/skills_guard.py.md)
- [`opcclaw/tools/skills_hub.py`](./opcclaw/tools/skills_hub.py.md)
- [`opcclaw/tools/skills_sync.py`](./opcclaw/tools/skills_sync.py.md)
- [`opcclaw/tools/skills_tool.py`](./opcclaw/tools/skills_tool.py.md)
- [`opcclaw/tools/slash_confirm.py`](./opcclaw/tools/slash_confirm.py.md)
- [`opcclaw/tools/smart_report_tools.py`](./opcclaw/tools/smart_report_tools.py.md)
- [`opcclaw/tools/sub_agent.py`](./opcclaw/tools/sub_agent.py.md)
- [`opcclaw/tools/template_tools.py`](./opcclaw/tools/template_tools.py.md)
- [`opcclaw/tools/terminal_tool.py`](./opcclaw/tools/terminal_tool.py.md)
- [`opcclaw/tools/tirith_security.py`](./opcclaw/tools/tirith_security.py.md)
- [`opcclaw/tools/todo_tool.py`](./opcclaw/tools/todo_tool.py.md)
- [`opcclaw/tools/tool_backend_helpers.py`](./opcclaw/tools/tool_backend_helpers.py.md)
- [`opcclaw/tools/tool_output_limits.py`](./opcclaw/tools/tool_output_limits.py.md)
- [`opcclaw/tools/tool_result_storage.py`](./opcclaw/tools/tool_result_storage.py.md)
- [`opcclaw/tools/transcription_tools.py`](./opcclaw/tools/transcription_tools.py.md)
- [`opcclaw/tools/tts_tool.py`](./opcclaw/tools/tts_tool.py.md)
- [`opcclaw/tools/url_safety.py`](./opcclaw/tools/url_safety.py.md)
- [`opcclaw/tools/vision_tools.py`](./opcclaw/tools/vision_tools.py.md)
- [`opcclaw/tools/voice_mode.py`](./opcclaw/tools/voice_mode.py.md)
- [`opcclaw/tools/web_providers/__init__.py`](./opcclaw/tools/web_providers/__init__.py.md)
- [`opcclaw/tools/web_providers/base.py`](./opcclaw/tools/web_providers/base.py.md)
- [`opcclaw/tools/web_providers/brave_free.py`](./opcclaw/tools/web_providers/brave_free.py.md)
- [`opcclaw/tools/web_providers/ddgs.py`](./opcclaw/tools/web_providers/ddgs.py.md)
- [`opcclaw/tools/web_providers/searxng.py`](./opcclaw/tools/web_providers/searxng.py.md)
- [`opcclaw/tools/web_search_tools.py`](./opcclaw/tools/web_search_tools.py.md)
- [`opcclaw/tools/web_tools.py`](./opcclaw/tools/web_tools.py.md)
- [`opcclaw/tools/website_policy.py`](./opcclaw/tools/website_policy.py.md)
- [`opcclaw/tools/xai_http.py`](./opcclaw/tools/xai_http.py.md)
- [`opcclaw/tools/yuanbao_tools.py`](./opcclaw/tools/yuanbao_tools.py.md)
- [`opcclaw/toolsets/__init__.py`](./opcclaw/toolsets/__init__.py.md)
- [`opcclaw/utils.py`](./opcclaw/utils.py.md)
- [`opcclaw/verify_sync.py`](./opcclaw/verify_sync.py.md)
- [`opcclaw/web_ui/__init__.py`](./opcclaw/web_ui/__init__.py.md)
- [`opcclaw/web_ui/harness/__init__.py`](./opcclaw/web_ui/harness/__init__.py.md)
- [`opcclaw/web_ui/workflow/__init__.py`](./opcclaw/web_ui/workflow/__init__.py.md)
- [`opcclaw/web_ui/workflow/compiler.py`](./opcclaw/web_ui/workflow/compiler.py.md)
- [`opcclaw/web_ui/workflow/templates.py`](./opcclaw/web_ui/workflow/templates.py.md)
- [`planet_daemon.py`](./planet_daemon.py.md)
- [`rollback_control.py`](./rollback_control.py.md)
- [`services/__init__.py`](./services/__init__.py.md)
- [`services/ai_chatbot_service.py`](./services/ai_chatbot_service.py.md)
- [`services/audit_service.py`](./services/audit_service.py.md)
- [`services/backup_service.py`](./services/backup_service.py.md)
- [`services/backup_tool.py`](./services/backup_tool.py.md)
- [`services/barcode_service.py`](./services/barcode_service.py.md)
- [`services/bi_service.py`](./services/bi_service.py.md)
- [`services/cache_service.py`](./services/cache_service.py.md)
- [`services/chart_service.py`](./services/chart_service.py.md)
- [`services/database_optimizer.py`](./services/database_optimizer.py.md)
- [`services/encryption_service.py`](./services/encryption_service.py.md)
- [`services/export_service.py`](./services/export_service.py.md)
- [`services/hotkey_manager.py`](./services/hotkey_manager.py.md)
- [`services/i18n_service.py`](./services/i18n_service.py.md)
- [`services/image_cache_service.py`](./services/image_cache_service.py.md)
- [`services/import_export_service.py`](./services/import_export_service.py.md)
- [`services/lazy_load_service.py`](./services/lazy_load_service.py.md)
- [`services/license_service.py`](./services/license_service.py.md)
- [`services/logistics_service.py`](./services/logistics_service.py.md)
- [`services/memory_service.py`](./services/memory_service.py.md)
- [`services/nl_query_service.py`](./services/nl_query_service.py.md)
- [`services/notification_service.py`](./services/notification_service.py.md)
- [`services/offline_queue.py`](./services/offline_queue.py.md)
- [`services/payment_service.py`](./services/payment_service.py.md)
- [`services/performance_service.py`](./services/performance_service.py.md)
- [`services/permission_service.py`](./services/permission_service.py.md)
- [`services/print_service.py`](./services/print_service.py.md)
- [`services/realtime_service.py`](./services/realtime_service.py.md)
- [`services/sales_prediction_service.py`](./services/sales_prediction_service.py.md)
- [`services/scheduler_service.py`](./services/scheduler_service.py.md)
- [`services/sms_service.py`](./services/sms_service.py.md)
- [`services/sync_manager.py`](./services/sync_manager.py.md)
- [`services/system_service.py`](./services/system_service.py.md)
- [`services/system_tray.py`](./services/system_tray.py.md)
- [`services/template_service.py`](./services/template_service.py.md)
- [`services/theme_service.py`](./services/theme_service.py.md)
- [`services/update_service.py`](./services/update_service.py.md)
- [`services/workflow_service.py`](./services/workflow_service.py.md)
- [`siri_command_handler.py`](./siri_command_handler.py.md)
- [`solar_explorer/__init__.py`](./solar_explorer/__init__.py.md)
- [`solar_explorer/body_data_entries.py`](./solar_explorer/body_data_entries.py.md)
- [`solar_explorer/body_detail_window.py`](./solar_explorer/body_detail_window.py.md)
- [`solar_explorer/body_encyclopedia.py`](./solar_explorer/body_encyclopedia.py.md)
- [`solar_explorer/star_catalog_window.py`](./solar_explorer/star_catalog_window.py.md)
- [`solar_explorer/voice_reader.py`](./solar_explorer/voice_reader.py.md)
- [`tools/__init__.py`](./tools/__init__.py.md)
- [`tools/environments/__init__.py`](./tools/environments/__init__.py.md)
- [`tools/environments/file_sync.py`](./tools/environments/file_sync.py.md)
- [`tools/skills_sync.py`](./tools/skills_sync.py.md)
