"""
数字员工 · NEURAL — 独立子窗口
自动化任务表格 + 新增/编辑/启停按钮 + 表单对话框
"""
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QTextEdit, QWidget, QMessageBox,
    QFormLayout, QLineEdit, QComboBox, QCheckBox, QDialogButtonBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

INPUT_STYLE = """
    QLineEdit, QComboBox, QTextEdit {
        background: rgba(12,6,22,230); color: #ccbbdd;
        border: 1px solid rgba(170,80,255,35); border-radius: 6px;
        padding: 6px 10px; font-size: 12px;
    }
    QLineEdit:focus { border: 1px solid rgba(180,100,255,180); }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: #150a20; color: #ccbbdd; selection-background-color: rgba(150,60,220,80);
    }
"""
TABLE_STYLE = """
    QTableWidget {
        background: rgba(12,6,22,220); color: #ccbbdd;
        border: 1px solid rgba(140,60,200,30); border-radius: 8px;
        gridline-color: rgba(60,20,100,25); font-size: 12px;
        selection-background-color: rgba(150,60,220,60);
    }
    QTableWidget::item { padding: 5px 10px; }
    QHeaderView::section {
        background: rgba(20,10,32,230); color: #aa99cc; padding: 8px 10px;
        border: none; border-bottom: 1px solid rgba(170,80,255,40);
        font-weight: 700; font-size: 11px; letter-spacing: 1px;
    }
"""
BTN_PRIMARY = """
    QPushButton {
        background: rgba(150,60,220,40); color: #ddaaff;
        border: 1px solid rgba(170,80,240,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(170,80,240,70); }
"""


class EmployeeTaskDialog(QDialog):
    """数字员工 — 新增/编辑任务"""

    def __init__(self, parent=None, task=None):
        super().__init__(parent)
        self.setWindowTitle("编辑任务" if task else "新增任务")
        self.setFixedSize(400, 320)
        self.setStyleSheet("background: rgba(16,8,28,235);")
        l = QFormLayout(self)
        l.setSpacing(10)

        self._name = QLineEdit(task.get("name", "") if task else "")
        self._name.setStyleSheet(INPUT_STYLE)
        self._name.setPlaceholderText("如: 数据采集员")
        l.addRow("任务名称:", self._name)

        self._role = QComboBox()
        self._role.addItems(["数据采集", "报表生成", "客户运营", "库存监控", "财务管理", "内容发布", "日志清理"])
        if task:
            idx = self._role.findText(task.get("role", ""))
            if idx >= 0:
                self._role.setCurrentIndex(idx)
        self._role.setStyleSheet(INPUT_STYLE)
        l.addRow("角色:", self._role)

        self._schedule = QLineEdit(task.get("schedule", "每日 8:00") if task else "每日 8:00")
        self._schedule.setStyleSheet(INPUT_STYLE)
        self._schedule.setPlaceholderText("如: 每日 8:00 / 周一 9:00 / 实时")
        l.addRow("调度:", self._schedule)

        self._desc = QLineEdit(task.get("desc", "") if task else "")
        self._desc.setStyleSheet(INPUT_STYLE)
        self._desc.setPlaceholderText("任务描述...")
        l.addRow("描述:", self._desc)

        self._enabled = QCheckBox("启动")
        if task:
            self._enabled.setChecked(task.get("status", True))
        else:
            self._enabled.setChecked(True)
        self._enabled.setStyleSheet("color: #ccbbdd;")
        l.addRow("", self._enabled)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._validate_and_accept)
        btn_box.rejected.connect(self.reject)
        btn_box.setStyleSheet("QPushButton { background: rgba(150,60,220,40); color: #ddaaff; border-radius: 12px; padding: 5px 18px; }")
        l.addRow(btn_box)

    def _validate_and_accept(self):
        if not self._name.text().strip():
            QMessageBox.warning(self, "缺少参数", "请输入任务名称")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self._name.text().strip(),
            "role": self._role.currentText(),
            "schedule": self._schedule.text().strip(),
            "desc": self._desc.text().strip(),
            "status": self._enabled.isChecked(),
            "last_run": "—"
        }


class DigitalEmpWindow(QDialog):
    """数字员工 · NEURAL"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数字员工 · NEURAL")
        self.setMinimumSize(780, 520)
        self.setStyleSheet("background: rgba(10,5,20,240);")
        self._emp_tasks = [
            {"name": "数据采集员", "role": "数据采集", "schedule": "每日 8:00", "status": True, "last_run": "2026-06-10 08:00", "desc": "每日自动采集各平台数据"},
            {"name": "报表生成员", "role": "报表生成", "schedule": "周一 9:00", "status": True, "last_run": "2026-06-09 09:00", "desc": "每周一自动生成周报"},
            {"name": "客户关怀员", "role": "客户运营", "schedule": "每日 10:00", "status": False, "last_run": "—", "desc": "定期发送客户问候"},
            {"name": "库存监控员", "role": "库存监控", "schedule": "实时", "status": True, "last_run": "运行中", "desc": "监控库存告警"},
            {"name": "对账小助手", "role": "财务管理", "schedule": "每月 1 日", "status": True, "last_run": "2026-06-01 08:00", "desc": "月末自动对账"},
        ]
        self._build_ui()
        self._emp_refresh()

    def _build_ui(self):
        l = QVBoxLayout(self)
        l.setSpacing(10)
        l.setContentsMargins(16, 12, 16, 12)

        info = QLabel("数字员工 — 自动化任务执行 / 监控")
        info.setStyleSheet("color: #776699; font-size: 12px; background: transparent;")
        l.addWidget(info)

        stats_row = QHBoxLayout()
        self.emp_stats_label = QLabel("任务: 0 | 运行中: 0 | 已完成: 0")
        self.emp_stats_label.setStyleSheet("color: #9988bb; font-size: 11px; background: rgba(16,8,28,150); border-radius: 8px; padding: 6px 12px;")
        stats_row.addWidget(self.emp_stats_label)
        stats_row.addStretch()
        btn_add = QPushButton("+ 新增任务")
        btn_add.setStyleSheet(BTN_PRIMARY)
        btn_add.clicked.connect(self._emp_add_task)
        stats_row.addWidget(btn_add)
        btn_refresh = QPushButton("刷新")
        btn_refresh.setStyleSheet(BTN_PRIMARY)
        btn_refresh.clicked.connect(self._emp_refresh)
        stats_row.addWidget(btn_refresh)
        l.addLayout(stats_row)

        self.emp_table = QTableWidget()
        self.emp_table.setColumnCount(6)
        self.emp_table.setHorizontalHeaderLabels(["任务名称", "角色", "调度", "状态", "上次执行", "操作"])
        self.emp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.emp_table.setStyleSheet(TABLE_STYLE)
        self.emp_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.emp_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.emp_table.doubleClicked.connect(self._emp_edit_task)
        l.addWidget(self.emp_table, 1)

        log_label = QLabel("执行日志:")
        log_label.setStyleSheet("color: #776699; font-size: 11px; background:transparent;")
        l.addWidget(log_label)
        self.emp_log = QTextEdit()
        self.emp_log.setReadOnly(True)
        self.emp_log.setMaximumHeight(140)
        self.emp_log.setStyleSheet(INPUT_STYLE)
        l.addWidget(self.emp_log)

    def _emp_refresh(self):
        self.emp_table.setRowCount(len(self._emp_tasks))
        running = sum(1 for t in self._emp_tasks if t["status"])
        self.emp_stats_label.setText(f"任务: {len(self._emp_tasks)} | 运行中: {running} | 已停用: {len(self._emp_tasks) - running}")
        for i, task in enumerate(self._emp_tasks):
            self.emp_table.setItem(i, 0, QTableWidgetItem(task["name"]))
            self.emp_table.setItem(i, 1, QTableWidgetItem(task["role"]))
            self.emp_table.setItem(i, 2, QTableWidgetItem(task["schedule"]))
            status_item = QTableWidgetItem("运行中" if task["status"] else "已停用")
            status_item.setForeground(QColor("#44cc88" if task["status"] else "#ff6666"))
            self.emp_table.setItem(i, 3, status_item)
            self.emp_table.setItem(i, 4, QTableWidgetItem(task["last_run"]))
            op_widget = QWidget()
            op_layout = QHBoxLayout(op_widget)
            op_layout.setContentsMargins(2, 2, 2, 2)
            op_layout.setSpacing(4)
            toggle_btn = QPushButton("停用" if task["status"] else "启用")
            toggle_btn.setFixedHeight(22)
            toggle_btn.setFixedWidth(44)
            toggle_btn.setStyleSheet(f"font-size:10px; border-radius:8px; padding:1px 6px; {'background:rgba(200,60,40,40);color:#ffaaaa;' if task['status'] else 'background:rgba(60,200,80,40);color:#aaffaa;'} border:1px solid rgba(120,60,180,40);")
            toggle_btn.clicked.connect(lambda _, idx=i: self._emp_toggle(idx))
            op_layout.addWidget(toggle_btn)
            edit_btn = QPushButton("编辑")
            edit_btn.setFixedHeight(22)
            edit_btn.setFixedWidth(40)
            edit_btn.setStyleSheet("font-size:10px; border-radius:8px; padding:1px 6px; background:rgba(150,60,220,30); color:#ddaaff; border:1px solid rgba(170,80,240,40);")
            edit_btn.clicked.connect(lambda _, idx=i: self._emp_edit_dialog(idx))
            op_layout.addWidget(edit_btn)
            del_btn = QPushButton("删除")
            del_btn.setFixedHeight(22)
            del_btn.setFixedWidth(40)
            del_btn.setStyleSheet("font-size:10px; border-radius:8px; padding:1px 6px; background:rgba(200,60,40,30); color:#ffaaaa; border:1px solid rgba(200,80,50,40);")
            del_btn.clicked.connect(lambda _, idx=i: self._emp_delete(idx))
            op_layout.addWidget(del_btn)
            self.emp_table.setCellWidget(i, 5, op_widget)

    def _emp_toggle(self, idx):
        self._emp_tasks[idx]["status"] = not self._emp_tasks[idx]["status"]
        self._emp_tasks[idx]["last_run"] = "已停用" if not self._emp_tasks[idx]["status"] else "—"
        status_text = "启动" if self._emp_tasks[idx]["status"] else "停用"
        self.emp_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {status_text}: {self._emp_tasks[idx]['name']}")
        self._emp_refresh()

    def _emp_add_task(self):
        dlg = EmployeeTaskDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self._emp_tasks.append(dlg.get_data())
            self.emp_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 新增任务: {dlg.get_data()['name']}")
            self._emp_refresh()

    def _emp_edit_task(self):
        row = self.emp_table.currentRow()
        if row >= 0:
            self._emp_edit_dialog(row)

    def _emp_edit_dialog(self, idx):
        dlg = EmployeeTaskDialog(self, self._emp_tasks[idx])
        if dlg.exec_() == QDialog.Accepted:
            self._emp_tasks[idx] = dlg.get_data()
            self.emp_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 编辑任务: {self._emp_tasks[idx]['name']}")
            self._emp_refresh()

    def _emp_delete(self, idx):
        name = self._emp_tasks[idx]["name"]
        if QMessageBox.question(self, "确认删除", f"确定删除任务「{name}」？") == QMessageBox.Yes:
            del self._emp_tasks[idx]
            self.emp_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 删除任务: {name}")
            self._emp_refresh()