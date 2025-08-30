from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QFileDialog, QMessageBox)
from .frame_functions.utils import create_button


class SettingsFrame(QWidget):
    def __init__(self, parent=None, back_callback=None):
        super().__init__(parent)
        self.main_frame = parent
        self.back_callback = back_callback
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        self.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(25)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        back_button = create_button("icons/back-arrow.png", self.go_back, 24)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #eeeeee; background: transparent;")

        header_layout.addWidget(back_button)
        header_layout.addWidget(title)
        header_layout.addStretch()

        shortcut_button = create_button("icons/menu.png", self.main_frame.show_shortcut_guide, 22)
        shortcut_button.setToolTip("Show Shortcut Guide (Ctrl+I)")

        header_layout.addWidget(shortcut_button)
        main_layout.addLayout(header_layout)

        api_header_layout = QHBoxLayout()
        api_title = QLabel("API Keys")
        api_title.setStyleSheet(
            "font-size: 16px; font-weight: 500; color: #cccccc; background: transparent; margin-top: 10px; margin-bottom: 5px;")
        api_header_layout.addWidget(api_title)
        api_header_layout.addStretch()

        groq_link = QLabel(
            '<a href="https://console.groq.com/keys" style="color: #7aa2f7; text-decoration: none;">Get Groq Key</a>')
        groq_link.setOpenExternalLinks(True)
        groq_link.setToolTip("Opens console.groq.com in your browser")

        spotify_link = QLabel(
            '<a href="https://developer.spotify.com/dashboard" style="color: #1DB954; text-decoration: none;">Get Spotify Keys</a>')
        spotify_link.setOpenExternalLinks(True)
        spotify_link.setToolTip("Opens developer.spotify.com in your browser")

        links_layout = QVBoxLayout()
        links_layout.setSpacing(0)
        links_layout.setAlignment(Qt.AlignBottom)
        links_layout.addWidget(groq_link)
        links_layout.addWidget(spotify_link)

        api_header_layout.addLayout(links_layout)

        main_layout.addLayout(api_header_layout)

        self.groq_api_key_input = self.create_setting_input("Groq API Key (for AI Recommendations)", is_password=True)
        main_layout.addLayout(self.groq_api_key_input['layout'])

        self.spotify_client_id_input = self.create_setting_input("Spotify Client ID (for Search/Import)")
        main_layout.addLayout(self.spotify_client_id_input['layout'])

        self.spotify_client_secret_input = self.create_setting_input("Spotify Client Secret", is_password=True)
        main_layout.addLayout(self.spotify_client_secret_input['layout'])

        general_title = QLabel("General")
        general_title.setStyleSheet(
            "font-size: 16px; font-weight: 500; color: #cccccc; background: transparent; margin-top: 20px; margin-bottom: 5px;")
        main_layout.addWidget(general_title)

        download_path_layout = QHBoxLayout()
        download_path_layout.setSpacing(10)
        self.download_path_edit = QLineEdit()
        self.download_path_edit.setPlaceholderText("Music Download Path")
        self.download_path_edit.setReadOnly(True)
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_download_path)
        download_path_layout.addWidget(QLabel("Download Path:"))
        download_path_layout.addWidget(self.download_path_edit, 1)
        download_path_layout.addWidget(browse_button)
        main_layout.addLayout(download_path_layout)

        main_layout.addStretch()

        save_button_layout = QHBoxLayout()
        save_button_layout.addStretch()
        save_button = QPushButton("Save and Apply Changes")
        save_button.clicked.connect(self.save_settings)
        save_button.setMinimumHeight(40)
        save_button_layout.addWidget(save_button)
        main_layout.addLayout(save_button_layout)

    def create_setting_input(self, label_text, is_password=False):
        layout = QHBoxLayout()
        label = QLabel(f"{label_text}:")
        line_edit = QLineEdit()
        if is_password:
            line_edit.setEchoMode(QLineEdit.Password)

        line_edit.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                color: #e0e0e0;
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
            }
            QLineEdit:focus {
                border-color: rgba(255, 255, 255, 0.5);
            }
        """)

        layout.addWidget(label)
        layout.addWidget(line_edit, 1)
        return {"layout": layout, "widget": line_edit}

    def go_back(self):
        if self.back_callback:
            self.back_callback()

    def browse_download_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Music Download Directory")
        if path:
            self.download_path_edit.setText(path)

    def load_settings(self):
        """Load current settings from the main frame into the input fields."""
        settings = self.main_frame.settings
        self.groq_api_key_input['widget'].setText(settings.get('groq_api_key', ''))
        self.spotify_client_id_input['widget'].setText(settings.get('spotify_client_id', ''))
        self.spotify_client_secret_input['widget'].setText(settings.get('spotify_client_secret', ''))
        self.download_path_edit.setText(settings.get('download_path', ''))

    def save_settings(self):
        """Save settings and apply them."""
        self.main_frame.settings['groq_api_key'] = self.groq_api_key_input['widget'].text().strip()
        self.main_frame.settings['spotify_client_id'] = self.spotify_client_id_input['widget'].text().strip()
        self.main_frame.settings['spotify_client_secret'] = self.spotify_client_secret_input['widget'].text().strip()
        self.main_frame.settings['download_path'] = self.download_path_edit.text().strip()

        self.main_frame.update_settings_in_json()

        self.main_frame.init_api_clients()

        QMessageBox.information(self, "Settings Saved",
                                "Your settings have been saved. API clients have been re-initialized.")
        self.go_back()