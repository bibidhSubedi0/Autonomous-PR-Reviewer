import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("No API Key found.")
    exit()

genai.configure(api_key=api_key)

print(f"Models : {api_key[:5]}")

try:
    print("\nAvailable Models:")
    found_any = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"   - {m.name}")
            found_any = True
    
    if not found_any:
        print("No models found! (Is your API key restricted?)")

except Exception as e:
    print(f"Error listing models: {e}")