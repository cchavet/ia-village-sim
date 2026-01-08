import streamlit as st
from langchain_community.llms import Ollama
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="IA Village Engine", layout="wide")

# Utilisation de Llama 3.2 1B pour la vitesse sur ta 1080 Ti
llm = Ollama(model="llama3.2:1b", temperature=0.7)

# --- INITIALISATION ---
if 'villagers' not in st.session_state:
    st.session_state.villagers = {
        "Elora": {"role": "Apothicaire", "traits": "Mystérieuse, calme", "memoire": [], "faim": 100},
        "Kael": {"role": "Forgeron", "traits": "Bourru, protecteur", "memoire": [], "faim": 100},
        "Lila": {"role": "Aubergiste", "traits": "Joviale, pipelette", "memoire": [], "faim": 100}
    }
if 'world_step' not in st.session_state:
    st.session_state.world_step = 0

# --- LOGIQUE DE SIMULATION ---
def simulate_step(name):
    v = st.session_state.villagers[name]
    
    # On construit un prompt qui donne du contexte
    prompt = f"""
    Tu es {name}, {v['role']}. Traits: {v['traits']}.
    Historique récent: {v['memoire'][-3:] if v['memoire'] else "Début de journée."}
    
    Réponds UNIQUEMENT en JSON avec ce format:
    {{
        "pensee": "ce que tu penses intérieurement",
        "action": "ce que tu fais concrètement dans le village"
    }}
    """
    
    try:
        response = llm.invoke(prompt)
        # Nettoyage sommaire pour extraire le JSON
        start = response.find('{')
        end = response.rfind('}') + 1
        data = json.loads(response[start:end])
        return data
    except:
        return {"pensee": "Je suis un peu perdu...", "action": "Rêvasse près du puits"}

# --- INTERFACE ---
st.title("🏘️ Moteur de Simulation de Vie")

# Barre latérale pour le statut du monde
with st.sidebar:
    st.header("🌍 État du Monde")
    st.write(f"Tour de simulation : {st.session_state.world_step}")
    if st.button("🔄 Simuler un tour", use_container_width=True):
        for name in st.session_state.villagers:
            res = simulate_step(name)
            st.session_state.villagers[name]['memoire'].append(res['action'])
        st.session_state.world_step += 1

# Affichage des cartes des personnages
cols = st.columns(len(st.session_state.villagers))

for i, (name, data) in enumerate(st.session_state.villagers.items()):
    with cols[i]:
        st.subheader(name)
        st.caption(data['role'])
        
        # Affichage du dernier souvenir / pensée
        if data['memoire']:
            st.success(f"**Action:** {data['memoire'][-1]}")
            
        with st.expander("Voir l'historique"):
            for m in reversed(data['memoire']):
                st.write(f"- {m}")