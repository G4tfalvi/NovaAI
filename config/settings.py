from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "models"


def find_wakeword_model():
    models = list(
        MODEL_DIR.glob("*.onnx")
    )

    if not models:
        return None

    return str(models[0])


class Settings:

    wakeword_name = "Hey Nova"
    wakeword_model = find_wakeword_model()
    wakeword_threshold = 0.55

    sample_rate = 16000
    wakeword_block_size = 1280

    stt_model = "small"
    stt_language = "hu"
    listen_max_seconds = 10
    silence_seconds = 1.0


SETTINGS = Settings()