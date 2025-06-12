import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS
from pathlib import Path
from utils.config import CHARACTERS

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
        actor = line["actor"]
        text = line["line"]
        voice_path = CHARACTERS[actor]["voice"]
        output_file = output_dir / f"{idx}_{actor.lower()}.wav"
        try:
            if not voice_path.exists():
                print(f"❌ Voice sample missing: {voice_path}")
                return None
            wav = model.generate(
                text,
                audio_prompt_path=str(voice_path),
                exaggeration=1,
                cfg_weight=0.7
            )
            ta.save(str(output_file), wav, model.sr)
            audio_files.append(str(output_file))
        except Exception as e:
            print(f"❌ Audio synthesis failed for {actor}: {e}")
            return None
    return audio_files
