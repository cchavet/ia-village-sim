import streamlit as st
import time
import pandas as pd
from core.config import GRID_SIZE, MAP_LOCATIONS
from core.llm import get_llm
from core import storage
from plugins import villagers, relations, buildings, weather

# --- CONFIGURATION ---
st.set_page_config(page_title="IA Village Life Cycle", layout="wide")

# --- INITIALISATION ---
if 'llm' not in st.session_state:
    st.session_state.llm = get_llm()

if 'villagers' not in st.session_state:
    # Tentative de chargement
    saved_state = storage.load_world()
    
    if saved_state:
        st.session_state.villagers = saved_state['villagers']
        st.session_state.world_time = saved_state['world_time']
        st.session_state.logs = saved_state['logs']
        if 'weather' in saved_state:
            st.session_state.weather = saved_state['weather']
    else:
        # Valeurs par défaut
        st.session_state.villagers = {
            "Elora": {"role": "Apothicaire", "pos": [0, 4], "home": [0, 4], "energy": 100, "rel": {"Kael": 0, "Lila": 10}},
            "Kael": {"role": "Forgeron", "pos": [0, 0], "home": [1, 0], "energy": 100, "rel": {"Elora": 0, "Lila": -5}},
            "Lila": {"role": "Aubergiste", "pos": [4, 4], "home": [4, 3], "energy": 100, "rel": {"Elora": 20, "Kael": 0}}
        }
        st.session_state.world_time = 8
        st.session_state.logs = []

if 'world_time' not in st.session_state:
    st.session_state.world_time = 8
if 'logs' not in st.session_state:
    st.session_state.logs = []

# --- ORCHESTRATION ---
def run_simulation_step():
    st.session_state.world_time = (st.session_state.world_time + 1) % 24
    current_weather = weather.update_weather()
    
    for name in st.session_state.villagers:
        # Décision de l'agent (Plugin Villagers)
        decision = villagers.agent_turn(
            st.session_state.llm, 
            name, 
            st.session_state.villagers, 
            st.session_state.world_time,
            current_weather
        )
        
        v = st.session_state.villagers[name]
        
        # Mise à jour de la position et de l'énergie (Plugin Buildings)
        v['pos'] = decision['dest']
        v['energy'] = buildings.update_energy(v, decision['action'])

        # Gestion des relations (Plugin Relations)
        v = relations.update_relationships(v, decision)
        
        # Logging
        st.session_state.logs.insert(0, f"{st.session_state.world_time}h - **{name}** : {decision['pensee']}")
    
    # Sauvegarde automatique
    storage.save_world(
        st.session_state.villagers, 
        st.session_state.world_time, 
        st.session_state.logs,
        st.session_state.get('weather', "Ensoleillé ☀️")
    )

# --- INTERFACE ---
st.title("🌙 Village IA : Cycle de Vie")

# Sidebar
with st.sidebar:
    st.header(f"⏰ {st.session_state.world_time}:00")
    st.info(f"Météo: {weather.get_current_weather()}")
    
    if st.session_state.world_time >= 22 or st.session_state.world_time <= 6:
        st.warning("🌙 Il fait nuit...")
    else:
        st.success("☀️ Il fait jour")
    
    if st.button("⏭️ Passer à l'heure suivante", use_container_width=True):
        run_simulation_step()
        st.rerun()

    auto_run = st.checkbox("🔄 Mode Automatique")

    st.markdown("---")
    st.subheader("Relations")
    for name, data in st.session_state.villagers.items():
        with st.expander(f"Relations de {name}"):
            for target, score in data['rel'].items():
                icon = "❤️" if score > 50 else "💔" if score < -20 else "😐"
                st.write(f"{icon} {target}: {score}")

# Affichage de la carte
grid = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
for (x, y), label in MAP_LOCATIONS.items(): grid[y][x] = f"📍{label}"
for name, data in st.session_state.villagers.items():
    x, y = data['pos']
    grid[y][x] += f" \n 👤{name} ({data['energy']}⚡)"

st.table(pd.DataFrame(grid))

st.subheader("📜 Journal de vie")
for log in st.session_state.logs[:8]:
    st.write(log)

# --- AUTO RUN ---
if 'auto_run' in locals() and auto_run:
    time.sleep(1)
    run_simulation_step()
    st.rerun()