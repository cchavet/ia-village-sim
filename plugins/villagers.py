import json
import streamlit as st
from core.config import GRID_SIZE

def agent_turn(llm, name, villagers_state, world_time, weather):
    v = villagers_state[name]
    est_nuit = world_time >= 22 or world_time <= 6
    
    presents_voisins = [other for other, data in villagers_state.items() if data['pos'] == v['pos'] and other != name]
    relations_text = ", ".join([f"{n}: {score}" for n, score in v['rel'].items()])
    
    status = "fatigué" if v['energy'] < 30 else "en forme"
    consigne_nuit = "Il fait nuit, tu devrais aller dormir chez toi." if est_nuit else "Il fait jour, travaille ou socialise."

    prompt = f"""
    Tu es {name}. Heure: {world_time}h. Énergie: {v['energy']}/100 ({status}).
    Météo: {weather}.
    Position: {v['pos']}. Maison: {v['home']}.
    Relations: {relations_text}.
    Voisins actuels: {presents_voisins}.
    
    {consigne_nuit}
    
    Réponds UNIQUEMENT avec un JSON valide. Pas de markdown, pas de texte avant/après.
    Format attendu:
    {{
        "pensee": "...",
        "action": "DORMIR",
        "dest": [0, 4],
        "reaction": {{"target": "Nom", "delta": 0}}
    }}
    """
    try:
        res = llm.invoke(prompt)
        
        # Nettoyage agressif
        start = res.find('{')
        end = res.rfind('}')
        if start != -1 and end != -1:
            json_str = res[start:end+1]
            # Correction des erreurs courantes (suppression virgules fin)
            import re
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            
            data = json.loads(json_str)
            
            # Valeurs par défaut pour éviter KeyError
            defaults = {
                "action": "RIEN",
                "pensee": "...",
                "dest": v['pos'],
                "reaction": None
            }
            # Merge: les valeurs de data écrasent defaults
            data = {**defaults, **data}
        else:
            raise ValueError("Pas de JSON trouvé")
        
        # Validation des coordonnées (Cast en int pour éviter les strings "0")
        if isinstance(data.get('dest'), list) and len(data['dest']) == 2:
            try:
                x = int(data['dest'][0])
                y = int(data['dest'][1])
                data['dest'][0] = max(0, min(GRID_SIZE - 1, x))
                data['dest'][1] = max(0, min(GRID_SIZE - 1, y))
            except (ValueError, TypeError):
                data['dest'] = v['pos']
        else:
            data['dest'] = v['pos'] # Fallback
            
        return data
    except Exception as e:
        print(f"Erreur IA pour {name}: {e}")
        return {"pensee": "Je suis confus...", "action": "RIEN", "dest": v['pos'], "reaction": None}
