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
import math # Ensure math is imported for PI, though FFmpeg might have its own PI

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

print("\n" + "=" * 50)
print("CONFIGURATION")
print("=" * 50)

# CONFIGURE YOUR TOPIC HERE
TOPIC = "why are there waves in the ocean?"  # Example topic, can be changed

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

Create 4-5 lines of pointed dialogue where:

- Stewie opens with attention grabbing remark tangential to the topic
- Peter responds with a witty comeback before pivoting smoothly into the topic
- Stewie interjects occasionally with incorrect observations or tangential remarks
- Peter responds with corrections and teaches Stewie correct information

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
    print("\n" + "=" * 50)
    print("SCRIPT GENERATION")
    print("=" * 50)
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
    print("\n" + "=" * 50)
    print("TTS MODEL SETUP")
    print("=" * 50)
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
    print("\n" + "=" * 50)
    print("AUDIO SYNTHESIS")
    print("=" * 50)
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
    print("\n" + "=" * 50)
    print("AUDIO COMBINATION")
    print("=" * 50)
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
    """Generate line-by-line and word-level subtitles with proper text escaping"""
    print("\n" + "=" * 50)
    print("SUBTITLE CREATION")
    print("=" * 50)
    print("📝 Creating subtitles...")
    
    try:
        model = whisper.load_model("base")
        result = model.transcribe(str(audio_path), word_timestamps=True)
        
        # Create both line-level and word-level subtitle files
        subtitle_file = output_dir / "subtitles.srt"
        word_subtitle_file = output_dir / "word_subtitles.srt"
        
        create_srt_file(result["segments"], subtitle_file)
        create_word_level_srt(result["segments"], word_subtitle_file)
        
        print(f"✅ Subtitle files created: {subtitle_file}, {word_subtitle_file}")
        return True
        
    except Exception as e:
        print(f"❌ Subtitle creation failed: {e}")
        return create_fallback_subtitles(audio_path, script, output_dir)

def create_srt_file(segments, output_path):
    """Create SRT subtitle file from Whisper segments, with max 5 words per line."""
    with open(output_path, 'w', encoding='utf-8') as f:
        subtitle_entry_index = 1
        for segment in segments:
            # Check if segment has word-level timestamps and the list is not empty
            if "words" in segment and segment["words"]:
                current_words_in_line = []
                for i, word_info in enumerate(segment["words"]):
                    # Ensure word_info is a dictionary and has 'word' key
                    if not isinstance(word_info, dict) or "word" not in word_info:
                        # Skip malformed word_info
                        continue
                    current_words_in_line.append(word_info)
                    
                    # If 5 words are collected, or it's the last word of the segment
                    if len(current_words_in_line) == 5 or i == len(segment["words"]) - 1:
                        if not current_words_in_line: # Should not happen if words list is not empty
                            continue

                        line_text = " ".join(w["word"].strip() for w in current_words_in_line if isinstance(w, dict) and "word" in w)
                        
                        # Ensure 'start' and 'end' keys exist
                        if not all(isinstance(w, dict) and "start" in w and "end" in w for w in current_words_in_line):
                            # Fallback to segment times if word times are incomplete, though this is unlikely
                            start_time = segment.get("start", 0)
                            end_time = segment.get("end", start_time + 1) # Default 1s duration
                        else:
                            start_time = current_words_in_line[0]["start"]
                            end_time = current_words_in_line[-1]["end"]

                        # Adjust duration: min 0.5s.
                        if end_time - start_time < 0.5:
                            end_time = start_time + 0.5
                        
                        start_srt = format_srt_time(start_time)
                        end_srt = format_srt_time(end_time)
                        
                        f.write(f"{subtitle_entry_index}\n")
                        f.write(f"{start_srt} --> {end_srt}\n")
                        f.write(f"{line_text}\n\n")
                        
                        subtitle_entry_index += 1
                        current_words_in_line = []
            else: # Fallback for segments without word-level timestamps
                original_text = segment.get("text", "").strip()
                words_in_original_text = original_text.split()
                num_original_words = len(words_in_original_text)

                if num_original_words == 0:
                    continue

                seg_start_time = segment.get("start", 0)
                seg_end_time = segment.get("end", seg_start_time + (0.2 * num_original_words)) # Estimate 0.2s per word if end is missing
                
                seg_duration = seg_end_time - seg_start_time
                if seg_duration <= 0: 
                    seg_duration = 0.2 * num_original_words # Estimate if duration is invalid
                    if seg_duration <=0: seg_duration = 0.5 # Absolute minimum

                for i in range(0, num_original_words, 5):
                    chunk_words = words_in_original_text[i : i + 5]
                    if not chunk_words:
                        continue
                    
                    line_text = " ".join(chunk_words)
                    num_chunk_words = len(chunk_words)

                    # Proportional timing for fallback
                    chunk_start_ratio = (i / num_original_words) if num_original_words > 0 else 0
                    chunk_end_ratio = ((i + num_chunk_words) / num_original_words) if num_original_words > 0 else 1
                    
                    start_time = seg_start_time + (chunk_start_ratio * seg_duration)
                    end_time = seg_start_time + (chunk_end_ratio * seg_duration)

                    current_chunk_duration = end_time - start_time
                    if current_chunk_duration < 0.5:
                        end_time = start_time + 0.5
                    elif current_chunk_duration > 3.0: # Cap for fallback lines (5 words max 3s)
                         end_time = start_time + 3.0
                    
                    if end_time <= start_time: # Ensure duration is positive
                        end_time = start_time + 0.5

                    start_srt = format_srt_time(start_time)
                    end_srt = format_srt_time(end_time)
                    
                    f.write(f"{subtitle_entry_index}\n")
                    f.write(f"{start_srt} --> {end_srt}\n")
                    f.write(f"{line_text}\n\n")
                    subtitle_entry_index += 1

def create_word_level_srt(segments, output_path):
    """Create word-level SRT for highlighting individual words"""
    with open(output_path, 'w', encoding='utf-8') as f:
        subtitle_index = 1
        
        for segment in segments:
            if "words" in segment:
                for word_info in segment["words"]:
                    word = word_info["word"].strip()
                    start_time = word_info["start"]
                    end_time = word_info["end"]
                    
                    # Ensure minimum duration
                    if end_time - start_time < 0.3:
                        end_time = start_time + 0.3
                    
                    start_srt = format_srt_time(start_time)
                    end_srt = format_srt_time(end_time)
                    
                    f.write(f"{subtitle_index}\n")
                    f.write(f"{start_srt} --> {end_srt}\n")
                    f.write(f"{word}\n\n")
                    subtitle_index += 1

def format_srt_time(seconds):
    """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def create_fallback_subtitles(audio_path, script, output_dir):
    """Fallback subtitle creation using script dialogue"""
    print("\n" + "=" * 50)
    print("FALLBACK SUBTITLE CREATION")
    print("=" * 50)
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
        word_segments = []
        current_time = 0
        
        for dialogue in script:
            text = dialogue["line"]  # Changed from "text" to "line"
            # Estimate duration based on text length (roughly 3 chars per second)
            estimated_duration = max(1.5, min(3.0, len(text) / 12))
            
            segments.append({
                "start": current_time,
                "end": current_time + estimated_duration,
                "text": text
            })
            
            # Create word-level segments for fallback
            words = text.split()
            word_duration = estimated_duration / len(words) if words else 1.0
            word_time = current_time
            
            for word in words:
                word_segments.append({
                    "start": word_time,
                    "end": word_time + word_duration,
                    "word": word
                })
                word_time += word_duration
            
            current_time += estimated_duration
        
        # Create both SRT files
        subtitle_file = output_dir / "subtitles.srt"
        word_subtitle_file = output_dir / "word_subtitles.srt"
        
        create_srt_file(segments, subtitle_file)
        create_word_srt_from_fallback(word_segments, word_subtitle_file)
        
        print(f"✅ Fallback subtitle files created: {subtitle_file}, {word_subtitle_file}")
        return True
        
    except Exception as e:
        print(f"❌ Fallback subtitle creation failed: {e}")
        return False

def create_word_srt_from_fallback(word_segments, output_path):
    """Create word-level SRT from fallback data"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, word_info in enumerate(word_segments):
            start_srt = format_srt_time(word_info["start"])
            end_srt = format_srt_time(word_info["end"])
            
            f.write(f"{i + 1}\n")
            f.write(f"{start_srt} --> {end_srt}\n")
            f.write(f"{word_info['word']}\n\n")

def get_audio_duration(audio_path):
    """Get audio duration in seconds"""
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"❌ Failed to get audio duration: {e}")
        return None

def render_video_pipeline(audio_path, output_dir):
    """Single-pass video rendering pipeline using pre-rendered character videos"""
    print("\n" + "=" * 50)
    print("VIDEO RENDERING PIPELINE")
    print("=" * 50)
    print("🎬 Starting single-pass video rendering...")
    
    video_dir = ASSETS / "input_videos"
    bg_videos = [f for f in video_dir.glob("*.mp4")]
    if not bg_videos:
        print("❌ No background videos found")
        return False
    
    # Check for character videos
    char_video_dir = ASSETS / "character_videos" / "positioned"
    peter_video = char_video_dir / "peter_positioned.mp4"
    stewie_video = char_video_dir / "stewie_positioned.mp4"
    
    if not peter_video.exists() or not stewie_video.exists():
        print("❌ Character videos not found. Run create_character_videos.py first!")
        print(f"  Peter: {peter_video}")
        print(f"  Stewie: {stewie_video}")
        return False
    
    bg_video_path = random.choice(bg_videos)
    print(f"📺 Selected background: {bg_video_path.name}")
    print(f"🎭 Using character videos:")
    print(f"  Peter: {peter_video.name}")
    print(f"  Stewie: {stewie_video.name}")
    
    audio_duration = get_audio_duration(audio_path)
    if not audio_duration:
        return False
    
    print(f"⏱️ Audio duration: {audio_duration:.2f} seconds")
    encoder_settings = get_encoder_settings()
    
    total_estimate = (audio_duration * 0.5) + 10 # Much faster with pre-rendered videos
    print(f"🕐 Total estimated rendering time: ~{total_estimate:.0f} seconds ({total_estimate/60:.1f} minutes)")
    if 'videotoolbox' in encoder_settings.get('video_codec',''):
        print("💡 Using Apple Silicon hardware acceleration for faster rendering")
    else:
        print("💡 Using software encoding")
    print("-" * 50)

    final_video_output = output_dir / "final_video.mp4"

    # Prepare paths for subtitle files
    main_srt_abs_path = (output_dir / "subtitles.srt").resolve().as_posix()
    word_srt_abs_path = (output_dir / "word_subtitles.srt").resolve().as_posix()

    def escape_ffmpeg_filter_path(path_str):
        return path_str.replace("'", "\\\\'")

    main_srt_escaped = escape_ffmpeg_filter_path(main_srt_abs_path)
    word_srt_escaped = escape_ffmpeg_filter_path(word_srt_abs_path)

    # Much simpler filter chain using pre-rendered character videos with chroma key
    filter_complex_parts = [
        # Process background video
        f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT}[bg_processed];",
        
        # Remove green screen from character videos using chroma key
        f"[1:v]chromakey=green:0.1:0.2[peter_keyed];",
        f"[2:v]chromakey=green:0.1:0.2[stewie_keyed];",
        
        # Overlay characters (they're already positioned and animated)
        f"[bg_processed][peter_keyed]overlay=shortest=1[with_peter];",
        f"[with_peter][stewie_keyed]overlay=shortest=1[with_chars];",
        
        # Add subtitles
        f"[with_chars]subtitles=filename='{main_srt_escaped}':force_style='Fontname=Arial,Fontsize={FONT_SIZE},PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=3,Alignment=2,MarginV=400,Bold=1'[with_main_subs];",
        f"[with_main_subs]subtitles=filename='{word_srt_escaped}':force_style='Fontname=Arial,Fontsize={FONT_SIZE},PrimaryColour=&H00ff00,OutlineColour=&H000000,Outline=3,Alignment=2,MarginV=400,Bold=1'[final_v]"
    ]
    filter_complex = "".join(filter_complex_parts)

    # Use higher quality settings for final output
    if encoder_settings['video_codec'] == 'h264_videotoolbox':
        final_quality_settings = ['-b:v', '12M']
    else:
        final_quality_settings = ['-crf', '16', '-preset', 'slow']

    cmd = [
        'ffmpeg', '-y',
        *encoder_settings['hwaccel'],
        '-i', str(bg_video_path),      # Input 0: background video
        '-i', str(peter_video),        # Input 1: Peter character video
        '-i', str(stewie_video),       # Input 2: Stewie character video
        '-i', str(audio_path),         # Input 3: master audio
        '-filter_complex', filter_complex,
        '-map', '[final_v]',           # Map final filtered video stream
        '-map', '3:a',                 # Map audio from input 3 (master_audio)
        '-c:v', encoder_settings['video_codec'],
        *final_quality_settings,
        '-c:a', 'aac',                 # Encode audio to AAC
        '-b:a', '192k',                # High quality audio bitrate
        '-t', str(audio_duration),     # Set total duration
        '-pix_fmt', 'yuv420p',         # Standard pixel format for compatibility
        str(final_video_output)
    ]

    try:
        start_render_time = time.time()
        print(f"🎬 Running FFmpeg with pre-rendered character videos...")
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        render_duration = time.time() - start_render_time
        print(f"✅ Final video created: {final_video_output}")
        print(f"⏱️ Actual rendering time: {render_duration:.1f} seconds ({render_duration/60:.1f} minutes)")
        print("-" * 50)
        
        print(f"\n🎉 Video rendering pipeline complete!")
        print(f"🎬 Final video: {final_video_output}")
        print(f"📊 Video quality: High ({final_quality_settings}, 192kbps audio)")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Video rendering failed. Command: {' '.join(e.cmd)}")
        print(f"❌ FFmpeg stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Video rendering encountered an unexpected error: {e}")
        print(f"Attempted FFmpeg command: {' '.join(cmd)}")
        return False

# Legacy function name for compatibility
def render_video(audio_path, output_dir):
    """Render final video using the new multi-stage pipeline"""
    return render_video_pipeline(audio_path, output_dir)

def check_requirements():
    """Check if all required assets and tools are available"""
    print("\n" + "=" * 50)
    print("REQUIREMENTS CHECK")
    print("=" * 50)
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

def check_hardware_acceleration():
    """Check if VideoToolbox hardware acceleration is available"""
    try:
        cmd = ['ffmpeg', '-hide_banner', '-encoders']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return 'h264_videotoolbox' in result.stdout
    except:
        return False

def get_encoder_settings():
    """Get optimal encoder settings based on hardware availability"""
    if check_hardware_acceleration():
        print("🚀 Apple Silicon VideoToolbox acceleration detected")
        return {
            'hwaccel': ['-hwaccel', 'videotoolbox'],
            'video_codec': 'h264_videotoolbox',
            'quality_settings': ['-b:v', '8M']  # Bitrate mode for hardware encoder
        }
    else:
        print("🔧 Using software encoding (libx264)")
        return {
            'hwaccel': [],
            'video_codec': 'libx264',
            'quality_settings': ['-crf', '18', '-preset', 'slow']  # High quality software encoding
        }

# =====================================
# MAIN FUNCTION
# =====================================

def main():
    """Main execution function"""
    print("=" * 50)
    print("BRAINROT VIDEO GENERATOR")
    print("=" * 50)
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
    
    # # Load existing script from previous run
    # script_file = output_dir / "script.json"
    # if script_file.exists():
    #     with open(script_file, 'r') as f:
    #         script_data = json.load(f)
    #         script = script_data["script"]
    #     print("✅ Loaded existing script")
    # else:
    #     print("❌ No existing script found") # This case might not be hit due to prior generation
    #     return False

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
    print("=" * 50)
    return True

if __name__ == "__main__":
    main()
