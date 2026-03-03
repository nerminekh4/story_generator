import os
import json
from .groq_client import get_groq_client
from .prompts import build_story_prompt
from .models import Story


def generate_story(
    character: str,
    place: str,
    emotion: str,
    theme: str,
    age_group: str,
    n_scenes: int,
    child_profile: dict,
) -> Story:
    client = get_groq_client()
    prompt = build_story_prompt(character, place, emotion, theme, age_group, n_scenes, child_profile)

    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "Tu réponds en JSON strict, sans texte autour."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    raw = completion.choices[0].message.content.strip()
    data = json.loads(raw)
    return Story.model_validate(data)