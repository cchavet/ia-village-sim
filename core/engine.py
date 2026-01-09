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
        st.session_state.world_time = (st.session_state.world_time + 1) % 24
        current_time = st.session_state.world_time
        st.session_state.weather = weather.update_weather(st.session_state.weather)
        
        step_logs = []
        
        # 2. Agents Turn
        # Using list() to avoid runtime error if dict changes size (unlikely here but safe)
        for name in list(st.session_state.characters.keys()):
            v = st.session_state.characters[name]
            x, y = v['pos']
            terrain = self.get_terrain_at(x, y)

            # FULL CONTEXT passed via kwargs or modified agent_turn signature
            # For now keeping signature compatible, but we can stick Context in session_state if needed
            # Actually, user wants "fiche, etat du monde, chapitre en cours entier".
            # We will handle the Prompt Construction update in 'characters.py' next.
            # Here we just execute the logic.
            
            decision = characters.agent_turn(
                st.session_state.llm, name, st.session_state.characters, 
                current_time, st.session_state.weather, self.seed, terrain, 
                context=current_chapter_text # Passing context, need to update characters.py to accept it
            )
            
            # ACTIONS CLUB
            action = decision['action']
            
            # Deplacement
            dest_x, dest_y = decision['dest']
            curr_x, curr_y = v['pos']
            move_x = max(-1, min(1, dest_x - curr_x))
            move_y = max(-1, min(1, dest_y - curr_y))
            new_x = max(0, min(self.grid_size-1, curr_x + move_x))
            new_y = max(0, min(self.grid_size-1, curr_y + move_y))
            v['pos'] = [new_x, new_y]
            
            # Effects
            action_msg = ""
            if action == "BOIRE":
                v['alcohol'] = round(v.get('alcohol', 0) + 0.2, 2)
                v['excitation'] = min(100, v.get('excitation', 0) + 5)
                action_msg = "🍸"
            elif action == "FUMER":
                v['cigarettes'] = v.get('cigarettes', 0) + 1
                v['excitation'] = min(100, v.get('excitation', 0) + 2)
                action_msg = "🚬"
            elif action == "DANSER":
                v['energy'] = max(0, v['energy'] - 5)
                v['excitation'] = min(100, v.get('excitation', 0) + 5)
                action_msg = "💃"
            elif action == "DRAGUER" or action == "INTERAGIR":
                v['excitation'] = min(100, v.get('excitation', 0) + 10)
                action_msg = "❤️"
            
            # Reaction Log
            if decision['reaction']: action_msg += f" \"{decision['reaction']}\""
            
            # Log
            # Include Location for Narrator Context
            terrain_display = self.get_terrain_at(new_x, new_y)
            log_entry = f"**{current_time}h - {name}** ({terrain_display}) [❤️{v.get('excitation',0)}% 🍷{v.get('alcohol',0)}g]\n*{decision['pensee']}*\n> {action} {action_msg}"
            step_logs.append(log_entry)

        # 3. Save State (Continuous)
        st.session_state.logs = step_logs + st.session_state.logs
        if len(st.session_state.logs) > 500: st.session_state.logs = st.session_state.logs[:500]
        storage.save_world(st.session_state.characters, st.session_state.world_time, st.session_state.logs, st.session_state.weather)
        
        return step_logs
