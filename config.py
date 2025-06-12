from pathlib import Path

TOPIC = "BRAT diet for recovering from diarrhea"
ASSETS = Path("assets")
OUTPUT = Path("output")
CHARACTERS = {
    "Peter": {"voice": ASSETS / "voices/peter_griffin.wav", "image": ASSETS / "images/Peter.png"},
    "Stewie": {"voice": ASSETS / "voices/stewie_griffin.wav", "image": ASSETS / "images/Stewie.png"}
}
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "deepseek-r1:32b"
PROMPT = """You are a scriptwriter for videos where Peter Griffin teaches Stewie Griffin.

Create lines of dialogue where:

- Stewie opens with attention grabbing remark
- Peter responds with a witty comeback before pivoting smoothly into the topic
- Stewie interjects occasionally with incorrect observations or tangential remarks
- Peter responds with corrections and teaches Stewie correct information
- Peter finishes with a call to action to share with a humourous twist

Use simple, clear language suitable for a general audience!

Format as JSON: {\"script\": [{\"actor\": \"Peter\", \"line\": \"text\"}, ...]}
No other text, just the JSON."""
WIDTH, HEIGHT = 1080, 1920
FONT_SIZE = 30
