import streamlit as st
import json
from datetime import datetime
from core.llm import get_llm
from core import storage, ui, engine as game_engine
from game.systems import storybook

# --- CONFIG ---
try:
    with open("resources/world_gen/world_seed.json", "r", encoding='utf-8') as f:
        SEED = json.load(f)
except FileNotFoundError:
    st.error("resources/world_gen/world_seed.json introuvable !")
    st.stop()

# --- INITIALISATION ---
st.set_page_config(page_title=SEED['scenario_name'], layout="wide")

if 'llm' not in st.session_state:
    st.session_state.llm = get_llm()

# --- ETAT SESSION & CHARGEMENT ---
# --- ETAT SESSION & CHARGEMENT ---
if 'characters' not in st.session_state:
    # Try Load
    current_state = storage.load_world()
    
    # CHECK SCENARIO MATCH
    stored_name = current_state.get('scenario_name', '') if current_state else ''
    if stored_name != SEED['scenario_name']:
        st.toast(f"Changement d'Univers détecté : {SEED['scenario_name']}")
        current_state = None # Force Reset
    
    if current_state:
        st.session_state.characters = current_state.get('characters', SEED['characters']) 
        # Time Management (Minutes)
        w_time = current_state.get('world_time', 1200)
        # Migration Old Save (Hours -> Minutes)
        if w_time < 30: w_time = 1200 
        st.session_state.world_time = w_time
        
        st.session_state.logs = current_state.get('logs', [])
        st.session_state.weather = current_state.get('weather', "Chaud")
        st.session_state.key_facts = current_state.get('key_facts', [])
        st.session_state.map_objects = current_state.get('map_objects', [])
        
        st.session_state.current_chapter = current_state.get('current_chapter', ["**INTRODUCTION**\n\nBienvenue au Club..."])
        st.session_state.archived_chapters = current_state.get('archived_chapters', [])
        st.session_state.scenario_name = SEED['scenario_name']
        
        # MERGE NEW CHARACTERS (Live Update)
        for name, data in SEED['characters'].items():
            if name not in st.session_state.characters:
                st.session_state.characters[name] = data
                st.toast(f"Nouveau personnage : {name}")
                
    else:
        # New Game
        st.session_state.characters = SEED['characters']
        st.session_state.world_time = 1200 # 20h00
        st.session_state.logs = []
        st.session_state.weather = "Chaud"
        st.session_state.key_facts = []
        st.session_state.map_objects = []
        
        st.session_state.current_chapter = [
            "**PANEL 1 [EXT. RUE - NUIT]**\n"
            "Une ruelle baignée d'une lueur rouge tamisée. L'enseigne 'EROS' pulse doucement comme un battement de coeur.\n"
            "Clem et Mary sont là. Mary ajuste sa robe, un peu trop courte. Clem la dévore des yeux. L'air sent le jasmin et le musc.\n\n"
            "**NARRATEUR**\n"
            "20h00. La nuit promet d'être brûlante. Ils franchissent le seuil."
        ]
        st.session_state.archived_chapters = []
        st.session_state.scenario_name = SEED['scenario_name']

# --- MOTEUR ---
engine = game_engine.SimulationEngine(SEED)

# --- LOGIC ---
def run_step(target_agents=None):
    # 1. Simulation (Agents)
    full_text = "\n".join(st.session_state.current_chapter)
    
    with st.spinner(f"🧠 {len(target_agents)} Agents réfléchissent..."):
        step_logs = engine.run_agents_turn(current_chapter_text=full_text, target_agents=target_agents)
    
    # 2. Narration (Storybook)
    with st.spinner("✍️ Le Narrateur écrit l'histoire..."):
        narrator_gen = storybook.narrate_continuous(
            full_text, 
            "\n".join(step_logs), 
            SEED, 
            world_time_min=st.session_state.world_time, 
            key_facts="\n".join(st.session_state.key_facts)
        )
        
        new_text_block = ""
        for chunk in narrator_gen:
                new_text_block += chunk
    
    if new_text_block:
        st.session_state.current_chapter.append(new_text_block)
        
        # 3. Dynamic Objects (Spawn from Text)
        try:
            new_objects = storybook.scan_for_objects(new_text_block)
            if new_objects:
                import random
                for obj_name in new_objects:
                    # Spawn near a random agent
                    target_agent = random.choice(list(st.session_state.characters.values()))
                    tx, ty = target_agent['pos']
                    # Offset random
                    ox, oy = random.randint(-1, 1), random.randint(-1, 1)
                    sx, sy = max(0, min(31, tx+ox)), max(0, min(31, ty+oy))
                    
                    st.session_state.map_objects.append({'name': obj_name, 'pos': [sx, sy]})
                    st.toast(f"Objet apparu : {obj_name} en [{sx},{sy}]", icon="🎁")
        except Exception as e:
            print(f"Spawn Error: {e}")

    # 4. Chapter Management
    if len(st.session_state.current_chapter) > 15: 
        end_chapter()

def end_chapter():
    full_text = "\n".join(st.session_state.current_chapter)
    st.session_state.archived_chapters.append(full_text)
    
    st.toast("Fin de Chapitre... Analyse...")
    new_facts = storybook.analyze_chapter(full_text, st.session_state.characters)
    st.session_state.key_facts.extend(new_facts)
    
    # Reset
    chap_num = len(st.session_state.archived_chapters) + 1
    st.session_state.current_chapter = [f"**CHAPITRE {chap_num}**\n\n"]
    st.toast(f"Nouveau Chapitre : {chap_num}")

# --- RENDU UI ---
ui.inject_custom_css()

# DISPLAY MODE TOGGLE
show_logs = st.sidebar.checkbox("Afficher Logs RPG (Technique)", value=True)

# Dashboard Render
if show_logs:
    # Show last 20 logs reversed (or normal?)
    # usually logs are appended. let's show last 30 for context.
    latest_text = "\n\n".join(st.session_state.logs[-30:])
elif st.session_state.current_chapter:
    latest_text = st.session_state.current_chapter[-1]
else:
    latest_text = "En attente..."

ui.render_dashboard(
    st.session_state.characters, 
    st.session_state.world_time, 
    SEED['map_layout'], 
    SEED['map_colors'],
    latest_text,
    st.session_state.logs,
    map_objects=st.session_state.map_objects
)

# --- CONTROLS & LIVE LOOP ---

if 'running' not in st.session_state:
    st.session_state.running = False

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
col_ctrl, col_info = st.columns([1,3])

with col_ctrl:
    if st.button("⏯ PAUSE / REPRENDRE", type="primary"):
        st.session_state.running = not st.session_state.running
        st.rerun()

# SPEED CONTROLS
st.sidebar.markdown("---")
st.sidebar.write("⚡ **Vitesse Simulation**")
speed_min = st.sidebar.slider("Minutes par Tick", 1, 60, 5)
turbo_mode = st.sidebar.checkbox("Mode Turbo (No Sleep)", value=True)

with col_info:
    status = "🟢 EN COURS" if st.session_state.running else "🔴 PAUSE"
    st.write(f"**Etat : {status}** ({speed_min} min de jeu / tick)")

# LIVE LOOP
if st.session_state.running:
    import time
    
# LIVE LOOP
if st.session_state.running:
    import time
    
    # Tick Engine
    if turbo_mode:
        # ASYNC SPEEDRUN: Jump to next finished action
        ready_agents = engine.jump_to_next_event()
    else:
        # PROPORTIONAL TIME: Tick by speed_min
        ready_agents = engine.tick(minutes=speed_min)
    
    # Check if Agents need to play
    if ready_agents:
        run_step(target_agents=ready_agents) 
        
        # Log update is already in engine
        st.session_state.logs.append(f"*[SYSTEM] {st.session_state.world_time//60}h{st.session_state.world_time%60:02d} : {len(ready_agents)} actions.*")
        st.rerun() 
    else:
        if not turbo_mode:
            time.sleep(0.5) 
        
        st.rerun()

