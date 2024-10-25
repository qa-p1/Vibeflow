import json
import os
import urllib.request
import re
import requests
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QWidget, QMessageBox,
    QSpacerItem, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, QByteArray, QObject, Signal, QRunnable, QThreadPool, QUrl, Slot
from PySide6.QtGui import QPixmap, QPixmapCache, QIcon
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from yt_dlp import YoutubeDL
from frames.frame_functions.utils import create_button, apply_hover_effect, name_label
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id="baf2d72ae6054acf91dca4f10f8e3f2e",
        client_secret="aa9bbc0e087445a0a8799e676cd3ca5d",
    )
)


class ImageDownloader(QRunnable):
    class Signals(QObject):
        finished = Signal(str, QPixmap)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.signals = self.Signals()

    def run(self):
        try:
            response = requests.get(self.url)
            image_data = QByteArray(response.content)
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            self.signals.finished.emit(self.url, pixmap)
        except Exception as e:
            print(f"Error downloading {self.url}: {str(e)}")


def sanitize_filename(filename):
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.replace(' ', '_')
    filename = ''.join(char for char in filename if ord(char) < 128)
    return filename[:255]


class DownloadWorker(QRunnable):
    class Signals(QObject):
        finished = Signal(str, str, int)
        error = Signal(str)

    def __init__(self, track, index, download_path):
        super().__init__()
        self.track = track
        self.index = index
        self.download_path = download_path
        self.signals = self.Signals()

    @Slot()
    def run(self):
        try:
            song_name = self.track["name"]
            artist_name = self.track["artists"][0]["name"]
            safe_filename = sanitize_filename(f"{song_name} by {artist_name}")
            cover_image = self.track["album"]["images"][0]["url"]

            cover_path = os.path.join(self.download_path, f"{safe_filename}.png")
            mp3_path = os.path.join(self.download_path, f"{safe_filename}.mp3")
            lrc_path = os.path.join(self.download_path, f"{safe_filename}.lrc")

            urllib.request.urlretrieve(cover_image, cover_path)

            search_query = f"{song_name} {artist_name}"
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': mp3_path,
                'noplaylist': True,
            }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"ytsearch1:{search_query}"])

            song_name_for_search = urllib.parse.quote(song_name)
            artist_name_for_search = urllib.parse.quote(artist_name)
            lyrics_url = f"https://lrclib.net/api/search?track_name={song_name_for_search}&artist_name={artist_name_for_search}"
            response = requests.get(lyrics_url)
            if response.status_code == 200:
                lyrics_data = response.json()
                if lyrics_data and len(lyrics_data) > 0:
                    synced_lyrics = lyrics_data[0].get('syncedLyrics')
                    if synced_lyrics:
                        with open(lrc_path, 'w', encoding='utf-8') as lrc_file:
                            lrc_file.write(synced_lyrics)
                    else:
                        print(f"No synced lyrics found for {song_name} by {artist_name}")
                else:
                    print(f"No lyrics found for {song_name} by {artist_name}")
            else:
                print(f"Failed to fetch lyrics for {song_name} by {artist_name}")

            self.signals.finished.emit(song_name, artist_name, self.index)
        except Exception as e:
            self.signals.error.emit(str(e))


class SearchFrame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_frame = parent
        self.download_icon_label_list = []
        self.player_button_list = []
        self.threadpool = QThreadPool()
        self.setup_ui()
        self.curr_index = None

        self.preview_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.preview_player.setAudioOutput(self.audio_output)

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.setup_title()
        self.setup_search_bar()
        self.setup_results_area()

    def setup_title(self):
        title_text = QLabel("Search Your Songs Here")
        title_text.setAlignment(Qt.AlignCenter)
        title_text.setStyleSheet(
            "QLabel{font-size: 30px; color: #ffffff; margin-top: 20px; font-family: Quicksand;}"
        )
        self.layout.addWidget(title_text)

    def setup_search_bar(self):
        search_layout = QHBoxLayout()
        search_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.search_box = QLineEdit()
        self.search_box.returnPressed.connect(self.search_spotify)
        self.search_box.setFixedWidth(500)
        self.search_box.setPlaceholderText("Name of Song")
        self.search_box.setStyleSheet(
            "QLineEdit{font-size: 15px; color: #ffffff; background-color: transparent; "
            "border: 1px solid #fff; border-radius: 12px; padding: 8px; margin-top: 30px; font-family: Quicksand;}"
        )
        search_layout.addWidget(self.search_box)

        search_button = create_button("icons/search.png", self.search_spotify, 40)
        search_button.setStyleSheet(
            "QPushButton{background-color: transparent; margin-top: 30px; margin-left: 20px;}"
        )
        search_layout.addWidget(search_button)

        search_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.layout.addLayout(search_layout)

    def setup_results_area(self):
        self.results = QWidget()
        self.results_layout = QVBoxLayout(self.results)
        self.results_layout.setAlignment(Qt.AlignTop)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.layout.addWidget(self.scroll_area)
        self.scroll_area.setWidget(self.results)

    def search_spotify(self):
        term = self.search_box.text()
        if not term:
            return

        self.clear_results()
        self.results_layout.addWidget(QLabel("Search Results"))
        data = sp.search(q=term, limit=10, type="track")
        for idx, track in enumerate(data["tracks"]["items"]):
            print(track)
            self.add_result_item(idx, track)

    def clear_results(self):
        for i in reversed(range(self.results_layout.count())):
            item = self.results_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    layout = item.layout()
                    if layout is not None:
                        while layout.count():
                            child_item = layout.takeAt(0)
                            if child_item.widget():
                                child_item.widget().deleteLater()
                            elif child_item.layout():
                                self.clear_layout(child_item.layout())
                        self.results_layout.removeItem(item)
        self.preview_player.stop()
        self.curr_index = None
        if self.main_frame.player.playbackState() == QMediaPlayer.PausedState:
            self.main_frame.player.play()
        self.download_icon_label_list.clear()

    def load_pixmap_from_url(self, url):
        pixmap = QPixmapCache.find(url)
        if pixmap:
            return pixmap

        placeholder_pixmap = QPixmap(40, 40)
        placeholder_pixmap.fill(Qt.transparent)

        downloader = ImageDownloader(url)
        downloader.signals.finished.connect(self.update_pixmap)
        self.threadpool.start(downloader)

        return placeholder_pixmap

    def update_pixmap(self, url, pixmap):
        QPixmapCache.insert(url, pixmap)
        for i in range(self.results_layout.count()):
            item = self.results_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                layout = widget.layout()
                if layout:
                    image_label = layout.itemAt(0).widget()
                    if isinstance(image_label, QLabel) and image_label.property("url") == url:
                        image_label.setPixmap(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def add_result_item(self, idx, track):
        search_widget = QWidget()
        search_item = QHBoxLayout(search_widget)

        number_label = QLabel()
        url = track["album"]["images"][0]["url"]
        pixmap = self.load_pixmap_from_url(url)
        number_label.setPixmap(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        number_label.setProperty("url", url)
        search_item.addWidget(number_label)

        label_text = f"{track['name']}: {track['artists'][0]['name']}"
        title_label = name_label()
        title_label.setText(label_text)
        title_label.setFixedWidth(350)
        title_label.setStyleSheet("QLabel{font-size: 18px; font-family: Quicksand; color: #ffffff; padding: 2px;}")
        search_item.addWidget(title_label)

        search_item.addStretch()

        preview_button = create_button("icons/play.png", lambda: self.play_song(track, idx), 26)
        search_item.addWidget(preview_button)

        download_button = create_button("icons/download.png", lambda: self.download_song(track, idx), 26)
        search_item.addWidget(download_button)

        apply_hover_effect(search_widget, "background: #292929; border-radius: 8px;", "background: transparent;")
        search_widget.setCursor(Qt.PointingHandCursor)

        search_widget.mouseDoubleClickEvent = lambda event: self.play_song(track, idx)

        self.results_layout.addWidget(search_widget)
        self.download_icon_label_list.append(download_button)
        self.player_button_list.append(preview_button)

    def play_song(self, track, index):
        if self.main_frame.player.playbackState() == QMediaPlayer.PlayingState:
            self.main_frame.player.pause()

        if self.curr_index == index:
            if self.preview_player.playbackState() == QMediaPlayer.PlayingState:
                self.preview_player.pause()
                self.player_button_list[index].setIcon(QIcon("icons/play.png"))
            else:
                self.preview_player.play()
                self.player_button_list[index].setIcon(QIcon("icons/pause.png"))
            return

        if self.curr_index is not None:
            self.preview_player.stop()
            self.player_button_list[self.curr_index].setIcon(QIcon("icons/play.png"))

        self.curr_index = index
        search_query = f"{track['name']} by {track['artists'][0]['name']}"
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{search_query}", download=False)['entries'][0]
            url = info['url']

        self.preview_player.setSource(QUrl(url))
        self.preview_player.play()
        self.player_button_list[index].setIcon(QIcon("icons/pause.png"))

    def download_song(self, track, index):
        print(track)
        data_json_path = self.main_frame.get_data_file_path()
        with open(data_json_path, "r") as f:
            data = json.load(f)
            download_path = data["Settings"]["download_path"]

        os.makedirs(download_path, exist_ok=True)

        worker = DownloadWorker(track, index, download_path)
        worker.signals.finished.connect(self.download_complete)
        worker.signals.error.connect(self.download_error)

        self.threadpool.start(worker)

        QMessageBox.information(
            self,
            "Downloading",
            f"Downloading {track['name']} by {track['artists'][0]['name']}",
        )

    def download_complete(self, song_name, artist_name, index):
        completed_icon = QPixmap("icons/complete.png").scaled(60, 60)
        self.download_icon_label_list[index].setIcon(QIcon(completed_icon))

        data_json_path = self.main_frame.get_data_file_path()
        with open(data_json_path, "r+") as f:
            data = json.load(f)
            download_path = data["Settings"]["download_path"]

            safe_filename = sanitize_filename(f"{song_name} by {artist_name}")
            mp3_location = os.path.join(download_path, f"{safe_filename}.mp3")
            cover_location = os.path.join(download_path, f"{safe_filename}.png")
            lyrics_location = os.path.join(download_path, f"{safe_filename}.lrc")

            new_song = {
                "song_name": song_name,
                "artist": artist_name,
                "mp3_location": mp3_location,
                "cover_location": cover_location,
                "lyrics_location": lyrics_location
            }

            data["All Songs"].append(new_song)

            new_song_index = len(data["All Songs"]) - 1

            data["Playlists"]["All songs"]["songs"].append(new_song_index)
            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=4)

        QMessageBox.information(self, "Download Complete", f"Download of {song_name} by {artist_name} complete!")
        self.main_frame.load_data()
        self.main_frame.url_to_song_info = {song["mp3_location"].lower(): song for song in self.main_frame.all_songs}
        self.main_frame.player_frame.all_songs = self.main_frame.all_songs
        self.main_frame.player_frame.playlists = self.main_frame.playlists
        self.main_frame.player_frame.setup_layout('All songs')
        self.main_frame.current_playlist = self.main_frame.playlists["All songs"]['songs']

    def download_error(self, error_message):
        QMessageBox.critical(self, "Download Error", f"An error occurred during download: {error_message}")
