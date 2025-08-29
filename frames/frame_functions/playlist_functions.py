import json
import os
import spotipy
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QPixmap, QIcon, QPixmapCache, QFont, QColor
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QPushButton, QFileDialog, QWidget, QScrollArea, QMessageBox,
                               QAbstractItemView, QCheckBox, QProgressBar, QListWidgetItem)
from spotipy.oauth2 import SpotifyClientCredentials
from frames.search_frame import ImageDownloader
from .utils import create_button, apply_hover_effect


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
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(35, 35, 40, 240),
                    stop:1 rgba(25, 25, 30, 240));
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 16px;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
                background: transparent;
                font-family: Quicksand;
            }
            QLineEdit {
                background: rgba(255, 255, 255, 15);
                color: #e0e0e0;
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                font-family: Quicksand;
            }
            QLineEdit:focus {
                border: 1px solid rgba(255, 255, 255, 80);
                background: rgba(255, 255, 255, 20);
            }
            QPushButton {
                background: rgba(255, 255, 255, 12);
                color: #e0e0e0;
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
                font-family: Quicksand;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 20);
                border: 1px solid rgba(255, 255, 255, 50);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 25);
            }
            QListWidget {
                background: rgba(255, 255, 255, 8);
                color: #e0e0e0;
                border: 1px solid rgba(255, 255, 255, 25);
                border-radius: 12px;
                outline: none;
                font-family: Quicksand;
            }
            QListWidget::item {
                background: transparent;
                padding: 8px 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background: rgba(255, 255, 255, 25);
                color: #ffffff;
            }
            QListWidget::item:hover {
                background: rgba(255, 255, 255, 15);
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 10);
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 30);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 50);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
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

class DownloadProgressDialog(QDialog):
    def __init__(self, playlist_name, total_songs, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importing Playlist")
        self.setMinimumSize(400, 500)
        self.playlist_name = playlist_name
        self.total_songs = total_songs
        self.completed_songs = 0
        self.song_items = {}

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.title_label = QLabel(f"Importing '{self.playlist_name}'")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_label)

        self.status_label = QLabel("Preparing...")
        self.status_label.setStyleSheet("font-size: 12px; color: #aaa;")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(self.total_songs)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        self.song_list_widget = QListWidget()
        layout.addWidget(self.song_list_widget)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setEnabled(False)  # Disabled until finished
        layout.addWidget(self.close_button)

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(35, 35, 40, 240), stop:1 rgba(25, 25, 30, 240));
                border-radius: 16px; color: #e0e0e0; font-family: Quicksand;
            }
            QProgressBar {
                border: none; border-radius: 5px; background: rgba(255, 255, 255, 10); height: 10px;
            }
            QProgressBar::chunk {
                background-color: #50b4ff; border-radius: 5px;
            }
            QListWidget {
                background: rgba(255, 255, 255, 8); border: 1px solid rgba(255, 255, 255, 25);
                border-radius: 12px; outline: none;
            }
            QListWidget::item { padding: 8px 12px; }
            QPushButton {
                background: rgba(255, 255, 255, 12); color: #e0e0e0; border-radius: 8px;
                padding: 10px 16px; font-size: 14px; font-weight: 500;
            }
            QPushButton:hover { background: rgba(255, 255, 255, 20); }
            QPushButton:disabled { background: rgba(255, 255, 255, 5); color: #888; }
        """)

    def populate_song_list(self, songs):
        for song in songs:
            song_name = song.get('name', 'Unknown Track')
            artist_name = ", ".join([a.get('name', 'Unknown Artist') for a in song.get('artists', [])])
            item = QListWidgetItem(f" {song_name} - {artist_name}")
            item.setForeground(QColor("#888"))
            self.song_list_widget.addItem(item)
            self.song_items[song['id']] = item

    def update_song_status(self, song_id, status, color):
        if song_id in self.song_items:
            item = self.song_items[song_id]

            if status == "Downloaded" or status == "In Library":
                self.completed_songs += 1
                self.progress_bar.setValue(self.completed_songs)
                self.status_label.setText(f"Processed {self.completed_songs} of {self.total_songs} songs...")
                item.setIcon(QIcon("icons/download-complete.png"))
                if status == "In Library":
                    item.setToolTip("Already in your library")
            elif status == "Failed":
                self.completed_songs += 1 # A failed attempt is still a "processed" song
                self.progress_bar.setValue(self.completed_songs)
                self.status_label.setText(f"Processed {self.completed_songs} of {self.total_songs} songs...")
                item.setIcon(QIcon("icons/download-failed.png"))
            elif status == "Downloading...":
                item.setIcon(QIcon("icons/downloading.png"))

            item.setForeground(QColor(color))

    def import_complete(self, new_playlist_name):
        self.title_label.setText("Import Complete!")
        self.status_label.setText(f"Playlist '{new_playlist_name}' has been created.")
        self.close_button.setEnabled(True)
        self.close_button.setText("Done")

class ImportPlaylistsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Spotify Playlist")
        self.setMinimumSize(480, 700)
        self.track_widgets = []
        self.setup_spotify()
        self.setup_ui()
        self.apply_styles()
        self.threadpool = QThreadPool()

    def setup_spotify(self):
        try:
            self.sp = spotipy.Spotify(
                auth_manager=SpotifyClientCredentials(
                    client_id="baf2d72ae6054acf91dca4f10f8e3f2e",
                    client_secret="aa9bbc0e087445a0a8799e676cd3ca5d",
                )
            )
            self.sp.search('test', limit=1, type='track')
        except Exception as e:
            QMessageBox.critical(self, "Spotify Error",
                                 f"Could not connect to Spotify. Please check your internet connection.\nError: {e}")
            self.sp = None

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # --- Search Bar ---
        search_box_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Paste Spotify Playlist URL here...")
        self.search_box.returnPressed.connect(self.search_playlist)
        search_box_layout.addWidget(self.search_box)
        self.go_button = create_button('icons/search.png', self.search_playlist, 35)
        search_box_layout.addWidget(self.go_button)
        self.main_layout.addLayout(search_box_layout)

        self.playlist_info_widget = QWidget()
        self.playlist_info_widget.setStyleSheet("background: transparent;")
        playlist_info_layout = QVBoxLayout(self.playlist_info_widget)
        playlist_info_layout.setSpacing(10)
        playlist_info_layout.setAlignment(Qt.AlignCenter)

        self.playlist_cover_label = QLabel()
        self.playlist_cover_label.setFixedSize(150, 150)
        self.playlist_cover_label.setStyleSheet("border-radius: 8px;")
        playlist_info_layout.addWidget(self.playlist_cover_label)

        self.playlist_name_label = QLabel("Playlist Name")
        self.playlist_name_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.playlist_name_label.setAlignment(Qt.AlignCenter)
        self.playlist_name_label.setWordWrap(True)
        playlist_info_layout.addWidget(self.playlist_name_label)

        self.playlist_details_label = QLabel("by Owner • 0 songs")
        self.playlist_details_label.setStyleSheet("color: #aaa; font-size: 13px;")
        self.playlist_details_label.setAlignment(Qt.AlignCenter)
        playlist_info_layout.addWidget(self.playlist_details_label)

        self.playlist_info_widget.setVisible(False)
        self.main_layout.addWidget(self.playlist_info_widget)

        # --- Track List ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setAlignment(Qt.AlignTop)
        self.results_layout.setSpacing(8)
        self.scroll_area.setWidget(self.results_container)
        self.main_layout.addWidget(self.scroll_area)

        # --- Action Buttons ---
        buttons_layout = QHBoxLayout()
        self.select_all_button = QPushButton("Deselect All")
        self.select_all_button.clicked.connect(self.toggle_select_all)
        buttons_layout.addWidget(self.select_all_button)
        buttons_layout.addStretch()
        self.import_button = QPushButton("Import Selected")
        self.import_button.clicked.connect(self.import_selected_tracks)
        buttons_layout.addWidget(self.import_button)
        self.main_layout.addLayout(buttons_layout)

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(35, 35, 40, 240),
                    stop:1 rgba(25, 25, 30, 240));
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 16px;
                color: #e0e0e0;
                font-family: Quicksand;
            }
            QLabel { color: #e0e0e0; background: transparent; }
            QLineEdit {
                background: rgba(255, 255, 255, 15);
                color: #e0e0e0;
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 8px;
                padding: 10px 14px;
                font-weight: 500;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(80, 180, 255, 150);
                background: rgba(255, 255, 255, 20);
            }
            QPushButton {
                background: rgba(255, 255, 255, 12);
                color: #e0e0e0;
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 20);
                border: 1px solid rgba(255, 255, 255, 50);
            }
            QPushButton:pressed { background: rgba(255, 255, 255, 25); }
            QScrollArea {
                background: rgba(255, 255, 255, 8);
                border: 1px solid rgba(255, 255, 255, 25);
                border-radius: 12px;
            }
            QScrollArea > QWidget > QWidget { background: transparent; }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 10);
                width: 8px; border-radius: 4px; margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 30);
                min-height: 20px; border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover { background: rgba(255, 255, 255, 50); }
            QCheckBox { spacing: 12px; }
            QCheckBox::indicator {
                width: 20px; height: 20px;
                border: 2px solid #555; border-radius: 6px;
            }
            QCheckBox::indicator:hover { border: 2px solid #777; }
            QCheckBox::indicator:checked {
                background-color: #50b4ff; border: 2px solid #50b4ff;
            }
        """)

    def search_playlist(self):
        if not self.sp:
            return

        for widget in self.track_widgets:
            widget.deleteLater()
        self.track_widgets.clear()
        self.playlist_info_widget.setVisible(False)

        playlist_link = self.search_box.text().strip()
        if not playlist_link.startswith('https://open.spotify.com/playlist/'):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid Spotify playlist URL.")
            return

        try:
            playlist_id = playlist_link.split('/')[-1].split('?')[0]
            playlist_data = self.sp.playlist(playlist_id)
            self.update_playlist_info_widget(playlist_data)

            tracks = []
            response = self.sp.playlist_items(playlist_id, fields='items.track(name,artists,album(images,name)),next')
            tracks.extend(response['items'])
            while response['next']:
                response = self.sp.next(response)
                tracks.extend(response['items'])

            if not tracks:
                QMessageBox.information(self, "Empty Playlist", "This playlist contains no tracks.")
                return

            for item in tracks:
                if item and item['track']:
                    widget = self.create_song_widget(item['track'])
                    self.results_layout.addWidget(widget)
                    self.track_widgets.append(widget)
        except spotipy.exceptions.SpotifyException as e:
            QMessageBox.critical(self, "API Error", f"Could not fetch playlist data from Spotify.\nReason: {e.msg}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def update_playlist_info_widget(self, data):
        self.playlist_name_label.setText(data['name'])
        details = f"by {data['owner']['display_name']} • {data['tracks']['total']} songs"
        self.playlist_details_label.setText(details)

        if data['images']:
            cover_url = data['images'][0]['url']
            placeholder = QPixmap(150, 150)
            placeholder.fill(Qt.gray)
            self.playlist_cover_label.setPixmap(placeholder)

            downloader = ImageDownloader(cover_url, {"id": "playlist_cover"})
            downloader.signals.finished.connect(self.update_playlist_cover)
            self.threadpool.start(downloader)
        else:
            pixmap = QPixmap("icons/music.png")
            scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.playlist_cover_label.setPixmap(scaled_pixmap)

        self.playlist_info_widget.setVisible(True)

    def update_playlist_cover(self, url, pixmap):
        scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.playlist_cover_label.setPixmap(scaled_pixmap)

    def create_song_widget(self, song):
        song_widget = QWidget()
        song_layout = QHBoxLayout(song_widget)
        song_layout.setContentsMargins(15, 10, 15, 10)
        song_layout.setSpacing(15)

        checkbox = QCheckBox()
        checkbox.setFixedWidth(30)
        checkbox.setChecked(True)
        song_layout.addWidget(checkbox)

        cover_label = QLabel()
        cover_label.setFixedSize(45, 45)
        cover_label.setStyleSheet("border-radius: 4px;")
        if song["album"]["images"]:
            url = song["album"]["images"][-1]["url"]
            cover_pix = self.load_pixmap_from_url(url, song)
            cover_label.setPixmap(cover_pix)
            cover_label.setProperty("url", url)
        else:
            placeholder = QPixmap("icons/music.png").scaled(45, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            cover_label.setPixmap(placeholder)
        song_layout.addWidget(cover_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        title_label = QLabel(song['name'])
        title_label.setToolTip(song['name'])
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        artist_name = ", ".join([a['name'] for a in song['artists']])
        artist_label = QLabel(artist_name)
        artist_label.setToolTip(artist_name)
        artist_label.setStyleSheet("font-size: 12px; color: #bbb;")
        text_layout.addWidget(title_label)
        text_layout.addWidget(artist_label)
        song_layout.addLayout(text_layout)

        if not song.get('id'):
            song_name_safe = song.get('name', 'Unknown Track')
            artist_name_safe = song.get('artists', [{'name': 'Unknown Artist'}])[0].get('name', 'Unknown Artist')
            song['id'] = f"fallback_{song_name_safe}_{artist_name_safe}"

        song_widget.setProperty("song_data", song)
        apply_hover_effect(song_widget, "background: rgba(255, 255, 255, 10); border-radius: 8px;",
                           "background: transparent;")
        return song_widget

    def toggle_select_all(self):
        if not self.track_widgets:
            return

        is_any_unchecked = any(not w.findChild(QCheckBox).isChecked() for w in self.track_widgets)
        new_state = is_any_unchecked
        for widget in self.track_widgets:
            widget.findChild(QCheckBox).setChecked(new_state)

        self.select_all_button.setText("Deselect All" if new_state else "Select All")

    def import_selected_tracks(self):
        selected_songs = [w.property("song_data") for w in self.track_widgets if w.findChild(QCheckBox).isChecked()]
        if not selected_songs:
            QMessageBox.warning(self, "No Songs Selected", "Please select at least one song to import.")
            return

        playlist_name = self.playlist_name_label.text()

        main_window = self.parent()
        if hasattr(main_window, 'start_playlist_import'):
            main_window.start_playlist_import(selected_songs, playlist_name)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Cannot find the import handler. Import failed.")

    def load_pixmap_from_url(self, url, song):
        pixmap = QPixmapCache.find(url)
        if pixmap:
            return pixmap.scaled(45, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        downloader = ImageDownloader(url, song)
        downloader.signals.finished.connect(self.update_pixmap)
        self.threadpool.start(downloader)

        placeholder = QPixmap(45, 45)
        placeholder.fill(Qt.transparent)
        return placeholder

    def update_pixmap(self, url, pixmap):
        QPixmapCache.insert(url, pixmap)
        for widget in self.track_widgets:
            for child in widget.findChildren(QLabel):
                if child.property("url") == url:
                    child.setPixmap(pixmap.scaled(45, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    break


class EditPlaylistDialog(QDialog):
    def __init__(self, parent, playlist_name):
        super().__init__(parent)
        self.main_frame = parent.home_frame.main_frame
        self.playlist_name = playlist_name
        self.original_name = playlist_name
        self.playlist_info = self.main_frame.playlists[playlist_name]
        self.all_songs = self.main_frame.all_songs
        self.setup_ui()
        self.setWindowIcon(QIcon("icons/vibeflow.ico"))
        self.apply_styles()

    def setup_ui(self):
        self.setWindowTitle(f"Edit Playlist: {self.playlist_name}")
        self.setMinimumSize(500, 600)
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        top_section = QHBoxLayout()

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(200, 200)
        self.cover_label.setStyleSheet("border-radius: 10px; border: 2px solid #555;")
        self.cover_label.setCursor(
            QPixmap("icons/edit.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.update_cover_image()
        top_section.addWidget(self.cover_label)

        name_section = QVBoxLayout()
        name_section.setSpacing(10)

        name_label = QLabel("Playlist Name")
        name_label.setFont(QFont("Quicksand", 12, QFont.Bold))
        name_section.addWidget(name_label)

        self.name_edit = QLineEdit(self.playlist_name)
        self.name_edit.setFont(QFont("Quicksand", 14))
        self.name_edit.textChanged.connect(lambda: self.on_name_changed(self.name_edit.text()))
        name_section.addWidget(self.name_edit)

        change_cover_btn = QPushButton("Change Cover")
        change_cover_btn.setIcon(QIcon("icons/icons8-edit-image-96.png"))
        change_cover_btn.clicked.connect(self.change_cover_image)
        name_section.addWidget(change_cover_btn)

        name_section.addStretch()
        top_section.addLayout(name_section)

        main_layout.addLayout(top_section)

        songs_label = QLabel("Songs")
        songs_label.setFont(QFont("Quicksand", 12, QFont.Bold))
        main_layout.addWidget(songs_label)

        self.songs_list = QListWidget()
        self.songs_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.songs_list.setStyleSheet("QListWidget::item { padding: 5px; }")
        self.update_songs_list()

        songs_scroll = QScrollArea()
        songs_scroll.setWidget(self.songs_list)
        songs_scroll.setWidgetResizable(True)
        songs_scroll.setFixedHeight(200)
        main_layout.addWidget(songs_scroll)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        remove_button = QPushButton("Remove Selected")
        remove_button.setIcon(QIcon("icons/icons8-trash-96.png"))
        remove_button.clicked.connect(self.remove_selected_songs)
        button_layout.addWidget(remove_button)

        save_button = QPushButton("Save Changes")
        save_button.setIcon(QIcon("icons/icons8-save-96.png"))
        save_button.clicked.connect(self.save_changes)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.setIcon(QIcon("icons/icons8-cancel-96.png"))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

        if self.playlist_name != "All songs":
            delete_button = QPushButton("Delete Playlist")
            delete_button.setIcon(QIcon("icons/icons8-delete-96.png"))
            delete_button.clicked.connect(self.delete_playlist)
            button_layout.addWidget(delete_button)

        main_layout.addLayout(button_layout)

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(35, 35, 40, 240),
                    stop:1 rgba(25, 25, 30, 240));
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 16px;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
                background: transparent;
                font-family: Quicksand;
            }
            QLineEdit {
                background: rgba(255, 255, 255, 15);
                color: #e0e0e0;
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                font-family: Quicksand;
            }
            QLineEdit:focus {
                border: 1px solid rgba(255, 255, 255, 80);
                background: rgba(255, 255, 255, 20);
            }
            QPushButton {
                background: rgba(255, 255, 255, 12);
                color: #e0e0e0;
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 14px;
                font-family: Quicksand;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 20);
                border: 1px solid rgba(255, 255, 255, 50);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 25);
            }
            QListWidget {
                background: rgba(255, 255, 255, 8);
                color: #e0e0e0;
                border: 1px solid rgba(255, 255, 255, 25);
                border-radius: 12px;
                outline: none;
                font-family: Quicksand;
            }
            QListWidget::item {
                background: transparent;
                padding: 8px 12px;
                border-radius: 6px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background: rgba(255, 255, 255, 25);
                color: #ffffff;
            }
            QListWidget::item:hover {
                background: rgba(255, 255, 255, 15);
            }
            QScrollArea {
                background: rgba(255, 255, 255, 8);
                border: 1px solid rgba(255, 255, 255, 25);
                border-radius: 12px;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 10);
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 30);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 50);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def update_cover_image(self):
        if self.playlist_info['playlist_cover'] == "auto":
            if self.playlist_info['songs']:
                first_song = self.all_songs[self.playlist_info['songs'][0]]
                pixmap = QPixmap(first_song['cover_location'])
            else:
                pixmap = QPixmap("icons/music.png")
        else:
            pixmap = QPixmap(self.playlist_info['playlist_cover'])

        self.cover_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def on_name_changed(self, new_name):
        if self.original_name == 'All songs':
            QMessageBox.warning(self, "Warning", "You can't change the name of this default playlist")
            self.name_edit.setText('All songs')
            return

        if new_name in self.main_frame.playlists and new_name != self.original_name:
            QMessageBox.warning(self, "Warning", "A playlist with this name already exists")
            self.name_edit.setText(self.playlist_name)
            return

        if new_name != self.original_name and new_name != "All songs":
            self.playlist_name = new_name

    def save_changes(self):
        new_name = self.name_edit.text()

        if new_name != self.original_name and new_name != "All songs":
            if new_name in self.main_frame.playlists:
                QMessageBox.warning(self, "Warning", "A playlist with this name already exists")
                return

            self.main_frame.playlists[new_name] = self.main_frame.playlists.pop(self.original_name)
            self.playlist_name = new_name

        self.main_frame.playlists[self.playlist_name] = self.playlist_info

        self.update_json()
        self.main_frame.home_screen_frame.display_playlists()
        self.accept()

    def change_cover_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Cover Image", "", "Image Files (*.png *.jpg)")
        if file_name:
            self.playlist_info['playlist_cover'] = file_name
            self.update_cover_image()
            self.update_json()

    def remove_selected_songs(self):
        selected_items = self.songs_list.selectedItems()
        if not selected_items:
            return

        if self.playlist_name == "All songs":
            confirm_msg = f"You are about to delete {len(selected_items)} song(s) from 'All songs'.\n\n" \
                          f"This will remove the selected song(s) from all playlists and delete the files from your system.\n\n" \
                          f"Are you sure you want to continue?"
            reply = QMessageBox.question(self, 'Confirm Deletion', confirm_msg,
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.No:
                return

            deleted_indices = []
            for item in reversed(selected_items):
                index = self.songs_list.row(item)
                song_index = self.playlist_info['songs'][index]

                song_info = self.all_songs[song_index]
                try:
                    os.remove(song_info['mp3_location'])
                    os.remove(song_info['cover_location'])
                    os.remove(song_info['lyrics_location'])
                except OSError as e:
                    QMessageBox.warning(self, "File Deletion Error",
                                        f"Error deleting files for '{song_info['song_name']}':\n{e}")

                deleted_indices.append(song_index)

            for index in sorted(deleted_indices, reverse=True):
                del self.all_songs[index]
            for playlist_name, playlist in self.main_frame.playlists.items():
                playlist['songs'] = [s for s in playlist['songs'] if s not in deleted_indices]
                playlist['songs'] = [s - sum(1 for d in deleted_indices if d < s) for s in playlist['songs']]

            self.update_songs_list()
            self.update_json()
            QMessageBox.information(self, "Deletion Complete",
                                    f"{len(selected_items)} song(s) have been deleted from your system and all playlists.")
        else:
            for item in reversed(selected_items):
                index = self.songs_list.row(item)
                song_index = self.playlist_info['songs'][index]
                self.playlist_info['songs'].remove(song_index)

            self.update_songs_list()

    def delete_playlist(self):
        if self.playlist_name == "All songs":
            return

        confirm_msg = f"Are you sure you want to delete the playlist '{self.playlist_name}'?"
        reply = QMessageBox.question(self, 'Confirm Deletion', confirm_msg,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if self.playlist_name in self.main_frame.playlists:
                del self.main_frame.playlists[self.playlist_name]

            if hasattr(self.main_frame, 'player_frame') and hasattr(self.main_frame.player_frame, 'playlists'):
                if self.playlist_name in self.main_frame.player_frame.playlists:
                    del self.main_frame.player_frame.playlists[self.playlist_name]

            if hasattr(self.main_frame, 'player_frame'):
                self.main_frame.player_frame.playlists = self.main_frame.playlists

            self.update_json()
            self.main_frame.home_screen_frame.display_playlists()
            self.accept()

    def update_json(self):
        data_json_path = os.path.join(os.getcwd(), self.main_frame.get_data_file_path())
        with open(data_json_path) as f:
            data = json.load(f)

        data['All Songs'] = self.all_songs

        updated_playlists = {}
        for playlist_name in list(data['Playlists'].keys()):
            if playlist_name in self.main_frame.playlists:
                updated_playlists[playlist_name] = self.main_frame.playlists[playlist_name]
            elif playlist_name == self.original_name and self.playlist_name != self.original_name:
                updated_playlists[self.playlist_name] = self.main_frame.playlists[self.playlist_name]

        data['Playlists'] = updated_playlists

        with open(data_json_path, 'w') as f:
            json.dump(data, f, indent=4)

    def update_songs_list(self):
        self.songs_list.clear()
        for song_index in self.playlist_info['songs']:
            song = self.all_songs[song_index]
            item = QListWidgetItem(f"{song['song_name']} - {song['artist']}")
            item.setIcon(QIcon(song['cover_location']))
            self.songs_list.addItem(item)