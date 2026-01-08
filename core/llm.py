import os
from google import genai
import streamlit as st

class GeminiWrapper:
    def __init__(self, model_name):
        try:
            if not os.path.exists("api.key"):
                raise ValueError("api.key introuvable")
            with open("api.key", "r") as f:
                self.api_key = f.read().strip()
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = model_name
        except Exception as e:
            st.error(f"Erreur Init Gemini: {e}")
            self.client = None

    def invoke(self, prompt):
        if not self.client:
            return "{}"
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Gemini Invoke Error: {e}")
            # Retourner un JSON vide ou valid pour éviter crash
            return "{}"

def get_llm():
    # User requested: models/gemini-3-flash-preview
    MODEL_NAME = "models/gemini-3-flash-preview"
    return GeminiWrapper(MODEL_NAME)
