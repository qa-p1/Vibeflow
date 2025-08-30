import json
import os
import sys
from random import randint
from frames.search_frame import SongDownloader
if sys.platform == "win32":
    try:
        from frames.frame_functions.smtc_handler import SMTCHandler
    except ImportError:
        SMTCHandler = None
from PySide6.QtGui import (QPainter, QPixmap, QFontDatabase, QImage, QPainterPath,
                           QIcon, QColor, QLinearGradient, QBrush)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QDialog, QMessageBox, QFileDialog,
    QStackedWidget, QGraphicsOpacityEffect, QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect
)
from PySide6.QtCore import Qt, QUrl, QRectF, QTimer, QPropertyAnimation, QEasingCurve, QSize, QParallelAnimationGroup
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from frames.frame_functions.shortcuts import ShortcutHandler
from frames.lyrics_view import LyricsView
from frames.music_player_frame import NowPlayingView
from frames.mini_player import MiniPlayer
from frames.home_screen_frame import HomeScreenFrame
from frames.frame_functions.playlist_functions import CreatePlaylistDialog, update_playlists_to_json, \
    ImportPlaylistsDialog, DownloadProgressDialog
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from groq import Groq
from frames.frame_functions.shortcut_guide import ShortcutGuideDialog

class BackgroundStackedWidget(QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setAttribute(Qt.WA_StyledBackground, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if (hasattr(self.main_window, 'background_pixmap') and
                not self.main_window.background_pixmap.isNull()):

            blurred_bg = self.main_window.create_blurred_background(
                self.main_window.background_pixmap, self.size())
            painter.drawPixmap(0, 0, blurred_bg)

            if (hasattr(self.main_window, 'dominant_colors') and
                    self.main_window.dominant_colors):
                gradient = QLinearGradient(0, 0, 0, self.height())

                color1_rgb = self.main_window.dominant_colors[0]
                color2_rgb = (self.main_window.dominant_colors[1]
                              if len(self.main_window.dominant_colors) > 1
                              else self.main_window.dominant_colors[0])

                color1 = QColor(*color1_rgb)
                color2 = QColor(*color2_rgb)

                color1.setAlpha(180)
                color2.setAlpha(120)

                gradient.setColorAt(0, color1)
                gradient.setColorAt(1, color2)

                painter.fillRect(self.rect(), QBrush(gradient))

            painter.fillRect(self.rect(), QColor(0, 0, 0, 80))
        else:
            painter.fillRect(self.rect(), QColor(20, 20, 20))


class VibeFlow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VibeFlow Music")
        self.sp = None
        self.groq_client = None
        self.shortcut_guide = None
        self.playlist_cover_cache = {}
        self.track_id_to_index_map = {}
        self.load_data()
        self.init_api_clients()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.smtc_handler = None

        self.current_playlist = []
        self.current_song_index = 0

        self.url_to_song_info = {}
        self.rebuild_song_info_lookup()

        self.is_home_screen_expanded = True
        if not self.settings.get('download_path'):
            self.ask_for_download_path()

        self.play_mode = "repeat"
        self.mini_player = MiniPlayer(self)
        self.mini_player.hide()
        self.download_queue = []
        self.is_downloading_playlist = False
        self.playlist_import_progress = {}
        self.init_ui()
        self.shortcut_handler = ShortcutHandler(self)
        self.setWindowIcon(QIcon("icons/vibeflow.ico"))
        self.setup_connections()
        QFontDatabase.addApplicationFont("font.ttf")

    def get_data_file_path(self):
        app_data_dir = os.path.join(os.getenv('APPDATA'), 'VibeFlow Music')
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir)
        return os.path.join(app_data_dir, 'data.json')

    def load_data(self):
        data_json_path = self.get_data_file_path()
        if not os.path.exists(data_json_path):
            with open(data_json_path, 'w') as f:
                default_data = {
                    "All Songs": [],
                    "Playlists": {"All songs": {"songs": [], "playlist_cover": "auto"}},
                    "Settings": {
                        "download_path": "",
                        "recently_played": [],
                        "groq_api_key": "",
                        "spotify_client_id": "",
                        "spotify_client_secret": ""
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
                self.playlists = data.get("Playlists", {"All songs": {"songs": [], "playlist_cover": "auto"}})
                if "All songs" not in self.playlists:
                    self.playlists["All songs"] = {"songs": list(range(len(self.all_songs))), "playlist_cover": "auto"}
                self.settings = data.get("Settings", {"download_path": "", "recently_played": []})
                self.settings = data.get("Settings", {})
                self.settings.setdefault("download_path", "")
                self.settings.setdefault("recently_played", [])
                self.settings.setdefault("groq_api_key", "")
                self.settings.setdefault("spotify_client_id", "")
                self.settings.setdefault("spotify_client_secret", "")

        if self.all_songs and "All songs" in self.playlists:
            valid_indices = list(range(len(self.all_songs)))
            for p_name, p_data in self.playlists.items():
                p_data['songs'] = [idx for idx in p_data.get('songs', []) if idx in valid_indices]
        self.track_id_to_index_map = {song.get('id'): i for i, song in enumerate(self.all_songs) if song.get('id')}

    def init_api_clients(self):
        """Initializes Spotify and Groq clients using keys from settings."""
        groq_key = self.settings.get('groq_api_key')
        if groq_key:
            try:
                self.groq_client = Groq(api_key=groq_key)
                print("Groq client initialized successfully.")
            except Exception as e:
                self.groq_client = None
                print(f"Failed to initialize Groq client: {e}")
        else:
            self.groq_client = None
            print("Groq API key not found in settings.")

        client_id = self.settings.get('spotify_client_id')
        client_secret = self.settings.get('spotify_client_secret')
        if client_id and client_secret:
            try:
                self.sp = spotipy.Spotify(
                    auth_manager=SpotifyClientCredentials(
                        client_id=client_id,
                        client_secret=client_secret,
                    )
                )
                self.sp.search('test', limit=1, type='track')
                print("Spotify client initialized successfully.")
            except Exception as e:
                self.sp = None
                print(f"Failed to initialize Spotify client: {e}")
        else:
            self.sp = None
            print("Spotify credentials not found in settings.")
    def init_ui(self):
        self.setMinimumSize(1280, 800)
        self.dominant_colors = []
        self.background_pixmap = QPixmap()
        self.current_background_pixmap = QPixmap()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.main_stack = BackgroundStackedWidget(self)

        self.main_view_widget = QWidget()
        self.main_view_widget.setStyleSheet("background: transparent;")

        self.main_view_layout = QHBoxLayout(self.main_view_widget)
        self.main_view_layout.setContentsMargins(0, 0, 0, 0)
        self.main_view_layout.setSpacing(0)

        self.now_playing_view = NowPlayingView(self)
        self.home_screen_frame = HomeScreenFrame(self)

        self.main_view_layout.addWidget(self.now_playing_view, 65)
        self.main_view_layout.addWidget(self.home_screen_frame, 35)

        self.lyrics_view = LyricsView(self)
        self.lyrics_view.setStyleSheet("background: transparent;")
        self.main_stack.addWidget(self.main_view_widget)
        self.main_stack.addWidget(self.lyrics_view)

        main_layout.addWidget(self.main_stack)

        if sys.platform == "win32" and SMTCHandler:
            try:
                self.smtc_handler = SMTCHandler(self)
                self.smtc_handler.playPauseRequested.connect(self.now_playing_view.play_pause)
                self.smtc_handler.nextRequested.connect(self.now_playing_view.next_song)
                self.smtc_handler.prevRequested.connect(self.now_playing_view.prev_song)
                print('yes')
            except Exception as e:
                print(f"Failed to initialize SMTCHandler: {e}")
        self.show_frame(self.main_view_widget, immediate=True)
        if self.all_songs:
            self.current_playlist = self.playlists.get("All songs", {}).get('songs', list(range(len(self.all_songs))))
            self.current_song_index = 0
            if self.current_playlist:
                song_info = self.all_songs[self.current_playlist[self.current_song_index]]
                self.now_playing_view.update_info(song_info)
                self.lyrics_view.set_lyrics(song_info.get('lyrics_location', ''))
                self.player.setSource(QUrl.fromLocalFile(song_info["mp3_location"]))
                self.mini_player.set_background_image(song_info['cover_location'])
                if self.smtc_handler:
                    self.smtc_handler.update_metadata(song_info)
            else:
                self.current_song_index = -1
                self.now_playing_view.update_info(None)
        else:
            self.current_playlist = []
            self.current_song_index = -1
            self.now_playing_view.update_info(None)

        self.home_screen_frame.display_playlists()

    def rebuild_song_info_lookup(self):
        """Rebuilds the URL-to-song-info dictionary consistently using the full URL string as the key."""
        self.url_to_song_info = {
            QUrl.fromLocalFile(song["mp3_location"]).toString().lower(): song for song in self.all_songs
        }

    def toggle_home_screen(self):
        animation_duration = 350

        self.home_screen_anim_group = QParallelAnimationGroup(self)

        max_anim = QPropertyAnimation(self.home_screen_frame, b"maximumWidth")
        max_anim.setDuration(animation_duration)
        max_anim.setEasingCurve(QEasingCurve.InOutQuad)

        min_anim = QPropertyAnimation(self.home_screen_frame, b"minimumWidth")
        min_anim.setDuration(animation_duration)
        min_anim.setEasingCurve(QEasingCurve.InOutQuad)

        self.home_screen_anim_group.addAnimation(max_anim)
        self.home_screen_anim_group.addAnimation(min_anim)

        if self.is_home_screen_expanded:
            current_width = self.home_screen_frame.width()
            max_anim.setStartValue(current_width)
            max_anim.setEndValue(0)
            min_anim.setStartValue(current_width)
            min_anim.setEndValue(0)

            self.home_screen_anim_group.finished.connect(self.home_screen_frame.hide)
        else:
            target_width = int(self.main_view_widget.width() * 0.35)

            self.home_screen_frame.setMinimumWidth(0)
            self.home_screen_frame.show()

            max_anim.setStartValue(0)
            max_anim.setEndValue(target_width)
            min_anim.setStartValue(0)
            min_anim.setEndValue(target_width)

            def on_finish():
                self.home_screen_frame.setMinimumWidth(0)
                self.home_screen_frame.setMaximumWidth(16777215)

            self.home_screen_anim_group.finished.connect(on_finish)

        self.home_screen_anim_group.start(QPropertyAnimation.DeleteWhenStopped)

        self.is_home_screen_expanded = not self.is_home_screen_expanded
        self.now_playing_view.update_menu_button_icon(self.is_home_screen_expanded)

    def create_blurred_background(self, pixmap, size):
        scaled_pixmap = pixmap.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        centered_pixmap = QPixmap(size)
        centered_pixmap.fill(Qt.transparent)

        painter = QPainter(centered_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        x_offset = (size.width() - scaled_pixmap.width()) // 2
        y_offset = (size.height() - scaled_pixmap.height()) // 2

        painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
        painter.end()

        scene = QGraphicsScene()
        pixmap_item = QGraphicsPixmapItem()
        pixmap_item.setPixmap(centered_pixmap)

        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(20)
        pixmap_item.setGraphicsEffect(blur_effect)
        scene.addItem(pixmap_item)

        blurred_image = QImage(size, QImage.Format_ARGB32_Premultiplied)
        blurred_image.fill(Qt.transparent)

        painter = QPainter(blurred_image)
        painter.setRenderHint(QPainter.Antialiasing)
        scene.render(painter, QRectF(blurred_image.rect()), QRectF(centered_pixmap.rect()))
        painter.end()

        return QPixmap.fromImage(blurred_image)

    def update_main_stack_background(self, pixmap):
        """Update the main_stack's background with the provided pixmap"""
        self.background_pixmap = pixmap
        self.main_stack.update()

    def play_song_from_sidebar(self, song_index_in_all_songs, playlist_name_context):
        self.current_playlist = self.playlists[playlist_name_context]['songs']
        try:
            self.current_song_index = self.current_playlist.index(song_index_in_all_songs)
        except ValueError:
            self.current_playlist = [song_index_in_all_songs]
            self.current_song_index = 0
        self.set_media(self.all_songs[song_index_in_all_songs]["mp3_location"])

    def ask_for_download_path(self):
        options = QFileDialog.Options() | QFileDialog.ShowDirsOnly
        path = QFileDialog.getExistingDirectory(self, "Select Music Download Directory", options=options)
        if path:
            self.settings['download_path'] = path
            self.update_settings_in_json()
        else:
            QMessageBox.warning(self, "Download Path Required", "Please select a directory to save your music.")
            self.ask_for_download_path()

    def update_settings_in_json(self):
        path = self.get_data_file_path()
        try:
            with open(path) as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        data['Settings'] = self.settings

        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    def setup_connections(self):
        self.player.playbackStateChanged.connect(self.play_back_state)
        self.player.mediaStatusChanged.connect(self.media_status)
        self.player.sourceChanged.connect(self.source_change_trigger)
        self.now_playing_view.backgroundChanged.connect(self.update_main_stack_background)
        self.player.playbackStateChanged.connect(self.update_smtc_playback_status)

    def update_smtc_playback_status(self, state):
        """Safe wrapper for SMTC playback status updates"""
        if self.smtc_handler:
            self.smtc_handler.update_playback_status(state)

    def play_back_state(self):
        self.now_playing_view.update_play_button_icon()
        if self.player.isPlaying():
            self.lyrics_view.start_lyrics_sync()
            if self.smtc_handler:
                self.smtc_handler.update_playback_status(self.player.playbackState())
        else:
            self.lyrics_view.stop_lyrics_sync()

    def set_media(self, source_str):
        url = QUrl.fromLocalFile(source_str) if os.path.exists(source_str) else QUrl(source_str)
        if url == self.player.source():
            if self.player.isPlaying():
                self.player.pause()
            else:
                self.player.play()
        else:
            self.player.stop()
            QTimer.singleShot(50, lambda: self._actually_set_media(url))

    def _actually_set_media(self, url):
        self.player.setSource(url)
        self.player.play()

    def media_status(self):
        if self.player.mediaStatus() == QMediaPlayer.EndOfMedia and self.current_playlist:
            if self.play_mode == "shuffle":
                if len(self.current_playlist) > 1:
                    new_idx = self.current_song_index
                    while new_idx == self.current_song_index:
                        new_idx = randint(0, len(self.current_playlist) - 1)
                    self.current_song_index = new_idx
                else:
                    self.current_song_index = 0
            elif self.play_mode == "repeat":
                self.current_song_index = (self.current_song_index + 1) % len(self.current_playlist)
            elif self.play_mode == "repeat_one":
                self.player.setPosition(0)
                self.player.play()
                return

            actual_idx = self.current_playlist[self.current_song_index]
            self.set_media(self.all_songs[actual_idx]["mp3_location"])

    def source_change_trigger(self):
        if self.player.source().isEmpty():
            return

        path = self.player.source().toString().lower()

        if path not in self.url_to_song_info:
            print(f"Path '{path}' not in song info lookup. Rebuilding.")
            self.rebuild_song_info_lookup()

        if path in self.url_to_song_info:
            song_info = self.url_to_song_info[path]
            self.now_playing_view.update_info(song_info)
            cover_pixmap = QPixmap(song_info.get('cover_location', 'icons/default-image.png'))
            if cover_pixmap.isNull():
                cover_pixmap = QPixmap("icons/default-image.png")
            self.background_pixmap = cover_pixmap
            self.dominant_colors = self.now_playing_view.get_dominant_colors(
                song_info.get('cover_location', 'icons/default-image.png'))
            self.mini_player.set_background_image(song_info['cover_location'])
            self.lyrics_view.set_lyrics(song_info.get('lyrics_location', ''))
            if self.smtc_handler:
                self.smtc_handler.update_metadata(song_info)
        else:
            print(f"Error: Song with path '{path}' still not found after rebuilding lookup table.")

    def get_song_index_by_id(self, track_id):
        """Returns the index of a song in all_songs if it exists, otherwise None."""
        return self.track_id_to_index_map.get(track_id)

    def open_import_playlist_dialog(self):
        dialog = ImportPlaylistsDialog(self)
        dialog.exec()
        self.home_screen_frame.display_playlists()

    def open_mini_player(self):
        if not self.all_songs:
            return
        source = self.player.source().toLocalFile().lower() if self.player.source().isLocalFile() else self.player.source().toString().lower()
        cover = self.url_to_song_info[source]['cover_location'] if source in self.url_to_song_info else \
            self.all_songs[0]['cover_location']
        self.mini_player.show_mini(cover)

    def open_create_playlist_dialog(self):
        dialog = CreatePlaylistDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name, indices, cover = dialog.get_playlist_info()
            if not name:
                QMessageBox.warning(self, "Invalid Name", "Playlist name cannot be empty.")
                return
            if name in self.playlists:
                QMessageBox.warning(self, "Playlist Exists", f"A playlist named '{name}' already exists.")
                return
            self.playlists[name] = {'songs': indices, 'playlist_cover': cover}
            update_playlists_to_json(self.get_data_file_path(), self.playlists)
            self.home_screen_frame.display_playlists()

    def find_existing_song_index(self, song_data):
        """
        Finds the index of an existing song.
        First checks by track ID, then falls back to checking by name and artist.
        """
        track_id = song_data.get('id')
        if track_id and not track_id.startswith('fallback_'):
            existing_index = self.get_song_index_by_id(track_id)
            if existing_index is not None:
                return existing_index

        try:
            song_name_to_check = song_data['name'].lower().strip()
            artist_name_to_check = song_data['artists'][0]['name'].lower().strip()

            for i, existing_song in enumerate(self.all_songs):
                existing_name = existing_song.get('song_name', '').lower().strip()
                existing_artist = existing_song.get('artist', '').lower().strip()
                if song_name_to_check == existing_name and artist_name_to_check == existing_artist:
                    return i
        except (KeyError, IndexError):
            pass

        return None

    def start_playlist_import(self, songs_to_download, playlist_name):
        if self.is_downloading_playlist:
            QMessageBox.information(self, "Import in Progress", "Another playlist import is already in progress.")
            return

        self.is_downloading_playlist = True
        progress_dialog = DownloadProgressDialog(playlist_name, len(songs_to_download), self)
        progress_dialog.populate_song_list(songs_to_download)

        self.playlist_import_progress = {
            "dialog": progress_dialog,
            "playlist_name": playlist_name,
            "songs_to_process": list(songs_to_download),
            "newly_added_indices": [],
            "failed_songs": []
        }

        progress_dialog.show()
        self.process_next_in_queue()

    def process_next_in_queue(self):
        if not self.playlist_import_progress["songs_to_process"]:
            self.finalize_playlist_import()
            return

        song_data = self.playlist_import_progress["songs_to_process"].pop(0)
        dialog = self.playlist_import_progress["dialog"]

        existing_index = self.find_existing_song_index(song_data)
        if existing_index is not None:
            self.playlist_import_progress["newly_added_indices"].append(existing_index)
            dialog.update_song_status(song_data['id'], "In Library", "#a9b1d6")
            QTimer.singleShot(50, self.process_next_in_queue)
            return

        dialog.update_song_status(song_data['id'], "Downloading...", "#e0e0e0")

        downloader = SongDownloader(song_data, -1, self.settings['download_path'])
        downloader.signals.finished.connect(
            lambda new_song, ui_idx, s=song_data: self.on_playlist_song_downloaded(s, new_song)
        )
        downloader.signals.error.connect(
            lambda error_msg, s=song_data: self.on_playlist_song_download_error(s, error_msg)
        )
        self.home_screen_frame.search_view_widget.threadpool.start(downloader)

    def on_playlist_song_downloaded(self, original_song_data, new_song_info):
        self.all_songs.append(new_song_info)
        new_song_index = len(self.all_songs) - 1

        self.track_id_to_index_map[new_song_info['id']] = new_song_index

        self.playlist_import_progress["newly_added_indices"].append(new_song_index)

        dialog = self.playlist_import_progress["dialog"]
        dialog.update_song_status(original_song_data['id'], "Downloaded", "#4ecdc4")

        self.process_next_in_queue()

    def on_playlist_song_download_error(self, original_song_data, error_msg):
        print(f"Failed to download {original_song_data['name']}: {error_msg}")
        self.playlist_import_progress["failed_songs"].append(original_song_data)

        dialog = self.playlist_import_progress["dialog"]
        dialog.update_song_status(original_song_data['id'], "Failed", "#ff6b6b")

        self.process_next_in_queue()

    def finalize_playlist_import(self):
        dialog = self.playlist_import_progress["dialog"]
        original_playlist_name = self.playlist_import_progress["playlist_name"]
        all_indices_for_new_playlist = self.playlist_import_progress["newly_added_indices"]

        if not all_indices_for_new_playlist:
            dialog.import_complete(original_playlist_name + " (Failed - No songs added)")
            self.is_downloading_playlist = False
            return

        unique_playlist_name = original_playlist_name
        counter = 1
        while unique_playlist_name in self.playlists:
            unique_playlist_name = f"{original_playlist_name} ({counter})"
            counter += 1

        self.playlists[unique_playlist_name] = {
            'songs': all_indices_for_new_playlist,
            'playlist_cover': 'auto'
        }

        if "All songs" in self.playlists:
            all_songs_playlist = self.playlists["All songs"]["songs"]
            genuinely_new_song_indices = [
                idx for idx in all_indices_for_new_playlist if idx not in all_songs_playlist
            ]
            all_songs_playlist.extend(genuinely_new_song_indices)

        self.save_all_data()
        self.rebuild_song_info_lookup()
        self.load_data()
        self.home_screen_frame.display_playlists()
        self.invalidate_playlist_cache(unique_playlist_name)

        dialog.import_complete(unique_playlist_name)
        self.is_downloading_playlist = False
        self.playlist_import_progress = {}

    def save_all_data(self):
        """Saves both 'All Songs' and 'Playlists' to the JSON file."""
        data_path = self.get_data_file_path()
        try:
            with open(data_path, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"Settings": self.settings}

        data['All Songs'] = self.all_songs
        data['Playlists'] = self.playlists

        with open(data_path, 'w') as f:
            json.dump(data, f, indent=4)

    def generate_playlist_cover(self, playlist_name, size):
        if playlist_name in self.playlist_cover_cache and self.playlist_cover_cache[playlist_name].size() == QSize(size,
                                                                                                                   size):
            return self.playlist_cover_cache[playlist_name]

        info = self.playlists.get(playlist_name, {})
        indices = info.get("songs", [])
        cover_type = info.get("playlist_cover", "auto")
        radius = 8

        def round_corners(pix):
            if pix.isNull():
                return QPixmap(size, size)
            scaled = pix.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            rounded = QPixmap(size, size)
            rounded.fill(Qt.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(QRectF(0, 0, size, size), radius, radius)
            painter.setClipPath(path)
            painter.drawPixmap((size - scaled.width()) / 2, (size - scaled.height()) / 2, scaled)
            painter.end()
            return rounded

        if not indices:
            final = round_corners(QPixmap("icons/music.png"))
            self.playlist_cover_cache[playlist_name] = final
            return final

        if cover_type != "auto" and os.path.exists(cover_type):
            final = round_corners(QPixmap(cover_type))
            self.playlist_cover_cache[playlist_name] = final
            return final

        covers = [self.all_songs[i]["cover_location"] for i in indices if
                  0 <= i < len(self.all_songs) and os.path.exists(self.all_songs[i]["cover_location"])]

        if not covers:
            final = round_corners(QPixmap("icons/music.png"))
            self.playlist_cover_cache[playlist_name] = final
            return final

        cover_pixmap = QPixmap(covers[0]) if len(covers) < 4 else self.create_mosaic_cover(covers, size)
        final = round_corners(cover_pixmap)
        self.playlist_cover_cache[playlist_name] = final
        return final

    def create_mosaic_cover(self, cover_paths, size):
        mosaic = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
        mosaic.fill(Qt.transparent)
        painter = QPainter(mosaic)
        painter.setRenderHint(QPainter.Antialiasing)
        half = size // 2
        for i, path in enumerate(cover_paths[:4]):
            pix = QPixmap(path).scaled(half, half, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x, y = (i % 2) * half, (i // 2) * half
            painter.drawPixmap(x + (half - pix.width()) / 2, y + (half - pix.height()) / 2, pix)
        painter.end()
        return QPixmap.fromImage(mosaic)

    def play_playlist(self, playlist_name):
        """Play all songs from the specified playlist"""
        if playlist_name not in self.playlists:
            return

        playlist_songs = self.playlists[playlist_name]['songs']
        if not playlist_songs:
            return

        self.current_playlist = playlist_songs.copy()
        self.current_song_index = 0

        first_song_idx = self.current_playlist[0]
        if 0 <= first_song_idx < len(self.all_songs):
            self.set_media(self.all_songs[first_song_idx]["mp3_location"])

    def add_playlist_to_queue(self, playlist_name):
        """Add all songs from playlist to the end of current queue"""
        if playlist_name not in self.playlists:
            return

        playlist_songs = self.playlists[playlist_name]['songs']
        if not playlist_songs:
            return

        if not self.current_playlist:
            self.current_playlist = playlist_songs.copy()
            self.current_song_index = 0
            return

        for song_idx in playlist_songs:
            if song_idx not in self.current_playlist:
                self.current_playlist.append(song_idx)

    def open_delete_playlist_dialog(self, playlist_name):
        """Show confirmation dialog for deleting a playlist"""
        from PySide6.QtWidgets import QMessageBox

        if playlist_name == "All songs":
            QMessageBox.warning(self, "Cannot Delete", "The 'All songs' playlist cannot be deleted.")
            return

        reply = QMessageBox.question(
            self,
            "Delete Playlist",
            f"Are you sure you want to delete the playlist '{playlist_name}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if playlist_name in self.playlists:
                del self.playlists[playlist_name]

                self.save_playlists_to_json()

                self.home_screen_frame.display_playlists()

                self.invalidate_playlist_cache(playlist_name)

    def play_song_next(self, song_index):
        """Add song to play next in queue (after current song)"""
        if not self.current_playlist or self.current_song_index < 0:
            self.current_playlist = [song_index]
            self.current_song_index = 0
            self.set_media(self.all_songs[song_index]["mp3_location"])
            return

        insert_position = self.current_song_index + 1
        if song_index not in self.current_playlist:
            self.current_playlist.insert(insert_position, song_index)
        else:
            self.current_playlist.remove(song_index)
            if self.current_playlist.index(song_index) < self.current_song_index:
                self.current_song_index -= 1
            self.current_playlist.insert(insert_position, song_index)

    def add_song_to_queue(self, song_index):
        """Add song to the end of current queue"""
        if not self.current_playlist:
            self.current_playlist = [song_index]
            self.current_song_index = 0
            self.set_media(self.all_songs[song_index]["mp3_location"])
            return

        if song_index not in self.current_playlist:
            self.current_playlist.append(song_index)

    def add_song_to_playlist(self, song_index, target_playlist_name):
        """Add a song to the specified playlist"""
        if target_playlist_name not in self.playlists:
            return

        playlist_songs = self.playlists[target_playlist_name]['songs']

        if song_index not in playlist_songs:
            playlist_songs.append(song_index)

            self.save_playlists_to_json()

            self.invalidate_playlist_cache(target_playlist_name)

    def save_playlists_to_json(self):
        """Save the current playlists to JSON file"""
        data_path = self.get_data_file_path()
        try:
            with open(data_path) as f:
                data = json.load(f)

            data['Playlists'] = self.playlists

            with open(data_path, 'w') as f:
                json.dump(data, f, indent=4)

        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error saving playlists: {e}")

    def show_shortcut_guide(self):
        """
        Creates (if needed) and shows the shortcut guide dialog.
        This is the single point of entry for showing the guide.
        """
        if self.shortcut_guide is None:
            self.shortcut_guide = ShortcutGuideDialog(self)

        self.shortcut_guide.exec()

    def show_frame(self, frame_to_show, immediate=False):
        if self.main_stack.currentWidget() == frame_to_show:
            return

        if immediate:
            self.main_stack.setCurrentWidget(frame_to_show)
            return

        self.opacity_effect = QGraphicsOpacityEffect(frame_to_show)
        frame_to_show.setGraphicsEffect(self.opacity_effect)

        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(250)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)

        def on_finish():
            if frame_to_show.graphicsEffect() == self.opacity_effect:
                frame_to_show.setGraphicsEffect(None)

        self.fade_animation.finished.connect(on_finish)

        self.main_stack.setCurrentWidget(frame_to_show)
        self.fade_animation.start(QPropertyAnimation.DeleteWhenStopped)

    def invalidate_playlist_cache(self, playlist_name):
        if playlist_name in self.playlist_cover_cache:
            del self.playlist_cover_cache[playlist_name]

    def keyPressEvent(self, event):
        """
        Overrides the default key press event to handle global shortcuts.
        Delegates the event to the ShortcutHandler.
        """
        if self.shortcut_handler.handle_key_press(event):
            return

        key = event.key()
        modifiers = event.modifiers()

        if modifiers == Qt.NoModifier and key in [
            Qt.Key_Space, Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right
        ]:
            event.accept()
            return

        super().keyPressEvent(event)

    def closeEvent(self, event):
        """Ensure the SMTC is cleaned up when the window closes."""
        if self.smtc_handler:
            self.smtc_handler.shutdown()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("""
            QWidget { background-color: #121212; color: #ffffff; font-family: Quicksand; }
            QPushButton { 
                font-family: Quicksand; 
                background-color: transparent; 
                border: none; 
                outline: none;
            }
            QPushButton:focus { 
                outline: none; 
                border: none;
            }
            QLabel { font-family: Quicksand; background: transparent; }
            QScrollArea { border: none; }
            QScrollBar:vertical { border: none; background: #1A1A1A; width: 8px; margin: 0; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #4A4A4A; min-height: 20px; border-radius: 4px; }
            QScrollBar::handle:vertical:hover { background: #5A5A5A; }

            /* Disable focus rectangles globally */
            *:focus {
                outline: none;
                border: none;
            }

            /* Specifically target any widgets that might show focus indicators */
            QWidget:focus {
                outline: none;
                border: none;
            }
        """)
    window = VibeFlow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
