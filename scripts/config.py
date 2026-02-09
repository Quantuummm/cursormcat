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
# Multi-model strategy optimized for BEST quality:
#
# gemini-2.5-flash:       Smart, 65K output. Best for PDF EXTRACTION (reads copyrighted text).
# gemini-3-flash-preview: NEWEST, best reasoning. Best for GENERATION (restructuring, questions).
#
# Gemini 3 has stricter copyright filters and refuses to extract verbatim from textbooks.
# So we use 2.5 for all extraction (Phases 1-5) and 3 for all generation (Phases 6-9).
GEMINI_MODEL_EXTRACT = "gemini-2.5-flash"          # Extraction from PDFs (reads copyrighted material)
GEMINI_MODEL_GENERATE = "gemini-3-flash-preview"   # Generation tasks (restructuring, enrichment, questions)

# Aliases used by the GeminiClient
GEMINI_MODEL_LIGHT = GEMINI_MODEL_EXTRACT    # Light = extraction tasks
GEMINI_MODEL_HEAVY = GEMINI_MODEL_EXTRACT    # Heavy extraction also uses 2.5 (copyright-safe)
GEMINI_MODEL_CREATIVE = GEMINI_MODEL_GENERATE  # Creative = generation tasks

# Legacy alias
GEMINI_MODEL = GEMINI_MODEL_EXTRACT

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
# Free tier: 15 RPM, 1M tokens/min for Gemini 2.0 Flash
GEMINI_REQUESTS_PER_MINUTE = 14   # Stay just under limit
GEMINI_DELAY_BETWEEN_REQUESTS = 60 / GEMINI_REQUESTS_PER_MINUTE  # ~4.3 seconds

# ─── TTS Settings (Google Cloud Text-to-Speech) ────────────
TTS_VOICE_NAME = "en-US-Journey-F"         # Natural neural voice
TTS_LANGUAGE_CODE = "en-US"
TTS_SPEAKING_RATE = 1.0
TTS_AUDIO_ENCODING = "MP3"
