"""
员工管理 · CREW
独立的 QDialog 子窗口，暖橙主题
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QFormLayout,
    QLineEdit, QComboBox, QTextEdit, QFrame, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from modules.personnel.personnel_window import (
    staff_get_all, staff_add, staff_update, staff_delete,
    staff_import_csv, staff_export_csv
)

# ═══════ 暖橙 QSS ═══════
BTN_PRIMARY = """
    QPushButton {
        background: rgba(255,100,60,40);
        color: #ffccaa;
        border: 1px solid rgba(255,120,70,60);
        border-radius: 16px; padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(255,120,70,70); }
"""
BTN_DANGER = """
    QPushButton {
        background: rgba(200,60,40,40);
        color: #ffaaaa;
        border: 1px solid rgba(200,80,50,60);
        border-radius: 16px; padding: 6px 18px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(220,80,50,70); }
"""
BTN_GREEN = """
    QPushButton {
        background: rgba(40,160,100,40);
        color: #88ffbb;
        border: 1px solid rgba(60,180,120,60);
        border-radius: 16px; padding: 6px 18px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(50,200,120,70); }
"""
TABLE_STYLE = """
    QTableWidget {
        background: rgba(15,8,5,220);
        color: #ddbbaa;
        border: 1px solid rgba(180,80,50,30);
        border-radius: 8px; gridline-color: rgba(80,40,20,25);
        font-size: 12px; selection-background-color: rgba(255,100,60,60);
    }
    QTableWidget::item { padding: 5px 10px; }
    QHeaderView::section {
        background: rgba(25,12,8,230);
        color: #bb9988; padding: 8px 10px; border: none;
        border-bottom: 1px solid rgba(255,100,60,40);
        font-weight: 700; font-size: 11px; letter-spacing: 1px;
    }
"""


# ═══════════════ 员工表单对话框 ═══════════════
class StaffDialog(QDialog):
    def __init__(self, parent=None, row=None):
        super().__init__(parent)
        self.row = row
        self.setWindowTitle("编辑员工" if row else "添加员工")
        self.setMinimumWidth(440)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0e0604, stop:1 #1a0d08);
                border: 1px solid rgba(255,100,60,45); border-radius: 12px;
            }
            QLabel { color: #ccaa99; font-size: 12px; background: transparent; }
            QLineEdit, QComboBox, QTextEdit {
                background: rgba(15,8,5,230); color: #ddbbaa;
                border: 1px solid rgba(255,120,60,35); border-radius: 6px;
                padding: 7px 10px; font-size: 12px;
            }
            QLineEdit:focus { border: 1px solid rgba(255,120,80,180); }
        """)
        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)

        self.edit_name = QLineEdit()
        self.edit_name.setText(row['name'] if row else '')
        self.edit_phone = QLineEdit()
        self.edit_phone.setText(row['phone'] if row else '')
        self.edit_email = QLineEdit()
        self.edit_email.setText(row['email'] if row else '')
        self.edit_position = QLineEdit()
        self.edit_position.setText(row['position'] if row else '')
        self.edit_salary = QLineEdit()
        self.edit_salary.setText(str(row['salary']) if row else '0')
        self.edit_status = QComboBox()
        self.edit_status.addItems(['在职', '离职', '休假'])
        if row:
            self.edit_status.setCurrentText(row['status'])
        self.edit_notes = QTextEdit()
        self.edit_notes.setMaximumHeight(60)
        if row:
            self.edit_notes.setText(row['notes'] or '')

        layout.addRow("姓名:", self.edit_name)
        layout.addRow("电话:", self.edit_phone)
        layout.addRow("邮箱:", self.edit_email)
        layout.addRow("职位:", self.edit_position)
        layout.addRow("薪资:", self.edit_salary)
        layout.addRow("状态:", self.edit_status)
        layout.addRow("备注:", self.edit_notes)

        btn_row = QHBoxLayout()
        save = QPushButton("保存")
        save.clicked.connect(self.accept)
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        save.setStyleSheet(BTN_PRIMARY)
        cancel.setStyleSheet(BTN_DANGER)
        btn_row.addStretch()
        btn_row.addWidget(save)
        btn_row.addWidget(cancel)
        layout.addRow(btn_row)

    def get_data(self):
        return {
            "name": self.edit_name.text().strip(),
            "phone": self.edit_phone.text().strip(),
            "email": self.edit_email.text().strip(),
            "position": self.edit_position.text().strip(),
            "salary": float(self.edit_salary.text() or 0),
            "status": self.edit_status.currentText(),
            "notes": self.edit_notes.toPlainText().strip(),
        }


# ═══════════════ 员工管理主窗口 ═══════════════
class StaffWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("员工管理 · CREW")
        self.setMinimumSize(1000, 650)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a0402, stop:1 #140a06);
            }
        """)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 16)

        # 标题
        title = QLabel("员工管理 · CREW")
        title.setStyleSheet(
            "color: #ffccaa; font-size: 20px; font-weight: 800; "
            "letter-spacing: 4px; background: transparent; padding: 8px 0;"
        )
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # 辉光线
        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(255,100,60,50),
                stop:0.5 rgba(255,140,80,120),
                stop:0.7 rgba(255,100,60,50), stop:1 transparent);
            border: none;
        """)
        layout.addWidget(line)

        # 搜索栏 + 按钮
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("搜索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("姓名 / 电话")
        self.search_input.setMaximumWidth(200)
        self.search_input.setStyleSheet(
            "background: rgba(15,8,5,230); color: #ddbbaa; "
            "border: 1px solid rgba(255,120,60,35); border-radius: 6px; "
            "padding: 6px 10px; font-size: 12px;"
        )
        self.search_input.textChanged.connect(self._load)
        toolbar.addWidget(self.search_input)
        toolbar.addStretch()

        btn_add = QPushButton("+ 添加员工")
        btn_add.setStyleSheet(BTN_PRIMARY)
        btn_add.clicked.connect(self._add)
        btn_import = QPushButton("导入CSV")
        btn_import.setStyleSheet(BTN_PRIMARY)
        btn_import.clicked.connect(self._import)
        btn_export = QPushButton("导出CSV")
        btn_export.setStyleSheet(BTN_GREEN)
        btn_export.clicked.connect(self._export)
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_import)
        toolbar.addWidget(btn_export)
        layout.addLayout(toolbar)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "姓名", "电话", "邮箱", "职位", "薪资", "状态", "备注"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # 操作按钮
        act_row = QHBoxLayout()
        btn_edit = QPushButton("编辑")
        btn_edit.setStyleSheet(BTN_PRIMARY)
        btn_edit.clicked.connect(self._edit)
        btn_del = QPushButton("删除")
        btn_del.setStyleSheet(BTN_DANGER)
        btn_del.clicked.connect(self._delete)
        act_row.addStretch()
        act_row.addWidget(btn_edit)
        act_row.addWidget(btn_del)
        layout.addLayout(act_row)

    # ═══════════ 业务逻辑 ═══════════
    def _load(self):
        search = self.search_input.text().strip()
        rows = staff_get_all(search)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate(
                ['id', 'name', 'phone', 'email', 'position', 'salary', 'status', 'notes']
            ):
                self.table.setItem(
                    i, j,
                    QTableWidgetItem(str(r[k]) if r[k] is not None else "")
                )

    def _add(self):
        dlg = StaffDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            staff_add(**dlg.get_data())
            self._load()

    def _edit(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "提示", "请先选中一行")
        sid = int(self.table.item(row, 0).text())
        rows = staff_get_all()
        target = next((r for r in rows if r['id'] == sid), None)
        if not target:
            return
        dlg = StaffDialog(self, target)
        if dlg.exec_() == QDialog.Accepted:
            staff_update(sid, **dlg.get_data())
            self._load()

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "提示", "请先选中一行")
        sid = int(self.table.item(row, 0).text())
        if QMessageBox.Yes == QMessageBox.question(
            self, "确认", f"确定删除员工 #{sid} 吗？"
        ):
            staff_delete(sid)
            self._load()

    def _import(self):
        fp, _ = QFileDialog.getOpenFileName(self, "选择CSV", "", "CSV (*.csv)")
        if fp:
            c = staff_import_csv(fp)
            QMessageBox.information(self, "导入完成", f"成功导入 {c} 条记录")
            self._load()

    def _export(self):
        fp, _ = QFileDialog.getSaveFileName(self, "导出", "", "CSV (*.csv)")
        if fp:
            staff_export_csv(fp)
            QMessageBox.information(self, "导出完成", "导出成功")