import json
import os
from typing import Any, Dict


def ensure_dirs() -> None:
    folders = [
        "outputs",
        "outputs/audio",
        "outputs/images",
        "outputs/pdf",
        "outputs/json",
    ]
    for folder in folders:
        if os.path.exists(folder) and not os.path.isdir(folder):
            raise RuntimeError(f"{folder} existe mais ce n'est pas un dossier.")
        os.makedirs(folder, exist_ok=True)


def save_json(data: Dict[str, Any], out_path: str) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)