def update_relationships(villager, decision):
    if 'reaction' in decision and decision['reaction'] and isinstance(decision['reaction'], dict):
        target = decision['reaction'].get('target')
        delta = decision['reaction'].get('delta', 0)
        
        if target in villager['rel']:
            villager['rel'][target] = max(-100, min(100, villager['rel'][target] + delta))
    
    return villager
