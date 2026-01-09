# SYSTEME DE RELATIONS (Sims-like)

# Seuils
TH_LOVER = 80
TH_FRIEND = 50
TH_NEUTRAL_HIGH = 10
TH_NEUTRAL_LOW = -10
TH_RIVAL = -40
TH_ENEMY = -70

def get_rel_status(score):
    if score >= TH_LOVER: return "Amour"
    if score >= TH_FRIEND: return "Ami"
    if score >= TH_NEUTRAL_HIGH: return "Sympathique"
    if score > TH_NEUTRAL_LOW: return "Neutre"
    if score > TH_RIVAL: return "Froid"
    if score > TH_ENEMY: return "Rival"
    return "Ennemi"

def init_relations_if_needed(characters_state):
    """
    Ensure everyone has a 'rel' dict.
    """
    for name, v in characters_state.items():
        if 'rel' not in v:
            v['rel'] = {}

def update_affinity(source_data, target_name, delta):
    """
    Update relationship score.
    """
    if 'rel' not in source_data: source_data['rel'] = {}
    
    current = source_data['rel'].get(target_name, 0)
    new_val = max(-100, min(100, current + delta))
    source_data['rel'][target_name] = new_val
    
    return new_val, get_rel_status(new_val)

def get_affinity(source_data, target_name):
    return source_data.get('rel', {}).get(target_name, 0)

def get_social_context(name, characters_state, visible_neighbors):
    """
    Returns a string describing relations with VISIBLE neighbors.
    Ex: "Draco (Rival: -45), Luna (Ami: 60)"
    """
    v = characters_state[name]
    rels = v.get('rel', {})
    
    context_parts = []
    
    for neighbor in visible_neighbors:
        if neighbor == name: continue
        
        score = rels.get(neighbor, 0)
        status = get_rel_status(score)
        context_parts.append(f"{neighbor} ({status}: {score})")
        
    if not context_parts:
        return "Aucune relation notable ici."
        
    return ", ".join(context_parts)
