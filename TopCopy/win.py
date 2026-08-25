import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QAction, QCursor, QIcon
from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QLineEdit, QMenu, QLabel

from tool import get_resource_path


class CopyTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(200)
        self.resize(400, 28)

        self.copy_label = QLabel("Copy")
        self.copy_label.setObjectName("copy_label")
        self.input_edit = QLineEdit()
        self.input_edit.setObjectName("input_edit")
        self.label = QLabel(self)
        self.label.setObjectName("label")

        self.copy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.copy_label.setMinimumHeight(28)
        self.copy_label.setMinimumWidth(50)
        self.input_edit.setPlaceholderText("输入要复制的内容...")
        self.input_edit.setMinimumHeight(28)
        self.input_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.label.setFixedWidth(8)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.copy_label)
        layout.addWidget(self.input_edit)
        layout.addWidget(self.label)

        self.drag_pos = None
        self.is_dragging = False
        self.is_resizing = False
        self.resize_start_pos = None
        self.resize_start_rect = None
        self.input_edit.returnPressed.connect(self.copy_text)
        self.load_style("style.qss")

    def load_style(self, style: str):
        """
        加载样式
        :param style:样式文件相对路径
        """
        qss_file = get_resource_path(style)
        with open(qss_file, "r", encoding='utf-8') as fs:
            self.setStyleSheet(fs.read())

    def mousePressEvent(self, event):
        """
        重写鼠标按下事件
        :param event:鼠标事件
        """
        if event.buttons() == Qt.MouseButton.LeftButton:
            pos = event.position()
            if (self.width() - 8) < pos.x() < self.width():
                self.is_resizing = True
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_rect = self.geometry()
            else:
                self.drag_pos = event.globalPosition().toPoint()
                self.is_dragging = True

    def mouseMoveEvent(self, event):
        """
        重写鼠标移动事件
        :param event:鼠标事件
        """
        if event.buttons() == Qt.MouseButton.LeftButton:
            if self.is_resizing:
                delta_x = event.globalPosition().toPoint().x() - self.resize_start_pos.x()
                new_width = max(200, self.resize_start_rect.width() + delta_x)
                self.setGeometry(self.resize_start_rect.x(), self.resize_start_rect.y(), new_width, self.resize_start_rect.height())
            elif self.is_dragging and self.drag_pos is not None:
                delta = event.globalPosition().toPoint() - self.drag_pos
                new_pos = self.pos() + delta
                screen = QGuiApplication.primaryScreen().availableGeometry()
                new_pos.setX(max(screen.x(), min(new_pos.x(), screen.right() - self.width())))
                new_pos.setY(max(screen.y(), min(new_pos.y(), screen.bottom() - self.height())))
                self.move(new_pos)
                self.drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        """
        重写鼠标释放事件
        :param event:鼠标事件
        """
        self.is_dragging = False
        self.is_resizing = False
        self.drag_pos = None
        self.resize_start_pos = None
        self.resize_start_rect = None
        self.unsetCursor()

    def enterEvent(self, event):
        """
        重写鼠标进入事件
        :param event:鼠标进入事件
        """
        if self.is_resizing or self.is_dragging:
            return
        pos = self.mapFromGlobal(QCursor.pos())
        if (self.width() - 8) < pos.x() < self.width():
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif pos.x() < self.copy_label.width():
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.unsetCursor()

    def contextMenuEvent(self, event):
        """
        重写自定义菜单事件
        :param event:自定义菜单事件
        """
        menu = QMenu(self)
        copy_action = QAction("复制", self)
        copy_action.triggered.connect(self.copy_text)
        copy_action.setEnabled(bool(self.input_edit.text()))
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.app_quit)
        menu.addAction(copy_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        menu.exec(event.globalPos())

    def copy_text(self):
        """
        复制文本
        """
        text = self.input_edit.text()
        if text:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(text)
            self.input_edit.selectAll()

    def app_quit(self):
        self.close()
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(get_resource_path("app.ico")))
    window = CopyTool()
    window.show()
    sys.exit(app.exec())
