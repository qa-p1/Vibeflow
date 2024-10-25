from random import choice
from PySide6.QtCore import Qt, QTimer, QTime, Signal, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QVBoxLayout, QSlider,
                               QPushButton, QDialog, QSpinBox, QFrame, QListWidgetItem,
                               QListWidget)

from frames.frame_functions.utils import create_button


class CustomTimerDialog(QDialog):
    timerStarted = Signal(QTime)
    timerStopped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Sleep Timer")
        self.setWindowModality(Qt.NonModal)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.setup_ui()
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowSystemMenuHint)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        time_layout = QHBoxLayout()
        self.hours = QSpinBox()
        self.minutes = QSpinBox()
        self.seconds = QSpinBox()

        for spinbox in (self.hours, self.minutes, self.seconds):
            spinbox.setRange(0, 59)
            spinbox.setWrapping(True)
            spinbox.setButtonSymbols(QSpinBox.PlusMinus)
            spinbox.setAlignment(Qt.AlignCenter)
            spinbox.setStyleSheet("""
                QSpinBox {
                    font-size: 24px;
                    background-color: #2e2e2e;
                    color: #ffffff;
                    border: 1px solid #3e3e3e;
                    border-radius: 5px;
                    padding: 5px;
                    min-width: 70px;
                }
                QSpinBox::up-button, QSpinBox::down-button {
                    width: 20px;
                    background-color: #3e3e3e;
                }
            """)

        self.hours.setRange(0, 23)

        time_layout.addWidget(self.hours)
        time_layout.addWidget(QLabel(":"))
        time_layout.addWidget(self.minutes)
        time_layout.addWidget(QLabel(":"))
        time_layout.addWidget(self.seconds)

        layout.addLayout(time_layout)

        self.start_stop_button = QPushButton("Start")
        self.start_stop_button.clicked.connect(self.toggle_timer)

        layout.addWidget(self.start_stop_button)
        self.hide_button = QPushButton("Minimize")
        self.hide_button.clicked.connect(self.hide)

        self.setStyleSheet("""
                        QPushButton {
                            background-color: #1e90ff;
                            color: white;
                            border: none;
                            padding: 5px 15px;
                            border-radius: 5px;
                            font-size: 18px;
                        }
                        QPushButton:hover {
                            background-color: #5599ff;
                        }
                    """)
        layout.addWidget(self.hide_button)

    def toggle_timer(self):
        if self.timer.isActive():
            self.stop_timer()
        else:
            self.start_timer()
            self.hide()

    def start_timer(self):
        self.hours.setReadOnly(True)
        self.minutes.setReadOnly(True)
        self.seconds.setReadOnly(True)
        if self.hours.value() == 0 and self.minutes.value() == 0 and self.seconds.value() == 0:
            return
        self.timer.start(1000)
        self.start_stop_button.setText("Stop")
        self.enable_spinboxes(False)
        self.timerStarted.emit(QTime(self.hours.value(), self.minutes.value(), self.seconds.value()))

    def stop_timer(self):
        self.hours.setReadOnly(False)
        self.minutes.setReadOnly(False)
        self.seconds.setReadOnly(False)
        self.timer.stop()
        self.start_stop_button.setText("Start")
        self.enable_spinboxes(True)
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

    def enable_spinboxes(self, enable):
        self.hours.setEnabled(enable)
        self.minutes.setEnabled(enable)
        self.seconds.setEnabled(enable)

    def closeEvent(self, event):
        self.stop_timer()
        super().closeEvent(event)


class QueueListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setDragDropMode(QListWidget.InternalMove)
        self.setAcceptDrops(True)

    def dropEvent(self, event):
        super().dropEvent(event)
        new_order = [self.item(i).data(Qt.UserRole) for i in range(self.count())]
        self.parent().parent().queueUpdated.emit(new_order)


class QueueView(QWidget):
    queueUpdated = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Widget)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setup_ui()
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.finished.connect(self.animation_finished)
        self.is_visible = False

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.frame = QFrame(self)
        self.frame.setObjectName("queueFrame")
        self.frame.setStyleSheet("""
            #queueFrame {
                background-color: #2e2e2e;
            }
        """)
        frame_layout = QVBoxLayout(self.frame)

        header_layout = QHBoxLayout()
        header_label = QLabel("Queue")
        header_label.setStyleSheet("font-size: 24px; font-weight: bold;background:none;")
        close_button = create_button('icons/minimiz.png', self.hide_queue,25)
        header_layout.addWidget(header_label, alignment=Qt.AlignCenter)
        header_layout.addStretch()
        header_layout.addWidget(close_button)

        self.queue_list = QueueListWidget()
        self.queue_list.setStyleSheet("""
            QListWidget {
                background-color: #2e2e2e;
                border: none;
                font-size: 18px;
                font-family: QuickSand;
                font-weight: 500;
            }
            QListWidget::item {
                background-color: #3e3e3e;
                color: #ffffff;
                border-radius: 8px;
                margin: 8px;
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #4e4e4e;
            }
        """)

        frame_layout.addLayout(header_layout)
        frame_layout.addWidget(self.queue_list)

        main_layout.addWidget(self.frame)

    def update_queue(self, playlist):
        self.queue_list.clear()

        for i, song in enumerate(playlist):
            item = QListWidgetItem(f"{i+1}.  {song['song_name']} - {song['artist']}")
            item.setData(Qt.UserRole, song)
            self.queue_list.addItem(item)

    def show_queue(self):
        if not self.is_visible:
            self.show()
            self.animateBottomUp()

    def animateBottomUp(self):
        start_rect = QRect(0, self.parent().height(), self.parent().width(), self.height())
        end_rect = QRect(0, self.parent().height() - self.height(), self.parent().width(), self.height())

        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()

    def hide_queue(self):
        if self.is_visible:
            start_rect = self.geometry()
            end_rect = QRect(0, self.parent().height(), self.parent().width(), self.height())

            self.animation.setStartValue(start_rect)
            self.animation.setEndValue(end_rect)
            self.animation.setEasingCurve(QEasingCurve.InCubic)
            self.animation.start()

    def animation_finished(self):
        if self.geometry().y() >= self.parent().height():
            self.hide()
            self.is_visible = False
        else:
            self.is_visible = True


class ExpandedPlayerFrame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_frame = parent
        self.setup_ui()
        self.play_modes = [
            ("repeat", "icons/repeat.png"),
            ("repeat_one", "icons/repeat-one.png"),
            ("shuffle", "icons/shuffle.png"),
        ]
        self.current_mode_index = 0
        self.sleep_timer = QTimer(self)
        self.sleep_timer.timeout.connect(self.update_timer_display)
        self.timer_dialog = None
        self.queue_view = QueueView(self)
        self.queue_view.queueUpdated.connect(self.update_current_playlist)
        self.queue_view.hide()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        self.large_cover = QLabel(self)
        self.large_cover.setFixedSize(200, 200)
        self.large_cover.setPixmap(
            QPixmap("icons/default-image.png").scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(self.large_cover, alignment=Qt.AlignCenter)

        self.song_title = QLabel("Title")
        self.song_title.setStyleSheet('font-size: 24px; font-weight: bold; color: #ffffff;; margin-top: 20px;')
        self.artist_label = QLabel("Artist")
        self.artist_label.setStyleSheet('font-size: 18px; color: #b3b3b3;')
        layout.addWidget(self.song_title, alignment=Qt.AlignCenter)
        layout.addWidget(self.artist_label, alignment=Qt.AlignCenter)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.sliderMoved.connect(self.set_position)
        layout.addWidget(self.slider)

        time_layout = QHBoxLayout()
        self.current_time = QLabel("0:00")
        self.total_time = QLabel("0:00")
        self.current_time.setStyleSheet('color: #b3b3b3;')
        self.total_time.setStyleSheet('color: #b3b3b3;')

        time_layout.addWidget(self.current_time)
        time_layout.addStretch(1)
        time_layout.addWidget(self.total_time)
        layout.addLayout(time_layout)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(20)
        self.add_to_playlist_button = create_button('icons/plus.png', self.show_lyrics, 35)
        self.play_mode_button = create_button("icons/repeat.png", self.cycle_play_mode, 40)
        self.prev_button = create_button("icons/previous.png", self.prev_song, 40)
        self.play_button = create_button("icons/play.png", self.play_pause, 60)
        self.next_button = create_button("icons/next.png", self.next_song, 40)
        self.lyrics_button = create_button("icons/lyrics.png", self.show_lyrics, 30)
        self.timer_button = create_button("icons/timer.png", self.open_timer_dialog, 30)
        self.queue_button = create_button("icons/queue.png", self.show_queue, 40)
        self.mini_player_open = create_button('icons/collapse.png', self.main_frame.open_mini_player, 40)
        controls_layout.addStretch(1)
        for button in [self.play_mode_button, self.timer_button, self.add_to_playlist_button, self.prev_button,
                       self.play_button, self.next_button, self.lyrics_button, self.queue_button,
                       self.mini_player_open]:
            controls_layout.addWidget(button)

        controls_layout.addStretch(1)
        layout.addLayout(controls_layout)
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_player_ui)
        self.timer.start()

        self.timer_label = QLabel()
        self.timer_label.setStyleSheet('color: #b3b3b3; font-size: 14px;')
        self.timer_label.hide()
        layout.addWidget(self.timer_label, alignment=Qt.AlignCenter)

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
            }
        """)

    def update_current_playlist(self, new_order):
        self.main_frame.current_playlist = [self.main_frame.all_songs.index(song) for song in new_order]

    def update_play_button_icon(self):
        if self.main_frame.player.isPlaying():
            self.play_button.setIcon(QIcon("icons/pause.png"))
        else:
            self.play_button.setIcon(QIcon("icons/play.png"))

    def update_info(self, song_info):
        self.song_title.setText(song_info['song_name'])
        self.artist_label.setText(song_info['artist'])
        self.large_cover.setPixmap(
            QPixmap(song_info['cover_location']).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def play_pause(self):
        if not self.main_frame.all_songs:
            return

        player = self.main_frame.player
        if player.source().isEmpty():
            self.main_frame.set_media(self.main_frame.all_songs[0]["mp3_location"])
            player.play()
        elif player.isPlaying():
            player.pause()
            self.play_button.setIcon(QIcon("icons/play.png"))
        else:
            player.play()
            self.play_button.setIcon(QIcon("icons/pause.png"))

    def next_song(self):
        if not self.main_frame.current_playlist:
            return

        if self.main_frame.play_mode == "shuffle":
            if len(self.main_frame.current_playlist) > 1:
                current_song = self.main_frame.current_playlist[self.main_frame.current_song_index]
                possible_next_songs = [song for song in self.main_frame.current_playlist if song != current_song]
                next_index = self.main_frame.current_playlist.index(choice(possible_next_songs))
            else:
                next_index = 0
        else:
            next_index = (self.main_frame.current_song_index + 1) % len(self.main_frame.current_playlist)

        self.main_frame.current_song_index = next_index
        next_song = self.main_frame.all_songs[self.main_frame.current_playlist[next_index]]
        self.main_frame.set_media(next_song["mp3_location"])
        self.update_info(next_song)

    def prev_song(self):
        if not self.main_frame.current_playlist:
            return

        self.main_frame.current_song_index = (self.main_frame.current_song_index - 1) % len(
            self.main_frame.current_playlist)
        self.main_frame.set_media(
            self.main_frame.all_songs[self.main_frame.current_playlist[self.main_frame.current_song_index]][
                "mp3_location"])

    def set_position(self, position):
        self.main_frame.player.setPosition(position * 1000)

    def update_player_ui(self):
        if self.main_frame.player.duration() > 0:
            self.slider.setValue(self.main_frame.player.position() / 1000)
            self.slider.setRange(0, self.main_frame.player.duration() / 1000)

        current = self.main_frame.player.position() // 1000
        total = self.main_frame.player.duration() // 1000
        self.current_time.setText(f"{current // 60}:{current % 60:02d}")
        self.total_time.setText(f"{total // 60}:{total % 60:02d}")

    def cycle_play_mode(self):
        self.current_mode_index = (self.current_mode_index + 1) % len(self.play_modes)
        mode, icon_path = self.play_modes[self.current_mode_index]
        self.play_mode_button.setIcon(QIcon(icon_path))
        self.play_mode_button.setToolTip(mode.replace("_", " ").title())
        self.main_frame.play_mode = mode

    def show_lyrics(self):
        self.main_frame.show_frame(self.main_frame.lyrics_view)

    def open_timer_dialog(self):
        if not self.timer_dialog:
            self.timer_dialog = CustomTimerDialog(self)
            self.timer_dialog.timerStarted.connect(self.start_timer)
            self.timer_dialog.timerStopped.connect(self.stop_timer)
        self.timer_dialog.show()

    def start_timer(self, time):
        self.remaining_time = time
        self.sleep_timer.start(1000)
        self.timer_button.setIcon(QIcon("icons/hourglass.png"))
        self.timer_label.hide()

    def stop_timer(self):
        self.sleep_timer.stop()
        self.timer_button.setIcon(QIcon("icons/timer.png"))
        self.timer_label.hide()
        if self.timer_dialog:
            self.timer_dialog.stop_timer()

    def update_timer_display(self):
        if self.remaining_time == QTime(0, 0, 0):
            self.stop_music()
            self.stop_timer()
        else:
            self.remaining_time = self.remaining_time.addSecs(-1)

    def stop_music(self):
        self.main_frame.player.pause()
        self.play_button.setIcon(QIcon("icons/play.png"))

    def show_queue(self):
        current_playlist = [self.main_frame.all_songs[i] for i in self.main_frame.current_playlist]
        self.queue_view.update_queue(current_playlist)
        self.queue_view.setGeometry(0, self.height(), self.width(), int(self.height()))
        self.queue_view.show_queue()
