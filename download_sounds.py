#!/usr/bin/env python3
import os
import urllib.request

SOUNDS_DIR = "/home/tao/Projects/ReaperAI_Karaoke/sounds"

SOUND_URLS = {
    "laughter.mp3": "https://cdn.jsdelivr.net/gh/jitsi/jitsi-meet@master/sounds/reactions-laughter.mp3",
    "applause.mp3": "https://cdn.jsdelivr.net/gh/jitsi/jitsi-meet@master/sounds/reactions-applause.mp3",
    "surprise.mp3": "https://cdn.jsdelivr.net/gh/jitsi/jitsi-meet@master/sounds/reactions-surprise.mp3",
    "boo.mp3": "https://cdn.jsdelivr.net/gh/jitsi/jitsi-meet@master/sounds/reactions-boo.mp3",
    "thumbs_up.mp3": "https://cdn.jsdelivr.net/gh/jitsi/jitsi-meet@master/sounds/reactions-thumbs-up.mp3",
    "airhorn.mp3": "https://cdn.jsdelivr.net/gh/GoogleChromeLabs/airhorn@main/app/sounds/airhorn.mp3",
    "crickets.mp3": "https://cdn.jsdelivr.net/gh/jitsi/jitsi-meet@master/sounds/reactions-crickets.mp3",
    "love.mp3": "https://cdn.jsdelivr.net/gh/jitsi/jitsi-meet@master/sounds/reactions-love.mp3",
    "message.mp3": "https://cdn.jsdelivr.net/gh/jitsi/jitsi-meet@master/sounds/incomingMessage.mp3"
}

def main():
    if not os.path.exists(SOUNDS_DIR):
        os.makedirs(SOUNDS_DIR)
        print(f"Created directory: {SOUNDS_DIR}")
        
    for filename, url in SOUND_URLS.items():
        filepath = os.path.join(SOUNDS_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Downloading {filename}...")
            try:
                urllib.request.urlretrieve(url, filepath)
                print(f"Successfully downloaded {filename}")
            except Exception as e:
                print(f"Error downloading {filename}: {e}")
        else:
            print(f"{filename} already exists, skipping.")

if __name__ == "__main__":
    main()
