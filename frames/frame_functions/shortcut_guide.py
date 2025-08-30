from PySide6.QtWidgets import QDialog, QVBoxLayout, QGridLayout, QLabel, QScrollArea, QWidget, QFrame, QHBoxLayout
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QPainterPath, QColor, QBrush, QLinearGradient, QMouseEvent
from .utils import create_button


class ShortcutGuideDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Shortcut Guide")
        self.setMinimumSize(450, 600)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.drag_pos = None

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)

        self.frame = QFrame(self)
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(25, 10, 25, 25)
        frame_layout.setSpacing(15)
        main_layout.addWidget(self.frame)

        title_bar_layout = QHBoxLayout()
        title_bar_layout.setContentsMargins(0, 0, 0, 10)
        title = QLabel("Shortcut Guide")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #eeeeee; background: transparent;")

        title_bar_layout.addWidget(title)
        title_bar_layout.addStretch()

        close_button = create_button("icons/minimiz.png", self.accept, 20)  # Use a close/minimize icon
        title_bar_layout.addWidget(close_button)
        frame_layout.addLayout(title_bar_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        self.grid_layout = QGridLayout(content_widget)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setColumnStretch(0, 0)
        self.grid_layout.setColumnStretch(1, 1)

        self.populate_shortcuts()

        scroll_area.setWidget(content_widget)
        frame_layout.addWidget(scroll_area, 1)

        self.apply_styles()

    def populate_shortcuts(self):
        shortcuts = {
            "Global Controls": [
                ("W", "Play / Pause playback"),
                ("Shift + >", "Next Song"),
                ("Shift + <", "Previous Song"),
                ("D", "Seek Forward 10 seconds"),
                ("A", "Seek Backward 10 seconds"),
                ("M", "Mute / Unmute audio"),
            ],
            "UI & Navigation": [
                ("L", "Toggle Lyrics View"),
                ("Q", "Toggle Queue View"),
                ("Ctrl + B", "Toggle Side Panel"),
                ("Ctrl + M", "Open Mini Player"),
                ("Ctrl + S", "Open Settings Page"),
                ("Ctrl + I", "Show this Shortcut Guide"),
            ],
            "Player Modes": [
                ("S", "Cycle Play Mode (Repeat/Shuffle/One)"),
            ],
            "Mini / Micro Player": [
                ("W", "Play / Pause"),
                ("D / A", "Seek Forward / Backward 5 seconds"),
                ("S (Mini Only)", "Cycle Play Mode"),
            ]
        }

        row = 0
        for section, items in shortcuts.items():
            section_label = QLabel(section)
            section_label.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #7aa2f7; background: transparent; margin-top: 10px; border-bottom: 1px solid #414868; padding-bottom: 4px;")
            self.grid_layout.addWidget(section_label, row, 0, 1, 2)
            row += 1

            for key, description in items:
                self._add_shortcut_row(key, description, row)
                row += 1

        self.grid_layout.setRowStretch(row, 1)

    def _add_shortcut_row(self, key_text, description_text, row):
        key_label = QLabel(key_text)
        key_label.setAlignment(Qt.AlignCenter)
        key_label.setMinimumWidth(80)
        key_label.setStyleSheet("""
            QLabel {
                background-color: #24283b; color: #c0caf5; font-family: Consolas, monospace;
                font-size: 13px; font-weight: bold; padding: 6px 10px; border-radius: 6px;
            }
        """)
        description_label = QLabel(description_text)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 14px; color: #a9b1d6; background: transparent;")
        self.grid_layout.addWidget(key_label, row, 0)
        self.grid_layout.addWidget(description_label, row, 1)

    def apply_styles(self):
        self.frame.setStyleSheet("""
            QFrame {
                background: rgba(25, 25, 30, 240); border: none;
                border-radius: 16px; font-family: Quicksand;
            }
            /* Removed QPushButton style as it's handled by create_button now */
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 10); width: 8px; border-radius: 4px; margin: 0;
            }
            QScrollBar::handle:vertical { background: #414868; min-height: 20px; border-radius: 4px; }
            QScrollBar::handle:vertical:hover { background: #565f89; }
        """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 16, 16)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(40, 42, 54, 220))
        gradient.setColorAt(1, QColor(30, 32, 42, 235))
        painter.fillPath(path, QBrush(gradient))
        painter.setPen(QColor(255, 255, 255, 30))
        painter.drawPath(path)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.drag_pos and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()
