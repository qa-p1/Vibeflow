import json
import os
import sys
import time
from random import randint
from PySide6.QtGui import QPainter, QPixmap, QFontDatabase, QImage, QPainterPath, QDragEnterEvent, \
    QDropEvent, QIcon
import asyncio
from frames.mini_player import MiniPlayer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QWidget, QFrame, QScrollArea, QDialog, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, QUrl, QRectF, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from frames.player_frame import PlayerFrame
from frames.search_frame import SearchFrame
from frames.bottom_player import BottomPlayer
from frames.lyrics_view import LyricsView
from frames.music_player_frame import ExpandedPlayerFrame
from frames.frame_functions.playlist_functions import CreatePlaylistDialog, update_playlists_to_json, ImportPlaylistsDialog
from frames.frame_functions.utils import apply_hover_effect, name_label
from threading import Timer


class VibeFlow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.load_data()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.current_playlist = []
        self.current_song_index = 0
        self.url_to_song_info = {song["mp3_location"].lower(): song for song in self.all_songs}
        if self.settings['download_path'] == "" or None:
            self.ask_for_download_path()
            self.show()
        self.init_ui()
        self.setWindowIcon(QIcon("icons/vibeflow.ico"))
        self.setup_connections()
        self.play_mode = "repeat"
        self.mini_player = MiniPlayer(self)
        self.mini_player.hide()
        self.setStyleSheet("""
            QPushButton{font-family: Quicksand;}
            QLabel{font-family: Quicksand;}
        """)
        self.button_cooldowns = {}
        QFontDatabase.addApplicationFont("font.ttf")

    def get_data_file_path(self):
        app_data_dir = os.path.join(os.getenv('APPDATA'), 'VibeFlow Music')
        print(app_data_dir
              )
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir)
        return os.path.join(app_data_dir, 'data.json')

    def load_data(self):
        data_json_path = self.get_data_file_path()
        if not os.path.exists(data_json_path):
            with open(data_json_path, 'w') as f:
                default_data = {
                    "All Songs": [],
                    "Playlists": {
                        "All songs": {
                            "songs": [],
                            "playlist_cover": "auto"
                        }
                    },
                    "Settings": {
                        "download_path": ""
                    }
                }
                json.dump(default_data, f, indent=4)
                self.all_songs = default_data["All Songs"]
                self.playlists = default_data["Playlists"]
                self.settings = default_data["Settings"]
        else:
            with open(data_json_path) as f:
                data = json.load(f)
                self.all_songs = data.get("All Songs", [])
                self.playlists = data.get("Playlists", {})
                self.settings = data.get("Settings", {})

    def init_ui(self):
        self.setWindowTitle("VibeFlow Music")
        self.setFixedSize(1013, 652)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.addWidget(self.create_menu_frame())
        layout.addWidget(self.create_content_frame())
        if self.all_songs:
            song_info = {
                "song_name": self.all_songs[0]['song_name'],
                "artist": self.all_songs[0]["artist"],
                "cover_location": self.all_songs[0]["cover_location"],
                "mp3_location": self.all_songs[0]["mp3_location"],
                "lyrics_location": self.all_songs[0]["lyrics_location"]
            }
            self.bottom_player.update_info(song_info)
            self.music_player_frame.update_info(song_info)
            self.player.setSource(self.all_songs[0]["mp3_location"])
            self.current_playlist = self.playlists["All songs"]['songs']
            self.lyrics_view.set_lyrics(song_info['lyrics_location'])

    def create_menu_frame(self):
        menu_frame = QFrame()
        menu_layout = QVBoxLayout(menu_frame)
        menu_frame.setFixedWidth(self.width() * 0.27)

        app_title = QLabel("VibeFlow Music")
        app_title.setStyleSheet("""font-size: 32px; font-weight: 500;""")
        app_title.setAlignment(Qt.AlignCenter)
        menu_layout.addWidget(app_title)

        self.playlist_widget = QWidget(menu_frame)
        self.playlist_layout = QVBoxLayout(self.playlist_widget)
        self.playlist_widget.setLayout(self.playlist_layout)

        title_layout = QHBoxLayout(menu_frame)

        title_icon = QLabel()
        title_icon.setPixmap(
            QPixmap("icons/music-library.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title_icon.setFixedSize(30, 30)
        title_layout.addWidget(title_icon)
        title = QLabel("Library", self)
        title.setStyleSheet(
            """
            QLabel{
                font-size: 26px;
                color: #ffffff;
                font-weight: 200;
            }
            """
        )
        title.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title)

        title_layout.addStretch()

        import_playlist = QLabel()
        import_playlist.setPixmap(
            QPixmap("icons/import.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        import_playlist.setCursor(Qt.PointingHandCursor)
        import_playlist.setFixedSize(30, 30)
        import_playlist.mousePressEvent = lambda event: self.open_import_playlist_dialog()
        title_layout.addWidget(import_playlist, alignment=Qt.AlignBottom)

        new_playlist_icon = QLabel()
        new_playlist_icon.setPixmap(
            QPixmap("icons/plus.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        new_playlist_icon.setCursor(Qt.PointingHandCursor)
        new_playlist_icon.setFixedSize(30, 30)
        new_playlist_icon.mousePressEvent = lambda event: self.open_create_playlist_dialog()
        title_layout.addWidget(new_playlist_icon, alignment=Qt.AlignBottom)

        menu_layout.addLayout(title_layout)

        self.scrollarea = QScrollArea(self)
        self.scrollarea.setWidget(self.playlist_widget)
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        menu_layout.addWidget(self.scrollarea)

        QTimer.singleShot(0, self.run_async_tasks)

        buttons = [QPushButton(text) for text in ["Home", "Search"]]
        buttons[0].clicked.connect(lambda: self.show_frame(self.player_frame))
        buttons[1].clicked.connect(lambda: self.show_frame(self.search_frame))
        for i, button in enumerate(buttons):
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedWidth(250)
            menu_layout.addWidget(button, alignment=Qt.AlignCenter)

        menu_frame.setStyleSheet(self.get_menu_style())
        return menu_frame

    def ask_for_download_path(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly

        download_path = QFileDialog.getExistingDirectory(self, "Select Music Download Directory", options=options)

        if download_path:
            self.settings['download_path'] = download_path + '/'
            self.update_settings_in_json()
        else:
            QMessageBox.warning(self, "Waitttttt.....",
                                "You should select a download path for saving your music, shouldn't you??? Pick a proper one its important.")
            self.ask_for_download_path()

    async def generate_playlist_covers_async(self):
        try:
            for playlist in self.playlists:
                await asyncio.sleep(0)
                playlist_widget = self.create_playlist_widget(playlist)
                self.playlist_layout.addWidget(playlist_widget)
            self.playlist_layout.addStretch()
        except Exception as e:
            print(f"Error in generate_playlist_covers_async: {e}")
            raise

    def update_settings_in_json(self):
        data_json_path = self.get_data_file_path()
        with open(data_json_path, 'r') as file:
            data = json.load(file)

        data['Settings'] = self.settings

        with open(data_json_path, 'w') as file:
            json.dump(data, file, indent=4)

    def run_async_tasks(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.generate_playlist_covers_async())
        except Exception as e:
            self.display_playlists_sync()
        finally:
            loop.close()
            self.playlist_layout.update()

    def display_playlists_sync(self):
        try:
            while self.playlist_layout.count():
                item = self.playlist_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()

            for playlist in self.playlists:
                playlist_widget = self.create_playlist_widget(playlist)
                self.playlist_layout.addWidget(playlist_widget)
            self.playlist_layout.addStretch()
        except Exception as e:
            print(f"Error in display_playlists_sync: {e}")

    def create_playlist_widget(self, playlist):
        playlist_button_layout = QHBoxLayout()

        cover_image = QLabel()
        cover_pixmap = self.generate_playlist_cover(playlist, 60)
        cover_image.setPixmap(cover_pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        cover_image.setFixedSize(50, 50)
        playlist_button_layout.addWidget(cover_image)

        label = name_label()
        label.setText(playlist)
        label.setStyleSheet('font-size: 18px; font-weight: light;')
        playlist_button_layout.addWidget(label)

        playlist_widget = QWidget(self)
        playlist_widget.setLayout(playlist_button_layout)
        playlist_widget.setFixedWidth(220)
        playlist_widget.setFixedHeight(65)
        playlist_widget.setCursor(Qt.PointingHandCursor)
        playlist_widget.mousePressEvent = lambda event, p=playlist: self.playlist_selected(p)
        apply_hover_effect(playlist_widget, "background: #303030; border-radius: 8px;", "background:transparent;")

        if playlist != "All songs":
            playlist_widget.setAcceptDrops(True)
            playlist_widget.dragEnterEvent = lambda event, p=playlist: self.playlist_drag_enter(event, p)
            playlist_widget.dropEvent = lambda event, p=playlist: self.playlist_drop(event, p)

        return playlist_widget

    def playlist_drag_enter(self, event: QDragEnterEvent, playlist):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def playlist_drop(self, event: QDropEvent, playlist):
        song_index = int(event.mimeData().text())
        if song_index not in self.playlists[playlist]['songs']:
            self.playlists[playlist]['songs'].append(song_index)
            self.update_playlists_json()
            self.player_frame.setup_layout(self.player_frame.curr_playlist_name)
            QMessageBox.information(self, "Song Added", f"Song added to {playlist} playlist.")
        else:
            QMessageBox.information(self, "Song Already Present", f"This song is already in the {playlist} playlist.")

    def update_playlists_json(self):
        data_json_path = self.get_data_file_path()
        with open(data_json_path, 'r') as f:
            data = json.load(f)
        data['Playlists'] = self.playlists
        with open(data_json_path, 'w') as f:
            json.dump(data, f, indent=4)

    def create_content_frame(self):
        self.content_frame = QFrame()
        self.content_layout = QVBoxLayout(self.content_frame)

        self.player_frame = PlayerFrame(self)
        self.search_frame = SearchFrame(self)
        self.lyrics_view = LyricsView(self)
        self.music_player_frame = ExpandedPlayerFrame(self)

        for frame in [self.player_frame, self.search_frame, self.lyrics_view, self.music_player_frame]:
            self.content_layout.addWidget(frame)
            frame.hide()

        self.player_frame.show()

        self.bottom_player = BottomPlayer(self)
        self.bottom_player.mousePressEvent = lambda event: self.show_frame(self.music_player_frame)
        self.bottom_player.setFixedHeight(110)
        self.content_layout.addWidget(self.bottom_player)

        return self.content_frame

    def setup_connections(self):
        self.player.playbackStateChanged.connect(self.play_back_state)
        self.player.mediaStatusChanged.connect(self.media_status)
        self.player.sourceChanged.connect(self.source_change_trigger)

    def play_back_state(self):
        self.bottom_player.update_play_button_icon()
        self.music_player_frame.update_play_button_icon()
        if self.player.isPlaying():
            self.lyrics_view.start_lyrics_sync()
        else:
            self.lyrics_view.stop_lyrics_sync()

    def set_media(self, source):
        if source.lower() == self.player.source().toString().lower():
            self.player.pause() if self.player.isPlaying() else self.player.play()
        else:
            print(self.size())
            self.player.stop()
            time.sleep(0.1)
            self.player.setSource(QUrl(source))
            self.player.play()
            if self.player.isPlaying():
                self.lyrics_view.start_lyrics_sync()
            else:
                self.lyrics_view.stop_lyrics_sync()

    def media_status(self):
        if self.player.mediaStatus() == QMediaPlayer.EndOfMedia:
            if self.play_mode == "shuffle":
                self.current_song_index = randint(0, len(self.current_playlist) - 1)
                self.set_media(self.all_songs[self.current_playlist[self.current_song_index]]["mp3_location"])

            elif self.play_mode == "repeat":
                self.current_song_index = (self.current_song_index + 1) % len(self.current_playlist)
                self.set_media(self.all_songs[self.current_playlist[self.current_song_index]]["mp3_location"])

            elif self.play_mode == "repeat_one":
                if not hasattr(self, '_repeat_once_flag'):
                    self._repeat_once_flag = False

                if not self._repeat_once_flag:
                    self._repeat_once_flag = True
                    self.player.setPosition(0)
                    self.player.play()
                else:
                    self._repeat_once_flag = False
                    self.current_song_index = (self.current_song_index + 1) % len(self.current_playlist)
                    self.set_media(
                        self.all_songs[self.current_playlist[self.current_song_index]]["mp3_location"])

    def source_change_trigger(self):
        source = self.player.source().toString().lower()
        if source in self.url_to_song_info:
            song_info = self.url_to_song_info[source]
            print(song_info)
            self.bottom_player.update_info(song_info)
            self.music_player_frame.update_info(song_info)
            self.mini_player.set_background_image(song_info['cover_location'])
            if 'lyrics_location' in song_info:
                self.lyrics_view.set_lyrics(song_info['lyrics_location'])
                self.lyrics_view.start_lyrics_sync()
            else:
                self.lyrics_view.display_no_lyrics()

    def open_import_playlist_dialog(self):
        import_dialog = ImportPlaylistsDialog(self)
        import_dialog.exec()

    def open_mini_player(self):
        if self.all_songs:
            source = self.player.source().toString().lower()
            song_info = self.url_to_song_info[source]
            self.mini_player.show_mini(song_info['cover_location'])
        else:
            pass

    def open_create_playlist_dialog(self):
        create_playlist_dialog = CreatePlaylistDialog(self)
        if create_playlist_dialog.exec() == QDialog.Accepted:
            playlist_name, song_indexes, cover = create_playlist_dialog.get_playlist_info()
            if playlist_name and song_indexes and cover:
                self.playlists[playlist_name] = {}
                self.playlists[playlist_name]['songs'] = song_indexes
                self.playlists[playlist_name]['playlist_cover'] = cover
                update_playlists_to_json(self.get_data_file_path(), self.playlists)
                self.load_data()
                self.player_frame.playlists = self.playlists
                self.display_playlists_sync()
        else:
            pass

    def generate_playlist_cover(self, playlist_name, size):
        playlist_info = self.playlists[playlist_name]
        songs = playlist_info["songs"]
        cover_type = playlist_info["playlist_cover"]
        radius = 8

        def round_corners(pixmap):
            rounded = QPixmap(size, size)
            rounded.fill(Qt.transparent)
            cover_painter = QPainter(rounded)
            cover_painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(QRectF(0, 0, size, size), radius, radius)
            cover_painter.setClipPath(path)
            cover_painter.drawPixmap(0, 0, pixmap)
            cover_painter.end()
            return rounded

        if not songs:
            default_pixmap = QPixmap("icons/music.png").scaled(size, size, Qt.KeepAspectRatio,
                                                               Qt.SmoothTransformation)
            return round_corners(default_pixmap)

        if cover_type != "auto":
            custom_pixmap = QPixmap(cover_type).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            return round_corners(custom_pixmap)

        if len(songs) <= 3:
            cover_pixmap = QPixmap(self.all_songs[songs[0]]["cover_location"]).scaled(size, size, Qt.KeepAspectRatio,
                                                                                      Qt.SmoothTransformation)
        else:

            cover = QImage(size, size, QImage.Format_RGB888)
            painter = QPainter(cover)
            for i, song_index in enumerate(songs[:4]):
                img = QPixmap(self.all_songs[song_index]["cover_location"]).scaled(size // 2, size // 2,
                                                                                   Qt.KeepAspectRatio,
                                                                                   Qt.SmoothTransformation)
                painter.drawPixmap(i % 2 * size // 2, i // 2 * size // 2, img)
            painter.end()
            cover_pixmap = QPixmap.fromImage(cover)

        return round_corners(cover_pixmap)

    def playlist_selected(self, playlist_name):
        current_time = time.time()
        if playlist_name in self.button_cooldowns:
            if current_time - self.button_cooldowns[playlist_name] < 2:
                return
        self.button_cooldowns[playlist_name] = current_time
        self.player_frame.setup_layout(playlist_name)
        self.current_playlist = self.playlists[playlist_name]['songs']
        self.set_media(self.all_songs[self.current_playlist[0]]['mp3_location'])
        self.player.pause()
        curr = [self.all_songs[i] for i in self.current_playlist]
        self.music_player_frame.queue_view.update_queue(curr)
        Timer(2, lambda: self.button_cooldowns.pop(playlist_name, None)).start()

    def show_frame(self, frame):
        for f in [self.player_frame, self.search_frame, self.lyrics_view, self.music_player_frame]:
            f.hide()
        frame.show()

    @staticmethod
    def get_menu_style():
        return """
        QPushButton {
            font-size: 19px;
            color: white;
            background: #242525;
            border-radius: 8px;
            padding: 9px;
            margin: 5px;
            height: 28px;
        }
        """


def main():
    start = time.time()
    app = QApplication(sys.argv)
    app.setStyleSheet("""
QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
}

QMenuBar, QMenu, QToolBar {
    background-color: #1e1e1e;
    color: #ffffff;
}

QPushButton {
    background-color: #1e1e1e;
    color: #ffffff;
}

QPushButton:hover {
    background-color: #333333;
}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox, QDateEdit, QTimeEdit, QDateTimeEdit {
    background-color: #1e1e1e;
    color: #ffffff;
}

QFrame {
    background-color: #1e1e1e;
    color: #ffffff;
}

QScrollArea {
    background-color: #1e1e1e;
    color: #ffffff;
}

QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QStackedLayout, QSplitter, QTabWidget {
    background-color: #1e1e1e;
    color: #ffffff;
}

/* Table and List views */
QTableView, QTreeView, QListView, QTableWidget, QTreeWidget, QListWidget {
    background-color: #1e1e1e;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #2e2e2e;
    color: #ffffff;
}

QScrollBar:vertical, QScrollBar:horizontal {
    background-color: #1e1e1e;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background-color: #444444;
}

/* Tabs */
QTabBar::tab {
    background-color: #2e2e2e;
    color: #ffffff;
    border: 1px solid #444444;
    padding: 5px;
}

QTabBar::tab:selected {
    background-color: #333333;
}

QSlider::groove:horizontal {
    border: none;
    height: 4px;
    background: #444444; /* Groove background color */
    border-radius: 2px;
}

QSlider::groove:vertical {
    border: none;
    width: 4px;
    background: #444444; /* Groove background color */
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #00bfff; /* Handle color - cyan for visibility */
    border: none;
    width: 12px;
    height: 12px;
    margin: -4px 0; /* Center the handle on the groove */
    border-radius: 6px;
}

QSlider::handle:vertical {
    background: #00bfff; /* Handle color - cyan for visibility */
    border: none;
    width: 12px;
    height: 12px;
    margin: 0 -4px; /* Center the handle on the groove */
    border-radius: 6px;
}

QSlider::handle:hover {
    background: #1e90ff; /* Lighter blue when hovering */
}

QSlider::sub-page:horizontal, QSlider::sub-page:vertical {
    background: #00bfff; /* Filled part of the slider */
    border-radius: 2px;
}

QProgressBar {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #444444;
    text-align: center;
}
QLabel{
    background: none;
}""")
    window = VibeFlow()
    QTimer.singleShot(100, window.show)
    end_time = time.time()
    print(f"Startup time: {end_time - start:.2f} seconds")
    sys.exit(app.exec())


if __name__ == "__main__":
    asyncio.run(main())
