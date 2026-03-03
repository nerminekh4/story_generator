import os
import time
import requests


def build_visual_constraints(child_profile: dict) -> str:
    diffs = set(child_profile.get("difficulties", []))
    goal = child_profile.get("pedagogy_goal", "")

    constraints = []

    # Inclusion: réduire complexité visuelle
    if "attention" in diffs or "dyslexie" in diffs:
        constraints.append("simple background, low clutter, clear subject centered")

    # Objectifs pédagogiques visuels
    if goal == "couleurs":
        constraints.append("primary colors emphasis, high contrast, very colorful")

    if goal == "gestion_des_emotions":
        constraints.append("expressive face, clear emotion, warm and friendly")

    if goal == "calme":
        constraints.append("soft pastel colors, calm mood, gentle lighting")

    # Toujours éviter texte/filigrane
    constraints.append("no text, no letters, no watermark")

    return ", ".join(constraints)


def _hf_inference_call(prompt: str, model_id: str, token: str, timeout: int = 120) -> bytes:
    """
    Appelle l'API Inference de Hugging Face.
    Retour attendu: bytes de l'image.
    Si le modèle charge ("is currently loading"), on attend et on réessaie.
    """
    url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "inputs": prompt,
        # paramètres optionnels (peuvent être ignorés selon modèle)
        "parameters": {
            "guidance_scale": 7.5,
            "num_inference_steps": 30,
        }
    }

    # On tente plusieurs fois (modèle parfois en "loading")
    for attempt in range(1, 6):
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)

        ctype = (r.headers.get("content-type") or "").lower()

        # ✅ Cas normal: on reçoit directement l'image
        if r.status_code == 200 and ("image" in ctype or ctype == "application/octet-stream"):
            return r.content

        # Cas JSON d'erreur (modèle en chargement, quota, etc.)
        try:
            data = r.json()
        except Exception:
            data = None

        if r.status_code == 503 and isinstance(data, dict) and "estimated_time" in data:
            # modèle en chargement
            wait_s = int(max(2, data.get("estimated_time", 3)))
            time.sleep(wait_s)
            continue

        # autre erreur
        raise RuntimeError(f"HuggingFace Inference error ({r.status_code}): {data if data else r.text}")

    raise RuntimeError("HuggingFace: modèle trop long à charger (après plusieurs tentatives).")


def generate_image(image_prompt: str, out_path: str, child_profile: dict, width: int = 512, height: int = 512) -> None:
    """
    Génère une image via Hugging Face Inference API.

    Notes:
    - width/height ne sont pas toujours respectés par tous les modèles HF.
    - Pour un rendu stable, on force un style "livre enfant" + contraintes profil.
    """
    token = os.getenv("HF_API_TOKEN", "").strip()
    if not token:
        raise ValueError("HF_API_TOKEN manquante. Mets-la dans le fichier .env")

    model_id = os.getenv("HF_IMAGE_MODEL", "stabilityai/stable-diffusion-xl-base-1.0").strip()

    base_style = "children's book illustration, cute, colorful, soft lighting, consistent character design"
    constraints = build_visual_constraints(child_profile)

    prompt = (image_prompt or "").strip()
    if not prompt:
        prompt = "a cute character in a simple scene"

    # prompt final
    full_prompt = f"{base_style}, {prompt}, {constraints}".strip()

    img_bytes = _hf_inference_call(full_prompt, model_id=model_id, token=token)

    # Sauvegarde
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(img_bytes)