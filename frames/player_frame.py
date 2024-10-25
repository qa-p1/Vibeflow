import asyncio
import json
import os
from PySide6.QtCore import Qt, QMimeData, QTimer
from PySide6.QtGui import QPixmap, QColor, QPainter, QPainterPath, QFont, QIcon, QDrag
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QHBoxLayout, QDialog, QLineEdit, \
    QListWidget, QAbstractItemView, QPushButton, QFileDialog, QListWidgetItem, QMessageBox, QGraphicsBlurEffect
from colorthief import ColorThief
from frames.frame_functions.utils import apply_hover_effect


class PlayerFrame(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_frame = parent
        self.all_songs = self.main_frame.all_songs
        self.playlists = self.main_frame.playlists
        self.curr_playlist_name = ''
        self.setup_ui()
        self.setup_layout('All songs')

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_widget.setFixedHeight(180)
        edit_icon = QPixmap("icons/edit.png").scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.header_widget.setCursor(edit_icon)
        self.header_widget.mousePressEvent = lambda event: self.edit_playlist(self.curr_playlist_name)

        self.header_layout.setContentsMargins(20, 0, 0, 0)
        self.header_cover = QLabel()
        self.header_cover.setFixedSize(150, 150)
        self.header_cover.setStyleSheet("background: transparent;")
        self.header_layout.addWidget(self.header_cover)

        self.playlist_title = QLabel()
        self.playlist_title.setStyleSheet("background: transparent; font-size: 35px; margin-left: 5px")
        self.header_layout.addWidget(self.playlist_title)
        self.header_layout.addStretch()

        self.layout.addWidget(self.header_widget)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layout.addWidget(self.scroll_area)
        self.song_list_widget = QWidget()
        self.song_list_layout = QVBoxLayout(self.song_list_widget)
        self.scroll_area.setWidget(self.song_list_widget)

    def setup_layout(self, playlist_name):
        QTimer.singleShot(0, lambda: self.run_async_setup(playlist_name))

    def run_async_setup(self, playlist_name):
        asyncio.run(self.setup_layout_async(playlist_name))

    async def setup_layout_async(self, playlist_name):
        self.curr_playlist_name = playlist_name
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

    def play_song(self, index, play_name):
        self.main_frame.current_song_index = self.playlists[play_name]['songs'].index(index)
        self.main_frame.set_media(self.all_songs[index]["mp3_location"])

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

    def edit_playlist(self, playlist_name):
        dialog = EditPlaylistDialog(self, playlist_name)
        if dialog.exec() == QDialog.Accepted:
            self.main_frame.load_data()
            self.all_songs = self.main_frame.all_songs
            self.playlists = self.main_frame.playlists
            self.main_frame.display_playlists_sync()
            self.setup_layout('All songs')


class EditPlaylistDialog(QDialog):
    def __init__(self, parent, playlist_name):
        super().__init__(parent)
        self.main_frame = parent.main_frame
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
            QScrollArea {
                border: none;
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
        self.main_frame.player_frame.playlists[self.playlist_name] = self.playlist_info
        self.update_json()
        self.accept()

    def change_cover_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Cover Image", "", "Image Files (*.png *.jpg)")
        if file_name:
            self.playlist_info['playlist_cover'] = file_name
            self.update_cover_image()
            self.update_json()

    def update_songs_list(self):
        self.songs_list.clear()
        for song_index in self.playlist_info['songs']:
            song = self.all_songs[song_index]
            item = QListWidgetItem()
            item.setText(f"{song['song_name']} - {song['artist']}")
            item.setIcon(QIcon(song['cover_location']))
            self.songs_list.addItem(item)

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
            self.accept()

    def update_json(self):
        data_json_path = os.path.join(os.getcwd(), self.main_frame.get_data_file_path())
        with open(data_json_path, 'r') as f:
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
