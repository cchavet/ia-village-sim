import streamlit as st
import json
from datetime import datetime
from core.llm import get_llm
from core import storage, ui, engine as game_engine
from plugins import storybook

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
def run_step():
    # 1. Simulation
    full_text = "\n".join(st.session_state.current_chapter)
    step_logs = engine.run_single_turn(current_chapter_text=full_text)
    
    # 2. Narration
    narrator_gen = storybook.narrate_continuous(
        full_text, 
        "\n".join(step_logs), 
        SEED, 
        world_time_min=st.session_state.world_time, # Pass time for Pacing Logic
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
    
    # PDF Update
    try:
        from plugins import publisher
        publisher.publish_book_pdf(
            SEED['scenario_name'], 
            st.session_state.archived_chapters,
            output_filename=f"story/{SEED['scenario_name'].replace(' ','_')}.pdf"
        )
        st.toast("📚 Livre mis à jour !")
    except Exception as e:
        st.error(f"Erreur PDF: {e}")

# --- RENDU UI ---
ui.inject_custom_css()

# Dashboard Render
# Show ONLY the latest text block (Live Feed behavior)
if st.session_state.current_chapter:
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

# --- CONTROLS ---
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
c1, c2, c3 = st.columns([1,1,1])

with c2:
    if st.button("▶ AVANCER (1 TOUR)"):
        with st.spinner("Simulation & Écriture..."):
            run_step()
        st.rerun()

if st.checkbox("Mode Auto (Expérimental)"):
    import time
    time.sleep(1)
    run_step()
    st.rerun()

# --- MAGIC GENERATOR ---
with st.expander("🔮 MAGIE : GÉNÉRATION INTÉGRALE DU TOME (BATCH)", expanded=False):
    st.write("Génère tous les tours jusqu'à 04h00 du matin (Fin de soirée) en une seule passe.")
    
    if st.button("🚀 LANCER LA GÉNÉRATION (Be Patient!)"):
        # Target: 04h00 Next Day. 
        # Logic: If now < 04h00 (240 min), run until 240. 
        # If now > 240 (e.g. 20h00 = 1200), run until 1440 then until 240.
        
        current_min = st.session_state.world_time
        target_min = 240 # 04h00
        
        # Calculate Total Duration (Minutes)
        if current_min < target_min:
            total_duration = target_min - current_min
        else:
            total_duration = (1440 - current_min) + target_min
            
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        elapsed = 0
        safety_max_turns = 1000
        turn_count = 0
        
        while elapsed < total_duration and turn_count < safety_max_turns:
            # Capture Previous Time
            t_prev = st.session_state.world_time
            
            # Run Turn
            status_text.text(f"Génération Tour {turn_count+1} (Accumulé {elapsed}/{total_duration} min) ... Heure : {st.session_state.world_time//60}h{st.session_state.world_time%60:02d}")
            run_step()
            turn_count += 1
            
            # Calculate Delta (Handle Midnight Wrap)
            t_curr = st.session_state.world_time
            if t_curr < t_prev: # Rollover 23h59 -> 00h
                 delta = (1440 - t_prev) + t_curr
            else:
                 delta = t_curr - t_prev
            
            elapsed += delta
            
            # Update Progress
            prog = min(1.0, elapsed / total_duration)
            progress_bar.progress(prog)
            
            # Stop condition logic is implicit via 'elapsed < total_duration'
            # But strictly speaking we stop when we pass the target
            
        status_text.text("✅ TOME TERMINÉ ! (04h00 Atteinte)")
        progress_bar.progress(1.0)
        st.success("Génération terminée avec succès. Le Tome est complet.")
        st.session_state.current_chapter.append("\n\n**--- FIN DU TOME 1 ---**")
        
        # EXPORT SCRIPT
        import os
        os.makedirs("story", exist_ok=True)
        filename = f"story/Tome_1_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {SEED['scenario_name']} - TOME 1\n\n")
            f.write(f"**Date Génération:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"**Casting:** {', '.join(st.session_state.characters.keys())}\n\n")
            f.write("---\n\n")
            f.write("\n".join(st.session_state.current_chapter))
            
        st.toast(f"💾 Script sauvegardé : {filename}")
        st.balloons()
        st.rerun()
