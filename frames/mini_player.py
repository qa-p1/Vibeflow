from PySide6.QtWidgets import QWidget, QHBoxLayout, QApplication, QVBoxLayout, QLabel, QGraphicsOpacityEffect, QSlider
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QPixmap, QMouseEvent, QPainter, QPainterPath, QBrush, QColor
from frames.frame_functions.utils import create_button


class MicroPlayer(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.dragging = False
        self.offset = None
        self.setup_ui()
        self.main_window.player.playbackStateChanged.connect(self.update_play_button_icon)
        self.main_window.player.positionChanged.connect(self.update_position)
        self.main_window.player.durationChanged.connect(self.update_duration)
        self.setWindowTitle("Micro Player")
        self.setMouseTracking(True)
        self.setToolTip("Micro Player - Click and drag to move, Double-click to expand")

    def setup_ui(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 80)

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Cover art
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(60, 60)
        self.cover_label.setScaledContents(True)
        self.cover_label.setStyleSheet("""
            QLabel {
                border-radius: 8px;
                background-color: #2a2a2a;
            }
        """)
        main_layout.addWidget(self.cover_label)

        # Controls layout
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(5)

        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.prev_button = create_button('icons/previous.png', self.prev_song, 20)
        self.play_button = create_button('icons/play.png', self.play_pause, 25)
        self.next_button = create_button('icons/next.png', self.next_song, 20)
        self.expand_button = create_button('icons/maximize.png', self.expand_to_mini, 20)

        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.next_button)
        button_layout.addStretch()
        button_layout.addWidget(self.expand_button)

        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setFixedHeight(6)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 4px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #1db954;
                border: none;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::sub-page:horizontal {
                background: #1db954;
                border-radius: 2px;
            }
        """)
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)
        self.progress_slider.sliderMoved.connect(self.on_slider_moved)
        self.slider_pressed = False

        controls_layout.addLayout(button_layout)
        controls_layout.addWidget(self.progress_slider)

        main_layout.addLayout(controls_layout)

        # Set background style
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(25, 25, 25, 230);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Create rounded rectangle background
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 12, 12)

        # Fill with semi-transparent background
        painter.fillPath(path, QBrush(QColor(25, 25, 25, 230)))

        # Add border
        painter.setPen(QColor(255, 255, 255, 25))
        painter.drawPath(path)

    def play_pause(self):
        self.main_window.now_playing_view.play_pause()

    def prev_song(self):
        self.main_window.now_playing_view.prev_song()

    def next_song(self):
        self.main_window.now_playing_view.next_song()

    def expand_to_mini(self):
        """Switch back to mini player"""
        self.hide()
        # Get the mini player instance from main window
        if hasattr(self.main_window, 'mini_player'):
            self.main_window.mini_player.show()

    def show_micro(self, cover_image_path):
        self.set_cover_image(cover_image_path)
        # Position in top-right corner
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.width() - self.width() - 10
        y = 10
        self.move(x, y)
        self.show()

    def set_cover_image(self, image_path):
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # Create rounded pixmap
            rounded_pixmap = QPixmap(60, 60)
            rounded_pixmap.fill(Qt.transparent)

            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            path = QPainterPath()
            path.addRoundedRect(0, 0, 60, 60, 8, 8)
            painter.setClipPath(path)

            scaled_pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            painter.drawPixmap(0, 0, scaled_pixmap)
            painter.end()

            self.cover_label.setPixmap(rounded_pixmap)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging and self.offset:
            self.move(self.mapToGlobal(event.position().toPoint()) - self.offset)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.expand_to_mini()

    def update_play_button_icon(self):
        if self.main_window.player.isPlaying():
            self.play_button.setIcon(QIcon("icons/pause.png"))
        else:
            self.play_button.setIcon(QIcon("icons/play.png"))

    def on_slider_pressed(self):
        self.slider_pressed = True

    def on_slider_released(self):
        self.slider_pressed = False
        position = self.progress_slider.value()
        self.main_window.player.setPosition(position)

    def on_slider_moved(self, position):
        if self.slider_pressed:
            self.main_window.player.setPosition(position)

    def update_position(self, position):
        if not self.slider_pressed:
            self.progress_slider.setValue(position)

    def update_duration(self, duration):
        self.progress_slider.setMaximum(duration)

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        player = self.main_window.player

        # Play/Pause
        if key == Qt.Key_W and modifiers == Qt.NoModifier:
            self.play_pause()
            event.accept()
            return

        # Next
        elif key == Qt.Key_Greater and modifiers == Qt.ShiftModifier:
            self.next_song()
            event.accept()
            return

        # Previous
        elif key == Qt.Key_Less and modifiers == Qt.ShiftModifier:
            self.prev_song()
            event.accept()
            return

        # Seek forward 5s
        elif key == Qt.Key_D and modifiers == Qt.NoModifier:
            new_pos = min(player.position() + 5000, player.duration())
            player.setPosition(new_pos)
            event.accept()
            return

        # Seek backward 5s
        elif key == Qt.Key_A and modifiers == Qt.NoModifier:
            new_pos = max(player.position() - 5000, 0)
            player.setPosition(new_pos)
            event.accept()
            return

        super().keyPressEvent(event)


class MiniPlayer(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.dragging = False
        self.offset = None
        self.setup_ui()
        self.main_window.player.playbackStateChanged.connect(self.update_play_button_icon)
        self.setWindowTitle("Mini Player")
        self.setMouseTracking(True)
        self.setToolTip("Click and hold anywhere on the Mini Player to move it around. "
                        "Double click anywhere to Minimize it")

        # Create micro player instance
        self.micro_player = MicroPlayer(main_window)

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

        # Main controls layout
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
        bottom_buttons_layout = QHBoxLayout()

        # Shuffle button
        self.shuffle_button = create_button('icons/shuffle.png', self.toggle_shuffle, 30)
        self.update_shuffle_button_icon()
        bottom_buttons_layout.addWidget(self.shuffle_button)

        bottom_buttons_layout.addStretch()

        # Micro player button
        self.micro_button = create_button('icons/collapse.png', self.show_micro_player, 30)
        self.micro_button.setToolTip("Switch to Micro Player")
        bottom_buttons_layout.addWidget(self.micro_button)

        # Return button
        self.return_button = create_button('icons/maximize.png', self.return_to_main, 35)
        bottom_buttons_layout.addWidget(self.return_button)

        controls_layout.addLayout(bottom_buttons_layout)

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

    def toggle_shuffle(self):
        """Toggle between repeat, shuffle, and repeat_one modes"""
        if self.main_window.play_mode == "repeat":
            self.main_window.play_mode = "shuffle"
        elif self.main_window.play_mode == "shuffle":
            self.main_window.play_mode = "repeat_one"
        else:  # repeat_one
            self.main_window.play_mode = "repeat"

        self.update_shuffle_button_icon()

    def update_shuffle_button_icon(self):
        """Update shuffle button icon based on current play mode"""
        if self.main_window.play_mode == "shuffle":
            self.shuffle_button.setIcon(QIcon("icons/shuffle.png"))
            self.shuffle_button.setToolTip("Shuffle: ON")
        elif self.main_window.play_mode == "repeat_one":
            self.shuffle_button.setIcon(QIcon("icons/repeat-one.png"))  # You'll need this icon
            self.shuffle_button.setToolTip("Repeat One: ON")
        else:  # repeat
            self.shuffle_button.setIcon(QIcon("icons/repeat.png"))  # You'll need this icon
            self.shuffle_button.setToolTip("Repeat All: ON")

    def show_micro_player(self):
        """Switch to micro player mode"""
        self.hide()
        # Get current cover image
        if hasattr(self.main_window, 'player') and not self.main_window.player.source().isEmpty():
            source = self.main_window.player.source().toString().lower()
            if source in self.main_window.url_to_song_info:
                cover_path = self.main_window.url_to_song_info[source]['cover_location']
            else:
                cover_path = 'icons/default-image.png'
        else:
            cover_path = 'icons/default-image.png'

        self.micro_player.show_micro(cover_path)

    def minimize_window(self):
        self.showMinimized()

    def return_to_main(self):
        self.hide()
        self.micro_player.hide()
        self.main_window.show()

    def show_mini(self, cover_image_path):
        self.set_background_image(cover_image_path)
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.width() - self.width() - 10
        y = 10
        self.move(x, y)
        self.main_window.hide()
        self.micro_player.hide()  # Hide micro player if it's showing
        self.show()

    def hide(self):
        """Override hide to also hide micro player"""
        super().hide()
        if hasattr(self, 'micro_player'):
            self.micro_player.hide()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.dragging and self.offset:
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
        # Also update micro player cover
        if hasattr(self, 'micro_player'):
            self.micro_player.set_cover_image(image_path)

    def enterEvent(self, event):
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.start()

    def leaveEvent(self, event):
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.start()

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        player = self.main_window.player

        # Play/Pause
        if key == Qt.Key_W and modifiers == Qt.NoModifier:
            self.play_pause()
            event.accept()
            return

        # Next
        elif key == Qt.Key_Greater and modifiers == Qt.ShiftModifier:
            self.next_song()
            event.accept()
            return

        # Previous
        elif key == Qt.Key_Less and modifiers == Qt.ShiftModifier:
            self.prev_song()
            event.accept()
            return

        # Seek forward 5s
        elif key == Qt.Key_D and modifiers == Qt.NoModifier:
            new_pos = min(player.position() + 5000, player.duration())
            player.setPosition(new_pos)
            event.accept()
            return

        # Seek backward 5s
        elif key == Qt.Key_A and modifiers == Qt.NoModifier:
            new_pos = max(player.position() - 5000, 0)
            player.setPosition(new_pos)
            event.accept()
            return

        # Cycle Play Mode
        elif key == Qt.Key_S and modifiers == Qt.NoModifier:
            self.toggle_shuffle()
            event.accept()
            return

        super().keyPressEvent(event)
