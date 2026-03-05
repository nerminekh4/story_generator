import os
import json
from dotenv import load_dotenv
import streamlit as st

from story.models import ChildProfile
from story.profile_store import load_profile, save_profile
from story.story_generator import generate_story
from story.tts import text_to_mp3
from story.image_generator import generate_image
from story.storage import ensure_dirs, save_json
from story.export_pdf import export_story_to_pdf
from story.progress_store import update_after_story, update_after_choice
from story.groq_client import get_groq_client


# ---------------------------
# Helpers UI: placeholders FR (compatibles anciennes versions)
# ---------------------------
def selectbox_fr(label, options, index=0, key=None):
    try:
        return st.selectbox(label, options, index=index, key=key, placeholder="Choisir…")
    except TypeError:
        return st.selectbox(label, options, index=index, key=key)


def multiselect_fr(label, options, default=None, key=None):
    if default is None:
        default = []
    try:
        return st.multiselect(label, options, default=default, key=key, placeholder="Choisir…")
    except TypeError:
        return st.multiselect(label, options, default=default, key=key)


def is_bad_image(path: str) -> bool:
    if not os.path.exists(path):
        return True
    try:
        return os.path.getsize(path) < 2000
    except OSError:
        return True


# ---------------------------
# Traduction via Groq (AJOUT)
# ---------------------------
LANG_UI_TO_NAME = {
    "fr": "French",
    "en": "English",
    "es": "Spanish",
    "it": "Italian",
    "zh-CN": "Chinese (Simplified)",
    "ar": "Arabic",
}
ALLOWED_LANGS = set(LANG_UI_TO_NAME.keys())


def _safe_json_loads(s: str):
    try:
        return json.loads(s)
    except Exception:
        return None


def translate_texts_batch(texts, target_lang_code: str):
    if target_lang_code == "fr":
        return texts

    target_name = LANG_UI_TO_NAME.get(target_lang_code, "English")
    try:
        client = get_groq_client()
        model_name = os.getenv("GROQ_MODEL_TRANSLATE", os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))

        payload = {"target_language": target_name, "texts": texts}

        system = (
            "You are a strict translation engine.\n"
            "Return ONLY valid JSON, with NO extra text.\n"
            "Rules:\n"
            "- Output must be a JSON array of strings, same length as input.\n"
            "- Preserve line breaks.\n"
            "- Do not add explanations.\n"
        )
        user = (
            "Translate the following JSON payload.\n"
            "Return ONLY the JSON array of translated strings.\n\n"
            f"PAYLOAD:\n{json.dumps(payload, ensure_ascii=False)}"
        )

        completion = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
        )

        raw = completion.choices[0].message.content.strip()
        data = _safe_json_loads(raw)
        if isinstance(data, list) and len(data) == len(texts) and all(isinstance(x, str) for x in data):
            return data

        return texts
    except Exception:
        return texts


def translate_story_data(story_data: dict, target_lang_code: str) -> dict:
    """
    Traduit: title, scenes[].text, scenes[].question, scenes[].choices(list), target_words(list)
    Ne traduit pas: image_prompt (pour ne pas casser HF)
    """
    if not story_data or target_lang_code == "fr":
        return story_data

    out = dict(story_data)
    scenes = out.get("scenes", []) or []

    batch = [str(out.get("title", ""))]
    plan = {"scenes": [], "tw_start": None, "tw_len": 0}
    cursor = 1

    for i, sc in enumerate(scenes):
        text = str(sc.get("text", ""))
        question = str(sc.get("question", "") or "")

        choices = sc.get("choices", []) or []
        if not isinstance(choices, list):
            choices = []
        choices = [str(c) for c in choices if str(c).strip()]

        # (scene_index, text_idx, question_idx, choices_start, choices_len)
        plan["scenes"].append((i, cursor, cursor + 1, cursor + 2, len(choices)))

        batch.append(text)
        batch.append(question)
        batch.extend(choices)
        cursor += 2 + len(choices)

    target_words = out.get("target_words", []) or []
    if not isinstance(target_words, list):
        target_words = []
    target_words = [str(w) for w in target_words if str(w).strip()]
    plan["tw_start"] = cursor
    plan["tw_len"] = len(target_words)
    batch.extend(target_words)

    translated = translate_texts_batch(batch, target_lang_code)

    out["title"] = translated[0] if translated else out.get("title", "")

    new_scenes = []
    for (i, t_idx, q_idx, c_start, c_len) in plan["scenes"]:
        sc0 = dict(scenes[i])

        if t_idx < len(translated):
            sc0["text"] = translated[t_idx]

        if q_idx < len(translated) and str(translated[q_idx]).strip():
            sc0["question"] = translated[q_idx]

        if c_len > 0 and c_start + c_len <= len(translated):
            sc0["choices"] = translated[c_start : c_start + c_len]

        new_scenes.append(sc0)

    out["scenes"] = new_scenes

    tw_start = plan["tw_start"]
    tw_len = plan["tw_len"]
    if isinstance(tw_start, int) and tw_len > 0 and tw_start + tw_len <= len(translated):
        out["target_words"] = translated[tw_start : tw_start + tw_len]

    return out


# ---------------------------
# Setup
# ---------------------------
load_dotenv()
ensure_dirs()
st.set_page_config(page_title="StoryGrow", layout="wide")

# ---------------------------
# CSS (FINAL) - ORIGINAL INCHANGÉ
# ---------------------------
st.markdown(
    r"""
<style>
/* =========================
   0) Enlever la barre noire du haut + footer
   ========================= */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
div[data-testid="stToolbar"] {display:none !important;}
div[data-testid="stHeader"] {display:none !important;}

/* =========
   BACKGROUND étoiles
   ========= */
.stApp {
  background-color: #ffffff;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220' viewBox='0 0 220 220'%3E%3Cg fill='none'%3E%3Cpath d='M24 25l2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z' fill='%23ff4d6d' opacity='.65'/%3E%3Cpath d='M176 38l2.2 4.4 4.9.7-3.6 3.5.9 4.9-4.4-2.3-4.4 2.3.9-4.9-3.6-3.5 4.9-.7z' fill='%2300b4ff' opacity='.55'/%3E%3Cpath d='M62 154l2.2 4.4 4.9.7-3.6 3.5.9 4.9-4.4-2.3-4.4 2.3.9-4.9-3.6-3.5 4.9-.7z' fill='%23ffd166' opacity='.6'/%3E%3Cpath d='M192 168l2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z' fill='%2367e8a3' opacity='.55'/%3E%3C/g%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 220px 220px;
}
.main .block-container {
  max-width: 1120px;
  padding-top: 0.8rem;
  padding-bottom: 2rem;
}

/* =========
   HEADER
   ========= */
.sg-hero { margin: 10px 0; text-align: center; padding: 10px; }
.sg-title {
  font-family: ui-rounded, "SF Pro Rounded", "Avenir Next", system-ui;
  font-weight: 900;
  letter-spacing: 0.6px;
  margin: 0;
  font-size: 90px;
  line-height: 1.0;
}
.sg-subtitle { margin-top: 10px; font-size: 16px; color: #1f2937; font-weight: 650; }
.sg-letter { display: inline-block; }
.sg-c1 { color: #ff4d6d; }
.sg-c2 { color: #ff7a59; }
.sg-c3 { color: #ffd166; }
.sg-c4 { color: #2dd4bf; }
.sg-c5 { color: #00b4ff; }
.sg-c6 { color: #3b82f6; }
.sg-c7 { color: #7c4dff; }

/* =========
   SIDEBAR
   ========= */
section[data-testid="stSidebar"] > div {
  background: #5db7ff;
  color: #ffffff;
}

/* cacher la nav auto multipage "app / Dashboard Parents" */
section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] { display:none !important; }

/* titres sidebar */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color:#ffffff !important; }

/* labels en rouge */
section[data-testid="stSidebar"] label {
  color:#ff1f4b !important;
  font-weight: 850 !important;
}

/* texte hors widgets */
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] small,
section[data-testid="stSidebar"] .stCaption {
  color:#ffffff !important;
}

/* =========================
    Widgets: fond clair + texte noir + bordure blanche
   ========================= */

/* input/textarea */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea {
  background: rgba(255,255,255,0.92) !important;
  border: 0 !important;
  outline: none !important;
  box-shadow: none !important;
  color: #111827 !important;
}

/* Bordure blanche (wrappers BaseWeb) */
section[data-testid="stSidebar"] div[data-baseweb="base-input"] > div,
section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
section[data-testid="stSidebar"] div[data-baseweb="textarea"] > div {
  background: rgba(255,255,255,0.92) !important;
  border: 2px solid rgba(255,255,255,0.95) !important;
  border-radius: 14px !important;
  box-shadow: none !important;
  outline: none !important;
}

/* Fix spécial Streamlit pour les contours noirs des text_input (Prénom / Personnage / Lieu) */
section[data-testid="stSidebar"] .stTextInput > div,
section[data-testid="stSidebar"] .stTextInput > div > div,
section[data-testid="stSidebar"] .stTextInput div[data-baseweb="base-input"] > div {
  border: 2px solid rgba(255,255,255,0.95) !important;
  border-radius: 14px !important;
  box-shadow: none !important;      /* enlève l’ombre noire */
  outline: none !important;
  background: rgba(255,255,255,0.92) !important;
}

/* select/multiselect */
section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
section[data-testid="stSidebar"] [role="combobox"] {
  background: rgba(255,255,255,0.92) !important;
  border: 2px solid rgba(255,255,255,0.95) !important;
  border-radius: 14px !important;
  box-shadow: none !important;
  outline: none !important;
}

/* texte DANS select/multiselect en noir */
section[data-testid="stSidebar"] div[data-baseweb="select"] * ,
section[data-testid="stSidebar"] [role="combobox"] * {
  color: #111827 !important;
}

/* placeholder visible */
section[data-testid="stSidebar"] input::placeholder,
section[data-testid="stSidebar"] textarea::placeholder {
  color: rgba(17,24,39,0.65) !important;
  font-weight: 600 !important;
}

/* menu options */
div[role="listbox"] { background:#ffffff !important; border:1px solid rgba(0,0,0,0.10) !important; }
div[role="option"] * { color:#111827 !important; }

/* =========================
    Chips multiselect : rouge + texte NOIR PAS GRAS
   ========================= */
section[data-testid="stSidebar"] span[data-baseweb="tag"] {
  background: #ff1f4b !important;
  color: #111827 !important;
  font-weight: 500 !important;   
  border: 0 !important;
}
section[data-testid="stSidebar"] span[data-baseweb="tag"] svg {
  fill: #111827 !important;
}

/* =========================
   Focus : bordure blanche 
   ========================= */
section[data-testid="stSidebar"] div[data-baseweb="base-input"] > div:focus-within,
section[data-testid="stSidebar"] div[data-baseweb="input"] > div:focus-within,
section[data-testid="stSidebar"] div[data-baseweb="textarea"] > div:focus-within,
section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within,
section[data-testid="stSidebar"] [role="combobox"]:focus-within,
section[data-testid="stSidebar"] .stTextInput > div:focus-within,
section[data-testid="stSidebar"] .stTextInput > div > div:focus-within {
  border: 2px solid rgba(255,255,255,1) !important;
  box-shadow: none !important;
  outline: none !important;
}

/* =========================
    Boutons rouges 
   ========================= */
.stButton > button {
  border-radius: 14px !important;
  font-weight: 900 !important;
  padding: 10px 14px !important;
}
div[data-testid="stButton"] > button{
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
.sg-story {
  border: 1px solid rgba(0,0,0,0.10);
  border-radius: 16px;
  padding: 14px 14px;
  background: #ffffff;
  color: #111827;
  font-size: 1.05rem;
  line-height: 1.65;
}
div[data-testid="stProgress"] > div > div { border-radius: 999px !important; }

/* nav buttons */
section[data-testid="stSidebar"] a[href*="app.py"],
section[data-testid="stSidebar"] a[href*="2_Dashboard_Parents.py"]{
  display: block;
  text-decoration: none !important;
  text-align: center;
  padding: 12px 12px;
  border: 2px solid rgba(255,255,255,0.95);
  border-radius: 16px;
  font-weight: 900;
  font-size: 18px;
  color: #ffffff !important;
  background: transparent;
  margin-bottom: 12px;
}
section[data-testid="stSidebar"] a[href*="app.py"]:hover,
section[data-testid="stSidebar"] a[href*="2_Dashboard_Parents.py"]:hover{
  background: rgba(255,255,255,0.15);
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# AJOUT CSS DRAPEAUX (NE CHANGE PAS TON UI)
# ---------------------------
st.markdown(
    """
<style>
.sg-langbar{
  position: fixed;
  right: 22px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 999999;
}
.sg-langbtn{
  font-size: 26px;
  text-decoration: none !important;
  background: transparent !important;
  border: none !important;
  padding: 6px 8px;
  border-radius: 10px;
  line-height: 1;
}
.sg-langbtn:hover{ filter: brightness(0.95); }
.sg-langbtn.active{ outline: 2px solid rgba(0,0,0,0.15); }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# AJOUT CSS BOUTON PREMIUM (NE CHANGE PAS TON UI)
# ---------------------------
st.markdown(
    """
<style>
.sg-premium{
  position: fixed;
  right: 22px;
  top: 18px;
  z-index: 999999;
}
.sg-premium a{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 14px;
  border-radius: 14px;
  background: #ff1f4b;
  color: #ffffff !important;
  font-weight: 350;
  text-decoration: none !important;
  box-shadow: 0 10px 22px rgba(0,0,0,0.10);
  border: 0;
}
.sg-premium a:hover{
  filter: brightness(0.95);
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Header (ORIGINAL)
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
# Session state (ORIGINAL + AJOUT)
# ---------------------------
if "story_data" not in st.session_state:
    st.session_state.story_data = None
if "scene_index" not in st.session_state:
    st.session_state.scene_index = 0
if "child_choices" not in st.session_state:
    st.session_state.child_choices = []

# AJOUT: langue + cache
if "ui_lang" not in st.session_state:
    st.session_state.ui_lang = "fr"
if "translated_cache" not in st.session_state:
    st.session_state.translated_cache = {}

# ---------------------------
# Lire la langue depuis URL ?lang=xx (AJOUT)
# ---------------------------
try:
    lang_q = st.query_params.get("lang", None)
    if isinstance(lang_q, list):
        lang_q = lang_q[0] if lang_q else None
except Exception:
    q = st.experimental_get_query_params()
    lang_q = q.get("lang", [None])[0]

if lang_q in ALLOWED_LANGS:
    st.session_state.ui_lang = lang_q

# ---------------------------
# Bouton Premium (AJOUT)
# ---------------------------
st.markdown(
    """
<div class="sg-premium">
  <a href="?premium=1">Premium</a>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# Afficher les drapeaux (AJOUT)
# ---------------------------
FLAGS = [("🇫🇷", "fr"), ("🇬🇧", "en"), ("🇪🇸", "es"), ("🇮🇹", "it"), ("🇨🇳", "zh-CN"), ("🇸🇦", "ar")]
html = '<div class="sg-langbar">'
for flag, code in FLAGS:
    cls = "sg-langbtn active" if st.session_state.ui_lang == code else "sg-langbtn"
    html += f'<a class="{cls}" href="?lang={code}">{flag}</a>'
html += "</div>"
st.markdown(html, unsafe_allow_html=True)

# ---------------------------
# Sidebar (ORIGINAL)
# ---------------------------
profile = load_profile()

with st.sidebar:
    st.markdown("### Navigation")
    try:
        st.page_link("app.py", label="Page principale", use_container_width=True)
        st.page_link("pages/2_Dashboard_Parents.py", label="Dashboard Parents", use_container_width=True)
    except Exception:
        st.info("Navigation: vérifie que pages/2_Dashboard_Parents.py existe.")
    st.divider()

    st.subheader("Profil enfant")

    child_name = st.text_input("Prénom", profile.name)
    child_age = st.slider("Âge", 3, 12, profile.age)

    reading_levels = ["débutant", "moyen", "avancé"]
    reading_level = selectbox_fr(
        "Niveau de lecture",
        reading_levels,
        index=reading_levels.index(profile.reading_level) if profile.reading_level in reading_levels else 0,
    )

    interests = multiselect_fr(
        "Centres d’intérêt",
        ["animaux", "espace", "dinosaures", "magie", "sport", "musique","robots","princesses","chevaliers","pirates"],
        default=profile.interests,
    )

    difficulties = multiselect_fr(
        "Besoins (optionnel)",
        ["dyslexie", "attention", "timidité", "peur du noir","impulsivité","difficulté à dormir","peur de la séparation"],
        default=profile.difficulties,
    )

    goals = ["confiance en soi", "gestion des emotions", "couleurs", "partage", "calme","écoute","autonomie","gratitude","concentration"]
    pedagogy_goal = selectbox_fr(
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
    age_group = selectbox_fr("Groupe d’âge", ["4-6", "7-9", "10-12"], index=0)
    character = st.text_input("Personnage", "Un petit renard")
    place = st.text_input("Lieu", "Une forêt magique")
    emotion = selectbox_fr("Émotion", ["joie", "courage", "curiosité", "calme"], index=0)
    theme = selectbox_fr("Valeur", ["amitié", "partage", "confiance", "découverte"], index=0)
    n_scenes = st.slider("Scènes", 3, 6, 4)

# ---------------------------
# Boutons centrés (ORIGINAL)
# ---------------------------
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
b1, b2 = st.columns([1, 1], gap="large")
with b1:
    st.markdown("<div style='display:flex; justify-content:flex-end;'>", unsafe_allow_html=True)
    create_clicked = st.button("Créer l’histoire", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
with b2:
    st.markdown("<div style='display:flex; justify-content:flex-start;'>", unsafe_allow_html=True)
    reset_clicked = st.button("Réinitialiser", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# ---------------------------
# Actions (ORIGINAL + reset cache traduction)
# ---------------------------
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

        # AJOUT: reset cache quand nouvelle histoire
        st.session_state.translated_cache = {}

        update_after_story(
            child_profile=profile.model_dump(),
            story_data=st.session_state.story_data,
            meta={"emotion": emotion, "theme": theme, "age_group": age_group, "n_scenes": n_scenes},
        )
        st.session_state.scene_index = 0
        st.session_state.child_choices = []

if reset_clicked:
    st.session_state.story_data = None
    st.session_state.scene_index = 0
    st.session_state.child_choices = []

    # AJOUT
    st.session_state.translated_cache = {}

    st.success("Réinitialisé")

# Export PDF + lien parents (ORIGINAL + PDF dans la langue affichée)
if st.session_state.story_data:
    exp_col1, exp_col2, exp_col3 = st.columns([1, 1, 1])
    with exp_col2:
        if st.button("Exporter PDF", use_container_width=True):
            lang = st.session_state.ui_lang
            base = st.session_state.story_data

            if lang == "fr":
                export_data = base
            else:
                if lang not in st.session_state.translated_cache:
                    with st.spinner("Traduction..."):
                        st.session_state.translated_cache[lang] = translate_story_data(base, lang)
                export_data = st.session_state.translated_cache[lang]

            scenes_for_pdf = []
            for sc in export_data["scenes"]:
                img_path = f"outputs/images/scene_{sc['scene_no']}.png"
                scenes_for_pdf.append({"scene_no": sc["scene_no"], "text": sc["text"], "image_path": img_path})

            pdf_path = "outputs/pdf/storygrow.pdf"
            export_story_to_pdf(export_data["title"], scenes_for_pdf, pdf_path)
            st.download_button(
                label="Télécharger le PDF",
                data=open(pdf_path, "rb").read(),
                file_name="storygrow.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
    with exp_col3:
        try:
            st.page_link("pages/2_Dashboard_Parents.py", label="Espace Parents", use_container_width=True)
        except Exception:
            st.info("Page Parents: crée le fichier pages/2_Dashboard_Parents.py")

# ---------------------------
# Contenu (ORIGINAL + data traduit selon langue)
# ---------------------------
base_data = st.session_state.story_data
lang = st.session_state.ui_lang

if not base_data:
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

if lang == "fr":
    data = base_data
else:
    if lang not in st.session_state.translated_cache:
        with st.spinner("Traduction..."):
            st.session_state.translated_cache[lang] = translate_story_data(base_data, lang)
    data = st.session_state.translated_cache[lang]

scenes = data["scenes"]
total = len(scenes)
idx = max(0, min(st.session_state.scene_index, total - 1))
st.session_state.scene_index = idx

st.progress((idx + 1) / total, text=f"Scène {idx+1}/{total}")

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

left, right = st.columns([1.15, 0.85])

with left:
    st.markdown("<div class='sg-card'><h3 style='margin:0; color:#111827;'>Texte</h3></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sg-story'>{text}</div>", unsafe_allow_html=True)

    # AUDIO (AJOUT): par langue
    audio_dir = os.path.join("outputs", "audio", lang)
    os.makedirs(audio_dir, exist_ok=True)
    audio_path = os.path.join(audio_dir, f"scene_{scene_no}.mp3")

    if not os.path.exists(audio_path):
        with st.spinner("Création audio..."):
            text_to_mp3(text, audio_path, lang=lang)

    st.audio(audio_path)

with right:
    st.markdown("<div class='sg-card'><h3 style='margin:0; color:#111827;'>Illustration</h3></div>", unsafe_allow_html=True)
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

question = scene.get("question")
choices_raw = scene.get("choices") or scene.get("options") or scene.get("answers")


def normalize_choices(x):
    if isinstance(x, list):
        return [str(i).strip() for i in x if str(i).strip()]
    if isinstance(x, str):
        lines = []
        for line in x.splitlines():
            s = line.strip()
            if not s:
                continue
            s = s.lstrip("-• \t")
            for p in ["A)", "B)", "C)", "D)"]:
                s = s.replace(p, "")
            s = s.strip()
            if s:
                lines.append(s)
        if len(lines) < 2 and ";" in x:
            parts = [p.strip() for p in x.split(";") if p.strip()]
            if len(parts) >= 2:
                return parts
        return lines
    return []


choices = normalize_choices(choices_raw)

if question and len(choices) >= 2:
    st.markdown(f"<p style='color:#111827; font-weight:bold; font-size:25px'>{question}</p>", unsafe_allow_html=True)

    # AJOUT: key dépend de la langue pour éviter erreurs si on change de langue
    choice = st.radio("Sélection :", choices[:2], key=f"choice_{lang}_{scene_no}")

    if st.button("Valider", key=f"btn_{lang}_{scene_no}"):
        st.session_state.child_choices.append({"scene_no": scene_no, "choice": choice})
        st.markdown(
            """
<div style="background-color:#fff4cc;color:#111827;padding:10px;border-radius:12px;font-weight:700;text-align:center;border:1px solid #ffd166;">
  🌟 Bravo ! Super choix ! 🌟
</div>
""",
            unsafe_allow_html=True,
        )
        update_after_choice(
            child_profile=profile.model_dump(),
            scene_no=scene_no,
            question=question,
            choice=choice,
        )

elif question:
    st.markdown("<div class='sg-card'><h3 style='margin:0; color:#111827;'>Choix</h3></div>", unsafe_allow_html=True)
    st.write(question)
    st.info("Aucun choix détecté pour cette scène (format inattendu).")

with st.expander("Debug (optionnel)"):
    st.write("Langue :", lang)
    st.write("Mots cibles :", data.get("target_words", []))
    st.write("Choix enregistrés :", st.session_state.child_choices)
    st.code(image_prompt)
    st.write("Question brute :", scene.get("question"))
    st.write("Choices brutes :", scene.get("choices"))
    st.write("Options brutes :", scene.get("options"))