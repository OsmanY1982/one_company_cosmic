"""
工具箱 · NEURAL — 独立子窗口
内嵌 QTabWidget: 文本编辑器 + 密码保险箱
"""
import os, json, hashlib, base64, secrets
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QHeaderView, QTextEdit,
    QLineEdit, QWidget, QMessageBox, QFileDialog, QInputDialog,
    QComboBox, QFormLayout, QDialogButtonBox, QMenu, QApplication,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
VAULT_FILE = os.path.join(DATA_DIR, "vault_cosmic.enc")
VAULT_CATEGORIES = ["全部", "社交媒体", "银行金融", "购物电商", "工作办公", "游戏娱乐", "邮箱", "开发工具", "其他"]
VAULT_CAT_COLORS = {
    "银行金融": "#e53e3e", "社交媒体": "#3182ce", "购物电商": "#d69e2e",
    "工作办公": "#38a169", "游戏娱乐": "#805ad5", "邮箱": "#dd6b20",
    "开发工具": "#2b6cb0", "其他": "#718096",
}

TAB_STYLE = """
    QTabWidget::pane {
        background: transparent;
        border: 1px solid rgba(170,80,255,30);
        border-radius: 10px;
    }
    QTabBar::tab {
        background: rgba(16,8,28,220);
        color: #9988bb; padding: 10px 22px;
        border: none; border-bottom: 2px solid transparent;
        font-size: 12px; font-weight: 600; letter-spacing: 2px; min-width: 70px;
    }
    QTabBar::tab:selected {
        color: #ddaaff;
        border-bottom: 2px solid #aa44ff;
        background: rgba(24,12,38,235);
    }
    QTabBar::tab:hover { color: #cc88ee; }
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
BTN_PRIMARY = """
    QPushButton {
        background: rgba(150,60,220,40); color: #ddaaff;
        border: 1px solid rgba(170,80,240,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(170,80,240,70); }
"""
BTN_DANGER = """
    QPushButton {
        background: rgba(200,60,40,40); color: #ffaaaa;
        border: 1px solid rgba(200,80,50,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(220,80,50,70); }
"""


def _vault_derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)

def _vault_xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

def vault_encrypt(plaintext: str, password: str) -> str:
    salt = os.urandom(16)
    key = _vault_derive_key(password, salt)
    enc = _vault_xor(plaintext.encode('utf-8'), key)
    return base64.b64encode(salt + enc).decode()

def vault_decrypt(ciphertext: str, password: str) -> str:
    payload = base64.b64decode(ciphertext.encode())
    salt = payload[:16]
    enc = payload[16:]
    key = _vault_derive_key(password, salt)
    return _vault_xor(enc, key).decode('utf-8')


class VaultEntryDialog(QDialog):
    """密码保险箱 — 新增/编辑条目"""

    def __init__(self, parent=None, entry=None):
        super().__init__(parent)
        self.setWindowTitle("编辑条目" if entry else "新建条目")
        self.setFixedSize(380, 300)
        self.setStyleSheet("background: rgba(16,8,28,235);")
        l = QFormLayout(self)
        l.setSpacing(10)

        self._title = QLineEdit(entry.get("title", "") if entry else "")
        self._title.setStyleSheet(INPUT_STYLE)
        self._title.setPlaceholderText("如: Google 账号")
        l.addRow("名称:", self._title)

        self._category = QComboBox()
        self._category.addItems(VAULT_CATEGORIES[1:])
        if entry:
            idx = self._category.findText(entry.get("category", "其他"))
            if idx >= 0:
                self._category.setCurrentIndex(idx)
        self._category.setStyleSheet(INPUT_STYLE)
        l.addRow("分类:", self._category)

        self._account = QLineEdit(entry.get("account", "") if entry else "")
        self._account.setStyleSheet(INPUT_STYLE)
        self._account.setPlaceholderText("邮箱 / 手机号")
        l.addRow("账号:", self._account)

        self._password = QLineEdit(entry.get("password", "") if entry else "")
        self._password.setStyleSheet(INPUT_STYLE)
        self._password.setPlaceholderText("密码")
        self._password.setEchoMode(QLineEdit.Password)
        l.addRow("密码:", self._password)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._validate_and_accept)
        btn_box.rejected.connect(self.reject)
        btn_box.setStyleSheet("QPushButton { background: rgba(150,60,220,40); color: #ddaaff; border-radius: 12px; padding: 5px 18px; }")
        l.addRow(btn_box)

    def _validate_and_accept(self):
        if not self._title.text().strip():
            QMessageBox.warning(self, "缺少参数", "请输入名称")
            return
        self.accept()

    def get_data(self):
        return {
            "title": self._title.text().strip(),
            "category": self._category.currentText(),
            "account": self._account.text().strip(),
            "password": self._password.text(),
            "url": ""
        }


class ToolsWindow(QDialog):
    """工具箱 · NEURAL"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("工具箱 · NEURAL")
        self.setMinimumSize(800, 560)
        self.setStyleSheet("background: rgba(10,5,20,240);")
        self._editor_filepath = None
        self._editor_password = None
        self._vault_master_pwd = None
        self._vault_entries = []
        self._build_ui()

    def _build_ui(self):
        l = QVBoxLayout(self)
        l.setSpacing(8)
        l.setContentsMargins(8, 8, 8, 8)

        info = QLabel("工具箱 — 文本编辑器 / 密码保险箱")
        info.setStyleSheet("color: #776699; font-size: 12px; background: transparent;")
        l.addWidget(info)

        inner = QTabWidget()
        inner.setStyleSheet(TAB_STYLE)

        # ── 子标签1: 文本编辑器 ──
        ed_tab = QWidget()
        ed_l = QVBoxLayout(ed_tab)
        ed_l.setContentsMargins(10, 10, 10, 10)
        ed_l.setSpacing(6)

        tb = QHBoxLayout()
        btn_open = QPushButton("打开")
        btn_open.setStyleSheet(BTN_PRIMARY)
        btn_open.clicked.connect(self._tool_editor_open)
        tb.addWidget(btn_open)
        btn_save = QPushButton("保存")
        btn_save.setStyleSheet(BTN_PRIMARY)
        btn_save.clicked.connect(self._tool_editor_save)
        tb.addWidget(btn_save)
        btn_enc = QPushButton("加密保存")
        btn_enc.setStyleSheet(BTN_PRIMARY)
        btn_enc.clicked.connect(self._tool_editor_save_enc)
        tb.addWidget(btn_enc)
        self._editor_path_label = QLabel("未打开文件")
        self._editor_path_label.setStyleSheet("color: #8877aa; font-size: 11px; background:transparent;")
        tb.addWidget(self._editor_path_label)
        tb.addStretch()
        ed_l.addLayout(tb)

        self._editor = QTextEdit()
        self._editor.setStyleSheet("""
            QTextEdit {
                background: rgba(8,4,16,230); color: #ccbbdd;
                border: 1px solid rgba(170,80,255,35); border-radius: 10px;
                padding: 12px; font-size: 13px; line-height: 1.6;
            }
        """)
        self._editor.textChanged.connect(self._tool_update_editor_status)
        ed_l.addWidget(self._editor, 1)

        sb = QHBoxLayout()
        self._editor_status = QLabel("字数: 0")
        self._editor_status.setStyleSheet("color: #8877aa; font-size: 11px; background:transparent;")
        sb.addWidget(self._editor_status)
        sb.addStretch()
        btn_clear_ed = QPushButton("清空")
        btn_clear_ed.setStyleSheet(BTN_DANGER)
        btn_clear_ed.clicked.connect(lambda: self._editor.clear())
        sb.addWidget(btn_clear_ed)
        ed_l.addLayout(sb)

        inner.addTab(ed_tab, "文本编辑器")

        # ── 子标签2: 密码保险箱 ──
        vault_tab = QWidget()
        vt_l = QVBoxLayout(vault_tab)
        vt_l.setContentsMargins(10, 10, 10, 10)
        vt_l.setSpacing(8)

        self._vault_lock_widget = QWidget()
        lock_l = QVBoxLayout(self._vault_lock_widget)
        lock_l.setAlignment(Qt.AlignCenter)
        lock_title = QLabel("密码保险箱")
        lock_title.setStyleSheet("color: #aa99dd; font-size: 20px; font-weight: 700; background:transparent;")
        lock_title.setAlignment(Qt.AlignCenter)
        lock_l.addWidget(lock_title)
        lock_l.addSpacing(20)
        self._vault_pwd_input = QLineEdit()
        self._vault_pwd_input.setPlaceholderText("输入主密码解锁...")
        self._vault_pwd_input.setEchoMode(QLineEdit.Password)
        self._vault_pwd_input.setStyleSheet(INPUT_STYLE + "QLineEdit { max-width: 280px; }")
        self._vault_pwd_input.returnPressed.connect(self._vault_unlock)
        lock_l.addWidget(self._vault_pwd_input, alignment=Qt.AlignCenter)
        self._vault_lock_msg = QLabel("")
        self._vault_lock_msg.setStyleSheet("color: #ff8888; font-size: 12px; background:transparent;")
        self._vault_lock_msg.setAlignment(Qt.AlignCenter)
        lock_l.addWidget(self._vault_lock_msg)
        btn_unlock = QPushButton("解锁")
        btn_unlock.setStyleSheet(BTN_PRIMARY + "QPushButton { max-width: 120px; }")
        btn_unlock.clicked.connect(self._vault_unlock)
        lock_l.addWidget(btn_unlock, alignment=Qt.AlignCenter)
        vt_l.addWidget(self._vault_lock_widget)

        self._vault_main_widget = QWidget()
        vm_l = QVBoxLayout(self._vault_main_widget)
        vm_l.setContentsMargins(0, 0, 0, 0)
        vm_l.setSpacing(8)

        vault_top = QHBoxLayout()
        self._vault_count_lbl = QLabel("共 0 条")
        self._vault_count_lbl.setStyleSheet("color: #8877aa; font-size: 12px; background:transparent;")
        vault_top.addWidget(self._vault_count_lbl)
        vault_top.addStretch()
        btn_repwd = QPushButton("改密")
        btn_repwd.setStyleSheet(BTN_PRIMARY)
        btn_repwd.clicked.connect(self._vault_change_pwd)
        vault_top.addWidget(btn_repwd)
        btn_vadd = QPushButton("+ 添加")
        btn_vadd.setStyleSheet(BTN_PRIMARY)
        btn_vadd.clicked.connect(self._vault_add_entry)
        vault_top.addWidget(btn_vadd)
        btn_locknow = QPushButton("锁定")
        btn_locknow.setStyleSheet(BTN_DANGER)
        btn_locknow.clicked.connect(self._vault_lock)
        vault_top.addWidget(btn_locknow)
        vm_l.addLayout(vault_top)

        filter_row = QHBoxLayout()
        self._vault_search = QLineEdit()
        self._vault_search.setPlaceholderText("搜索...")
        self._vault_search.setStyleSheet(INPUT_STYLE)
        self._vault_search.textChanged.connect(self._vault_refresh)
        filter_row.addWidget(self._vault_search)
        self._vault_cat = QComboBox()
        self._vault_cat.addItems(VAULT_CATEGORIES)
        self._vault_cat.setStyleSheet("background: rgba(20,10,35,230); color: #bb99dd; border: 1px solid rgba(170,80,255,35); border-radius: 8px; padding: 4px 8px;")
        self._vault_cat.currentIndexChanged.connect(self._vault_refresh)
        filter_row.addWidget(self._vault_cat)
        self._vault_show_pwd = QPushButton("显示密码")
        self._vault_show_pwd.setCheckable(True)
        self._vault_show_pwd.setStyleSheet(BTN_PRIMARY)
        self._vault_show_pwd.toggled.connect(self._vault_refresh)
        filter_row.addWidget(self._vault_show_pwd)
        vm_l.addLayout(filter_row)

        self._vault_table = QTableWidget()
        self._vault_table.setColumnCount(5)
        self._vault_table.setHorizontalHeaderLabels(["名称", "分类", "账号", "密码", "更新时间"])
        self._vault_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._vault_table.setStyleSheet(TABLE_STYLE)
        self._vault_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._vault_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._vault_table.doubleClicked.connect(self._vault_edit_entry)
        self._vault_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._vault_table.customContextMenuRequested.connect(self._vault_context_menu)
        vm_l.addWidget(self._vault_table, 1)

        vt_l.addWidget(self._vault_main_widget)
        self._vault_main_widget.hide()
        inner.addTab(vault_tab, "密码保险箱")

        l.addWidget(inner)

    # ═══════ 文本编辑器方法 ═══════
    def _tool_editor_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开文件", "",
            "文本文件 (*.txt *.md *.py *.json *.html *.csv);;所有文件 (*)")
        if not path:
            return
        try:
            raw = open(path, 'rb').read(12)
            if raw.startswith(b'VLT'):
                pwd, ok = QInputDialog.getText(self, "加密文件", "输入密码：", QLineEdit.Password)
                if not ok:
                    return
                full = open(path, encoding='utf-8').read()
                try:
                    content = vault_decrypt(full, pwd)
                    self._editor_filepath = path
                    self._editor_password = pwd
                except Exception:
                    QMessageBox.warning(self, "错误", "密码错误或文件损坏")
                    return
            else:
                content = open(path, encoding='utf-8', errors='replace').read()
                self._editor_filepath = path
                self._editor_password = None
            self._editor.setPlainText(content)
            self._editor_path_label.setText(os.path.basename(path))
            self._tool_update_editor_status()
        except Exception as e:
            QMessageBox.warning(self, "打开失败", str(e))

    def _tool_editor_save(self):
        if not self._editor_filepath:
            return self._tool_editor_save_as()
        try:
            content = self._editor.toPlainText()
            if self._editor_password:
                enc = vault_encrypt(content, self._editor_password)
                with open(self._editor_filepath, 'wb') as f:
                    f.write(enc.encode())
            else:
                with open(self._editor_filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            self._editor_path_label.setText(os.path.basename(self._editor_filepath))
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))

    def _tool_editor_save_enc(self):
        self._tool_editor_save_as(encrypted=True)

    def _tool_editor_save_as(self, encrypted=False):
        ext = ".opc" if encrypted else ".txt"
        path, _ = QFileDialog.getSaveFileName(self, "保存文件", "", f"文本文件 (*{ext});;所有文件 (*)")
        if not path:
            return False
        if encrypted:
            pwd, ok = QInputDialog.getText(self, "设置密码", "请输入加密密码（至少4位）：", QLineEdit.Password)
            if not ok or len(pwd) < 4:
                QMessageBox.warning(self, "错误", "密码至少4位")
                return False
            confirm, ok = QInputDialog.getText(self, "确认密码", "再次输入密码：", QLineEdit.Password)
            if not ok or pwd != confirm:
                QMessageBox.warning(self, "错误", "两次密码不一致")
                return False
            self._editor_password = pwd
            content = self._editor.toPlainText()
            enc = vault_encrypt(content, pwd)
            with open(path, 'wb') as f:
                f.write(enc.encode())
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self._editor.toPlainText())
            self._editor_password = None
        self._editor_filepath = path
        self._editor_path_label.setText(os.path.basename(path))
        return True

    def _tool_update_editor_status(self):
        text = self._editor.toPlainText()
        words = len(text)
        self._editor_status.setText(f"字数: {words}")

    # ═══════ 密码保险箱方法 ═══════
    def _vault_unlock(self):
        pwd = self._vault_pwd_input.text()
        if not pwd:
            self._vault_lock_msg.setText("请输入主密码")
            return
        if not os.path.exists(VAULT_FILE):
            confirm, ok = QInputDialog.getText(self, "设置主密码", "首次使用，请再次输入确认：", QLineEdit.Password)
            if not ok or pwd != confirm:
                self._vault_lock_msg.setText("两次密码不一致")
                return
            self._vault_master_pwd = pwd
            self._vault_entries = []
            self._vault_save()
            self._vault_show_main()
        else:
            try:
                raw = open(VAULT_FILE, encoding='utf-8').read()
                data = json.loads(vault_decrypt(raw, pwd))
                self._vault_master_pwd = pwd
                self._vault_entries = data.get('entries', [])
                self._vault_show_main()
            except Exception:
                self._vault_lock_msg.setText("密码错误")
                self._vault_pwd_input.clear()

    def _vault_show_main(self):
        self._vault_lock_widget.hide()
        self._vault_main_widget.show()
        self._vault_pwd_input.clear()
        self._vault_lock_msg.setText("")
        self._vault_refresh()

    def _vault_lock(self):
        self._vault_master_pwd = None
        self._vault_entries = []
        self._vault_main_widget.hide()
        self._vault_lock_widget.show()
        self._vault_pwd_input.clear()

    def _vault_save(self):
        data = json.dumps({'entries': self._vault_entries}, ensure_ascii=False)
        enc = vault_encrypt(data, self._vault_master_pwd)
        os.makedirs(os.path.dirname(VAULT_FILE), exist_ok=True)
        with open(VAULT_FILE, 'w', encoding='utf-8') as f:
            f.write(enc)

    def _vault_add_entry(self):
        dlg = VaultEntryDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            entry = dlg.get_data()
            entry['id'] = secrets.token_hex(8)
            entry['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self._vault_entries.append(entry)
            self._vault_save()
            self._vault_refresh()

    def _vault_edit_entry(self):
        row = self._vault_table.currentRow()
        if row < 0:
            return
        idx = self._vault_table.item(row, 0).data(Qt.UserRole)
        entry = next((e for e in self._vault_entries if e.get('id') == idx), None)
        if not entry:
            return
        dlg = VaultEntryDialog(self, entry)
        if dlg.exec_() == QDialog.Accepted:
            entry.update(dlg.get_data())
            entry['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self._vault_save()
            self._vault_refresh()

    def _vault_delete(self, row):
        idx = self._vault_table.item(row, 0).data(Qt.UserRole)
        name = self._vault_table.item(row, 0).text()
        if QMessageBox.Yes == QMessageBox.question(self, "确认删除", f"删除「{name}」？"):
            self._vault_entries = [e for e in self._vault_entries if e.get('id') != idx]
            self._vault_save()
            self._vault_refresh()

    def _vault_context_menu(self, pos):
        row = self._vault_table.rowAt(pos.y())
        if row < 0:
            return
        idx = self._vault_table.item(row, 0).data(Qt.UserRole)
        entry = next((e for e in self._vault_entries if e.get('id') == idx), None)
        if not entry:
            return
        menu = QMenu(self)
        menu.addAction("复制账号", lambda: QApplication.clipboard().setText(entry.get('account', '')))
        menu.addAction("复制密码", lambda: QApplication.clipboard().setText(entry.get('password', '')))
        if entry.get('url'):
            menu.addAction("复制网址", lambda: QApplication.clipboard().setText(entry.get('url', '')))
        menu.addSeparator()
        menu.addAction("编辑", self._vault_edit_entry)
        menu.addAction("删除", lambda: self._vault_delete(row))
        menu.exec_(self._vault_table.viewport().mapToGlobal(pos))

    def _vault_refresh(self):
        keyword = self._vault_search.text().strip().lower()
        cat = self._vault_cat.currentText()
        filtered = [e for e in self._vault_entries
                    if (cat == "全部" or e.get('category') == cat)
                    and (not keyword or keyword in e.get('title', '').lower()
                         or keyword in e.get('account', '').lower())]
        self._vault_table.setRowCount(len(filtered))
        show_pwd = self._vault_show_pwd.isChecked()
        for i, e in enumerate(filtered):
            name_item = QTableWidgetItem(e.get('title', ''))
            name_item.setData(Qt.UserRole, e.get('id'))
            self._vault_table.setItem(i, 0, name_item)
            cat_item = QTableWidgetItem(e.get('category', ''))
            cat_item.setForeground(QColor(VAULT_CAT_COLORS.get(e.get('category', ''), '#718096')))
            self._vault_table.setItem(i, 1, cat_item)
            self._vault_table.setItem(i, 2, QTableWidgetItem(e.get('account', '')))
            pwd = e.get('password', '')
            self._vault_table.setItem(i, 3, QTableWidgetItem(pwd if show_pwd else '*' * len(pwd)))
            self._vault_table.setItem(i, 4, QTableWidgetItem(e.get('updated', '')))
        self._vault_count_lbl.setText(f"共 {len(self._vault_entries)} 条")

    def _vault_change_pwd(self):
        old, ok = QInputDialog.getText(self, "修改主密码", "当前密码：", QLineEdit.Password)
        if not ok or old != self._vault_master_pwd:
            QMessageBox.warning(self, "错误", "密码错误")
            return
        new, ok = QInputDialog.getText(self, "修改主密码", "新密码（至少4位）：", QLineEdit.Password)
        if not ok or len(new) < 4:
            QMessageBox.warning(self, "错误", "新密码至少4位")
            return
        confirm, ok = QInputDialog.getText(self, "修改主密码", "确认新密码：", QLineEdit.Password)
        if not ok or new != confirm:
            QMessageBox.warning(self, "错误", "两次不一致")
            return
        self._vault_master_pwd = new
        self._vault_save()
        QMessageBox.information(self, "成功", "主密码已修改")