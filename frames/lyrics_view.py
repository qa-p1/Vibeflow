import colorsys

from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame, QGraphicsScene, QGraphicsPixmapItem, \
    QGraphicsBlurEffect, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QColor, QLinearGradient, QPalette, QFont, QImage, QPainter, QBrush, QPixmap, QPainterPath
from colorthief import ColorThief

from frames.frame_functions.utils import create_button


class LyricsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        self.current_lyric_index = 0
        self.lyrics = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_lyrics)
        self.scroll_animation = None
        self.setStyleSheet("background:transparent;")

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.top_bar_widget = QWidget(self)
        self.top_bar_widget.setFixedHeight(55)
        self.top_bar_widget.setStyleSheet("background:transparent;")
        top_bar_layout = QHBoxLayout(self.top_bar_widget)
        back_button = create_button("icons/back-arrow.png", self.go_back, 32)
        back_button.setToolTip("Back to Player")
        top_bar_layout.addWidget(back_button, alignment=Qt.AlignLeft)
        top_bar_layout.addStretch()



        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent;")

        self.lyrics_container = QWidget()
        self.lyrics_container.setStyleSheet("background: transparent;")
        self.lyrics_layout = QVBoxLayout(self.lyrics_container)

        self.scroll_area.setWidget(self.lyrics_container)
        self.layout.addWidget(self.scroll_area)
        self.top_bar_widget.raise_()# Add scroll area to main layout

    def go_back(self):
        self.parent.show_frame(self.parent.main_view_widget)

    def set_lyrics(self, lyrics_file):
        try:
            with open(lyrics_file, 'r', encoding='utf-8') as f:
                lrc_content = f.read()
            self.lyrics = self.parse_lrc(lrc_content)
            self.display_lyrics()
        except FileNotFoundError:
            print(f"Lyrics file not found: {lyrics_file}")
            self.display_no_lyrics()

    @staticmethod
    def parse_lrc(lrc_content):
        lines = lrc_content.strip().split('\n')
        parsed_lyrics = []
        for line in lines:
            time_tag, lyric = line.split(']', 1)
            time_tag = time_tag[1:]
            minutes, seconds = map(float, time_tag.split(':'))
            timestamp = minutes * 60 + seconds
            parsed_lyrics.append((timestamp, lyric.strip()))
        return parsed_lyrics

    def display_lyrics(self):
        for i in reversed(range(self.lyrics_layout.count())):
            self.lyrics_layout.itemAt(i).widget().setParent(None)

        # Add spacers to center the first lyrics
        scroll_area_height = self.scroll_area.height()
        spacer_height = int(scroll_area_height / 2) - 50  # Center minus some offset

        # Top spacer to push first lyrics to center
        top_spacer = QLabel()
        top_spacer.setFixedHeight(spacer_height)
        top_spacer.setStyleSheet("background: transparent;")
        self.lyrics_layout.addWidget(top_spacer)

        for i, (_, lyric) in enumerate(self.lyrics):
            label = QLabel(lyric if lyric else " ♪  ♪  ♪  ♪  ♪  ♪ ")
            label.setAlignment(Qt.AlignCenter)
            label.setWordWrap(True)
            label.setProperty("lyric_index", i)
            label.setCursor(Qt.PointingHandCursor)
            label.mousePressEvent = lambda event, index=i: self.lyric_clicked(index)
            # Add some padding between lyrics
            label.setStyleSheet("""
                QLabel {
                    padding: 15px 20px;
                    background: transparent;
                }
            """)
            self.lyrics_layout.addWidget(label)

        # Bottom spacer
        bottom_spacer = QLabel()
        bottom_spacer.setFixedHeight(spacer_height)
        bottom_spacer.setStyleSheet("background: transparent;")
        self.lyrics_layout.addWidget(bottom_spacer)

        self.update_lyrics_style()

    def display_no_lyrics(self):
        # Clear existing widgets
        for i in reversed(range(self.lyrics_layout.count())):
            self.lyrics_layout.itemAt(i).widget().setParent(None)

        # Center the "no lyrics" message
        scroll_area_height = self.scroll_area.height()
        spacer_height = int(scroll_area_height / 2) - 25

        top_spacer = QLabel()
        top_spacer.setFixedHeight(spacer_height)
        top_spacer.setStyleSheet("background: transparent;")
        self.lyrics_layout.addWidget(top_spacer)

        label = QLabel("No lyrics available for this song.")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8); 
            font-size: 18px; 
            font-weight: 500;
            background: transparent;
            padding: 20px;
        """)
        self.lyrics_layout.addWidget(label)

        bottom_spacer = QLabel()
        bottom_spacer.setFixedHeight(spacer_height)
        bottom_spacer.setStyleSheet("background: transparent;")
        self.lyrics_layout.addWidget(bottom_spacer)

    def update_lyrics_style(self):
        for i in range(self.lyrics_layout.count()):
            label = self.lyrics_layout.itemAt(i).widget()
            if isinstance(label, QLabel) and label.property("lyric_index") is not None:
                if label.property("lyric_index") == self.current_lyric_index:
                    label.setStyleSheet("""
                        QLabel {
                            color: white; 
                            font-size: 28px; 
                            font-weight: bold;
                            padding: 15px 20px;
                            background: transparent;
                            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
                        }
                    """)
                else:
                    label.setStyleSheet("""
                        QLabel {
                            color: rgba(255, 255, 255, 0.6); 
                            font-size: 16px;
                            padding: 15px 20px;
                            background: transparent;
                            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.7);
                        }
                    """)

    def scroll_to_current_lyric(self):
        if self.current_lyric_index < 0 or self.current_lyric_index >= len(self.lyrics):
            return

        # Account for the top spacer (index 0) when finding the current label
        current_label = self.lyrics_layout.itemAt(self.current_lyric_index + 1).widget()
        if not current_label:
            return

        scroll_area_height = self.scroll_area.height()
        label_height = current_label.height()

        target_y = current_label.pos().y() - (scroll_area_height / 2) + (label_height / 2)

        if self.scroll_animation and self.scroll_animation.state() == QPropertyAnimation.Running:
            self.scroll_animation.stop()

        self.scroll_animation = QPropertyAnimation(self.scroll_area.verticalScrollBar(), b"value")
        self.scroll_animation.setDuration(350)
        self.scroll_animation.setStartValue(self.scroll_area.verticalScrollBar().value())
        self.scroll_animation.setEndValue(target_y)
        self.scroll_animation.setEasingCurve(QEasingCurve.OutQuad)
        self.scroll_animation.start()

    def update_lyrics(self):
        current_time = self.parent.player.position() / 1000
        for i, (timestamp, _) in enumerate(self.lyrics):
            if timestamp > current_time:
                if i > 0 and i != self.current_lyric_index:
                    self.current_lyric_index = i - 1
                    self.update_lyrics_style()
                    self.scroll_to_current_lyric()
                break

    def lyric_clicked(self, index):
        timestamp, _ = self.lyrics[index]
        self.parent.player.setPosition(int(timestamp * 1000))

    def start_lyrics_sync(self):
        self.timer.start(50)

    def stop_lyrics_sync(self):
        self.timer.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Redisplay lyrics to adjust spacers for new size
        if self.lyrics:
            self.display_lyrics()
        self.scroll_to_current_lyric()