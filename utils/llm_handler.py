import requests
import json
from config import OLLAMA_URL, MODEL, PROMPT

def validate_script_structure(script):
    """Validate that each script entry has required 'actor' and 'line' fields"""
    if not isinstance(script, list):
        print("❌ Script is not a list")
        return False
    
    for i, entry in enumerate(script):
        if not isinstance(entry, dict):
            print(f"❌ Script entry {i} is not a dictionary")
            return False
        if "actor" not in entry:
            print(f"❌ Script entry {i} missing 'actor' field")
            return False
        if "line" not in entry:
            print(f"❌ Script entry {i} missing 'line' field")
            return False
        if not isinstance(entry["actor"], str) or not entry["actor"].strip():
            print(f"❌ Script entry {i} has invalid 'actor' field")
            return False
        if not isinstance(entry["line"], str) or not entry["line"].strip():
            print(f"❌ Script entry {i} has invalid 'line' field")
            return False
    
    print(f"✅ Script structure validated: {len(script)} entries")
    return True

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
                        script = script_data["script"]
                        # Validate script structure
                        if validate_script_structure(script):
                            return script
                        else:
                            print(f"⚠️ Invalid script structure. Retry {retries + 1}/{max_retries}")
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

def generate_title_and_description(topic, output_dir):
    """Generate a catchy title and long-form description using Ollama and save to a .txt file."""
    title_prompt = f"Generate a catchy, specific, and silly video title for a video about: {topic}. The title should be short and attention-grabbing."
    description_prompt = f"Generate a long-form, verbose, and keyword-rich video description for a video about: {topic}. The description should include as many relevant keywords as possible to maximize virality and searchability. Make it comprehensive and engaging."

    for prompt_type, prompt_content in [("title", title_prompt), ("description", description_prompt)]:
        retries = 0
        max_retries = 3
        generated_text = None
        while retries < max_retries:
            payload = {
                "model": MODEL,
                "prompt": prompt_content,
                "system": "You are a helpful assistant that generates creative and engaging video titles and descriptions.",
                # Not using JSON format for these as they are free-form text
                "stream": False
            }
            try:
                response = requests.post(OLLAMA_URL, json=payload, timeout=60)
                response.raise_for_status()
                result = response.json()
                if "response" in result and result["response"].strip():
                    generated_text = result["response"].strip()
                    break
                else:
                    print(f"⚠️ Empty response for {prompt_type}. Retry {retries + 1}/{max_retries}")
            except requests.exceptions.RequestException as e:
                print(f"❌ {prompt_type.capitalize()} generation request failed: {e}. Retry {retries + 1}/{max_retries}")
            except Exception as e:
                print(f"❌ An unexpected error occurred during {prompt_type} generation: {e}. Retry {retries + 1}/{max_retries}")
            
            retries += 1
            if retries < max_retries:
                print(f"Retrying {prompt_type} generation...")

        if not generated_text:
            print(f"❌ {prompt_type.capitalize()} generation failed after {max_retries} retries.")
            # Fallback to a simple text if generation fails
            generated_text = f"Failed to generate {prompt_type} for {topic}" if prompt_type == "title" else f"A video about {topic}."

        # Save to file
        try:
            file_path = output_dir / f"video_{prompt_type}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(generated_text)
            print(f"📄 Video {prompt_type} saved: {file_path}")
        except Exception as e:
            print(f"❌ Failed to save video {prompt_type} to file: {e}")
            return False # Indicate failure to save

    return True # Indicate success if both are generated and attempted to save
