import json

import requests
import spotipy
from PySide6.QtCore import Qt, QRunnable, Signal, QObject, QByteArray, QThreadPool
from PySide6.QtGui import QPixmap, QIcon, QPainter, QPainterPath, QPixmapCache
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QPushButton, QFileDialog, QWidget, QScrollArea, QMessageBox)
from PySide6.QtWidgets import QListWidgetItem
from spotipy.oauth2 import SpotifyClientCredentials
from frames.search_frame import ImageDownloader
from .utils import create_button, apply_hover_effect, name_label


class CreatePlaylistDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Create New Playlist")
        self.setMinimumSize(500, 600)
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        top_section = QHBoxLayout()

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(200, 200)
        self.cover_label.setStyleSheet("border-radius: 10px; border: 2px solid #555;")
        self.cover_label.setCursor(Qt.PointingHandCursor)
        self.cover_label.mousePressEvent = lambda event: self.change_cover_image()
        self.auto_cover = True
        self.cover_path = ""
        self.update_cover_image()
        top_section.addWidget(self.cover_label)

        name_section = QVBoxLayout()
        name_section.setSpacing(10)

        name_label = QLabel("Playlist Name")
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        name_section.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setStyleSheet("font-size: 14px;")
        name_section.addWidget(self.name_input)

        self.change_cover_btn = QPushButton("Change Cover")
        self.change_cover_btn.clicked.connect(self.change_cover_image)
        name_section.addWidget(self.change_cover_btn)

        name_section.addStretch()
        top_section.addLayout(name_section)

        main_layout.addLayout(top_section)

        songs_label = QLabel("Choose Songs from below to add")
        songs_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        main_layout.addWidget(songs_label)

        self.song_list_widget = QListWidget()
        self.song_list_widget.setSelectionMode(QListWidget.MultiSelection)
        self.song_list_widget.setStyleSheet("QListWidget::item { padding: 5px; }")

        for i, song in enumerate(self.parent.all_songs):
            item = QListWidgetItem(f"{song['song_name']} - {song['artist']}")
            item.setIcon(QIcon(song['cover_location']))
            item.setData(Qt.UserRole, i)
            self.song_list_widget.addItem(item)

        main_layout.addWidget(self.song_list_widget)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        save_button = QPushButton("Create Playlist")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit {
                background-color: #3b3b3b;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton {
                background-color: #3b3b3b;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #4b4b4b;
            }
            QListWidget {
                background-color: #3b3b3b;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
            }
        """)

    def change_cover_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Cover Image", "", "Image Files (*.png *.jpg *.bmp)")
        if file_name:
            self.cover_path = file_name
            self.auto_cover = False
            self.update_cover_image()

    def update_cover_image(self):
        if self.auto_cover:
            pixmap = QPixmap("icons/music.png")
        else:
            pixmap = QPixmap(self.cover_path)

        self.cover_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def get_playlist_info(self):
        playlist_name = self.name_input.text()
        song_indexes = [item.data(Qt.UserRole) for item in self.song_list_widget.selectedItems()]
        cover_info = "auto" if self.auto_cover else self.cover_path
        return playlist_name, song_indexes, cover_info


def update_playlists_to_json(file_path, playlists):
    with open(file_path, 'r+') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}

        data['Playlists'] = playlists

        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=4)


class ImportPlaylistsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Your Playlists Here")
        self.setFixedSize(430, 560)
        self.setup_ui()
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id="baf2d72ae6054acf91dca4f10f8e3f2e",
                client_secret="aa9bbc0e087445a0a8799e676cd3ca5d",
            )
        )
        self.threadpool = QThreadPool()

    def setup_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        search_box_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.returnPressed.connect(self.search_playlist)
        self.search_box.setStyleSheet("""
            font-size: 16px;
            font-family: Quicksand;
            font-weight: 700;
        """)
        self.search_box.setFixedHeight(40)
        search_box_layout.addWidget(self.search_box)

        self.go_button = create_button('icons/search.png', self.search_playlist, 35)
        search_box_layout.addWidget(self.go_button)

        self.layout.addLayout(search_box_layout)

        self.results = QWidget()
        self.results_layout = QVBoxLayout(self.results)
        self.results_layout.setAlignment(Qt.AlignTop)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.layout.addWidget(self.scroll_area)
        self.scroll_area.setWidget(self.results)

        self.download_all = QPushButton("Download All")
        self.layout.addWidget(self.download_all)

    def search_playlist(self):
        for i in reversed(range(self.results_layout.count())):
            item = self.results_layout.itemAt(i)
            widget = item.widget()
            widget.deleteLater()

        playlist_link = self.search_box.text()
        if playlist_link.startswith('https://open.spotify.com/playlist/'):
            playlist_id = playlist_link.split('/')[-1]
            pl_id = f'spotify:playlist:{playlist_id}'

            response = self.sp.playlist_items(pl_id,
                                              fields='items.track.name,items.track.album.images.url,items.track.artists')
            if len(response['items']) == 0:
                QMessageBox.warning(self, "Warning", "No tracks found")
            else:
                for i, item in enumerate(response['items']):
                    print(response['items'])
                    song = {
                        "cover_url": f"{item['track']['album']['images'][0]['url']}",
                        "title": f"{item['track']['name']}",
                        "index": f"{i}",
                        "artist": f"{item['track']['artists'][0]['name']}"
                    }
                    self.results_layout.addWidget(self.create_song_widget(song, i, response['items']))
        else:
            print("nigga")

    def create_song_widget(self, song, index, song1):
        song_widget = QWidget()
        song_layout = QHBoxLayout(song_widget)
        song_layout.setContentsMargins(20, 0, 0, 0)
        song_widget.setFixedWidth(380)

        counter = QLabel(f"{int(song['index']) + 1}")
        counter.setFixedSize(30, 40)
        counter.setStyleSheet("font-size: 25px")
        song_layout.addWidget(counter)

        cover_label = QLabel()
        cover_pix = self.load_pixmap_from_url(song['cover_url'])
        cover_label.setFixedSize(40, 40)
        cover_label.setPixmap(cover_pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        cover_label.setProperty("url", song['cover_url'])
        song_layout.addWidget(cover_label)

        title_label = name_label(song['title'])
        title_label.setToolTip(song['title'])
        title_label.setStyleSheet('font-size: 20px;')
        song_layout.addWidget(title_label)
        song_layout.addStretch()
        download_button = create_button('icons/download.png', lambda event, song=song1, index=index: self.parent().search_frame.download_song(song, index), 35)
        song_layout.addWidget(download_button)

        song_widget.setFixedHeight(70)
        song_widget.setCursor(Qt.PointingHandCursor)
        apply_hover_effect(song_widget, "background: #292929; border-radius: 8px;", "background: transparent;")

        return song_widget

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
                    image_label = layout.itemAt(1).widget()
                    if isinstance(image_label, QLabel) and image_label.property("url") == url:
                        image_label.setPixmap(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
