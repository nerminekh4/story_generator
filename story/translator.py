import json
import os
from typing import Any, Dict, List, Optional

from .groq_client import get_groq_client


# Mapping "UI" -> langue cible (en toutes lettres, pour le prompt)
LANG_UI_TO_NAME = {
    "fr": "French",
    "en": "English",
    "es": "Spanish",
    "it": "Italian",
    "zh-CN": "Chinese (Simplified)",
    "ar": "Arabic",
}


def _safe_json_loads(s: str) -> Optional[Any]:
    try:
        return json.loads(s)
    except Exception:
        return None


def translate_texts(texts: List[str], target_lang_code: str) -> List[str]:
    """
    Traduit une liste de textes en une seule requête Groq, et renvoie la liste traduite.
    Retourne les originaux si problème.
    """
    target_name = LANG_UI_TO_NAME.get(target_lang_code, "English")

    # Rien à faire
    if target_lang_code == "fr":
        return texts

    client = get_groq_client()
    model_name = os.getenv("GROQ_MODEL_TRANSLATE", os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))

    payload = {
        "target_language": target_name,
        "texts": texts,
    }

    system = (
        "You are a strict translation engine.\n"
        "Return ONLY valid JSON, with NO extra text.\n"
        "Rules:\n"
        "- Output must be a JSON array of strings, same length as input.\n"
        "- Preserve line breaks if present.\n"
        "- Do not add explanations.\n"
    )

    user = (
        "Translate the following JSON payload.\n"
        "Return ONLY the JSON array of translated strings.\n\n"
        f"PAYLOAD:\n{json.dumps(payload, ensure_ascii=False)}"
    )

    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        raw = completion.choices[0].message.content.strip()
        data = _safe_json_loads(raw)

        if isinstance(data, list) and len(data) == len(texts) and all(isinstance(x, str) for x in data):
            return data

        # Si le modèle renvoie autre chose, fallback
        return texts
    except Exception:
        return texts


def translate_story_data(story_data: Dict[str, Any], target_lang_code: str) -> Dict[str, Any]:
    """
    Prend story_data (dict) et renvoie une copie traduite:
    - title
    - scenes[].text
    - scenes[].question
    - scenes[].choices (liste)
    - target_words
    """
    if not story_data or target_lang_code == "fr":
        return story_data

    out = dict(story_data)  # shallow copy
    scenes = out.get("scenes", []) or []

    # Construire la liste de textes à traduire en batch
    # Ordre: title, puis pour chaque scène: text, question (ou ""), puis choices (0..n), puis target_words
    batch: List[str] = []
    batch.append(str(out.get("title", "")))

    # On garde un plan de reconstruction
    plan = {"title": 0, "scenes": [], "target_words_start": None, "target_words_len": 0}
    cursor = 1

    for i, sc in enumerate(scenes):
        sc = dict(sc)
        text = str(sc.get("text", ""))
        question = str(sc.get("question", "") or "")
        choices = sc.get("choices", []) or []
        choices = [str(c) for c in choices if str(c).strip()]

        entry = {
            "scene_index": i,
            "text_idx": cursor,
            "question_idx": cursor + 1,
            "choices_idx_start": cursor + 2,
            "choices_len": len(choices),
        }
        plan["scenes"].append(entry)

        batch.append(text)
        batch.append(question)
        batch.extend(choices)

        cursor += 2 + len(choices)

    target_words = out.get("target_words", []) or []
    target_words = [str(w) for w in target_words if str(w).strip()]
    plan["target_words_start"] = cursor
    plan["target_words_len"] = len(target_words)
    batch.extend(target_words)

    translated = translate_texts(batch, target_lang_code)

    # Reconstruction
    out["title"] = translated[plan["title"]] if translated else out.get("title", "")

    new_scenes = []
    for entry in plan["scenes"]:
        i = entry["scene_index"]
        sc0 = dict(scenes[i])

        sc0["text"] = translated[entry["text_idx"]] if entry["text_idx"] < len(translated) else sc0.get("text", "")
        q_idx = entry["question_idx"]
        q_val = translated[q_idx] if q_idx < len(translated) else (sc0.get("question") or "")
        sc0["question"] = q_val if str(q_val).strip() else sc0.get("question")

        # choices
        c_start = entry["choices_idx_start"]
        c_len = entry["choices_len"]
        if c_len > 0 and c_start + c_len <= len(translated):
            sc0["choices"] = translated[c_start : c_start + c_len]
        else:
            sc0["choices"] = sc0.get("choices", [])

        new_scenes.append(sc0)

    out["scenes"] = new_scenes

    tw_start = plan["target_words_start"]
    tw_len = plan["target_words_len"]
    if isinstance(tw_start, int) and tw_len > 0 and tw_start + tw_len <= len(translated):
        out["target_words"] = translated[tw_start : tw_start + tw_len]
    else:
        out["target_words"] = out.get("target_words", [])

    return out