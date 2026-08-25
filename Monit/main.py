"""程序入口：检测管理员权限并按需提升"""
import ctypes
import sys
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox
from monitor import MonitorThread
from window import MonitorWindow
from tool import get_respath

class MonitorApp:
    """主应用控制类"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setWindowIcon(QIcon(get_respath("res/app.ico")))
        self.app.setQuitOnLastWindowClosed(False)
        self.window = MonitorWindow()
        self.worker = MonitorThread(get_respath("res/ohwl.dll"))
        self.worker.reads.connect(self.window.update_data)
        self.app.aboutToQuit.connect(self.worker.stop)

    @staticmethod
    def is_admin() -> bool:
        """判断当前进程是否拥有管理员权限"""
        if sys.platform != "win32":
            return False
        try:
            is_user_admin = getattr(ctypes.windll.shell32, "IsUserAnAdmin", None)
            return is_user_admin() != 0
        except (AttributeError, OSError):
            return False

    def run(self):
        """启动主程序"""
        if not self.is_admin():
            QMessageBox.warning(None, "警告", "请以管理员权限运行！")
            return 0
        self.window.show()
        self.worker.start()  # 启动后台监控线程
        return self.app.exec()

if __name__ == "__main__":
    app = MonitorApp()
    sys.exit(app.run())
