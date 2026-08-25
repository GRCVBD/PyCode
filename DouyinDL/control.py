"""应用控制器：协调 UI 与解析/下载线程。"""

import os

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox

from window import MainWindow, SettingsDialog
from parse import DouyinParser
from download import VideoDownloader
from utils import set_browser_path


class AppController(QObject):
    """连接 UI 与后台线程，处理用户交互。"""

    def __init__(self) -> None:
        super().__init__()
        self.window = MainWindow()
        self.parser = DouyinParser()
        self.downloader = VideoDownloader()
        self.current_info: dict | None = None
        self._connect_signals()

    def _connect_signals(self) -> None:
        self.window.parse_btn.clicked.connect(self.start_parse)
        self.window.download_btn.clicked.connect(self.start_download)
        self.window.cancel_btn.clicked.connect(self.cancel_task)
        self.window.config_label.clicked.connect(self.open_settings)
        self.window.closeEvent = self.handle_close_event

        self.parser.log.connect(self.window.append_log)
        self.parser.parse_finished.connect(self.on_parse_finished)
        self.parser.error.connect(self.on_parse_error)

        self.downloader.log.connect(self.window.append_log)
        self.downloader.progress.connect(self.window.set_progress)
        self.downloader.download_finished.connect(self.on_download_finished)
        self.downloader.error.connect(self.on_download_error)

    def show_window(self) -> None:
        self.window.show()

    def start_parse(self) -> None:
        if self.parser.isRunning() or self.downloader.isRunning():
            return
        url = self.window.url_input.text().strip()
        if not url:
            QMessageBox.warning(self.window, '提示', '请输入视频链接！')
            return

        self.window.set_parsing_state(True)
        self.window.append_log('[*] 开始解析...')
        self.parser.setup(url)
        self.parser.start()

    def on_parse_finished(self, info: dict) -> None:
        self.current_info = info
        self.window.show_parse_result(info)
        self.window.download_btn.setEnabled(True)
        self.window.parse_btn.setEnabled(True)
        self.window.append_log('[+] 解析完成，可以开始下载。')

    def on_parse_error(self, err_msg: str) -> None:
        self.window.append_log(f'[-] 错误: {err_msg}')
        self.window.reset_ui_state()

    def start_download(self) -> None:
        if self.parser.isRunning() or self.downloader.isRunning():
            return
        if not self.current_info:
            QMessageBox.warning(self.window, '提示', '请先解析视频！')
            return

        save_dir = self.window.get_save_dir()
        if not save_dir or not os.path.isdir(save_dir):
            QMessageBox.warning(self.window, '提示', '保存路径无效，请在“设置”中配置！')
            return

        self.window.set_downloading_state(True)
        self.window.append_log(f'[*] 保存目录: {save_dir}')
        self.window.append_log('[*] 开始下载任务...')
        self.downloader.setup(self.current_info, save_dir)
        self.downloader.start()

    def on_download_finished(self, save_path: str) -> None:
        self.window.append_log(f'[+] 文件已保存至: {save_path}')
        self.window.reset_ui_state()
        QMessageBox.information(self.window, '成功', f'下载完成！\n路径: {save_path}')

    def on_download_error(self, err_msg: str) -> None:
        self.window.append_log(f'[-] 错误: {err_msg}')
        self.window.reset_ui_state()

    def cancel_task(self) -> None:
        if self.parser.isRunning():
            self.parser.cancel()
        if self.downloader.isRunning():
            self.downloader.cancel()

    def open_settings(self) -> None:
        dialog = SettingsDialog(
            browser_path=self.window.get_browser_path(),
            save_dir=self.window.get_save_dir(),
            parent=self.window,
        )
        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            return

        values = dialog.values()
        self._apply_browser_path(values['browser_path'])
        self._apply_save_dir(values['save_dir'])

    def _apply_browser_path(self, browser_path: str) -> None:
        if not browser_path or browser_path == self.window.get_browser_path():
            return
        if set_browser_path(browser_path):
            self.window.set_browser_path(browser_path)
            self.window.append_log(f'[*] 浏览器路径已更新为: {browser_path}')
        else:
            QMessageBox.warning(self.window, '失败', '浏览器路径配置失败！')

    def _apply_save_dir(self, save_dir: str) -> None:
        if not save_dir:
            return
        if os.path.isdir(save_dir):
            self.window.set_save_dir(save_dir)
            self.window.append_log(f'[*] 保存路径已更新为: {save_dir}')
        else:
            QMessageBox.warning(self.window, '提示', '保存路径无效，未更新！')

    def handle_close_event(self, event) -> None:
        if self.parser.isRunning() or self.downloader.isRunning():
            reply = QMessageBox.question(
                self.window, '确认退出', '有任务正在执行，确定要退出吗？',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self.parser.cancel()
            self.downloader.cancel()
            self.parser.wait(2000)
            self.downloader.wait(2000)
        self.parser.close()
        event.accept()
