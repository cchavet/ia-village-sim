import os
from google import genai
from dotenv import load_dotenv

# Load Env (API Key)
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("FATAL: Clé API Google manquante dans le fichier .env !")

class GeminiWrapper:
    def __init__(self, model_name="models/gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.client = None
        if API_KEY:
            try:
                self.client = genai.Client(api_key=API_KEY)
            except Exception as e:
                print(f"Erreur Client GenAI: {e}")
        
        # Compatibility layer for storybook.py (client.models.generate_content)
        self.models = self 

    def invoke(self, prompt):
        """Interface simple Synchrone (pour characters.py)"""
        if not self.client: return "No Client"
        try:
            response = self.client.models.generate_content(
                model=self.model_name, 
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"[Erreur GenAI: {e}]"

    def generate_content(self, model, contents):
        """Compatibilité avec storybook.py"""
        if not self.client: return type('Response', (), {'text': "No Client"})
        
        target = model if model else self.model_name
        try:
            return self.client.models.generate_content(
                model=target,
                contents=contents
            )
        except Exception as e:
            return type('Response', (), {'text': f"[Erreur: {e}]"})

    def generate_content_stream(self, model, contents):
        """Streaming"""
        if not self.client: 
            yield type('Chunk', (), {'text': "No Client"})
            return

        target = model if model else self.model_name
        try:
            # New SDK might return an iterator directly
            for chunk in self.client.models.generate_content_stream(model=target, contents=contents):
                yield chunk
        except Exception as e:
            yield type('Chunk', (), {'text': f"[Erreur Stream: {e}]"})

def get_llm():
    # Model: Gemini 3 Flash Preview (Requis par User)
    MODEL_NAME = "models/gemini-3-flash-preview"
    
    return GeminiWrapper(MODEL_NAME)
