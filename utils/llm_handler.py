import requests
import json
from utils.config import OLLAMA_URL, MODEL, PROMPT

def generate_script(topic):
    """Generate dialogue script using Ollama"""
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
                return script_data["script"]
        return None
    except Exception as e:
        print(f"❌ Script generation failed: {e}")
        return None
