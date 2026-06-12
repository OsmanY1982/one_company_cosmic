#!/usr/bin/env python3
"""
全模块审计脚本 — 遍历 modules/ 下所有 .py 文件，做 import + widget 实例化测试。
输出审计报告到 temp 目录。
用法: env -i HOME="$HOME" PATH="/usr/bin:/bin:/usr/local/bin" python3 temp/audit_modules.py
"""
import os
import sys
import traceback
import importlib
import inspect
import json
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"

# 项目根
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QDialog, QFrame, QLabel

# 找所有模块文件
MODULES_DIR = PROJECT_ROOT / "modules"
py_files = sorted(MODULES_DIR.rglob("*.py"))
py_files = [f for f in py_files if f.name != "__init__.py"]

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
skipped_create = 0

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
        entry["import_status"] = "pass"
        passed_import += 1
    except Exception as e:
        entry["import_status"] = "import_fail"
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
            continue
        widget_classes.append((name, obj))

    if not widget_classes:
        entry["create_status"] = "skip"
        skipped_create += 1
        results.append(entry)
        continue

    # 优先选命名匹配的类
    stem = fpath.stem
    expected_base = "".join(part.capitalize() for part in stem.split("_"))

    target_cls = None
    for cls_name, cls_obj in widget_classes:
        if cls_name == expected_base:
            target_cls = (cls_name, cls_obj)
            break

    if target_cls is None:
        for cls_name, cls_obj in widget_classes:
            if issubclass(cls_obj, (QMainWindow, QDialog)):
                target_cls = (cls_name, cls_obj)
                break

    if target_cls is None:
        target_cls = widget_classes[0]

    cls_name, cls_obj = target_cls
    entry["widget_class"] = cls_name

    # ── Step 3: 实例化 ──
    try:
        sig = inspect.signature(cls_obj.__init__)
        params = [p for p in sig.parameters.keys() if p != "self"]

        if not params:
            instance = cls_obj()
        elif params == ["parent"]:
            instance = cls_obj(parent=None)
        else:
            kwargs = {p: None for p in params}
            instance = cls_obj(**kwargs)

        entry["create_status"] = "pass"
        passed_create += 1

        try:
            instance.close()
            instance.deleteLater()
        except Exception:
            import traceback; traceback.print_exc()

    except Exception as e:
        entry["create_status"] = "create_fail"
        entry["create_error"] = f"{type(e).__name__}: {e}"
        entry["create_traceback"] = traceback.format_exc()
        failed_create += 1

    results.append(entry)

# ── 生成 Markdown 报告 ──
md_lines = []
md_lines.append("# 模块审计报告")
md_lines.append(f"**时间**: {__import__('datetime').datetime.now().isoformat()}")
md_lines.append("")
md_lines.append("## 总览")
md_lines.append("")
md_lines.append(f"| 指标 | 数值 |")
md_lines.append(f"|------|------|")
md_lines.append(f"| 模块文件总数 | {total} |")
md_lines.append(f"| 导入通过 | {passed_import} |")
md_lines.append(f"| 导入失败 | {failed_import} |")
md_lines.append(f"| 实例化通过 | {passed_create} |")
md_lines.append(f"| 实例化失败 | {failed_create} |")
md_lines.append(f"| 跳过(无widget类) | {skipped_create} |")
md_lines.append("")

import_fail = [r for r in results if r["import_status"] == "import_fail"]
create_fail = [r for r in results if r["create_status"] == "create_fail"]
pass_all = [r for r in results if r["import_status"] == "pass" and r["create_status"] == "pass"]
skip = [r for r in results if r["create_status"] == "skip"]

if import_fail:
    md_lines.append("## ❌ 导入失败")
    md_lines.append("")
    for r in import_fail:
        md_lines.append(f"### [{r['index']}] `{r['file']}`")
        md_lines.append(f"- **模块**: `{r['module']}`")
        md_lines.append(f"- **错误**: `{r['import_error']}`")
        tb_lines = r["import_traceback"].strip().split("\n")
        tb_short = "\n".join(tb_lines[-5:])
        md_lines.append(f"```\n{tb_short}\n```")
        md_lines.append("")

if create_fail:
    md_lines.append("## ⚠️ 实例化失败（导入成功）")
    md_lines.append("")
    for r in create_fail:
        md_lines.append(f"### [{r['index']}] `{r['file']}`")
        md_lines.append(f"- **模块**: `{r['module']}`")
        md_lines.append(f"- **目标类**: `{r['widget_class']}`")
        md_lines.append(f"- **错误**: `{r['create_error']}`")
        tb_lines = r["create_traceback"].strip().split("\n")
        tb_short = "\n".join(tb_lines[-5:])
        md_lines.append(f"```\n{tb_short}\n```")
        md_lines.append("")

if skip:
    md_lines.append("## ⚠️ 跳过实例化（导入成功，无本地 widget 类）")
    md_lines.append("")
    for r in skip:
        md_lines.append(f"- [{r['index']}] `{r['file']}`")

if pass_all:
    md_lines.append("## ✅ 全部通过")
    md_lines.append("")
    for r in pass_all:
        md_lines.append(f"- [{r['index']}] `{r['file']}` → `{r['widget_class']}`")

# 写入
report_dir = PROJECT_ROOT / "temp"
report_dir.mkdir(parents=True, exist_ok=True)

md_path = report_dir / "audit_report.md"
md_path.write_text("\n".join(md_lines), encoding="utf-8")

json_path = report_dir / "audit_report.json"
json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"DONE|import_pass={passed_import}|import_fail={failed_import}|create_pass={passed_create}|create_fail={failed_create}|skip={skipped_create}")
print(f"MD: {md_path}")
print(f"JSON: {json_path}")
