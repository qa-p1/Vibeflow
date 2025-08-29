import requests
import base64
import json
import sys
import urllib3
from ddgs import DDGS
try:
    from pyDes import des, ECB, PAD_PKCS5
except ImportError:
    print("Error: 'py-des' library not found.", file=sys.stderr)
    print("Please install it using: pip install py-des", file=sys.stderr)
    sys.exit(1)

# Disable the annoying SSL warnings that show up because of verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Global headers to mimic a browser ---
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- API Endpoints ---
song_details_base_url = "https://www.jiosaavn.com/api.php?__call=song.getDetails&cc=in&_marker=0%3F_marker%3D0&_format=json&pids="
lyrics_base_url = "https://www.jiosaavn.com/api.php?__call=lyrics.getLyrics&ctx=web6dot0&api_version=4&_format=json&_marker=0%3F_marker%3D0&lyrics_id="


def search_for_jiosaavn_url(query):
    results = DDGS().text(f"site:jiosaavn.com/song {query} ", max_results=5)
    print(results)
    return results[0]['href']

def get_lyrics(id):
    """Fetches lyrics for a given song ID."""
    try:
        url = lyrics_base_url + id
        lyrics_json = requests.get(url, headers=headers).text
        return json.loads(lyrics_json)['lyrics']
    except Exception:
        return None


def decrypt_url(url):
    """Decrypts the media URL."""
    des_cipher = des(b"38346591", ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)
    enc_url = base64.b64decode(url.strip())
    dec_url = des_cipher.decrypt(enc_url, padmode=PAD_PKCS5).decode('utf-8')
    return dec_url.replace("_96.mp4", "_320.mp4")


def format_string(text):
    """Formats strings to be more readable."""
    return text.encode().decode().replace("&quot;", "'").replace("&amp;", "&").replace("&#039;", "'")


def format_song(data, lyrics):
    """Formats a single song's data."""
    try:
        data['media_url'] = decrypt_url(data['encrypted_media_url'])
        if data['320kbps'] != "true":
            data['media_url'] = data['media_url'].replace("_320.mp4", "_160.mp4")
    except (KeyError, TypeError):
        url = data.get('media_preview_url', '')
        url = url.replace("preview", "aac")
        if data.get('320kbps') == "true":
            url = url.replace("_96_p.mp4", "_320.mp4")
        else:
            url = url.replace("_96_p.mp4", "_160.mp4")
        data['media_url'] = url

    for key in ['song', 'music', 'singers', 'starring', 'album', 'primary_artists']:
        if key in data and isinstance(data[key], str):
            data[key] = format_string(data[key])

    data['image'] = data.get('image', '').replace("150x150", "500x500")

    if lyrics and data.get('has_lyrics') == 'true':
        data['lyrics'] = get_lyrics(data['id'])
    else:
        data['lyrics'] = None

    if 'copyright_text' in data:
        data['copyright_text'] = data['copyright_text'].replace("&copy;", "©")
    return data


def get_song(id, lyrics):
    """Gets a song's details by its ID."""
    try:
        url = song_details_base_url + id
        song_response = requests.get(url, headers=headers, verify=False).text.encode().decode('unicode-escape')
        song_response = json.loads(song_response)
        return format_song(song_response[id], lyrics)
    except Exception:
        return None


def get_song_id(url):
    """Extracts song ID from a JioSaavn URL."""
    try:
        res = requests.get(url, headers=headers, data=[('bitrate', '320')], verify=False)
        return res.text.split('"pid":"')[1].split('","')[0]
    except IndexError:
        print('Error: Could not find song ID. The link might be for an album or playlist.', file=sys.stderr)
        return None