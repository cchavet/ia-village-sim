import os
from google import genai
from datetime import datetime
import subprocess

STORY_DIR = "story"
os.makedirs(STORY_DIR, exist_ok=True)

def get_gemini_client():
    try:
        if not os.path.exists("api.key"):
            return None
        with open("api.key", "r") as f:
            api_key = f.read().strip()
        client = genai.Client(api_key=api_key)
        return client
    except Exception as e:
        print(f"Gemini Init Error: {e}")
        return None

def prepare_prompt_ai(events):
    """
    Utilise Gemini 3 pour synthétiser les logs (anciennement local).
    """
    client = get_gemini_client()
    if not client: return events

    try:
        metaprompt = f"""
        Tu es un assistant scénariste. Voici des logs bruts d'un jeu de survie :
        {events}
        
        Tache : Résume ces actions en 4 lignes maximum. Identifie tension/danger.
        Format : "Actions: ..., Ambiance: ..."
        """
        response = client.models.generate_content(
            model='models/gemini-3-flash-preview',
            contents=metaprompt
        )
        return response.text.strip()
    except Exception:
        return events # Fallback brut

def narrate_turn_local(events):
    """
    Récit de secours via Llama local.
    """
    try:
        # On utilise le même pré-prompt ou un prompt simplifié
        prompt = f"""
        Tu es le Narrateur d'un jeu de survie sombre.
        LOGS:
        {events}
        
        Tache : Raconte ce qui se passe en 2 phrases max. Ambiance tendue.
        """
        res = subprocess.run(
            ["ollama", "run", "llama3.2:1b", prompt], 
            capture_output=True, text=True, encoding='utf-8', shell=True
        )
        return res.stdout.strip()
    except Exception as e:
        return f"(Erreur Local: {e})"

def extract_facts_ai(logs_text):
    """
    Analyse les logs pour extraire les faits marquants via Gemini 3 (anciennement local).
    """
    client = get_gemini_client()
    if not client: return []

    try:
        prompt = f"""
        Analyste de scénario.
        LOGS:
        {logs_text}
        
        TACHE: Liste UNIQUEMENT les événements majeurs (1 ligne par fait).
        CRITERES: Blessure grave, Objet trouvé, Découverte lieu, Rencontre.
        SI RIEN D'IMPORTANT: Réponds "Rien".
        FORMAT: "- [Nom] a trouvé..."
        """
        response = client.models.generate_content(
            model='models/gemini-3-flash-preview',
            contents=prompt
        )
        output = response.text.strip()
        
        if "Rien" in output or not output:
             return []
        
        # Filtrage basique
        facts = [line for line in output.split('\n') if line.strip().startswith('-')]
        return facts
    except Exception:
        return []

def narrate_continuous(current_chapter_text, turn_logs, world_seed, key_facts=""):
    """
    Génère la suite de l'histoire en se basant sur TOUT le chapitre en cours.
    Assure une continuité parfaite.
    """
    client = get_gemini_client()
    if not client:
        return narrate_turn_local(turn_logs) # Fallback simple

    # Prompt avec Contexte Max
    # Prompt Style Bande Dessinée / Roman Graphique
    prompt = f"""
    ROLE: Scénariste de Bande Dessinée Adulte / Roman Graphique (Style "Blacksad" ou "Thorgal" moderne).
    
    CONTEXTE DU MONDE:
    {world_seed['description']}
    
    MEMOIRE (Faits Importants Passés) :
    {key_facts}
    
    CHAPITRE EN COURS (Continuité) :
    {current_chapter_text[-3000:]} 
    
    NOUVELLES ACTIONS DES PERSONNAGES (Raw Logs) :
    {turn_logs}
    
    TACHE :
    - Écris la suite sous forme de SCRIPT DE BD (Panels et Dialogues).
    - **STYLE** : Visuel, dynamique, dialogues percutants.
    - **LANGAGE** : Soutenu, élégant et soigné. Évite absolument le langage familier ou l'argot.
    - **FORMAT** :
      *   **PANEL [Lieu] :** Description courte et visuelle de l'action.
      *   **[Perso] :** Dialogue.
    
    - **SPATIALITÉ** : Respecte scrupuleusement les zones (Bar, Piste...).
    - **COHÉRENCE** : Les ivres balbutient, les timides hésitent.
    - Évite les descriptions psychologiques vagues ("Il pense que..."). Montre-le par l'action ("Il serre les poings").
    """
    
    try:
        response_stream = client.models.generate_content_stream(
            model='models/gemini-3-flash-preview',
            contents=prompt
        )
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"[Erreur Narrateur: {e}]"

def analyze_chapter(full_chapter_text, villagers_data):
    """
    Analyse un chapitre TERMINÉ pour en extraire des souvenirs.
    """
    client = get_gemini_client()
    if not client: return []
    
    prompt = f"""
    TACHE: Archiviste.
    TEXTE A ANALYSER (Chapitre complet):
    {full_chapter_text}
    
    OBJECTIF: Extraire les 3-5 faits majeurs qui ont changé l'histoire ou les personnages.
    FORMAT: Liste à puces "- [Jour X] Fait..."
    """
    
    try:
        response = client.models.generate_content(
            model='models/gemini-3-flash-preview',
            contents=prompt
        )
        return [l.strip() for l in response.text.split('\n') if l.strip().startswith('-')]
    except Exception:
        return []
