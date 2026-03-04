def build_story_prompt(
    character: str,
    place: str,
    emotion: str,
    theme: str,
    age_group: str,
    n_scenes: int,
    child_profile: dict,
) -> str:
    return f"""
Tu es un auteur d'histoires pour enfants + un pédagogue.

PROFIL ENFANT:
{child_profile}

OBJECTIF:
Créer une histoire chaleureuse et inclusive en {n_scenes} scènes.

CONTRAINTES LANGAGE:
- Groupe d'âge: {age_group}
- Niveau de lecture: {child_profile.get("reading_level")}
- Phrases courtes, vocabulaire simple.
- Répéter 2 à 3 mots-clés importants pour mémorisation.
- Toutes les 2 scènes: une question interactive ("Et toi, que ferais-tu ?") + 2 choix simples.
- Chaque scène doit être assez longue de à peu près 500 mots par scène pour maintenir l'intérêt que l'enfant a pour l'histoire.

INCLUSION:
- Si difficultés incluent dyslexie: mots très simples, répétitions douces, adapter à une personne dyslexique.
- Si difficultés incluent attention: action claire, peu de personnages secondaires, adapter à une personne qui a des troubles de l'attention.

PARAMÈTRES HISTOIRE:
- Personnage principal: {character}
- Lieu: {place}
- Émotion dominante: {emotion}
- Thème/valeur: {theme}
- Objectif pédagogique: {child_profile.get("pedagogy_goal")}

CONTRAINTES IMAGES:
Pour chaque scène, "image_prompt" doit être une description VISUELLE (pas de texte dans l'image),
style livre pour enfants, couleurs vives, douce, mignonne.
Toujours garder un personnage cohérent (même animal/couleur).

FORMAT:
Réponds UNIQUEMENT en JSON strict, sans texte autour:
{{
  "title": "string",
  "age_group": "4-6 ou 7-9 ou 10-12",
  "scenes": [
    {{
      "scene_no": 1,
      "text": "string",
      "image_prompt": "string",
      "question": "string ou null",
      "choices": ["string", "string"] ou []
    }}
  ],
  "target_words": ["liste de mots simples à renforcer"]
}}
""".strip()