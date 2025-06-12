import subprocess
from pathlib import Path

def combine_audio(audio_files, output_path):
    """Combine audio files using FFmpeg"""
    output_path = Path(output_path)
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
        concat_file.unlink()
        return True
    except Exception as e:
        print(f"❌ Audio combination failed: {e}")
        return False

def get_audio_duration(audio_path):
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
