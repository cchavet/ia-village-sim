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
        stats_str = f"[🔋{v['energy']}% | 📍{v['pos']} | 🎒{len(v.get('inventory', []))}]"
        log_entry = f"**{current_time}h - {name}** {stats_str}\n\n*{decision['pensee']}*\n\n> 🔧 {decision['action']} {action_msg}"
        step_logs.append(log_entry)

    # --- NARRATEUR GEMINI (Temps Réel & Streaming) ---
    if step_logs:
        narrative_text = ""
        # Si un placeholder est fourni (Mode streaming)
        if placeholder:
            placeholder.markdown(f"✍️ *Le narrateur observe...*")
            
        stream_gen = storybook.narrate_turn_stream(step_logs)
        
        for chunk in stream_gen:
             if chunk:
                 narrative_text += chunk
                 if placeholder:
                     placeholder.markdown(f"📖 **CHRONIQUE ({current_time}h)**\n\n{narrative_text} ▌")
        
        if narrative_text:
            narrative_block = f"📖 **CHRONIQUE ({current_time}h)**\n\n{narrative_text}\n\n---"
            step_logs.insert(0, narrative_block)
            if placeholder:
                placeholder.empty() # On nettoie car ça va être ajouté aux logs permanents

    # Historique Global (Lore)
    st.session_state.logs = step_logs + st.session_state.logs
    
    # Limite de sécurité plus large (ex: 500) pour éviter le lag UI, 
    # mais on pourrait sauver l'historique complet dans un fichier à part si besoin.
    if len(st.session_state.logs) > 500:
        st.session_state.logs = st.session_state.logs[:500] 
        
    storage.save_world(st.session_state.villagers, st.session_state.world_time, st.session_state.logs, st.session_state.weather)

# --- UI ---
st.title(f"🏝️ {SEED['scenario_name']} - {st.session_state.weather}")
st.caption(SEED['description'])

with st.sidebar:
    st.header(f"⏰ Jour {st.session_state.world_time // 24 + 1} - {st.session_state.world_time}h")
    auto_run = st.checkbox("🔄 Mode Automatique", key="auto_run")
    
    st.subheader("Survivants")
    for name, v in st.session_state.villagers.items():
        x, y = v['pos']
        terrain = get_terrain_at(x, y)
        st.markdown(f"**{name}** ({v['role']})")
        st.write(f"📍 {terrain} [{x}, {y}]")
        st.progress(v['energy']/100, text=f"Énergie: {v['energy']}%")
        st.write(f"🎒 {v.get('inventory', [])}")
        st.divider()

col_map, col_logs = st.columns([2, 1])

with col_map:
    # Rendu Map (Custom HTML pour style Pixel Art 32x32)
    style = """
    <style>
        .map-container {
            display: grid;
            grid-template-columns: repeat(32, 1fr);
            gap: 0px;
            width: 100%;
            max-width: 800px;
            aspect-ratio: 1/1;
            background-color: #1E90FF;
            border: 2px solid #333;
        }
        .map-cell {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px; /* Ajuster selon taille écran */
            overflow: visible;
            position: relative;
        }
        .char-marker {
            position: absolute;
            z-index: 10;
            font-size: 14px;
            text-shadow: 0px 0px 2px white;
        }
        .tooltip {
            visibility: hidden;
            background-color: black;
            color: #fff;
            text-align: center;
            padding: 2px 0;
            border-radius: 6px;
            position: absolute;
            z-index: 20;
            top: -20px;
            left: 50%;
            margin-left: -30px;
            width: 60px;
            font-size: 9px;
        }
        .map-cell:hover .tooltip {
            visibility: visible;
        }
    </style>
    """
    
    html = '<div class="map-container">'
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            char_terrain = SEED['map_layout'][y][x]
            color = SEED['map_colors'].get(char_terrain, "#000000")
            
            # Contenu (Personnage ou Débris)
            content = ""
            tooltip = ""

            # Check Personnages
            for p_name, p_data in st.session_state.villagers.items():
                if p_data['pos'] == [x, y]:
                    # Avatar simple basé sur la première lettre ou rôle
                    avatar = "👱‍♀️" if p_name == "Barbie" else "👮‍♂️" if p_name == "John" else "👨‍🔬"
                    content += f'<span class="char-marker" title="{p_name}">{avatar}</span>'
                    tooltip = p_name
            
            # Check Débris (si pas de perso)
            if not content and char_terrain == "?":
                content = "📦"
            if not content and char_terrain == "A":
                content = "✈️"

            # Cellule
            cell_html = f'<div class="map-cell" style="background-color: {color};">'
            if content:
                cell_html += content
            if tooltip:
                 cell_html += f'<span class="tooltip">{tooltip}</span>'
            cell_html += '</div>'
            
            html += cell_html
            
    html += '</div>'
    st.markdown(style + html, unsafe_allow_html=True)
    st.caption("Légende: ✈️Crash 📦Débris | 👱‍♀️Barbie 👮‍♂️John 👨‍🔬Ken")

with col_logs:
    st.subheader("Journal de Bord")
    for log in st.session_state.logs:
        st.write(log)

if auto_run:
    time.sleep(2)
    narrative_spot = col_logs.empty()
    run_simulation_step(narrative_spot)
    st.rerun()

if st.button("Tour Suivant"):
    narrative_spot = col_logs.empty()
    run_simulation_step(narrative_spot)
    st.rerun()