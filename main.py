import streamlit as st
import time
import subprocess
import pandas as pd
from core.llm import get_llm
from core.config import GRID_SIZE, LOCATIONS, STARTING_GOLD, ITEMS_PRICES
from core import storage
from plugins import villagers, relations, buildings, weather, economy

# --- INITIALISATION ---
st.set_page_config(page_title="MyVillage AI 5.1", layout="wide")

if 'llm' not in st.session_state:
    st.session_state.llm = get_llm()

# --- ETAT SESSION ---
def init_villagers():
    return {
        "Elora": {"role": "Apothicaire", "pos": [0, 4], "home": [0, 4], "energy": 100, "rel": {}, "gold": STARTING_GOLD, "inventory": []},
        "Kael": {"role": "Forgeron", "pos": [1, 0], "home": [1, 0], "energy": 100, "rel": {}, "gold": STARTING_GOLD, "inventory": []},
        "Lila": {"role": "Aubergiste", "pos": [4, 3], "home": [4, 3], "energy": 100, "rel": {}, "gold": STARTING_GOLD, "inventory": []}
    }

# Chargers ou initialiser
current_state = storage.load_world()
if current_state:
    st.session_state.villagers = current_state.get('villagers', init_villagers())
    st.session_state.world_time = current_state.get('world_time', 8)
    st.session_state.logs = current_state.get('logs', [])
    st.session_state.weather = current_state.get('weather', "Ensoleillé")
else:
    if 'villagers' not in st.session_state:
        st.session_state.villagers = init_villagers()
    if 'world_time' not in st.session_state:
        st.session_state.world_time = 8
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'weather' not in st.session_state:
        st.session_state.weather = "Ensoleillé"

# --- MOTEUR DE JEU ---
def run_simulation_step():
    st.session_state.world_time = (st.session_state.world_time + 1) % 24
    st.session_state.weather = weather.update_weather(st.session_state.weather)
    
    current_time = st.session_state.world_time
    # Logs temporaires pour ce tour
    step_logs = []

    for name in st.session_state.villagers:
        v = st.session_state.villagers[name]
        
        # 1. Décision IA
        decision = villagers.agent_turn(
            st.session_state.llm, 
            name, 
            st.session_state.villagers, 
            current_time,
            st.session_state.weather
        )
        
        # 2. Application
        v['pos'] = decision['dest']
        # Limites et énergie
        v['energy'] = buildings.update_energy(v, decision['action'])
        
        # 3. Économie & Actions spéciales
        action_msg = ""
        if decision['action'] == "CRAFT" and decision.get('objet'):
            ok, msg = economy.craft_item(v, decision['objet'])
            action_msg = f" | 🛠️ {msg}"
        
        elif decision['action'] == "ACHETER" and decision.get('cible') and decision.get('objet'):
            target_name = decision['cible']
            if target_name in st.session_state.villagers:
                seller = st.session_state.villagers[target_name]
                # Vérif distance (doivent être au même endroit)
                if v['pos'] == seller['pos']:
                    ok, msg = economy.transaction(v, seller, decision['objet'], target_name)
                    action_msg = f" | 💰 {msg}"
                else:
                    action_msg = f" | ❌ Trop loin de {target_name} pour acheter."
        
        # 4. Relations
        if decision['reaction']:
           relations.update_relations(v, decision['reaction'])
        
        # Log
        log_entry = f"{current_time}h - **{name}** : {decision['pensee']} [Action: {decision['action']}{action_msg}]"
        step_logs.append(log_entry)

    # Mise à jour des logs globaux (inversé pour avoir le plus récent en haut)
    st.session_state.logs = step_logs + st.session_state.logs[:50]
    
    # Save
    storage.save_world(st.session_state.villagers, st.session_state.world_time, st.session_state.logs, st.session_state.weather)

# --- UI ---
st.title(f"🏘️ MyVillage AI 5.1 - {st.session_state.weather}")

# Sidebar : Stats
with st.sidebar:
    st.header(f"⏰ Heure: {st.session_state.world_time}:00")
    
    # Bouton Auto-Run
    auto_run = st.checkbox("🔄 Mode Automatique", key="auto_run")
    
    st.subheader("Villageois")
    for name, v in st.session_state.villagers.items():
        loc_name = buildings.get_location_name(v['pos'])
        st.markdown(f"**{name}** ({v['role']})")
        st.write(f"📍 {loc_name} {v['pos']}")
        st.progress(v['energy']/100, text=f"Énergie: {v['energy']}%")
        st.write(f"💰 {v.get('gold', 0)} Or | 🎒 {v.get('inventory', [])}")
        
    st.subheader("Relations")
    for name, v in st.session_state.villagers.items():
        rel_str = ", ".join([f"{k}: {val}" for k, val in v.get('rel', {}).items()])
        st.caption(f"{name}: {rel_str}")

# Main : Carte
col_map, col_logs = st.columns([2, 1])

with col_map:
    # Grille simple
    grid_data = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    
    # Marquer les lieux
    for loc_name, coords in LOCATIONS.items():
        x, y = coords
        grid_data[y][x] = f"📍 {loc_name}"
        
    # Marquer les villageois
    for name, v in st.session_state.villagers.items():
        x, y = v['pos'] # [x, y]
        # Attention indices : grid[y][x]
        current_content = grid_data[y][x]
        grid_data[y][x] = f"{current_content}\n👤 {name}"
        
    df_grid = pd.DataFrame(grid_data)
    st.table(df_grid)

with col_logs:
    st.subheader("Journal")
    for log in st.session_state.logs:
        st.write(log)


# Auto-Run Logic (at usage end)
if auto_run:
    time.sleep(2)
    run_simulation_step()
    st.rerun()

# Bouton manuel
if st.button("Avancer (+1h)"):
    run_simulation_step()
    st.rerun()