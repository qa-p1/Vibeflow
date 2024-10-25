import colorsys

from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame, QGraphicsScene, QGraphicsPixmapItem, \
    QGraphicsBlurEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QColor, QLinearGradient, QPalette, QFont, QImage, QPainter, QBrush, QPixmap
from colorthief import ColorThief



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

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.lyrics_container = QWidget()
        self.lyrics_layout = QVBoxLayout(self.lyrics_container)
        self.scroll_area.setWidget(self.lyrics_container)

        self.layout.addWidget(self.scroll_area)

    def set_lyrics(self, lyrics_file):
        try:
            with open(lyrics_file, 'r', encoding='utf-8') as f:
                lrc_content = f.read()
            self.lyrics = self.parse_lrc(lrc_content)
            self.display_lyrics()
        except FileNotFoundError:
            print(f"Lyrics file not found: {lyrics_file}")
            self.display_no_lyrics()

    def parse_lrc(self, lrc_content):
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
        self.lyrics_layout.addWidget(QLabel())

        for i, (_, lyric) in enumerate(self.lyrics):
            label = QLabel(lyric if lyric else " ♪  ♪  ♪  ♪  ♪  ♪ ")
            label.setAlignment(Qt.AlignCenter)
            label.setWordWrap(True)
            label.setProperty("lyric_index", i)
            label.setCursor(Qt.PointingHandCursor)
            label.mousePressEvent = lambda event, index=i: self.lyric_clicked(index)
            self.lyrics_layout.addWidget(label)
        self.lyrics_layout.addWidget(QLabel())

        self.update_lyrics_style()

    def display_no_lyrics(self):
        label = QLabel("No lyrics available for this song.")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: white; font-size: 16px;")
        self.lyrics_layout.addWidget(label)

    def update_lyrics_style(self):
        for i in range(self.lyrics_layout.count()):
            label = self.lyrics_layout.itemAt(i).widget()
            if isinstance(label, QLabel):
                if label.property("lyric_index") == self.current_lyric_index:
                    label.setStyleSheet("color: white; font-size: 25px; font-weight: bold;")
                else:
                    label.setStyleSheet("color: rgba(255, 255, 255, 150); font-size: 14px;")

    def scroll_to_current_lyric(self):
        if self.current_lyric_index < 0 or self.current_lyric_index >= self.lyrics_layout.count():
            return

        current_label = self.lyrics_layout.itemAt(self.current_lyric_index + 1).widget()
        if not current_label:
            return

        scroll_area_height = self.scroll_area.height()
        label_height = current_label.height()

        target_y = current_label.pos().y() - (scroll_area_height / 2) + (label_height / 2)

        if self.scroll_animation and self.scroll_animation.state() == QPropertyAnimation.Running:
            self.scroll_animation.stop()

        self.scroll_animation = QPropertyAnimation(self.scroll_area.verticalScrollBar(), b"value")

        self.scroll_animation.setDuration(400)

        self.scroll_animation.setStartValue(self.scroll_area.verticalScrollBar().value())
        self.scroll_animation.setEndValue(target_y)
        self.scroll_animation.setEasingCurve(QEasingCurve.InOutSine)
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
        self.timer.start(100)

    def stop_lyrics_sync(self):
        self.timer.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scroll_to_current_lyric()