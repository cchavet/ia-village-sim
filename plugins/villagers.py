import json
import streamlit as st

def agent_turn(llm, name, villagers_state, world_time, weather, seed, terrain_name):
    v = villagers_state[name]
    
    # Infos perso
    bio = v.get('description', 'Survivant')
    role = v['role']
    inventory = v.get('inventory', [])
    
    # Voisins
    voisins_infos = []
    for other, data in villagers_state.items():
        if data['pos'] == v['pos'] and other != name:
            voisins_infos.append(other)
            
    # Contexte
    est_nuit = world_time >= 20 or world_time <= 5
    consigne = "Il fait nuit. DANGER. Reste groupé ou dors." if est_nuit else "Cherche des ressources, explore, répare la radio."
    
    prompt = f"""
    CONTEXTE: {seed['description']}
    PERSONNAGE: Tu es {name}, {role} ({v['age']} ans). {bio}.
    ETAT: Énergie {v['energy']}/100. Inventaire: {inventory}.
    ENVIRONNEMENT: Tu es à: {terrain_name} (Coord {v['pos']}). Météo: {weather}.
    VOISINS: {voisins_infos}.
    
    {consigne}

    ACTIONS POSSIBLES:
    - "SE DEPLACER": Changer de case [x, y]. (Max 1 case de distance).
    - "FOUILLER": Chercher des objets (efficace sur les zones '?' rouges ou 'A' crash).
    - "DORMIR": Récupérer énergie.
    - "PARLER": Discuter avec voisins.
    - "UTILISER": Utiliser un objet de l'inventaire.

    Réponds UNIQUEMENT en JSON:
    {{
        "pensee": "Ta réflexion de survivant (peur, espoir, faim...)",
        "action": "SE DEPLACER" | "FOUILLER" | "DORMIR" | "PARLER",
        "dest": [x, y], // Tes nouvelles coordonnées (Obligatoire si action=SE DEPLACER, sinon garder actuelles)
        "reaction": {{"target": "Nom", "delta": 2}} // Optionnel
    }}
    """
    try:
        res = llm.invoke(prompt)
        
        # Nettoyage
        start = res.find('{')
        end = res.rfind('}')
        if start != -1 and end != -1:
            json_str = res[start:end+1]
            data = json.loads(json_str)
            
            # Defaults
            defaults = {
                "action": "RIEN",
                "pensee": "...",
                "dest": v['pos'],
                "reaction": None
            }
            data = {**defaults, **data}
            
            # Validation Coordonnées (Fix ValueError unpacking)
            dest = data.get('dest')
            if not isinstance(dest, list) or len(dest) != 2:
                data['dest'] = v['pos']
            
            return data
        else:
             raise ValueError("JSON introuvable")

    except Exception as e:
        print(f"Erreur IA {name}: {e}")
        return {"pensee": f"Je survis... ({e})", "action": "RIEN", "dest": v['pos'], "reaction": None}
