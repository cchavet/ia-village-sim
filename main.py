import streamlit as st
from langchain_community.llms import Ollama
import json
import random
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="IA Village Life Cycle", layout="wide")
llm = Ollama(model="llama3.2:1b", temperature=0.7)

# --- CONSTANTES ---
GRID_SIZE = 5
MAP_LOCATIONS = {
    (0, 0): "La Forge", (4, 4): "L'Auberge", (2, 2): "La Place",
    (0, 4): "L'Apothicaire", (4, 0): "La Forêt"
}

# --- INITIALISATION ---
if 'villagers' not in st.session_state:
    st.session_state.villagers = {
        "Elora": {"role": "Apothicaire", "pos": [0, 4], "home": [0, 4], "energy": 100, "rel": {"Kael": 0, "Lila": 10}},
        "Kael": {"role": "Forgeron", "pos": [0, 0], "home": [1, 0], "energy": 100, "rel": {"Elora": 0, "Lila": -5}},
        "Lila": {"role": "Aubergiste", "pos": [4, 4], "home": [4, 3], "energy": 100, "rel": {"Elora": 20, "Kael": 0}}
    }
if 'world_time' not in st.session_state:
    st.session_state.world_time = 8  # Début à 8h du matin
if 'logs' not in st.session_state:
    st.session_state.logs = []

# --- LOGIQUE IA ---
def agent_turn(name):
    v = st.session_state.villagers[name]
    heure = st.session_state.world_time
    est_nuit = heure >= 22 or heure <= 6
    
    status = "fatigué" if v['energy'] < 30 else "en forme"
    consigne_nuit = "Il fait nuit, tu devrais aller dormir chez toi." if est_nuit else "Il fait jour, travaille ou socialise."

    prompt = f"""
    Tu es {name}. Heure: {heure}h. Énergie: {v['energy']}/100 ({status}).
    Position: {v['pos']}. Maison: {v['home']}.
    {consigne_nuit}
    
    Réponds en JSON:
    {{
        "pensee": "...",
        "action": "DORMIR" ou "TRAVAILLER" ou "MARCHER",
        "dest": [x, y]
    }}
    """
    try:
        res = llm.invoke(prompt)
        data = json.loads(res[res.find('{'):res.rfind('}')+1])
        return data
    except:
        return {"pensee": "Je plane...", "action": "RIEN", "dest": v['pos']}

# --- INTERFACE ---
st.title("🌙 Village IA : Cycle de Vie")

# Sidebar Status
with st.sidebar:
    st.header(f"⏰ {st.session_state.world_time}:00")
    if st.session_state.world_time >= 22 or st.session_state.world_time <= 6:
        st.warning("🌙 Il fait nuit...")
    else:
        st.success("☀️ Il fait jour")
    
    if st.button("⏭️ Passer à l'heure suivante", use_container_width=True):
        st.session_state.world_time = (st.session_state.world_time + 1) % 24
        for name in st.session_state.villagers:
            decision = agent_turn(name)
            v = st.session_state.villagers[name]
            
            # Application des conséquences
            v['pos'] = decision['dest']
            if decision['action'] == "DORMIR" and v['pos'] == v['home']:
                v['energy'] = min(100, v['energy'] + 20)
            else:
                v['energy'] = max(0, v['energy'] - 10)
            
            st.session_state.logs.insert(0, f"{st.session_state.world_time}h - **{name}** : {decision['pensee']}")

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