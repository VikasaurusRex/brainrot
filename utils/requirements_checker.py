import subprocess
from config import OLLAMA_URL, CHARACTERS, ASSETS

def check_requirements():
    print("\n" + "=" * 50)
    print("REQUIREMENTS CHECK")
    print("=" * 50)
    print("🔍 Checking requirements...")
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg available")
    except:
        print("❌ FFmpeg not found")
        return False
    try:
        import requests
        response = requests.get(OLLAMA_URL.replace('/api/generate', '/api/tags'), timeout=5)
        if response.status_code == 200:
            print("✅ Ollama running")
        else:
            print("❌ Ollama not responding correctly")
            return False
    except:
        print("❌ Ollama not accessible")
        return False
    for char, data in CHARACTERS.items():
        if not data["voice"].exists():
            print(f"❌ Missing voice sample: {data['voice']}")
            return False
        else:
            print(f"✅ {char} voice sample found")
    if not any((ASSETS / "input_videos").glob("*.mp4")):
        print("❌ No background videos found")
        return False
    else:
        print("✅ Background videos found")
    return True
