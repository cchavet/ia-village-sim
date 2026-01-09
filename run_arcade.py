import threading
import time
import json
import arcade
import os

from core import engine as game_engine
from core import llm
from core import storage
from game.ui_arcade import VillageWindow

# Shared State (replacing st.session_state)
class GameState(dict):
    """ Simple dict wrapper to allow attribute access if needed by legacy code """
    def __getattr__(self, item):
        return self.get(item)
    def __setattr__(self, key, value):
        self[key] = value

state = GameState()

# LOAD DATA
try:
    with open("resources/world_gen/world_seed.json", "r", encoding='utf-8') as f:
        SEED = json.load(f)
except FileNotFoundError:
    print("FATAL: resources/world_gen/world_seed.json not found!")
    exit(1)

# INITIALIZE STATE
loaded_state = storage.load_world()
if loaded_state:
    state.update(loaded_state) # Load existing Save
else:
    # Init New
    state.characters = SEED['characters']
    state.world_time = 1200
    state.weather = "Chaud"
    state.logs = []
    
state.map_layout = SEED['map_layout']
state.map_legend = SEED['map_legend']

# Init Engine
# Important: Engine needs llm in state?
# In engine.py we saw: llm_instance = state.llm
# So we need to init LLM here.
state.llm = llm.get_llm()

engine = game_engine.SimulationEngine(SEED)

def engine_thread_loop():
    """ Background thread running the simulation tick """
    print("🚀 Engine Thread Started")
    while True:
        # 1. Tick
        ready_agents = engine.tick(state, minutes=5)
        
        # 2. Decisions?
        # If agents are ready, we trigger them.
        # Note: This might be blocking if LLM is slow.
        # In main.py we separate UI spinner from Logic.
        # Here we are in a background thread, so blocking is 'okay' for logic, 
        # but the UI thread (Arcade) handles rendering so it won't freeze.
        
        if ready_agents:
            print(f"🧠 Processing agents: {ready_agents}")
            engine.run_agents_turn(state, target_agents=ready_agents)
            print(f"✅ Turn Complete.")
        
        # Sleep a bit to avoid CPU burn if nothing happens
        time.sleep(0.5)

# START THREAD
t = threading.Thread(target=engine_thread_loop, daemon=True)
t.start()

# START UI (Main Thread)
if __name__ == "__main__":
    window = VillageWindow(state)
    window.setup()
    arcade.run()
