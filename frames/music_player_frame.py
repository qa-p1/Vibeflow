from random import choice
from PySide6.QtCore import Qt, QTimer, QTime, Signal, QRect, QPropertyAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor, QPainterPath, QFont, QBrush, QLinearGradient, \
    QCursor
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QVBoxLayout, QSlider,
                               QPushButton, QDialog, QSpinBox, QFrame, QListWidgetItem,
                               QListWidget, QSizePolicy, QGridLayout, QProgressBar)
from .frame_functions.utils import create_button
from colorthief import ColorThief


class CustomTimerDialog(QDialog):
    timerStarted = Signal(QTime)
    timerStopped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.setup_ui()
        self.setWindowTitle("Timer")
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowSystemMenuHint)
        self.setFixedSize(400, 280)

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(25)

        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(15)

        self.hours = QSpinBox()
        self.minutes = QSpinBox()
        self.seconds = QSpinBox()

        time_grid = QGridLayout()
        time_grid.setSpacing(8)

        labels = ["Hours", "Minutes", "Seconds"]
        spinboxes = [self.hours, self.minutes, self.seconds]

        for i, (label_text, spinbox) in enumerate(zip(labels, spinboxes)):
            label = QLabel(label_text)
            label.setObjectName("inputLabel")
            spinbox.setRange(0, 59)
            spinbox.setButtonSymbols(QSpinBox.PlusMinus)
            time_grid.addWidget(label, i, 0)
            time_grid.addWidget(spinbox, i, 1)

        self.hours.setRange(0, 23)
        controls_layout.addLayout(time_grid)
        controls_layout.addStretch()

        self.start_stop_button = QPushButton("Start")
        self.start_stop_button.setObjectName("startButton")
        self.start_stop_button.clicked.connect(self.toggle_timer)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)

        controls_layout.addWidget(self.start_stop_button)
        controls_layout.addWidget(self.close_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setOrientation(Qt.Vertical)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(0)

        main_layout.addWidget(controls_widget)
        main_layout.addWidget(self.progress_bar)

        self.apply_stylesheet()

    def toggle_timer(self):
        if self.timer.isActive():
            self.stop_timer()
        else:
            self.start_timer()
            self.hide()

    def start_timer(self):
        total_seconds = self.hours.value() * 3600 + self.minutes.value() * 60 + self.seconds.value()
        if total_seconds == 0:
            return

        self.progress_bar.setMaximum(total_seconds)
        self.progress_bar.setValue(total_seconds)
        self.timer.start(1000)
        self.start_stop_button.setText("Stop")
        self.enable_spinboxes(False)
        self.timerStarted.emit(QTime(self.hours.value(), self.minutes.value(), self.seconds.value()))

    def stop_timer(self):
        self.timer.stop()
        self.start_stop_button.setText("Start")
        self.enable_spinboxes(True)
        self.progress_bar.setValue(0)
        self.timerStopped.emit()

    def update_time(self):
        if self.seconds.value() > 0:
            self.seconds.setValue(self.seconds.value() - 1)
        elif self.minutes.value() > 0:
            self.minutes.setValue(self.minutes.value() - 1)
            self.seconds.setValue(59)
        elif self.hours.value() > 0:
            self.hours.setValue(self.hours.value() - 1)
            self.minutes.setValue(59)
            self.seconds.setValue(59)
        else:
            self.stop_timer()
            return

        current_seconds = self.hours.value() * 3600 + self.minutes.value() * 60 + self.seconds.value()
        self.progress_bar.setValue(current_seconds)

    def enable_spinboxes(self, enable):
        self.hours.setEnabled(enable)
        self.minutes.setEnabled(enable)
        self.seconds.setEnabled(enable)

    def closeEvent(self, event):
        self.stop_timer()
        super().closeEvent(event)

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1f22;
                font-family: 'Inter', sans-serif;
            }
            #inputLabel {
                color: #a9b1d6;
                font-size: 13px;
            }
            QSpinBox {
                background-color: #24283b;
                color: #c0caf5;
                border: 1px solid #414868;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                subcontrol-origin: border;
                background-color: #2f334d;
                width: 18px;
                border-left: 1px solid #414868;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                 /* You can provide custom arrow images here if desired */
            }
            QPushButton {
                background-color: #414868;
                color: #c0caf5;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #565f89;
            }
            QPushButton:pressed {
                background-color: #3b4261;
            }
            #startButton {
                background-color: #7aa2f7;
                color: #1a1b26;
                font-weight: bold;
                border: none;
            }
            #startButton:hover {
                background-color: #9eceff;
            }
            QProgressBar {
                border: 1px solid #414868;
                border-radius: 8px;
                background-color: #24283b;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #7dcfff, stop:1 #7aa2f7);
                border-radius: 6px;
                margin: 2px;
            }
        """)


class QueueListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setAcceptDrops(True)

    def dropEvent(self, event):
        super().dropEvent(event)
        new_order_data = [self.item(i).data(Qt.UserRole) for i in range(self.count())]
        actual_song_order = [data for data in new_order_data if isinstance(data, dict) and 'mp3_location' in data]
        if hasattr(self.parent().parent(), 'queueUpdated'):
            self.parent().parent().queueUpdated.emit(actual_song_order)


class QueueView(QWidget):
    queueUpdated = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Widget | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setup_ui()
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(400)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.finished.connect(self.animation_finished)
        self.is_visible = False

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.frame = QFrame(self)
        self.frame.setObjectName("queueFrame")
        self.frame.setStyleSheet("""
            #queueFrame {
                background: rgba(20, 20, 20, 0.9);
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }
        """)
        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)

        header_layout = QHBoxLayout()
        header_label = QLabel("Up Next")
        header_label.setStyleSheet(
            "font-size: 22px; font-weight: 600; background: none; color: #ffffff; margin-bottom: 10px;")
        close_button = create_button('icons/minimiz.png', self.hide_queue, 24)
        close_button.setStyleSheet(
            "QPushButton { background: rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 8px; } QPushButton:hover { background: rgba(255, 255, 255, 0.2); }")

        header_layout.addWidget(header_label, alignment=Qt.AlignLeft)
        header_layout.addStretch()
        header_layout.addWidget(close_button)

        self.queue_list = QueueListWidget(self.frame)
        self.queue_list.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.queue_list.setStyleSheet("""
            QListWidget { background: transparent; border: none; font-size: 15px; color: #e8e8e8; }
            QListWidget::item { background: rgba(255, 255, 255, 0.05); border-radius: 12px; margin: 4px 0px; padding: 14px 16px; border: 1px solid rgba(255, 255, 255, 0.05); }
            QListWidget::item:selected { background: rgba(255, 255, 255, 0.12); }
            QListWidget::item:hover { background: rgba(255, 255, 255, 0.08); }
        """)

        frame_layout.addLayout(header_layout)
        frame_layout.addWidget(self.queue_list)
        main_layout.addWidget(self.frame)

    def update_queue(self, playlist_songs_info):
        self.queue_list.clear()
        if not playlist_songs_info:
            return

        current_index = self.parent().main_frame.current_song_index
        if current_index < 0 or current_index >= len(playlist_songs_info):
            print(f"QueueView.update_queue: Invalid current_index ({current_index}).")
            return

        def create_section_label(text):
            item = QListWidgetItem(text)
            item.setFlags(Qt.NoItemFlags)
            item.setForeground(QColor("#aaaaaa"))
            font = QFont(self.queue_list.font())
            font.setBold(True)
            item.setFont(font)
            return item

        def create_song_item(song_info, highlight=False):
            display_text = f"⠿ {song_info['song_name']} - {song_info['artist']}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, song_info)
            if highlight:
                gradient = QLinearGradient(0, 0, 1, 0)
                gradient.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
                gradient.setColorAt(0.0, QColor("#ff6b6b"))
                gradient.setColorAt(1.0, QColor("#4ecdc4"))
                item.setBackground(QBrush(gradient))
                item.setForeground(QColor("white"))
                font = QFont(item.font())
                font.setBold(True)
                item.setFont(font)
            return item

        if current_index > 0:
            self.queue_list.addItem(create_section_label("Previously Played"))
            for i in range(current_index):
                self.queue_list.addItem(create_song_item(playlist_songs_info[i]))

        self.queue_list.addItem(create_song_item(playlist_songs_info[current_index], highlight=True))

        if current_index < len(playlist_songs_info) - 1:
            self.queue_list.addItem(create_section_label("Up Next"))
            for i in range(current_index + 1, len(playlist_songs_info)):
                self.queue_list.addItem(create_song_item(playlist_songs_info[i]))

    def show_queue(self):
        if not self.is_visible:
            parent = self.parentWidget()
            if not parent:
                return
            self.setGeometry(0, parent.height(), parent.width(), int(parent.height() * 0.7))
            self.show()
            self.animateBottomUp()

    def animateBottomUp(self):
        parent = self.parentWidget()
        if not parent:
            return
        start_rect = QRect(0, parent.height(), parent.width(), self.height())
        end_rect = QRect(0, parent.height() - self.height(), parent.width(), self.height())
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()

    def hide_queue(self):
        if self.is_visible:
            parent = self.parentWidget()
            if not parent:
                return
            start_rect = self.geometry()
            end_rect = QRect(0, parent.height(), parent.width(), self.height())
            self.animation.setStartValue(start_rect)
            self.animation.setEndValue(end_rect)
            self.animation.start()

    def animation_finished(self):
        parent = self.parentWidget()
        if not parent:
            self.is_visible = False
            return
        if self.geometry().y() >= parent.height():
            self.hide()
            self.is_visible = False
        else:
            self.is_visible = True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.is_visible:
            parent = self.parentWidget()
            if parent:
                new_height = int(parent.height() * 0.7)
                self.setGeometry(0, parent.height() - new_height, parent.width(), new_height)


class NowPlayingView(QWidget):
    backgroundChanged = Signal(QPixmap)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_frame = parent
        self.play_modes = [("repeat", "icons/repeat.png"), ("repeat_one", "icons/repeat-one.png"),
                           ("shuffle", "icons/shuffle.png")]
        self.current_mode_index = 0
        self.sleep_timer_qtimer = QTimer(self)
        self.sleep_timer_qtimer.timeout.connect(self.update_timer_display)
        self.timer_dialog = None
        self.setup_ui()
        self.queue_view = QueueView(self)
        self.queue_view.queueUpdated.connect(self.update_current_playlist_from_queue)
        self.queue_view.hide()
        self.ui_update_timer = QTimer(self)
        self.ui_update_timer.setInterval(100)
        self.ui_update_timer.timeout.connect(self.update_player_ui)
        self.ui_update_timer.start()

    def setup_ui(self):
        self.setAttribute(Qt.WA_StyledBackground, True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 10, 40, 30)
        main_layout.setSpacing(0)

        self.top_bar_widget = QWidget(self)
        self.top_bar_widget.setStyleSheet("background:transparent;")

        self.top_bar_layout = QHBoxLayout(self.top_bar_widget)
        self.top_bar_layout.setContentsMargins(0, 25, 20, 0)
        self.top_bar_layout.addStretch()
        self.menu_button = create_button("icons/bar.png", self.main_frame.toggle_home_screen, 40)
        self.menu_button.setToolTip("Toggle Panel")
        self.menu_button.setFixedSize(60, 60)
        self.menu_button.setStyleSheet(
            "QPushButton { background: rgba(0,0,0,0.4); border-radius: 30px; } QPushButton:hover { background: rgba(0,0,0,0.6); }")
        self.top_bar_layout.addWidget(self.menu_button)

        main_layout.addStretch(1)

        cover_layout = QHBoxLayout()
        cover_layout.addStretch()
        self.large_cover = QLabel()
        self.large_cover.setFixedSize(300, 300)
        self.large_cover.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.large_cover.setStyleSheet("background: transparent;")
        self.large_cover.setAlignment(Qt.AlignCenter)
        self.large_cover.setPixmap(
            QPixmap("icons/default-image.png").scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        cover_layout.addWidget(self.large_cover)
        cover_layout.addStretch()
        main_layout.addLayout(cover_layout)

        main_layout.addSpacing(30)
        self.song_title = QLabel("Song Title", alignment=Qt.AlignCenter, wordWrap=True,
                                 styleSheet="font-size: 28px; font-weight: 700; color: #ffffff; text-shadow: 2px 2px 4px rgba(0,0,0,0.8);")
        main_layout.addWidget(self.song_title)
        main_layout.addSpacing(10)
        self.artist_label = QLabel("Artist Name", alignment=Qt.AlignCenter,
                                   styleSheet="font-size: 18px; color: rgba(255, 255, 255, 0.8); font-weight: 500; text-shadow: 1px 1px 3px rgba(0,0,0,0.7);")
        main_layout.addWidget(self.artist_label)

        main_layout.addSpacing(5)
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)
        progress_container.setStyleSheet("background:transparent;")
        time_layout = QHBoxLayout()
        self.current_time = QLabel("0:00")
        self.total_time = QLabel("0:00")
        time_style = "color: rgba(255,255,255,0.7); font-size: 14px; font-weight: 500;"
        self.current_time.setStyleSheet(time_style)
        self.total_time.setStyleSheet(time_style)
        time_layout.addWidget(self.current_time)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time)
        progress_layout.addLayout(time_layout)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderMoved.connect(self.set_position)
        self.slider.setMinimumWidth(400)
        self.slider.setStyleSheet(
            "QSlider::groove:horizontal{height:6px;background:rgba(255,255,255,0.2);border-radius:3px} QSlider::handle:horizontal{background:#fff;border:none;width:18px;height:18px;margin:-6px 0;border-radius:9px} QSlider::sub-page:horizontal{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #ff6b6b,stop:1 #4ecdc4);border-radius:3px}")
        progress_layout.addWidget(self.slider)
        progress_center = QHBoxLayout()
        progress_center.addStretch()
        progress_center.addWidget(progress_container)
        progress_center.addStretch()
        main_layout.addLayout(progress_center)

        main_layout.addSpacing(20)
        controls = QHBoxLayout()
        controls.setSpacing(15)
        self.play_mode_button = create_button("icons/repeat.png", self.cycle_play_mode, 32)
        self.play_mode_button.setFixedSize(56, 56)
        self.prev_button = create_button("icons/previous.png", self.prev_song, 36)
        self.prev_button.setFixedSize(64, 64)
        self.play_button = create_button("icons/play.png", self.play_pause, 64)
        self.play_button.setFixedSize(80, 80)
        self.next_button = create_button("icons/next.png", self.next_song, 36)
        self.next_button.setFixedSize(64, 64)
        self.queue_button = create_button("icons/queue.png", self.show_queue, 32)
        self.queue_button.setFixedSize(56, 56)
        btn_style = "QPushButton{{background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.1);border-radius:{r}px}} QPushButton:hover{{background:rgba(0,0,0,0.5)}}"
        self.play_mode_button.setStyleSheet(btn_style.format(r=28))
        self.prev_button.setStyleSheet(btn_style.format(r=32))
        self.play_button.setStyleSheet(btn_style.format(r=40))
        self.next_button.setStyleSheet(btn_style.format(r=32))
        self.queue_button.setStyleSheet(btn_style.format(r=28))
        controls.addStretch()
        controls.addWidget(self.play_mode_button)
        controls.addWidget(self.prev_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.next_button)
        controls.addWidget(self.queue_button)
        controls.addStretch()
        main_layout.addLayout(controls)

        main_layout.addSpacing(30)
        sec_controls = QHBoxLayout()
        sec_controls.setSpacing(20)
        self.lyrics_button = create_button("icons/lyrics.png", self.show_lyrics, 28)
        self.timer_button = create_button("icons/timer.png", self.open_timer_dialog, 28)
        self.mini_player_button = create_button('icons/collapse.png', self.main_frame.open_mini_player, 28)
        for btn in [self.lyrics_button, self.timer_button, self.mini_player_button]:
            btn.setStyleSheet(btn_style.format(r=26))
            btn.setFixedSize(52, 52)

        sec_controls.addStretch()
        sec_controls.addWidget(self.lyrics_button)
        sec_controls.addWidget(self.timer_button)
        sec_controls.addWidget(self.mini_player_button)
        sec_controls.addStretch()
        main_layout.addLayout(sec_controls)

        main_layout.addSpacing(15)
        timer_layout = QHBoxLayout()
        self.timer_label = QLabel(alignment=Qt.AlignCenter,
                                  styleSheet="color:#4ecdc4;font-size:14px;background:rgba(78,205,196,0.1);font-weight:600;padding:8px 16px;border-radius:20px");
        self.timer_label.hide()
        timer_layout.addStretch()
        timer_layout.addWidget(self.timer_label)
        timer_layout.addStretch()
        main_layout.addLayout(timer_layout)
        main_layout.addStretch(1)
        self.top_bar_widget.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.top_bar_widget.setGeometry(0, 0, self.width(), 85)
        self.queue_view.resizeEvent(event)

    def update_menu_button_icon(self, is_expanded):
        if is_expanded:
            self.top_bar_layout.setContentsMargins(0, 25, 20, 0)
            self.menu_button.setToolTip("Hide Panel")
        else:
            self.top_bar_layout.setContentsMargins(20, 25, 20, 0)
            self.menu_button.setToolTip("Show Panel")

    @staticmethod
    def get_dominant_colors(image_path):
        try:
            color_thief = ColorThief(image_path)
            palette = color_thief.get_palette(color_count=3, quality=1)
            return palette
        except Exception as e:
            print(f"Error getting dominant colors: {e}")
            return [(100, 100, 100), (80, 80, 80), (60, 60, 60)]

    def update_info(self, song_info):
        if not song_info or 'cover_location' not in song_info:
            self.song_title.setText("No Song Playing")
            self.artist_label.setText("Select a song to begin")
            pixmap = QPixmap("icons/default-image.png")
            self.dominant_colors = self.get_dominant_colors("icons/default-image.png")
        else:
            self.song_title.setText(song_info['song_name'])
            self.artist_label.setText(song_info['artist'])
            pixmap = QPixmap(song_info['cover_location'])
            if pixmap.isNull():
                pixmap = QPixmap("icons/default-image.png")
            self.dominant_colors = self.get_dominant_colors(song_info.get('cover_location', "icons/default-image.png"))

        self.update_large_cover(pixmap)
        QTimer.singleShot(10, lambda: self.backgroundChanged.emit(pixmap))

    def update_large_cover(self, pixmap):
        rounded_cover_pixmap = QPixmap(self.large_cover.size())
        rounded_cover_pixmap.fill(Qt.transparent)
        painter = QPainter(rounded_cover_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(0, 0, self.large_cover.width(), self.large_cover.height()), 30, 30)
        painter.setClipPath(clip_path)
        scaled_image_for_cover = pixmap.scaled(self.large_cover.size(), Qt.KeepAspectRatioByExpanding,
                                               Qt.SmoothTransformation)
        painter.drawPixmap(0, 0, scaled_image_for_cover)
        painter.end()
        self.large_cover.setPixmap(rounded_cover_pixmap)

    def update_current_playlist_from_queue(self, new_song_info_order):
        new_indices = []
        current_song_path = self.main_frame.player.source().toLocalFile().lower() if self.main_frame.player.source().isLocalFile() else ""
        for info in new_song_info_order:
            try:
                original_index = next(
                    i for i, s in enumerate(self.main_frame.all_songs) if s['mp3_location'] == info['mp3_location'])
                new_indices.append(original_index)
            except StopIteration:
                print(f"Warning: Song '{info.get('song_name')}' from queue not found in all_songs.")

        self.main_frame.current_playlist = new_indices
        if current_song_path and new_indices:
            try:
                current_original_idx = next(i for i, s in enumerate(self.main_frame.all_songs) if
                                            s['mp3_location'].lower() == current_song_path)
                self.main_frame.current_song_index = new_indices.index(current_original_idx)
            except (StopIteration, ValueError):
                self.main_frame.current_song_index = 0
        elif new_indices:
            self.main_frame.current_song_index = 0
        else:
            self.main_frame.current_song_index = -1
            self.main_frame.player.stop()
            self.update_info(None)

        current_songs_for_queue = [self.main_frame.all_songs[i] for i in self.main_frame.current_playlist if
                                   0 <= i < len(self.main_frame.all_songs)]
        self.queue_view.update_queue(current_songs_for_queue)

    def update_play_button_icon(self):
        if self.main_frame.player.isPlaying():
            self.play_button.setIcon(QIcon("icons/pause.png"))
        else:
            self.play_button.setIcon(QIcon("icons/play.png"))

    def play_pause(self):
        if not self.main_frame.all_songs:
            return
        player = self.main_frame.player
        if player.source().isEmpty():
            if self.main_frame.current_playlist and self.main_frame.current_song_index != -1:
                idx = self.main_frame.current_playlist[self.main_frame.current_song_index]
                self.main_frame.set_media(self.main_frame.all_songs[idx]["mp3_location"])
        elif player.isPlaying():
            player.pause()
        else:
            player.play()
        self.update_play_button_icon()

    def next_song(self):
        if not self.main_frame.current_playlist:
            return
        count = len(self.main_frame.current_playlist)
        if count == 0:
            return

        if self.main_frame.play_mode == "shuffle":
            if count > 1:
                self.main_frame.current_song_index = choice(
                    [i for i in range(count) if i != self.main_frame.current_song_index])
            else:
                self.main_frame.current_song_index = 0
        else:
            self.main_frame.current_song_index = (self.main_frame.current_song_index + 1) % count

        actual_idx = self.main_frame.current_playlist[self.main_frame.current_song_index]
        self.main_frame.set_media(self.main_frame.all_songs[actual_idx]["mp3_location"])

    def prev_song(self):
        if not self.main_frame.current_playlist:
            return
        count = len(self.main_frame.current_playlist)
        if count == 0:
            return

        self.main_frame.current_song_index = (self.main_frame.current_song_index - 1 + count) % count
        actual_idx = self.main_frame.current_playlist[self.main_frame.current_song_index]
        self.main_frame.set_media(self.main_frame.all_songs[actual_idx]["mp3_location"])

    def set_position(self, position):
        self.main_frame.player.setPosition(position * 1000)

    def update_player_ui(self):
        player = self.main_frame.player
        duration, position = player.duration(), player.position()
        if duration > 0:
            total_sec, current_sec = duration // 1000, position // 1000
            if not self.slider.isSliderDown():
                self.slider.setRange(0, total_sec)
                self.slider.setValue(current_sec)
            self.current_time.setText(f"{current_sec // 60}:{current_sec % 60:02d}")
            self.total_time.setText(f"{total_sec // 60}:{total_sec % 60:02d}")
        else:
            self.slider.setRange(0, 0)
            self.slider.setValue(0)
            self.current_time.setText("0:00")
            self.total_time.setText("0:00")

    def cycle_play_mode(self):
        self.current_mode_index = (self.current_mode_index + 1) % len(self.play_modes)
        mode, icon = self.play_modes[self.current_mode_index]
        self.play_mode_button.setIcon(QIcon(icon))
        self.play_mode_button.setToolTip(mode.replace("_", " ").title())
        self.main_frame.play_mode = mode

    def show_lyrics(self):
        self.main_frame.show_frame(self.main_frame.lyrics_view)

    def open_timer_dialog(self):
        if not self.timer_dialog:
            self.timer_dialog = CustomTimerDialog(self)
            self.timer_dialog.timerStarted.connect(self.start_sleep_timer)
            self.timer_dialog.timerStopped.connect(self.stop_sleep_timer_actions)
        self.timer_dialog.show()
        self.timer_dialog.activateWindow()

    def start_sleep_timer(self, time_qtime):
        self.remaining_time = time_qtime
        self.sleep_timer_qtimer.start(1000)
        self.timer_button.setIcon(QIcon("icons/hourglass.png"))
        self.timer_label.setText(f"Sleep in: {self.remaining_time.toString('hh:mm:ss')}")
        self.timer_label.show()

    def stop_sleep_timer_actions(self):
        self.sleep_timer_qtimer.stop()
        self.timer_button.setIcon(QIcon("icons/timer.png"))
        self.timer_label.hide()
        if self.timer_dialog and self.timer_dialog.timer.isActive():
            self.timer_dialog.stop_timer()

    def update_timer_display(self):
        if self.remaining_time == QTime(0, 0, 0):
            self.main_frame.player.pause()
            self.update_play_button_icon()
            self.stop_sleep_timer_actions()
        else:
            self.remaining_time = self.remaining_time.addSecs(-1)
            self.timer_label.setText(f"Sleep in: {self.remaining_time.toString('hh:mm:ss')}")

    def show_queue(self):
        current_songs = []
        if self.main_frame.current_playlist:
            current_songs = [self.main_frame.all_songs[i] for i in self.main_frame.current_playlist if
                             0 <= i < len(self.main_frame.all_songs)]
        self.queue_view.update_queue(current_songs)
        self.queue_view.show_queue()
