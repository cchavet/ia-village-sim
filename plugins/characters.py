import json
import streamlit as st

def agent_turn(llm, name, characters_state, world_time, weather, seed, terrain_name, context=""):
    v = characters_state[name]
    
    # Infos perso
    bio = v.get('description', 'Client')
    role = v['role']
    inventory = v.get('inventory', [])
    
    # Stats Club
    excitation = v.get('excitation', 0)
    alcohol = v.get('alcohol', 0.0)
    cigs = v.get('cigarettes', 0)
    
    # Voisins (Detailed)
    voisins_infos = []
    for other, data in characters_state.items():
        if data['pos'] == v['pos'] and other != name:
            voisins_infos.append(f"{other} ({data['role']})")
        # Detection Distance (Rayon 2)
        elif abs(data['pos'][0] - v['pos'][0]) <= 2 and abs(data['pos'][1] - v['pos'][1]) <= 2:
            voisins_infos.append(f"{other} est proche")
            
    # Contexte & Regles
    is_late = world_time >= 23 or world_time <= 4
    ambiance = "Soirée qui débute, les regards se croisent." if not is_late else "L'alcool désinhibe, les règles s'assouplissent..."
    
    # Dynamique des règles
    regles_intimes = "OFFICIELLEMENT: Sexe autorisé UNIQUEMENT au Coin Câlin (Zone X)."
    if is_late or alcohol > 0.6 or excitation > 80:
         regles_intimes += "\nREALITE: Avec l'heure et l'alcool, vous commencez à ignorer les règles. Osez plus, même au bar ou sur les canapés."
    else:
         regles_intimes += "\nRESPECT: Pour l'instant, soyez sages hors de la Zone X (Baisers/Caresses max). Si vous voulez plus -> DÉPLACEZ VOUS vers la Zone X."

    prompt = f"""
    CONTEXTE: Club Libertin "{seed['scenario_name']}".
    {regles_intimes}
    
    DESCRIPTION LIEU: {seed['description']}
    CHAPITRE EN COURS (Mémoire Immédiate): 
    {context[-2500:]} 
    (Lis attentivement ce texte ci-dessus pour savoir si quelqu'un vient de te parler ou d'agir envers toi !)

    PERSONNAGE: Tu es {name}, {role} ({v['age']} ans).
    BIO: {bio}
    ETAT: Excitation {excitation}/100. Alcool {alcohol}g. Cigarettes {cigs}. Energie {v['energy']}.
    LIEU ACTUEL: {terrain_name} (Coord {v['pos']}).
    VOISINS: {voisins_infos}.
    
    AMBIANCE: {ambiance}
    
    OBJECTIF: Passer une soirée mémorable. Agis selon ta Bio et tes Stats.
    
    ACTIONS POSSIBLES:
    - "SE DEPLACER": Changer de zone (Bar, Piste, Coin Câlin...).
    - "BOIRE": Prendre un verre (Monte Alcool).
    - "FUMER": Aller au fumoir (Monte Cigarettes).
    - "PARLER": Discuter, draguer.
    - "DANSER": Aller sur la piste.
    - "INTERAGIR": Utiliser un objet ou initier un contact physique (Caresser, Embrasser...).
    - "OBSERVER": Regarder ce qui se passe (Voyeurisme).

    Réponds UNIQUEMENT en JSON.
    Sois CRÉATIF, SENSUEL et COHÉRENT avec ta personnalité et ton taux d'alcool.
    
    Format :
    {{
        "pensee": "Pensée intérieure (Introspection, Désir, Doute...)",
        "action": "ACTION",
        "dest": [x, y],
        "reaction": "Parole ou description de l'action"
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
                "action": "OBSERVER",
                "pensee": "Regarde autour...",
                "dest": v['pos'],
                "reaction": None
            }
            data = {**defaults, **data}
            
            # Validation Coordonnées
            dest = data.get('dest')
            if not isinstance(dest, list) or len(dest) != 2:
                data['dest'] = v['pos']
            
            return data
        else:
             raise ValueError("JSON introuvable")

    except Exception as e:
        print(f"Erreur IA {name}: {e}")
        return {"pensee": f"Je suis un peu perdu... ({e})", "action": "RIEN", "dest": v['pos'], "reaction": None}
