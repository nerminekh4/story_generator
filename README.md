# StoryGrow 🌱📚  
**Générateur d’histoires illustrées adaptatives pour enfants (Streamlit + IA)**

StoryGrow est une mini-application éducative qui génère **des histoires personnalisées**, **illustrées scène par scène**, avec **audio**, **traduction multilingue**, **choix interactifs** et **export PDF** — le tout adapté au **profil réel** de l’enfant (âge, niveau de lecture, centres d’intérêt, difficultés, objectif pédagogique).  
> Objectif : aider les parents à accompagner leurs enfants dans la lecture… avec une histoire qui s’adapte à l’enfant, pas l’inverse.

---

## ✨ Fonctionnalités

### 🎯 Personnalisation par profil enfant
Le profil inclut : **âge (3–12)**, **niveau de lecture**, **centres d’intérêt**, **difficultés** (ex: dyslexie, attention), **objectif pédagogique** (couleurs, calme, émotions, etc.).  
Le générateur adapte le vocabulaire et le style en conséquence.  
(voir `ChildProfile` dans `story/models.py`) :contentReference[oaicite:1]{index=1}

### 🤖 Génération d’histoire (LLM)
- Génère une histoire structurée en **JSON strict** (titre + scènes).
- Ajoute des **questions + 2 choix** régulièrement (gamification légère).
- Répète des **mots cibles** pour la mémorisation.  
(voir `story/story_generator.py` et `story/prompts.py`) :contentReference[oaicite:2]{index=2}

### 🎨 Illustrations scène par scène (Hugging Face)
- Génère une image pour chaque scène via l’API Inference Hugging Face.
- Style forcé : **illustration “livre pour enfants”** + cohérence personnage + contraintes “no text / no watermark”.  
(voir `story/image_generator.py`) :contentReference[oaicite:3]{index=3}

### 🔊 Audio (TTS)
- Génère l’audio de l’histoire via **gTTS** (Google Text-to-Speech).  
(voir `requirements.txt`) :contentReference[oaicite:4]{index=4}

### 🌍 Traduction multilingue (texte + UI)
- Traduction via **Groq** (batch JSON).
- Langues UI supportées : **FR, EN, ES, IT, AR, ZH-CN**.  
(voir `app.py`) :contentReference[oaicite:5]{index=5}

### 🧾 Export PDF
- Export de l’histoire en PDF (et dans la langue affichée).  
(voir `app.py`) :contentReference[oaicite:6]{index=6}

### 👨‍👩‍👧 Dashboard Parents
- Suivi : **mots appris, émotions, choix, thèmes, historique** des histoires.
- Historique des décisions de l’enfant (les plus récents en premier).  
(voir `pages/2_Dashboard_Parents.py`) :contentReference[oaicite:7]{index=7}

---

## 🧱 Stack technique
- **Python** + **Streamlit**
- **Groq API** pour génération + traduction :contentReference[oaicite:8]{index=8}  
- **Hugging Face Inference API** pour images :contentReference[oaicite:9]{index=9}  
- **gTTS** pour audio :contentReference[oaicite:10]{index=10}  
- **ReportLab** pour export PDF :contentReference[oaicite:11]{index=11}  
- **Pydantic** pour les modèles de données (profil, scènes, histoire) :contentReference[oaicite:12]{index=12}

---

## 📂 Structure du projet

```bash
.
├── app.py
├── pages/
│   └── 2_Dashboard_Parents.py
├── story/
│   ├── models.py
│   ├── prompts.py
│   ├── story_generator.py
│   ├── image_generator.py
│   ├── tts.py
│   ├── export_pdf.py
│   ├── profile_store.py
│   ├── progress_store.py
│   ├── groq_client.py
│   └── storage.py
├── outputs/
│   ├── images/
│   ├── pdf/
│   └── ...
└── requirements.txt

🚀 Installation & Lancement
# 1) Cloner
git clone https://github.com/nerminekh4/story_generator.git
cd story_generator

# 2) (Optionnel) Créer un venv
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3) Installer les dépendances
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4) Lancer l’app
streamlit run app.py

🧪 Utilisation (workflow)
Remplir le profil enfant dans la sidebar (âge, niveau, difficultés, objectif).
Choisir personnage / lieu / émotion / thème + nombre de scènes.
Cliquer Créer l’histoire :
LLM génère l’histoire (JSON)
HF génère une image par scène
gTTS génère l’audio
Lire l’histoire + répondre aux choix.
Ouvrir Espace Parents pour consulter l’historique.
Exporter l’histoire en PDF.

🗺️ Roadmap (améliorations prévues)
✅ Champs libres dans la sidebar (centres d’intérêt / besoins personnalisés)
🎧 Audio premium : musique douce + bruitages contextuels (forêt, pluie, oiseaux…)
🌳 Vraie interactivité : les choix changent réellement la scène suivante (mini arborescence narrative)
📈 Profil évolutif : apprentissage des préférences + émotions + progression et adaptation automatique
👪 Dashboard parents avancé : recommandations d’activités + axes d’amélioration