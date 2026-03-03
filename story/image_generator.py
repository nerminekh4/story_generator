import requests
import urllib.parse


def build_visual_constraints(child_profile: dict) -> str:
    diffs = set(child_profile.get("difficulties", []))
    goal = child_profile.get("pedagogy_goal", "")

    constraints = []

    # Inclusion: réduire complexité visuelle
    if "attention" in diffs or "dyslexie" in diffs:
        constraints.append("simple background, low clutter, clear subject centered")

    # Objectifs pédagogiques visuels
    if goal == "couleurs":
        constraints.append("primary colors emphasis (red blue yellow), high contrast, very colorful")

    if goal == "gestion_des_emotions":
        constraints.append("expressive face, clear emotion, warm and friendly")

    if goal == "calme":
        constraints.append("soft pastel colors, calm mood, gentle lighting")

    # Toujours éviter texte/filigrane
    constraints.append("no text, no letters, no watermark")

    return ", ".join(constraints)


def generate_image(image_prompt: str, out_path: str, child_profile: dict, width: int = 512, height: int = 512) -> None:
    """
    Génère une image via Pollinations (gratuit, sans clé).
    On force un style "livre enfant" + contraintes selon profil.
    """
    base_style = "children's book illustration, cute, colorful, soft lighting, consistent character design"
    constraints = build_visual_constraints(child_profile)

    prompt = image_prompt.strip()
    if not prompt:
        prompt = "a cute character in a simple scene"

    full_prompt = f"{base_style}, {prompt}, {constraints}".strip()

    encoded = urllib.parse.quote(full_prompt)
    url = (
        f"https://gen.pollinations.ai/image/{encoded}"
        f"?width={width}&height={height}"
        f"&nologo=true&safe=true"
    )

    r = requests.get(url, timeout=120)
    r.raise_for_status()

    with open(out_path, "wb") as f:
        f.write(r.content)