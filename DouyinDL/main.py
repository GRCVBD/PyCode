"""程序入口：创建应用与控制器并启动事件循环。"""

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from utils import get_resource_path
from control import AppController


def main() -> None:
    """创建 Qt 应用、初始化控制器并进入事件循环。"""
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(get_resource_path('res/app.ico')))
    controller = AppController()
    controller.show_window()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
