from PySide6.QtWidgets import QWidget, QHBoxLayout, QApplication, QVBoxLayout, QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QPixmap, QMouseEvent
from frames.frame_functions.utils import create_button

class MiniPlayer(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()
        self.main_window.player.playbackStateChanged.connect(self.update_play_button_icon)
        self.setWindowTitle("Mini Player")
        self.setMouseTracking(True)
        self.setToolTip("Click and hold anywhere on the Mini Player to move it around "
                        "And double click anywhere to Minimize it")

    def setup_ui(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 400)
        self.mouseDoubleClickEvent = lambda event: self.minimize_window()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.background_label = QLabel(self)
        self.background_label.setScaledContents(True)
        main_layout.addWidget(self.background_label)

        self.controls_widget = QWidget(self)
        self.controls_widget.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        self.controls_widget.setFixedSize(self.size())

        controls_layout = QVBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(10, 52, 10, 10)

        main_controls_layout = QHBoxLayout()
        main_controls_layout.setAlignment(Qt.AlignCenter)
        main_controls_layout.setSpacing(20)

        self.prev_button = create_button('icons/previous.png', self.prev_song, 40)
        main_controls_layout.addWidget(self.prev_button)

        self.play_button = create_button('icons/play.png', self.play_pause, 50)
        main_controls_layout.addWidget(self.play_button)

        self.next_button = create_button('icons/next.png', self.next_song, 40)
        main_controls_layout.addWidget(self.next_button)

        controls_layout.addLayout(main_controls_layout)

        return_button_layout = QHBoxLayout()
        return_button_layout.addStretch()
        self.return_button = create_button('icons/maximize.png', self.return_to_main, 35)
        return_button_layout.addWidget(self.return_button)
        controls_layout.addLayout(return_button_layout)

        self.opacity_effect = QGraphicsOpacityEffect(self.controls_widget)
        self.controls_widget.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)

        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)

    def play_pause(self):
        self.main_window.now_playing_view.play_pause()

    def prev_song(self):
        self.main_window.now_playing_view.prev_song()

    def next_song(self):
        self.main_window.now_playing_view.next_song()

    def minimize_window(self):
        self.showMinimized()

    def return_to_main(self):
        self.hide()
        self.main_window.show()

    def show_mini(self, cover_image_path):
        self.set_background_image(cover_image_path)
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.width() - self.width() - 10
        y = 10
        self.move(x, y)
        self.main_window.hide()
        self.show()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging:
            self.move(self.mapToGlobal(event.position().toPoint()) - self.offset)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def update_play_button_icon(self):
        if self.main_window.player.isPlaying():
            self.play_button.setIcon(QIcon("icons/pause.png"))
        else:
            self.play_button.setIcon(QIcon("icons/play.png"))

    def set_background_image(self, image_path):
        pixmap = QPixmap(image_path)
        self.background_label.setPixmap(pixmap)

    def enterEvent(self, event):
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.start()

    def leaveEvent(self, event):
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.start()
