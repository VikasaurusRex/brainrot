from pathlib import Path

# TOPIC = "The History of the Internet"  # Example topic, will be overridden by main.py

# =====================================

ASSETS = Path("assets")
OUTPUT = Path("output")
CHARACTERS = {
    "Peter": {"voice": ASSETS / "voices/peter_griffin.wav",},
    "Stewie": {"voice": ASSETS / "voices/stewie_griffin.wav",}
}
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "deepseek-r1:32b"
PROMPT = """You are a comedy writer known for raunchy sit-com dialogue. Peter is teaching Stewie about a topic in a humorous way.

Create around 10 lines of cohesive dialogue to explore a topic where:

- Stewie opens with a dumb observation
- Peter responds with a witty segue into the topic
- Stewie interjects occasionally with incorrect or tangential observations
- Peter responds with corrections and offers specific and correct information
- Peter finishes with a call to action to share this video if ... some condition is met making it relevant to the topic but as specific and funny as possible.

Use simple, clear language and make layered jokes!

Format as JSON: {\"script\": [{\"actor\": \"Peter\", \"line\": \"text\"}, ...]}
No other text, just the JSON."""
WIDTH, HEIGHT = 1080, 1920
FONT_SIZE = 100
WORDS_PER_LINE = 2
ASS_BASE_COLOR = "&H00FFFFFF"  # White
ASS_HIGHLIGHT_COLOR = "&H0000FF00"  # Green
