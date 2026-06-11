# 一人公司 · 宇宙版 — 源码全书
> 自动生成于 2026-06-12 00:26
> 共 111 个模块，每个 `.py` 文件独立为一个文档

---

## 目录结构

```
.
├── backups/
├── core/
│   ├── __init__.py
│   ├── agent.py
│   ├── cosmic.py
│   ├── data.py
│   ├── deps.py
│   ├── llm_client.py
│   ├── planet_painter.py
│   └── voice.py
├── data/
│   ├── metrics/
├── knowledge_base/
├── log/
├── modules/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── admin_login_dialog.py
│   │   ├── auth_service.py
│   │   ├── change_password_dialog.py
│   │   ├── connect_window.py
│   │   ├── login_window.py
│   │   ├── model_setup_window.py
│   │   ├── upgrade_window.py
│   ├── business/
│   │   ├── __init__.py
│   │   ├── business_window.py
│   │   ├── customer_window.py
│   │   ├── finance_window.py
│   │   ├── order_window.py
│   │   └── product_window.py
│   ├── dashboard/
│   │   ├── __init__.py
│   │   └── dashboard_window.py
│   ├── data_center/
│   │   ├── __init__.py
│   │   ├── bi_window.py
│   │   ├── data_window.py
│   │   └── report_window.py
│   ├── intelligence/
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── llm_backend.py
│   │   ├── data/
│   │   │   ├── learning/
│   │   │   └── reflections/
│   │   ├── __init__.py
│   │   ├── _ai_shared.py
│   │   ├── _ai_widgets.py
│   │   ├── _api_key_dialog.py
│   │   ├── _chat_dialog.py
│   │   ├── _compat.py
│   │   ├── _model_manager.py
│   │   ├── _navigation_hud.py
│   │   ├── _quick_tools.py
│   │   ├── _shell_dialogs.py
│   │   ├── _stubs.py
│   │   ├── advanced_features.py
│   │   ├── agent_bridge.py
│   │   ├── ai_assistant_window.py
│   │   ├── ai_assistant_window_monolith_backup.py
│   │   ├── ai_center_window.py
│   │   ├── ai_center_window_v2.py
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
│   │   ├── business_ai_assistant.py
│   │   ├── business_tools.py
│   │   ├── core_engine_star.py
│   │   ├── crm_tools.py
│   │   ├── data_import_tools.py
│   │   ├── data_visualization.py
│   │   ├── digital_emp_window.py
│   │   ├── editor_window.py
│   │   ├── enhanced_chat.py
│   │   ├── finance_analysis_tools.py
│   │   ├── hr_tools.py
│   │   ├── intelligence_window.py
│   │   ├── inventory_tools.py
│   │   ├── key_manager.py
│   │   ├── knowledge_base.py
│   │   ├── llm_config_dialog.py
│   │   ├── marketing_tools.py
│   │   ├── model_config.py
│   │   ├── offline_analyzer.py
│   │   ├── opcclaw_floating_planet.py
│   │   ├── performance_monitor.py
│   │   ├── quick_actions.py
│   │   ├── recommendation_engine.py
│   │   ├── report_generator.py
│   │   ├── scan_window.py
│   │   ├── self_monitor.py
│   │   ├── smart_report_tools.py
│   │   ├── smart_workflow.py
│   │   ├── super_intelligence.py
│   │   ├── super_intelligence_star.py
│   │   ├── system_hub_window.py
│   │   ├── system_monitor.py
│   │   ├── tools_window.py
│   │   ├── vault_window.py
│   │   ├── voice_interface.py
│   │   └── workflow_engine.py
│   ├── personnel/
│   │   ├── __init__.py
│   │   ├── distribution_window.py
│   │   ├── member_window.py
│   │   ├── personnel_window.py
│   │   ├── staff_window.py
│   │   └── wallet_window.py
│   ├── system/
│   │   ├── __init__.py
│   │   ├── activation_window.py
│   │   ├── base_info_window.py
│   │   ├── cloud_window.py
│   │   ├── logs_window.py
│   │   ├── system_hub_window.py
│   │   ├── system_window.py
│   │   └── update_dialog.py
│   └── __init__.py
├── test_kb/
├── gen_book.py
├── main.py
├── rollback_control.py
```

---

## 模块列表

- [`core/__init__.py`](./core/__init__.py.md)
- [`core/agent.py`](./core/agent.py.md)
- [`core/cosmic.py`](./core/cosmic.py.md)
- [`core/data.py`](./core/data.py.md)
- [`core/deps.py`](./core/deps.py.md)
- [`core/llm_client.py`](./core/llm_client.py.md)
- [`core/planet_painter.py`](./core/planet_painter.py.md)
- [`core/voice.py`](./core/voice.py.md)
- [`gen_book.py`](./gen_book.py.md)
- [`main.py`](./main.py.md)
- [`modules/__init__.py`](./modules/__init__.py.md)
- [`modules/auth/__init__.py`](./modules/auth/__init__.py.md)
- [`modules/auth/admin_login_dialog.py`](./modules/auth/admin_login_dialog.py.md)
- [`modules/auth/auth_service.py`](./modules/auth/auth_service.py.md)
- [`modules/auth/change_password_dialog.py`](./modules/auth/change_password_dialog.py.md)
- [`modules/auth/connect_window.py`](./modules/auth/connect_window.py.md)
- [`modules/auth/login_window.py`](./modules/auth/login_window.py.md)
- [`modules/auth/model_setup_window.py`](./modules/auth/model_setup_window.py.md)
- [`modules/auth/upgrade_window.py`](./modules/auth/upgrade_window.py.md)
- [`modules/business/__init__.py`](./modules/business/__init__.py.md)
- [`modules/business/business_window.py`](./modules/business/business_window.py.md)
- [`modules/business/customer_window.py`](./modules/business/customer_window.py.md)
- [`modules/business/finance_window.py`](./modules/business/finance_window.py.md)
- [`modules/business/order_window.py`](./modules/business/order_window.py.md)
- [`modules/business/product_window.py`](./modules/business/product_window.py.md)
- [`modules/dashboard/__init__.py`](./modules/dashboard/__init__.py.md)
- [`modules/dashboard/dashboard_window.py`](./modules/dashboard/dashboard_window.py.md)
- [`modules/data_center/__init__.py`](./modules/data_center/__init__.py.md)
- [`modules/data_center/bi_window.py`](./modules/data_center/bi_window.py.md)
- [`modules/data_center/data_window.py`](./modules/data_center/data_window.py.md)
- [`modules/data_center/report_window.py`](./modules/data_center/report_window.py.md)
- [`modules/intelligence/__init__.py`](./modules/intelligence/__init__.py.md)
- [`modules/intelligence/_ai_shared.py`](./modules/intelligence/_ai_shared.py.md)
- [`modules/intelligence/_ai_widgets.py`](./modules/intelligence/_ai_widgets.py.md)
- [`modules/intelligence/_api_key_dialog.py`](./modules/intelligence/_api_key_dialog.py.md)
- [`modules/intelligence/_chat_dialog.py`](./modules/intelligence/_chat_dialog.py.md)
- [`modules/intelligence/_compat.py`](./modules/intelligence/_compat.py.md)
- [`modules/intelligence/_model_manager.py`](./modules/intelligence/_model_manager.py.md)
- [`modules/intelligence/_navigation_hud.py`](./modules/intelligence/_navigation_hud.py.md)
- [`modules/intelligence/_quick_tools.py`](./modules/intelligence/_quick_tools.py.md)
- [`modules/intelligence/_shell_dialogs.py`](./modules/intelligence/_shell_dialogs.py.md)
- [`modules/intelligence/_stubs.py`](./modules/intelligence/_stubs.py.md)
- [`modules/intelligence/advanced_features.py`](./modules/intelligence/advanced_features.py.md)
- [`modules/intelligence/agent_bridge.py`](./modules/intelligence/agent_bridge.py.md)
- [`modules/intelligence/ai_assistant_window.py`](./modules/intelligence/ai_assistant_window.py.md)
- [`modules/intelligence/ai_assistant_window_monolith_backup.py`](./modules/intelligence/ai_assistant_window_monolith_backup.py.md)
- [`modules/intelligence/ai_center_window.py`](./modules/intelligence/ai_center_window.py.md)
- [`modules/intelligence/ai_center_window_v2.py`](./modules/intelligence/ai_center_window_v2.py.md)
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
- [`modules/intelligence/business_ai_assistant.py`](./modules/intelligence/business_ai_assistant.py.md)
- [`modules/intelligence/business_tools.py`](./modules/intelligence/business_tools.py.md)
- [`modules/intelligence/core/__init__.py`](./modules/intelligence/core/__init__.py.md)
- [`modules/intelligence/core/llm_backend.py`](./modules/intelligence/core/llm_backend.py.md)
- [`modules/intelligence/core_engine_star.py`](./modules/intelligence/core_engine_star.py.md)
- [`modules/intelligence/crm_tools.py`](./modules/intelligence/crm_tools.py.md)
- [`modules/intelligence/data_import_tools.py`](./modules/intelligence/data_import_tools.py.md)
- [`modules/intelligence/data_visualization.py`](./modules/intelligence/data_visualization.py.md)
- [`modules/intelligence/digital_emp_window.py`](./modules/intelligence/digital_emp_window.py.md)
- [`modules/intelligence/editor_window.py`](./modules/intelligence/editor_window.py.md)
- [`modules/intelligence/enhanced_chat.py`](./modules/intelligence/enhanced_chat.py.md)
- [`modules/intelligence/finance_analysis_tools.py`](./modules/intelligence/finance_analysis_tools.py.md)
- [`modules/intelligence/hr_tools.py`](./modules/intelligence/hr_tools.py.md)
- [`modules/intelligence/intelligence_window.py`](./modules/intelligence/intelligence_window.py.md)
- [`modules/intelligence/inventory_tools.py`](./modules/intelligence/inventory_tools.py.md)
- [`modules/intelligence/key_manager.py`](./modules/intelligence/key_manager.py.md)
- [`modules/intelligence/knowledge_base.py`](./modules/intelligence/knowledge_base.py.md)
- [`modules/intelligence/llm_config_dialog.py`](./modules/intelligence/llm_config_dialog.py.md)
- [`modules/intelligence/marketing_tools.py`](./modules/intelligence/marketing_tools.py.md)
- [`modules/intelligence/model_config.py`](./modules/intelligence/model_config.py.md)
- [`modules/intelligence/offline_analyzer.py`](./modules/intelligence/offline_analyzer.py.md)
- [`modules/intelligence/opcclaw_floating_planet.py`](./modules/intelligence/opcclaw_floating_planet.py.md)
- [`modules/intelligence/performance_monitor.py`](./modules/intelligence/performance_monitor.py.md)
- [`modules/intelligence/quick_actions.py`](./modules/intelligence/quick_actions.py.md)
- [`modules/intelligence/recommendation_engine.py`](./modules/intelligence/recommendation_engine.py.md)
- [`modules/intelligence/report_generator.py`](./modules/intelligence/report_generator.py.md)
- [`modules/intelligence/scan_window.py`](./modules/intelligence/scan_window.py.md)
- [`modules/intelligence/self_monitor.py`](./modules/intelligence/self_monitor.py.md)
- [`modules/intelligence/smart_report_tools.py`](./modules/intelligence/smart_report_tools.py.md)
- [`modules/intelligence/smart_workflow.py`](./modules/intelligence/smart_workflow.py.md)
- [`modules/intelligence/super_intelligence.py`](./modules/intelligence/super_intelligence.py.md)
- [`modules/intelligence/super_intelligence_star.py`](./modules/intelligence/super_intelligence_star.py.md)
- [`modules/intelligence/system_hub_window.py`](./modules/intelligence/system_hub_window.py.md)
- [`modules/intelligence/system_monitor.py`](./modules/intelligence/system_monitor.py.md)
- [`modules/intelligence/tools_window.py`](./modules/intelligence/tools_window.py.md)
- [`modules/intelligence/vault_window.py`](./modules/intelligence/vault_window.py.md)
- [`modules/intelligence/voice_interface.py`](./modules/intelligence/voice_interface.py.md)
- [`modules/intelligence/workflow_engine.py`](./modules/intelligence/workflow_engine.py.md)
- [`modules/personnel/__init__.py`](./modules/personnel/__init__.py.md)
- [`modules/personnel/distribution_window.py`](./modules/personnel/distribution_window.py.md)
- [`modules/personnel/member_window.py`](./modules/personnel/member_window.py.md)
- [`modules/personnel/personnel_window.py`](./modules/personnel/personnel_window.py.md)
- [`modules/personnel/staff_window.py`](./modules/personnel/staff_window.py.md)
- [`modules/personnel/wallet_window.py`](./modules/personnel/wallet_window.py.md)
- [`modules/system/__init__.py`](./modules/system/__init__.py.md)
- [`modules/system/activation_window.py`](./modules/system/activation_window.py.md)
- [`modules/system/base_info_window.py`](./modules/system/base_info_window.py.md)
- [`modules/system/cloud_window.py`](./modules/system/cloud_window.py.md)
- [`modules/system/logs_window.py`](./modules/system/logs_window.py.md)
- [`modules/system/system_hub_window.py`](./modules/system/system_hub_window.py.md)
- [`modules/system/system_window.py`](./modules/system/system_window.py.md)
- [`modules/system/update_dialog.py`](./modules/system/update_dialog.py.md)
- [`rollback_control.py`](./rollback_control.py.md)
