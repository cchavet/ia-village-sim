from google import genai
import os

try:
    with open("api.key", "r") as f:
        api_key = f.read().strip()
    
    client = genai.Client(api_key=api_key)
    print("Listing models with google-genai SDK:")
    # Pager through list_models
    for m in client.models.list():
        # The object structure might have .name or .display_name
        # The new SDK returns Model objects.
        print(f" - {m.name}")

except Exception as e:
    print(f"Error: {e}")
