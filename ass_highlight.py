import re
from pathlib import Path

def format_ass_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int((seconds % 1) * 100)
    return f"{hours:d}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

def escape_ass_text(text):
    # Escape curly braces and backslashes for ASS
    return text.replace('{', '\\{').replace('}', '\\}').replace('\\', '\\\\')

def generate_ass_highlight(segments, output_path, font_name="Luckiest Guy", font_size=60, outline=3):
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
Style: Default,{font_name},{font_size},&H00FFFFFF,&H0000FF00,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,{outline},0,2,60,60,400,1
Style: Highlight,{font_name},{font_size},&H0000FF00,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,{outline},0,2,60,60,400,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for segment in segments:
        if "words" not in segment or not segment["words"]:
            continue
        words = segment["words"]
        full_line = " ".join(escape_ass_text(w["word"]) for w in words)
        for i, word_info in enumerate(words):
            # Highlight only the current word
            start = word_info["start"]
            end = word_info["end"]
            # Compose line with highlight
            line_parts = []
            for j, w in enumerate(words):
                word_txt = escape_ass_text(w["word"])
                if j == i:
                    line_parts.append(r"{\\c&H24FF03&}" + word_txt + r"{\\c&HFFFFFF&}")
                else:
                    line_parts.append(word_txt)
            ass_line = " ".join(line_parts)
            events.append(f"Dialogue: 0,{format_ass_time(start)},{format_ass_time(end)},Default,,0,0,0,,{ass_line}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header)
        for ev in events:
            f.write(ev + "\n")

# Example usage:
# generate_ass_highlight(segments, Path("output/test_highlight.ass"))
