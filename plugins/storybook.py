import os
import google.generativeai as genai
from datetime import datetime

STORY_DIR = "story"
os.makedirs(STORY_DIR, exist_ok=True)

def init_gemini():
    try:
        if not os.path.exists("api.key"):
            print("api.key not found.")
            return False
            
        with open("api.key", "r") as f:
            api_key = f.read().strip()
            
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"Gemini Init Error: {e}")
        return False

def generate_chapter(day_num, logs, survivors_state):
    """
    Génère un chapitre BD Adulte basé sur les logs de la journée.
    """
    if not init_gemini():
        return "Erreur: Clé API manquante."

    # Préparation du contexte
    survivors_desc = "\n".join([f"- {name} ({data['role']}): {data.get('description', '')}" for name, data in survivors_state.items()])
    recent_logs = "\n".join(logs[-50:]) # On prend les 50 derniers logs pour le contexte immédiat
    
    prompt = f"""
    CONTEXTE: Simulation de survie "Crash sur l'Île". Jour {day_num}.
    PERSONNAGES:
    {survivors_desc}
    
    EVENEMENTS RECENTS (Logs):
    {recent_logs}
    
    TACHE:
    Écris le Chapitre {day_num} de cette histoire sous forme de SCÉNARIO DE BANDE DESSINÉE (Graphic Novel) pour adultes.
    STYLE: Noir, Réaliste, "Gritty", Introspectif. Ne pas hésiter sur la difficulté de la survie.
    
    FORMAT:
    Génère 2 "PAGES" de BD. Pour chaque page :
    - Titre de la Page.
    - 4 à 6 Cases (Panels).
    - Pour chaque Case : 
      - [IMAGE PROMPT]: Description visuelle TRÈS DÉTAILLÉE pour un générateur d'image (cadrage, lumière, action, expressions).
      - RÉCIT/DIALOGUE: Le texte de la case.
      
    SORTIE: Markdown brut.
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        filename = os.path.join(STORY_DIR, f"chapter_{day_num}.md")
        with open(filename, "w", encoding='utf-8') as f:
            f.write(f"# CHAPITRE {day_num}\n\n")
            f.write(response.text)
            
        return f"Chapitre {day_num} généré dans {filename}"
    except Exception as e:
        return f"Erreur Génération: {e}"

def narrate_turn(events):
    """
    Transforme les logs bruts d'un tour en un court récit d'ambiance.
    """
    if not init_gemini():
        return None

    prompt = f"""
    CONTEXTE: Survival "Crash sur l'Île".
    EVENEMENTS DU MOMENT:
    {events}
    
    TACHE: Agis comme un narrateur de film de survie/noir.
    Synthétise ces événements en un seul paragraphe court (max 3 phrases) et immersif.
    Mets l'accent sur l'atmosphère, la tension, ou les émotions.
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"(Erreur Narrateur: {e})"
