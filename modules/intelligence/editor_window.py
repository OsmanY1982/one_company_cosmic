"""
文本编辑器 · NEURAL — 独立子窗口
从 tools_window.py 拆分，提供加密/明文文本编辑能力
"""
import os, hashlib, base64
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QFileDialog, QInputDialog, QMessageBox, QLineEdit,
)
from PyQt5.QtCore import Qt

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

# ═══════ QSS 主题 ═══════
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


# ═══════ 加解密函数（自包含副本） ═══════
def _derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)

def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

def vault_encrypt(plaintext: str, password: str) -> str:
    salt = os.urandom(16)
    key = _derive_key(password, salt)
    enc = _xor(plaintext.encode('utf-8'), key)
    return base64.b64encode(salt + enc).decode()

def vault_decrypt(ciphertext: str, password: str) -> str:
    payload = base64.b64decode(ciphertext.encode())
    salt = payload[:16]
    enc = payload[16:]
    key = _derive_key(password, salt)
    return _xor(enc, key).decode('utf-8')


# ═══════ 文本编辑器窗口 ═══════
class EditorWindow(QDialog):
    """文本编辑器 · NEURAL"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("文本编辑器 · NEURAL")
        self.setMinimumSize(700, 500)
        self.setStyleSheet("background: rgba(10,5,20,240);")
        self._editor_filepath = None
        self._editor_password = None
        self._build_ui()

    def _build_ui(self):
        l = QVBoxLayout(self)
        l.setSpacing(6)
        l.setContentsMargins(10, 10, 10, 10)

        # ── 工具栏 ──
        tb = QHBoxLayout()
        btn_open = QPushButton("打开")
        btn_open.setStyleSheet(BTN_PRIMARY)
        btn_open.clicked.connect(self._open)
        tb.addWidget(btn_open)

        btn_save = QPushButton("保存")
        btn_save.setStyleSheet(BTN_PRIMARY)
        btn_save.clicked.connect(self._save)
        tb.addWidget(btn_save)

        btn_enc = QPushButton("加密保存")
        btn_enc.setStyleSheet(BTN_PRIMARY)
        btn_enc.clicked.connect(self._save_enc)
        tb.addWidget(btn_enc)

        self._path_label = QLabel("未打开文件")
        self._path_label.setStyleSheet("color: #8877aa; font-size: 11px; background: transparent;")
        tb.addWidget(self._path_label)
        tb.addStretch()
        l.addLayout(tb)

        # ── 编辑区 ──
        self._editor = QTextEdit()
        self._editor.setStyleSheet("""
            QTextEdit {
                background: rgba(8,4,16,230); color: #ccbbdd;
                border: 1px solid rgba(170,80,255,35); border-radius: 10px;
                padding: 12px; font-size: 13px; line-height: 1.6;
            }
        """)
        self._editor.textChanged.connect(self._update_status)
        l.addWidget(self._editor, 1)

        # ── 状态栏 ──
        sb = QHBoxLayout()
        self._status = QLabel("字数: 0")
        self._status.setStyleSheet("color: #8877aa; font-size: 11px; background: transparent;")
        sb.addWidget(self._status)
        sb.addStretch()
        btn_clear = QPushButton("清空")
        btn_clear.setStyleSheet(BTN_DANGER)
        btn_clear.clicked.connect(lambda: self._editor.clear())
        sb.addWidget(btn_clear)
        l.addLayout(sb)

    # ═══════ 文件操作 ═══════
    def _open(self):
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
            self._path_label.setText(os.path.basename(path))
            self._update_status()
        except Exception as e:
            QMessageBox.warning(self, "打开失败", str(e))

    def _save(self):
        if not self._editor_filepath:
            return self._save_as()
        try:
            content = self._editor.toPlainText()
            if self._editor_password:
                enc = vault_encrypt(content, self._editor_password)
                with open(self._editor_filepath, 'wb') as f:
                    f.write(enc.encode())
            else:
                with open(self._editor_filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            self._path_label.setText(os.path.basename(self._editor_filepath))
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))

    def _save_enc(self):
        self._save_as(encrypted=True)

    def _save_as(self, encrypted=False):
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
        self._path_label.setText(os.path.basename(path))
        return True

    def _update_status(self):
        text = self._editor.toPlainText()
        words = len(text)
        self._status.setText(f"字数: {words}")
