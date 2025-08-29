from PySide6.QtCore import Qt


class ShortcutHandler:
    """
    Handles global keyboard shortcuts for the main application window.
    This class is instantiated in the main VibeFlow window and its
    `handle_key_press` method is called from the window's `keyPressEvent`.
    """

    def __init__(self, main_window):
        """
        Initializes the shortcut handler.

        Args:
            main_window: A reference to the main VibeFlow QMainWindow instance.
        """
        self.main_window = main_window

    def handle_key_press(self, event):
        """
        Processes a QKeyEvent and triggers corresponding actions.

        Args:
            event: The QKeyEvent object from the keyPressEvent.
        """
        key = event.key()
        modifiers = event.modifiers()

        # We ignore shortcuts if a text input field (like a search box) has focus
        # to allow normal typing.
        if isinstance(self.main_window.focusWidget(), (
                getattr(__import__('PySide6.QtWidgets', fromlist=['QLineEdit']), 'QLineEdit'),
                getattr(__import__('PySide6.QtWidgets', fromlist=['QSpinBox']), 'QSpinBox'),
                getattr(__import__('PySide6.QtWidgets', fromlist=['QTextEdit']), 'QTextEdit'),
                getattr(__import__('PySide6.QtWidgets', fromlist=['QPlainTextEdit']), 'QPlainTextEdit'))):

            # For text input widgets, only handle specific shortcuts with modifiers
            if modifiers == Qt.ControlModifier and key == Qt.Key_B:
                # Ctrl + B: Toggle Home Screen Side Panel (works even in text fields)
                self.main_window.toggle_home_screen()
                event.accept()
                return True

            # Let text input widgets handle their own keys normally
            return False

        player = self.main_window.player
        now_playing_view = self.main_window.now_playing_view

        # --- Playback Controls ---

        # Spacebar: Play/Pause
        if key == Qt.Key_W and modifiers == Qt.NoModifier:
            now_playing_view.play_pause()
            event.accept()
            return True

        elif key == Qt.Key_Greater and modifiers == Qt.ShiftModifier:
            now_playing_view.next_song()
            event.accept()
            return True

        elif key == Qt.Key_Less and modifiers == Qt.ShiftModifier:
            now_playing_view.prev_song()
            event.accept()
            return True

        # --- Seeking ---

        # Right Arrow: Seek forward 10 seconds
        elif key == Qt.Key_D and modifiers == Qt.NoModifier:
            new_pos = min(player.position() + 10000, player.duration())
            player.setPosition(new_pos)
            event.accept()
            return True

        # Left Arrow: Seek backward 10 seconds
        elif key == Qt.Key_A and modifiers == Qt.NoModifier:
            new_pos = max(player.position() - 10000, 0)
            player.setPosition(new_pos)
            event.accept()
            return True

        elif key == Qt.Key_M and modifiers == Qt.NoModifier:
            self.main_window.audio_output.setMuted(not self.main_window.audio_output.isMuted())
            event.accept()
            return True

        elif key == Qt.Key_L and modifiers == Qt.NoModifier:
            if self.main_window.main_stack.currentWidget() == self.main_window.lyrics_view:
                self.main_window.show_frame(self.main_window.main_view_widget)
            else:
                self.main_window.show_frame(self.main_window.lyrics_view)
            event.accept()
            return True

        elif key == Qt.Key_Q and modifiers == Qt.NoModifier:
            queue_view = now_playing_view.queue_view
            if queue_view.is_visible:
                queue_view.hide_queue()
            else:
                now_playing_view.show_queue()
            event.accept()
            return True

        elif key == Qt.Key_S and modifiers == Qt.NoModifier:
            now_playing_view.cycle_play_mode()
            event.accept()
            return True

        # Ctrl + B: Toggle Home Screen Side Panel
        elif key == Qt.Key_B and modifiers == Qt.ControlModifier:
            self.main_window.toggle_home_screen()
            event.accept()
            return True

        elif key == Qt.Key_M and modifiers == Qt.ControlModifier:
            self.main_window.open_mini_player()
            event.accept()
            return True
        return False