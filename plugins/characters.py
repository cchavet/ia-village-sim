from core.llm import get_llm
from plugins import rpg_system, relations
import json
import streamlit as st

def get_agent_prompt_data(name, v, characters_state, world_time, seed, terrain_name, context):
    # Infos perso
    bio = v.get('description', '')
    role = v['role']
    inventory = v.get('inventory', [])
    
    # Init Relations
    relations.init_relations_if_needed(characters_state)
    
    # Voisins (Detailed)
    visible_neighbors = []
    for other, data in characters_state.items():
        if data['pos'] == v['pos'] and other != name:
            visible_neighbors.append(other)
        # Detection Distance (Rayon 2)
        elif abs(data['pos'][0] - v['pos'][0]) <= 2 and abs(data['pos'][1] - v['pos'][1]) <= 2:
            visible_neighbors.append(other)
            
    social_context = relations.get_social_context(name, characters_state, visible_neighbors)

    # Stats RPG
    stats = v.get('stats', {})
    if not stats: 
        stats_str = "Standard"
    else:
        stats_str = " | ".join([f"{k}:{val}" for k, val in stats.items()])

    return f"""
    --- PERSONNAGE: {name} ---
    ROLE: {role} ({v['age']} ans). BIO: {bio}
    STATS: {stats_str}. XP: {v.get('xp', 0)} (Lvl {v.get('level', 1)})
    ETAT: Energie {v['energy']}. Inv: {inventory}
    LIEU: {terrain_name} (Coord {v['pos']}).
    RELATIONS (Voisins): {social_context}.
    """

def agent_turn(llm, name, characters_state, world_time, weather, seed, terrain_name, context=""):
    # Wrapper simple pour compatibilité
    return batch_agent_turn(llm, [name], characters_state, world_time, weather, seed, {name: terrain_name}, context)[name]

def batch_agent_turn(llm, agent_names, characters_state, world_time, weather, seed, terrains_dict, context=""):
    """
    Traite une liste d'agents en une seule requête LLM.
    Retourne un dict {name: decision_dict}
    """
    
    agents_block = ""
    for name in agent_names:
        v = characters_state[name]
        agents_block += get_agent_prompt_data(name, v, characters_state, world_time, seed, terrains_dict.get(name, "Inconnu"), context)
    
    prompt = f"""
    CONTEXTE: {seed['scenario_name']} (RPG SIMULATION)
    HEURE ACTUELLE: {world_time}
    DESCRIPTION LIEU GLOBALE: {seed['description']}
    
    CHAPITRE EN COURS (Mémoire Immédiate): 
    {context[-2000:]} 
    
    VOICI LES PERSONNAGES (Groupe):
    {agents_block}
    
    OBJECTIF COMMUN: Progresser, réussir ses objets, interagir.
    CONSIGNE: **1 TOUR = 1 HEURE.**
    
    MECANIQUE RPG:
    - Chaque action "difficile" (Etudier un sort complexe, convaincre, escalader) demandera un jet de dés.
    - Choisis des actions cohérentes avec tes STATS (Ex: Si Magie faible, évite les duels).
    
    ACTIONS POSSIBLES:
    - "SE DEPLACER" [dest]: Changer de lieu.
    - "ETUDIER" [target_skill='SAVOIR'/'MAGIE']: Gagner de l'XP.
    - "DISCUTER" [target_skill='SOCIAL', target='NOM']: Socialiser.
    - "EXPLORER" [target_skill='PHYSIQUE']: Fouiller/Observer.
    - "MAGIE" [target_skill='MAGIE']: Lancer un sort/Pratiquer.
    - "REPOS": Regagner Energie.
    
    Réponds UNIQUEMENT en JSON.
    Format :
    {{
        "NomAgent1": {{
            "pensee": "Stratégie...",
            "action": "ACTION",
            "target": "NOM_CIBLE (Optionnel)",
            "target_skill": "NOM_COMPETENCE_UTILISEE", 
            "dest": [x, y],
            "reaction": "..."
        }},
        ...
    }}
    """
    
    try:
        res = llm.invoke(prompt)
        
        # Nettoyage JSON
        start = res.find('{')
        end = res.rfind('}')
        if start != -1 and end != -1:
            json_str = res[start:end+1]
            data = json.loads(json_str)
            
            final_results = {}
            for name in agent_names:
                d = data.get(name)
                # Fallback Defaults
                defaults = {
                    "action": "RIEN",
                    "pensee": "Attend...",
                    "dest": characters_state[name]['pos'],
                    "reaction": None
                }
                
                if not d:
                    final_results[name] = defaults
                else:
                    # Validate Dest
                    dst = d.get('dest')
                    if not isinstance(dst, list) or len(dst) != 2:
                        d['dest'] = characters_state[name]['pos']
                    final_results[name] = {**defaults, **d}
            
            return final_results

        else:
             raise ValueError("JSON invalide")

    except Exception as e:
        print(f"Erreur Batch IA: {e}")
        # Return fallback for all
        return {name: {"action": "RIEN", "pensee": f"Erreur {e}", "dest": characters_state[name]['pos'], "reaction": None} for name in agent_names}
