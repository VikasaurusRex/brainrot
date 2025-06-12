import requests
import json
from config import OLLAMA_URL, MODEL, PROMPT

def generate_script(topic):
    """Generate dialogue script using Ollama with retries for JSON validation"""
    retries = 0
    max_retries = 5
    while retries < max_retries:
        payload = {
            "model": MODEL,
            "prompt": f"TOPIC: {topic}",
            "system": PROMPT,
            "format": "json",
            "stream": False
        }
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            if "response" in result:
                try:
                    script_data = json.loads(result["response"])
                    if "script" in script_data:
                        return script_data["script"]
                    else:
                        print(f"⚠️ 'script' key not found in JSON response. Retry {retries + 1}/{max_retries}")
                except json.JSONDecodeError as json_e:
                    print(f"❌ Invalid JSON response: {json_e}. Retry {retries + 1}/{max_retries}")
            else:
                print(f"⚠️ 'response' key not found in API result. Retry {retries + 1}/{max_retries}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Script generation request failed: {e}. Retry {retries + 1}/{max_retries}")
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}. Retry {retries + 1}/{max_retries}")
        
        retries += 1
        if retries < max_retries:
            print(f"Retrying...")
            # Optional: Add a small delay here if needed, e.g., time.sleep(1)
            
    print(f"❌ Script generation failed after {max_retries} retries.")
    return None
