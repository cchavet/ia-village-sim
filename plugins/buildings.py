from core.config import MAP_LOCATIONS, GRID_SIZE

def get_location_name(pos):
    return MAP_LOCATIONS.get(tuple(pos), f"Route ({pos})")

def update_energy(villager, action):
    if action == "DORMIR" and villager['pos'] == villager['home']:
        villager['energy'] = min(100, villager['energy'] + 20)
    else:
        villager['energy'] = max(0, villager['energy'] - 10)
    
    return villager['energy']
