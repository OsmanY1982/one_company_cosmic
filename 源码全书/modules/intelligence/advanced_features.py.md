# `modules/intelligence/advanced_features.py`

> 路径：`modules/intelligence/advanced_features.py` | 行数：510


---


```python
# -*- coding: utf-8 -*-
"""
高级功能面板 - 集成工作流、知识库、语音、可视化
"""

import os
import sys
from typing import Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QTextEdit, QLineEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QMessageBox,
    QProgressBar, QFileDialog, QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class WorkflowThread(QThread):
    """工作流执行线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    
    def __init__(self, workflow_id: str):
        super().__init__()
        self.workflow_id = workflow_id
        
    def run(self):
        try:
            from modules.intelligence.workflow_engine import workflow_engine
            result = workflow_engine.execute_workflow(self.workflow_id)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"success": False, "error": str(e)})


class AdvancedFeaturesWidget(QWidget):
    """高级功能面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 标题
        title = QLabel("🚀 高级功能")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # 子标签页 — 使用轨道式 QStackedWidget 替代 QTabWidget
        self._tab_stack = QStackedWidget()
        
        # 导航按钮栏
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(4)
        self._tab_btns = []
        tab_defs = [
            ("⚙️ 工作流", 0),
            ("📚 知识库", 1),
            ("📊 可视化", 2),
        ]
        for name, idx in tab_defs:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background: #edf2f7; padding: 10px 20px; margin-right: 2px;
                    border-top-left-radius: 8px; border-top-right-radius: 8px;
                    font-size: 13px; font-weight: bold; border: none;
                }
                QPushButton:checked {
                    background: white; color: #3498db;
                    border-bottom: 3px solid #3498db;
                }
            """)
            btn.clicked.connect(lambda checked, i=idx: self._switch_tab(i))
            nav_layout.addWidget(btn)
            self._tab_btns.append(btn)
        nav_layout.addStretch()
        
        layout.addLayout(nav_layout)
        
        # 工作流标签
        self._tab_stack.addWidget(self._create_workflow_tab())
        
        # 知识库标签
        self._tab_stack.addWidget(self._create_knowledge_tab())
        
        # 可视化标签
        self._tab_stack.addWidget(self._create_visualization_tab())
        
        layout.addWidget(self._tab_stack)
        
        # 默认选中第一个
        self._tab_btns[0].setChecked(True)
        self._tab_stack.setCurrentIndex(0)
        
    def _switch_tab(self, idx):
        """切换轨道式标签页"""
        self._tab_stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._tab_btns):
            btn.setChecked(i == idx)
        
    def _create_workflow_tab(self) -> QWidget:
        """创建工作流标签"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 预设工作流
        preset_group = QGroupBox("预设工作流")
        preset_layout = QVBoxLayout(preset_group)
        
        preset_buttons = [
            ("每日报告", "daily_report", "自动生成每日业务报告"),
            ("数据备份", "data_backup", "备份重要数据"),
            ("网页采集", "web_scraper", "自动采集网页数据"),
        ]
        
        for name, preset_id, desc in preset_buttons:
            btn = QPushButton(f"{name} - {desc}")
            btn.clicked.connect(lambda checked, pid=preset_id: self._run_preset_workflow(pid))
            preset_layout.addWidget(btn)
        
        layout.addWidget(preset_group)
        
        # 自定义工作流
        custom_group = QGroupBox("自定义工作流")
        custom_layout = QVBoxLayout(custom_group)
        
        self._workflow_input = QTextEdit()
        self._workflow_input.setPlaceholderText("""输入工作流JSON定义:
{
  "name": "我的工作流",
  "description": "描述",
  "steps": [
    {
      "id": "step1",
      "name": "步骤1",
      "tool_name": "run_code",
      "params": {"code": "print('hello')"}
    }
  ]
}""")
        self._workflow_input.setMaximumHeight(200)
        custom_layout.addWidget(self._workflow_input)
        
        run_btn = QPushButton("▶ 执行工作流")
        run_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60; color: white; padding: 10px;
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background: #219a52; }
        """)
        run_btn.clicked.connect(self._run_custom_workflow)
        custom_layout.addWidget(run_btn)
        
        layout.addWidget(custom_group)
        
        # 结果显示
        self._workflow_result = QTextEdit()
        self._workflow_result.setReadOnly(True)
        self._workflow_result.setPlaceholderText("工作流执行结果...")
        layout.addWidget(self._workflow_result)
        
        layout.addStretch()
        return widget
        
    def _create_knowledge_tab(self) -> QWidget:
        """创建知识库标签"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 导入区域
        import_group = QGroupBox("导入文档")
        import_layout = QVBoxLayout(import_group)
        
        btn_layout = QHBoxLayout()
        
        import_file_btn = QPushButton("📁 导入文件")
        import_file_btn.clicked.connect(self._import_file)
        btn_layout.addWidget(import_file_btn)
        
        import_text_btn = QPushButton("📝 导入文本")
        import_text_btn.clicked.connect(self._import_text)
        btn_layout.addWidget(import_text_btn)
        
        btn_layout.addStretch()
        import_layout.addLayout(btn_layout)
        
        self._doc_title = QLineEdit()
        self._doc_title.setPlaceholderText("文档标题")
        import_layout.addWidget(self._doc_title)
        
        self._doc_content = QTextEdit()
        self._doc_content.setPlaceholderText("文档内容（如果是导入文本）")
        self._doc_content.setMaximumHeight(100)
        import_layout.addWidget(self._doc_content)
        
        layout.addWidget(import_group)
        
        # 查询区域
        query_group = QGroupBox("智能查询")
        query_layout = QVBoxLayout(query_group)
        
        self._query_input = QLineEdit()
        self._query_input.setPlaceholderText("输入问题...")
        query_layout.addWidget(self._query_input)
        
        query_btn = QPushButton("🔍 查询")
        query_btn.clicked.connect(self._query_knowledge)
        query_layout.addWidget(query_btn)
        
        self._query_result = QTextEdit()
        self._query_result.setReadOnly(True)
        self._query_result.setPlaceholderText("查询结果...")
        query_layout.addWidget(self._query_result)
        
        layout.addWidget(query_group)
        
        # 文档列表
        list_group = QGroupBox("文档列表")
        list_layout = QVBoxLayout(list_group)
        
        self._doc_table = QTableWidget()
        self._doc_table.setColumnCount(4)
        self._doc_table.setHorizontalHeaderLabels(["ID", "标题", "类型", "操作"])
        self._doc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        list_layout.addWidget(self._doc_table)
        
        refresh_btn = QPushButton("🔄 刷新列表")
        refresh_btn.clicked.connect(self._refresh_doc_list)
        list_layout.addWidget(refresh_btn)
        
        layout.addWidget(list_group)
        
        layout.addStretch()
        return widget
        
    def _create_visualization_tab(self) -> QWidget:
        """创建可视化标签"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 数据输入
        input_group = QGroupBox("数据输入 (JSON)")
        input_layout = QVBoxLayout(input_group)
        
        self._viz_data = QTextEdit()
        self._viz_data.setPlaceholderText('''[
  {"label": "一月", "value": 100},
  {"label": "二月", "value": 150},
  {"label": "三月", "value": 120}
]''')
        self._viz_data.setMaximumHeight(150)
        input_layout.addWidget(self._viz_data)
        
        btn_layout = QHBoxLayout()
        
        btn_layout.addWidget(QLabel("图表类型:"))
        self._viz_type = QComboBox()
        self._viz_type.addItems(["柱状图", "折线图", "饼图", "表格"])
        btn_layout.addWidget(self._viz_type)
        
        generate_btn = QPushButton("📊 生成")
        generate_btn.clicked.connect(self._generate_visualization)
        btn_layout.addWidget(generate_btn)
        
        btn_layout.addStretch()
        input_layout.addLayout(btn_layout)
        
        layout.addWidget(input_group)
        
        # 结果显示
        self._viz_result = QTextEdit()
        self._viz_result.setReadOnly(True)
        self._viz_result.setPlaceholderText("可视化结果...")
        layout.addWidget(self._viz_result)
        
        # 报表生成
        report_group = QGroupBox("报表生成")
        report_layout = QVBoxLayout(report_group)
        
        self._report_title = QLineEdit()
        self._report_title.setPlaceholderText("报表标题")
        report_layout.addWidget(self._report_title)
        
        report_btn = QPushButton("📄 生成HTML报表")
        report_btn.clicked.connect(self._generate_report)
        report_layout.addWidget(report_btn)
        
        layout.addWidget(report_group)
        
        layout.addStretch()
        return widget
        
    def _run_preset_workflow(self, preset_id: str):
        """运行预设工作流"""
        try:
            from modules.intelligence.workflow_engine import workflow_engine
            
            workflow = workflow_engine.create_preset_workflow(preset_id)
            if workflow:
                self._workflow_result.append(f"创建工作流: {workflow.name}\n")
                
                # 执行工作流
                self._workflow_thread = WorkflowThread(workflow.id)
                self._workflow_thread.finished.connect(self._on_workflow_finished)
                self._workflow_thread.start()
            else:
                QMessageBox.warning(self, "错误", f"未知预设: {preset_id}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
    
    def _run_custom_workflow(self):
        """运行自定义工作流"""
        try:
            import json
            from modules.intelligence.workflow_engine import workflow_engine
            
            data = json.loads(self._workflow_input.toPlainText())
            workflow = workflow_engine.create_workflow(
                name=data["name"],
                description=data.get("description", ""),
                steps=data["steps"],
            )
            
            self._workflow_result.append(f"创建工作流: {workflow.name}\n")
            
            self._workflow_thread = WorkflowThread(workflow.id)
            self._workflow_thread.finished.connect(self._on_workflow_finished)
            self._workflow_thread.start()
            
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "错误", f"JSON格式错误: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
    
    def _on_workflow_finished(self, result: dict):
        """工作流完成"""
        if result.get("success"):
            self._workflow_result.append(f"✅ 成功: {result.get('message', '')}\n")
        else:
            self._workflow_result.append(f"❌ 失败: {result.get('error', '')}\n")
        
        self._workflow_result.append(f"结果: {result}\n")
        self._workflow_result.append("-" * 50 + "\n")
    
    def _import_file(self):
        """导入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "文本文件 (*.txt *.md *.json);;所有文件 (*.*)"
        )
        if file_path:
            try:
                from modules.intelligence.knowledge_base import knowledge_base
                result = knowledge_base.import_document(file_path, self._doc_title.text())
                
                if result.get("success"):
                    QMessageBox.information(self, "成功", f"导入成功: {result['title']}")
                    self._refresh_doc_list()
                else:
                    QMessageBox.critical(self, "错误", result.get("error", "导入失败"))
                    
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))
    
    def _import_text(self):
        """导入文本"""
        title = self._doc_title.text().strip()
        content = self._doc_content.toPlainText().strip()
        
        if not title or not content:
            QMessageBox.warning(self, "提示", "请输入标题和内容")
            return
        
        try:
            from modules.intelligence.knowledge_base import knowledge_base
            result = knowledge_base.import_text(content, title)
            
            if result.get("success"):
                QMessageBox.information(self, "成功", f"导入成功: {result['title']}")
                self._refresh_doc_list()
            else:
                QMessageBox.critical(self, "错误", result.get("error", "导入失败"))
                
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
    
    def _query_knowledge(self):
        """查询知识库"""
        question = self._query_input.text().strip()
        if not question:
            QMessageBox.warning(self, "提示", "请输入问题")
            return
        
        try:
            from modules.intelligence.knowledge_base import knowledge_base
            result = knowledge_base.query(question)
            
            if result.get("success"):
                self._query_result.setText(result.get("answer", ""))
            else:
                self._query_result.setText(f"查询失败: {result.get('error', '')}")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
    
    def _refresh_doc_list(self):
        """刷新文档列表"""
        try:
            from modules.intelligence.knowledge_base import knowledge_base
            docs = knowledge_base.list_documents()
            
            self._doc_table.setRowCount(len(docs))
            for i, doc in enumerate(docs):
                self._doc_table.setItem(i, 0, QTableWidgetItem(doc.get("id", "")))
                self._doc_table.setItem(i, 1, QTableWidgetItem(doc.get("title", "")))
                self._doc_table.setItem(i, 2, QTableWidgetItem(doc.get("doc_type", "")))
                
                delete_btn = QPushButton("删除")
                delete_btn.clicked.connect(lambda checked, did=doc.get("id"): self._delete_doc(did))
                self._doc_table.setCellWidget(i, 3, delete_btn)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
    
    def _delete_doc(self, doc_id: str):
        """删除文档"""
        try:
            from modules.intelligence.knowledge_base import knowledge_base
            if knowledge_base.delete_document(doc_id):
                QMessageBox.information(self, "成功", "删除成功")
                self._refresh_doc_list()
            else:
                QMessageBox.warning(self, "错误", "删除失败")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
    
    def _generate_visualization(self):
        """生成可视化"""
        try:
            import json
            from modules.intelligence.data_visualization import DataVisualization
            
            data = json.loads(self._viz_data.toPlainText())
            chart_type_map = {"柱状图": "bar", "折线图": "line", "饼图": "pie", "表格": "table"}
            chart_type = chart_type_map.get(self._viz_type.currentText(), "bar")
            
            if chart_type == "table":
                result = DataVisualization.generate_table(data)
            else:
                result = DataVisualization.generate_chart_data(data, chart_type)
            
            self._viz_result.setText(json.dumps(result, ensure_ascii=False, indent=2))
            
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "错误", f"JSON格式错误: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
    
    def _generate_report(self):
        """生成报表"""
        try:
            from modules.intelligence.data_visualization import DataVisualization
            
            title = self._report_title.text().strip() or "数据报表"
            
            sections = [
                {
                    "type": "text",
                    "title": "概述",
                    "content": "自动生成的数据报表",
                },
                {
                    "type": "metrics",
                    "title": "关键指标",
                    "metrics": [
                        {"label": "数据量", "value": "100"},
                        {"label": "完成率", "value": "98%"},
                    ],
                },
            ]
            
            html = DataVisualization.generate_report(title, sections)
            
            output_path = os.path.join(os.path.expanduser("~"), "report.html")
            if DataVisualization.save_report(html, output_path):
                self._viz_result.setText(f"报表已保存到: {output_path}\n\n{html[:500]}...")
                QMessageBox.information(self, "完成", f"报表已保存")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    widget = AdvancedFeaturesWidget()
    widget.setWindowTitle("高级功能")
    widget.resize(900, 700)
    widget.show()
    sys.exit(app.exec_())

```
