import os
from dotenv import load_dotenv
import streamlit as st

from story.models import ChildProfile
from story.profile_store import load_profile, save_profile
from story.story_generator import generate_story
from story.tts import text_to_mp3
from story.image_generator import generate_image
from story.storage import ensure_dirs, save_json
from story.export_pdf import export_story_to_pdf


def is_bad_image(path: str) -> bool:
    if not os.path.exists(path):
        return True
    try:
        return os.path.getsize(path) < 2000  
    except OSError:
        return True


def safe_generate_and_show_image(image_prompt: str, img_path: str, child_profile: dict):
    """
    - supprime une image cassée
    - tente de générer
    - affiche l'image si OK sinon affiche l'erreur
    """
    # si image cassée, on supprime pour forcer la régénération
    if is_bad_image(img_path) and os.path.exists(img_path):
        try:
            os.remove(img_path)
        except OSError:
            pass

    # si pas d'image, on génère
    if not os.path.exists(img_path):
        try:
            generate_image(image_prompt, img_path, child_profile=child_profile)
        except Exception as e:
            st.error("Erreur génération image (Hugging Face).")
            st.code(str(e))
            return

    # si toujours cassée -> message clair
    if is_bad_image(img_path):
        st.error("Image non générée (fichier vide ou invalide).")
        return

    # sinon affiche
    st.image(img_path, use_column_width=True)

    
# ---------------------------
# Setup
# ---------------------------
load_dotenv()
ensure_dirs()

st.set_page_config(page_title="StoryGrow", layout="wide")

# ---------------------------
# CSS (style demandé) + FIX sidebar input text + FIX boutons centrés
# ---------------------------
st.markdown(
    """
<style>
/* =========
   PAGE BACKGROUND: blanc + petites étoiles
   ========= */
.stApp {
  background-color: #ffffff;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220' viewBox='0 0 220 220'%3E%3Cg fill='none'%3E%3Cpath d='M24 25l2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z' fill='%23ff4d6d' opacity='.65'/%3E%3Cpath d='M176 38l2.2 4.4 4.9.7-3.6 3.5.9 4.9-4.4-2.3-4.4 2.3.9-4.9-3.6-3.5 4.9-.7z' fill='%2300b4ff' opacity='.55'/%3E%3Cpath d='M62 154l2.2 4.4 4.9.7-3.6 3.5.9 4.9-4.4-2.3-4.4 2.3.9-4.9-3.6-3.5 4.9-.7z' fill='%23ffd166' opacity='.6'/%3E%3Cpath d='M192 168l2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z' fill='%2367e8a3' opacity='.55'/%3E%3C/g%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 220px 220px;
}

/* Container */
.main .block-container {
  max-width: 1120px;
  padding-top: 0.8rem;
  padding-bottom: 2rem;
}

/* =========
   HEADER centré
   ========= */
.sg-hero {
  margin: 10px 0 10px 0;
  text-align: center;
  padding: 10px 10px;
}

.sg-title {
  font-family: ui-rounded, "SF Pro Rounded", "Avenir Next", system-ui;
  font-weight: 900;
  letter-spacing: 0.6px;
  margin: 0;
  font-size: 56px;
  line-height: 1.0;
}

.sg-subtitle {
  margin: 10px 0 0 0;
  font-size: 16px;
  color: #1f2937;
  font-weight: 650;
}

/* lettres colorées assorties */
.sg-letter { display: inline-block; }
.sg-c1 { color: #ff4d6d; }
.sg-c2 { color: #ff7a59; }
.sg-c3 { color: #ffd166; }
.sg-c4 { color: #2dd4bf; }
.sg-c5 { color: #00b4ff; }
.sg-c6 { color: #3b82f6; }
.sg-c7 { color: #7c4dff; }

/* =========
   SIDEBAR bleu clair + labels rouges + texte blanc
   ========= */
section[data-testid="stSidebar"] > div {
  background: #5db7ff;
  color: #ffffff;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
  color: #ffffff !important;
}

/* labels en rouge */
section[data-testid="stSidebar"] label {
  color: #ff1f4b !important;
  font-weight: 850 !important;
}

/* textes hors champs en blanc */
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
  color: #ffffff !important;
}

/* inputs: fond clair + arrondi */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea {
  background: rgba(255,255,255,0.92) !important;
  border-radius: 12px !important;
}

/* selectbox (zone) */
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
  background: rgba(255,255,255,0.92) !important;
  border-radius: 12px !important;
}

/* =========
   FIX #1: texte à l'intérieur des cases toujours lisible (noir/gris foncé)
   -> on ne touche PAS aux labels dehors (blanc/rouge)
   ========= */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea,
section[data-testid="stSidebar"] div[data-baseweb="select"] * ,
section[data-testid="stSidebar"] div[data-baseweb="tag"] {
  color: #111827 !important;   /* texte dans les champs */
}

/* placeholder dans les champs */
section[data-testid="stSidebar"] input::placeholder,
section[data-testid="stSidebar"] textarea::placeholder {
  color: rgba(17,24,39,0.55) !important;
}

/* Tags du multiselect (chips) : texte blanc dedans, mais lisible */
section[data-testid="stSidebar"] span[data-baseweb="tag"] {
  color: #ffffff !important;
  background: #ff1f4b !important;
  border: 0 !important;
}
section[data-testid="stSidebar"] span[data-baseweb="tag"] svg {
  fill: #ffffff !important;
}

/* =========
   Buttons
   ========= */
.stButton > button {
  border-radius: 14px !important;
  font-weight: 900 !important;
  padding: 10px 14px !important;
}

div[data-testid="stButton"] > button[kind="primary"]{
  background: #ff1f4b !important;
  border: 0 !important;
  color: white !important;
}

/* Cards */
.sg-card {
  background: rgba(255,255,255,0.94);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 18px;
  padding: 16px 16px;
  box-shadow: 0 10px 22px rgba(0,0,0,0.06);
  margin-bottom: 14px;
}

/* Story text */
.sg-story {
  border: 1px solid rgba(0,0,0,0.10);
  border-radius: 16px;
  padding: 14px 14px;
  background: #ffffff;
  color: #111827;
  font-size: 1.05rem;
  line-height: 1.65;
}

/* Progress bar arrondie */
div[data-testid="stProgress"] > div > div {
  border-radius: 999px !important;
}

/* ===============================
   FIX RADIO CHOICES VISIBILITY
   =============================== */
   
/* Texte "Sélection :" */
div[data-testid="stRadio"] > label {
  color: #111827 !important;
  font-size:18px;
}

/* Texte des options radio */
div[role="radiogroup"] > label {
  color: #111827 !important;
  font-size:14px;
}

/* Cercle sélectionné (petite pastille) */
div[role="radiogroup"] div {
  color: #111827 !important;
  border-color: #ff1f4b !important;
}


</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Header centré (multicolore)
# ---------------------------
st.markdown(
    """
<div class="sg-hero">
  <h1 class="sg-title">
    <span class="sg-letter sg-c1">S</span>
    <span class="sg-letter sg-c2">t</span>
    <span class="sg-letter sg-c3">o</span>
    <span class="sg-letter sg-c4">r</span>
    <span class="sg-letter sg-c5">y</span>
    <span class="sg-letter sg-c6">G</span>
    <span class="sg-letter sg-c7">r</span>
    <span class="sg-letter sg-c1">o</span>
    <span class="sg-letter sg-c2">w</span>
  </h1>
  <div class="sg-subtitle">Histoires illustrées personnalisées, adaptées au profil de l’enfant.</div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Session state
# ---------------------------
if "story_data" not in st.session_state:
    st.session_state.story_data = None
if "scene_index" not in st.session_state:
    st.session_state.scene_index = 0
if "child_choices" not in st.session_state:
    st.session_state.child_choices = []

# ---------------------------
# Sidebar: Profil + paramètres histoire
# ---------------------------
profile = load_profile()

with st.sidebar:
    st.subheader("Profil enfant")

    child_name = st.text_input("Prénom", profile.name)
    child_age = st.slider("Âge", 3, 12, profile.age)

    reading_levels = ["débutant", "moyen", "avancé"]
    reading_level = st.selectbox(
        "Niveau de lecture",
        reading_levels,
        index=reading_levels.index(profile.reading_level) if profile.reading_level in reading_levels else 0,
    )

    interests = st.multiselect(
        "Centres d’intérêt",
        ["animaux", "espace", "dinosaures", "magie", "sport", "musique"],
        default=profile.interests,
    )

    difficulties = st.multiselect(
        "Besoins (optionnel)",
        ["dyslexie", "attention", "timidité", "peur_du_noir"],
        default=profile.difficulties,
    )

    goals = ["confiance", "gestion_des_emotions", "couleurs", "partage", "calme"]
    pedagogy_goal = st.selectbox(
        "Objectif",
        goals,
        index=goals.index(profile.pedagogy_goal) if profile.pedagogy_goal in goals else 0,
    )

    if st.button("Sauvegarder", use_container_width=True):
        profile = ChildProfile(
            name=child_name,
            age=child_age,
            reading_level=reading_level,
            interests=interests,
            difficulties=difficulties,
            pedagogy_goal=pedagogy_goal,
        )
        save_profile(profile)
        st.success("Profil sauvegardé")

    st.divider()

    st.subheader("Histoire")
    age_group = st.selectbox("Groupe d’âge", ["4-6", "7-9", "10-12"], index=0)
    character = st.text_input("Personnage", "Un petit renard")
    place = st.text_input("Lieu", "Une forêt magique")
    emotion = st.selectbox("Émotion", ["joie", "courage", "curiosité", "calme"])
    theme = st.selectbox("Valeur", ["amitié", "partage", "confiance", "découverte"])
    n_scenes = st.slider("Scènes", 3, 6, 4)

# ---------------------------
# FIX #2: Boutons centrés sous le titre
# ---------------------------
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
b1, b2 = st.columns([1, 1], gap="large")
with b1:
    st.markdown("<div style='display:flex; justify-content:flex-end;'>", unsafe_allow_html=True)
    create_clicked = st.button("Créer l’histoire", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
with b2:
    st.markdown("<div style='display:flex; justify-content:flex-start;'>", unsafe_allow_html=True)
    reset_clicked = st.button("Réinitialiser", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# Actions
if create_clicked:
    with st.spinner("Génération de l’histoire..."):
        story = generate_story(
            character=character,
            place=place,
            emotion=emotion,
            theme=theme,
            age_group=age_group,
            n_scenes=n_scenes,
            child_profile=profile.model_dump(),
        )
        st.session_state.story_data = story.model_dump()
        save_json(st.session_state.story_data, "outputs/json/last_story.json")
        st.session_state.scene_index = 0
        st.session_state.child_choices = []

if reset_clicked:
    st.session_state.story_data = None
    st.session_state.scene_index = 0
    st.session_state.child_choices = []
    st.success("Réinitialisé")

# Export PDF (reste en bas comme avant)
if st.session_state.story_data:
    exp_col1, exp_col2, exp_col3 = st.columns([1, 1, 1])
    with exp_col2:
        if st.button("Exporter PDF", use_container_width=True):
            scenes_for_pdf = []
            for sc in st.session_state.story_data["scenes"]:
                img_path = f"outputs/images/scene_{sc['scene_no']}.png"
                scenes_for_pdf.append({"scene_no": sc["scene_no"], "text": sc["text"], "image_path": img_path})
            pdf_path = "outputs/pdf/storygrow.pdf"
            export_story_to_pdf(st.session_state.story_data["title"], scenes_for_pdf, pdf_path)
            st.download_button(
                label="Télécharger le PDF",
                data=open(pdf_path, "rb").read(),
                file_name="storygrow.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

# ---------------------------
# Contenu
# ---------------------------
data = st.session_state.story_data
if not data:
    st.markdown(
        """
<div class="sg-card">
  <h3 style="margin:0; color:#111827;">Démarrer</h3>
  <p style="margin:8px 0 0 0; color:#374151;">
    Complète le profil à gauche, puis clique sur <b>Créer l’histoire</b>.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.stop()

scenes = data["scenes"]
total = len(scenes)
idx = max(0, min(st.session_state.scene_index, total - 1))
st.session_state.scene_index = idx

st.progress((idx + 1) / total, text=f"Scène {idx+1}/{total}")

# Titre histoire + infos
st.markdown(
    f"""
<div class="sg-card">
  <h2 style="margin:0; color:#111827;">{data["title"]}</h2>
  <p style="margin:8px 0 0 0; color:#374151;">
    Profil : <b>{profile.name}</b> ({profile.age} ans) — Objectif : <b>{profile.pedagogy_goal}</b> — Niveau : <b>{profile.reading_level}</b>
  </p>
</div>
""",
    unsafe_allow_html=True,
)

# Navigation
n1, n2, n3 = st.columns([1, 1, 1])
with n1:
    if st.button("Précédent", use_container_width=True) and idx > 0:
        st.session_state.scene_index -= 1
        st.rerun()
with n2:
    st.markdown(
        f"<div style='text-align:center; font-weight:900; color:#111827;'>Scène {idx+1}</div>",
        unsafe_allow_html=True,
    )
with n3:
    if st.button("Suivant", use_container_width=True) and idx < total - 1:
        st.session_state.scene_index += 1
        st.rerun()

scene = scenes[idx]
scene_no = scene["scene_no"]
text = scene["text"]
image_prompt = scene["image_prompt"]

# Layout texte / image
left, right = st.columns([1.15, 0.85])

with left:
    st.markdown(
        "<div class='sg-card'><h3 style='margin:0; color:#111827;'>Texte</h3></div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<div class='sg-story'>{text}</div>", unsafe_allow_html=True)

    audio_path = f"outputs/audio/scene_{scene_no}.mp3"
    if not os.path.exists(audio_path):
        with st.spinner("Création audio..."):
            text_to_mp3(text, audio_path, lang="fr")
    st.audio(audio_path)

with right:
    st.markdown(
        "<div class='sg-card'><h3 style='margin:0; color:#111827;'>Illustration</h3></div>",
        unsafe_allow_html=True,
    )
    img_path = f"outputs/images/scene_{scene_no}.png"

    with st.spinner("Génération image..."):
        if is_bad_image(img_path) and os.path.exists(img_path):
            try:
                os.remove(img_path)
            except OSError:
                pass

        if not os.path.exists(img_path):
            try:
                generate_image(image_prompt, img_path, child_profile=profile.model_dump())
            except Exception as e:
                st.error("Erreur génération image (Hugging Face).")
                st.code(str(e))

    if not is_bad_image(img_path):
        st.image(img_path, use_column_width=True)
    else:
        st.error("Image non générée ou fichier invalide.")

# Choix interactif (si présent)
# Choix interactif (si présent)
question = scene.get("question")

# Certaines IA renvoient les choix sous d'autres clés
choices_raw = scene.get("choices")
if choices_raw is None:
    choices_raw = scene.get("options")
if choices_raw is None:
    choices_raw = scene.get("answers")

def normalize_choices(x):
    # 1) Liste déjà OK
    if isinstance(x, list):
        out = []
        for item in x:
            s = str(item).strip()
            if s:
                out.append(s)
        return out

    # 2) String: on extrait les lignes comme choix
    if isinstance(x, str):
        lines = []
        for line in x.splitlines():
            s = line.strip()
            if not s:
                continue
            # supprime les préfixes "A)", "B)", "-", "•", "1."
            s = s.lstrip("-• \t")
            s = s.replace("A)", "").replace("B)", "").replace("C)", "").replace("D)", "")
            s = s.strip()
            if s:
                lines.append(s)
        # parfois c’est séparé par ";"
        if len(lines) < 2 and ";" in x:
            parts = [p.strip() for p in x.split(";") if p.strip()]
            if len(parts) >= 2:
                return parts
        return lines

    # 3) Autres types -> vide
    return []

choices = normalize_choices(choices_raw)

if question and len(choices) >= 2:
    st.markdown(
        f"<p style='color:#111827; font-weight:bold; font-size:25px'>{question}</p>",
        unsafe_allow_html=True,
    )
    
    choice = st.radio("Sélection :", choices[:2], key=f"choice_{scene_no}")

    if st.button("Valider", key=f"btn_{scene_no}"):
        st.session_state.child_choices.append({"scene_no": scene_no, "choice": choice})
        st.markdown(
    """
    <div style="
        background-color:#fff4cc;
        color:#111827;
        padding:10px;
        border-radius:12px;
        font-weight:700;
        text-align:center;
        border:1px solid #ffd166;
    ">
        🌟 Bravo ! Super choix ! 🌟
    </div>
    """,
    unsafe_allow_html=True,
)
        
elif question:
    # Si question présente mais pas de choix exploitables
    st.markdown(
        "<div class='sg-card'><h3 style='margin:0; color:#111827;'>Choix</h3></div>",
        unsafe_allow_html=True,
    )
    st.write(question)
    st.info("Aucun choix détecté pour cette scène (format inattendu).")

# Debug (optionnel)
with st.expander("Debug (optionnel)"):
    st.write("Mots cibles :", data.get("target_words", []))
    st.write("Choix enregistrés :", st.session_state.child_choices)
    st.code(image_prompt)
    st.write("Question brute :", scene.get("question"))
    st.write("Choices brutes :", scene.get("choices"))
    st.write("Options brutes :", scene.get("options"))