import json
import os
import zipfile
from datetime import datetime

SAVE_DIR = "data"
SAVE_FILE_ZIP = os.path.join(SAVE_DIR, "current_world.zip")
SAVE_FILE_JSON = os.path.join(SAVE_DIR, "current_world.json") # Legacy

def save_world(characters_data, world_time, logs, weather):
    """
    Sauvegarde l'état dans une archive ZIP (state.json + metadata.json).
    """
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
        
    state_to_save = {
        "characters": characters_data, 
        "world_time": world_time,
        "logs": logs,
        "weather": weather
    }
    
    metadata = {
        "version": "1.0",
        "saved_at": datetime.now().isoformat(),
        "timestamp": world_time
    }
    
    try:
        with zipfile.ZipFile(SAVE_FILE_ZIP, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. État du monde
            zf.writestr("state.json", json.dumps(state_to_save, indent=4, ensure_ascii=False))
            # 2. Métadonnées
            zf.writestr("metadata.json", json.dumps(metadata, indent=4))
            # 3. Version
            zf.writestr("version.txt", "1.0.0")
            # 4. Screenshot Placeholder
            zf.writestr("screenshot.txt", "[Capture d'écran non disponible]")
            
        print(f"Sauvegarde ZIP réussie : {SAVE_FILE_ZIP}")
        
    except Exception as e:
        print(f"Erreur de sauvegarde ZIP : {e}")

def load_world():
    """
    Charge le monde. Priorise le ZIP. Fallback sur le JSON.
    """
    # 1. Try ZIP
    if os.path.exists(SAVE_FILE_ZIP):
        try:
            with zipfile.ZipFile(SAVE_FILE_ZIP, 'r') as zf:
                with zf.open("state.json") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erreur lecture ZIP: {e}")
    
    # 2. Try Legacy JSON
    if os.path.exists(SAVE_FILE_JSON):
        print("Chargement sauvegarde Legacy (JSON)...")
        try:
            with open(SAVE_FILE_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur lecture JSON: {e}")

    return None
