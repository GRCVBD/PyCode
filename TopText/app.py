"""TopTop 应用管理层：QApplication、托盘、控件生命周期。"""
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QMenu, QStyle, QSystemTrayIcon)

from topwidget import TopWidget

def resource_path(relative_path: str) -> Path:
    """获取资源文件绝对路径（兼容 PyInstaller _MEIPASS）。不保证文件存在。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative_path

class App:
    """TopTop应用控制器"""

    def __init__(self) -> None:
        self.app = QApplication(sys.argv)
        self._app_icon = self._load_icon()
        self.app.setWindowIcon(self._app_icon)
        self._widgets: list[TopWidget] = []
        self._init_tray()
        self.add_widget()

    def _load_icon(self) -> QIcon:
        """加载应用图标，缺失时回退到系统标准图标。"""
        icon_path = resource_path("res/app.ico")
        if icon_path.exists():
            return QIcon(str(icon_path))
        return self.app.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)

    def _init_tray(self) -> None:
        """初始化系统托盘与右键菜单。"""
        self._tray_menu = QMenu()
        self._tray_menu.addAction("退出").triggered.connect(self._quit_all)
        self._tray = QSystemTrayIcon()
        self._tray.setIcon(self._app_icon)
        self._tray.setToolTip("TopTop")
        self._tray.setContextMenu(self._tray_menu)
        self._tray.show()

    def add_widget(self, text: str = "编辑内容") -> TopWidget:
        """新增并显示一个置顶控件。"""
        widget = TopWidget(text=text)
        widget.add_widget_requested.connect(self.add_widget)
        widget.widget_closed.connect(self._on_widget_closed)
        self._widgets.append(widget)
        widget.show()
        return widget

    def _on_widget_closed(self, widget: TopWidget) -> None:
        if widget in self._widgets:
            self._widgets.remove(widget)
        if not self._widgets:
            self.app.quit()

    def _quit_all(self) -> None:
        """关闭所有控件并退出。"""
        self._tray.hide()
        for w in list(self._widgets):
            w.close()
        self.app.quit()

    def run(self) -> int:
        return self.app.exec()
