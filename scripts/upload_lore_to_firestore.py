"""Upload lore JSON files to Firestore game_config collection."""
import os, json, sys
from pathlib import Path

os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS",
    r"C:\Users\Rauf\AppData\Roaming\Code\CloudKey.json")

from google.cloud import firestore

LORE_DIR = Path(__file__).resolve().parent.parent / "lore"
db = firestore.Client()

def upload_json(collection, doc_id, file_path):
    """Upload a JSON file as a Firestore document."""
    with open(file_path, encoding='utf-8') as f:
        data = json.load(f)
    db.collection(collection).document(doc_id).set(data)
    print(f"  ✅ {collection}/{doc_id} ({file_path.name})")

def main():
    print("Uploading lore data to Firestore...\n")
    
    # Top-level lore files
    for name in ["world", "creatures"]:
        fp = LORE_DIR / f"{name}.json"
        if fp.exists():
            upload_json("game_config", name, fp)
    
    # Characters
    for fp in (LORE_DIR / "characters").glob("*.json"):
        upload_json("game_config", f"character_{fp.stem}", fp)
    
    # Planets
    for fp in (LORE_DIR / "planets").glob("*.json"):
        upload_json("game_config", f"planet_{fp.stem}", fp)
    
    # Audio config
    for fp in (LORE_DIR / "audio").glob("*.json"):
        upload_json("game_config", f"audio_{fp.stem}", fp)
    
    # Systems config
    for fp in (LORE_DIR / "systems").glob("*.json"):
        upload_json("game_config", f"system_{fp.stem}", fp)
    
    print(f"\nDone! All lore data uploaded to game_config collection.")

if __name__ == "__main__":
    main()
