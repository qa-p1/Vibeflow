import json
import os
import re
import requests
import urllib.request
from PySide6.QtCore import Qt, QByteArray, QObject, Signal, QRunnable, QThreadPool, QUrl, Slot, QSize, QRectF
from PySide6.QtGui import QPixmap, QPixmapCache, QIcon, QPainter, QPainterPath, QColor, QLinearGradient, QBrush
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QScrollArea
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from yt_dlp import YoutubeDL
from frames.frame_functions.utils import create_button, name_label

# Initialize Spotipy
try:
    sp = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id="2658ededc64b43dab40216de5d6f2b71",
            client_secret="ce0ccaf83df34d3ea629a4938a36511c",
        )
    )
except Exception as e:
    print(f"Spotipy initialization error: {e}")
    sp = None


class SearchResultCardWidget(QWidget):
    """Card for search results with glassmorphism on hover."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedHeight(80)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.is_hovered = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 10, 10)
        painter.setClipPath(path)

        if self.is_hovered:
            # Stronger glassmorphism effect on hover
            background_color = QColor(255, 255, 255, 25)
            painter.fillRect(self.rect(), background_color)

            # Subtle gradient
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, QColor(255, 255, 255, 15))
            gradient.setColorAt(1, QColor(0, 0, 0, 10))
            painter.fillRect(self.rect(), QBrush(gradient))

            # Border
            painter.setClipping(False)
            painter.setPen(QColor(255, 255, 255, 60))
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 10, 10)
        else:
            # Transparent background when not hovered
            painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        super().paintEvent(event)

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)


class ImageDownloader(QRunnable):
    class Signals(QObject):
        finished = Signal(str, QPixmap)
        error = Signal(str)

    def __init__(self, url: str, item_identifier: str):
        super().__init__()
        self.url = url
        self.item_identifier = item_identifier
        self.signals = self.Signals()

    def run(self):
        try:
            if not self.url:
                self.signals.error.emit(f"No URL for {self.item_identifier}")
                return
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            pixmap = QPixmap()
            if pixmap.loadFromData(QByteArray(response.content)):
                self.signals.finished.emit(self.url, pixmap)
            else:
                self.signals.error.emit(f"Failed to load image data for {self.url}")
        except Exception as e:
            self.signals.error.emit(str(e))


def sanitize_filename(filename):
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename.replace(' ', '_')
    filename = ''.join(char for char in filename if ord(char) < 128)
    return filename[:200]


class SongDownloader(QRunnable):
    class Signals(QObject):
        # MODIFIED: Signal now emits a dictionary and the original UI index
        finished = Signal(dict, int)
        error = Signal(str, int)
        progress = Signal(str, int)

    def __init__(self, track_info, ui_index, download_path):
        super().__init__()
        self.track_info = track_info
        self.ui_index = ui_index
        self.download_path = download_path
        self.signals = self.Signals()

    @Slot()
    def run(self):
        try:
            # This part is the same as before
            song_name = self.track_info["name"]
            artist_name = self.track_info["artists"][0]["name"]
            track_id = self.track_info.get("id", song_name + artist_name)
            artist_id = self.track_info['artists'][0]['id']
            safe_fb = sanitize_filename(f"{song_name}_{artist_name}")
            cover_url = self.track_info["album"]["images"][0]["url"] if self.track_info["album"]["images"] else None
            cover_path = os.path.join(self.download_path, f"{safe_fb}.png")
            mp3_path = os.path.join(self.download_path, f"{safe_fb}.mp3")
            lrc_path = os.path.join(self.download_path, f"{safe_fb}.lrc")

            if cover_url:
                try:
                    urllib.request.urlretrieve(cover_url, cover_path)
                    self.signals.progress.emit("Cover downloaded", self.ui_index)
                except:
                    self.signals.progress.emit("Cover download failed", self.ui_index)

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': mp3_path,
                'noplaylist': True,
                'no_warnings': True,
                'default_search': 'ytsearch1',
                'quiet': True
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"{song_name} {artist_name} audio"])
                self.signals.progress.emit("MP3 downloaded", self.ui_index)

            try:
                l_song, l_artist = urllib.parse.quote_plus(song_name), urllib.parse.quote_plus(artist_name)
                lyrics_url = f"https://lrclib.net/api/search?track_name={l_song}&artist_name={l_artist}"
                resp = requests.get(lyrics_url, timeout=10)
                resp.raise_for_status()
                lyrics_data = resp.json()
                lyrics_txt = lyrics_data[0].get('syncedLyrics') or lyrics_data[0].get('plainLyrics') if lyrics_data and lyrics_data[0] else None
                with open(lrc_path, 'w', encoding='utf-8') as f:
                    f.write(lyrics_txt or "")
                self.signals.progress.emit("Lyrics fetched" if lyrics_txt else "No lyrics", self.ui_index)
            except:
                open(lrc_path, 'w').close()
                self.signals.progress.emit("Lyrics fetch error", self.ui_index)

            # --- MODIFICATION START ---
            # Construct the final song dictionary here INSIDE the worker
            new_song_dict = {
                "song_name": song_name,
                "artist": artist_name,
                "mp3_location": mp3_path,
                "cover_location": cover_path if os.path.exists(cover_path) else "icons/default-image.png",
                "lyrics_location": lrc_path if os.path.exists(lrc_path) else "",
                "id": track_id,
                "artist_id": artist_id
            }

            # Emit the complete dictionary and the UI index
            self.signals.finished.emit(new_song_dict, self.ui_index)
            # --- MODIFICATION END ---
        except Exception as e:
            self.signals.error.emit(str(e), self.ui_index)


class SearchFrame(QWidget):
    def __init__(self, parent=None, back_callback=None):
        super().__init__(parent)
        self.main_frame = parent
        self.back_callback = back_callback
        self.active_downloads = {}
        self.preview_buttons = {}
        self.download_buttons = {}
        self.result_cards = []
        self.search_results = []
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(5)
        QPixmapCache.setCacheLimit(20 * 1024 * 1024)
        self.preview_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.preview_player.setAudioOutput(self.audio_output)
        self.currently_playing_preview_idx = -1
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        self.setStyleSheet("background: transparent;")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 15, 20, 15)
        self.main_layout.setSpacing(15)
        print(self.main_frame.width())
        # --- Header ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        back_button = create_button("icons/back-arrow.png", self.go_back, 24)
        header_layout.addWidget(back_button)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search for songs, artists...")
        self.search_box.returnPressed.connect(self.start_search)
        self.search_box.setFixedHeight(45)
        self.search_box.setStyleSheet("""
            QLineEdit {
                font-size: 16px;
                color: #e0e0e0;
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 22px;
                padding: 0 20px;
            }
            QLineEdit:focus {
                border-color: rgba(255, 255, 255, 0.5);
            }
        """)
        header_layout.addWidget(self.search_box, 1)

        self.main_layout.addLayout(header_layout)

        # --- Results Area ---
        self.results_scroll_area = QScrollArea()
        self.results_scroll_area.setWidgetResizable(True)
        self.results_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.results_scroll_area.setStyleSheet("background: transparent; border: none;")

        self.results_container = QWidget()
        self.results_container.setStyleSheet("background: transparent;")
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 5, 0, 5)
        self.results_layout.setSpacing(8)
        self.results_layout.setAlignment(Qt.AlignTop)

        self.status_label = QLabel("Search for music on Spotify.")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; color: #a0a0a0; background: transparent; padding-top: 50px;")
        self.results_layout.addWidget(self.status_label)

        self.results_scroll_area.setWidget(self.results_container)
        self.main_layout.addWidget(self.results_scroll_area)

    def go_back(self):
        self.preview_player.stop()
        self.clear_results()
        self.search_box.clear()
        if self.back_callback:
            self.back_callback()

    def connect_signals(self):
        self.preview_player.playbackStateChanged.connect(self.on_preview_playback_state_changed)
        self.preview_player.mediaStatusChanged.connect(self.on_preview_media_status_changed)
        self.preview_player.errorOccurred.connect(self.on_preview_player_error)

    def on_preview_player_error(self, error):
        idx = self.currently_playing_preview_idx
        if idx != -1 and idx in self.preview_buttons:
            self.preview_buttons[idx].setIcon(QIcon("icons/play.png"))
            self.preview_buttons[idx].setToolTip("Preview (Error)")
        self.currently_playing_preview_idx = -1

    def on_preview_playback_state_changed(self, state):
        idx = self.currently_playing_preview_idx
        if idx != -1 and idx in self.preview_buttons:
            button = self.preview_buttons[idx]
            if state == QMediaPlayer.PlayingState:
                button.setIcon(QIcon("icons/pause.png"))
                button.setToolTip("Pause Preview")
            else:
                button.setIcon(QIcon("icons/play.png"))
                button.setToolTip("Play Preview")

    def on_preview_media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            idx = self.currently_playing_preview_idx
            if idx != -1 and idx in self.preview_buttons:
                self.preview_buttons[idx].setIcon(QIcon("icons/play.png"))
            self.currently_playing_preview_idx = -1

    def start_search(self):
        term = self.search_box.text().strip()
        if not term:
            self.clear_results()
            self.status_label.setText("Please enter a search term.")
            self.status_label.show()
            return
        if not sp:
            self.clear_results()
            self.status_label.setText("Spotify service not available.")
            self.status_label.show()
            return

        self.clear_results()
        self.status_label.setText("Searching...")
        self.status_label.show()

        try:
            data = sp.search(q=term, limit=20, type="track")
            if data and data["tracks"]["items"]:
                self.status_label.hide()
                self.search_results = data["tracks"]["items"]
                for idx, track_data in enumerate(self.search_results):
                    card = self.create_result_card(track_data, idx)
                    self.results_layout.addWidget(card)
                    self.result_cards.append(card)
            else:
                self.status_label.setText(f"No results found for '{term}'.")
                self.status_label.show()
        except Exception as e:
            self.status_label.setText(f"Search failed: {e}")
            self.status_label.show()

    def create_result_card(self, track_data, ui_index):
        card = SearchResultCardWidget(self)
        card.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        art_label = QLabel()
        art_label.setFixedSize(60, 60)
        art_label.setStyleSheet("background: transparent; border-radius: 8px;")
        art_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(art_label)

        cover_url = track_data["album"]["images"][0]["url"] if track_data["album"]["images"] else None
        if cover_url:
            self.load_image_async(cover_url, art_label, QSize(60, 60), track_data.get("id", str(ui_index)))
        else:
            default_pixmap = QPixmap("icons/default-image.png").scaled(60, 60, Qt.KeepAspectRatio,
                                                                       Qt.SmoothTransformation)
            art_label.setPixmap(self.round_pixmap(default_pixmap, 8))

        text_widget = QWidget()
        text_widget.setStyleSheet("background: transparent;")
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        title_label = name_label(track_data.get('name', 'N/A'))
        title_label.setFixedWidth(100)
        title_label.setStyleSheet("color: #e0e0e0; font-size: 15px; font-weight: 500; background: transparent;")

        artist_label = name_label(track_data['artists'][0]['name'] if track_data['artists'] else 'N/A')
        artist_label.setStyleSheet("color: #a0a0a0; font-size: 13px; background: transparent;")

        title_label.setToolTip(track_data.get('name', 'N/A'))
        artist_label.setToolTip(track_data['artists'][0]['name'] if track_data['artists'] else 'N/A')

        text_layout.addWidget(title_label)
        text_layout.addWidget(artist_label)
        text_layout.addStretch()
        layout.addWidget(text_widget, 1)

        actions_widget = QWidget()
        actions_widget.setStyleSheet("background: transparent;")
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(10)

        button_style = """
            QPushButton { background: transparent; border-radius: 16px; }
            QPushButton:hover { background-color: rgba(0,0,0,0.2); }
        """
        preview_btn = create_button("icons/play.png", lambda: self.play_preview(track_data, ui_index), 32)
        preview_btn.setToolTip("Play Preview")
        preview_btn.setStyleSheet(button_style)
        self.preview_buttons[ui_index] = preview_btn

        download_btn = create_button("icons/download.png", lambda: self.initiate_download(track_data, ui_index), 28)
        download_btn.setStyleSheet(button_style)
        self.download_buttons[ui_index] = download_btn

        track_id = track_data.get('id')
        print(track_id, self.main_frame.get_song_index_by_id(track_id))
        if track_id and self.main_frame.get_song_index_by_id(track_id) is not None:
            download_btn.setIcon(QIcon("icons/complete.png"))
            download_btn.setEnabled(False)
            download_btn.setToolTip("Already in library")
            self.active_downloads[ui_index] = "completed"
        else:
            download_btn.setToolTip("Download")

        actions_layout.addWidget(preview_btn)
        actions_layout.addWidget(download_btn)
        layout.addWidget(actions_widget)

        return card

    def clear_results(self):
        self.preview_player.stop()
        self.currently_playing_preview_idx = -1

        for card in self.result_cards:
            card.deleteLater()
        self.result_cards.clear()

        # Remove only the result cards, not the status label
        for i in range(self.results_layout.count() - 1, 0, -1):  # Start from end, skip index 0 (status_label)
            item = self.results_layout.takeAt(i)
            if widget := item.widget():
                widget.deleteLater()

        self.status_label.setText("Search for music on Spotify.")
        self.status_label.show()

        self.preview_buttons.clear()
        self.download_buttons.clear()
        self.active_downloads.clear()
        self.search_results.clear()

    def round_pixmap(self, pixmap, radius):
        if pixmap.isNull(): return QPixmap()
        rounded = QPixmap(pixmap.size())
        rounded.fill(Qt.transparent)
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(rounded.rect()), radius, radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        return rounded

    def load_image_async(self, url, label, size, item_id):
        cached = QPixmapCache.find(url)
        if cached:
            label.setPixmap(self.round_pixmap(cached.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation), 8))
            return

        downloader = ImageDownloader(url, item_id)
        downloader.signals.finished.connect(lambda u, p: self.update_image_on_label(u, p, label, size))
        downloader.signals.error.connect(lambda err: print(f"Image download error for {item_id}: {err}"))
        self.threadpool.start(downloader)

    def update_image_on_label(self, url, pixmap, label, size):
        if not pixmap.isNull():
            scaled = pixmap.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(self.round_pixmap(scaled, 8))
            QPixmapCache.insert(url, pixmap)
        else:
            default_pixmap = QPixmap("icons/default-image.png").scaled(size, Qt.KeepAspectRatio,
                                                                       Qt.SmoothTransformation)
            label.setPixmap(self.round_pixmap(default_pixmap, 8))

    def play_preview(self, track_data, ui_index):
        if self.main_frame.player.playbackState() == QMediaPlayer.PlayingState:
            self.main_frame.player.pause()

        preview_url = track_data.get('preview_url')
        if self.currently_playing_preview_idx == ui_index:
            if self.preview_player.playbackState() == QMediaPlayer.PlayingState:
                self.preview_player.pause()
            elif self.preview_player.playbackState() == QMediaPlayer.PausedState:
                self.preview_player.play()
            return

        self.preview_player.stop()
        if self.currently_playing_preview_idx != -1 and self.currently_playing_preview_idx in self.preview_buttons:
            self.preview_buttons[self.currently_playing_preview_idx].setIcon(QIcon("icons/play.png"))

        self.currently_playing_preview_idx = ui_index

        if preview_url:
            self.preview_player.setSource(QUrl(preview_url))
            self.preview_player.play()
        else:
            if ui_index in self.preview_buttons:
                self.preview_buttons[ui_index].setIcon(QIcon("icons/no-preview.png"))
                self.preview_buttons[ui_index].setToolTip("Preview N/A")
                self.preview_buttons[ui_index].setEnabled(False)
            self.currently_playing_preview_idx = -1

    def initiate_download(self, track_data, ui_index):
        if ui_index in self.active_downloads and self.active_downloads[ui_index] in ["downloading", "completed"]:
            return

        track_id = track_data.get('id')
        if track_id and self.main_frame.get_song_index_by_id(track_id) is not None:
            if ui_index in self.download_buttons:
                self.download_buttons[ui_index].setIcon(QIcon("icons/complete.png"))
                self.download_buttons[ui_index].setEnabled(False)
                self.download_buttons[ui_index].setToolTip("Already in library")
            return

        data_json_path = self.main_frame.get_data_file_path()
        try:
            with open(data_json_path, "r") as f:
                data = json.load(f)
            download_path = data.get("Settings", {}).get("download_path")
            if not download_path or not os.path.isdir(download_path):
                return
        except:
            return

        os.makedirs(download_path, exist_ok=True)

        worker = SongDownloader(track_data, ui_index, download_path) # Renamed
        worker.signals.finished.connect(self.on_download_complete)
        worker.signals.error.connect(self.on_download_error)
        worker.signals.progress.connect(self.on_download_progress)

        self.threadpool.start(worker)
        self.active_downloads[ui_index] = "downloading"

        if ui_index in self.download_buttons:
            self.download_buttons[ui_index].setIcon(QIcon("icons/loading.png"))
            self.download_buttons[ui_index].setEnabled(False)
            self.download_buttons[ui_index].setToolTip("Downloading...")

    def on_download_progress(self, message, ui_index):
        if ui_index in self.download_buttons:
            self.download_buttons[ui_index].setToolTip(message)

    def on_download_complete(self, new_song_info, ui_index):
        self.active_downloads[ui_index] = "completed"

        if ui_index in self.download_buttons:
            self.download_buttons[ui_index].setIcon(QIcon("icons/complete.png"))
            self.download_buttons[ui_index].setEnabled(False)
            self.download_buttons[ui_index].setToolTip("Download Complete")

        data_json_path = self.main_frame.get_data_file_path()
        try:
            with open(data_json_path, "r+") as f:
                data = json.load(f)

                # Check if song already exists (double-check)
                if any(s.get("id") == new_song_info["id"] for s in data["All Songs"]):
                    return

                data["All Songs"].append(new_song_info)
                new_idx = len(data["All Songs"]) - 1
                if "All songs" not in data["Playlists"]:
                    data["Playlists"]["All songs"] = {"songs": [], "playlist_cover": "auto"}
                data["Playlists"]["All songs"]["songs"].append(new_idx)

                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=4)
        except Exception:
            if ui_index in self.download_buttons:
                self.download_buttons[ui_index].setIcon(QIcon("icons/download-error.png"))
                self.download_buttons[ui_index].setEnabled(True)
                self.download_buttons[ui_index].setToolTip("Error saving. Retry?")
            return

        self.main_frame.load_data()
        self.main_frame.rebuild_song_info_lookup()
        self.main_frame.home_screen_frame.display_playlists()

    def on_download_error(self, error_message, ui_index):
        self.active_downloads[ui_index] = "error"
        if ui_index in self.download_buttons:
            self.download_buttons[ui_index].setIcon(QIcon("icons/download-error.png"))
            self.download_buttons[ui_index].setEnabled(True)
            self.download_buttons[ui_index].setToolTip(f"Error. Retry?")
