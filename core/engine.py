import streamlit as st
from plugins import villagers, relations, buildings, weather, economy, storybook
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

    def generate_page_content(self, placeholder=None):
        """
        Génère une PAGE complète de roman (~300 mots).
        Simule autant de tours que nécessaire.
        """
        accumulated_text = ""
        turn_count = 0
        MAX_TURNS_PER_PAGE = 5
        TARGET_WORDS = 300
        
        full_page_logs = [] # To store Logs for history
        
        placeholder_text = "" # Local buffer for stream display
        
        while len(accumulated_text.split()) < TARGET_WORDS and turn_count < MAX_TURNS_PER_PAGE:
            turn_count += 1
            st.session_state.world_time = (st.session_state.world_time + 1) % 24
            current_time = st.session_state.world_time
            st.session_state.weather = weather.update_weather(st.session_state.weather)
            
            step_logs = []
            
            # --- SIMULATION TOUR ---
            for name in st.session_state.villagers:
                v = st.session_state.villagers[name]
                x, y = v['pos']
                terrain = self.get_terrain_at(x, y)

                # Décision & Mouvement (Simplified for brevity, logic remains same)
                decision = villagers.agent_turn(
                    st.session_state.llm, name, st.session_state.villagers, 
                    current_time, st.session_state.weather, self.seed, terrain
                )
                
                # Apply Move
                dest_x, dest_y = decision['dest']
                curr_x, curr_y = v['pos']
                move_x = max(-1, min(1, dest_x - curr_x))
                move_y = max(-1, min(1, dest_y - curr_y))
                new_x = max(0, min(self.grid_size-1, curr_x + move_x))
                new_y = max(0, min(self.grid_size-1, curr_y + move_y))
                v['pos'] = [new_x, new_y]
                
                # Energy
                v['energy'] = max(0, v['energy'] - 5)
                if decision['action'] == "DORMIR": v['energy'] = min(100, v['energy'] + 15)
                
                # Loot
                action_msg = ""
                if decision['action'] == "FOUILLER" and "?" in self.seed['map_layout'][new_y][new_x]:
                    import random
                    if random.random() < 0.3:
                        item = random.choice(self.seed['loot_table'])
                        v['inventory'].append(item)
                        action_msg = f" | 🎁 Trouvé : {item} !"
                
                if decision['reaction']: relationships = relations.update_relationships(v, decision)
                
                # Log
                stats = f"[🔋{v['energy']}%]"
                step_logs.append(f"**{current_time}h - {name}** {stats}\n*{decision['pensee']}*\n> {decision['action']} {action_msg}")

            # --- GENERATION NARRATIVE (SEGMENT) ---
            if step_logs:
                # Memoire
                if 'key_facts' not in st.session_state: st.session_state.key_facts = []
                new_facts = storybook.extract_facts_ai("\n".join(step_logs))
                for f in new_facts: st.session_state.key_facts.append(f"J{st.session_state.world_time//24} {current_time}h: {f}")
                
                valid_facts = st.session_state.get('key_facts', [])[-10:]
                
                # Context = Previous Page + Current Params
                prev_context = accumulated_text[-500:] # Last 500 chars of current page
                
                stream = storybook.narrate_page_segment(step_logs, prev_context, "\n".join(valid_facts))
                
                segment_text = ""
                for chunk in stream:
                    if chunk:
                        segment_text += chunk
                        # Live Update UI
                        if placeholder:
                            placeholder.markdown(f'<div class="story-block current-writing">{placeholder_text} {segment_text} ▌</div>', unsafe_allow_html=True)
                
                accumulated_text += "\n\n" + segment_text
                placeholder_text += "\n\n" + segment_text
                
                full_page_logs.extend(step_logs)

        # --- FIN PAGE ---
        # Save logs
        st.session_state.logs = full_page_logs + st.session_state.logs
        if len(st.session_state.logs) > 500: st.session_state.logs = st.session_state.logs[:500]
        
        storage.save_world(st.session_state.villagers, st.session_state.world_time, st.session_state.logs, st.session_state.weather)
        
        return accumulated_text
