#!/usr/bin/env python3
"""
Brainrot Educational Video Generator Module
Creates educational videos with Peter Griffin teaching Stewie Griffin.

Configure the TOPIC variable below and run: python brainrot.py
"""

import json
import ssl

# Import modular pipeline components
from config import OUTPUT
from utils.subtitle_handler import create_simple_subtitles
from utils.video_renderer import render_video

# SSL bypass for model downloads (Whisper, etc.)
ssl._create_default_https_context = ssl._create_unverified_context

# =====================================
# MAIN FUNCTION
# =====================================

def main():

    # Create output directory
    timestamp = "25_06_13_03_19"  # time.strftime("%y_%m_%d_%H_%M")
    
    output_dir = OUTPUT / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output: {output_dir}")

    # Load script from file
    script_file = output_dir / "script.json"
    if not script_file.exists():
        print(f"❌ Script file not found: {script_file}")
        return False
    with open(script_file, 'r', encoding='utf-8') as f:
        script_data = json.load(f)
        script = script_data["script"]

    master_audio = output_dir / "master_audio.wav"

    # Create subtitles
    subtitle_result = create_simple_subtitles(master_audio, script, output_dir)
    if not subtitle_result:
        print("❌ Failed to create subtitles")
        return False

    # Render final video
    if not render_video(master_audio, output_dir):
        return False

    print(f"🎬 Final video: {output_dir}/final_video.mp4")
    print("=" * 50)
    return True

if __name__ == "__main__":
    main()
