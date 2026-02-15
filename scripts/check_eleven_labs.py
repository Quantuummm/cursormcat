import requests
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")
API_KEY = os.getenv("ELEVENLABS_API_KEY")

def list_voices():
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {
        "xi-api-key": API_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        voices = response.json()["voices"]
        for voice in voices:
            if "Jessica" in voice["name"]:
                print(f"Voice Name: {voice['name']}, ID: {voice['voice_id']}")
    else:
        print(f"Error listing voices: {response.text}")

def list_models():
    url = "https://api.elevenlabs.io/v1/models"
    headers = {
        "xi-api-key": API_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        models = response.json()
        for model in models:
            if "v3" in model["model_id"].lower() or "v3" in model["name"].lower():
                print(f"Model ID: {model['model_id']}, Name: {model['name']}")
    else:
        print(f"Error listing models: {response.text}")

if __name__ == "__main__":
    print("--- Voices ---")
    list_voices()
    print("\n--- Models ---")
    list_models()
