#!/usr/bin/env python3
import os
import subprocess

SOUNDS_DIR = "/home/tao/Projects/ReaperAI_Karaoke/sounds"

def main():
    if not os.path.exists(SOUNDS_DIR):
        print(f"Directory {SOUNDS_DIR} does not exist.")
        return
        
    for filename in os.listdir(SOUNDS_DIR):
        if filename.endswith(".mp3"):
            mp3_path = os.path.join(SOUNDS_DIR, filename)
            wav_filename = filename[:-4] + ".wav"
            wav_path = os.path.join(SOUNDS_DIR, wav_filename)
            
            print(f"Converting {filename} to {wav_filename}...")
            cmd = ["ffmpeg", "-y", "-i", mp3_path, wav_path]
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                print(f"Successfully converted {filename} to {wav_filename}")
                os.remove(mp3_path)
            except Exception as e:
                print(f"Failed to convert {filename}: {e}")

if __name__ == "__main__":
    main()
