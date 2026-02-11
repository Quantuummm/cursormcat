"""
Central configuration for the MCAT Content Pipeline.
All paths, API settings, and book definitions live here.
"""

# NOTE: Updated in second workflow (Feb 9, 2026).

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
# Gemini 3 is now the default for ALL phases (0-11).
# Fallback is ALWAYS Gemini 2.5 Flash Latest.
GEMINI_MODEL_PRIMARY = "gemini-3-flash-preview"   # Best quality, try first
GEMINI_MODEL_FALLBACK = "gemini-2.5-flash"         # Reliable fallback
GEMINI_MODEL_EXTRACT = "gemini-3-flash-preview"   # Now using Gemini 3 first for extraction

# Legacy aliases used by scripts
GEMINI_MODEL_LIGHT = GEMINI_MODEL_PRIMARY
GEMINI_MODEL_HEAVY = GEMINI_MODEL_PRIMARY
GEMINI_MODEL_CREATIVE = GEMINI_MODEL_PRIMARY
GEMINI_MODEL = GEMINI_MODEL_PRIMARY

GEMINI_TEMPERATURE_EXTRACT = 0.1           # Low creativity for faithful extraction
GEMINI_TEMPERATURE_RESTRUCTURE = 0.4       # Creative for ADHD-friendly question wording
GEMINI_TEMPERATURE_ENRICH = 0.3            # Moderate for explanations

# ─── Paths ──────────────────────────────────────────────────
PDFS_DIR = PROJECT_ROOT / "pdfs"

# Per-phase outputs: each phase writes its outputs beneath its own folder
# e.g., Phase 0 → phases/phase0/output/assets, Phase 1 → phases/phase1/output/extracted
ASSETS_DIR = PROJECT_ROOT / "phases" / "phase0" / "output" / "assets"
TOC_DIR = PROJECT_ROOT / "phases" / "phase1" / "output" / "extracted"
EXTRACTED_DIR = TOC_DIR  # Legacy handle for Phase 1 TOC

ASSESSMENTS_DIR = PROJECT_ROOT / "phases" / "phase2" / "output" / "extracted"
SECTIONS_DIR = PROJECT_ROOT / "phases" / "phase3" / "output" / "extracted"
GLOSSARY_DIR = PROJECT_ROOT / "phases" / "phase4" / "output" / "extracted"
FIGURE_CATALOG_DIR = PROJECT_ROOT / "phases" / "phase5" / "output" / "extracted"
ENRICHED_ASSESSMENTS_DIR = PROJECT_ROOT / "phases" / "phase6" / "output"
VERIFIED_ASSESSMENTS_DIR = PROJECT_ROOT / "phases" / "phase6_1" / "output" / "verified"
TEMP_VERIFICATION_DIR = PROJECT_ROOT / "phases" / "phase6_1" / "output" / "temp"

CLASSIFIED_DIR = PROJECT_ROOT / "phases" / "phase7_legacy" / "output" / "classified"
STRUCTURED_DIR = PROJECT_ROOT / "phases" / "phase8" / "output" / "structured"
VERIFIED_STRUCTURED_DIR = PROJECT_ROOT / "phases" / "phase8_2" / "output" / "verified"
COMPILED_DIR = PROJECT_ROOT / "phases" / "phase8_1" / "output" / "compiled"
PRIMITIVES_DIR = PROJECT_ROOT / "phases" / "phase7" / "output" / "primitives"
LORE_DIR = PROJECT_ROOT / "lore"
BRIDGES_DIR = PROJECT_ROOT / "phases" / "phase9" / "output" / "bridges"
AUDIO_DIR = PROJECT_ROOT / "phases" / "phase10" / "output" / "audio"
PROMPTS_DIR = Path(__file__).parent / "prompts"  # legacy prompts folder (phase-level prompts also exist)

# Note: After running `scripts/migrate_outputs_to_phases.py` (dry-run first),
# the old top-level folders (assets, extracted, classified, ...) will be moved
# into their respective phase output locations above.

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
    "MCAT Critical Analysis and Reasoning Skills Review.pdf": "cars",
}

# ─── Rate Limiting (Gemini free tier) ───────────────────────
GEMINI_REQUESTS_PER_MINUTE = 14   # Stay under 15 RPM free tier limit
GEMINI_DELAY_BETWEEN_REQUESTS = 60 / GEMINI_REQUESTS_PER_MINUTE  # ~4.3 seconds
# Per-request timeout (seconds) for Gemini API calls. Increased for heavy extraction.
GEMINI_API_TIMEOUT = int(os.getenv("GEMINI_API_TIMEOUT", "600"))

# Shared interrupt state to allow graceful shutdown across modules
INTERRUPT_REQUESTED = False

# ─── TTS Settings (Google Cloud Text-to-Speech) ────────────
# Multi-voice TTS: voice assignments loaded from lore/audio/tts_voices.json at runtime.
# These defaults are fallbacks only — Phase 10 reads per-character settings from tts_voices.json.
TTS_VOICE_NAME = "en-US-Studio-O"          # Default: LYRA's voice
TTS_LANGUAGE_CODE = "en-US"
TTS_SPEAKING_RATE = 1.05                    # LYRA's default speaking rate
TTS_AUDIO_ENCODING = "MP3"

# ─── Lore Subdirectories ────────────────────────────────────
LORE_CHARACTERS_DIR = LORE_DIR / "characters"
LORE_PLANETS_DIR = LORE_DIR / "planets"
LORE_SYSTEMS_DIR = LORE_DIR / "systems"
LORE_AUDIO_DIR = LORE_DIR / "audio"
TTS_VOICES_PATH = LORE_AUDIO_DIR / "tts_voices.json"
