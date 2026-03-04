import json
import os
from datetime import datetime
from typing import Any, Dict, List


PROGRESS_PATH = "outputs/json/progress.json"


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_progress() -> Dict[str, Any]:
    if not os.path.exists(PROGRESS_PATH):
        return {
            "children": {}  # key = child_name (ou id), value = stats
        }
    try:
        with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"children": {}}


def save_progress(data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(PROGRESS_PATH), exist_ok=True)
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_child_key(child_profile: Dict[str, Any]) -> str:
    # Simple: on utilise le prénom comme clé. (Tu peux améliorer + tard avec un id)
    name = (child_profile.get("name") or "Enfant").strip()
    return name if name else "Enfant"


def update_after_story(child_profile: Dict[str, Any], story_data: Dict[str, Any], meta: Dict[str, Any]) -> None:
    """
    Appelée quand une nouvelle histoire est générée.
    meta peut contenir: emotion, theme, age_group, n_scenes...
    """
    progress = load_progress()
    children = progress.setdefault("children", {})

    key = _get_child_key(child_profile)
    child = children.setdefault(
        key,
        {
            "profile": child_profile,
            "stories_count": 0,
            "words_learned": [],     # liste de mots uniques appris
            "emotions": [],          # émotions abordées (unique)
            "themes": [],            # valeurs / thèmes (unique)
            "choices": [],           # historique des choix
            "history": [],           # historique des histoires (résumé)
            "updated_at": None,
        },
    )

    # met à jour le profil enregistré (si la sidebar change)
    child["profile"] = child_profile

    # Compter histoires
    child["stories_count"] = int(child.get("stories_count", 0)) + 1

    # Mots appris = target_words
    target_words = story_data.get("target_words") or []
    for w in target_words:
        w = str(w).strip()
        if w and w not in child["words_learned"]:
            child["words_learned"].append(w)

    # Emotions / themes (issus de meta)
    emotion = meta.get("emotion")
    theme = meta.get("theme")

    if emotion and emotion not in child["emotions"]:
        child["emotions"].append(emotion)
    if theme and theme not in child["themes"]:
        child["themes"].append(theme)

    # Historique (mini résumé)
    child["history"].append(
        {
            "created_at": _now_iso(),
            "title": story_data.get("title", "Sans titre"),
            "age_group": meta.get("age_group"),
            "emotion": emotion,
            "theme": theme,
            "n_scenes": meta.get("n_scenes"),
            "target_words": target_words[:10],
        }
    )

    child["updated_at"] = _now_iso()
    save_progress(progress)


def update_after_choice(child_profile: Dict[str, Any], scene_no: int, question: str, choice: str) -> None:
    """
    Appelée quand l'enfant valide un choix.
    """
    progress = load_progress()
    children = progress.setdefault("children", {})

    key = _get_child_key(child_profile)
    child = children.setdefault(
        key,
        {
            "profile": child_profile,
            "stories_count": 0,
            "words_learned": [],
            "emotions": [],
            "themes": [],
            "choices": [],
            "history": [],
            "updated_at": None,
        },
    )

    child["profile"] = child_profile

    child["choices"].append(
        {
            "created_at": _now_iso(),
            "scene_no": int(scene_no),
            "question": question,
            "choice": choice,
        }
    )

    child["updated_at"] = _now_iso()
    save_progress(progress)