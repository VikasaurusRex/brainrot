import subprocess
from pathlib import Path
from .subtitle_handler import create_srt_file, create_word_level_srt

def create_fallback_subtitles(audio_path, script, output_dir):
    print("\n" + "=" * 50)
    print("FALLBACK SUBTITLE CREATION")
    print("=" * 50)
    print("📝 Creating fallback subtitles from script...")
    try:
        cmd_duration = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)
        ]
        duration_result = subprocess.run(cmd_duration, capture_output=True, text=True)
        total_duration = float(duration_result.stdout.strip())
        segments = []
        word_segments = []
        current_time = 0
        for dialogue in script:
            text = dialogue["line"]
            estimated_duration = max(1.5, min(3.0, len(text) / 12))
            segments.append({
                "start": current_time,
                "end": current_time + estimated_duration,
                "text": text
            })
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
        subtitle_file = Path(output_dir) / "subtitles.srt"
        word_subtitle_file = Path(output_dir) / "word_subtitles.srt"
        create_srt_file(segments, subtitle_file)
        create_word_level_srt(segments, word_subtitle_file)
        print(f"✅ Fallback subtitle files created: {subtitle_file}, {word_subtitle_file}")
        return True
    except Exception as e:
        print(f"❌ Fallback subtitle creation failed: {e}")
        return False
