from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QVBoxLayout, 
                               QSlider, QPushButton, QSpacerItem, QSizePolicy)
from PySide6.QtGui import QPixmap, QIcon, QPainter, QFontMetrics
from PySide6.QtCore import Qt, QSize, QTimer, QUrl
from PySide6.QtMultimedia import QMediaPlayer
from frames.frame_functions.utils import create_button, name_label

class ResponsiveLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumWidth(50)

    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        text = self.text()
        rect = self.rect()

        if metrics.horizontalAdvance(text) > rect.width():
            elided = metrics.elidedText(text, Qt.ElideRight, rect.width())
            painter.drawText(rect, self.alignment(), elided)
        else:
            painter.drawText(rect, self.alignment(), text)

class BottomPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_frame = parent
        self.setup_ui()
        self.connect_signals()
        self.setContentsMargins(0, 0, 0, 0)

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.setCursor(Qt.PointingHandCursor)

        layout1 = QHBoxLayout()
        layout2 = QHBoxLayout()
        self.cover_image = QLabel(self)
        self.cover_image.setFixedSize(60, 60)
        self.cover_image.setPixmap(QPixmap("icons/default-image.png").scaled(60, 60))
        layout1.addWidget(self.cover_image)

        info_container = QVBoxLayout()
        self.song_title = ResponsiveLabel("Title")
        self.song_title.setStyleSheet('font-size: 18px;')
        self.artist_label = ResponsiveLabel("Artist")
        self.artist_label.setStyleSheet('font-size: 12px;')
        info_container.addWidget(self.song_title)
        info_container.addWidget(self.artist_label)
        layout1.addLayout(info_container)

        controls_layout = QHBoxLayout()
        self.prev_button = create_button("icons/previous.png", self.prev_song, 35)
        self.play_button = create_button("icons/play.png", self.play_pause, 35)
        self.next_button = create_button("icons/next.png", self.next_song, 35)
        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.next_button)
        layout1.addLayout(controls_layout)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.sliderMoved.connect(self.set_position)
        layout2.addWidget(self.slider)
        self.layout.addLayout(layout1)
        self.layout.addLayout(layout2)

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_slider)
        self.timer.start()

    def connect_signals(self):
        self.main_frame.player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.main_frame.player.playbackStateChanged.connect(self.update_play_button_icon)

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.LoadedMedia:
            source = self.main_frame.player.source().toString().lower()
            if source in self.main_frame.url_to_song_info:
                song_info = self.main_frame.url_to_song_info[source]
                self.update_info(song_info)

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

    def update_info(self, song_info):
        self.song_title.setText(song_info['song_name'])
        self.artist_label.setText(song_info['artist'])
        self.cover_image.setPixmap(QPixmap(song_info['cover_location']).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def set_position(self, position):
        self.main_frame.player.setPosition(position * 1000)

    def update_slider(self):
        if self.main_frame.player.duration() > 0:
            self.slider.setValue(self.main_frame.player.position() / 1000)
            self.slider.setRange(0, self.main_frame.player.duration() / 1000)

    def update_play_button_icon(self):
        if self.main_frame.player.isPlaying():
            self.play_button.setIcon(QIcon("icons/pause.png"))
        else:
            self.play_button.setIcon(QIcon("icons/play.png"))