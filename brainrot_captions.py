#!/usr/bin/env python3
"""
Brainrot Educational Video Generator Module
Creates educational videos with Peter Griffin teaching Stewie Griffin.

Configure the TOPIC variable below and run: python brainrot_simplified.py
"""

import os
import random
import json
import time
import subprocess
import ssl
from pathlib import Path

# Required imports
import ssl
import requests
import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS
import whisper

# SSL bypass for model downloads (Whisper, etc.)
ssl._create_default_https_context = ssl._create_unverified_context

# Disable SSL verification for Whisper model downloads
ssl._create_default_https_context = ssl._create_unverified_context

# =====================================
# CONFIGURATION
# =====================================

# CONFIGURE YOUR TOPIC HERE
TOPIC = "How volcanos work"

# Paths
ASSETS = Path("assets")
OUTPUT = Path("output")
CHARACTERS = {
    "Peter": {"voice": ASSETS / "voices/peter_griffin.wav", "image": ASSETS / "images/Peter.png"},
    "Stewie": {"voice": ASSETS / "voices/stewie_griffin.wav", "image": ASSETS / "images/Stewie.png"}
}

# LLM Settings
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "deepseek-r1:32b"
PROMPT = """You are a scriptwriter for educational videos with Peter Griffin teaching Stewie Griffin.

Create 2-3 lines of dialogue where:
- Peter enthusiastically explains the topic (sometimes incorrectly)
- Stewie responds with wit, corrections, or clever observations
- Alternate between characters, starting with Peter

Format as JSON: {"script": [{"actor": "Peter", "line": "text"}, ...]}
No other text, just the JSON."""

# Video Settings
WIDTH, HEIGHT = 1080, 1920
FONT_SIZE = 18  # Reasonable size for 1920px height video

# =====================================
# CORE FUNCTIONS
# =====================================

def generate_script(topic):
    """Generate dialogue script using Ollama"""
    print(f"🧠 Generating script for: {topic}")
    
    payload = {
        "model": MODEL,
        "prompt": f"Create an educational script about: {topic}",
        "system": PROMPT,
        "format": "json",
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        if "response" in result:
            script_data = json.loads(result["response"])
            if "script" in script_data:
                print("✅ Script generated")
                return script_data["script"]
        
        print("❌ Invalid script format")
        return None
        
    except Exception as e:
        print(f"❌ Script generation failed: {e}")
        return None

def setup_tts_model():
    """Initialize ChatterboxTTS with CPU compatibility"""
    print("🔊 Loading TTS model...")
    
    # Monkey patch for CPU compatibility (from working tts_test.py)
    original_torch_load = torch.load
    def patched_torch_load(*args, **kwargs):
        kwargs['map_location'] = torch.device('cpu')
        return original_torch_load(*args, **kwargs)
    
    torch.load = patched_torch_load
    
    try:
        model = ChatterboxTTS.from_pretrained(device="cpu")
        torch.load = original_torch_load  # Restore original
        print("✅ TTS model loaded")
        return model
    except Exception as e:
        torch.load = original_torch_load  # Restore on error
        print(f"❌ TTS model failed: {e}")
        return None

def synthesize_audio(script, model, output_dir):
    """Generate audio for each line using ChatterboxTTS"""
    print("🎤 Synthesizing audio...")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    audio_files = []
    for idx, line in enumerate(script):
        actor = line["actor"]
        text = line["line"]
        voice_path = CHARACTERS[actor]["voice"]
        output_file = output_dir / f"{idx}_{actor.lower()}.wav"
        
        print(f"  {actor}: {text[:50]}...")
        
        try:
            if not voice_path.exists():
                print(f"❌ Voice sample missing: {voice_path}")
                return None
                
            wav = model.generate(
                text, 
                audio_prompt_path=str(voice_path),
                exaggeration=1,
                cfg_weight=0.7
            )
            ta.save(str(output_file), wav, model.sr)
            audio_files.append(str(output_file))
            print(f"    ✅ Saved: {output_file.name}")
            
        except Exception as e:
            print(f"❌ Audio synthesis failed for {actor}: {e}")
            return None
    
    return audio_files

def combine_audio(audio_files, output_path):
    """Combine audio files using FFmpeg"""
    print("🎶 Combining audio...")
    
    # Create concat file
    concat_file = output_path.parent / "concat_list.txt"
    with open(concat_file, 'w') as f:
        for audio_file in audio_files:
            f.write(f"file '{Path(audio_file).resolve()}'\n")
    
    try:
        cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', 
            '-i', str(concat_file), '-c', 'copy', str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        concat_file.unlink()  # Clean up
        print(f"✅ Master audio: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Audio combination failed: {e}")
        return False

def create_simple_subtitles(audio_path, script, output_dir):
    """Generate simple line-by-line subtitles with proper text escaping"""
    print("📝 Creating simple subtitles...")
    
    try:
        model = whisper.load_model("base")
        result = model.transcribe(str(audio_path), word_timestamps=True)
        
        # Create subtitle file approach (more reliable than complex filter)
        subtitle_file = output_dir / "subtitles.srt"
        create_srt_file(result["segments"], subtitle_file)
        
        print(f"✅ Subtitle file created: {subtitle_file}")
        return True
        
    except Exception as e:
        print(f"❌ Subtitle creation failed: {e}")
        return create_fallback_subtitles(audio_path, script, output_dir)

def create_srt_file(segments, output_path):
    """Create SRT subtitle file from Whisper segments"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments):
            start_time = segment["start"]
            end_time = segment["end"]
            
            # Ensure proper timing (1-2 seconds per line)
            duration = end_time - start_time
            if duration < 1.0:
                end_time = start_time + 1.5
            elif duration > 2.5:
                end_time = start_time + 2.0
            
            # Format timestamps for SRT
            start_srt = format_srt_time(start_time)
            end_srt = format_srt_time(end_time)
            
            # Clean text
            text = segment["text"].strip()
            
            f.write(f"{i + 1}\n")
            f.write(f"{start_srt} --> {end_srt}\n")
            f.write(f"{text}\n\n")

def format_srt_time(seconds):
    """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def create_fallback_subtitles(audio_path, script, output_dir):
    """Fallback subtitle creation using script dialogue"""
    print("📝 Creating fallback subtitles from script...")
    
    try:
        # Get audio duration
        cmd_duration = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)
        ]
        duration_result = subprocess.run(cmd_duration, capture_output=True, text=True)
        total_duration = float(duration_result.stdout.strip())
        
        # Create subtitle segments from script
        segments = []
        current_time = 0
        
        for dialogue in script:
            text = dialogue["text"]
            # Estimate duration based on text length (roughly 3 chars per second)
            estimated_duration = max(1.5, min(3.0, len(text) / 12))
            
            segments.append({
                "start": current_time,
                "end": current_time + estimated_duration,
                "text": text
            })
            current_time += estimated_duration
        
        # Create SRT file
        subtitle_file = output_dir / "subtitles.srt"
        create_srt_file(segments, subtitle_file)
        
        print(f"✅ Fallback subtitle file created: {subtitle_file}")
        return True
        
    except Exception as e:
        print(f"❌ Fallback subtitle creation failed: {e}")
        return False

def render_video(audio_path, output_dir):
    """Render final video with background, audio, and direct subtitle rendering"""
    print("🎬 Rendering video...")
    
    # Select random background video
    video_dir = ASSETS / "input_videos"
    bg_videos = [f for f in video_dir.glob("*.mp4")]
    if not bg_videos:
        print("❌ No background videos found")
        return False
    
    bg_video = random.choice(bg_videos)
    final_video = output_dir / "final_video.mp4"
    
    try:
        # Get audio duration to match video length
        cmd_duration = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)
        ]
        duration_result = subprocess.run(cmd_duration, capture_output=True, text=True)
        audio_duration = float(duration_result.stdout.strip())
        
        # Use direct subtitle rendering instead of overlay to avoid black background
        cmd = [
            'ffmpeg', '-y',
            '-i', str(bg_video),           # Input 0: Background video
            '-i', str(audio_path),         # Input 1: Audio track
            '-filter_complex',
            f'[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT}[bg];'
            f'[bg]subtitles={output_dir}/subtitles.srt:force_style=\'Fontname=Luckiest Guy,Fontsize={FONT_SIZE},PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=3,Alignment=2,MarginV=200\'[vout]',
            '-map', '[vout]',              # Video output
            '-map', '1:a',                 # Audio from second input
            '-c:v', 'libx264', '-c:a', 'aac',
            '-preset', 'fast',             # Faster encoding
            '-t', str(audio_duration),     # Match audio duration
            str(final_video)
        ]
        
        print(f"🎬 Running FFmpeg command...")
        result_process = subprocess.run(cmd, capture_output=True, text=True)
        if result_process.returncode != 0:
            print(f"❌ Video rendering failed: {result_process.stderr}")
            return False
        
        print(f"✅ Final video rendered: {final_video}")
        return True
        
    except Exception as e:
        print(f"❌ Video rendering failed: {e}")
        return False

def check_requirements():
    """Check if all required assets and tools are available"""
    print("🔍 Checking requirements...")
    
    # Check FFmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg available")
    except:
        print("❌ FFmpeg not found")
        return False
    
    # Check Ollama
    try:
        response = requests.get(OLLAMA_URL.replace('/api/generate', '/api/tags'), timeout=5)
        if response.status_code == 200:
            print("✅ Ollama running")
        else:
            print("❌ Ollama not responding correctly")
            return False
    except:
        print("❌ Ollama not accessible")
        return False
    
    # Check voice samples
    for char, data in CHARACTERS.items():
        if not data["voice"].exists():
            print(f"❌ Missing voice sample: {data['voice']}")
            return False
        else:
            print(f"✅ {char} voice sample found")
    
    # Check background videos
    if not any((ASSETS / "input_videos").glob("*.mp4")):
        print("❌ No background videos found")
        return False
    else:
        print("✅ Background videos found")
    
    return True

# =====================================
# MAIN FUNCTION
# =====================================

def main():
    """Main execution function"""
    print(f"🎯 Topic: {TOPIC}")
    
    # Check requirements
    if not check_requirements():
        print("❌ Requirements not met")
        return False
    
    # Create output directory
    timestamp = "1749713561" # str(int(time.time()))
    output_dir = OUTPUT / timestamp
    # output_dir.mkdir(parents=True, exist_ok=True)
    # print(f"📁 Output: {output_dir}")
    
    # # Generate script
    # script = generate_script(TOPIC)
    # if not script:
    #     return False
    
    # # Save script
    # with open(output_dir / "script.json", 'w') as f:
    #     json.dump({"script": script}, f, indent=2)
    
    # # Setup TTS
    # tts_model = setup_tts_model()
    # if not tts_model:
    #     return False
    
    # # Generate audio
    # temp_audio_dir = output_dir / "temp_audio"
    # audio_files = synthesize_audio(script, tts_model, temp_audio_dir)
    # if not audio_files:
    #     return False
    
    # # Combine audio
    master_audio = output_dir / "master_audio.wav"
    # if not combine_audio(audio_files, master_audio):
    #     return False
    
    # # Create subtitles 
    # subtitle_result = create_simple_subtitles(master_audio, script, output_dir)
    # if not subtitle_result:
    #     print("❌ Failed to create subtitles")
    #     return False
    
    # Render final video (now includes direct subtitle rendering)
    if not render_video(master_audio, output_dir):
        return False
    
    print(f"\n🎉 Video generation complete!")
    print(f"📂 Output folder: {output_dir}")
    print(f"🎬 Final video: {output_dir}/final_video.mp4")
    return True

if __name__ == "__main__":
    main()
