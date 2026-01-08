import streamlit as st
import time
import json
import pandas as pd
from core.llm import get_llm
from core import storage
from plugins import villagers, relations, buildings, weather, economy, storybook

# --- CHARGEMENT CONFIG (SEED) ---
try:
    with open("world_seed.json", "r", encoding='utf-8') as f:
        SEED = json.load(f)
except FileNotFoundError:
    st.error("world_seed.json introuvable !")
    st.stop()

GRID_SIZE = SEED['grid_size']

# --- INITIALISATION ---
st.set_page_config(page_title=SEED['scenario_name'], layout="wide")

if 'llm' not in st.session_state:
    st.session_state.llm = get_llm()

# --- ETAT SESSION ---
def init_from_seed():
    """Charge l'état initial depuis le seed JSON."""
    return SEED['characters']

# Chargement
current_state = storage.load_world()
if current_state:
    st.session_state.villagers = current_state.get('villagers', init_from_seed())
    st.session_state.world_time = current_state.get('world_time', 8)
    st.session_state.logs = current_state.get('logs', [])
    # Reset si le fichier de sauvegarde ne correspond pas aux nouveaux persos
    first_char = list(st.session_state.villagers.keys())[0]
    if first_char not in SEED['characters']:
        st.warning("Ancienne sauvegarde incompatible détectée. Réinitialisation...")
        st.session_state.villagers = init_from_seed()
    
    st.session_state.weather = current_state.get('weather', "Ensoleillé")
else:
    if 'villagers' not in st.session_state:
        st.session_state.villagers = init_from_seed()
    if 'world_time' not in st.session_state:
        st.session_state.world_time = 8
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'weather' not in st.session_state:
        st.session_state.weather = "Ensoleillé"

# --- HELPER MAP ---
def get_terrain_at(x, y):
    if 0 <= y < GRID_SIZE and 0 <= x < GRID_SIZE:
        char = SEED['map_layout'][y][x]
        return SEED['map_legend'].get(char, "Inconnu")
    return "Océan"

# --- MOTEUR DE JEU ---
def run_simulation_step(placeholder=None):
    st.session_state.world_time = (st.session_state.world_time + 1) % 24
    st.session_state.weather = weather.update_weather(st.session_state.weather)
    
    current_time = st.session_state.world_time
    
    # Storybook Trigger (Minuit)
    if current_time == 0:
        day_num = len(st.session_state.logs) // 50 + 1 # Approx du jour
        with st.spinner("Génération du Chapitre BD..."):
            msg = storybook.generate_chapter(day_num, st.session_state.logs, st.session_state.villagers)
            st.toast(msg, icon="📚")
            st.session_state.logs.append(f"📚 **STORYBOOK** : {msg}")
    step_logs = []

    for name in st.session_state.villagers:
        v = st.session_state.villagers[name]
        
        # Contexte Terrain
        x, y = v['pos']
        terrain = get_terrain_at(x, y)
        
        # 1. Décision IA
        decision = villagers.agent_turn(
            st.session_state.llm, 
            name, 
            st.session_state.villagers, 
            current_time,
            st.session_state.weather,
            SEED,
            terrain
        )
        
        # 2. Application Mouvement
        # Vérif bornes via déplacement unitaire
        dest_x, dest_y = decision['dest']
        curr_x, curr_y = v['pos']
        
        move_x = max(-1, min(1, dest_x - curr_x))
        move_y = max(-1, min(1, dest_y - curr_y))
        
        new_x = curr_x + move_x
        new_y = curr_y + move_y
        
        new_x = max(0, min(GRID_SIZE-1, new_x))
        new_y = max(0, min(GRID_SIZE-1, new_y))
        
        v['pos'] = [new_x, new_y]
        
        # Energie
        v['energy'] = max(0, v['energy'] - 5)
        if decision['action'] == "DORMIR":
             v['energy'] = min(100, v['energy'] + 15)
        
        # 3. Actions Spéciales (Fouille)
        action_msg = ""
        if decision['action'] == "FOUILLER" and "?" in SEED['map_layout'][new_y][new_x]:
             import random
             if random.random() < 0.3: # 30% chance
                 item = random.choice(SEED['loot_table'])
                 v['inventory'].append(item)
                 action_msg = f" | 🎁 Trouvé : {item} !"
             else:
                 action_msg = f" | Rien trouvé..."

        # 4. Relations
        if decision['reaction']:
           relations.update_relationships(v, decision)
        
        # Log Enrichi (Lore + Stats)
        # Log Enrichi (Lore + Stats)
        stats_str = f"[🔋{v['energy']}% | 📍{v['pos']} | 🎒{len(v.get('inventory', []))}]"
        log_entry = f"**{current_time}h - {name}** {stats_str}\n\n*{decision['pensee']}*\n\n> 🔧 {decision['action']} {action_msg}"
        step_logs.append(log_entry)
        
    # --- MEMOIRE INTELLIGENTE (Extraction AI) ---
    if 'key_facts' not in st.session_state:
        st.session_state.key_facts = []

    # On demande à Llama d'analyser ce tour pour trouver des faits marquants
    if step_logs:
        new_facts = storybook.extract_facts_ai("\n".join(step_logs))
        for fact in new_facts:
            # On ajoute le timestamp pour le différencier
            timestamped_fact = f"Jour {st.session_state.world_time//24 + 1} {current_time}h: {fact}"
            st.session_state.key_facts.append(timestamped_fact)

    # --- NARRATEUR GEMINI (Temps Réel & Streaming) ---
    # Init Story Log
    if 'story_log' not in st.session_state:
        st.session_state.story_log = []

    # --- NARRATEUR GEMINI (Streaming History) ---
    if step_logs:
        narrative_text = ""
        # Si un placeholder est fourni, on stream dedans
        if placeholder:
             placeholder.markdown('<div class="story-block current-writing">✍️ <i>L\'histoire s\'écrit...</i></div>', unsafe_allow_html=True)
        
        # Récupération du contexte précédent (3 derniers blocs) pour éviter répétitions
        prev_history = "\n".join(st.session_state.story_log[:3])
        # Récupération des faits marquants (Les 10 derniers)
        facts_memory = "\n".join(st.session_state.get('key_facts', [])[-10:])
        
        stream_gen = storybook.narrate_turn_stream(step_logs, prev_history, facts_memory)
        
        for chunk in stream_gen:
             if chunk:
                 narrative_text += chunk
                 if placeholder:
                     # On affiche le texte en cours de génération avec le style CSS
                     placeholder.markdown(f'<div class="story-block current-writing">### 🕐 {current_time}h00<br><br>{narrative_text} ▌</div>', unsafe_allow_html=True)
        
        if narrative_text:
            story_block = f"### 🕐 {current_time}h00\n\n{narrative_text}"
            st.session_state.story_log.insert(0, story_block)
            if placeholder:
                placeholder.empty() # On nettoie car ça va être ajouté aux logs permanents

    # Historique Global (Lore caché pour contexte modèles)
    st.session_state.logs = step_logs + st.session_state.logs
    
    if len(st.session_state.logs) > 500:
        st.session_state.logs = st.session_state.logs[:500] 
        
    storage.save_world(st.session_state.villagers, st.session_state.world_time, st.session_state.logs, st.session_state.weather)

# --- UI (Glassmorphism & New Layout) ---
# CSS Injection
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    :root {
      --glass-bg: rgba(255, 255, 255, 0.08);
      --glass-border: rgba(255, 255, 255, 0.15);
      --accent-color: #00f2ff;
      --text-color: #e0e0e0;
    }

    /* Override Streamlit Base */
    .stApp {
        background: radial-gradient(circle at center, #1a2a3a 0%, #0a0f14 100%);
        font-family: 'Inter', sans-serif;
        color: var(--text-color);
    }
    
    /* Hide Streamlit Elements */
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    #MainMenu {visibility: hidden;}
    
    /* Custom App Container (Virtual) */
    .app-container {
        border: 1px solid var(--glass-border);
        border-radius: 24px;
        backdrop-filter: blur(20px);
        background: var(--glass-bg);
        padding: 20px;
        margin-top: -50px; /* Pull up to hide whitespace */
    }

    /* Header & Avatars */
    .ui-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--glass-border);
      margin-bottom: 20px;
    }
    
    .scenario-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: var(--accent-color);
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    .character-group {
      display: flex;
      gap: 15px;
    }

    .avatar-box {
      position: relative;
      cursor: pointer;
    }

    .avatar {
      width: 50px;
      height: 50px;
      border-radius: 50%;
      border: 2px solid transparent;
      padding: 2px;
      transition: all 0.3s ease;
      filter: grayscale(0.8);
      object-fit: cover;
      background: #222;
    }

    .avatar:hover, .avatar.active {
      border-color: var(--accent-color);
      filter: grayscale(0);
      box-shadow: 0 0 15px var(--accent-color);
    }
    
    .avatar-badge {
        position: absolute;
        bottom: -5px;
        right: -5px;
        background: #000;
        color: white;
        font-size: 0.7rem;
        padding: 2px 5px;
        border-radius: 4px;
        border: 1px solid #444;
    }

    /* Map Panel */
    .map-placeholder {
      background: rgba(0,0,0,0.3);
      border-radius: 16px;
      border: 1px solid var(--glass-border);
      padding: 10px;
      box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
    }

    /* Grid Styling inside Map */
    .map-grid {
        display: grid;
        grid-template-columns: repeat(32, 1fr);
        gap: 1px;
        aspect-ratio: 1/1;
        width: 100%;
    }
    
    .map-cell {
        position: relative;
        width: 100%;
        height: 100%;
    }
    
    .char-marker {
        font-size: 1.4cqw; 
        filter: drop-shadow(0 0 4px var(--accent-color));
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }

    /* Story Panel */
    .story-panel {
      background: rgba(0, 0, 0, 0.2);
      border-radius: 16px;
      padding: 25px;
      height: 600px;
      overflow-y: auto;
      border: 1px solid var(--glass-border);
    }
    
    .story-content {
        font-family: 'Georgia', serif;
        line-height: 1.8;
        font-size: 1.1rem;
        color: #ddd;
    }
    
    .story-block {
        margin-bottom: 25px;
        padding-left: 15px;
        border-left: 2px solid #444;
        animation: fadeIn 1s ease-in;
    }
    
    .current-writing {
        border-left: 3px solid var(--accent-color);
        background: linear-gradient(90deg, rgba(0,242,255,0.05) 0%, transparent 100%);
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    /* Bouton Custom (Hack Streamlit) */
    div[data-testid="stButton"] button {
        background: var(--glass-bg);
        border: 1px solid var(--accent-color);
        color: var(--accent-color);
        width: 100%;
        border-radius: 12px;
        font-size: 18px;
        transition: 0.3s;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    div[data-testid="stButton"] button:hover {
        background: var(--accent-color);
        color: #000;
        box-shadow: 0 0 20px var(--accent-color);
        border-color: var(--accent-color);
    }

</style>
""", unsafe_allow_html=True)

# --- HEADER (HTML Injection) ---
# Génération dynamique des avatars
avatars_html = ""
for name, v in st.session_state.villagers.items():
    # Placeholder icons based on role
    icon_url = "https://cdn-icons-png.flaticon.com/512/4140/4140048.png" # Default
    if "John" in name: icon_url = "https://cdn-icons-png.flaticon.com/512/4140/4140037.png"
    if "Barbie" in name: icon_url = "https://cdn-icons-png.flaticon.com/512/4140/4140047.png"
    
    avatars_html += f"""
    <div class="avatar-box" title="{name} | 🔋{v['energy']}%">
      <img src="{icon_url}" class="avatar active">
      <div class="avatar-badge">{v['energy']}%</div>
    </div>
    """

header_html = f"""
<div class="ui-header">
    <div class="scenario-title">{SEED['scenario_name']} <span style="font-size:0.8rem; opacity:0.6">| Jour {st.session_state.world_time // 24 + 1} - {st.session_state.world_time}h00</span></div>
    <div class="character-group">
      {avatars_html}
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)


# --- MAIN LAYOUT ---
col1, col2 = st.columns([1, 1])

with col1:
    # MAP PANEL
    st.markdown('<div class="map-placeholder">', unsafe_allow_html=True)
    
    # Map Generation (Pure HTML Grid)
    grid_html = '<div class="map-grid">'
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            char_terrain = SEED['map_layout'][y][x]
            color = SEED['map_colors'].get(char_terrain, "#111")
            
            # Contenu
            content = ""
            for p_name, p_data in st.session_state.villagers.items():
                if p_data['pos'] == [x, y]:
                    avatar = "👱‍♀️" if "Barbie" in p_name else "👮‍♂️" if "John" in p_name else "👨‍🔬"
                    content = f'<div class="char-marker">{avatar}</div>'
            
            if not content:
                if char_terrain == "?": content = "📦"
                if char_terrain == "A": content = "✈️"
                
            grid_html += f'<div class="map-cell" style="background-color: {color}; display:flex; align-items:center; justify-content:center;">{content}</div>'
            
    grid_html += '</div>' # End Grid
    st.markdown(grid_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True) # End Placeholder

    # CONTROLS
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("▶ CONTINUER"):
             # On vide le placeholder précédent pour le clean slate
             narrative_spot = col2.empty()
             run_simulation_step(narrative_spot)
             st.rerun()
    with c2:
        st.markdown(f"*Météo: {st.session_state.weather}*")

with col2:
    # STORY PANEL
    st.markdown('<div class="story-panel"><div class="story-content">', unsafe_allow_html=True)
    
    # Placeholder for streaming (inserted via main function logic, targeting this column?)
    # Streamlit execution order means we need the placeholder here.
    story_placeholder = st.empty()
    
    # Render History
    if 'story_log' in st.session_state:
        for block in st.session_state.story_log:
            # Clean markdown for HTML class
            clean_block = block.replace("### ", "").replace("\n", "<br>")
            st.markdown(f'<div class="story-block">{clean_block}</div>', unsafe_allow_html=True)
            
    st.markdown('</div></div>', unsafe_allow_html=True)

# Auto Run Logic (Hidden but functional)
# The 'auto_run' checkbox was removed from the UI.
# If auto-run functionality is still desired, it needs to be re-implemented
# (e.g., via a hidden session state variable or a different trigger).
# For now, this block is effectively disabled as 'auto_run' is not set by a UI element.
# if auto_run:
#     time.sleep(2)
#     run_simulation_step(story_placeholder)
#     st.rerun()