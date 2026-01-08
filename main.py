import streamlit as st
from langchain_ollama import OllamaLLM
import time
import subprocess

# --- CONFIGURATION ---
st.set_page_config(page_title="IA Village Simulator", layout="wide")

# --- VÉRIFICATION DU MODÈLE ---
def check_and_pull_model(model_name):
    """Vérifie si le modèle Ollama est disponible, sinon le télécharge."""
    try:
        # Liste les modèles locaux
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, encoding='utf-8')
        if model_name not in result.stdout:
            st.info(f"Le modèle '{model_name}' n'est pas trouvé localement. Téléchargement en cours...")
            with st.spinner(f"Téléchargement de {model_name} (cela peut prendre quelques minutes)..."):
                # Télécharge le modèle
                subprocess.run(["ollama", "pull", model_name], check=True)
            st.success(f"Modèle '{model_name}' téléchargé avec succès !")
    except FileNotFoundError:
        st.error("Ollama n'est pas installé ou n'est pas dans le PATH. Veuillez installer Ollama : https://ollama.com")
        st.stop()
    except Exception as e:
        st.error(f"Erreur lors de la gestion du modèle Ollama : {e}")
        st.stop()

MODEL_NAME = "llama3.2:1b"
check_and_pull_model(MODEL_NAME)
llm = OllamaLLM(model=MODEL_NAME)

# --- INITIALISATION DU VILLAGE ---
if 'villagers' not in st.session_state:
    st.session_state.villagers = [
        {"nom": "Elora", "role": "Apothicaire", "traits": "Calme, herboriste, un peu mystérieuse.", "etat": "Croit que la forêt lui parle.", "logs": []},
        {"nom": "Kael", "role": "Forgeron", "traits": "Bourru, travailleur, déteste le bruit inutile.", "etat": "Fatigué par la chaleur de la forge.", "logs": []},
        {"nom": "Lila", "role": "Aubergiste", "traits": "Joviale, sait tout sur tout le monde.", "etat": "Prépare l'arrivée de voyageurs.", "logs": []}
    ]
if 'history' not in st.session_state:
    st.session_state.history = []

# --- LOGIQUE IA ---
def generate_life_step(villager):
    prompt = f"""
    Tu es {villager['nom']}, le {villager['role']}. 
    Personnalité: {villager['traits']}
    Contexte actuel: {villager['etat']}
    
    Décris en une phrase courte ton action actuelle dans le village ou une pensée.
    Réponds directement par l'action, sans introduction.
    """
    response = llm.invoke(prompt)
    return response.strip()

# --- INTERFACE UI ---
st.title("🏘️ Simulation de Village IA")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Habitants")
    for v in st.session_state.villagers:
        with st.expander(f"{v['nom']} ({v['role']})"):
            st.write(f"**Traits:** {v['traits']}")
            st.info(f"**État:** {v['etat']}")

with col2:
    st.header("Journal du Village")
    
    if st.button("Passer une heure dans le village"):
        with st.spinner("Le temps passe..."):
            for v in st.session_state.villagers:
                action = generate_life_step(v)
                v['etat'] = action # Mise à jour de l'état pour la prochaine itération
                timestamp = time.strftime("%H:%M")
                log_entry = f"**{timestamp} - {v['nom']}:** {action}"
                st.session_state.history.insert(0, log_entry)
        
    # Affichage du journal
    for entry in st.session_state.history:
        st.write(entry)

# --- STYLE ---
st.markdown("""
<style>
    .stExpander { border: 1px solid #4CAF50; border-radius: 10px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)