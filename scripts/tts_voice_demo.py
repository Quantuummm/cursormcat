#!/usr/bin/env python3
"""
TTS Voice Demo — Chirp3-HD Premium Voices
==========================================
Generates one MP3 per character using Google Cloud Chirp3-HD voices.
Each character speaks a line in their unique style from the game lore.

Also generates a combined "all_voices_demo.mp3" stitched together.

Usage:
    Set GOOGLE_APPLICATION_CREDENTIALS env var to your CloudKey.json path
    python scripts/tts_voice_demo.py
"""

import os
import sys
import struct
from pathlib import Path
from google.cloud import texttospeech

# ─── Output directory ─────────────────────────────────
OUT_DIR = Path(__file__).resolve().parent.parent / "demo_voices"
OUT_DIR.mkdir(exist_ok=True)

# ─── Character voice definitions (Chirp3-HD) ─────────
CHARACTERS = [
    {
        "id": "lyra",
        "name": "LYRA — Ship AI & Narrator",
        "voice": "en-US-Chirp3-HD-Aoede",
        "speaking_rate": 1.05,
        "pitch": 0.0,
        "line": "Commander, your neural map is rebuilding. "
                "Let's reinforce this pathway. "
                "The citric acid cycle begins when acetyl-CoA "
                "combines with oxaloacetate to form citrate. "
                "Strong recall starts here.",
    },
    {
        "id": "grimble",
        "name": "Grimble — The Eternal Dusk (Villain)",
        "voice": "en-US-Chirp3-HD-Fenrir",
        "speaking_rate": 0.9,
        "pitch": -2.0,
        "line": "Foolish Commander! You think a few correct answers "
                "can push back my darkness? "
                "My fog will swallow every synapse you've rebuilt. "
                "Enjoy your little victory... while it lasts.",
    },
    {
        "id": "dr_calder",
        "name": "Dr. Pax 'Cal' Calder — Gen Chem Specialist",
        "voice": "en-US-Chirp3-HD-Puck",
        "speaking_rate": 1.15,
        "pitch": 1.0,
        "line": "OKAY Commander, this is the good stuff! "
                "Electron orbitals are like apartments. "
                "Each one has a max capacity, and electrons "
                "fill from the ground floor up. "
                "Isn't that AMAZING?",
    },
    {
        "id": "dr_kade",
        "name": "Dr. Imani Kade — Biology Specialist",
        "voice": "en-US-Chirp3-HD-Kore",
        "speaking_rate": 1.0,
        "pitch": 0.0,
        "line": "Let's zoom out for a second, Commander. "
                "Every cell in your body has the same D-N-A. "
                "The difference is which genes are turned on. "
                "Think of it like a library — same books, "
                "different chapters open.",
    },
    {
        "id": "dr_vale",
        "name": "Dr. Rowan Vale — Biochemistry Specialist",
        "voice": "en-US-Chirp3-HD-Enceladus",
        "speaking_rate": 1.0,
        "pitch": -1.0,
        "line": "Here is the beautiful thing about the citric acid cycle. "
                "Every step produces something the next step needs. "
                "It is a factory with zero waste. "
                "Elegant, efficient, optimized.",
    },
    {
        "id": "dr_finch",
        "name": "Dr. Elara Finch — Org Chem Specialist",
        "voice": "en-US-Chirp3-HD-Achernar",
        "speaking_rate": 1.1,
        "pitch": 1.0,
        "line": "Alright Commander, we have a mystery! "
                "This molecule has a leaving group and "
                "a nucleophile nearby. "
                "Follow the curved arrows — they always tell you "
                "where the electrons went.",
    },
    {
        "id": "cmdr_voss",
        "name": "Cmdr. Mara Voss — Physics Specialist",
        "voice": "en-US-Chirp3-HD-Sulafat",
        "speaking_rate": 1.0,
        "pitch": -1.0,
        "line": "Newton's second law. "
                "F equals m a. "
                "Force equals mass times acceleration. "
                "Know it. Use it. It solves half your problems.",
    },
    {
        "id": "dr_solomon",
        "name": "Dr. Nia Solomon — Psych/Soc Specialist",
        "voice": "en-US-Chirp3-HD-Laomedeia",
        "speaking_rate": 0.95,
        "pitch": 0.0,
        "line": "Let's make this real, Commander. "
                "Imagine you see someone trip in public. "
                "Your first thought — is it their fault or the sidewalk's? "
                "That snap judgment is the fundamental attribution error.",
    },
    {
        "id": "prof_rhee",
        "name": "Prof. Adrian Rhee — CARS Specialist",
        "voice": "en-US-Chirp3-HD-Umbriel",
        "speaking_rate": 0.95,
        "pitch": 0.0,
        "line": "Before you touch the questions, Commander. "
                "Read the first and last paragraph. "
                "Find the author's central claim. "
                "Everything — every question, every answer — "
                "flows from that thesis.",
    },
]


def generate_voice(client, char: dict) -> Path:
    """Generate a single character's demo MP3."""
    print(f"  🎙️  {char['name']}")
    print(f"      Voice: {char['voice']}")
    print(f"      Line: \"{char['line'][:60]}...\"")

    synthesis_input = texttospeech.SynthesisInput(text=char["line"])

    voice_params = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name=char["voice"],
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=char["speaking_rate"],
        pitch=char["pitch"],
    )

    try:
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config,
        )
    except Exception as e:
        # If pitch/rate not supported for Chirp3-HD, retry without them
        print(f"      ⚠️  Retrying without pitch/rate adjustments: {e}")
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
        )
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config,
        )

    out_path = OUT_DIR / f"{char['id']}_chirp3hd_demo.mp3"
    out_path.write_bytes(response.audio_content)
    size_kb = len(response.audio_content) / 1024
    print(f"      ✅ Saved: {out_path.name} ({size_kb:.1f} KB)")
    return out_path


def combine_mp3s(files: list[Path], output: Path):
    """Concatenate MP3 files into a single demo file."""
    with open(output, "wb") as out_f:
        for f in files:
            out_f.write(f.read_bytes())
    size_kb = output.stat().st_size / 1024
    print(f"\n  📦 Combined demo: {output.name} ({size_kb:.1f} KB)")


def main():
    # Verify credentials
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not Path(creds_path).exists():
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set or file not found!")
        print("   Set it with:")
        print("   $env:GOOGLE_APPLICATION_CREDENTIALS = '<path-to-CloudKey.json>'")
        sys.exit(1)

    print(f"🔑 Using credentials: {creds_path}")
    print(f"📁 Output directory: {OUT_DIR}\n")

    client = texttospeech.TextToSpeechClient()
    print("=" * 60)
    print("  MCAT MASTERY — Chirp3-HD Voice Demo")
    print("  9 Characters × Premium Google Voices")
    print("=" * 60 + "\n")

    generated_files = []
    total_chars = 0

    for char in CHARACTERS:
        try:
            path = generate_voice(client, char)
            generated_files.append(path)
            total_chars += len(char["line"])
        except Exception as e:
            print(f"      ❌ FAILED: {e}")
        print()

    # Combine all into one demo
    if generated_files:
        combined_path = OUT_DIR / "all_voices_demo.mp3"
        combine_mp3s(generated_files, combined_path)

    # Summary
    print("\n" + "=" * 60)
    print("  DEMO SUMMARY")
    print("=" * 60)
    print(f"  Characters generated: {len(generated_files)}/{len(CHARACTERS)}")
    print(f"  Total characters synthesized: {total_chars:,}")
    print(f"  Estimated cost: ${total_chars * 100 / 1_000_000:.4f}")
    print(f"  Output location: {OUT_DIR}")
    print()
    print("  Files:")
    for f in generated_files:
        print(f"    • {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    if generated_files:
        combined = OUT_DIR / "all_voices_demo.mp3"
        if combined.exists():
            print(f"    • {combined.name} ({combined.stat().st_size / 1024:.1f} KB)  ← PLAY THIS ONE")
    print("\n  🎧 Open demo_voices/ folder and play all_voices_demo.mp3 to audition!")
    print("  💰 These are Chirp3-HD ($100/1M chars) — the best Google has.")
    print("  💳 Charged to GCP credits (not your card).\n")


if __name__ == "__main__":
    main()
