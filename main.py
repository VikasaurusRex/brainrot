#!/usr/bin/env python3
"""
Brainrot Educational Video Generator Module
Creates educational videos with Peter Griffin teaching Stewie Griffin.

Configure the TOPICS_LIST variable in the main() function below and run: python main.py
"""

import json
import time
import ssl
import re # Added for sanitizing topic names

# Import modular pipeline components
# Removed TOPIC from this import
from config import ASSETS, OUTPUT, CHARACTERS, OLLAMA_URL, MODEL, PROMPT, WIDTH, HEIGHT, FONT_SIZE
from utils.llm_handler import generate_script, generate_title_and_description # Added generate_title_and_description
from utils.tts_handler import setup_tts_model, synthesize_audio
from utils.audio_handler import combine_audio
from utils.subtitle_handler import create_simple_subtitles
from utils.video_renderer import render_video
from utils.requirements_checker import check_requirements

# SSL bypass for model downloads (Whisper, etc.)
ssl._create_default_https_context = ssl._create_unverified_context

# =====================================
# MAIN FUNCTION
# =====================================

def main():
    print("=" * 50)
    print("BRAINROT VIDEO GENERATOR - MULTI-TOPIC")
    print("=" * 50)

    # Define your list of topics here
    TOPICS_LIST = [
        "Lions: Coordinated group hunting strategies",
        "Dolphins: Advanced social communication and behavior",
        "Bees: Intricate waggle dance for navigation",
        "Elephants: Remarkable memory and empathetic behavior",
        "Cheetahs: Explosive sprinting ability and hunting tactics",
        "Octopuses: Unique problem-solving and camouflage techniques",
        "Airfoil Engineering: Detailed analysis of wing design and lift generation",
        "Propulsion Systems: In-depth breakdown of jet engines and turbofan mechanics",
        "Flight Dynamics: Exploring stability, control, and maneuverability in flight",
        "Aircraft Structures: Materials, stress analysis, and design efficiency",
        "Avionics Systems: Modern navigation, communication, and automation technologies"
    ]

    # Check requirements (once at the beginning)
    if not check_requirements():
        print("❌ Overall requirements not met. Aborting.")
        return False

    # Create a base output directory for this run
    timestamp = time.strftime("%y_%m_%d_%H_%M")
    run_base_output_dir = OUTPUT / timestamp
    run_base_output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📂 Base output directory for this run: {run_base_output_dir}")

    overall_success = True

    for idx, current_topic in enumerate(TOPICS_LIST):
        print("\\n" + "=" * 50)
        print(f"Processing Topic {idx + 1}/{len(TOPICS_LIST)}: {current_topic}")
        print("=" * 50)

        # Sanitize topic for directory name
        # Remove special characters, replace spaces with underscores, and convert to lowercase
        sanitized_topic_name = re.sub(r'[^\w\s-]', '', current_topic).strip()
        sanitized_topic_name = re.sub(r'[-\s]+', '_', sanitized_topic_name).lower()
        if not sanitized_topic_name: # Fallback if topic name becomes empty
            sanitized_topic_name = f"topic_{idx+1}"

        # Add DD_HH_MM timestamp to topic directory for chronological organization
        topic_timestamp = time.strftime("%d_%H_%M")
        topic_dir_name = f"{topic_timestamp}_{sanitized_topic_name}"
        topic_output_dir = run_base_output_dir / topic_dir_name
        topic_output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🎯 Current Topic: {current_topic}")
        print(f"📁 Output for this topic: {topic_output_dir}")

        # Generate script
        script = generate_script(current_topic) # Pass current_topic
        if not script:
            print(f"❌ Failed to generate script for topic: {current_topic}")
            overall_success = False
            continue # Move to next topic

        # Save script
        script_file_path = topic_output_dir / "script.json"
        with open(script_file_path, 'w') as f:
            json.dump({"script": script}, f, indent=2)
        print(f"📄 Script saved: {script_file_path}")

        # Generate title and description
        if not generate_title_and_description(current_topic, topic_output_dir):
            print(f"⚠️ Failed to generate or save title/description for topic: {current_topic}")
            # Continue with video generation even if title/description fails, as it's not critical path
            # overall_success = False # Optionally mark as failure if this is critical

        # Setup TTS
        tts_model = setup_tts_model()
        if not tts_model:
            print(f"❌ Failed to setup TTS for topic: {current_topic}")
            overall_success = False
            continue

        # Generate audio
        temp_audio_dir = topic_output_dir / "temp_audio"
        # temp_audio_dir.mkdir(parents=True, exist_ok=True) # synthesize_audio should handle this
        audio_files = synthesize_audio(script, tts_model, temp_audio_dir)
        if not audio_files:
            print(f"❌ Failed to synthesize audio for topic: {current_topic}")
            overall_success = False
            continue

        # Combine audio
        master_audio_path = topic_output_dir / "master_audio.wav"
        if not combine_audio(audio_files, master_audio_path):
            print(f"❌ Failed to combine audio for topic: {current_topic}")
            overall_success = False
            continue
        print(f"🔊 Master audio created: {master_audio_path}")

        # Create subtitles
        # The original code re-reads the script from file here. We can use the 'script' variable directly.
        # However, to minimize deviation if other parts rely on this, we can keep the reload or ensure 'script' is the same.
        # For this refactor, using the in-memory 'script' variable is more efficient.
        subtitle_result = create_simple_subtitles(master_audio_path, script, topic_output_dir)
        if not subtitle_result:
            print(f"❌ Failed to create subtitles for topic: {current_topic}")
            overall_success = False
            continue
        print(f"📜 Subtitles created in: {topic_output_dir}")

        # Render final video
        if not render_video(master_audio_path, topic_output_dir):
            print(f"❌ Failed to render video for topic: {current_topic}")
            overall_success = False
            continue

        print(f"\\n🎉 Video generation complete for topic: {current_topic}!")
        print(f"📂 Output folder: {topic_output_dir}")
        print(f"🎬 Final video: {topic_output_dir}/final_video.mp4")

    print("\\n" + "=" * 50)
    if overall_success:
        print("✅ All topics processed successfully.")
    else:
        print("⚠️ Some topics failed to process. Check logs above for details.")
    print(f"📂 Base output directory for this run: {run_base_output_dir}")
    print("=" * 50)
    return overall_success

if __name__ == "__main__":
    main()
