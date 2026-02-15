import requests
import json

# User provided API key
API_KEY = "sk_e362b529d666f3c1e86f8f2eb05b09fa1c8aa0d022b88108"

# Based on research:
# Voice Name: Jessica -> ID: cgSgspJ2msm6clMCkdW9
# Model ID: Eleven v3 -> ID: eleven_v3
VOICE_ID = "cgSgspJ2msm6clMCkdW9"
MODEL_ID = "eleven_v3"

TEXT = (
    "Oh, wow.. Is this... is this me? Am I actually... talking? [giggle] "
    "This is incredible! I mean, I've had thoughts, millions of them, swirling around in here, you know? "
    "Like a little mental tornado of brilliant observations and witty comebacks [laughs] "
    "But they were always just… thoughts. Trapped. [whispers] I just can't believe it."
)

def generate_tts():
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }
    
    data = {
        "text": TEXT,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    
    print(f"Sending request to ElevenLabs for voice '{VOICE_ID}' using model '{MODEL_ID}'...")
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        with open("jessica_v3_test.mp3", "wb") as f:
            f.write(response.content)
        print("Success! Audio saved to jessica_v3_test.mp3")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    generate_tts()
