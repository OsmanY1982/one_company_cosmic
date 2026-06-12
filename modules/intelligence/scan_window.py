"""
扫码工具 · NEURAL — 独立子窗口
二维码生成（输入文本 → 显示QR码 + 保存） + 解析（手动输入 / 图片解析 + 历史记录）
"""
import os
from io import BytesIO
from datetime import datetime
import traceback
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QTextEdit, QLineEdit,
    QWidget, QFrame, QMessageBox, QFileDialog,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
# 懒安装
from core.deps import ensure
_QRCODE_AVAILABLE = False
try:
    ensure("qrcode")
    import qrcode
    _QRCODE_AVAILABLE = True
except Exception:
    import traceback; traceback.print_exc()

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
    QLineEdit, QTextEdit {
        background: rgba(12,6,22,230); color: #ccbbdd;
        border: 1px solid rgba(170,80,255,35); border-radius: 6px;
        padding: 6px 10px; font-size: 12px;
    }
    QLineEdit:focus { border: 1px solid rgba(180,100,255,180); }
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


class ScanWindow(QDialog):
    """扫码工具 · NEURAL"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("扫码工具 · NEURAL")
        self.setMinimumSize(650, 620)
        self.setStyleSheet("background: rgba(10,5,20,240);")
        self._qr_pixmap = None
        self._build_ui()

    def _build_ui(self):
        l = QVBoxLayout(self)
        l.setSpacing(10)
        l.setContentsMargins(16, 12, 16, 12)

        info = QLabel("二维码工具 — 生成 / 解析")
        info.setStyleSheet("color: #776699; font-size: 12px; background: transparent;")
        l.addWidget(info)

        # ── 生成区 ──
        gen_frame = QFrame()
        gen_frame.setStyleSheet("background: rgba(12,6,22,200); border: 1px solid rgba(170,80,255,25); border-radius: 10px; padding: 12px;")
        gen_l = QVBoxLayout(gen_frame)
        gen_l.setSpacing(8)
        gen_title = QLabel("生成二维码")
        gen_title.setStyleSheet("color: #aa88dd; font-size: 13px; font-weight: 700; background:transparent;")
        gen_l.addWidget(gen_title)

        gen_row = QHBoxLayout()
        self._qr_input = QLineEdit()
        self._qr_input.setPlaceholderText("输入文本 / 链接，回车生成...")
        self._qr_input.setStyleSheet(INPUT_STYLE)
        self._qr_input.returnPressed.connect(self._qr_generate)
        gen_row.addWidget(self._qr_input, 1)
        btn_gen = QPushButton("生成")
        btn_gen.setStyleSheet(BTN_PRIMARY)
        btn_gen.clicked.connect(self._qr_generate)
        gen_row.addWidget(btn_gen)
        btn_save = QPushButton("保存图片")
        btn_save.setStyleSheet(BTN_PRIMARY)
        btn_save.clicked.connect(self._qr_save)
        gen_row.addWidget(btn_save)
        gen_l.addLayout(gen_row)

        self._qr_display = QLabel()
        self._qr_display.setAlignment(Qt.AlignCenter)
        self._qr_display.setFixedSize(220, 220)
        self._qr_display.setStyleSheet("border: 1px dashed rgba(170,80,255,40); border-radius: 8px; background: white;")
        gen_l.addWidget(self._qr_display, alignment=Qt.AlignCenter)
        l.addWidget(gen_frame)

        # ── 解析区 ──
        parse_frame = QFrame()
        parse_frame.setStyleSheet("background: rgba(12,6,22,200); border: 1px solid rgba(170,80,255,25); border-radius: 10px; padding: 12px;")
        parse_l = QVBoxLayout(parse_frame)
        parse_l.setSpacing(8)
        parse_title = QLabel("解析二维码")
        parse_title.setStyleSheet("color: #aa88dd; font-size: 13px; font-weight: 700; background:transparent;")
        parse_l.addWidget(parse_title)

        pr = QHBoxLayout()
        self._qr_decode_input = QLineEdit()
        self._qr_decode_input.setPlaceholderText("扫码枪输入或粘贴条码 → 回车解析")
        self._qr_decode_input.setStyleSheet(INPUT_STYLE)
        self._qr_decode_input.returnPressed.connect(self._qr_decode_text)
        pr.addWidget(self._qr_decode_input, 1)
        btn_file = QPushButton("打开图片")
        btn_file.setStyleSheet(BTN_PRIMARY)
        btn_file.clicked.connect(self._qr_decode_image)
        pr.addWidget(btn_file)
        parse_l.addLayout(pr)

        self._qr_result = QTextEdit()
        self._qr_result.setReadOnly(True)
        self._qr_result.setMaximumHeight(80)
        self._qr_result.setStyleSheet(INPUT_STYLE)
        parse_l.addWidget(self._qr_result)

        hist_label = QLabel("解析历史")
        hist_label.setStyleSheet("color: #776699; font-size: 11px; background:transparent;")
        parse_l.addWidget(hist_label)
        self._qr_history = QTableWidget()
        self._qr_history.setColumnCount(3)
        self._qr_history.setHorizontalHeaderLabels(["时间", "内容", "来源"])
        self._qr_history.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._qr_history.setStyleSheet(TABLE_STYLE)
        self._qr_history.setMaximumHeight(160)
        self._qr_history.setEditTriggers(QTableWidget.NoEditTriggers)
        parse_l.addWidget(self._qr_history)

        clr_row = QHBoxLayout()
        clear = QPushButton("清空历史")
        clear.setStyleSheet(BTN_DANGER)
        clear.clicked.connect(lambda: self._qr_history.setRowCount(0))
        clr_row.addStretch()
        clr_row.addWidget(clear)
        parse_l.addLayout(clr_row)

        l.addWidget(parse_frame)

    def _qr_generate(self):
        text = self._qr_input.text().strip()
        if not text:
            return
        if not _QRCODE_AVAILABLE:
            QMessageBox.warning(self, "模块缺失", "二维码生成需要 qrcode 模块，请执行: pip install qrcode")
            return
        try:
            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#aa55ff", back_color="white")
            buf = BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(buf.read())
            scaled = pixmap.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._qr_pixmap = scaled
            self._qr_display.setPixmap(scaled)
        except Exception as e:
            QMessageBox.warning(self, "生成失败", str(e))

    def _qr_save(self):
        if self._qr_pixmap is None:
            QMessageBox.information(self, "提示", "请先生成二维码")
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存二维码", "qrcode.png", "PNG 图片 (*.png)")
        if path:
            self._qr_pixmap.save(path, 'PNG')

    def _qr_decode_text(self):
        text = self._qr_decode_input.text().strip()
        if not text:
            return
        self._qr_result.setText(f"[手动输入] {text}")
        self._qr_add_history(text, "手动输入")
        self._qr_decode_input.clear()

    def _qr_decode_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择二维码图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*)")
        if not path:
            return
        try:
            from PIL import Image
            from pyzbar.pyzbar import decode as zb_decode
            img = Image.open(path)
            results = zb_decode(img)
            if results:
                data = results[0].data.decode('utf-8', errors='replace')
                self._qr_result.setText(f"[图片解析] {data}")
                self._qr_add_history(data, os.path.basename(path))
            else:
                self._qr_result.setText("[图片解析] 未检测到二维码")
        except ImportError:
            self._qr_result.setText("[图片解析] 需要安装 pyzbar 和 Pillow 库：pip install pyzbar Pillow")
        except Exception as e:
            self._qr_result.setText(f"[图片解析] 错误: {e}")

    def _qr_add_history(self, content, source):
        row = self._qr_history.rowCount()
        self._qr_history.insertRow(0)
        self._qr_history.setItem(0, 0, QTableWidgetItem(datetime.now().strftime('%H:%M:%S')))
        self._qr_history.setItem(0, 1, QTableWidgetItem(content[:80]))
        self._qr_history.setItem(0, 2, QTableWidgetItem(source))