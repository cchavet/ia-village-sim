import streamlit as st
from game.entities import characters, buildings
from game.systems import relations, weather, economy, storybook
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

    def tick(self, minutes=1):
        """
        Avance le temps. Retourne la liste des agents PRETS A JOUER.
        """
        st.session_state.world_time = (st.session_state.world_time + minutes) % 1440
        current_time = st.session_state.world_time
        
        # Weather chance
        if current_time % 10 == 0:
             st.session_state.weather = weather.update_weather(st.session_state.weather)
             
        # Find Free Agents
        ready_agents = []
        for name, v in st.session_state.characters.items():
            busy_until = v.get('busy_until', 0)
            # If busy_until < current_time (accounting for day wrap? Simplified: just linear check)
            # Simplification: Reset busy_until on new day? 
            # For now, let's assume linear time or handle midnight wrap carefully.
            # To avoid wrap issues, we might want to store 'busy_remaining' instead?
            # Or just ignore wrap for a prototype logic if we reset manually.
            # Robust: busy_until is absolute minute of day. If we wrap 1440->0, we must reset busy_until too?
            # Hack: If busy_until > 1440, it means next day.
            
            # Simple Logic: Action finishes.
            if  current_time >= busy_until:
                 ready_agents.append(name)
        
        return ready_agents

    def jump_to_next_event(self):
        """
        Avance jusqu'à la fin de la prochaine action en cours.
        """
        current = st.session_state.world_time
        min_busy = 9999
        
        for v in st.session_state.characters.values():
            b = v.get('busy_until', current)
            if b > current:
                if b < min_busy: min_busy = b
        
        if min_busy == 9999: 
            return self.tick(1) # No one busy? +1
            
        delta = min_busy - current
        if delta <= 0: delta = 1
        
        return self.tick(delta)

    def run_agents_turn(self, current_chapter_text="", target_agents=None):
        """
        Exécute la décision pour les agents spécifiés.
        """
        # Update Time Display
        current_time_min = st.session_state.world_time
        time_str = f"{current_time_min // 60}h{current_time_min % 60:02d}"

        # Initialize Stats if needed
        from game.entities import rpg as rpg_system
        for name, v in st.session_state.characters.items():
            if 'stats' not in v:
                v['stats'] = rpg_system.init_stats(v['role'])
                v['xp'] = 0; v['level'] = 1
        
        step_logs = []
        
        # Determine who plays
        if target_agents is None:
            # Fallback: All
            target_agents = list(st.session_state.characters.keys())
            
        if not target_agents:
            return []

        # PROCESSING (Tiered Logic reused but filtered)
        import concurrent.futures
        
        # Filter Batches for only target_agents
        characters_snapshot = st.session_state.characters
        weather_snapshot = st.session_state.weather
        llm_instance = st.session_state.llm
        
        # Create ad-hoc batches for just these agents
        batches = []
        # Create ad-hoc batches for just these agents
        batches = []
        
        # User defined Group: Creatures/Extras
        extras_group = ["Peeves", "Baron", "Crocdur"]
        found_extras = [n for n in target_agents if n in extras_group]
        
        # Remove them from the pool to batch
        remaining_pool = [n for n in target_agents if n not in extras_group]
        
        # 1. Batch Extras together
        if found_extras:
            batches.append(found_extras)
            
        # 2. Batch others in MASSIVE groups (Gemini Flash Context is huge)
        BATCH_SIZE = 15
        for i in range(0, len(remaining_pool), BATCH_SIZE):
            batches.append(remaining_pool[i:i+BATCH_SIZE])
            
        # Worker (Same as before)
        def process_batch_task(agent_names, chars_data, current_weather, llm_obj, t_str):
            try:
                terrains = {}
                for name in agent_names:
                    v = chars_data[name]
                    terrains[name] = self.get_terrain_at(v['pos'][0], v['pos'][1])
                
                decisions_map = characters.batch_agent_turn(
                    llm_obj, agent_names, chars_data, 
                    t_str, current_weather, self.seed, terrains, 
                    context=current_chapter_text
                )
                
                batch_results = []
                for name, decis in decisions_map.items():
                    if name in chars_data:
                        batch_results.append((name, decis, chars_data[name]))
                return batch_results
            except Exception as e:
                print(f"Error Batch {agent_names}: {e}")
                return []

        # Execute
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_batch = {
                executor.submit(process_batch_task, batch, characters_snapshot, weather_snapshot, llm_instance, time_str): batch 
                for batch in batches
            }
            for future in concurrent.futures.as_completed(future_to_batch):
                 results.extend(future.result())

        # Apply Updates
        for name, decision, v in results:
            
            # --- DURATION LOGIC ---
            duration = int(decision.get('duration', 15))
            if duration < 5: duration = 5 # Minimum 5 mins
            v['busy_until'] = (st.session_state.world_time + duration) % 1440
            # Handle midnight wrap logic carefully later. For now sim is 1 day.
            
            # ACTIONS ...
            action = str(decision.get('action', 'RIEN')).strip().upper()
            
            # Deplacement
            dest_x, dest_y = decision.get('dest', v['pos'])
            new_x = max(0, min(self.grid_size-1, dest_x))
            new_y = max(0, min(self.grid_size-1, dest_y))
            v['pos'] = [new_x, new_y]
            
            # Stats (Generic Fantasy) & RPG Recovery
            if action == "REPOS":
                v['energy'] = min(100, v.get('energy', 0) + 10)
                if 'mana' in v: v['mana'] = min(200, v.get('mana', 0) + 10)
            else:
                v['energy'] = max(0, v.get('energy', 100) - 2)
            
            # --- RPG MECHANIC: SKILL CHECK ---
            target_skill = decision.get('target_skill')
            rpg_log = ""
            skill_success = False
            
            if target_skill and target_skill in rpg_system.SKILLS:
                # Roll
                check = rpg_system.check_skill(v, target_skill)
                status = "SUCCÈS" if check['success'] else "ÉCHEC"
                skill_success = check['success']
                rpg_log = f"\n> 🎲 **{target_skill}**: {check['roll']} + {check['bonus']} = {check['total']} (Diff {check['difficulty']}) -> **{status}**"
                
                if check['success']:
                    xp_logs = rpg_system.gain_xp(v, 20) 
                    if xp_logs: rpg_log += f" | {' '.join(xp_logs)}"
                else:
                    rpg_log += " | (Fatigue +2)"
                    v['energy'] = max(0, v.get('energy', 0) - 2)

            # --- SOCIAL MECHANIC ---
            target_name = decision.get('target')
            if target_name and target_name in st.session_state.characters and target_name != name:
                delta = 0
                if target_skill == "SOCIAL": delta = 5 if skill_success else -2
                elif action == "DISCUTER" or action == "DRAGUER": delta = 2 
                
                if delta != 0:
                    new_val, status = relations.update_affinity(v, target_name, delta)
                    rpg_log += f"\n> ❤️ **Relation {target_name}**: {delta:+d} ({status}: {new_val})"

            # Effects
            action_msg = ""
            if action == "BOIRE": action_msg = "🍺"
            if action == "MAGIE": action_msg = "✨"
            if action == "ETUDIER": action_msg = "📖"
            if action == "DISCUTER": action_msg = "💬"
            
            if decision['reaction']: action_msg += f" \"{decision['reaction']}\""
            
            # Log
            terrain_display = self.get_terrain_at(new_x, new_y)
            stats_display = f"Lvl {v.get('level', 1)}"
            # Show Duration in Log
            log_entry = f"**{time_str} - {name}** ({terrain_display}) [{stats_display}]\n*{decision['pensee']}*\n> {action} {action_msg} (⏳ {duration} min){rpg_log}"
            step_logs.append(log_entry)

        # 3. Save State (Continuous)
        st.session_state.logs = step_logs + st.session_state.logs
        if len(st.session_state.logs) > 500: st.session_state.logs = st.session_state.logs[:500]
        storage.save_world(st.session_state.characters, st.session_state.world_time, st.session_state.logs, st.session_state.weather)
        
        return step_logs
