"""主窗口视图：构建界面布局与日志展示，不包含业务逻辑。"""

import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QProgressBar,
                               QTextEdit, QGroupBox, QDialog, QFormLayout, QFileDialog, QLabel)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QTextCharFormat, QIcon

from utils import get_resource_path

# 日志前缀 → 文字颜色（在深色日志背景上清晰可读）
_LOG_COLORS = {
    '[*]': '#74b9ff',  # 信息 - 亮蓝
    '[+]': '#55efc4',  # 成功 - 青绿
    '[-]': '#ff7675',  # 错误 - 亮红
    '[!]': '#ffeaa7',  # 警告 - 亮黄
}
# 无前缀日志的默认颜色
_DEFAULT_LOG_COLOR = '#dfe6e9'

class ClickableLabel(QLabel):
    """可点击的 QLabel。"""

    clicked = Signal()

    def __init__(self, text: str = '', parent=None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()
        super().mousePressEvent(event)

class MainWindow(QMainWindow):
    """应用主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("抖音视频解析下载器")
        self.setWindowIcon(QIcon(get_resource_path('res/抖音.png')))
        self._init_ui()
        self.resize(750, 550)
        self._save_dir = os.path.expanduser('~') + r'\Videos\抖音'
        self._browser_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
        self._init_style()

    def _init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        link_group = QGroupBox("视频链接")
        link_layout = QHBoxLayout(link_group)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入抖音视频链接")
        self.parse_btn = QPushButton("解析")
        link_layout.addWidget(self.url_input)
        link_layout.addWidget(self.parse_btn)
        main_layout.addWidget(link_group)

        download_layout = QHBoxLayout()
        self.download_btn = QPushButton("下载")
        self.download_btn.setObjectName("download_btn")
        self.download_btn.setEnabled(False)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.setEnabled(False)
        self.config_label = ClickableLabel("配置")
        self.config_label.setObjectName("config_label")

        download_layout.addWidget(self.download_btn)
        download_layout.addWidget(self.cancel_btn)
        download_layout.addStretch()
        download_layout.addWidget(self.config_label)
        main_layout.addLayout(download_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        main_layout.addWidget(self.log_text)

    def _init_style(self) -> None:
        qss_path = get_resource_path('res/theme.qss')
        if os.path.exists(qss_path):
            with open(qss_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())

    def append_log(self, text: str) -> None:
        """按前缀着色输出日志。"""
        color_hex = _LOG_COLORS.get(text[:3], _DEFAULT_LOG_COLOR)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color_hex))
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(f'{text}\n', fmt)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum())

    def show_parse_result(self, info: dict) -> None:
        desc = info['desc'] if info['desc'] else "无描述"
        self.append_log('[+] 解析结果:')
        self.append_log(f'    视频 ID  : {info["video_id"]}')
        self.append_log(f'    视频名称 : {desc}')
        self.append_log(f'    播放地址 : {info["playaddr"]}')

    def set_parsing_state(self, is_parsing: bool) -> None:
        self.progress_bar.setValue(0)
        self.download_btn.setEnabled(not is_parsing)
        self.parse_btn.setEnabled(not is_parsing)
        self.cancel_btn.setEnabled(is_parsing)

    def set_downloading_state(self, is_downloading: bool) -> None:
        self.progress_bar.setValue(0)
        self.download_btn.setEnabled(not is_downloading)
        self.parse_btn.setEnabled(not is_downloading)
        self.cancel_btn.setEnabled(is_downloading)

    def reset_ui_state(self) -> None:
        self.parse_btn.setEnabled(True)
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

    def set_progress(self, value: int) -> None:
        self.progress_bar.setValue(value)

    def get_save_dir(self) -> str:
        return self._save_dir

    def set_save_dir(self, path: str) -> None:
        self._save_dir = path

    def get_browser_path(self) -> str:
        return self._browser_path

    def set_browser_path(self, path: str) -> None:
        self._browser_path = path

class SettingsDialog(QDialog):
    """配置对话框。"""

    def __init__(self, browser_path: str, save_dir: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle('设置')
        self.resize(600, 120)
        self._browser_path = browser_path
        self._save_dir = save_dir
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.browser_path_input = QLineEdit(self._browser_path)
        self.browser_path_input.setReadOnly(True)
        self.browser_path_input.setPlaceholderText('您的浏览器')
        browser_row = QHBoxLayout()
        browser_row.addWidget(self.browser_path_input)
        browser_btn = QPushButton('选择')
        browser_btn.clicked.connect(self._choose_browser)
        browser_row.addWidget(browser_btn)
        form.addRow('浏览器路径:', browser_row)

        self.save_dir_input = QLineEdit(self._save_dir)
        save_row = QHBoxLayout()
        save_row.addWidget(self.save_dir_input)
        save_btn = QPushButton('选择')
        save_btn.clicked.connect(self._choose_dir)
        save_row.addWidget(save_btn)
        form.addRow('保 存 路 径:', save_row)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton('确定')
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _choose_browser(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择浏览器可执行文件', '', '可执行文件 (*.exe);;所有文件 (*)'
        )
        if file_path:
            self.browser_path_input.setText(file_path)

    def _choose_dir(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(self, '选择保存目录', self._save_dir)
        if dir_path:
            self.save_dir_input.setText(dir_path)

    def values(self) -> dict:
        return {
            'browser_path': self.browser_path_input.text().strip(),
            'save_dir': self.save_dir_input.text().strip(),
        }
