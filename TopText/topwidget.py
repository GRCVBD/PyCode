"""TopTop 置顶显示控件。

无边框、置顶、背景透明的 QLabel 子类，支持拖动、双击编辑、右键菜单。
纵向显示为字符堆叠（每字一行）。
"""
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import (QColor, QFont, QKeyEvent, QMouseEvent)
from PySide6.QtWidgets import (QApplication, QColorDialog, QFontDialog, QLabel, QLineEdit, QMenu, QWidget)

# 默认样式：黑体 24pt 粗体，白色
DEFAULT_FONT_FAMILY = "SimHei"
DEFAULT_FONT_SIZE = 20
DEFAULT_COLOR = QColor(255, 255, 255)
# 文字与控件边界的留白
PADDING = 12

class TopWidget(QLabel):
    """置顶显示控件"""
    add_widget_requested = Signal()
    widget_closed = Signal(object)

    def __init__(self, text: str = "编辑内容", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self._text: str = text
        self._font: QFont = QFont(DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE, QFont.Weight.Bold)
        self._fill_color: QColor = QColor(DEFAULT_COLOR)
        self._vertical: bool = False
        self._editing: bool = False
        self._dragging: bool = False
        self._drag_offset: QPoint = QPoint()
        self._edit = QLineEdit(self)
        self._edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._edit.setFont(self._font)
        self._apply_edit_style()
        self._edit.hide()
        self._edit.editingFinished.connect(self._commit_edit)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.setFont(self._font)
        self._apply_display_style()
        self.move(50, 50)
        self._update_size()

    def _display_text(self) -> str:
        """返回显示文本（纵向模式按字符换行）。"""
        if self._vertical and self._text:
            return "\n".join(self._text)
        return self._text

    def _refresh_display(self) -> None:
        """刷新显示文本与字体。"""
        self.setFont(self._font)
        self.setText(self._display_text())

    def _apply_display_style(self) -> None:
        """同步文字颜色与透明背景。限定选择器避免子菜单继承透明背景。"""
        self.setStyleSheet(f"QLabel {{ color: {self._fill_color.name()}; background: transparent; }}")

    def _update_size(self) -> None:
        """根据字体和文本计算并设置控件尺寸。"""
        self._refresh_display()
        hint = self.sizeHint()
        w = hint.width() + PADDING * 2
        h = hint.height() + PADDING * 2
        self.resize(max(int(w), 40), max(int(h), 40))
        self._edit.setGeometry(self.rect())

    def enterEvent(self, event) -> None:
        self.setCursor(Qt.CursorShape.IBeamCursor if self._editing else Qt.CursorShape.SizeAllCursor)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.unsetCursor()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._editing:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging and not self._editing:
            delta = event.position().toPoint() - self._drag_offset
            new_pos = self.pos() + delta
            self.move(self._clamp_to_screen(new_pos))

    def _clamp_to_screen(self, pos: QPoint) -> QPoint:
        """约束目标位置到屏幕可用区域，保证控件完全可见。

        优先按目标位置所在屏幕约束；若不在任何屏幕上则回退到当前所在屏幕。
        """
        screen = QApplication.screenAt(pos)
        if screen is None:
            screen = QApplication.screenAt(self.geometry().center())
        if screen is None:
            screen = self.screen()
        if screen is None:
            return pos

        avail = screen.availableGeometry()
        w = self.width()
        h = self.height()
        max_x = avail.right() - w + 1
        max_y = avail.bottom() - h + 1
        x = max(avail.left(), min(pos.x(), max_x))
        y = max(avail.top(), min(pos.y(), max_y))
        return QPoint(x, y)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._dragging:
            self._dragging = False
            if self.rect().contains(event.position().toPoint()):
                self.setCursor(Qt.CursorShape.SizeAllCursor)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and not self._editing:
            self._start_editing()

    def _start_editing(self) -> None:
        self._editing = True
        self._edit.setText(self._text)
        self._edit.selectAll()
        self._edit.show()
        self._edit.setFocus()
        self.setCursor(Qt.CursorShape.IBeamCursor)
        self._edit.textChanged.connect(self._on_edit_text_changed)
        self._on_edit_text_changed()

    def _edit_padding(self) -> tuple[int, int]:
        """返回编辑器紧凑内边距 (h_pad, v_pad)，按字体大小缩放。"""
        font_size = self._font.pointSize() or DEFAULT_FONT_SIZE
        h_pad = max(2, font_size // 6)
        v_pad = max(1, font_size // 12)
        return h_pad, v_pad

    def _on_edit_text_changed(self) -> None:
        """根据输入动态调整控件与编辑器尺寸，紧凑布局。

        按横向原始文本计算宽度，仅保留边框 + 内边距 + 光标余量。
        """
        text = self._edit.text()
        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(text) if text else 0
        text_h = fm.height()

        h_pad, v_pad = self._edit_padding()
        w = text_w + h_pad * 2 + 2 + 4
        h = text_h + v_pad * 2 + 2

        font_size = self._font.pointSize() or DEFAULT_FONT_SIZE
        w = max(w, font_size * 3)
        h = max(h, text_h + 6)

        screen = QApplication.screenAt(self.geometry().center()) or self.screen()
        if screen is not None:
            max_w = screen.availableGeometry().width()
            w = min(w, max_w)

        self.resize(w, h)
        self._edit.setGeometry(self.rect())

    def _end_editing(self, commit: bool) -> None:
        """退出编辑模式。commit=True 保存，False 丢弃（ESC）。"""
        if not self._editing:
            return
        try:
            self._edit.textChanged.disconnect(self._on_edit_text_changed)
        except RuntimeError:
            pass
        if commit:
            self._text = self._edit.text()
        self._editing = False
        self._edit.hide()
        self._update_size()
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def _commit_edit(self) -> None:
        self._end_editing(commit=True)

    def _apply_edit_style(self) -> None:
        """同步编辑器的字体与配色，使用按字体缩放的紧凑内边距。"""
        self._edit.setFont(self._font)
        h_pad, v_pad = self._edit_padding()
        self._edit.setStyleSheet(
            f"color: {self._fill_color.name()};"
            f"background: rgba(0, 0, 0, 180);"
            f"border: 1px solid white;"
            f"padding: {v_pad}px {h_pad}px;"
            f"selection-background-color: #4a90e2;"
        )

    def contextMenuEvent(self, event) -> None:
        if self._editing:
            return
        menu = QMenu(self)
        action_font = menu.addAction("字体")
        action_color = menu.addAction("颜色")
        menu.addSeparator()

        orientation_menu = menu.addMenu("方向")
        action_horizontal = orientation_menu.addAction("横向")
        action_vertical = orientation_menu.addAction("纵向")
        action_horizontal.setCheckable(True)
        action_vertical.setCheckable(True)
        action_horizontal.setChecked(not self._vertical)
        action_vertical.setChecked(self._vertical)

        menu.addSeparator()
        action_add = menu.addAction("新增")
        action_close = menu.addAction("关闭")

        chosen = menu.exec(event.globalPos())

        if chosen is action_font:
            self._set_font()
        elif chosen is action_color:
            self._set_color()
        elif chosen is action_horizontal:
            self._set_vertical(False)
        elif chosen is action_vertical:
            self._set_vertical(True)
        elif chosen is action_add:
            self.add_widget_requested.emit()
        elif chosen is action_close:
            self.close()

    def _set_font(self) -> None:
        ok, font = QFontDialog.getFont(self._font, self, "选择字体")
        if ok and font is not None:
            self._font = font
            self._apply_edit_style()
            self._update_size()

    def _set_color(self) -> None:
        color = QColorDialog.getColor(self._fill_color, self, "选择文字颜色")
        if color.isValid():
            self._fill_color = color
            self._apply_display_style()
            self._apply_edit_style()

    def _set_vertical(self, vertical: bool) -> None:
        """设置文字方向（True=纵向堆叠，False=横向）。"""
        if self._vertical == vertical:
            return
        self._vertical = vertical
        self._update_size()

    def closeEvent(self, event) -> None:
        self.widget_closed.emit(self)
        super().closeEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self._editing and event.key() == Qt.Key.Key_Escape:
            self._end_editing(commit=False)
            return
        super().keyPressEvent(event)
