from pydantic import BaseModel, Field
from typing import List, Optional


class ChildProfile(BaseModel):
    name: str = "Enfant"
    age: int = Field(5, ge=3, le=12)
    reading_level: str = "débutant"  # débutant / moyen / avancé
    interests: List[str] = []
    difficulties: List[str] = []     # ex: ["dyslexie", "attention"]
    pedagogy_goal: str = "confiance" # confiance / gestion_des_emotions / couleurs / partage / calme


class Scene(BaseModel):
    scene_no: int = Field(..., ge=1)
    text: str = Field(..., min_length=1)
    image_prompt: str = Field(..., min_length=1)

    # StoryGrow: gamification légère
    question: Optional[str] = None
    choices: List[str] = []


class Story(BaseModel):
    title: str = Field(..., min_length=1)
    age_group: str = Field(..., min_length=1)
    scenes: List[Scene] = Field(..., min_length=1)

    # StoryGrow: mots cibles pédagogiques
    target_words: List[str] = []