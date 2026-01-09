import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("GOOGLE_API_KEY")

print(f"Testing with Key: {KEY[:5]}...")
client = genai.Client(api_key=KEY)

MODELS_TO_TEST = [
    "models/gemini-3-flash-preview", 
    "gemini-3-flash-preview",
    "gemini-2.0-flash-exp"
]

for m in MODELS_TO_TEST:
    print(f"\n--- Testing: {m} ---")
    try:
        response = client.models.generate_content(
            model=m, 
            contents="Hello, are you there?"
        )
        print(f"SUCCESS! Response: {response.text[:50]}...")
    except Exception as e:
        print(f"FAILED: {e}")
