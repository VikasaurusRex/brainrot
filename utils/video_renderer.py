import random
import time
import subprocess
from pathlib import Path
from utils.audio_handler import get_audio_duration
from config import ASSETS, WIDTH, HEIGHT, FONT_SIZE

def parse_character_subtitles(subtitle_path):
    """Parse character subtitle file to get timing info for each character"""
    character_timings = []
    
    with open(subtitle_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        if lines[i].strip() and lines[i].strip().isdigit():  # subtitle number
            try:
                time_line = lines[i + 1].strip()
                character_line = lines[i + 2].strip()
                
                # Parse time format: HH:MM:SS,mmm --> HH:MM:SS,mmm
                start_str, end_str = time_line.split(' --> ')
                start_time = parse_srt_time(start_str)
                end_time = parse_srt_time(end_str)
                
                character_timings.append({
                    'start': start_time,
                    'end': end_time,
                    'character': character_line
                })
                
                i += 4  # Skip to next subtitle entry
            except (IndexError, ValueError):
                i += 1
        else:
            i += 1
    
    return character_timings

def parse_srt_time(time_str):
    """Convert SRT time format to seconds"""
    # Format: HH:MM:SS,mmm
    time_part, ms_part = time_str.split(',')
    h, m, s = map(int, time_part.split(':'))
    ms = int(ms_part)
    
    return h * 3600 + m * 60 + s + ms / 1000.0

def create_character_filter_complex(character_timings, width, height, ass_highlight_escaped):
    """Create FFmpeg filter complex that shows only the active speaker"""
    
    # Base processing with much less aggressive chroma key
    filter_parts = [
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}[bg_processed]",
        f"[1:v]chromakey=green:0.05:0.02[peter_keyed]",
        f"[2:v]chromakey=green:0.05:0.02[stewie_keyed]"
    ]
    
    # Start with background
    current_input = "[bg_processed]"
    
    # Group consecutive segments by character to minimize overlays
    peter_segments = []
    stewie_segments = []
    
    for timing in character_timings:
        character = timing['character']
        start_time = timing['start']
        end_time = timing['end']
        
        if character.lower() == 'peter':
            peter_segments.append(f"between(t,{start_time},{end_time})")
        elif character.lower() == 'stewie':
            stewie_segments.append(f"between(t,{start_time},{end_time})")
    
    # Create enable expressions for each character
    if peter_segments:
        peter_enable = "+".join(peter_segments)
        filter_parts.append(f"[bg_processed][peter_keyed]overlay=enable='{peter_enable}'[with_peter]")
        current_input = "[with_peter]"
    else:
        current_input = "[bg_processed]"
    
    if stewie_segments:
        stewie_enable = "+".join(stewie_segments)
        filter_parts.append(f"{current_input}[stewie_keyed]overlay=enable='{stewie_enable}'[with_stewie]")
        current_input = "[with_stewie]"
    
    # Add subtitles to final output
    filter_parts.append(f"{current_input}subtitles='{ass_highlight_escaped}'[final_v]")
    
    return ";".join(filter_parts)

def render_video(audio_path, output_dir):
    video_dir = ASSETS / "background_videos"
    bg_videos = [f for f in video_dir.glob("*.mp4")]
    if not bg_videos:
        print("❌ No background videos found")
        return False
    char_video_dir = ASSETS / "character_videos" / "positioned"
    peter_video = char_video_dir / "peter_positioned.mp4"
    stewie_video = char_video_dir / "stewie_positioned.mp4"
    if not peter_video.exists() or not stewie_video.exists():
        print("❌ Character videos not found. Run create_character_videos.py first!")
        return False
    
    # Check for character subtitles file
    character_subtitle_path = Path(output_dir) / "character_subtitles.srt"
    if not character_subtitle_path.exists():
        print("❌ Character subtitles file not found. Using fallback rendering.")
        return render_video_fallback(audio_path, output_dir)
    
    print("✅ Character subtitles found. Using character-based rendering.")
    
    bg_video_path = random.choice(bg_videos)
    audio_duration = get_audio_duration(audio_path)
    if not audio_duration:
        return False
    
    encoder_settings = get_encoder_settings()
    final_video_output = Path(output_dir) / "final_video.mp4"
    ass_highlight_abs_path = (Path(output_dir) / "subtitles_highlight.ass").resolve().as_posix()
    
    def escape_ffmpeg_filter_path(path_str):
        return path_str.replace("'", "\\'")
    
    ass_highlight_escaped = escape_ffmpeg_filter_path(ass_highlight_abs_path)
    
    # Parse character timings
    character_timings = parse_character_subtitles(character_subtitle_path)
    print(f"📊 Found {len(character_timings)} character segments")
    
    # Create dynamic filter complex
    filter_complex = create_character_filter_complex(character_timings, WIDTH, HEIGHT, ass_highlight_escaped)
    print(f"🔧 Filter complex: {filter_complex[:200]}...")  # Show first 200 chars
    
    if encoder_settings['video_codec'] == 'h264_videotoolbox':
        final_quality_settings = ['-b:v', '12M']
    else:
        final_quality_settings = ['-crf', '16', '-preset', 'slow']
    
    cmd = [
        'ffmpeg', '-y',
        *encoder_settings['hwaccel'],
        '-i', str(bg_video_path),
        '-i', str(peter_video),
        '-i', str(stewie_video),
        '-i', str(audio_path),
        '-filter_complex', filter_complex,
        '-map', '[final_v]',
        '-map', '3:a',
        '-c:v', encoder_settings['video_codec'],
        *final_quality_settings,
        '-c:a', 'aac',
        '-b:a', '192k',
        '-t', str(audio_duration),
        '-pix_fmt', 'yuv420p',
        str(final_video_output)
    ]
    
    try:
        start_render_time = time.time()
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        render_duration = time.time() - start_render_time
        print(f"✅ Final video created: {final_video_output}")
        print(f"⏱️ Actual rendering time: {render_duration:.1f} seconds ({render_duration/60:.1f} minutes)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Video rendering failed. Command: {' '.join(e.cmd)}")
        print(f"❌ FFmpeg stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Video rendering encountered an unexpected error: {e}")
        print(f"Attempted FFmpeg command: {' '.join(cmd)}")
        return False

def render_video_fallback(audio_path, output_dir):
    """Fallback rendering function that shows both characters (original behavior)"""
    video_dir = ASSETS / "background_videos"
    bg_videos = [f for f in video_dir.glob("*.mp4")]
    if not bg_videos:
        print("❌ No background videos found")
        return False
    char_video_dir = ASSETS / "character_videos" / "positioned"
    peter_video = char_video_dir / "peter_positioned.mp4"
    stewie_video = char_video_dir / "stewie_positioned.mp4"
    if not peter_video.exists() or not stewie_video.exists():
        print("❌ Character videos not found. Run create_character_videos.py first!")
        return False
    bg_video_path = random.choice(bg_videos)
    audio_duration = get_audio_duration(audio_path)
    if not audio_duration:
        return False
    encoder_settings = get_encoder_settings()
    final_video_output = Path(output_dir) / "final_video.mp4"
    ass_highlight_abs_path = (Path(output_dir) / "subtitles_highlight.ass").resolve().as_posix()
    def escape_ffmpeg_filter_path(path_str):
        return path_str.replace("'", "\\'")
    ass_highlight_escaped = escape_ffmpeg_filter_path(ass_highlight_abs_path)
    filter_complex = (
        f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT}[bg_processed];"
        f"[1:v]chromakey=green:0.05:0.02[peter_keyed];"
        f"[2:v]chromakey=green:0.05:0.02[stewie_keyed];"
        f"[bg_processed][peter_keyed]overlay=shortest=1[with_peter];"
        f"[with_peter][stewie_keyed]overlay=shortest=1[with_chars];"
        f"[with_chars]subtitles='{ass_highlight_escaped}'[final_v]"
    )
    if encoder_settings['video_codec'] == 'h264_videotoolbox':
        final_quality_settings = ['-b:v', '12M']
    else:
        final_quality_settings = ['-crf', '16', '-preset', 'slow']
    cmd = [
        'ffmpeg', '-y',
        *encoder_settings['hwaccel'],
        '-i', str(bg_video_path),
        '-i', str(peter_video),
        '-i', str(stewie_video),
        '-i', str(audio_path),
        '-filter_complex', filter_complex,
        '-map', '[final_v]',
        '-map', '3:a',
        '-c:v', encoder_settings['video_codec'],
        *final_quality_settings,
        '-c:a', 'aac',
        '-b:a', '192k',
        '-t', str(audio_duration),
        '-pix_fmt', 'yuv420p',
        str(final_video_output)
    ]
    try:
        start_render_time = time.time()
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        render_duration = time.time() - start_render_time
        print(f"✅ Final video created: {final_video_output}")
        print(f"⏱️ Actual rendering time: {render_duration:.1f} seconds ({render_duration/60:.1f} minutes)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Video rendering failed. Command: {' '.join(e.cmd)}")
        print(f"❌ FFmpeg stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Video rendering encountered an unexpected error: {e}")
        print(f"Attempted FFmpeg command: {' '.join(cmd)}")
        return False

def get_encoder_settings():
    # This function should be imported or moved from your main config
    # Placeholder for now
    return {
        'hwaccel': ['-hwaccel', 'videotoolbox'],
        'video_codec': 'h264_videotoolbox',
    }
