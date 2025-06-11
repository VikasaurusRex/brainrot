#!/usr/bin/env python3
"""
Brainrot Educational Video Generator
Self-contained script for generating educational videos with Peter Griffin teaching Stewie Griffin.

Features:
- Educational dialogue generation using Ollama LLM
- Voice cloning with ChatterboxTTS 
- Automatic video rendering with subtitles
- Peter teaching Stewie format with comic relief

Usage:
    python brainrot.py "Your educational topic here"

Example:
    python brainrot.py "How photosynthesis works in plants"
"""

import os
import sys
import random
import json
import time
import subprocess
import tempfile
import argparse
import shutil
from datetime import datetime # Added for timestamp formatting
from pathlib import Path

# Try importing required libraries
try:
    import requests
    import torch
    import torchaudio as ta
    from chatterbox.tts import ChatterboxTTS
    import whisper
except ImportError as e:
    print(f"❌ Missing required library: {e}")
    print("\n📦 Please install dependencies first:")
    print("pip install requests torch torchaudio chatterbox-tts openai-whisper")
    print("\n⚠️  Note: FFmpeg must also be installed on your system")
    sys.exit(1)

# =====================================
# CONFIGURATION
# =====================================

# File Paths
ASSET_PATH = "assets/"
INPUT_VIDEO_PATH = f"{ASSET_PATH}input_videos/"
VOICE_PATH = f"{ASSET_PATH}voices/"
IMAGE_PATH = f"{ASSET_PATH}images/"
FONT_PATH = f"{ASSET_PATH}fonts/"
FONT_FILE = f"{FONT_PATH}LuckiestGuy-Regular.ttf"
OUTPUT_PATH = "output/"

# LLM & Script Generation
OLLAMA_API_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "deepseek-r1:32b"
LLM_SYSTEM_PROMPT = """
You are an expert scriptwriter for viral short-form educational videos featuring Peter Griffin teaching Stewie Griffin.

CHARACTER DYNAMICS:
- Peter is the enthusiastic but often misguided teacher who explains concepts in simple, funny ways
- Stewie is the brilliant but bewildered student who makes witty jokes and points out Peter's misunderstandings
- Each exchange should build logically on the previous one, creating a flowing educational conversation

FORMAT REQUIREMENTS:
- 8-12 lines of dialogue total for 65-80 seconds of content
- Alternate between Peter and Stewie, starting with Peter introducing the topic
- Peter should explain the educational concept with enthusiasm and occasional inaccuracies
- Stewie should respond with comic relief, corrections, or clever observations about the lesson
- Each line should build context from the previous exchanges
- Include both educational content and character-appropriate humor

You MUST format your response as a valid JSON object with a single key "script" containing an array of objects.
Each object must have "actor" (either "Peter" or "Stewie") and "line" (the character's dialogue).
Do not include any other text, preambles, or explanations as your response is used as direct JSON input.
"""

# Character & Asset Mapping
CHARACTERS = {
    "Peter": {
        "voice_sample": f"{VOICE_PATH}peter_griffin.wav",
        "image": f"{IMAGE_PATH}Peter.png",
    },
    "Stewie": {
        "voice_sample": f"{VOICE_PATH}stewie_griffin.wav",
        "image": f"{IMAGE_PATH}Stewie.png",
    }
}

# Video Rendering Settings
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
BACKGROUND_VIDEO_VOLUME = 0.7

# Subtitle Settings
SUBTITLE_FONT_SIZE = 120
SUBTITLE_FONT_COLOR = "white"
SUBTITLE_HIGHLIGHT_COLOR = "#24ff03"
SUBTITLE_OUTLINE_COLOR = "black"
SUBTITLE_POSITION_Y = 1600

# =====================================
# UTILITY FUNCTIONS
# =====================================

def check_dependencies():
    """Check if all required dependencies and assets are available"""
    print("🔍 Checking dependencies and assets...")
    
    # Check FFmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found. Please install FFmpeg first.")
        return False
    
    # Check Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
        else:
            print("❌ Ollama is not responding properly")
            return False
    except requests.RequestException:
        print("❌ Ollama is not running. Please start Ollama first.")
        return False
    
    # Check voice samples
    for character, data in CHARACTERS.items():
        if not os.path.exists(data['voice_sample']):
            print(f"❌ Voice sample missing: {data['voice_sample']}")
            return False
        else:
            print(f"✅ {character} voice sample found")
    
    # Check background videos
    if not os.path.exists(INPUT_VIDEO_PATH):
        print(f"❌ Input video directory missing: {INPUT_VIDEO_PATH}")
        return False
    
    video_files = [f for f in os.listdir(INPUT_VIDEO_PATH) if f.endswith('.mp4')]
    if not video_files:
        print("❌ No background videos found")
        return False
    else:
        print(f"✅ Found {len(video_files)} background videos")
    
    return True

# =====================================
# LLM HANDLER
# =====================================

def generate_script(topic: str):
    """Generate an educational script with Peter teaching Stewie"""
    try:
        payload = {
            "model": LLM_MODEL,
            "prompt": f"Educational Topic: {topic}",
            "system": LLM_SYSTEM_PROMPT,
            "stream": False,
            "format": "json"
        }
        
        print(f"🤖 Requesting educational script from Ollama for topic: {topic}")
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            script_text = result.get('response', '')
            
            try:
                script_data = json.loads(script_text)
                if 'script' in script_data and isinstance(script_data['script'], list):
                    print(f"✅ Generated educational script with {len(script_data['script'])} lines")
                    return script_data['script']
                else:
                    print("❌ Invalid script format from LLM")
                    return None
            except json.JSONDecodeError:
                print("❌ Failed to parse LLM response as JSON")
                return None
        else:
            print(f"❌ LLM request failed: {response.status_code}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Request error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

# =====================================
# TTS HANDLER
# =====================================

# Global model instance to avoid reloading
_tts_model = None

def get_tts_model():
    """Get or initialize the TTS model with CPU compatibility"""
    global _tts_model
    if _tts_model is None:
        print("🎤 Loading ChatterboxTTS model...")
        try:
            # Monkey patch torch.load to force CPU loading for ChatterboxTTS
            original_torch_load = torch.load
            
            def patched_torch_load(*args, **kwargs):
                """Force CPU loading for all torch.load calls"""
                kwargs['map_location'] = torch.device('cpu')
                return original_torch_load(*args, **kwargs)
            
            # Apply the patch
            torch.load = patched_torch_load
            
            # Force CPU device for compatibility with ChatterboxTTS
            device = "cpu"
            print(f"Using device: {device} (ChatterboxTTS requires CPU for model loading)")
            
            # Load the TTS model
            _tts_model = ChatterboxTTS.from_pretrained(device=device)
            
            # Restore original torch.load
            torch.load = original_torch_load
            
            print("✅ ChatterboxTTS model loaded successfully!")
        except Exception as e:
            print(f"❌ Error loading ChatterboxTTS model: {e}")
            # Restore original torch.load in case of error
            try:
                torch.load = original_torch_load
            except:
                pass
            return None
    return _tts_model

def synthesize_dialogue(script, output_dir):
    """Synthesize dialogue using ChatterboxTTS voice cloning"""
    dialogue_with_audio = []
    
    # Get the TTS model
    model = get_tts_model()
    if not model:
        print("❌ ChatterboxTTS model not available, falling back to basic TTS")
        return synthesize_dialogue_fallback(script, output_dir)
    
    for idx, line in enumerate(script):
        actor = line['actor']
        text = line['line']
        
        # Get the voice sample for this character
        if actor in CHARACTERS:
            voice_sample_path = CHARACTERS[actor]['voice_sample']
            
            # Create output filename
            output_file = os.path.join(output_dir, f"{idx}_{actor.lower()}.wav")
            
            if os.path.exists(voice_sample_path):
                try:
                    print(f"🎵 Generating voice-cloned audio for {actor}: {text[:50]}...")
                    
                    # Generate voice-cloned audio using ChatterboxTTS
                    wav = model.generate(text, audio_prompt_path=voice_sample_path, exaggeration=1, cfg_weight=0.7)
                    
                    # Save the voice-cloned audio
                    ta.save(output_file, wav, model.sr)
                    
                    print(f"✅ Voice-cloned audio generated for {actor}")
                    
                    # Add audio path to the line data
                    line_with_audio = line.copy()
                    line_with_audio['audio_path'] = output_file
                    dialogue_with_audio.append(line_with_audio)
                    
                except Exception as e:
                    print(f"❌ Error generating voice-cloned audio for {actor}: {e}")
                    continue
            else:
                print(f"❌ Voice sample not found for {actor}: {voice_sample_path}")
                continue
        else:
            print(f"❌ Unknown character: {actor}")
    
    return dialogue_with_audio

def synthesize_dialogue_fallback(script, output_dir):
    """Fallback TTS without voice cloning (macOS only)"""
    dialogue_with_audio = []
    
    print("🔄 Using fallback TTS (system voices)")
    
    for idx, line in enumerate(script):
        actor = line['actor']
        text = line['line']
        
        # Create output filename
        output_file = os.path.join(output_dir, f"{idx}_{actor.lower()}.wav")
        
        try:
            print(f"🎵 Generating basic TTS for {actor}: {text[:50]}...")
            
            # Use different voices for different characters (macOS)
            voice = "Alex" if actor == "Peter" else "Fred"
            
            with tempfile.NamedTemporaryFile(suffix='.aiff', delete=False) as tmp_file:
                tts_path = tmp_file.name
            
            # Generate TTS
            cmd = ['say', '-v', voice, '-o', tts_path, text]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Convert to WAV
                convert_cmd = ['ffmpeg', '-i', tts_path, '-y', output_file]
                subprocess.run(convert_cmd, capture_output=True)
                os.remove(tts_path)
                
                print(f"✅ Basic TTS generated for {actor}")
                
                # Add audio path to the line data
                line_with_audio = line.copy()
                line_with_audio['audio_path'] = output_file
                dialogue_with_audio.append(line_with_audio)
            else:
                print(f"❌ TTS generation failed for {actor}")
                
        except Exception as e:
            print(f"❌ Error generating TTS for {actor}: {e}")
            continue
    
    return dialogue_with_audio

def combine_audio_clips(dialogue_with_audio, master_audio_path):
    """Combine all audio clips into a single master audio file"""
    if not dialogue_with_audio:
        print("❌ No audio clips to combine")
        return False
    
    # Create a list file for ffmpeg concat
    concat_list_path = os.path.join(os.path.dirname(master_audio_path), "concat_list.txt")
    
    with open(concat_list_path, 'w') as f:
        for line in dialogue_with_audio:
            if 'audio_path' in line and os.path.exists(line['audio_path']):
                f.write(f"file '{os.path.abspath(line['audio_path'])}'\n")
    
    # Use ffmpeg to concatenate
    try:
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', concat_list_path,
            '-c', 'copy',
            master_audio_path,
            '-y'  # Overwrite output file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Master audio created: {master_audio_path}")
            return True
        else:
            print(f"❌ FFmpeg error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ FFmpeg not found. Please install FFmpeg.")
        return False
    except Exception as e:
        print(f"❌ Error combining audio: {e}")
        return False

# =====================================
# WHISPER HANDLER
# =====================================

def get_word_timestamps(audio_path):
    """Get word-level timestamps using Whisper"""
    try:
        print("🗣️  Loading Whisper model...")
        model = whisper.load_model("base")
        
        print(f"📝 Transcribing audio: {audio_path}")
        result = model.transcribe(audio_path, word_timestamps=True)
        
        # Extract word-level timestamps
        timed_words = []
        
        for segment in result.get('segments', []):
            for word_info in segment.get('words', []):
                timed_words.append({
                    'word': word_info['word'].strip(),
                    'start': word_info['start'],
                    'end': word_info['end']
                })
        
        print(f"✅ Generated timestamps for {len(timed_words)} words")
        return {
            'words': timed_words,
            'full_text': result['text'],
            'duration': result.get('segments', [{}])[-1].get('end', 0) if result.get('segments') else 0
        }
        
    except Exception as e:
        print(f"❌ Error generating timestamps: {e}")
        return None

# =====================================
# VIDEO RENDERER
# =====================================

def create_subtitle_file(timed_script, script_data, subtitle_path):
    """Create an SRT subtitle file from timed script data"""
    try:
        with open(subtitle_path, 'w', encoding='utf-8') as f:
            if timed_script and 'words' in timed_script:
                # Use word-level timestamps for precise subtitles
                words = timed_script['words']
                
                # Group words by dialogue lines
                current_line = 0
                current_text = ""
                current_start = 0
                word_count_in_line = 0
                words_per_line = len(words) // len(script_data) if script_data else 1
                
                for i, word in enumerate(words):
                    if word_count_in_line == 0:
                        current_start = word['start']
                    
                    current_text += word['word']
                    word_count_in_line += 1
                    
                    # End of line or last word
                    if word_count_in_line >= words_per_line or i == len(words) - 1:
                        end_time = word['end']
                        
                        # Format timestamps
                        start_srt = format_timestamp_srt(current_start)
                        end_srt = format_timestamp_srt(end_time)
                        
                        # Write subtitle entry
                        f.write(f"{current_line + 1}\n")
                        f.write(f"{start_srt} --> {end_srt}\n")
                        f.write(f"{current_text.strip()}\n\n")
                        
                        current_line += 1
                        current_text = ""
                        word_count_in_line = 0
            else:
                # Fallback: use script data without timestamps
                duration_per_line = 3.0  # 3 seconds per line
                for i, line in enumerate(script_data):
                    start_time = i * duration_per_line
                    end_time = (i + 1) * duration_per_line
                    
                    start_srt = format_timestamp_srt(start_time)
                    end_srt = format_timestamp_srt(end_time)
                    
                    f.write(f"{i + 1}\n")
                    f.write(f"{start_srt} --> {end_srt}\n")
                    f.write(f"{line['line']}\n\n")
        
        print(f"✅ Subtitle file created: {subtitle_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating subtitle file: {e}")
        return False

def format_timestamp_srt(seconds):
    """Convert seconds to SRT timestamp format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def create_final_video(script_data, timed_script, master_audio_path, background_video_path, final_video_path):
    """Create the final video with background, audio, and subtitles"""
    try:
        # Create subtitle file
        subtitle_path = os.path.join(os.path.dirname(final_video_path), "subtitles.srt")
        if not create_subtitle_file(timed_script, script_data, subtitle_path):
            print("⚠️  Using fallback subtitle creation")
        
        print("🎬 Rendering final video with FFmpeg...")
        
        # FFmpeg command to combine background video, audio, and subtitles
        cmd = [
            'ffmpeg',
            '-i', background_video_path,  # Input background video
            '-i', master_audio_path,      # Input audio
            '-vf', f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},subtitles={subtitle_path}:force_style='FontName=Arial,FontSize={SUBTITLE_FONT_SIZE},PrimaryColour=&H00ffffff,OutlineColour=&H00000000,BackColour=&H80000000,Bold=1,Outline=2'",
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-shortest',  # End when shortest input ends
            '-y',  # Overwrite output
            final_video_path
        ]
        
        print(f"🔄 Running FFmpeg command...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Final video created successfully: {final_video_path}")
            return True
        else:
            print(f"❌ FFmpeg error: {result.stderr}")
            # Try simplified version without subtitles
            print("🔄 Trying simplified version without subtitle overlay...")
            simple_cmd = [
                'ffmpeg',
                '-i', background_video_path,
                '-i', master_audio_path,
                '-vf', f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,crop={VIDEO_WIDTH}:{VIDEO_HEIGHT}",
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-shortest',
                '-y',
                final_video_path
            ]
            
            simple_result = subprocess.run(simple_cmd, capture_output=True, text=True)
            if simple_result.returncode == 0:
                print(f"✅ Simplified video created successfully: {final_video_path}")
                return True
            else:
                print(f"❌ Simplified FFmpeg also failed: {simple_result.stderr}")
                return False
            
    except FileNotFoundError:
        print("❌ FFmpeg not found. Please install FFmpeg.")
        return False
    except Exception as e:
        print(f"❌ Error in video creation: {e}")
        return False

# =====================================
# MAIN FUNCTION
# =====================================

def main(topic: str):
    """Main function to generate an educational video from a topic."""
    print("🎓 === Starting Educational Video Generation ===")
    print(f"📚 Topic: {topic}")
    print("🎭 Format: Peter teaching Stewie with comic relief")
    
    # Check dependencies first
    if not check_dependencies():
        print("❌ Dependency check failed. Please fix the issues above.")
        return False
    
    # 1. Create a unique timestamped directory for this run
    run_timestamp = str(int(time.time()))
    run_output_path = os.path.join(OUTPUT_PATH, run_timestamp)
    temp_audio_path = os.path.join(run_output_path, "temp_audio")
    os.makedirs(temp_audio_path, exist_ok=True)
    print(f"📁 Created output directory: {run_output_path}")

    # 2. Generate Script using LLM with improved educational format
    print("\n1️⃣ Generating educational script...")
    script_data = generate_script(topic)
    if not script_data:
        print("❌ Failed to generate script")
        return False
    
    # Save script
    script_path = os.path.join(run_output_path, "script.json")
    with open(script_path, 'w') as f:
        json.dump(script_data, f, indent=2)
    print(f"💾 Script saved to: {script_path}")
    
    # Display generated script
    print("\n📝 Generated Educational Script:")
    for i, line in enumerate(script_data):
        print(f"  {i+1:2d}. {line['actor']:6s}: {line['line']}")

    # 3. Synthesize Audio using integrated working TTS
    print("\n2️⃣ Synthesizing audio with voice cloning...")
    dialogue_with_audio = synthesize_dialogue(script_data, temp_audio_path)
    if not dialogue_with_audio:
        print("❌ Failed to synthesize audio")
        return False

    # 4. Concatenate all audio clips
    print("\n3️⃣ Combining audio clips...")
    master_audio_path = os.path.join(run_output_path, "master_audio.wav")
    if not combine_audio_clips(dialogue_with_audio, master_audio_path):
        print("❌ Failed to combine audio clips")
        return False

    # 5. Get Word-Level Timestamps using Whisper
    print("\n4️⃣ Generating word-level timestamps...")
    timed_script = get_word_timestamps(master_audio_path)
    if timed_script:
        timestamps_path = os.path.join(run_output_path, "timestamps.json")
        with open(timestamps_path, 'w') as f:
            json.dump(timed_script, f, indent=2)
        print(f"💾 Timestamps saved to: {timestamps_path}")

    # 6. Use minecraft_parkour_1 as specified or fallback
    print("\n5️⃣ Selecting background video...")
    background_video = "minecraft_parkour_1.mp4"
    background_video_path = os.path.join(INPUT_VIDEO_PATH, background_video)
    
    if not os.path.exists(background_video_path):
        print(f"⚠️  Background video not found: {background_video_path}")
        # Fallback to any available video
        available_videos = [f for f in os.listdir(INPUT_VIDEO_PATH) if f.endswith('.mp4')]
        if available_videos:
            background_video = random.choice(available_videos)
            background_video_path = os.path.join(INPUT_VIDEO_PATH, background_video)
            print(f"🔄 Using fallback video: {background_video}")
        else:
            print("❌ No background videos found")
            return False
    else:
        print(f"✅ Using background: {background_video}")
    
    # 7. Render the Final Video
    print("\n6️⃣ Rendering the final educational video...")
    final_video_path = os.path.join(run_output_path, "final_video.mp4")
    
    if create_final_video(script_data, timed_script, master_audio_path, background_video_path, final_video_path):
        print(f"\n🎉 ✅ EDUCATIONAL VIDEO GENERATION COMPLETE! ✅ 🎉")
        print(f"🎬 Final video: {final_video_path}")
        print(f"📁 Output folder: {run_output_path}")
        print(f"🎓 Peter taught Stewie about: {topic}")
        return True
    else:
        print("❌ Video rendering failed")
        return False

# =====================================
# COMMAND LINE INTERFACE
# =====================================

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    # Install numpy first to avoid conflicts
    print("Installing numpy...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'numpy>=1.24.0,<2.0.0'])
        print("✅ numpy installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install numpy")
        return False

    # Install required packages
    packages = [
        'requests',
        'torch',
        'torchaudio',
        'git+https://github.com/openai/whisper.git'
    ]

    for package in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False

    # Install chatterbox-tts dependencies manually with compatible versions
    print("\nInstalling chatterbox-tts dependencies...")
    chatterbox_deps = [
        'conformer==0.3.2',
        'diffusers==0.29.0', 
        'librosa==0.10.0',
        'omegaconf==2.3.0',
        'resampy==0.4.3',
        'resemble-perth==1.0.1',
        's3tokenizer'
    ]

    for dep in chatterbox_deps:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
            print(f"✅ {dep} installed successfully")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {dep}")

    # Try installing chatterbox-tts with --no-deps to avoid version conflicts
    print("\nInstalling chatterbox-tts (bypassing version conflicts)...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'chatterbox-tts', '--no-deps'])
        print("✅ chatterbox-tts installed successfully (no-deps)")
        print("Note: Using existing torch/transformers versions (may have compatibility warnings)")
    except subprocess.CalledProcessError:
        print("❌ Failed to install chatterbox-tts")
        print("Will use fallback TTS without voice cloning")

    print("\n✅ Dependency installation complete!")
    print("⚠️  Note: FFmpeg must be installed separately on your system.")
    print("   macOS: brew install ffmpeg")
    print("   Ubuntu: sudo apt install ffmpeg")
    print("   Windows: Download from https://ffmpeg.org/download.html")
    
    return True

def list_example_topics():
    """List example educational topics"""
    topics = [
        "How photosynthesis works in plants",
        "The solar system and planetary orbits", 
        "How the human digestive system processes food",
        "The process of how volcanoes form and erupt",
        "Why the sky appears blue during the day",
        "How batteries store and release electrical energy",
        "The water cycle and how rain is formed",
        "How sound waves travel through different materials",
        "The basic principles of gravity and mass",
        "How the internet works and data transmission",
        "The process of photosynthesis in leaves",
        "How earthquakes happen and tectonic plate movement",
        "The human circulatory system and blood flow",
        "How computers process binary code",
        "The formation of clouds and weather patterns"
    ]
    
    print("📚 Example Educational Topics:")
    print("=" * 50)
    for i, topic in enumerate(topics, 1):
        print(f"{i:2d}. {topic}")
    print("=" * 50)
    print("💡 Use any of these or create your own educational topic!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate educational brainrot videos with Peter Griffin teaching Stewie Griffin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python brainrot.py "How photosynthesis works in plants"
  python brainrot.py "The water cycle and how rain is formed"
  python brainrot.py --install-deps
  python brainrot.py --list-topics
        """
    )
    
    parser.add_argument('topic', nargs='?', help='Educational topic to generate video about')
    parser.add_argument('--install-deps', action='store_true', help='Install required dependencies')
    parser.add_argument('--list-topics', action='store_true', help='List example educational topics')
    parser.add_argument('--model', default=LLM_MODEL, help=f'Ollama model to use (default: {LLM_MODEL})')
    
    args = parser.parse_args()
    
    if args.install_deps:
        install_dependencies()
        sys.exit(0)
    
    if args.list_topics:
        list_example_topics()
        sys.exit(0)
    
    if not args.topic:
        print("❌ Please provide an educational topic!")
        print("\n💡 Examples:")
        print("  python brainrot.py \"How photosynthesis works in plants\"")
        print("  python brainrot.py \"The water cycle and how rain is formed\"")
        print("\n📚 Use --list-topics to see more examples")
        print("📦 Use --install-deps to install dependencies")
        sys.exit(1)
    
    # Update model if specified
    if args.model != LLM_MODEL:
        globals()['LLM_MODEL'] = args.model
        print(f"🤖 Using model: {args.model}")
    
    print("🎬 Brainrot Educational Video Generator")
    print("=" * 50)
    
    # Run the main function
    success = main(args.topic)
    
    if success:
        print("\n🎉 Educational video generation completed successfully!")
        print("📚 Peter has successfully taught Stewie with comic relief!")
        print("🎥 Check the output folder for your educational brainrot content!")
    else:
        print("\n❌ Video generation failed. Check the errors above.")
        sys.exit(1)
