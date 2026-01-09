import json
import os

SAVE_FILE = "world_state.json"

def save_world(characters_data, world_time, logs, weather):
    """
    Sauvegarde l'état du monde dans un fichier JSON.
    """
    state_to_save = {
        "characters": characters_data, 
        "world_time": world_time,
        "logs": logs,
        "weather": weather
    }
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(state_to_save, f, indent=4, ensure_ascii=False)

def load_world():
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur de chargement: {e}")
        return None
