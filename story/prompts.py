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

INCLUSION:
- Si difficultés incluent dyslexie: phrases très courtes, mots très simples, répétitions douces.
- Si difficultés incluent attention: scènes courtes, action claire, peu de personnages secondaires.

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
  "age_group": "string",
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