import json
import random
import requests
import math
from PySide6.QtCore import Qt, QRunnable, QObject, Signal, QThreadPool, QRectF, QTimer, QEasingCurve, QPropertyAnimation
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QLinearGradient, QPen
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGraphicsOpacityEffect
from frames.frame_functions.music_helper import search_for_jiosaavn_url, get_song_id, get_song


class RecommendationCard(QWidget):
    """Card widget displaying a song with its cover art as the background."""

    def __init__(self, parent=None, track_data=None, main_frame=None, size_class="medium"):
        super().__init__(parent)
        self.track_data = track_data
        self.main_frame = main_frame
        self.size_class = size_class
        self.is_hovered = False
        self.cover_pixmap = QPixmap()
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)

        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addStretch()

        if self.size_class == "small":
            layout.setContentsMargins(8, 8, 8, 8)
            name_font_size = 12
            max_width = 80
        elif self.size_class == "large":
            layout.setContentsMargins(16, 16, 16, 16)
            name_font_size = 18
            max_width = 200
        elif self.size_class in ("wide", "tall"):
            layout.setContentsMargins(14, 14, 14, 14)
            name_font_size = 15
            max_width = 150
        else:
            layout.setContentsMargins(12, 12, 12, 12)
            name_font_size = 14
            max_width = 120

        song_name = self.track_data.get('name', 'Unknown Song') if self.track_data else 'Unknown Song'
        self.song_label = QLabel(song_name)
        self.song_label.setFixedWidth(max_width)
        self.song_label.setStyleSheet(f"""
            color: #f0f0f0;
            font-size: {name_font_size}px; 
            font-weight: bold; 
            background: transparent;
        """)
        self.song_label.setWordWrap(False)
        self.song_label.setText(self.song_label.fontMetrics().elidedText(
            song_name, Qt.ElideRight, max_width
        ))

        layout.addWidget(self.song_label)

    def fade_in(self, duration=500):
        """Animate fade in effect"""
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(duration)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_animation.start()

    def fade_out(self, duration=500, callback=None):
        """Animate fade out effect"""
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(duration)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InCubic)
        if callback:
            self.fade_animation.finished.connect(callback)
        self.fade_animation.start()

    def set_cover_image(self, pixmap):
        """Set the cover image from downloaded pixmap and trigger a repaint."""
        if not pixmap.isNull():
            self.cover_pixmap = pixmap
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12, 12)
        painter.setClipPath(path)

        if not self.cover_pixmap.isNull():
            scaled_pixmap = self.cover_pixmap.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            crop_x = (scaled_pixmap.width() - self.width()) / 2
            crop_y = (scaled_pixmap.height() - self.height()) / 2

            painter.drawPixmap(-crop_x, -crop_y, scaled_pixmap)
        else:
            placeholder_gradient = QLinearGradient(0, 0, 0, self.height())
            placeholder_gradient.setColorAt(0, QColor(65, 65, 75))
            placeholder_gradient.setColorAt(1, QColor(45, 45, 55))
            painter.fillRect(self.rect(), placeholder_gradient)

        dim_gradient = QLinearGradient(0, self.height() * 0.3, 0, self.height())
        dim_gradient.setColorAt(0, Qt.transparent)
        dim_gradient.setColorAt(1, QColor(0, 0, 0, 220))
        painter.fillRect(self.rect(), dim_gradient)

        
        if self.is_hovered:
            pen = QPen(QColor(255, 255, 255, 200))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)

        
        super().paintEvent(event)

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.track_data:
            song_name = self.track_data.get('name', 'Unknown')
            artist_name = self.track_data['artists'][0]['name'] if self.track_data.get('artists') else 'Unknown'
            song = f"{song_name} by {artist_name}"
            print(song)
            song_url = search_for_jiosaavn_url(song)

            if song_url:
                if song_url.startswith("https://"):
                    song_url = song_url.replace("https://", "http://", 1)
                    print(f"Converted URL to http for processing: {song_url}")

                song_id = get_song_id(song_url)

                if song_id:
                    song_data = get_song(song_id, False)
                    if song_data:
                        print(song_data['media_url'])
        super().mousePressEvent(event)


class HandcraftedLayoutManager:
    """Manages handcrafted layout patterns for different card counts and container sizes"""

    def __init__(self, container_width, container_height, gap=6):
        self.container_width = container_width
        self.container_height = container_height
        self.gap = gap

    def get_layout(self, card_count):
        """Get a beautiful handcrafted layout for the given card count"""
        layouts = self.get_layout_patterns()

        if card_count in layouts:
            pattern_variations = layouts[card_count]
            chosen_pattern = random.choice(pattern_variations)
            return self.apply_pattern(chosen_pattern, card_count)

        
        return self.create_simple_grid(card_count)

    def get_layout_patterns(self):
        """Define handcrafted layout patterns for different card counts - NO OVERLAPS"""
        return {
            2: [
                
                [(0, 0, 0.5, 1, "medium"), (0.5, 0, 0.5, 1, "medium")],
                
                [(0, 0, 1, 0.5, "wide"), (0, 0.5, 1, 0.5, "wide")],
                
                [(0, 0, 0.618, 1, "medium"), (0.618, 0, 0.382, 1, "medium")]
            ],
            3: [
                
                [(0, 0, 0.6, 0.6, "large"), (0.6, 0, 0.4, 0.6, "medium"), (0, 0.6, 1, 0.4, "wide")],
                
                [(0, 0, 0.33, 1, "tall"), (0.33, 0, 0.34, 1, "tall"), (0.67, 0, 0.33, 1, "tall")],
                
                [(0, 0, 0.7, 1, "large"), (0.7, 0, 0.3, 0.5, "small"), (0.7, 0.5, 0.3, 0.5, "small")]
            ],
            4: [
                
                [(0, 0, 0.5, 0.5, "medium"), (0.5, 0, 0.5, 0.5, "medium"),
                 (0, 0.5, 0.5, 0.5, "medium"), (0.5, 0.5, 0.5, 0.5, "medium")],
                
                [(0, 0, 0.6, 0.6, "large"), (0.6, 0, 0.4, 0.3, "small"),
                 (0.6, 0.3, 0.4, 0.3, "small"), (0, 0.6, 1, 0.4, "wide")],
                
                [(0, 0, 1, 0.3, "wide"), (0, 0.3, 0.33, 0.7, "tall"),
                 (0.33, 0.3, 0.34, 0.7, "tall"), (0.67, 0.3, 0.33, 0.7, "tall")]
            ],
            5: [
                
                [(0.3, 0, 0.4, 0.3, "medium"), (0, 0.3, 0.3, 0.4, "medium"), (0.3, 0.3, 0.4, 0.4, "large"),
                 (0.7, 0.3, 0.3, 0.4, "medium"), (0.3, 0.7, 0.4, 0.3, "medium")],
                
                [(0, 0, 0.4, 0.6, "medium"), (0.4, 0, 0.3, 0.3, "small"), (0.7, 0, 0.3, 0.6, "medium"),
                 (0.4, 0.3, 0.3, 0.3, "small"), (0, 0.6, 0.7, 0.4, "wide")]
            ],
            6: [
                
                [(0, 0, 0.33, 0.5, "medium"), (0.33, 0, 0.34, 0.5, "medium"), (0.67, 0, 0.33, 0.5, "medium"),
                 (0, 0.5, 0.33, 0.5, "medium"), (0.33, 0.5, 0.34, 0.5, "medium"), (0.67, 0.5, 0.33, 0.5, "medium")],
                
                [(0.2, 0.2, 0.6, 0.6, "large"), (0, 0, 0.2, 0.5, "small"), (0.8, 0, 0.2, 0.5, "small"),
                 (0, 0.5, 0.2, 0.5, "small"), (0.8, 0.5, 0.2, 0.5, "small"), (0.2, 0.8, 0.6, 0.2, "wide")]
            ],
            7: [
                
                [(0.25, 0.15, 0.5, 0.4, "large"), (0, 0, 0.25, 0.3, "small"), (0.75, 0, 0.25, 0.3, "small"),
                 (0, 0.3, 0.25, 0.4, "small"), (0.75, 0.3, 0.25, 0.4, "small"),
                 (0, 0.7, 0.5, 0.3, "medium"), (0.5, 0.7, 0.5, 0.3, "medium")]
            ],
            8: [
                
                [(0, 0, 0.4, 0.5, "medium"), (0.4, 0, 0.3, 0.25, "small"), (0.7, 0, 0.3, 0.5, "medium"),
                 (0.4, 0.25, 0.3, 0.25, "small"), (0, 0.5, 0.2, 0.5, "small"), (0.2, 0.5, 0.2, 0.5, "small"),
                 (0.4, 0.5, 0.3, 0.5, "medium"), (0.7, 0.5, 0.3, 0.5, "medium")],
                
                [(0, 0, 0.25, 0.5, "medium"), (0.25, 0, 0.25, 0.5, "medium"), (0.5, 0, 0.25, 0.5, "medium"),
                 (0.75, 0, 0.25, 0.5, "medium"),
                 (0, 0.5, 0.25, 0.5, "medium"), (0.25, 0.5, 0.25, 0.5, "medium"), (0.5, 0.5, 0.25, 0.5, "medium"),
                 (0.75, 0.5, 0.25, 0.5, "medium")]
            ],
            9: [
                
                [(0, 0, 0.33, 0.33, "medium"), (0.33, 0, 0.34, 0.33, "medium"), (0.67, 0, 0.33, 0.33, "medium"),
                 (0, 0.33, 0.33, 0.34, "medium"), (0.33, 0.33, 0.34, 0.34, "medium"),
                 (0.67, 0.33, 0.33, 0.34, "medium"),
                 (0, 0.67, 0.33, 0.33, "medium"), (0.33, 0.67, 0.34, 0.33, "medium"),
                 (0.67, 0.67, 0.33, 0.33, "medium")],
                
                [(0.3, 0.3, 0.4, 0.4, "large"), (0, 0, 0.3, 0.3, "small"), (0.7, 0, 0.3, 0.3, "small"),
                 (0, 0.7, 0.3, 0.3, "small"), (0.7, 0.7, 0.3, 0.3, "small"), (0.3, 0, 0.4, 0.3, "medium"),
                 (0, 0.3, 0.3, 0.4, "medium"), (0.7, 0.3, 0.3, 0.4, "medium"), (0.3, 0.7, 0.4, 0.3, "medium")]
            ],
            10: [
                
                [(0, 0, 0.2, 0.5, "medium"), (0.2, 0, 0.2, 0.5, "medium"), (0.4, 0, 0.2, 0.5, "medium"),
                 (0.6, 0, 0.2, 0.5, "medium"), (0.8, 0, 0.2, 0.5, "medium"),
                 (0, 0.5, 0.2, 0.5, "medium"), (0.2, 0.5, 0.2, 0.5, "medium"), (0.4, 0.5, 0.2, 0.5, "medium"),
                 (0.6, 0.5, 0.2, 0.5, "medium"), (0.8, 0.5, 0.2, 0.5, "medium")]
            ],
            11: [
                
                [(0, 0, 0.3, 0.4, "medium"), (0.3, 0, 0.4, 0.6, "large"), (0.7, 0, 0.3, 0.3, "small"),
                 (0, 0.4, 0.15, 0.3, "small"), (0.15, 0.4, 0.15, 0.3, "small"), (0.7, 0.3, 0.3, 0.3, "small"),
                 (0, 0.7, 0.14, 0.3, "small"), (0.14, 0.7, 0.14, 0.3, "small"), (0.28, 0.7, 0.14, 0.3, "small"),
                 (0.42, 0.7, 0.14, 0.3, "small"), (0.56, 0.7, 0.44, 0.3, "medium")]
            ],
            12: [
                
                [(0, 0, 0.25, 0.33, "medium"), (0.25, 0, 0.25, 0.33, "medium"), (0.5, 0, 0.25, 0.33, "medium"),
                 (0.75, 0, 0.25, 0.33, "medium"),
                 (0, 0.33, 0.25, 0.34, "medium"), (0.25, 0.33, 0.25, 0.34, "medium"), (0.5, 0.33, 0.25, 0.34, "medium"),
                 (0.75, 0.33, 0.25, 0.34, "medium"),
                 (0, 0.67, 0.25, 0.33, "medium"), (0.25, 0.67, 0.25, 0.33, "medium"), (0.5, 0.67, 0.25, 0.33, "medium"),
                 (0.75, 0.67, 0.25, 0.33, "medium")],
                
                [(0.1, 0.05, 0.8, 0.3, "large"), (0, 0.35, 0.2, 0.3, "small"), (0.2, 0.35, 0.15, 0.3, "small"),
                 (0.35, 0.35, 0.15, 0.3, "small"), (0.5, 0.35, 0.15, 0.3, "small"), (0.65, 0.35, 0.15, 0.3, "small"),
                 (0.8, 0.35, 0.2, 0.3, "small"),
                 (0, 0.65, 0.2, 0.35, "small"), (0.2, 0.65, 0.2, 0.35, "small"), (0.4, 0.65, 0.2, 0.35, "small"),
                 (0.6, 0.65, 0.2, 0.35, "small"), (0.8, 0.65, 0.2, 0.35, "small")]
            ]
        }

    def apply_pattern(self, pattern, card_count):
        layout = []
        for i, (rel_x, rel_y, rel_width, rel_height, size_class) in enumerate(pattern[:card_count]):
            x = rel_x * self.container_width + self.gap / 2
            y = rel_y * self.container_height + self.gap / 2
            width = (rel_width * self.container_width) - self.gap
            height = (rel_height * self.container_height) - self.gap
            width = max(width, 80)
            height = max(height, 80)
            layout.append({'x': x, 'y': y, 'width': width, 'height': height, 'size_class': size_class})
        return layout

    def create_simple_grid(self, card_count):
        cols = int(math.sqrt(card_count))
        rows = math.ceil(card_count / cols)
        card_width = (self.container_width - (cols + 1) * self.gap) / cols
        card_height = (self.container_height - (rows + 1) * self.gap) / rows
        layout = []
        for i in range(card_count):
            row = i // cols
            col = i % cols
            x = col * (card_width + self.gap) + self.gap
            y = row * (card_height + self.gap) + self.gap
            layout.append({'x': x, 'y': y, 'width': card_width, 'height': card_height, 'size_class': 'medium'})
        return layout






class ImageDownloadWorker(QRunnable):
    class Signals(QObject):
        finished = Signal(str, QPixmap)
        error = Signal(str)

    def __init__(self, url, track_id):
        super().__init__()
        self.url = url
        self.track_id = track_id
        self.signals = self.Signals()

    def run(self):
        try:
            if not self.url:
                return
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            pixmap = QPixmap()
            if pixmap.loadFromData(response.content):
                self.signals.finished.emit(self.track_id, pixmap)
        except Exception as e:
            self.signals.error.emit(f"Error downloading image: {str(e)}")


class RecommendationWorker(QRunnable):
    class Signals(QObject):
        finished = Signal(list)
        error = Signal(str)
        progress = Signal(str)

    def __init__(self, all_songs, sp_client, groq_client):
        super().__init__()
        self.all_songs = all_songs
        self.signals = self.Signals()
        
        self.sp = sp_client
        self.groq_client = groq_client

    def run(self):
        try:
            
            if not self.groq_client or not self.sp:
                self.signals.error.emit("AI or Spotify services not available. Check API keys in Settings.")
                return
            if not self.all_songs:
                self.signals.error.emit("No songs in library")
                return
            self.signals.progress.emit("Analyzing your music taste...")
            user_data = self.prepare_user_music_data()
            self.signals.progress.emit("Getting AI recommendations...")
            ai_recommendations = self.get_groq_recommendations(user_data)
            if not ai_recommendations:
                self.signals.error.emit("Unable to generate recommendations")
                return
            self.signals.progress.emit("Fetching metadata...")
            spotify_tracks = self.get_spotify_metadata(ai_recommendations)
            filtered_recommendations = self.filter_recommendations(spotify_tracks)
            if not filtered_recommendations:
                self.signals.error.emit("All recommended songs are already in your library")
                return
            self.signals.finished.emit(filtered_recommendations)
        except Exception as e:
            self.signals.error.emit(f"Error: {str(e)}")

    def prepare_user_music_data(self):
        songs_data = []
        artists_data = set()
        for song in self.all_songs:
            song_name = song.get('song_name', '')
            artist_name = song.get('artist', '')
            if song_name and artist_name:
                songs_data.append(f"{song_name} by {artist_name}")
                artists_data.add(artist_name)
        return {"songs": songs_data[:20], "artists": list(artists_data)[:15], "total_songs": len(self.all_songs)}

    def get_groq_recommendations(self, user_data):
        """Get music recommendations from Groq AI with improved error handling and detailed prompting"""
        try:
            
            if not user_data or not isinstance(user_data, dict):
                print("Invalid user_data provided")
                return []

            songs = user_data.get("songs", [])
            artists = user_data.get("artists", [])
            total_songs = user_data.get("total_songs", len(songs))

            if not songs and not artists:
                print("No songs or artists found in user data")
                return []

            
            songs_list = ", ".join([f'"{song}"' for song in songs[:50]])  
            artists_list = ", ".join([f'"{artist}"' for artist in artists[:30]])  

            
            prompt = f"""You are a professional music recommendation AI. Based on the user's music library data below, recommend exactly 12 songs that match their taste.

       USER'S MUSIC LIBRARY ANALYSIS:
       - Total songs in library: {total_songs}
       - Sample songs: {songs_list}
       - Favorite artists: {artists_list}

       RECOMMENDATION REQUIREMENTS:
       1. Recommend EXACTLY 12 songs
       2. ONLY original versions (NO remixes, slowed versions, reverb versions, speed up versions, acoustic versions, live versions)
       3. ONLY official studio recordings by original artists
       4. DO NOT repeat ANY songs already in the user's library
       5. Provide a diverse mix including:
          - Songs by artists the user already likes (40% weight)
          - Similar artists in the same genres (40% weight)  
          - Discovery songs from related genres (20% weight)
       6. Focus on high-quality, popular, and critically acclaimed tracks
       7. Consider musical elements like tempo, mood, instrumentation that match user's taste
       8. Ensure variety in release years (mix of classic and recent tracks)

       RESPONSE FORMAT REQUIREMENTS:
       - Respond with ONLY valid JSON
       - Use the exact structure shown below
       - Wrap the song array in a "songs" object
       - Use proper JSON formatting with double quotes
       - No additional text, explanations, or markdown

       REQUIRED JSON STRUCTURE:
       {{
         "songs": [
           {{"song_name": "Song Title Here", "artist_name": "Artist Name Here"}},
           {{"song_name": "Song Title Here", "artist_name": "Artist Name Here"}}
         ]
       }}

       Generate recommendations now:"""

            
            completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                temperature=0.8,  
                max_tokens=1024,  
                response_format={"type": "json_object"},
                stream=False,
            )

            response_text = completion.choices[0].message.content.strip()
            print("Raw Groq Response:", response_text)

            
            recommendations_songs = []

            try:
                
                recommendations = json.loads(response_text)

                
                if "songs" in recommendations:
                    recommendations_songs = recommendations["songs"]
                elif isinstance(recommendations, list):
                    recommendations_songs = recommendations
                else:
                    print("Unexpected JSON structure:", recommendations.keys())
                    return []

            except json.JSONDecodeError as json_error:
                print(f"JSON parsing failed: {json_error}")

                
                try:
                    
                    clean_text = response_text.replace("```json", "").replace("```", "").strip()

                    
                    recommendations = json.loads(clean_text)

                    if "songs" in recommendations:
                        recommendations_songs = recommendations["songs"]
                    elif isinstance(recommendations, list):
                        recommendations_songs = recommendations

                except json.JSONDecodeError:
                    print("All JSON parsing attempts failed")
                    return []

            
            if not isinstance(recommendations_songs, list):
                print("Recommendations is not a list:", type(recommendations_songs))
                return []

            
            validated_songs = []
            for song in recommendations_songs:
                if not isinstance(song, dict):
                    print(f"Invalid song format: {song}")
                    continue

                song_name = song.get("song_name", "").strip()
                artist_name = song.get("artist_name", "").strip()

                
                if not song_name or not artist_name:
                    print(f"Missing song_name or artist_name: {song}")
                    continue

                
                user_songs_lower = [s.lower() for s in songs]
                if song_name.lower() in user_songs_lower:
                    print(f"Song already in library: {song_name}")
                    continue

                
                unwanted_keywords = [
                    'remix', 'slowed', 'reverb', 'speed up', 'sped up',
                    'acoustic', 'live', 'cover', 'karaoke', 'instrumental',
                    '(remix)', '(slowed)', '(reverb)', '(acoustic)', '(live)'
                ]

                song_name_lower = song_name.lower()
                if any(keyword in song_name_lower for keyword in unwanted_keywords):
                    print(f"Filtered out unwanted version: {song_name}")
                    continue

                validated_songs.append({
                    "song_name": song_name,
                    "artist_name": artist_name
                })

            print(f"Successfully validated {len(validated_songs)} recommendations")
            return validated_songs

        except Exception as e:
            print(f"Groq recommendation error: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            return []

    def get_spotify_metadata(self, ai_recommendations):
        spotify_tracks = []
        for rec in ai_recommendations:
            try:
                song_name = rec.get('song_name', '')
                artist_name = rec.get('artist_name', '')
                if not song_name or not artist_name:
                    continue
                search_query = f'track:"{song_name}" artist:"{artist_name}"'
                results = self.sp.search(q=search_query, type='track', limit=1, market='US')
                if results and results['tracks']['items']:
                    spotify_tracks.append(results['tracks']['items'][0])
                else:
                    results = self.sp.search(q=f"{song_name} {artist_name}", type='track', limit=1, market='US')
                    if results and results['tracks']['items']:
                        spotify_tracks.append(results['tracks']['items'][0])
            except Exception:
                continue
        return spotify_tracks

    def filter_recommendations(self, spotify_tracks):
        if not spotify_tracks:
            return []
        existing_songs = {f"{s.get('song_name', '').lower().strip()}|{s.get('artist', '').lower().strip()}" for s in
                          self.all_songs}
        filtered = []
        seen_tracks = set()
        for track in spotify_tracks:
            track_name = track.get('name', '').lower().strip()
            artist_name = track['artists'][0]['name'].lower().strip() if track.get('artists') else ''
            track_key = f"{track_name}|{artist_name}"
            if track_key not in existing_songs and track_key not in seen_tracks:
                filtered.append(track)
                seen_tracks.add(track_key)
        return filtered


class PicksForYouWidget(QWidget):
    """Main widget for displaying AI-powered personalized music recommendations with handcrafted layouts"""
    CYCLE_INTERVAL_MS = 12000  

    def __init__(self, main_frame):
        super().__init__(main_frame)
        self.main_frame = main_frame
        self.threadpool = QThreadPool()
        self.recommendation_cards = []
        self.image_cache = {}
        self.all_recommendations = []
        self.current_displayed_tracks = []
        self.animation_timer = QTimer(self)  
        self.animation_timer.timeout.connect(self.cycle_recommendations)

        
        self.is_mouse_over = False
        self.timer_was_active = False

        self.setup_ui()

    
    def enterEvent(self, event):
        """Handle mouse entering the widget - pause cycling"""
        self.is_mouse_over = True
        if self.animation_timer.isActive():
            self.timer_was_active = True
            self.animation_timer.stop()
        super().enterEvent(event)

    
    def leaveEvent(self, event):
        """Handle mouse leaving the widget - resume cycling"""
        self.is_mouse_over = False
        if self.timer_was_active and len(self.all_recommendations) > len(self.current_displayed_tracks):
            self.animation_timer.start(self.CYCLE_INTERVAL_MS)
            self.timer_was_active = False
        super().leaveEvent(event)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        header_layout = QHBoxLayout()
        title_label = QLabel("Picks for You")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #eeeeee; background: transparent;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Refresh Recommendations")
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.setStyleSheet("""
            QPushButton { background: rgba(255, 255, 255, 0.1); border: none; border-radius: 16px; font-size: 16px; color: 
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); }""")
        self.refresh_btn.clicked.connect(self.refresh_recommendations)
        header_layout.addWidget(self.refresh_btn)
        layout.addLayout(header_layout)
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.status_label = QLabel("Loading your personalized picks...", self.grid_container)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #a0a0a0; font-size: 14px; background: transparent; padding: 40px;")
        layout.addWidget(self.grid_container, 1)

    def load_recommendations(self):
        if not hasattr(self.main_frame, 'all_songs') or not self.main_frame.all_songs:
            self.status_label.setText("Add songs to your library for personalized recommendations!")
            self.status_label.show()
            self.status_label.setGeometry(self.grid_container.rect())
            return

        if not self.main_frame.sp or not self.main_frame.groq_client:
            self.status_label.setText("Please configure your Spotify and Groq API keys in Settings.")
            self.status_label.show()
            self.status_label.setGeometry(self.grid_container.rect())
            return

        worker = RecommendationWorker(
            self.main_frame.all_songs,
            self.main_frame.sp,
            self.main_frame.groq_client
        )
        worker.signals.finished.connect(self.on_all_recommendations_loaded)
        worker.signals.error.connect(self.handle_error)
        worker.signals.progress.connect(self.update_status)
        self.threadpool.start(worker)

    def on_all_recommendations_loaded(self, recommendations):
        if not recommendations:
            self.handle_error("No new recommendations found!")
            return
        self.all_recommendations = recommendations

        self.create_dynamic_grid()

    def get_container_category(self):
        area = self.grid_container.width() * self.grid_container.height()
        if area < 150000:
            return "small"
        elif area < 350000:
            return "medium"
        else:
            return "large"

    def get_optimal_card_count(self, container_category):
        if container_category == "small":
            return random.randint(3, 4)
        elif container_category == "medium":
            return random.randint(5, 8)
        else:
            return random.randint(8, 12)

    def select_tracks_to_display(self, count):
        count = min(count, len(self.all_recommendations))

        available_tracks = [t for t in self.all_recommendations if t not in self.current_displayed_tracks]
        if len(available_tracks) >= count:
            return random.sample(available_tracks, count)
        else:
            return random.sample(self.all_recommendations, count)

    def create_dynamic_grid(self):
        """Create handcrafted layout grid and manage the animation timer."""
        self.animation_timer.stop()
        self.timer_was_active = False

        if not self.all_recommendations:
            return

        self.clear_grid(stop_timer=False)

        available_width = self.grid_container.width()
        available_height = self.grid_container.height()
        if available_width <= 50 or available_height <= 50:
            QTimer.singleShot(50, self.create_dynamic_grid)
            return

        container_category = self.get_container_category()
        optimal_count = self.get_optimal_card_count(container_category)

        self.current_displayed_tracks = self.select_tracks_to_display(optimal_count)

        if not self.current_displayed_tracks:
            return

        layout_manager = HandcraftedLayoutManager(available_width, available_height, gap=6)
        card_layouts = layout_manager.get_layout(len(self.current_displayed_tracks))

        for i, (track, layout_info) in enumerate(zip(self.current_displayed_tracks, card_layouts)):
            card = RecommendationCard(self.grid_container, track, self.main_frame, layout_info['size_class'])
            card.setGeometry(int(layout_info['x']), int(layout_info['y']), int(layout_info['width']),
                             int(layout_info['height']))
            card.show()
            card.fade_in(duration=600)
            self.recommendation_cards.append(card)
            self.download_album_cover(track, card)

        self.status_label.hide()

        if (len(self.all_recommendations) > len(self.current_displayed_tracks) and
                not self.is_mouse_over):
            self.animation_timer.start(self.CYCLE_INTERVAL_MS)
            self.timer_was_active = False
        elif len(self.all_recommendations) > len(self.current_displayed_tracks):
            self.timer_was_active = True

    def cycle_recommendations(self):
        """Cycle through recommendations with fade animation."""
        if len(self.all_recommendations) <= 3:
            return

        cards_to_remove = self.recommendation_cards[:]
        self.recommendation_cards.clear()

        self.fade_out_counter = len(cards_to_remove)

        def on_fade_out_complete():
            self.fade_out_counter -= 1
            if self.fade_out_counter <= 0:
                for card in cards_to_remove:
                    card.deleteLater()
                QTimer.singleShot(100, self.create_dynamic_grid)

        if not cards_to_remove:
            self.create_dynamic_grid()
            return

        for card in cards_to_remove:
            card.fade_out(duration=400, callback=on_fade_out_complete)

    def resizeEvent(self, event):
        """Handle resize event to regenerate the grid."""
        super().resizeEvent(event)
        self.status_label.setGeometry(self.grid_container.rect())

        if self.all_recommendations and not self.status_label.isVisible():
            self.animation_timer.stop()
            if not hasattr(self, '_resize_timer'):
                self._resize_timer = QTimer(self)
                self._resize_timer.setSingleShot(True)
                self._resize_timer.timeout.connect(self.create_dynamic_grid)
            self._resize_timer.start(250)

    def download_album_cover(self, track, card):
        """Download album cover for a card."""
        track_id = track.get('id', '')
        cover_url = None
        if track.get('album', {}).get('images'):
            cover_url = track['album']['images'][0]['url']

        if track_id in self.image_cache:
            card.set_cover_image(self.image_cache[track_id])
            return

        if not cover_url:
            return

        worker = ImageDownloadWorker(cover_url, track_id)
        worker.signals.finished.connect(lambda tid, pixmap, c=card: self.update_card_image(tid, pixmap, c))
        self.threadpool.start(worker)

    def update_card_image(self, track_id, pixmap, card):
        """Update card with downloaded image."""
        self.image_cache[track_id] = pixmap
        if card in self.recommendation_cards:
            card.set_cover_image(pixmap)

    def clear_grid(self, stop_timer=True):
        """Clear existing grid and optionally stop cycling."""
        if stop_timer:
            self.animation_timer.stop()
        for card in self.recommendation_cards:
            card.deleteLater()
        self.recommendation_cards.clear()

    def refresh_recommendations(self):
        """Refresh recommendations with new grid."""
        self.update_status("Getting fresh recommendations...")
        self.clear_grid()
        self.all_recommendations = []
        self.current_displayed_tracks = []
        QTimer.singleShot(100, self.load_recommendations)

    def handle_error(self, error_message):
        """Handle loading errors."""
        self.clear_grid()
        self.status_label.setText(f"Error: {error_message}")
        self.status_label.show()
        self.status_label.setGeometry(self.grid_container.rect())

    def update_status(self, message):
        """Update status message."""
        self.clear_grid()
        self.status_label.setText(message)
        self.status_label.show()
        self.status_label.setGeometry(self.grid_container.rect())
