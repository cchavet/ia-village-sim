from core.llm import get_llm
import os
import json

STORY_DIR = "resources/story"
os.makedirs(STORY_DIR, exist_ok=True)

def get_gemini_client():
    # Deprecated: Redirect to core.llm
    return get_llm()

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
            model=None,
            contents=metaprompt
        )
        return response.text.strip()
    except Exception:
        return events # Fallback brut

def narrate_turn_local(events):
    """
    Récit simple via API (remplace l'ancien fallback local).
    """
    client = get_gemini_client()
    if not client: return "(Pas d'IA disponible)"

    try:
        prompt = f"""
        Tu es le Narrateur d'un jeu de survie sombre.
        LOGS:
        {events}
        
        Tache : Raconte ce qui se passe en 2 phrases max. Ambiance tendue.
        """
        # On utilise le modèle par défaut du client
        response = client.models.generate_content(model=None, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"(Erreur Récit: {e})"

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
            model=None,
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

def narrate_continuous(current_chapter_text, turn_logs, world_seed, world_time_min=1200, key_facts=""):
    """
    Génère la suite de l'histoire en se basant sur TOUT le chapitre en cours.
    Assure une continuité parfaite.
    """
    client = get_gemini_client()
    if not client:
        return narrate_turn_local(turn_logs) # Fallback simple

    # Calcul Phase Narrative
    h = world_time_min // 60
    m = world_time_min % 60
    time_str = f"{h}h{m:02d}"
    
    directors_note = "PHASE 1 (Matinale) : Cours de magie, interactions sociales, petits secrets entres élèves."
    if h >= 12:
        directors_note = "PHASE 2 (Après-midi) : Sortie au village, visite des boutiques, intrigues qui se nouent."
    if h >= 18:
        directors_note = "PHASE 3 (Soirée) : Mystère sombre, ombres dans les couloirs, couvre-feu imminent."
    if h >= 22 or h < 6:
        directors_note = "PHASE 4 (Nuit) : DANGER. Exploration interdite, Forêt Interdite, créatures magiques, duels clandestins."
    
    # Prompt avec Contexte Max
    # Prompt Style Bande Dessinée / Roman Graphique Fantasy
    prompt = f"""
    ROLE: Auteur de Fantasy / Chroniqueur du Monde des Sorciers (Style Harry Potter).
    PROJET: TOME 1 "MYSTÈRES DE L'ACADÉMIE".
    TIMELINE: Une journée complète à l'école de magie.
    NOTE: Ambiance "Magical School". Merveilleux, Whimsical, mais avec une menace sous-jacente sombre.
    
    CONTEXTE DU MONDE:
    
    DIRECTIVE DU REALISATEUR ({directors_note}):
    - Suis impérativement cette phase pour le ton de la scène.
    
    CONTEXTE DU MONDE:
    {world_seed['description']}
    
    MEMOIRE (Faits Importants Passés) :
    {key_facts}
    
    CHAPITRE EN COURS (Continuité) :
    {current_chapter_text[-3000:]} 
    
    NOUVELLES ACTIONS (Logs Minute par Minute) :
    {turn_logs}
    
    TACHE :
    - Écris le script de la PAGE SUIVANTE (Panels et Dialogues).
    - **TEMPS** : Ça ne dure qu'une minute ! Étire l'action. Ne saute pas dans le temps.
    - **STYLE** : Très visuel. Magique. Effets de sortilèges.
    - **DIALOGUES** : Typés sorciers ("Par la barbe de Merlin!", formules magiques).
    - **LANGAGE** : Romanesque, immersif.
    
    FORMAT ATTENDU :
      **PANEL 1 [Lieu] :** Description courte et visuelle.
      **[Perso] :** Dialogue...
      
    - **SPATIALITÉ** : Respecte les lieux des logs.
    - **ATTITUDE** : Montre la magie (étincelles, potions qui fument, balais qui volent).
    """
    
    try:
        response_stream = client.models.generate_content_stream(
            model=None,
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
            model=None,
            contents=prompt
        )
        return [l.strip() for l in response.text.split('\n') if l.strip().startswith('-')]
    except Exception:
        return []

def scan_for_objects(text):
    """
    Scanne le texte pour trouver des objets mentionnés qui devraient apparaître sur la carte.
    """
    client = get_gemini_client()
    if not client: return []
    
    prompt = f"""
    Analyste de décors.
    TEXTE:
    {text}
    
    TACHE: Identifie les OBJETS PHYSIQUES concrets mentionnés qui sont "posés" ou "apparus" dans la scène (PAS ceux déjà dans l'inventaire).
    Ex: "Elle pose une bouteille sur la table" -> Bouteille.
    Ex: "Il sort son téléphone" -> NON (Inventaire).
    Renvoie une liste Python de strings. Ex: ["Bouteille de vin", "Cendrier"]
    Renvoie [] si rien.
    """
    try:
        response = client.models.generate_content(
            model=None,
            contents=prompt
        )
        # Nettoyage basique
        txt = response.text.replace("```python", "").replace("```", "").strip()
        import ast
        return ast.literal_eval(txt)
    except Exception:
        return []
