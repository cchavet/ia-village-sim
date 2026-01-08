import subprocess
import streamlit as st
from langchain_ollama import OllamaLLM

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

def get_llm():
    MODEL_NAME = "mistral-nemo"
    check_and_pull_model(MODEL_NAME)
    return OllamaLLM(model=MODEL_NAME, temperature=0.7, format="json")
