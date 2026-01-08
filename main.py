import streamlit as st
import json
from core.llm import get_llm
from core import storage, ui, engine as game_engine

# --- CONFIG ---
try:
    with open("world_seed.json", "r", encoding='utf-8') as f:
        SEED = json.load(f)
except FileNotFoundError:
    st.error("world_seed.json introuvable !")
    st.stop()

# --- INITIALISATION ---
st.set_page_config(page_title=SEED['scenario_name'], layout="wide")

if 'llm' not in st.session_state:
    st.session_state.llm = get_llm()

# --- ETAT SESSION & CHARGEMENT ---
def init_state():
    current_state = storage.load_world()
    if current_state:
        st.session_state.villagers = current_state.get('villagers', SEED['characters'])
        st.session_state.world_time = current_state.get('world_time', 8)
        st.session_state.logs = current_state.get('logs', [])
        st.session_state.weather = current_state.get('weather', "Ensoleillé")
        st.session_state.story_log = current_state.get('story_log', []) 
    else:
        st.session_state.villagers = SEED['characters']
        st.session_state.world_time = 8
        st.session_state.logs = []
        st.session_state.weather = "Ensoleillé"
        st.session_state.story_log = []

    if 'page_index' not in st.session_state:
        st.session_state.page_index = 0

if 'villagers' not in st.session_state:
    init_state()

# --- MOTEUR ---
engine = game_engine.SimulationEngine(SEED)

# --- RENDU UI ---
ui.inject_css()

# Header
ui.render_header(SEED['scenario_name'], st.session_state.world_time, st.session_state.villagers)

# Layout
col1, col2 = st.columns([1, 1])

with col1:
    # Map
    ui.render_map(SEED['grid_size'], SEED['map_layout'], SEED['map_colors'], st.session_state.villagers)
    
    # Controls
    st.markdown("<br>", unsafe_allow_html=True)
    c_prev, c_stat, c_next = st.columns([1, 2, 1])
    
    with c_prev:
        if st.button("⏪ RETOUR"):
            if st.session_state.page_index > 0:
                st.session_state.page_index -= 1
                st.rerun()
                
    with c_next:
        total_pages = len(st.session_state.get('story_log', []))
        is_latest = total_pages == 0 or st.session_state.page_index >= total_pages - 1
            
        btn_label = "SUIVANT ⏩"
        
        # Si on est à la fin, le bouton sert à tourner la page vers la "Page suivante" (Buffer ou Generation)
        if is_latest:
            if 'pending_page' in st.session_state and st.session_state.pending_page:
                 btn_label = "LIRE LA SUITE ✨"
            else:
                 btn_label = "GÉNÉRER ⏳"
        
        if st.button(btn_label):
            if is_latest:
                # 1. Si une page est prête en buffer, on l'affiche direct
                if 'pending_page' in st.session_state and st.session_state.pending_page:
                    st.session_state.story_log.append(st.session_state.pending_page)
                    st.session_state.pending_page = None
                    st.session_state.page_index = len(st.session_state.story_log) - 1
                    # TRIGGER PRELOAD N+1
                    st.session_state.trigger_preload = True
                    st.rerun()
                
                # 2. Sinon, on génère (cas "Générer")
                else:
                    with col2:
                        ui.render_loader()
                        stream_spot = st.empty()
                    
                    # On génère une page complète
                    page_text = engine.generate_page_content(stream_spot)
                    
                    if page_text:
                        st.session_state.story_log.append(page_text)
                        # TRIGGER PRELOAD N+1
                        st.session_state.trigger_preload = True
                        
                    st.session_state.page_index = len(st.session_state.story_log) - 1
                    st.rerun()
            else:
                # Navigation normale
                st.session_state.page_index += 1
                st.rerun()
                
    with c_stat:
         st.markdown(f"<div style='text-align:center; padding-top:10px;'>Météo: {st.session_state.weather}</div>", unsafe_allow_html=True)

with col2:
    # Story Book
    total_pages = len(st.session_state.get('story_log', []))
    
    if st.session_state.page_index >= total_pages and total_pages > 0:
        st.session_state.page_index = total_pages - 1
        
    current_content = ""
    if total_pages > 0:
        current_content = st.session_state.story_log[st.session_state.page_index]
        
    ui.render_story_page(current_content, st.session_state.page_index + 1, total_pages)

# --- PRE-LOADING (Background Generation) ---
# Si on est à la dernière page affichée et qu'il n'y a pas de pending_page, on lance la génération de la suivante
# Astuce: On le fait UNIQUEMENT si on ne vient pas de générer (pour ne pas boucler infini si erreur)
# Pour l'instant, faisons simple : Button "Générer" explicite si pas de buffer.
# Pour le vrai "Pre-load", il faudrait un thread ou un callback async, difficile avec Streamlit pur sans bloquer l'UI.
# Alternative : On génère la page suivante APRES avoir affiché la courante, bloquant l'UI un moment ? Non.
# On va laisser le bouton "Générer" pour l'instant, ou utiliser st.spinner() en fin de script mais ça bloquerait l'interaction.
# Le User veut "toujours générer une page complète d'avance".
# Le mieux : Quand on clique sur SUIVANT et qu'on affiche la page N, on lance illico la gen de N+1.
if 'trigger_preload' in st.session_state and st.session_state.trigger_preload:
    st.session_state.trigger_preload = False
    with st.spinner("Préparation de la page suivante..."):
         # On génère sans streamer (background)
         next_page = engine.generate_page_content(None)
         st.session_state.pending_page = next_page
         st.rerun()

# Logic Trigger pour le preload
if is_latest and ('pending_page' not in st.session_state or not st.session_state.pending_page):
    # On est à la fin et rien de prêt.
    # On ne peut pas auto-run car ça bloquerait la lecture de la page actuelle.
    # On affiche juste un indicateur ou on laisse le bouton "Générer".
    pass 
else:
    pass