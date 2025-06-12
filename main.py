#!/usr/bin/env python3
"""
Brainrot Educational Video Generator Module
Creates educational videos with Peter Griffin teaching Stewie Griffin.

Configure the TOPIC variable below and run: python brainrot.py
"""

import random
import json
import time
from pathlib import Path
import ssl

# Import modular pipeline components
from config import TOPIC, ASSETS, OUTPUT, CHARACTERS, OLLAMA_URL, MODEL, PROMPT, WIDTH, HEIGHT, FONT_SIZE
from utils.llm_handler import generate_script
from utils.tts_handler import setup_tts_model, synthesize_audio
from utils.audio_handler import combine_audio, get_audio_duration
from utils.subtitle_handler import create_simple_subtitles
from utils.fallback_subtitles import create_fallback_subtitles
from utils.video_renderer import render_video, get_encoder_settings
from utils.requirements_checker import check_requirements

# SSL bypass for model downloads (Whisper, etc.)
ssl._create_default_https_context = ssl._create_unverified_context

# =====================================
# MAIN FUNCTION
# =====================================

def main():
    print("=" * 50)
    print("BRAINROT VIDEO GENERATOR")
    print("=" * 50)
    print(f"🎯 Topic: {TOPIC}")

    # Check requirements
    if not check_requirements():
        print("❌ Requirements not met")
        return False

    # Create output directory
    timestamp = str(int(time.time()))
    output_dir = OUTPUT / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output: {output_dir}")

    # Generate script
    script = generate_script(TOPIC)
    if not script:
        return False

    # Save script
    with open(output_dir / "script.json", 'w') as f:
        json.dump({"script": script}, f, indent=2)

    # Setup TTS
    tts_model = setup_tts_model()
    if not tts_model:
        return False

    # Generate audio
    temp_audio_dir = output_dir / "temp_audio"
    audio_files = synthesize_audio(script, tts_model, temp_audio_dir)
    if not audio_files:
        return False

    # Combine audio
    master_audio = output_dir / "master_audio.wav"
    if not combine_audio(audio_files, master_audio):
        return False

    # Load script from file
    script_file = output_dir / "script.json"
    if not script_file.exists():
        print(f"❌ Script file not found: {script_file}")
        return False
    with open(script_file, 'r', encoding='utf-8') as f:
        script_data = json.load(f)
        script = script_data["script"]

    # Create subtitles
    subtitle_result = create_simple_subtitles(master_audio, script, output_dir)
    if not subtitle_result:
        print("❌ Failed to create subtitles")
        return False

    # Render final video
    if not render_video(master_audio, output_dir):
        return False

    print(f"\n🎉 Video generation complete!")
    print(f"📂 Output folder: {output_dir}")
    print(f"🎬 Final video: {output_dir}/final_video.mp4")
    print("=" * 50)
    return True

if __name__ == "__main__":
    main()
