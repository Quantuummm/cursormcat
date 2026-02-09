"""
Central configuration for the MCAT Content Pipeline.
All paths, API settings, and book definitions live here.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Fix Windows terminal encoding for emoji/unicode output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ─── API Keys ───────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_CLOUD_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "")

# ─── Gemini Model Settings ──────────────────────────────────
# Strategy: Try Gemini 3 Flash first (best quality). If it fails
# (copyright block, rate limit, etc.), fall back to 2.5 Flash.
#
# For PDF extraction: Gemini 3 blocks copyrighted text, so extraction
# methods start with 2.5 Flash directly (known to work).
# For generation (no PDF): Gemini 3 first, fallback to 2.5.
GEMINI_MODEL_PRIMARY = "gemini-3-flash-preview"   # Best quality, try first
GEMINI_MODEL_FALLBACK = "gemini-2.5-flash"         # Reliable fallback
GEMINI_MODEL_EXTRACT = "gemini-2.5-flash"          # PDF extraction (copyright-safe)

# Legacy aliases used by scripts
GEMINI_MODEL_LIGHT = GEMINI_MODEL_EXTRACT
GEMINI_MODEL_HEAVY = GEMINI_MODEL_EXTRACT
GEMINI_MODEL_CREATIVE = GEMINI_MODEL_PRIMARY
GEMINI_MODEL = GEMINI_MODEL_EXTRACT

GEMINI_TEMPERATURE_EXTRACT = 0.1           # Low creativity for faithful extraction
GEMINI_TEMPERATURE_RESTRUCTURE = 0.4       # Creative for ADHD-friendly question wording
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
# Update filenames here to match your actual PDF names in pdfs/
BOOKS = {
    "MCAT Biology Review.pdf":                  "biology",
    "MCAT Biochemistry Review.pdf":             "biochemistry",
    "MCAT General Chemistry Review.pdf":        "gen_chem",
    "MCAT Organic Chemistry Review.pdf":        "org_chem",
    "MCAT Physics and Math Review.pdf":         "physics",
    "MCAT Behavioral Sciences Review.pdf":      "psych_soc",
    "MCAT Critical Analysis Review.pdf":        "cars",
}

# ─── Rate Limiting (Gemini free tier) ───────────────────────
GEMINI_REQUESTS_PER_MINUTE = 14   # Stay under 15 RPM free tier limit
GEMINI_DELAY_BETWEEN_REQUESTS = 60 / GEMINI_REQUESTS_PER_MINUTE  # ~4.3 seconds

# ─── TTS Settings (Google Cloud Text-to-Speech) ────────────
TTS_VOICE_NAME = "en-US-Journey-F"         # Natural neural voice
TTS_LANGUAGE_CODE = "en-US"
TTS_SPEAKING_RATE = 1.0
TTS_AUDIO_ENCODING = "MP3"
