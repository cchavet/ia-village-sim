from core.llm import get_llm
import json
import streamlit as st

def get_agent_prompt_data(name, v, characters_state, world_time, seed, terrain_name, context):
    # Infos perso
    bio = v.get('description', '')
    role = v['role']
    inventory = v.get('inventory', [])
    
    # Voisins (Detailed)
    voisins_infos = []
    for other, data in characters_state.items():
        if data['pos'] == v['pos'] and other != name:
            voisins_infos.append(f"{other} ({data['role']})")
        # Detection Distance (Rayon 2)
        elif abs(data['pos'][0] - v['pos'][0]) <= 2 and abs(data['pos'][1] - v['pos'][1]) <= 2:
            voisins_infos.append(f"{other} est proche")

    return f"""
    --- PERSONNAGE: {name} ---
    ROLE: {role} ({v['age']} ans). BIO: {bio}
    ETAT: Energie {v['energy']}. Inv: {inventory}
    LIEU: {terrain_name} (Coord {v['pos']}).
    VOISINS: {voisins_infos}.
    """

def agent_turn(llm, name, characters_state, world_time, weather, seed, terrain_name, context=""):
    # Wrapper simple pour compatibilité
    # On pourrait appeler batch_agent_turn avec une liste de 1, mais pour garder la logique "Main Character" pure, on garde le prompt individuel riche.
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
    CONTEXTE: {seed['scenario_name']}
    HEURE ACTUELLE: {world_time}
    DESCRIPTION LIEU GLOBALE: {seed['description']}
    
    CHAPITRE EN COURS (Mémoire Immédiate): 
    {context[-2000:]} 
    
    VOICI LES PERSONNAGES A JOUER (Groupe):
    {agents_block}
    
    OBJECTIF COMMUN: Vivre leur vie dans cet univers.
    CONSIGNE DE TEMPS: **1 TOUR = 1 HEURE.**
    
    ACTIONS POSSIBLES:
    - "SE DEPLACER": Changer de lieu.
    - "ETUDIER/TRAVAILLER": Améliorer compétences.
    - "DISCUTER": Social.
    - "EXPLORER": Fouiller.
    - "MAGIE": Pratiquer.
    - "REPOS": Dormir.
    - "RIEN": Attendre.
    
    Réponds UNIQUEMENT en JSON.
    Format attendu : Dictionnaire avec le nom de l'agent comme clé.
    {{
        "NomAgent1": {{
            "pensee": "...",
            "action": "ACTION",
            "dest": [x, y],
            "reaction": "..."
        }},
        "NomAgent2": ...
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
