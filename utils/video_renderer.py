import random
import time
import subprocess
from pathlib import Path
from utils.audio_handler import get_audio_duration
from utils.config import ASSETS, WIDTH, HEIGHT, FONT_SIZE

def render_video(audio_path, output_dir):
    video_dir = ASSETS / "input_videos"
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
        f"[1:v]chromakey=green:0.1:0.2[peter_keyed];"
        f"[2:v]chromakey=green:0.1:0.2[stewie_keyed];"
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
