import os
import shutil
import asyncio
from pathlib import Path

try:
    import winrt.windows.media.playback as win_media_playback
    import winrt.windows.media as win_media
    import winrt.windows.storage as win_storage
    import winrt.windows.storage.streams as win_streams
    from winrt.windows.foundation import Uri

    WINRT_AVAILABLE = True
except ImportError:
    print("SMTC: WinRT not available — SMTC features disabled. Install 'winrt'.")
    WINRT_AVAILABLE = False


class SMTCHandler:
    """
    Handles integration with Windows System Media Transport Controls (SMTC)
    using a dummy WinRT MediaPlayer for metadata + headset button control.
    """

    def __init__(self, main_window):
        self.enabled = False
        if not WINRT_AVAILABLE:
            return

        try:
            self.main_window = main_window
            self.player = getattr(main_window, "player", None)
            if self.player is None:
                print("SMTC: No QMediaPlayer found in main window — disabled.")
                return

            self.winrt_player = win_media_playback.MediaPlayer()
            self.winrt_player.command_manager.is_enabled = False

            self.smtc = self.winrt_player.system_media_transport_controls
            self.smtc.is_enabled = True
            self.smtc.is_play_enabled = True
            self.smtc.is_pause_enabled = True
            self.smtc.is_next_enabled = True
            self.smtc.is_previous_enabled = True

            self.smtc.add_button_pressed(self._on_button_pressed)

            self.update_playback_status(self.player.playbackState())

            self.enabled = True
            print("SMTC: Initialized.")
        except Exception as e:
            print(f"SMTC: Failed to initialize -> {e}")
            self.enabled = False

    # ---------- INTERNAL HELPERS ----------

    def _safe_cover_path(self, cover_path):
        """Copy cover image to AppData\Roaming\VibeFlow Music\cover.png and return that path."""
        app_data_dir = Path(os.getenv('APPDATA')) / "VibeFlow Music"
        app_data_dir.mkdir(parents=True, exist_ok=True)

        safe_path = app_data_dir / "cover.png"
        shutil.copyfile(cover_path, safe_path)

        return safe_path

    async def _update_thumbnail_async(self, updater, cover_path):
        """Load local file via StorageFile to ensure WinRT can use it."""
        try:
            file = await win_storage.StorageFile.get_file_from_path_async(str(Path(cover_path)))
            updater.thumbnail = win_streams.RandomAccessStreamReference.create_from_file(file)
        except Exception as e:
            print(f"SMTC: Failed to load thumbnail via StorageFile -> {e}")
            updater.thumbnail = None

    # ---------- PUBLIC API ----------

    def update_metadata(self, song_info):
        if not self.enabled or not song_info:
            return

        # Skip if no actual media loaded
        try:
            if not self.player.source().isLocalFile() or not self.player.source().toLocalFile():
                return
        except Exception:
            return

        try:
            updater = self.smtc.display_updater
            updater.type = win_media.MediaPlaybackType.MUSIC
            updater.music_properties.title = song_info.get('song_name', 'Unknown Song')
            updater.music_properties.artist = song_info.get('artist', 'Unknown Artist')
            if 'album' in song_info:
                updater.music_properties.album_title = song_info['album']

            cover_path = song_info.get('cover_location')
            if cover_path and Path(cover_path).exists():
                try:
                    safe_path = self._safe_cover_path(cover_path)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._update_thumbnail_async(updater, safe_path))
                    loop.close()
                except Exception as e:
                    print(f"SMTC: Thumbnail async update failed -> {e}")
                    updater.thumbnail = None
            else:
                updater.thumbnail = None

            updater.update()
        except Exception as e:
            print(f"SMTC: Failed to update metadata -> {e}")

    def update_playback_status(self, qt_playback_state):
        if not self.enabled:
            return
        try:
            playing = getattr(self.player.PlaybackState, "PlayingState", 1)
            paused = getattr(self.player.PlaybackState, "PausedState", 2)
            stopped = getattr(self.player.PlaybackState, "StoppedState", 0)

            if qt_playback_state == playing:
                self.smtc.playback_status = win_media.MediaPlaybackStatus.PLAYING
            elif qt_playback_state == paused:
                self.smtc.playback_status = win_media.MediaPlaybackStatus.PAUSED
            elif qt_playback_state == stopped:
                self.smtc.playback_status = win_media.MediaPlaybackStatus.STOPPED
            else:
                self.smtc.playback_status = win_media.MediaPlaybackStatus.CLOSED
        except Exception as e:
            print(f"SMTC: Failed to update playback status -> {e}")

    def shutdown(self):
        if not self.enabled:
            return
        try:
            self.smtc.playback_status = win_media.MediaPlaybackStatus.CLOSED
            self.smtc.display_updater.clear_all()
            self.smtc.is_enabled = False
            self.enabled = False
            print("SMTC: Shutdown.")
        except Exception as e:
            print(f"SMTC: Shutdown failed -> {e}")

    # ---------- BUTTON HANDLERS ----------

    def _on_button_pressed(self, sender, args):
        if not self.enabled:
            return
        try:
            button = args.button
            if button == win_media.SystemMediaTransportControlsButton.PLAY:
                self._qt_play_pause()
            elif button == win_media.SystemMediaTransportControlsButton.PAUSE:
                self._qt_play_pause()
            elif button == win_media.SystemMediaTransportControlsButton.NEXT:
                self._qt_next()
            elif button == win_media.SystemMediaTransportControlsButton.PREVIOUS:
                self._qt_prev()
        except Exception as e:
            print(f"SMTC: Button handler failed -> {e}")

    # ---------- APP-SPECIFIC ACTIONS ----------

    def _qt_play_pause(self):
        """Handle play/pause from SMTC - call the main app's play_pause method"""
        try:
            # Call the play_pause method from NowPlayingView which handles all the logic
            self.main_window.now_playing_view.play_pause()
        except Exception as e:
            print(f"SMTC: Play/pause failed -> {e}")

    def _qt_next(self):
        print("next")
        """Handle next song from SMTC"""
        try:
            if hasattr(self.main_window, 'now_playing_view'):
                self.main_window.now_playing_view.next_song()
            else:
                print("SMTC: now_playing_view not found")
        except Exception as e:
            print(f"SMTC: Next song failed -> {e}")

    def _qt_prev(self):
        """Handle previous song from SMTC"""
        try:
            if hasattr(self.main_window, 'now_playing_view'):
                self.main_window.now_playing_view.prev_song()
            else:
                print("SMTC: now_playing_view not found")
        except Exception as e:
            print(f"SMTC: Previous song failed -> {e}")
