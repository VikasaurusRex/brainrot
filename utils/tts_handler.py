import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS
from pathlib import Path
from config import CHARACTERS

def setup_tts_model():
    """Initialize ChatterboxTTS with CPU compatibility"""
    original_torch_load = torch.load
    def patched_torch_load(*args, **kwargs):
        kwargs['map_location'] = torch.device('cpu')
        return original_torch_load(*args, **kwargs)
    torch.load = patched_torch_load
    try:
        model = ChatterboxTTS.from_pretrained(device="cpu")
        torch.load = original_torch_load
        return model
    except Exception as e:
        torch.load = original_torch_load
        print(f"❌ TTS model failed: {e}")
        return None

def synthesize_audio(script, model, output_dir):
    """Generate audio for each line using ChatterboxTTS"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []
    
    for idx, line in enumerate(script):
        try:
            # Validate script entry structure
            if not isinstance(line, dict):
                print(f"❌ Script entry {idx} is not a dictionary: {line}")
                return None
            
            if "actor" not in line:
                print(f"❌ Script entry {idx} missing 'actor' field: {line}")
                return None
                
            if "line" not in line:
                print(f"❌ Script entry {idx} missing 'line' field: {line}")
                return None
            
            actor = line["actor"]
            text = line["line"]
            
            # Clean and preprocess text
            text = text.strip()
            # Replace problematic unicode characters
            text = text.replace('\u2019', "'")  # Replace smart apostrophe
            text = text.replace('\u2013', "-")  # Replace en dash
            text = text.replace('\u2014', "--") # Replace em dash
            text = text.replace('\u201c', '"')  # Replace left double quote
            text = text.replace('\u201d', '"')  # Replace right double quote
            
            if not text:
                print(f"⚠️ Skipping empty text for {actor} at entry {idx}")
                continue
            
            # Validate actor exists in characters config
            if actor not in CHARACTERS:
                print(f"❌ Unknown actor '{actor}' in script entry {idx}")
                return None
            
            voice_path = CHARACTERS[actor]["voice"]
            output_file = output_dir / f"{idx}_{actor.lower()}.wav"
            
            if not voice_path.exists():
                print(f"❌ Voice sample missing: {voice_path}")
                return None
            
            print(f"🎙️ Generating audio for {actor}: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            print(f"📝 Full text (length {len(text)}): '{text}'")
            print(f"🎵 Voice path: {voice_path}")
            
            try:
                wav = model.generate(
                    text,
                    audio_prompt_path=str(voice_path),
                    exaggeration=1,
                    cfg_weight=0.7
                )
                print(f"✅ Audio generation successful for {actor}")
            except Exception as generation_error:
                print(f"❌ TTS model generation failed for {actor}: {generation_error}")
                print(f"❌ Error type: {type(generation_error).__name__}")
                
                # Try with simplified text (remove punctuation, etc.)
                simplified_text = ''.join(c for c in text if c.isalnum() or c.isspace())
                simplified_text = ' '.join(simplified_text.split())  # Normalize whitespace
                
                if simplified_text != text and len(simplified_text) > 0:
                    print(f"🔄 Retrying with simplified text: '{simplified_text}'")
                    try:
                        wav = model.generate(
                            simplified_text,
                            audio_prompt_path=str(voice_path),
                            exaggeration=1,
                            cfg_weight=0.7
                        )
                        print(f"✅ Audio generation successful with simplified text for {actor}")
                    except Exception as retry_error:
                        print(f"❌ Retry also failed for {actor}: {retry_error}")
                        raise retry_error
                else:
                    raise generation_error
            ta.save(str(output_file), wav, model.sr)
            audio_files.append(str(output_file))
            
        except Exception as e:
            print(f"❌ Audio synthesis failed for entry {idx} ({line.get('actor', 'unknown')}): {e}")
            return None
    
    print(f"✅ Generated {len(audio_files)} audio files")
    return audio_files
