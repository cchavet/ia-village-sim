# Documentation du Workflow Technique "MyVillage"

## 1. Architecture Globale
Le projet fonctionne selon une architecture **Modulaire pilotée par Événements**, orchestrée par **Streamlit**.
Tout est exécuté en local, le cerveau (IA) étant délégué à **Ollama** (`gemma3:4b`).

### Composants Clés
*   **Front-End / Orchestrateur** : `main.py` (Streamlit). Gère l'état (SessionState), l'UI, et la boucle principale.
*   **Noyau (Core)** :
    *   `engine.py` : Logique de jeu déterministe (Déplacements, Stats, Temps).
    *   `llm.py` : Wrapper pour Ollama (Gère le cycle de vie du processus et les appels API).
    *   `ui.py` : Rendu visuel (Dashboard, CSS propre).
*   **Plugins (Logique Métier)** :
    *   `characters.py` : "Cerveau" individuel des agents (Prompts de décision).
    *   `storybook.py` : "Narrateur" omniscient (Transformation des logs en récit).
*   **Données** : `world_seed.json` (Configuration statique de l'univers).

---

## 2. Cycle de Vie (Démarrage)

1.  **Initialisation (`main.py`)** :
    *   Chargement de la configuration (`world_seed.json`).
    *   Vérification/Démarrage du modèle Ollama (`ensure_model_ready`).
    *   Initialisation de `st.session_state` (Création des agents si nouvelle partie, ou chargement sauvegarde).
2.  **Rendu UI (`core/ui.py`)** :
    *   Affichage du Dashboard (Cartes Agents, Map, Log Narratif) via CSS injecté.
    *   Attente d'interaction utilisateur (Bouton "AVANCER").

---

## 3. Workflow d'un Tour de Simulation (`run_step`)

Chaque clic sur "AVANCER" (ou boucle auto) déclenche une séquence précise :

### A. Phase Moteur (`core/engine.py`)
1.  **Mise à jour Temporelle** : Avance de **60 minutes** (1 Tour = 1 Heure).
2.  **Météo** : Mise à jour probabiliste (`weather.py`).
3.  **Décision des Agents (Parallélisme)** :
    *   Le moteur lance un **ThreadPoolExecutor** (Multithreading).
    *   Pour chaque Agent, il appelle `characters.agent_turn()`.
    *   **Prompt Agent** : L'agent reçoit son état, le lieu, l'heure, et le contexte immédiat.
    *   **Réponse LLM** : JSON structuré `{"action": "...", "dest": [...], "pensee": "..."}`.
4.  **Application des Actions** :
    *   Les décisions sont appliquées séquentiellement (Déplacement sur la grille, modification stats Énergie/Mana).
    *   Génération des **Logs Techniques** (Ex: `Alaric se déplace vers [4,4]`).

### B. Phase Narrative (`plugins/storybook.py`)
1.  **Contexte** : Le narrateur récupère le texte du chapitre en cours + les nouveaux logs techniques.
2.  **Calcul de l'Ambiance** : Selon l'heure (Phase Matinale, Soirée, Nuit...), une "Note du Réalisateur" est injectée dans le prompt.
3.  **Génération (Streaming)** :
    *   Le LLM reçoit les logs bruts et doit écrire la suite de l'histoire (Style "Bande Dessinée Fantasy").
    *   Le texte est streamé directement dans l'UI.
4.  **Effets de Bord** :
    *   **Scan d'Objets** : Analyse du texte généré pour voir si des objets physiques ont été mentionnés. Si oui, ils apparaissent sur la Map (`map_objects`).

### C. Gestion de Chapitre
*   Si le texte dépasse une certaine taille (~15 blocs), le chapitre est archivé (`analyze_chapter` extrait des résumés/faits marquants) et un nouveau chapitre vierge commence.

---

## 4. Flux de Données (IA)

1.  **Core -> Ollama** : `core/llm.py` envoie une requête POST à `localhost:11434`.
2.  **Ollama** : Traite avec le modèle `gemma3:4b` (chargé en VRAM).
3.  **Ollama -> Core** : Retourne du JSON (Agents) ou du Texte (Narrateur).
4.  **Erreurs** : Si le JSON est invalide, une action par défaut ("OBSERVER") est appliquée pour ne pas crasher.

## 5. Particularités Actuelles
*   **Temps Accéléré** : 1 Tour = 1 Heure. Permet de simuler une journée complète en 24 clics.
*   **Thème Magique** : Univers "Mystères de l'Académie" (Harry Potter-like).
*   **UI Pro** : Interface sobre et technique.
