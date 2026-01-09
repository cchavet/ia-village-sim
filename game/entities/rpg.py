import random

# --- CONSTANTS ---
SKILLS = ["MAGIE", "SOCIAL", "PHYSIQUE", "SAVOIR"]

BASE_XP_LEVEL = 100  # XP required for level 2

def roll_d20():
    return random.randint(1, 20)

def get_modifier(stat_value):
    # D&D style: 10 = +0, 12 = +1, etc.
    # Here let's say stats range 0-100 directly used?
    # Or keep it simple: Stat is the chances?
    # Let's use a "Stat + d20 vs Diff" system.
    # Stat range: 0 to 20 (like D&D args?).
    # If Stat is 0-100 (Energy style), let's normalize to 0-10.
    return stat_value // 10

def check_skill(character_state, skill_name, difficulty=15):
    """
    Performs a skill check.
    Returns (success: bool, roll: int, total: int, msg: str)
    """
    skill_val = character_state.get('stats', {}).get(skill_name, 0)
    roll = roll_d20()
    total = roll + skill_val
    
    success = total >= difficulty
    return {
        "success": success,
        "roll": roll,
        "bonus": skill_val,
        "total": total,
        "difficulty": difficulty
    }

def gain_xp(character_state, amount):
    """
    Adds XP and handles Level Up.
    Returns list of logs (strings).
    """
    logs = []
    current_xp = character_state.get('xp', 0)
    current_lvl = character_state.get('level', 1)
    
    new_xp = current_xp + amount
    xp_needed = current_lvl * BASE_XP_LEVEL
    
    character_state['xp'] = new_xp
    logs.append(f"Gagne {amount} XP")
    
    if new_xp >= xp_needed:
        character_state['level'] = current_lvl + 1
        character_state['xp'] = new_xp - xp_needed
        logs.append(f"🎉 LEVEL UP! Niveau {current_lvl + 1} atteint!")
        # Boost random stat?
        # For now, just logging.
    
    return logs

def init_stats(role):
    """
    Returns initial stats dict based on Role.
    Range 1-10 (Bonus added to d20).
    """
    stats = {s: 0 for s in SKILLS}
    
    if "Prof" in role or "Bibliothécaire" in role:
        stats["MAGIE"] = 8
        stats["SAVOIR"] = 9
        stats["SOCIAL"] = 4
        stats["PHYSIQUE"] = 2
    elif "Étudiant" in role:
        stats["MAGIE"] = 4
        stats["SAVOIR"] = 4
        stats["SOCIAL"] = 5
        stats["PHYSIQUE"] = 5
    elif "Garde" in role or "Videur" in role or "Concierge" in role:
        stats["PHYSIQUE"] = 8
        stats["SOCIAL"] = 2
        stats["MAGIE"] = 1
        stats["SAVOIR"] = 3
    elif "Vendeur" in role or "Tenancière" in role:
        stats["SOCIAL"] = 8
        stats["SAVOIR"] = 6
        stats["MAGIE"] = 3
        stats["PHYSIQUE"] = 3
    elif "Fantôme" in role:
        stats["MAGIE"] = 6
        stats["PHYSIQUE"] = 0
        stats["SOCIAL"] = 7
        stats["SAVOIR"] = 10
    else:
        # Default
        stats = {s: 3 for s in SKILLS}
        
    return stats
