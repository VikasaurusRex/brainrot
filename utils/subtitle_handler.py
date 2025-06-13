import whisper
from pathlib import Path
from utils.ass_highlight import generate_ass_highlight
from utils.audio_handler import get_audio_duration
from config import WORDS_PER_LINE

def create_simple_subtitles(audio_path, script, output_dir):
    """Generate line-by-line and word-level subtitles with proper text escaping, and ASS highlight subtitles"""
    # Use audio segment timing for accurate character attribution
    temp_audio_dir = Path(output_dir) / "temp_audio"
    if temp_audio_dir.exists():
        segments = create_segments_from_audio_files(temp_audio_dir, script)
        character_subtitle_file = Path(output_dir) / "character_subtitles.srt"
        create_character_srt_from_segments(segments, character_subtitle_file)
        
        # Still use Whisper for word-level timing for subtitles
        model = whisper.load_model("base")
        result = model.transcribe(str(audio_path), word_timestamps=True)
        subtitle_file = Path(output_dir) / "subtitles.srt"
        word_subtitle_file = Path(output_dir) / "word_subtitles.srt"
        ass_highlight_file = Path(output_dir) / "subtitles_highlight.ass"
        create_srt_file(result["segments"], subtitle_file)
        create_word_level_srt(result["segments"], word_subtitle_file)
        create_ass_highlight_subtitles(result["segments"], ass_highlight_file)
    else:
        # Fallback to original method if temp audio files not found
        model = whisper.load_model("base")
        result = model.transcribe(str(audio_path), word_timestamps=True)
        subtitle_file = Path(output_dir) / "subtitles.srt"
        word_subtitle_file = Path(output_dir) / "word_subtitles.srt"
        character_subtitle_file = Path(output_dir) / "character_subtitles.srt"
        ass_highlight_file = Path(output_dir) / "subtitles_highlight.ass"
        create_srt_file(result["segments"], subtitle_file)
        create_word_level_srt(result["segments"], word_subtitle_file)
        create_character_srt_file(result["segments"], script, character_subtitle_file)
        create_ass_highlight_subtitles(result["segments"], ass_highlight_file)
    return True

def create_segments_from_audio_files(temp_audio_dir, script):
    """Create timing segments based on actual audio file durations"""
    segments = []
    current_time = 0.0
    
    # Get all audio files sorted by index
    audio_files = sorted(temp_audio_dir.glob("*.wav"), key=lambda x: int(x.stem.split('_')[0]))
    
    for i, audio_file in enumerate(audio_files):
        if i < len(script):
            duration = get_audio_duration(audio_file)
            if duration:
                segments.append({
                    'start': current_time,
                    'end': current_time + duration,
                    'character': script[i]['actor'],
                    'text': script[i]['line']
                })
                current_time += duration
            else:
                print(f"⚠️ Could not get duration for {audio_file}, using fallback")
                # Fallback duration based on text length
                fallback_duration = max(2.0, len(script[i]['line']) * 0.1)
                segments.append({
                    'start': current_time,
                    'end': current_time + fallback_duration,
                    'character': script[i]['actor'],
                    'text': script[i]['line']
                })
                current_time += fallback_duration
    
    return segments

def create_character_srt_from_segments(segments, output_path):
    """Create SRT file from audio segment timing"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, 1):
            start_srt = format_srt_time(segment['start'])
            end_srt = format_srt_time(segment['end'])
            
            f.write(f"{i}\n")
            f.write(f"{start_srt} --> {end_srt}\n")
            f.write(f"{segment['character']}\n\n")
    
    print(f"✅ Created character subtitles with {len(segments)} segments from audio timing")

def create_character_srt_file(segments, script, output_path):
    """Create SRT file that maps dialogue segments to characters using proper script order"""
    with open(output_path, 'w', encoding='utf-8') as f:
        subtitle_index = 1
        script_index = 0
        
        for segment in segments:
            if script_index >= len(script):
                break
                
            # Get the current character from script in order
            current_character = script[script_index]["actor"]
            
            # Get segment timing
            start_time = segment.get("start", 0)
            end_time = segment.get("end", start_time + 1)
            
            # Format times
            start_srt = format_srt_time(start_time)
            end_srt = format_srt_time(end_time)
            
            # Write character info as subtitle
            f.write(f"{subtitle_index}\n")
            f.write(f"{start_srt} --> {end_srt}\n")
            f.write(f"{current_character}\n\n")
            
            subtitle_index += 1
            script_index += 1
            
        print(f"✅ Created character subtitles with {subtitle_index-1} segments matching {len(script)} script lines")

def create_ass_highlight_subtitles(segments, output_path):
    generate_ass_highlight(segments, output_path)

def create_srt_file(segments, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        subtitle_entry_index = 1
        for segment in segments:
            if "words" in segment and segment["words"]:
                current_words_in_line = []
                for i, word_info in enumerate(segment["words"]):
                    if not isinstance(word_info, dict) or "word" not in word_info:
                        continue
                    current_words_in_line.append(word_info)
                    if len(current_words_in_line) == WORDS_PER_LINE or i == len(segment["words"]) - 1:
                        if not current_words_in_line:
                            continue
                        line_text = " ".join(w["word"].strip() for w in current_words_in_line if isinstance(w, dict) and "word" in w)
                        if not all(isinstance(w, dict) and "start" in w and "end" in w for w in current_words_in_line):
                            start_time = segment.get("start", 0)
                            end_time = segment.get("end", start_time + 1)
                        else:
                            start_time = current_words_in_line[0]["start"]
                            end_time = current_words_in_line[-1]["end"]
                        if end_time - start_time < 0.5:
                            end_time = start_time + 0.5
                        start_srt = format_srt_time(start_time)
                        end_srt = format_srt_time(end_time)
                        f.write(f"{subtitle_entry_index}\n")
                        f.write(f"{start_srt} --> {end_srt}\n")
                        f.write(f"{line_text}\n\n")
                        subtitle_entry_index += 1
                        current_words_in_line = []
            else:
                original_text = segment.get("text", "").strip()
                words_in_original_text = original_text.split()
                num_original_words = len(words_in_original_text)
                if num_original_words == 0:
                    continue
                seg_start_time = segment.get("start", 0)
                seg_end_time = segment.get("end", seg_start_time + (0.2 * num_original_words))
                seg_duration = seg_end_time - seg_start_time
                if seg_duration <= 0:
                    seg_duration = 0.2 * num_original_words
                    if seg_duration <= 0:
                        seg_duration = 0.5
                for i in range(0, num_original_words, WORDS_PER_LINE):
                    chunk_words = words_in_original_text[i: i + WORDS_PER_LINE]
                    if not chunk_words:
                        continue
                    line_text = " ".join(chunk_words)
                    num_chunk_words = len(chunk_words)
                    chunk_start_ratio = (i / num_original_words) if num_original_words > 0 else 0
                    chunk_end_ratio = ((i + num_chunk_words) / num_original_words) if num_original_words > 0 else 1
                    start_time = seg_start_time + (chunk_start_ratio * seg_duration)
                    end_time = seg_start_time + (chunk_end_ratio * seg_duration)
                    current_chunk_duration = end_time - start_time
                    if current_chunk_duration < 0.5:
                        end_time = start_time + 0.5
                    elif current_chunk_duration > 3.0:
                        end_time = start_time + 3.0
                    if end_time <= start_time:
                        end_time = start_time + 0.5
                    start_srt = format_srt_time(start_time)
                    end_srt = format_srt_time(end_time)
                    f.write(f"{subtitle_entry_index}\n")
                    f.write(f"{start_srt} --> {end_srt}\n")
                    f.write(f"{line_text}\n\n")
                    subtitle_entry_index += 1

def create_word_level_srt(segments, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        subtitle_index = 1
        for segment in segments:
            if "words" in segment:
                for word_info in segment["words"]:
                    word = word_info["word"].strip()
                    start_time = word_info["start"]
                    end_time = word_info["end"]
                    if end_time - start_time < 0.3:
                        end_time = start_time + 0.3
                    start_srt = format_srt_time(start_time)
                    end_srt = format_srt_time(end_time)
                    f.write(f"{subtitle_index}\n")
                    f.write(f"{start_srt} --> {end_srt}\n")
                    f.write(f"{word}\n\n")
                    subtitle_index += 1

def format_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
