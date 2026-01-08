import json
import streamlit as st
from core.config import LOCATIONS, ITEMS_PRICES

def agent_turn(llm, name, villagers_state, world_time, weather):
    v = villagers_state[name]
    est_nuit = world_time >= 22 or world_time <= 6
    
    # Localisation
    current_pos_tuple = tuple(v['pos'])
    current_location_name = "En chemin"
    for loc_name, coords in LOCATIONS.items():
        if tuple(coords) == current_pos_tuple:
            current_location_name = loc_name
            break
            
    # Voisins et leurs inventaires pour le commerce
    voisins_infos = []
    for other, data in villagers_state.items():
        if data['pos'] == v['pos'] and other != name:
            inv = data.get('inventory', [])
            voisins_infos.append(f"{other} (Vend: {inv})")
    
    relations_text = ", ".join([f"{n}: {score}" for n, score in v['rel'].items()])
    
    status = "fatigué" if v['energy'] < 30 else "en forme"
    consigne_nuit = "Il fait nuit, rentre." if est_nuit else "Il fait jour, travaille, crafte ou commerce."
    
    # Infos économie
    gold = v.get('gold', 0)
    inventory = v.get('inventory', [])
    prices_list = ", ".join([f"{k}:{v}or" for k, v in ITEMS_PRICES.items()])

    prompt = f"""
    Tu es {name} ({v['role']}). Heure: {world_time}h. Énergie: {v['energy']}. Or: {gold}. Inv: {inventory}.
    Météo: {weather}. Lieu: {current_location_name}.
    Relations: {relations_text}.
    Voisins ici: {voisins_infos}.
    Prix du marché: {prices_list}.
    
    OBJECTIFS:
    1. Survivre (Dormir la nuit).
    2. Exercer ton métier (CRAFT si tu as le bon rôle).
    3. T'enrichir (ACHETER des objets utiles, ou attendre des clients).
    
    ROLES CRAFT: Forgeron -> "Épée", Apothicaire -> "Potion".
    
    Réponds UNIQUEMENT en JSON:
    {{
        "pensee": "...",
        "destination": "Nom exact du lieu (L'Auberge, La Place...)",
        "action": "DORMIR" | "TRAVAILLER" | "CRAFT" | "ACHETER" | "RIEN",
        "objet": "Nom de l'objet (si CRAFT ou ACHETER)",
        "cible": "Nom du vendeur (si ACHETER)",
        "reaction": {{"target": "Nom", "delta": 5}} // optionnel
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
                "destination": current_location_name,
                "objet": None,
                "cible": None,
                "reaction": None
            }
            data = {**defaults, **data}

            # TRADUCTION Coordonnées
            dest_name = data.get('destination')
            if dest_name in LOCATIONS:
                data['dest'] = LOCATIONS[dest_name]
            else:
                data['dest'] = v['pos']
            
            return data
        else:
             raise ValueError("JSON introuvable")

    except Exception as e:
        print(f"Erreur IA {name}: {e}")
        return {"pensee": f"Erreur.. {e}", "action": "RIEN", "dest": v['pos'], "reaction": None}
