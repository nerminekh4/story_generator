from gtts import gTTS


def text_to_mp3(text: str, out_path: str, lang: str = "fr") -> None:
    tts = gTTS(text=text, lang=lang)
    tts.save(out_path)