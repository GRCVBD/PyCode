import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QAction, QMouseEvent, QContextMenuEvent, QPaintEvent, QColor, QPalette, QFont, QIcon
from PySide6.QtWidgets import QLabel, QWidget, QMenu, QColorDialog, QSystemTrayIcon, QFontDialog
from PySide6.QtWidgets import QApplication, QHBoxLayout, QFrame
import tool

class MonitorWindow(QWidget):
    """监控器窗口类，包含CPU占用率、温度 | GPU显存占用率、温度 | 内存占用率"""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFont(QFont('Microsoft YaHei', 12))
        self.trayicon = QSystemTrayIcon(self)
        self._bg_alpha = 191
        self._bg_color = QColor(15, 23, 42, self._bg_alpha)
        self._fg_color = QColor(255, 255, 255)
        self._drag_pos = None

        self.cpu_name = QLabel("CPU")
        self.cpu_load_value = QLabel("0.0")
        self.cpu_load_unit = QLabel("%")
        self.cpu_temp_value = QLabel("0.0")
        self.cpu_temp_unit = QLabel("℃")

        self.gpu_name = QLabel("GPU")
        self.gpu_load_value = QLabel("0.0")
        self.gpu_load_unit = QLabel("%")
        self.gpu_temp_value = QLabel("0.0")
        self.gpu_temp_unit = QLabel("℃")

        self.ram_name = QLabel("RAM")
        self.ram_load_value = QLabel("0.0")
        self.ram_load_unit = QLabel("%")

        self.sepline1 = QFrame()
        self.sepline2 = QFrame()

        self.setup_widget()
        self.setup_layout()
        self.set_fg_color(self._fg_color)
        self.setup_trayicon()

    def setup_layout(self):
        """配置布局"""
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 1, 2, 1)
        layout.setSpacing(5)
        widgets = [self.cpu_name, self.cpu_load_value, self.cpu_load_unit, self.cpu_temp_value, self.cpu_temp_unit, self.sepline1,
                   self.gpu_name, self.gpu_load_value, self.gpu_load_unit, self.gpu_temp_value, self.gpu_temp_unit, self.sepline2,
                   self.ram_name, self.ram_load_value, self.ram_load_unit]
        for widget in widgets:
            layout.addWidget(widget)
        self.setLayout(layout)

    def setup_widget(self):
        """配置控件"""
        labels = [self.cpu_name, self.cpu_load_value, self.cpu_load_unit, self.cpu_temp_value, self.cpu_temp_unit,
                  self.gpu_name, self.gpu_load_value, self.gpu_load_unit, self.gpu_temp_value, self.gpu_temp_unit,
                  self.ram_name, self.ram_load_value, self.ram_load_unit]
        for lb in labels:
            lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        seplines = [self.sepline1, self.sepline2]
        for sl in seplines:
            sl.setFrameShape(QFrame.Shape.VLine)

    def setup_trayicon(self):
        """初始化托盘图标"""
        self.trayicon.setIcon(QIcon(tool.get_respath("res/app.ico")))
        self.trayicon.setToolTip("温度监控")
        tray_menu = QMenu(self)
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.quit_run)
        tray_menu.addAction(exit_action)
        self.trayicon.setContextMenu(tray_menu)
        self.trayicon.show()

    def set_bg_alpha(self, alpha):
        """设置背景透明度"""
        self._bg_alpha = max(0, min(255, int(alpha)))
        self._bg_color.setAlpha(self._bg_alpha)
        self.update()

    def quit_run(self):
        """退出应用"""
        self.hide()
        QApplication.quit()

    def paintEvent(self, event: QPaintEvent):
        """重写窗体重绘事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self._bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 4.0, 4.0)

    def contextMenuEvent(self, event: QContextMenuEvent):
        """重写右键菜单事件"""
        menu = QMenu(self)
        font_action = QAction("字体")
        font_action.triggered.connect(self.set_font)
        menu.addAction(font_action)
        bgcolor_action = QAction("背景颜色", self)
        bgcolor_action.triggered.connect(self.set_bg_color)
        menu.addAction(bgcolor_action)
        fgcolor_action = QAction("字体颜色", self)
        fgcolor_action.triggered.connect(self.select_color)
        menu.addAction(fgcolor_action)
        opacity_menu = menu.addMenu("透明度")
        actions_data = [("0%", 255), ("25%", 191), ("50%", 128), ("75%", 64), ("100%", 0)]
        for text, alpha in actions_data:
            action = QAction(text, self)
            action.triggered.connect(lambda checked, a=alpha: self.set_bg_alpha(a))
            opacity_menu.addAction(action)
        menu.addSeparator()
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.quit_run)
        menu.addAction(exit_action)
        menu.exec(event.globalPos())

    def set_font(self):
        b, font = QFontDialog.getFont(self.font(), self, "选择字体")
        if b:
            self.setFont(font)
            self.adjustSize()

    def set_bg_color(self):
        """设置背景色"""
        color = QColorDialog.getColor(self._bg_color, parent=self, title="设置背景色")
        if color:
            self._bg_color.setRgb(color.red(), color.green(), color.blue())
            self._bg_color.setAlpha(self._bg_alpha)
            self.update()

    def select_color(self):
        """设置前景色"""
        color = QColorDialog.getColor(self._fg_color, parent=self, title="设置前景色")
        if color:
            self._fg_color.setRgb(color.red(), color.green(), color.blue())
            self.set_fg_color(self._fg_color)

    def set_fg_color(self, color: QColor):
        """设置前景色"""
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.WindowText, color)
        widgets = [self.cpu_name, self.cpu_load_value, self.cpu_load_unit, self.cpu_temp_value, self.cpu_temp_unit, self.sepline1,
                   self.gpu_name, self.gpu_load_value, self.gpu_load_unit, self.gpu_temp_value, self.gpu_temp_unit, self.sepline2,
                   self.ram_name, self.ram_load_value, self.ram_load_unit]
        for widget in widgets:
            widget.setPalette(palette)

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件"""
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            mouse_pos = event.globalPosition().toPoint()
            new_pos = mouse_pos - self._drag_pos
            screen = QApplication.screenAt(mouse_pos)
            if not screen:
                screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            new_pos.setX(max(screen_rect.left(), min(new_pos.x(), screen_rect.right() - self.width())))
            new_pos.setY(max(screen_rect.top(), min(new_pos.y(), screen_rect.bottom() - self.height())))
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        self._drag_pos = None
        event.accept()

    def update_data(self, monit_data: dict):
        """更新数据"""
        self.cpu_load_value.setText(f"{monit_data.get("CPULoad", "0.0"):.1f}")
        self.cpu_temp_value.setText(f"{monit_data.get("CPUTemp", "0.0"):.1f}")
        self.gpu_load_value.setText(f"{monit_data.get("GPULoad", "0.0"):.1f}")
        self.gpu_temp_value.setText(f"{monit_data.get("GPUTemp", "0.0"):.1f}")
        self.ram_load_value.setText(f"{monit_data.get("RAMLoad", "0.0"):.1f}")
