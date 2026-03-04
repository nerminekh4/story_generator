import streamlit as st
from story.progress_store import load_progress
from collections import Counter

st.set_page_config(page_title="StoryGrow – Dashboard Parents", layout="wide")

# =========================
# CSS (DA identique app.py + fixes)
# =========================
st.markdown(
    """
<style>

/* =========================
   0) Enlever la barre du haut (Deploy / menu)
   ========================= */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
div[data-testid="stToolbar"] {display: none !important;}
div[data-testid="stHeader"] {display:none !important;}

/* =========
   Background étoiles (identique app.py)
   ========= */
.stApp {
  background-color: #ffffff;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='220' viewBox='0 0 220 220'%3E%3Cg fill='none'%3E%3Cpath d='M24 25l2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z' fill='%23ff4d6d' opacity='.65'/%3E%3Cpath d='M176 38l2.2 4.4 4.9.7-3.6 3.5.9 4.9-4.4-2.3-4.4 2.3.9-4.9-3.6-3.5 4.9-.7z' fill='%2300b4ff' opacity='.55'/%3E%3Cpath d='M62 154l2.2 4.4 4.9.7-3.6 3.5.9 4.9-4.4-2.3-4.4 2.3.9-4.9-3.6-3.5 4.9-.7z' fill='%23ffd166' opacity='.6'/%3E%3Cpath d='M192 168l2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.2-4.1 5.8-.8z' fill='%2367e8a3' opacity='.55'/%3E%3C/g%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 220px 220px;
}

/* Container (identique app.py) */
.main .block-container {
  max-width: 1120px;
  padding-top: 0.6rem;
  padding-bottom: 2rem;
}

/* =========================
   1) MAIN : texte noir
   ⚠️ IMPORTANT: on NE force PAS les spans, sinon ça casse les lettres colorées
   ========================= */
section.main :is(h1,h2,h3,h4,h5,h6,p,label,li,small) {
  color: #111827 !important;
}
div[data-testid="stMetricLabel"] * { color:#111827 !important; }
div[data-testid="stMetricValue"] * { color:#111827 !important; }
div[data-testid="stCaptionContainer"] * { color:#1f2937 !important; }

/* =========================
   2) HERO titre multicolore (identique app.py)
   ========================= */
.sg-hero {
  margin: 10px 0 8px 0;
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
.sg-letter { display: inline-block; }

/* Couleurs EXACTES + !important (sinon écrasées) */
.sg-c1 { color: #ff4d6d !important; }
.sg-c2 { color: #ff7a59 !important; }
.sg-c3 { color: #ffd166 !important; }
.sg-c4 { color: #2dd4bf !important; }
.sg-c5 { color: #00b4ff !important; }
.sg-c6 { color: #3b82f6 !important; }
.sg-c7 { color: #7c4dff !important; }

.sg-page-title {
  text-align:center;
  font-family: ui-rounded, "SF Pro Rounded", "Avenir Next", system-ui;
  font-weight: 900;
  font-size: 28px;
  margin-top: 8px;
  margin-bottom: 6px;
  color: #111827 !important;
}

/* =========================
   3) SIDEBAR : même DA que app.py
   ========================= */
section[data-testid="stSidebar"] > div {
  background: #5db7ff;
}

/* Cacher UNIQUEMENT la nav multipage auto (app / Dashboard Parents) */
section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] {
  display: none !important;
}

/* Texte sidebar */
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
  color: #ffffff !important;
}

/* Labels rouges */
section[data-testid="stSidebar"] label {
  color: #ff1f4b !important;
  font-weight: 850 !important;
}

/* =========================
   4) Liens de nav (page_link) style boutons
   ========================= */
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

/* =========================
   5) Cards / KPI (comme app.py)
   ========================= */
.sg-card {
  background: rgba(255,255,255,0.94);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 18px;
  padding: 16px 16px;
  box-shadow: 0 10px 22px rgba(0,0,0,0.06);
  margin-bottom: 14px;
}
.sg-card-title {
  margin: 0 0 6px 0;
  font-weight: 950;
  font-size: 20px;
  color: #111827 !important;
}
.sg-card-sub {
  margin: 0 0 10px 0;
  color: #374151 !important;
  font-weight: 650;
}
.sg-list { margin: 0; padding-left: 18px; font-weight: 750; }
.sg-list li { margin: 6px 0; }

.sg-kpi {
  background: rgba(255,255,255,0.94);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 18px;
  padding: 14px 14px;
  box-shadow: 0 10px 22px rgba(0,0,0,0.06);
}
.sg-kpi-label { font-weight: 900; color:#111827 !important; opacity: 0.9; }
.sg-kpi-value { font-size: 40px; line-height: 1.05; font-weight: 950; margin-top: 8px; color:#111827 !important; }

/* =========================
   6) Selectbox rouge (comme bouton "Créer l’histoire")
   ========================= */
section.main div[data-baseweb="select"] > div {
  background: #ff1f4b !important;
  border: 0 !important;
  border-radius: 14px !important;
}
section.main div[data-baseweb="select"] * {
  color: #ffffff !important;
  font-weight: 850 !important;
}
ul[role="listbox"] {
  background: #ffffff !important;
  border-radius: 14px !important;
}
ul[role="listbox"] * {
  color: #111827 !important;
  font-weight: 700 !important;
}

/* =========================
   7) Choix : cartes internes
   ========================= */
.sg-choice {
  background:#ffffff;
  border:1px solid rgba(0,0,0,0.08);
  border-radius:14px;
  padding:12px;
  margin-top:10px;
  box-shadow: 0 8px 18px rgba(0,0,0,0.05);
}
.sg-choice-title { font-weight:900; color:#111827 !important; }
.sg-choice-meta { opacity:0.7; font-size:12px; margin-top:8px; color:#111827 !important; }

</style>
""",
    unsafe_allow_html=True,
)

# =========================
# Sidebar (uniquement ce que tu veux)
# =========================
with st.sidebar:
    st.markdown("### Navigation")
    st.page_link("app.py", label="Page principale", use_container_width=True)
    st.page_link("pages/2_Dashboard_Parents.py", label="Dashboard Parents", use_container_width=True)
    st.markdown("---")
    st.markdown("### Espace Parents")
    st.markdown("Suivez la progression : **vocabulaire**, **émotions**, **choix**, **régularité**.")

# =========================
# HERO
# =========================
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
  <div class="sg-subtitle">Suivi de la progression de l’enfant : mots, émotions, choix, et progression.</div>
</div>
<div class="sg-page-title">Dashboard Parents</div>
""",
    unsafe_allow_html=True,
)

# =========================
# Data
# =========================
data = load_progress()
children = data.get("children", {})

if not children:
    st.markdown(
        """
<div class="sg-card">
  <div class="sg-card-title">Données manquantes</div>
  <div class="sg-card-sub">Aucune donnée de progression pour l’instant. Génère une histoire et valide au moins un choix 🙂</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.stop()

# Select child
child_names = sorted(children.keys())
selected = st.selectbox("Choisir l’enfant", child_names)

child = children[selected]
profile = child.get("profile", {})

stories_count = child.get("stories_count", 0)
words_learned = child.get("words_learned", []) or []
emotions = child.get("emotions", []) or []
choices = child.get("choices", []) or []
themes = child.get("themes", []) or []
updated_at = child.get("updated_at", "—")

history = child.get("history", []) or []
themes_in_history = [h.get("theme") for h in history if h.get("theme")]
fav_theme = Counter(themes_in_history).most_common(1)[0][0] if themes_in_history else "—"

# KPI
k1, k2, k3, k4 = st.columns(4, gap="large")
k1.markdown(
    f"""
<div class="sg-kpi">
  <div class="sg-kpi-label">📚 Histoires générées</div>
  <div class="sg-kpi-value">{stories_count}</div>
</div>
""",
    unsafe_allow_html=True,
)
k2.markdown(
    f"""
<div class="sg-kpi">
  <div class="sg-kpi-label">🧠 Mots appris</div>
  <div class="sg-kpi-value">{len(words_learned)}</div>
</div>
""",
    unsafe_allow_html=True,
)
k3.markdown(
    f"""
<div class="sg-kpi">
  <div class="sg-kpi-label">😊 Émotions abordées</div>
  <div class="sg-kpi-value">{len(emotions)}</div>
</div>
""",
    unsafe_allow_html=True,
)
k4.markdown(
    f"""
<div class="sg-kpi">
  <div class="sg-kpi-label">🎯 Choix enregistrés</div>
  <div class="sg-kpi-value">{len(choices)}</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# Profil (1 cadre)
st.markdown(
    f"""
<div class="sg-card">
  <div class="sg-card-title">Profil de l’enfant</div>
  <div class="sg-card-sub">
    <b>Prénom :</b> {profile.get('name','-')} &nbsp;&nbsp;•&nbsp;&nbsp;
    <b>Âge :</b> {profile.get('age','-')} ans &nbsp;&nbsp;•&nbsp;&nbsp;
    <b>Niveau :</b> {profile.get('reading_level','-')} &nbsp;&nbsp;•&nbsp;&nbsp;
    <b>Objectif :</b> {profile.get('pedagogy_goal','-')}
    <br><br>
    <b>Dernière mise à jour :</b> {updated_at}
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# 2 colonnes
colA, colB = st.columns(2, gap="large")

with colA:
    # Vocabulaire : même cadre
    if words_learned:
        items = "".join([f"<li>{w}</li>" for w in words_learned])
        list_html = f"<ul class='sg-list'>{items}</ul>"
    else:
        list_html = "<div class='sg-card-sub'>—</div>"

    st.markdown(
        f"""
<div class="sg-card">
  <div class="sg-card-title">📚 Vocabulaire</div>
  <div class="sg-card-sub">Mots appris (liste cumulée)</div>
  {list_html}
</div>
""",
        unsafe_allow_html=True,
    )

    # Émotions : même cadre
    if emotions:
        items = "".join([f"<li>{e}</li>" for e in emotions])
        list_html = f"<ul class='sg-list'>{items}</ul>"
    else:
        list_html = "<div class='sg-card-sub'>—</div>"

    st.markdown(
        f"""
<div class="sg-card">
  <div class="sg-card-title">😊 Émotions</div>
  <div class="sg-card-sub">Émotions abordées dans les histoires</div>
  {list_html}
</div>
""",
        unsafe_allow_html=True,
    )

with colB:
    # Thèmes : même cadre
    if themes:
        items = "".join([f"<li>{t}</li>" for t in themes])
        list_html = f"<ul class='sg-list'>{items}</ul>"
    else:
        list_html = "<div class='sg-card-sub'>—</div>"

    st.markdown(
        f"""
<div class="sg-card">
  <div class="sg-card-title">🎯 Valeurs / thèmes</div>
  <div class="sg-card-sub">Thèmes pédagogiques vus avec l’enfant</div>
  {list_html}
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="sg-card">
  <div class="sg-card-title">✨ Tendance</div>
  <div class="sg-card-sub"><b>Valeur la plus fréquente :</b> {fav_theme}</div>
</div>
""",
        unsafe_allow_html=True,
    )

# Choix : 1 seul cadre
choices_rev = list(reversed(choices)) if choices else []

if not choices_rev:
    st.markdown(
        """
<div class="sg-card">
  <div class="sg-card-title">🧭 Choix de l’enfant</div>
  <div class="sg-card-sub">Aucun choix validé pour le moment.</div>
</div>
""",
        unsafe_allow_html=True,
    )
else:
    inner = ""
    for ch in choices_rev[:20]:
        inner += f"""
        <div class="sg-choice">
          <div class="sg-choice-title">Scène {ch.get('scene_no')}</div>
          <div style="margin-top:6px;"><b>Question :</b> {ch.get('question')}</div>
          <div style="margin-top:6px;"><b>Choix :</b> {ch.get('choice')}</div>
          <div class="sg-choice-meta">{ch.get('created_at')}</div>
        </div>
        """

    st.markdown(
        f"""
<div class="sg-card">
  <div class="sg-card-title">🧭 Choix de l’enfant</div>
  <div class="sg-card-sub">Historique des décisions (les plus récents en premier)</div>
  {inner}
</div>
""",
        unsafe_allow_html=True,
    )

# Historique histoires
with st.expander("📖 Historique des histoires"):
    history_rev = list(reversed(history)) if history else []
    if not history_rev:
        st.write("Aucun historique.")
    else:
        for h in history_rev[:20]:
            st.write(
                f"• **{h.get('title')}** — {h.get('created_at')} "
                f"(groupe {h.get('age_group')}, émotion {h.get('emotion')}, valeur {h.get('theme')})"
            )