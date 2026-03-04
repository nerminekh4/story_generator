import os
from gtts import gTTS


def text_to_mp3(text: str, out_path: str, lang: str = "fr") -> None:
    # Sécurise le dossier parent
    parent = os.path.dirname(out_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    tts = gTTS(text=text, lang=lang)
    tts.save(out_path)