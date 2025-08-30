<p align="center">
  <img src="https://res.cloudinary.com/db2vusdvh/image/upload/v1733220951/VibeFlow_Music_o3mren.png"/>
</p>

# VibeFlow Music 🎵

Yeah, you got it right by the name its another music player. Built with python in PYSIDE6 and made it so that you can or I can just focus on working while listening to the songs I like without ads.

## ❔ Why did I built it?

So basically I cannot work without music blasting in background, and I was irritated with ads like we all are , so I searched but nothing came up that I would daily drive so built one with all the things I needed no ads, quick and easy search and some good GUI 

## 🚀 Installation

### Method 1: Quick Install (Windows)
1. Download the latest `Vibeflow-setup.exe` from the [releases page](https://github.com/qa-p1/Vibeflow/releases/tag/first)
2. Run the installer and follow the on-screen instructions
3. Launch VibeFlow Music and enjoy! 

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


---
## 😎 Features

### Core Functionality
-  **Modern GUI Experience**: Love Glassmorphism.
-  **Music Queue Management**: Order however you like, and also you can reorder in the playlist by dragging and dropping.
-  **Mini Player Mode**: We got 2 Versions **Mini** and **Micro**, so you can focus on work.
-  **SMTC For windows**: Works with WIN smtc API
-  **Multiple Player Modes**: Basic thing, just wanted to add more points.

### Music Management
-  **Lyrics Support**: You get a nice lyrics view thank ME.
-  **Multiple Playlist Options**: BOOM groundbreaking feature.
-  **Spotify Playlist Import**: Import your already made one here directly.
-  **Easy Search**: Find your favorite music instantly 😎

### Enhanced Experience
-  **Sleep Timer**: Good for SESSIONS
- ️**Easy Music Downloads**: Integrated downloading capability
-  **Suggestions**: It's a download and listen typa app but i thought its a cool thing to add, you might need you api key from groq.
-  **Regular Updates**: New features added frequently(maybe a lie)
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
    │   │   ├── shortcuts.py
    │   │   ├── smtc_handler.py
    │   │   ├── music_helper.py
    │   │   ├── shortcut_guide.py
    │   ├── lyrics_view.py
    │   ├── mini_player.py
    │   ├── music_player_frame.py
    │   ├── search_frame.py
    │   ├── home_screen_frame.py
    │   ├── picks_for_you.py
    │   └── settings_frame.py
    ├── icons
    │   ├── containing all the icons needed
    └── requirements.txt
```

---

## 😁 Upcoming Features

### Basically I want to add some things that are I guess are left 
- Most importantly I guess there's a feature or a whole thing I should work upon I directly adding songs to playlist without downloading them, I know I know what's the point of this APP then but main focus was just to build something for windows or ig mac's and linux further if this grows was simplicity a good old music player where you have your songs and enjoy them. If this works out , the preview feature and the picks for you player will also work then it will be a full fledged player but tbh I could not find a stable way to that currently when you click a song in picks for you section it searches with ddgs and gets a link to a mp3 (its not always the right song that's why all this is incomplete) . If I somehow I find a fast around that's not slow as yt_dlp one 6-7 sec and not as unstable as jio savaan workaround this project will be complete.

- **Settings Screen will be added soon**.

- Others things are just small things I will vibe code in future if I like that's all ig.
## 🤝 Contributing

Yeah find bugs , Improve the already existing features if you can but mostly if you are contributing pls contribute to the main problem that I have described in the section above(big ass para).

Thanks if you read all this shit I wrote.

---

<p align="center">Made with 😈 for music lovers by music lovers by qa-p1 (AI generated text)</p>
