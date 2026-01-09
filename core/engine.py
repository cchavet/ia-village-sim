import streamlit as st
from plugins import characters, relations, buildings, weather, economy, storybook
from core import storage

class SimulationEngine:
    def __init__(self, seed):
        self.seed = seed
        self.grid_size = seed['grid_size']

    def get_terrain_at(self, x, y):
        if 0 <= y < self.grid_size and 0 <= x < self.grid_size:
            char = self.seed['map_layout'][y][x]
            return self.seed['map_legend'].get(char, "Inconnu")
        return "Océan"

    def run_single_turn(self, current_chapter_text=""):
        """
        Exécute UN seul tour de simulation pour tous les agents.
        Retourne les logs techniques de ce tour.
        """
        # 1. Update Time/Weather
        # ADAPTIVE TIME STEPPING
        increment = st.session_state.get('next_time_increment', 1)
        st.session_state.world_time = (st.session_state.world_time + increment) % 1440
        
        current_time_min = st.session_state.world_time
        # Format HH:MM
        time_str = f"{current_time_min // 60}h{current_time_min % 60:02d}"
        
        st.session_state.weather = weather.update_weather(st.session_state.weather)
        
        step_logs = []
        
        # 2. Agents Turn (PARALLEL)
        import concurrent.futures
        
        # Prepare Snapshot Data for Threads (Avoid st.session_state inside threads)
        characters_snapshot = st.session_state.characters
        weather_snapshot = st.session_state.weather
        llm_instance = st.session_state.llm
        
        # Helper for parallel execution
        def process_agent(name, chars_data, current_weather, llm_obj, t_str):
            try:
                v = chars_data[name]
                x, y = v['pos']
                terrain = self.get_terrain_at(x, y)
                
                # Decision (Using passed data)
                decision = characters.agent_turn(
                    llm_obj, name, chars_data, 
                    t_str, current_weather, self.seed, terrain, 
                    context=current_chapter_text
                )
                return name, decision, v
            except Exception as e:
                print(f"Error Agent {name}: {e}")
                return None

        # 2. Agents Turn (TIERED BATCH PARALLEL)
        import concurrent.futures
        
        # Snapshot Data
        characters_snapshot = st.session_state.characters
        weather_snapshot = st.session_state.weather
        llm_instance = st.session_state.llm
        
        # Define Tiers
        MAINS = ["Alaric", "Elara", "Thorne"]
        EXTRAS = ["Peeves", "Baron", "Crocdur"]
        # Others = Secondaries
        
        all_names = list(characters_snapshot.keys())
        secondaries = [n for n in all_names if n not in MAINS and n not in EXTRAS]
        
        # Create Batches
        batches = []
        
        # Tier 1: Mains (1 per thread)
        for name in MAINS:
            if name in all_names: batches.append([name])
            
        # Tier 2: Secondaries (2 per thread)
        for i in range(0, len(secondaries), 2):
            batches.append(secondaries[i:i+2])
            
        # Tier 3: Extras (All in 1 thread)
        valid_extras = [n for n in EXTRAS if n in all_names]
        if valid_extras:
            batches.append(valid_extras)
            
        # Worker Function
        def process_batch_task(agent_names, chars_data, current_weather, llm_obj, t_str):
            try:
                # Prepare Terrain Dict
                terrains = {}
                for name in agent_names:
                    v = chars_data[name]
                    x, y = v['pos']
                    terrains[name] = self.get_terrain_at(x, y)
                
                # Batch Call
                decisions_map = characters.batch_agent_turn(
                    llm_obj, agent_names, chars_data, 
                    t_str, current_weather, self.seed, terrains, 
                    context=current_chapter_text
                )
                
                # Format Result List
                batch_results = []
                for name, decis in decisions_map.items():
                    batch_results.append((name, decis, chars_data[name]))
                return batch_results
            except Exception as e:
                print(f"Error Batch {agent_names}: {e}")
                return []

        # Execute
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_batch = {
                executor.submit(process_batch_task, batch, characters_snapshot, weather_snapshot, llm_instance, time_str): batch 
                for batch in batches
            }
            for future in concurrent.futures.as_completed(future_to_batch):
                 res_list = future.result()
                 results.extend(res_list)

        # Apply Updates Sequentially
        for name, decision, v in results:
            
            # ACTIONS
            # Safe clean of newlines or spaces
            action = str(decision.get('action', 'RIEN')).strip().upper()
            
            # Deplacement
            dest_x, dest_y = decision.get('dest', v['pos'])
            
            # Clamp Map
            new_x = max(0, min(self.grid_size-1, dest_x))
            new_y = max(0, min(self.grid_size-1, dest_y))
            v['pos'] = [new_x, new_y]
            
            # Stats (Generic Fantasy)
            if action == "REPOS":
                v['energy'] = min(100, v.get('energy', 0) + 10)
                if 'mana' in v: v['mana'] = min(200, v.get('mana', 0) + 10)
            else:
                v['energy'] = max(0, v.get('energy', 100) - 2)
            
            # Effects
            action_msg = ""
            if action == "BOIRE": action_msg = "🍺"
            if action == "MAGIE": action_msg = "✨"
            if action == "ETUDIER": action_msg = "📖"
            
            # Reaction Log
            if decision['reaction']: action_msg += f" \"{decision['reaction']}\""
            
            # Log
            # Include Location for Narrator Context
            terrain_display = self.get_terrain_at(new_x, new_y)
            log_entry = f"**{time_str} - {name}** ({terrain_display}) [❤️{v.get('excitation',0)}% 🍷{v.get('alcohol',0)}g]\n*{decision['pensee']}*\n> {action} {action_msg}"
            step_logs.append(log_entry)

        # FIXED TIME STEP (User Request: 1 turn = 1 hour)
        next_inc = 60
        
        st.session_state.next_time_increment = next_inc
        step_logs.append(f"*[MOTEUR] Eclipse Temporelle : +{next_inc} min.*")

        # 3. Save State (Continuous)
        st.session_state.logs = step_logs + st.session_state.logs
        if len(st.session_state.logs) > 500: st.session_state.logs = st.session_state.logs[:500]
        storage.save_world(st.session_state.characters, st.session_state.world_time, st.session_state.logs, st.session_state.weather)
        
        return step_logs
