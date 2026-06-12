#!/usr/bin/env python3
"""
全模块审计脚本 — 遍历 modules/ 下所有 .py 文件，做 import + widget 实例化测试。
输出审计报告到 temp 目录。
"""
import sys
import os
import traceback
import importlib
import inspect
import json
from pathlib import Path

# 项目根
PROJECT_ROOT = "/Volumes/D盘工作区/一人公司/one_company_cosmic"
sys.path.insert(0, PROJECT_ROOT)

# 临时 QApplication（最小化平台，无窗口显示）
os.environ["QT_QPA_PLATFORM"] = "minimal"

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QDialog, QFrame, QLabel

# 找所有模块文件
MODULES_DIR = Path(PROJECT_ROOT) / "modules"
py_files = sorted(MODULES_DIR.rglob("*.py"))

# 排除 __init__.py
py_files = [f for f in py_files if f.name != "__init__.py"]

# 映射：文件相对路径 -> 模块名
def file_to_module(filepath: Path) -> str:
    rel = filepath.relative_to(PROJECT_ROOT)
    parts = list(rel.with_suffix("").parts)
    return ".".join(parts)

results = []
total = len(py_files)
passed_import = 0
failed_import = 0
passed_create = 0
failed_create = 0
skipped_create = 0  # 无 widget 类可实例化

app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

for i, fpath in enumerate(py_files, 1):
    mod_name = file_to_module(fpath)
    entry = {
        "index": i,
        "file": str(fpath.relative_to(PROJECT_ROOT)),
        "module": mod_name,
        "import_status": "unknown",
        "import_error": None,
        "import_traceback": None,
        "create_status": "unknown",
        "create_error": None,
        "create_traceback": None,
        "widget_class": None,
    }

    # ── Step 1: import ──
    try:
        mod = importlib.import_module(mod_name)
        entry["import_status"] = "✅ pass"
        passed_import += 1
    except Exception as e:
        entry["import_status"] = "❌ import_fail"
        entry["import_error"] = f"{type(e).__name__}: {e}"
        entry["import_traceback"] = traceback.format_exc()
        failed_import += 1
        results.append(entry)
        continue

    # ── Step 2: 找到可实例化的 widget 类 ──
    widget_classes = []
    for name, obj in inspect.getmembers(mod, inspect.isclass):
        if not issubclass(obj, (QWidget,)):
            continue
        if obj.__module__ != mod_name:
            continue  # 排除 import 进来的外部类
        widget_classes.append((name, obj))

    if not widget_classes:
        entry["create_status"] = "⚠️ skip"
        skipped_create += 1
        results.append(entry)
        continue

    # 优先选命名匹配的类（文件名 → 类名）
    # 例如 customer_window.py → CustomerWindow
    stem = fpath.stem  # e.g. customer_window
    expected_base = "".join(part.capitalize() for part in stem.split("_"))

    target_cls = None
    for cls_name, cls_obj in widget_classes:
        if cls_name == expected_base:
            target_cls = (cls_name, cls_obj)
            break

    # 如果没有精确匹配，选第一个 QMainWindow 或 QDialog
    if target_cls is None:
        for cls_name, cls_obj in widget_classes:
            if issubclass(cls_obj, (QMainWindow, QDialog)):
                target_cls = (cls_name, cls_obj)
                break

    # 再不行取第一个 widget 类
    if target_cls is None:
        target_cls = widget_classes[0]

    cls_name, cls_obj = target_cls
    entry["widget_class"] = cls_name

    # ── Step 3: 实例化 ──
    try:
        # 检查构造函数签名
        sig = inspect.signature(cls_obj.__init__)
        params = list(sig.parameters.keys())
        # 跳过 self
        params = [p for p in params if p != "self"]

        if not params:
            instance = cls_obj()
        elif params == ["parent"] or params == ["parent", "args", "kwargs"]:
            instance = cls_obj(parent=None)
        else:
            # 尝试传 None 给所有参数
            kwargs = {p: None for p in params}
            instance = cls_obj(**kwargs)

        entry["create_status"] = "✅ pass"
        passed_create += 1

        # 清理
        try:
            instance.close()
            instance.deleteLater()
        except Exception:
            import traceback; traceback.print_exc()

    except Exception as e:
        entry["create_status"] = "⚠️ create_fail"
        entry["create_error"] = f"{type(e).__name__}: {e}"
        entry["create_traceback"] = traceback.format_exc()
        failed_create += 1

    results.append(entry)

# ── 生成报告 ──
report_lines = []
report_lines.append("# 模块审计报告")
report_lines.append(f"## 总览")
report_lines.append(f"- 总计: {total} 个模块文件")
report_lines.append(f"- 导入通过: {passed_import} | 导入失败: {failed_import}")
report_lines.append(f"- 实例化通过: {passed_create} | 实例化失败: {failed_create} | 跳过(无widget类): {skipped_create}")
report_lines.append("")

# 按状态分组
import_fail = [r for r in results if r["import_status"] == "❌ import_fail"]
create_fail = [r for r in results if r["create_status"] == "⚠️ create_fail"]
pass_all = [r for r in results if r["import_status"] == "✅ pass" and r["create_status"] in ("✅ pass",)]
skip = [r for r in results if r["create_status"] == "⚠️ skip"]
pass_import_only = [r for r in results if r["import_status"] == "✅ pass" and r["create_status"] not in ("✅ pass", "⚠️ skip")]

# 导入失败
if import_fail:
    report_lines.append("## ❌ 导入失败")
    report_lines.append("")
    for r in import_fail:
        report_lines.append(f"### [{r['index']}] {r['file']}")
        report_lines.append(f"- 模块: `{r['module']}`")
        report_lines.append(f"- 错误: {r['import_error']}")
        tb_short = "\n".join(r["import_traceback"].strip().split("\n")[-4:])
        report_lines.append(f"```\n{tb_short}\n```")
        report_lines.append("")

# 实例化失败
if create_fail:
    report_lines.append("## ⚠️ 实例化失败（导入成功）")
    report_lines.append("")
    for r in create_fail:
        report_lines.append(f"### [{r['index']}] {r['file']}")
        report_lines.append(f"- 模块: `{r['module']}`")
        report_lines.append(f"- 目标类: `{r['widget_class']}`")
        report_lines.append(f"- 错误: {r['create_error']}")
        tb_short = "\n".join(r["create_traceback"].strip().split("\n")[-4:])
        report_lines.append(f"```\n{tb_short}\n```")
        report_lines.append("")

# 跳过的
if skip:
    report_lines.append("## ⚠️ 跳过实例化（导入成功，但无本地 widget 类）")
    report_lines.append("")
    for r in skip:
        report_lines.append(f"- [{r['index']}] {r['file']}")

# 全部通过
if pass_all:
    report_lines.append("## ✅ 全部通过")
    report_lines.append("")
    for r in pass_all:
        report_lines.append(f"- [{r['index']}] {r['file']} → `{r['widget_class']}`")

# 写入报告
report_path = Path(PROJECT_ROOT) / "temp" / "audit_report.md"
os.makedirs(report_path.parent, exist_ok=True)
report_path.write_text("\n".join(report_lines), encoding="utf-8")

# 同时输出 JSON
json_path = Path(PROJECT_ROOT) / "temp" / "audit_report.json"
os.makedirs(json_path.parent, exist_ok=True)
json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"审计完成。")
print(f"报告: {report_path}")
print(f"JSON: {json_path}")
print(f"通过: {passed_import + passed_create}  /  失败: {failed_import + failed_create}  /  跳过: {skipped_create}")
