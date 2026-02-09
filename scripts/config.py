"""
Central configuration for the MCAT Content Pipeline.
All paths, API settings, and book definitions live here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ─── API Keys ───────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_CLOUD_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "")

# ─── Gemini Model Settings ──────────────────────────────────
GEMINI_MODEL = "gemini-2.0-flash"          # Best balance of speed/cost/quality
GEMINI_TEMPERATURE_EXTRACT = 0.1           # Low creativity for faithful extraction
GEMINI_TEMPERATURE_RESTRUCTURE = 0.4       # Slightly more creative for question wording
GEMINI_TEMPERATURE_ENRICH = 0.3            # Moderate for explanations

# ─── Paths ──────────────────────────────────────────────────
PDFS_DIR = PROJECT_ROOT / "pdfs"
ASSETS_DIR = PROJECT_ROOT / "assets"
EXTRACTED_DIR = PROJECT_ROOT / "extracted"
CLASSIFIED_DIR = PROJECT_ROOT / "classified"
STRUCTURED_DIR = PROJECT_ROOT / "structured"
BRIDGES_DIR = PROJECT_ROOT / "bridges"
AUDIO_DIR = PROJECT_ROOT / "audio"
PROMPTS_DIR = Path(__file__).parent / "prompts"

# ─── Book Definitions ───────────────────────────────────────
# Map each PDF filename to its subject slug
BOOKS = {
    "biology.pdf":         "biology",
    "biochemistry.pdf":    "biochemistry",
    "gen_chem.pdf":        "gen_chem",
    "org_chem.pdf":        "org_chem",
    "physics.pdf":         "physics",
    "psych_soc.pdf":       "psych_soc",
    "cars.pdf":            "cars",
}

# ─── Rate Limiting (Gemini free tier) ───────────────────────
# Free tier: 15 RPM, 1M tokens/min for Gemini 2.0 Flash
GEMINI_REQUESTS_PER_MINUTE = 14   # Stay just under limit
GEMINI_DELAY_BETWEEN_REQUESTS = 60 / GEMINI_REQUESTS_PER_MINUTE  # ~4.3 seconds

# ─── TTS Settings (Google Cloud Text-to-Speech) ────────────
TTS_VOICE_NAME = "en-US-Journey-F"         # Natural neural voice
TTS_LANGUAGE_CODE = "en-US"
TTS_SPEAKING_RATE = 1.0
TTS_AUDIO_ENCODING = "MP3"
