from PySide6.QtWidgets import QPushButton, QLayout, QWidget, QLabel
from PySide6.QtCore import QSize, Qt, QUrl, Signal, QObject, QEvent
from PySide6.QtGui import QIcon, QPainter, QFontMetrics


def create_button(icon_path, on_click, size):
    button = QPushButton()
    button.setIcon(QIcon(icon_path))
    button.setIconSize(QSize(size, size))
    button.setStyleSheet("QPushButton{border: none; padding: 5px; background: transparent;}")
    button.setCursor(Qt.PointingHandCursor)
    button.clicked.connect(on_click)
    return button


def play_pause(player, play_button, all_songs):
    if len(all_songs) == 0:
        return
    else:
        if player.source().toString() == '':
            player.setSource(QUrl(all_songs[0]["mp3_location"]))
            player.play()
        else:
            if player.isPlaying():
                player.pause()
                play_button.setIcon(QIcon("icons/play.png"))
            else:
                player.play()
                play_button.setIcon(QIcon("icons/pause.png"))


class HoverEventFilter(QObject):
    hoverEnter = Signal()
    hoverLeave = Signal()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            self.hoverEnter.emit()
        elif event.type() == QEvent.Leave:
            self.hoverLeave.emit()
        return super().eventFilter(obj, event)


def apply_hover_effect(widget_or_layout, enter_style, leave_style):
    if isinstance(widget_or_layout, QLayout):
        widget = widget_or_layout.parentWidget()
    elif isinstance(widget_or_layout, QWidget):
        widget = widget_or_layout
    else:
        raise TypeError("Input must be a QWidget or QLayout")

    hover_filter = HoverEventFilter(widget)
    widget.installEventFilter(hover_filter)

    def on_hover_enter():
        widget.setStyleSheet(enter_style)

    def on_hover_leave():
        widget.setStyleSheet(leave_style)

    hover_filter.hoverEnter.connect(on_hover_enter)
    hover_filter.hoverLeave.connect(on_hover_leave)

    widget.setStyleSheet(leave_style)


class name_label(QLabel):
    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), Qt.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment(), elided)
