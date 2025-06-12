import re
from pathlib import Path
from config import FONT_SIZE, ASS_BASE_COLOR, ASS_HIGHLIGHT_COLOR, WORDS_PER_LINE

def format_ass_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int((seconds % 1) * 100)
    return f"{hours:d}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

def escape_ass_text(text):
    # Escape curly braces and backslashes for ASS
    return text.replace('{', '\\{').replace('}', '\\}').replace('\\', '\\\\')

def generate_ass_highlight(segments, output_path, font_name="Luckiest Guy", font_size=FONT_SIZE, outline=3):
    """
    segments: list of dicts with keys: 'words' (list of dicts with 'word','start','end'), 'text', 'start', 'end'
    output_path: Path to write the .ass file
    """
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{ASS_BASE_COLOR},{ASS_HIGHLIGHT_COLOR},&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,{outline},0,2,60,60,1400,1
Style: Highlight,{font_name},{font_size},{ASS_HIGHLIGHT_COLOR},{ASS_BASE_COLOR},&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,{outline},0,2,60,60,1400,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for segment in segments:
        if "words" in segment and segment["words"]:
            # Group words into chunks based on WORDS_PER_LINE
            current_words_in_line = []
            for i, word_info in enumerate(segment["words"]):
                if not isinstance(word_info, dict) or "word" not in word_info:
                    continue
                current_words_in_line.append(word_info)
                if len(current_words_in_line) == WORDS_PER_LINE or i == len(segment["words"]) - 1:
                    if not current_words_in_line:
                        continue
                    
                    # Determine line timing
                    if not all(isinstance(w, dict) and "start" in w and "end" in w for w in current_words_in_line):
                        line_start = segment.get("start", 0)
                        line_end = segment.get("end", line_start + 1)
                    else:
                        line_start = current_words_in_line[0]["start"]
                        line_end = current_words_in_line[-1]["end"]
                    
                    if line_end - line_start < 0.5:
                        line_end = line_start + 0.5
                    
                    # Create highlight events for each word in this line
                    for j, word_info in enumerate(current_words_in_line):
                        word_start = word_info.get("start", line_start)
                        word_end = word_info.get("end", word_start + 0.3)
                        
                        # Build the line with current word highlighted
                        line_parts = []
                        for k, w in enumerate(current_words_in_line):
                            word_txt = escape_ass_text(w["word"].strip())
                            if k == j:
                                # Highlight current word using ASS color codes
                                line_parts.append(f"{{\\c{ASS_HIGHLIGHT_COLOR.replace('&H', '&H')}&}}{word_txt}{{\\c{ASS_BASE_COLOR.replace('&H', '&H')}&}}")
                            else:
                                line_parts.append(word_txt)
                        
                        ass_line = " ".join(line_parts)
                        events.append(f"Dialogue: 0,{format_ass_time(word_start)},{format_ass_time(word_end)},Default,,0,0,0,,{ass_line}")
                    
                    current_words_in_line = []
        else:
            # Fallback for segments without word-level timestamps
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
                
                num_chunk_words = len(chunk_words)
                chunk_start_ratio = (i / num_original_words) if num_original_words > 0 else 0
                chunk_end_ratio = ((i + num_chunk_words) / num_original_words) if num_original_words > 0 else 1
                line_start = seg_start_time + (chunk_start_ratio * seg_duration)
                line_end = seg_start_time + (chunk_end_ratio * seg_duration)
                
                if line_end - line_start < 0.5:
                    line_end = line_start + 0.5
                
                # Create simple subtitle without word-level highlighting for fallback
                line_text = " ".join(escape_ass_text(word) for word in chunk_words)
                events.append(f"Dialogue: 0,{format_ass_time(line_start)},{format_ass_time(line_end)},Default,,0,0,0,,{line_text}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header)
        for ev in events:
            f.write(ev + "\n")

# Example usage:
# generate_ass_highlight(segments, Path("output/test_highlight.ass"))
