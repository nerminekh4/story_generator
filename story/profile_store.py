import json
import os
from .models import ChildProfile

PROFILE_PATH = "outputs/json/child_profile.json"


def load_profile() -> ChildProfile:
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ChildProfile.model_validate(data)
    return ChildProfile()


def save_profile(profile: ChildProfile) -> None:
    os.makedirs("outputs/json", exist_ok=True)
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile.model_dump(), f, ensure_ascii=False, indent=2)