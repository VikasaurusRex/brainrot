This spec is designed for maximum clarity to ensure a smooth implementation process. Implement, but use the Brainrot notebook instead of a main. Please take your time to ensure everything is rigorously implemented and well connected.

### **1. Project Overview**

The goal is to create a single Python script (`main.py`) that, when executed, automates the entire process of creating a short-form vertical video. The script will generate a dialogue, synthesize speech, select a background video, and render a final MP4 file with character sprites and animated subtitles, all using local tools. Each run will generate a unique, timestamped output folder to keep all related assets organized.

### **2. Core Technologies**

* **Language**: Python 3.9+
* **LLM**: Ollama with the **`qwen3:30b-a3b`** model.
* **TTS / Voice Cloning**: **Chatterbox TTS**
* **Audio Transcription (for timestamps)**: Whisper
* **Video Processing**: FFmpeg
* **Python Libraries**: `requests`, **`chatterbox-tts`**, **`torch`**, **`torchaudio`**, `subprocess`, `moviepy` (optional).

### **3. Directory Structure Plan**

The directory structure has been updated to place all inputs within the `assets` folder and to create a unique, timestamped folder for each video generation run.

```
/Viral_Video_Project/
|
|-- main.py                     # The main execution script
|-- config.py                   # Central configuration for all parameters
|-- requirements.txt            # Python dependencies
|
|-- /assets/
|   |
|   |-- /input_videos/            # <-- MOVED HERE
|   |   |-- minecraft_parkour_1.mp4
|   |   |-- ...
|   |
|   |-- /voices/
|   |   |-- peter_griffin.wav   # High-quality voice sample for voice cloning
|   |   |-- stewie_griffin.wav
|   |
|   |-- /images/
|   |   |-- Peter.png           # Character sprite, transparent background
|   |   |-- Stewie.png
|   |
|   |-- /fonts/
|   |   |-- LuckiestGuy-Regular.ttf
|
|-- /output/
|   |
|   |-- /1717983014/               # <-- EXAMPLE TIMESTAMPED OUTPUT FOLDER
|   |   |-- final_video.mp4       # The final rendered video
|   |   |-- master_audio.wav      # The combined dialogue track
|   |   |-- script.json           # A copy of the generated script
|   |   |-- timestamps.json       # Word-level timestamps from Whisper
|   |   |-- /temp_audio/          # Temp audio clips for each line
|   |   |   |-- 0_stewie.wav
|   |   |   |-- 1_peter.wav
|   |   |   |-- ...
```

### **4. Detailed Task Specification**

#### **Task 4.1: Update `requirements.txt`**

This file lists all necessary Python packages for installation.

**`requirements.txt` - Content:**
```
# For LLM communication
requests

# For Text-to-Speech
chatterbox-tts
torch
torchaudio

# For audio transcription (if using the library)
openai-whisper

# Optional, for easier video manipulation
moviepy
```

#### **Task 4.2: Update the Configuration File (`config.py`)**

The configuration is updated with the new LLM model and simplified paths, as full output paths will be generated dynamically.

**`config.py` - Example Content:**
```python
# -- File Paths --
ASSET_PATH = "assets/"
INPUT_VIDEO_PATH = f"{ASSET_PATH}input_videos/"
VOICE_PATH = f"{ASSET_PATH}voices/"
IMAGE_PATH = f"{ASSET_PATH}images/"
FONT_PATH = f"{ASSET_PATH}fonts/"
FONT_FILE = f"{FONT_PATH}LuckiestGuy-Regular.ttf"
OUTPUT_PATH = "output/"

# -- LLM & Script Generation --
OLLAMA_API_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "qwen3:30b-a3b"  # <-- UPDATED MODEL
LLM_SYSTEM_PROMPT = """
You are an expert scriptwriter for viral short-form videos. Your task is to write a short, funny, and engaging conversation between Peter Griffin and Stewie Griffin.
The script should be no more than 6 lines of dialogue in total. The topic of the conversation will be provided by the user.
You MUST format your response as a valid JSON object, containing a single key "script" which is an array of objects.
Each object in the array must have two keys: "actor" (either "Peter" or "Stewie") and "line" (the character's dialogue).
Do not include any other text, preambles, or explanations in your response.
"""

# -- Character & Asset Mapping --
CHARACTERS = {
    "Peter": {
        "voice_sample": f"{VOICE_PATH}peter_griffin.wav",
        "image": f"{IMAGE_PATH}Peter.png",
    },
    "Stewie": {
        "voice_sample": f"{VOICE_PATH}stewie_griffin.wav",
        "image": f"{IMAGE_PATH}Stewie.png",
    }
}

# -- Video Rendering Settings --
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
BACKGROUND_VIDEO_VOLUME = 0.3

# -- Subtitle Settings --
SUBTITLE_FONT_SIZE = 120
SUBTITLE_FONT_COLOR = "white"
SUBTITLE_HIGHLIGHT_COLOR = "#24ff03"
SUBTITLE_OUTLINE_COLOR = "black"
SUBTITLE_POSITION_Y = 1600
```

#### **Task 4.3: Implement the Main Script (`main.py`)**

The main script will now create a unique directory for each run.

**`main.py` - Example Content (Skeleton):**
```python
import os
import random
import json
import subprocess
import time
from config import *

# --- MODULES WOULD BE DEFINED HERE OR IMPORTED ---
# e.g., from llm_handler import generate_script
# from tts_handler import synthesize_dialogue # <-- Updated for Chatterbox
# from video_renderer import create_final_video

def main(topic: str):
    """ Main function to generate a video from a topic. """
    print("--- Starting Video Generation ---")
    
    # 1. Create a unique timestamped directory for this run
    run_timestamp = str(int(time.time()))
    run_output_path = os.path.join(OUTPUT_PATH, run_timestamp)
    temp_audio_path = os.path.join(run_output_path, "temp_audio")
    os.makedirs(temp_audio_path, exist_ok=True)
    print(f"Created output directory: {run_output_path}")

    # 2. Generate Script using LLM
    print(f"1. Generating script for topic: {topic}...")
    # script_data = generate_script(topic)
    # with open(os.path.join(run_output_path, "script.json"), 'w') as f:
    #     json.dump(script_data, f, indent=2)

    # 3. Synthesize Audio for each line using Chatterbox TTS
    print("2. Synthesizing audio with Chatterbox...")
    # dialogue_with_audio = synthesize_dialogue(script_data, temp_audio_path)

    # 4. Concatenate all audio clips
    print("3. Combining audio clips...")
    # master_audio_path = os.path.join(run_output_path, "master_audio.wav")
    # combine_audio_clips(dialogue_with_audio, master_audio_path)

    # 5. Get Word-Level Timestamps using Whisper
    print("4. Generating word-level timestamps...")
    # timed_script = get_word_timestamps(master_audio_path)
    # with open(os.path.join(run_output_path, "timestamps.json"), 'w') as f:
    #     json.dump(timed_script, f, indent=2)

    # 6. Select a Random Background Video
    print("5. Selecting random background video...")
    background_video_path = os.path.join(INPUT_VIDEO_PATH, random.choice(os.listdir(INPUT_VIDEO_PATH)))
    
    # 7. Render the Final Video
    print("6. Rendering the final video...")
    final_video_path = os.path.join(run_output_path, "final_video.mp4")
    # create_final_video(timed_script, master_audio_path, background_video_path, final_video_path)
    
    print(f"--- Video Generation Complete! ---")
    print(f"Final video saved to: {final_video_path}")

if __name__ == "__main__":
    video_topic = "Why cats secretly run the world"
    main(video_topic)
```

#### **Task 4.4: Define Implementation Details for Modules**

* **LLM Handler (`llm_handler.py`)**:
    * **Function**: `generate_script(topic: str) -> list | None`
    * **Logic**: No changes in logic. It will use the `LLM_MODEL` from `config.py`, which is now `qwen3:30b-a3b`.

* **TTS Handler (`tts_handler.py`) - UPDATED FOR CHATTERBOX**:
    * **Function**: `synthesize_dialogue(script: list, output_dir: str) -> list`
    * **Logic**:
        1.  Import `ChatterboxTTS` from `chatterbox.tts` and `torchaudio`.
        2.  Initialize the model once: `model = ChatterboxTTS.from_pretrained(device="cuda")`.
        3.  Loop through the `script` list with an index (`idx`).
        4.  For each line, get the character's voice sample path (`audio_prompt_path`) from the `CHARACTERS` dictionary.
        5.  Generate the audio tensor: `wav = model.generate(line['line'], audio_prompt_path=audio_prompt_path)`.
        6.  Define a unique output path: `output_file = os.path.join(output_dir, f"{idx}_{line['actor'].lower()}.wav")`.
        7.  Save the audio file: `torchaudio.save(output_file, wav, model.sr)`.
        8.  Add the `audio_path` key to the line object: `line['audio_path'] = output_file`.
        9.  Return the updated `script` list.

* **Video Renderer (`video_renderer.py`)**:
    * **Logic**: No major changes to the core logic, but it's critical that the function signature is updated to accept the dynamically generated `run_output_path` or the specific file paths within it, ensuring it reads from and writes to the correct timestamped folder for each run.