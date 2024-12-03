<p align="center">
  <img src="https://res.cloudinary.com/db2vusdvh/image/upload/v1733220951/VibeFlow_Music_o3mren.png"/>
</p>

# VibeFlow Music 🎵

VibeFlow Music is an all-in-one music player solution that combines the power of seamless music playback with modern features, beautiful interface, and hassle-free music downloading capabilities. Built with Python and PySide6, it offers a premium music experience without any subscriptions or advertisements.

## 🌟 The Story Behind

As a developer who codes while listening to music, I found myself increasingly frustrated with the limitations of existing music platforms and players. The constant interruption of ads on Spotify led me to search for alternatives, but I encountered a common problem: existing solutions were fragmented. Music players lacked downloading capabilities, downloaders lacked proper playback features, and applications that offered both often came with subscription fees or subpar user interfaces.

This frustration sparked the creation of VibeFlow Music - a solution that seamlessly integrates all essential features into one elegant, user-friendly application.

## 🚀 Installation

### Method 1: Quick Install (Windows)
1. Download the latest `Vibeflow-setup.exe` from the [releases page](https://github.com/qa-p1/Vibeflow/releases/tag/first)
2. Run the installer and follow the on-screen instructions
3. Launch VibeFlow Music and enjoy! 🎉

### Method 2: From Source
1. Clone the repository:
```bash
git clone https://github.com/VTxHive/Vibeflow-Music.git
cd Vibeflow-Music
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python main.py
```

### Requirements
- Python 3.8 or higher
- PySide6
- Other dependencies are listed in `requirements.txt`:
  - PySide6
  - spotipy
  - yt_dlp

### System Requirements
- OS: Windows 10/11, macOS 10.14+, or Linux
- RAM: 4GB minimum (8GB recommended)
- Storage: 500MB for installation

---
## ✨ Features

### Core Functionality
- 🎯 **Modern GUI Experience**: Built with PySide6 for a sleek, responsive interface
- 🎶 **Advanced Music Queue Management**: Organize your listening experience
- 📱 **Mini Player Mode**: Perfect for multitasking
- 🎵 **Multiple Player Modes**: Adapt to your listening style

### Music Management
- 📃 **Lyrics Support**: Never miss a word of your favorite songs
- 📂 **Multiple Playlist Options**: Organize your music library your way
- 🔄 **Spotify Playlist Import**: Easily import your existing Spotify playlists
- 🔍 **Smart Search**: Find your favorite music instantly

### Enhanced Experience
- ⏰ **Sleep Timer**: Perfect for falling asleep to music
- ⬇️ **Easy Music Downloads**: Integrated downloading capability
- 🎨 **Customizable Interface**: Tailor the app to your preferences
- 🚀 **Regular Updates**: New features added frequently
---
## 📁 Project Structure

```sh
└── Vibeflow-Music/
    ├── main.py
    ├── font.ttf
    ├── frames
    │   ├── frame_functions
    │   │   ├── utils.py
    │   │   ├── playlists-functions.py
    │   ├── bottom_player.py 
    │   ├── lyrics_view.py
    │   ├── mini_player.py
    │   ├── music_player_frame.py
    │   ├── player_frame.py
    │   ├── search_frame.py
    │   └── settings_frame.py
    ├── icons
    │   ├── containing all the icons needed
    └── requirements.txt
```

---
## 🛠️ Technical Details

- **Framework**: PySide6
- **Language**: Python
- **Architecture**: Modern, modular design for easy maintenance and updates.

## 🔜 Upcoming Features

We're constantly working to improve VibeFlow Music. Here are some features in our pipeline:
- Enhanced visualization options
- Advanced equalizer settings
- Cross-platform sync capabilities
- And much more!

## 💡 Philosophy

VibeFlow Music is built on three core principles:
1. **Simplicity**: Focus on the music, not the interface
2. **Integration**: All essential features in one place
3. **User Experience**: Smooth, intuitive, and enjoyable to use

## 🤝 Contributing

We welcome contributions! Whether it's bug reports, feature suggestions, or code contributions, every input helps make VibeFlow Music better for everyone.

### How to Contribute
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

<p align="center">Made with ❤️ for music lovers by music lovers by VTxHive</p>