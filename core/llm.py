import os
import requests
import json
import streamlit as st
import subprocess
import atexit

class OllamaResponse:
    def __init__(self, text):
        self.text = text

# LIFECYCLE MANAGEMENT
def check_ollama_running():
    try:
        requests.get("http://localhost:11434")
        return True
    except:
        return False

def ensure_model_ready(model_name):
    """
    Vérifie si le modèle existe, sinon le télécharge via 'ollama pull'.
    """
    if not check_ollama_running():
        st.error("Ollama n'est pas lancé ! (http://localhost:11434 inaccessible)")
        return False

    # Check existence via API tags
    try:
        r = requests.get("http://localhost:11434/api/tags")
        if r.status_code == 200:
            models = [m['name'] for m in r.json().get('models', [])]
            # Handle tags (e.g. "gemma:latest" matches "gemma")
            if model_name not in models and f"{model_name}:latest" not in models:
                st.warning(f"Modèle '{model_name}' introuvable. Tentative de téléchargement...")
                
                # Stream Pull
                process = subprocess.Popen(
                    ["ollama", "pull", model_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                # Show Spinner/Progress?
                with st.spinner(f"Téléchargement de {model_name} en cours... (Cela peut prendre du temps)"):
                    stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    st.error(f"Echec du téléchargement : {stderr}")
                    return False
                
                st.success(f"Modèle {model_name} installé !")
            return True
    except Exception as e:
        st.error(f"Erreur vérification modèle: {e}")
        return False

def unload_model_on_exit(model_name):
    """Libère la VRAM à la fermeture"""
    try:
        payload = {"model": model_name, "keep_alive": 0}
        requests.post("http://localhost:11434/api/generate", json=payload)
        print(f"Modèle {model_name} déchargé (Exit).")
    except:
        pass

class OllamaWrapper:
    def __init__(self, model_name):
        self.model_name = model_name
        # Self-reference to mimic client.models.generate_content
        self.models = self 
        self.api_url = "http://localhost:11434/api/generate"

    def invoke(self, prompt):
        """Interface simple pour le moteur de jeu"""
        return self.generate_content(model=self.model_name, contents=prompt).text

    def generate_content(self, model, contents):
        """Mimics Google GenAI generate_content"""
        # Model override allowed, but usually we stick to init model
        target_model = model if model else self.model_name
        
        payload = {
            "model": target_model,
            "prompt": contents,
            "stream": False
        }
        try:
            r = requests.post(self.api_url, json=payload)
            r.raise_for_status()
            res_json = r.json()
            return OllamaResponse(res_json.get('response', ''))
        except Exception as e:
            print(f"Ollama Error: {e}")
            return OllamaResponse("")

    def generate_content_stream(self, model, contents):
        """Mimics Google GenAI generate_content_stream"""
        target_model = model if model else self.model_name
        payload = {
            "model": target_model,
            "prompt": contents,
            "stream": True
        }
        try:
            with requests.post(self.api_url, json=payload, stream=True) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        try:
                            json_obj = json.loads(line)
                            chunk = json_obj.get('response', '')
                            if chunk:
                                # Mimic chunk object with .text
                                yield type('Chunk', (), {'text': chunk})
                        except:
                            pass
        except Exception as e:
            yield type('Chunk', (), {'text': f"[Error Local: {e}]"})

def get_llm():
    # User requested local: Gemma 3 (4B)
    # Correct Ollama Tag: gemma3:4b
    MODEL_NAME = "gemma3:4b"
    
    # LIFECYCLE CHECK And PULL
    # Only check once per session to avoid sluggishness on reruns, 
    # but since st.session_state is not avail here strictly (or creates circular deps), 
    # we just run it. It's fast if model exists.
    if ensure_model_ready(MODEL_NAME):
        # Register Cleanup
        atexit.register(unload_model_on_exit, MODEL_NAME)
        return OllamaWrapper(MODEL_NAME)
    else:
        st.error(f"Impossible d'utiliser le modèle {MODEL_NAME}.")
        return None
