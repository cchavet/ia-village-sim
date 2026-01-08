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

def narrate_turn_stream(events, previous_context="", key_facts=""):
    """
    Récit d'ambiance via Gemini (Cloud) - Mode Streaming.
    Renvoie un générateur.
    previous_context : Le texte des derniers tours pour éviter les répétitions.
    key_facts : Liste des faits marquants (Loot, blessures...) à garder en tête.
    """
    client = get_gemini_client()
    # Si pas de client ou erreur init, fallback direct
    if not client:
        yield narrate_turn_local(events)
        return

    context = prepare_prompt_locally(events)
    prompt = f"""
    CONTEXTE: Jeu Survival "Crash sur l'Île".
    
    FAITS IMPORTANTS (Mémoire) :
    {key_facts}
    
    PRECEDEMMENT (Style et Ton) :
    {previous_context}
    
    NOUVEAUX FAITS (Résumé) : 
    {context}
    
    TACHE: Écris la suite. Narrateur style Film Noir / Survie.
    CRITIQUE: Un seul paragraphe court (< 3 phrases). Immersif.
    IMPORTANT: NE PAS RÉPÉTER CE QUI A ÉTÉ DIT PRÉCÉDEMMENT. FAIS AVANCER L'HISTOIRE.
    """
    
    try:
        # Utilisation de generate_content_stream pour le V1 SDK
        response_stream = client.models.generate_content_stream(
            model='models/gemini-3-flash-preview',
            contents=prompt
        )
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"⚠️ *Relais Local...* "
        # Fallback synchrone (pas de stream token par token pour Ollama via subprocess)
        yield narrate_turn_local(events)

def narrate_turn(events):
    """
    Récit d'ambiance via Gemini (Cloud).
    """
    client = get_gemini_client()
    if not client:
        return None

    context = prepare_prompt_ai(events)
    prompt = f"""
    CONTEXTE: Jeu Survival "Crash sur l'Île".
    RESUME: {context}
    TACHE: Narrateur style Film Noir / Survie.
    CRITIQUE: Un seul paragraphe court (< 3 phrases). Immersif.
    """
    
    try:
        response = client.models.generate_content(
            model='models/gemini-3-flash-preview',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        if "429" in str(e):
            return None
        return f"(Pause Narrateur... {str(e)[:50]})"

def generate_chapter(day_num, logs, survivors_state):
    """
    Génère un chapitre BD quotidien.
    """
    client = get_gemini_client()
    if not client:
        return "Erreur Clé API"

    survivors_desc = "\n".join([f"- {name}: {data['role']}" for name, data in survivors_state.items()])
    recent_logs = "\n".join(logs[-50:])
    
    prompt = f"""
    CONTEXTE: Survival Jour {day_num}.
    CAST: {survivors_desc}
    LOGS: {recent_logs}
    Output: SCENARIO BD ADULTE/NOIR. 2 Pages.
    Pour chaque case: [IMAGE PROMPT] + DIALOGUE.
    """
    
    try:
        response = client.models.generate_content(
            model='models/gemini-3-flash-preview',
            contents=prompt
        )
        
        filename = os.path.join(STORY_DIR, f"chapter_{day_num}.md")
        with open(filename, "w", encoding='utf-8') as f:
             f.write(f"# CHAPITRE {day_num}\n\n{response.text}")
             
        return f"Chapitre écrit: {filename}"
        
    except Exception as e:
        return f"Erreur Chapitre: {e}"
