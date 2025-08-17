import asyncio
import json
import os
from PySide6.QtCore import Qt, QMimeData, QTimer
from PySide6.QtGui import QPixmap, QColor, QPainter, QPainterPath, QFont, QIcon, QDrag
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QHBoxLayout, QDialog, QLineEdit, \
    QListWidget, QAbstractItemView, QPushButton, QFileDialog, QListWidgetItem, QMessageBox, QGraphicsBlurEffect
from colorthief import ColorThief
from frames.frame_functions.utils import apply_hover_effect
from .frame_functions.utils import create_button

class PlayerFrame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_frame = parent
        self.all_songs = self.main_frame.all_songs  # Initial copy
        self.playlists = self.main_frame.playlists  # Initial copy
        self.curr_playlist_name = ''
        self.setup_ui()
        # self.setup_layout('All songs') # Initial layout is now set by HomeScreen selection

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)  # Add some padding

        # --- Back Button and Header ---
        top_bar_layout = QHBoxLayout()
        self.back_button = create_button("icons/back-arrow.png", self.go_back, 24)  # Ensure you have a back-arrow.png
        self.back_button.setToolTip("Back to Home")
        top_bar_layout.addWidget(self.back_button, alignment=Qt.AlignLeft)
        # top_bar_layout.addStretch(1) # Removed stretch to keep header content to the left of songs

        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)
        # self.header_widget.setFixedHeight(180) # Height will be dynamic
        self.header_layout.setContentsMargins(10, 0, 0, 0)  # Reduced left margin

        self.header_cover = QLabel()
        self.header_cover.setFixedSize(150, 150)
        self.header_cover.setStyleSheet("background: transparent;")
        self.header_layout.addWidget(self.header_cover)

        playlist_info_layout = QVBoxLayout()  # For title and edit icon
        self.playlist_title = QLabel()
        self.playlist_title.setStyleSheet(
            "background: transparent; font-size: 28px; font-weight:bold; margin-left: 10px")

        self.edit_playlist_button = create_button("icons/edit.png",
                                                  lambda: self.edit_playlist(self.curr_playlist_name), 22)
        self.edit_playlist_button.setToolTip("Edit this playlist")

        title_and_edit_layout = QHBoxLayout()
        title_and_edit_layout.addWidget(self.playlist_title)
        title_and_edit_layout.addWidget(self.edit_playlist_button, alignment=Qt.AlignTop)
        title_and_edit_layout.addStretch()

        playlist_info_layout.addLayout(title_and_edit_layout)
        # Add more playlist info if needed, e.g., song count, duration
        playlist_info_layout.addStretch()

        self.header_layout.addLayout(playlist_info_layout)
        self.header_layout.addStretch()  # Stretch after playlist info

        top_bar_layout.addWidget(self.header_widget)  # Add header_widget to top_bar_layout
        self.layout.addLayout(top_bar_layout)  # Add top bar (back button + header)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")  # Style scroll area
        self.layout.addWidget(self.scroll_area)

        self.song_list_widget = QWidget()
        self.song_list_layout = QVBoxLayout(self.song_list_widget)
        self.song_list_layout.setAlignment(Qt.AlignTop)  # Align songs to top
        self.scroll_area.setWidget(self.song_list_widget)

    def go_back(self):
        self.main_frame.show_frame(self.main_frame.home_screen_frame)

    def setup_layout(self, playlist_name):
        # Refresh data sources from main_frame each time layout is set
        self.all_songs = self.main_frame.all_songs
        self.playlists = self.main_frame.playlists

        if playlist_name not in self.playlists:
            QMessageBox.warning(self, "Error", f"Playlist '{playlist_name}' not found.")
            self.go_back()  # Go back if playlist doesn't exist
            return

        # Asynchronously run the setup
        QTimer.singleShot(0, lambda: self.run_async_setup(playlist_name))

    def run_async_setup(self, playlist_name):
        asyncio.run(self.setup_layout_async(playlist_name))

    async def setup_layout_async(self, playlist_name):
        self.curr_playlist_name = playlist_name

        # Defensive check
        if playlist_name not in self.playlists:
            print(f"Error: Playlist '{playlist_name}' disappeared before async setup.")
            # Optionally show a message or go back
            self.clear_song_list_layout()  # Clear previous content
            no_playlist_label = QLabel(f"Playlist '{playlist_name}' could not be loaded.")
            self.song_list_layout.addWidget(no_playlist_label)
            self.playlist_title.setText("Error")
            self.header_cover.setPixmap(
                QPixmap("icons/music.png").scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.apply_gradient_to_widget(QColor(50, 50, 50))  # Default gradient
            return

        curr_playlist = self.playlists[playlist_name]
        self.clear_song_list_layout()

        if not curr_playlist['songs']:
            self.setup_empty_playlist(playlist_name)
        else:
            self.setup_populated_playlist(playlist_name, curr_playlist)

        self.song_list_layout.addStretch()
        await asyncio.sleep(0)

    def clear_song_list_layout(self):
        while self.song_list_layout.count():
            item = self.song_list_layout.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()

    def setup_empty_playlist(self, playlist_name):
        first_img = "icons/music.png"
        dominant_color = self.get_dominant_color(first_img)
        self.apply_gradient_to_widget(dominant_color)
        pixmap = QPixmap(first_img)
        self.set_rounded_pixmap(self.header_cover, pixmap, 10)
        self.playlist_title.setText(playlist_name)
        no_song = QLabel("No songs found in the playlist.")
        self.song_list_layout.addWidget(no_song)

    def setup_populated_playlist(self, playlist_name, curr_playlist):
        first_img = self.all_songs[curr_playlist['songs'][0]]['cover_location']
        dominant_color = self.get_dominant_color(first_img)
        self.apply_gradient_to_widget(dominant_color)
        pixmap = self.main_frame.generate_playlist_cover(playlist_name, 150)
        self.set_rounded_pixmap(self.header_cover, pixmap, 10)
        self.playlist_title.setText(playlist_name)
        self.add_songs(curr_playlist['songs'], playlist_name)

    def add_songs(self, songs, playlist_name):
        for i, index in enumerate(songs):
            song = self.all_songs[index]
            song_widget = self.create_song_widget(i, song, index, playlist_name)
            self.song_list_layout.addWidget(song_widget)

    def create_song_widget(self, i, song, index, playlist_name):
        song_widget = QWidget()
        song_layout = QHBoxLayout(song_widget)
        song_layout.setContentsMargins(20, 0, 0, 0)

        counter = QLabel(f"{i + 1}")
        counter.setFixedSize(30, 40)
        counter.setStyleSheet("font-size: 25px")
        song_layout.addWidget(counter)

        cover_label = QLabel()
        cover_pix = QPixmap(song['cover_location'])
        cover_label.setFixedSize(50, 50)
        self.set_rounded_pixmap(cover_label, cover_pix, 5)
        song_layout.addWidget(cover_label)

        title_label = QLabel(song['song_name'])
        title_label.setToolTip(song['song_name'])
        title_label.setStyleSheet('font-size: 20px;')
        song_layout.addWidget(title_label)

        song_widget.setFixedHeight(70)
        song_widget.mousePressEvent = lambda event, idx=index, nn=playlist_name: self.handle_mouse_press(event, idx, nn)
        song_widget.mouseDoubleClickEvent = lambda event, idx=index, nn=playlist_name: self.play_song(idx, nn)
        song_widget.setCursor(Qt.PointingHandCursor)
        apply_hover_effect(song_widget, "background: #292929; border-radius: 8px;", "background: transparent;")

        song_widget.setProperty("song_index", index)

        return song_widget

    def handle_mouse_press(self, event, index, playlist_name):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(str(index))
            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction)

    def play_song(self, song_index_in_all_songs, playlist_name_context):
        self.main_frame.current_playlist = self.playlists[playlist_name_context]['songs']
        try:
            self.main_frame.current_song_index = self.main_frame.current_playlist.index(song_index_in_all_songs)
        except ValueError:
            print(f"Error: Song index {song_index_in_all_songs} not found in playlist {playlist_name_context}")
            self.main_frame.current_playlist = [song_index_in_all_songs]
            self.main_frame.current_song_index = 0

        self.main_frame.set_media(self.all_songs[song_index_in_all_songs]["mp3_location"])

        # Update queue in expanded player
        curr_playlist_songs = [self.main_frame.all_songs[i] for i in self.main_frame.current_playlist]
        self.main_frame.music_player_frame.queue_view.update_queue(curr_playlist_songs)

    def set_rounded_pixmap(self, label, pixmap, radius):
        rounded_pixmap = QPixmap(label.size())
        rounded_pixmap.fill(Qt.transparent)
        painter = QPainter(rounded_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, label.width(), label.height(), radius, radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap.scaled(label.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        painter.end()
        label.setPixmap(rounded_pixmap)

    def get_dominant_color(self, image_path):
        color_thief = ColorThief(image_path)
        dominant_color = color_thief.get_color(quality=1)
        qcolor = QColor(*dominant_color)
        return self.adjust_color(qcolor)

    def adjust_color(self, color):
        hsv = color.toHsv()
        hsv.setHsv(hsv.hue(), int(hsv.saturation() * 0.8), int(hsv.value() * 0.8))
        return hsv.toRgb()

    def apply_gradient_to_widget(self, dominant_color):
        dominant_color_str = dominant_color.name()
        style_sheet = f"""
        background: qlineargradient(
            x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 {dominant_color_str},
            stop: 1 rgba({dominant_color.red()}, {dominant_color.green()}, {dominant_color.blue()}, 40)
        );
        border-radius: 5px;
        """
        self.header_widget.setStyleSheet(style_sheet)




