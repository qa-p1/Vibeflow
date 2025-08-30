from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QStackedWidget, QApplication, \
    QMenu, QDialog
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup, QRectF, QMimeData, \
    QTimer
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QLinearGradient, QBrush, QDrag, QAction
from frames.frame_functions.utils import name_label, create_button
from frames.frame_functions.playlist_functions import EditPlaylistDialog
from frames.search_frame import SearchFrame
from frames.picks_for_you import PicksForYouWidget
from frames.settings_frame import SettingsFrame


class GlassmorphismWidget(QWidget):
    """Custom widget that applies glassmorphism effect"""

    def __init__(self, parent, blur_intensity=0.15, border_opacity=0.3):
        super().__init__(parent)
        self.blur_intensity = blur_intensity
        self.border_opacity = border_opacity
        self.setAttribute(Qt.WA_StyledBackground, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12, 12)
        painter.setClipPath(path)

        background_color = QColor(255, 255, 255, int(self.blur_intensity * 255))
        painter.fillRect(self.rect(), background_color)

        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 255, 255, int(self.blur_intensity * 80)))
        gradient.setColorAt(1, QColor(0, 0, 0, int(self.blur_intensity * 40)))
        painter.fillRect(self.rect(), QBrush(gradient))

        painter.setClipping(False)
        painter.setPen(QColor(255, 255, 255, int(self.border_opacity * 255)))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 12, 12)

        super().paintEvent(event)


class PlaylistCardWidget(QWidget):
    """Enhanced playlist card with subtle glassmorphism and context menu"""

    def __init__(self, parent=None, home_frame=None, playlist_name=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.is_hovered = False
        self.home_frame = home_frame
        self.playlist_name = playlist_name

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 8, 8)
        painter.setClipPath(path)

        if self.is_hovered:
            background_color = QColor(255, 255, 255, 25)
            painter.fillRect(self.rect(), background_color)

            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, QColor(255, 255, 255, 15))
            gradient.setColorAt(1, QColor(0, 0, 0, 10))
            painter.fillRect(self.rect(), QBrush(gradient))

            painter.setClipping(False)
            painter.setPen(QColor(255, 255, 255, 60))
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)
        else:
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

    def edit_playlist(self, playlist_name):
        dialog = EditPlaylistDialog(self, playlist_name)
        if dialog.exec() == QDialog.Accepted:
            self.home_frame.main_frame.load_data()
            self.home_frame.display_playlists()

    def contextMenuEvent(self, event):
        if not self.home_frame or not self.playlist_name:
            return

        menu = QMenu(self)

        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(40, 40, 40, 200);
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 12px;
                padding: 8px;
                font-size: 14px;
                color: #e0e0e0;
                backdrop-filter: blur(20px);
            }
            QMenu::item {
                background-color: transparent;
                padding: 8px 16px;
                border-radius: 6px;
                margin: 2px;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 25);
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(255, 255, 255, 30);
                margin: 4px 8px;
            }
        """)

        main_frame = self.home_frame.main_frame

        play_action = QAction("Play", self)
        add_to_queue_action = QAction("Add to Queue", self)
        rename_action = QAction("Rename", self)
        delete_action = QAction("Delete Playlist", self)

        play_action.triggered.connect(lambda: main_frame.play_playlist(self.playlist_name))
        add_to_queue_action.triggered.connect(lambda: main_frame.add_playlist_to_queue(self.playlist_name))
        rename_action.triggered.connect(lambda: self.edit_playlist(self.playlist_name))
        delete_action.triggered.connect(lambda: main_frame.open_delete_playlist_dialog(self.playlist_name))

        menu.addAction(play_action)
        menu.addAction(add_to_queue_action)
        menu.addSeparator()
        menu.addAction(rename_action)
        menu.addAction(delete_action)

        menu.exec(event.globalPos())


class DropIndicator(QWidget):
    """Visual indicator for drop zones between songs"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(3)
        self.setStyleSheet("background-color: #1db954; border-radius: 1px;")
        self.hide()


class SongCardWidget(QWidget):
    """Enhanced song card with drag & drop and a context menu"""

    def __init__(self, parent=None, song_index=None, playlist_name=None, home_frame=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.is_hovered = False
        self.is_being_dragged = False
        self.song_index = song_index
        self.playlist_name = playlist_name
        self.home_frame = home_frame
        self.drag_start_position = None
        self.drag_started = False

        self.setAcceptDrops(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 8, 8)
        painter.setClipPath(path)

        if self.is_being_dragged:
            background_color = QColor(255, 255, 255, 10)
            painter.fillRect(self.rect(), background_color)
        elif self.is_hovered:
            background_color = QColor(255, 255, 255, 20)
            painter.fillRect(self.rect(), background_color)

            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, QColor(255, 255, 255, 12))
            gradient.setColorAt(1, QColor(0, 0, 0, 8))
            painter.fillRect(self.rect(), QBrush(gradient))

            painter.setClipping(False)
            painter.setPen(QColor(255, 255, 255, 50))
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)
        else:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        super().paintEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            self.drag_started = False
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if (event.button() == Qt.LeftButton and
                self.drag_start_position and
                not self.drag_started):

            if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
                pass

        self.drag_start_position = None
        self.drag_started = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double-click to play song"""
        if event.button() == Qt.LeftButton and self.song_index and self.playlist_name:
            self.home_frame.main_frame.play_song_from_sidebar(self.song_index, self.playlist_name)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        if self.song_index is None or not self.playlist_name or not self.home_frame:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(40, 40, 40, 200);
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 12px;
                padding: 8px;
                font-size: 14px;
                color: #e0e0e0;
                backdrop-filter: blur(20px);
            }
            QMenu::item {
                background-color: transparent;
                padding: 8px 16px;
                border-radius: 6px;
                margin: 2px;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 25);
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(255, 255, 255, 30);
                margin: 4px 8px;
            }
            QMenu::item:disabled {
                color: #808080;
            }
        """)

        main_frame = self.home_frame.main_frame

        play_next_action = QAction("Play Next", self)
        add_to_queue_action = QAction("Add to Queue", self)
        remove_action = QAction("Remove from this Playlist", self)

        play_next_action.triggered.connect(lambda: main_frame.play_song_next(self.song_index))
        add_to_queue_action.triggered.connect(lambda: main_frame.add_song_to_queue(self.song_index))
        remove_action.triggered.connect(lambda: self.home_frame.remove_song_from_current_playlist(self.song_index))

        menu.addAction(play_next_action)
        menu.addAction(add_to_queue_action)

        add_to_playlist_menu = QMenu("Add to Playlist...", menu)
        add_to_playlist_menu.setStyleSheet(menu.styleSheet())

        other_playlists = [p for p in main_frame.playlists if p != self.playlist_name]

        if not other_playlists:
            add_to_playlist_menu.setEnabled(False)
        else:
            for p_name in other_playlists:
                action = QAction(p_name, self)
                action.triggered.connect(
                    lambda checked=False, p=p_name: main_frame.add_song_to_playlist(self.song_index, p))
                add_to_playlist_menu.addAction(action)

        menu.addMenu(add_to_playlist_menu)
        menu.addSeparator()
        menu.addAction(remove_action)

        menu.exec(event.globalPos())

    def mouseMoveEvent(self, event):
        if (event.buttons() == Qt.LeftButton and
                self.drag_start_position and
                not self.drag_started and
                (event.pos() - self.drag_start_position).manhattanLength() >= QApplication.startDragDistance()):
            self.drag_started = True
            self.start_drag()

    def start_drag(self):
        """Start the drag operation"""
        if self.song_index is None or not self.playlist_name or not self.home_frame:
            return

        drag = QDrag(self)
        mimeData = QMimeData()

        mimeData.setText(f"{self.song_index}|{self.playlist_name}")
        drag.setMimeData(mimeData)

        pixmap = self.grab()
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        painter.fillRect(pixmap.rect(), QColor(0, 0, 0, 180))
        painter.end()

        drag.setPixmap(pixmap)
        drag.setHotSpot(self.drag_start_position)

        self.is_being_dragged = True
        self.update()

        drag.exec_(Qt.MoveAction)

        self.is_being_dragged = False
        self.drag_started = False
        self.update()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.source() != self:
            try:
                data = event.mimeData().text()
                source_index, source_playlist = data.split('|')
                if source_playlist == self.playlist_name:
                    event.acceptProposedAction()
                    if hasattr(self.home_frame, 'show_drop_indicator'):
                        self.home_frame.show_drop_indicator(self)
                    return
            except ValueError:
                pass
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText() and event.source() != self:
            try:
                data = event.mimeData().text()
                source_index, source_playlist = data.split('|')
                if source_playlist == self.playlist_name:
                    event.acceptProposedAction()
                    return
            except ValueError:
                pass
        event.ignore()

    def dragLeaveEvent(self, event):
        if hasattr(self.home_frame, 'hide_drop_indicator'):
            self.home_frame.hide_drop_indicator()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            data = event.mimeData().text()
            try:
                source_index, source_playlist = data.split('|')
                source_index = int(source_index)

                if source_playlist == self.playlist_name and source_index != self.song_index:
                    self.home_frame.reorder_song_in_playlist(
                        source_index, self.song_index, self.playlist_name
                    )
                    event.acceptProposedAction()
            except (ValueError, AttributeError):
                pass

        if hasattr(self.home_frame, 'hide_drop_indicator'):
            self.home_frame.hide_drop_indicator()

    def enterEvent(self, event):
        if not self.is_being_dragged:
            self.is_hovered = True
            self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)


class HomeScreenFrame(QWidget):
    def __init__(self, main_frame):
        super().__init__(main_frame)
        self.main_frame = main_frame
        self.current_playlist_name = None
        self.drop_indicator = None
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 20, 15, 20)
        self.layout.setSpacing(20)
        self.setStyleSheet('background: transparent;')

        self.content_stack = QStackedWidget(self)
        self.content_stack.setStyleSheet("background: transparent;")
        self.setup_playlist_view()
        self.setup_song_list_view()
        self.setup_search_view()

        self.picks_widget = PicksForYouWidget(self.main_frame)
        self.layout.addWidget(self.content_stack, 65)
        self.layout.addWidget(self.picks_widget, 35)
        self.setup_settings_view()

        QTimer.singleShot(1000, self.picks_widget.load_recommendations)

    def setup_playlist_view(self):
        self.playlist_glass_container = GlassmorphismWidget(self, blur_intensity=0.12, border_opacity=0.25)

        layout = QVBoxLayout(self.playlist_glass_container)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        header = QHBoxLayout()
        playlist_title = QLabel("Playlists")
        playlist_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #eeeeee; background: transparent;")
        header.addWidget(playlist_title)
        header.addStretch()
        header.addWidget(create_button("icons/search.png", self.show_search, 24))
        header.addWidget(create_button("icons/import.png", self.main_frame.open_import_playlist_dialog, 24))
        header.addWidget(create_button("icons/plus.png", self.main_frame.open_create_playlist_dialog, 24))
        header.addWidget(create_button("icons/settings.png", self.show_settings, 24))
        layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background: transparent; 
            }
            QScrollArea > QWidget > QWidget { 
                background: transparent; 
            }
        """)

        self.playlist_list_container = QWidget()
        self.playlist_list_container.setStyleSheet("background: transparent;")
        self.playlist_list_layout = QVBoxLayout(self.playlist_list_container)
        self.playlist_list_layout.setAlignment(Qt.AlignTop)
        self.playlist_list_layout.setSpacing(8)

        scroll.setWidget(self.playlist_list_container)
        layout.addWidget(scroll)
        self.content_stack.addWidget(self.playlist_glass_container)

    def setup_song_list_view(self):
        self.song_glass_container = GlassmorphismWidget(self, blur_intensity=0.12, border_opacity=0.25)

        layout = QVBoxLayout(self.song_glass_container)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        header = QHBoxLayout()
        header.addWidget(create_button("icons/back-arrow.png", self.show_playlists, 24))
        self.song_list_title = QLabel("Playlist Songs")
        self.song_list_title.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #eeeeee; background: transparent;")
        header.addWidget(self.song_list_title)
        header.addStretch()
        layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background: transparent; 
            }
            QScrollArea > QWidget > QWidget { 
                background: transparent; 
            }
        """)

        self.song_list_container = QWidget()
        self.song_list_container.setStyleSheet("background: transparent;")
        self.song_list_layout = QVBoxLayout(self.song_list_container)
        self.song_list_layout.setAlignment(Qt.AlignTop)
        self.song_list_layout.setSpacing(5)

        scroll.setWidget(self.song_list_container)
        layout.addWidget(scroll)

        self.drop_indicator = DropIndicator(self.song_list_container)

        self.content_stack.addWidget(self.song_glass_container)

    def setup_search_view(self):
        self.search_glass_container = GlassmorphismWidget(self, blur_intensity=0.12, border_opacity=0.25)
        search_layout = QVBoxLayout(self.search_glass_container)
        search_layout.setContentsMargins(0, 0, 0, 0)

        self.search_view_widget = SearchFrame(self.main_frame, back_callback=self.show_playlists)
        self.search_view_widget.setStyleSheet("background: transparent;")
        search_layout.addWidget(self.search_view_widget)

        self.content_stack.addWidget(self.search_glass_container)

    def setup_settings_view(self):
        self.settings_glass_container = GlassmorphismWidget(self, blur_intensity=0.12, border_opacity=0.25)
        settings_layout = QVBoxLayout(self.settings_glass_container)
        settings_layout.setContentsMargins(0, 0, 0, 0)

        self.settings_view_widget = SettingsFrame(self.main_frame, back_callback=self.show_playlists)
        self.settings_view_widget.setStyleSheet("background: transparent;")
        settings_layout.addWidget(self.settings_view_widget)

        self.content_stack.addWidget(self.settings_glass_container)

    def display_playlists(self):
        while self.playlist_list_layout.count():
            item = self.playlist_list_layout.takeAt(0)
            if w := item.widget():
                w.deleteLater()

        for name in self.main_frame.playlists:
            self.playlist_list_layout.addWidget(self.create_playlist_card(name))
        self.playlist_list_layout.addStretch()

    def create_playlist_card(self, name):
        card = PlaylistCardWidget(home_frame=self, playlist_name=name)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(10, 5, 10, 5)

        cover = QLabel()
        cover.setFixedSize(60, 60)
        cover.setPixmap(self.main_frame.generate_playlist_cover(name, 60))
        cover.setStyleSheet("background: transparent;")

        name_widget = name_label(name,
                                 styleSheet="font-size: 16px; font-weight: 500; color: #e0e0e0; background: transparent;")

        layout.addWidget(cover)
        layout.addWidget(name_widget, 1)

        card.setCursor(Qt.PointingHandCursor)
        card.mousePressEvent = lambda e: self.display_songs_for_playlist(name) if e.button() == Qt.LeftButton else None

        return card

    def display_songs_for_playlist(self, name):
        self.current_playlist_name = name
        self.song_list_title.setText(name)
        while self.song_list_layout.count():
            item = self.song_list_layout.takeAt(0)
            if w := item.widget():
                w.deleteLater()

        playlist = self.main_frame.playlists.get(name)
        if not playlist or not playlist.get('songs'):
            empty_label = QLabel("This playlist is empty.")
            empty_label.setStyleSheet("color: #a0a0a0; background: transparent;")
            self.song_list_layout.addWidget(empty_label)
        else:
            for idx in playlist['songs']:
                self.song_list_layout.addWidget(self.create_song_card(self.main_frame.all_songs[idx], idx, name))

        self.song_list_layout.addStretch()
        self.animate_transition(self.song_glass_container)

    def create_song_card(self, info, index, playlist_name):
        card = SongCardWidget(song_index=index, playlist_name=playlist_name, home_frame=self)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(10, 5, 10, 5)

        cover = QLabel()
        cover.setFixedSize(50, 50)
        cover.setStyleSheet("background: transparent;")
        pix = QPixmap(info['cover_location'])
        rounded = QPixmap(cover.size())
        rounded.fill(Qt.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QRectF(cover.rect()), 8, 8)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pix.scaled(cover.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        painter.end()
        cover.setPixmap(rounded)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)

        song_name_label = name_label(info['song_name'],
                                     styleSheet="font-size: 14px; font-weight: 500; color: #e0e0e0; background: transparent;")
        artist_label = name_label(info['artist'],
                                  styleSheet="font-size: 12px; color: #a0a0a0; background: transparent;")

        info_layout.addWidget(song_name_label)
        info_layout.addWidget(artist_label)

        layout.addWidget(cover)
        layout.addLayout(info_layout, 1)

        card.setCursor(Qt.PointingHandCursor)

        return card

    def reorder_song_in_playlist(self, source_index, target_index, playlist_name):
        """Reorder songs in the playlist and update JSON"""
        if playlist_name not in self.main_frame.playlists:
            return

        playlist_songs = self.main_frame.playlists[playlist_name]['songs']

        try:
            source_pos = playlist_songs.index(source_index)
            target_pos = playlist_songs.index(target_index)

            song_to_move = playlist_songs.pop(source_pos)
            playlist_songs.insert(target_pos, song_to_move)

            self.main_frame.save_playlists_to_json()

            self.display_songs_for_playlist(playlist_name)

        except ValueError:
            pass

    def remove_song_from_current_playlist(self, song_index):
        """Removes a song from the currently displayed playlist and refreshes the view."""
        if self.current_playlist_name not in self.main_frame.playlists:
            return

        playlist_songs = self.main_frame.playlists[self.current_playlist_name]['songs']

        try:
            playlist_songs.remove(song_index)
            self.main_frame.save_playlists_to_json()
            self.display_songs_for_playlist(self.current_playlist_name)
        except ValueError:
            pass

    def show_drop_indicator(self, target_card):
        """Show drop indicator above the target card"""
        if not self.drop_indicator:
            return

        card_pos = target_card.pos()
        self.drop_indicator.move(card_pos.x(), card_pos.y() - 2)
        self.drop_indicator.resize(target_card.width(), 3)
        self.drop_indicator.show()
        self.drop_indicator.raise_()

    def hide_drop_indicator(self):
        """Hide the drop indicator"""
        if self.drop_indicator:
            self.drop_indicator.hide()

    def show_playlists(self):
        self.animate_transition(self.playlist_glass_container, from_right=False)

    def show_search(self):
        self.animate_transition(self.search_glass_container)

    def show_settings(self):
        self.animate_transition(self.settings_glass_container)

    def animate_transition(self, target_widget, from_right=True):
        if self.content_stack.currentWidget() == target_widget:
            return
        w = self.content_stack.width()
        start_x = w if from_right else -w

        target_widget.setGeometry(start_x, 0, w, self.content_stack.height())
        anim_target = QPropertyAnimation(target_widget, b"pos")
        anim_target.setDuration(400)
        anim_target.setEasingCurve(QEasingCurve.InOutQuad)
        anim_target.setStartValue(QPoint(start_x, 0))
        anim_target.setEndValue(QPoint(0, 0))

        current_widget = self.content_stack.currentWidget()
        end_x = -w if from_right else w

        anim_current = QPropertyAnimation(current_widget, b"pos")
        anim_current.setDuration(400)
        anim_current.setEasingCurve(QEasingCurve.InOutQuad)
        anim_current.setStartValue(QPoint(0, 0))
        anim_current.setEndValue(QPoint(end_x, 0))

        self.anim_group = QParallelAnimationGroup()
        self.anim_group.addAnimation(anim_target)
        self.anim_group.addAnimation(anim_current)
        self.anim_group.finished.connect(lambda: self.content_stack.setCurrentWidget(target_widget))

        target_widget.show()
        target_widget.raise_()
        self.anim_group.start()
