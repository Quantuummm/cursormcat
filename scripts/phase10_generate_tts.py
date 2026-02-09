"""
Phase 10: Generate TTS audio files from narrator_text in structured content.
Uses Google Cloud Text-to-Speech API. Requires Google Cloud credentials + billing.

NOTE: This phase uses your $300 Google Cloud credits (not the free Gemini API).
      Skip this phase during development — the frontend can use browser-based TTS
      as a fallback until you're ready for production audio.

Requires: Phase 8 complete (needs structured/*.json files).

Usage:
    python scripts/phase10_generate_tts.py                    # All books
    python scripts/phase10_generate_tts.py biology             # One subject
"""

import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    STRUCTURED_DIR, AUDIO_DIR,
    TTS_VOICE_NAME, TTS_LANGUAGE_CODE, TTS_SPEAKING_RATE,
    GOOGLE_CLOUD_PROJECT_ID,
)


def narrator_to_ssml(text: str) -> str:
    """Convert narrator_text with [PAUSE] markers to SSML."""
    # Escape XML special characters
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")

    # Convert [PAUSE] to SSML break
    text = re.sub(
        r'\[PAUSE\]',
        '<break time="700ms"/>',
        text
    )

    # Convert [PAUSE Xs] to specific duration
    text = re.sub(
        r'\[PAUSE (\d+)s\]',
        lambda m: f'<break time="{int(m.group(1)) * 1000}ms"/>',
        text
    )

    return f"<speak>{text}</speak>"


def run(subject_filter: str = None):
    """Generate TTS audio for all structured content."""
    try:
        from google.cloud import texttospeech
    except ImportError:
        print("❌ google-cloud-texttospeech not installed.")
        print("   Run: pip install google-cloud-texttospeech")
        return

    if not GOOGLE_CLOUD_PROJECT_ID:
        print("❌ GOOGLE_CLOUD_PROJECT_ID not set in .env")
        print("   This phase requires Google Cloud credentials.")
        print("   Skip this phase and use browser TTS during development.")
        return

    client = texttospeech.TextToSpeechClient()

    voice = texttospeech.VoiceSelectionParams(
        language_code=TTS_LANGUAGE_CODE,
        name=TTS_VOICE_NAME,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=TTS_SPEAKING_RATE,
    )

    # Find all structured concept files
    subjects = [subject_filter] if subject_filter else [
        d.name for d in STRUCTURED_DIR.iterdir() if d.is_dir()
    ]

    total_chars = 0
    total_files = 0

    for subject in subjects:
        subject_dir = STRUCTURED_DIR / subject
        if not subject_dir.exists():
            print(f"⏭️  Skipping {subject}: No structured files")
            continue

        print(f"\n{'='*60}")
        print(f"🔊 Generating TTS audio: {subject}")
        print(f"{'='*60}")

        for concept_path in sorted(subject_dir.glob("*.json")):
            concept = json.loads(concept_path.read_text(encoding="utf-8"))
            concept_id = concept.get("concept_id", concept_path.stem)

            audio_dir = AUDIO_DIR / subject / concept_id
            audio_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n  🎙️  {concept_id}")

            # Generate mission briefing audio
            briefing = concept.get("mission_briefing", {})
            if briefing.get("narrator_text"):
                _generate_audio(
                    client, voice, audio_config,
                    briefing["narrator_text"],
                    audio_dir / "mission_briefing.mp3"
                )
                total_chars += len(briefing["narrator_text"])
                total_files += 1

            # Generate level audio
            for level in concept.get("levels", []):
                lv_num = level.get("level", "?")

                for seg in level.get("learn_segments", []):
                    seg_id = seg.get("segment_id", f"L{lv_num}-S?")
                    narrator_text = seg.get("narrator_text", "")

                    if narrator_text:
                        filename = f"{seg_id}.mp3"
                        _generate_audio(
                            client, voice, audio_config,
                            narrator_text,
                            audio_dir / filename
                        )
                        total_chars += len(narrator_text)
                        total_files += 1

                # Pro tip audio
                for tip in level.get("pro_tips", []):
                    if tip.get("narrator_text"):
                        tip_file = f"L{lv_num}-tip.mp3"
                        _generate_audio(
                            client, voice, audio_config,
                            tip["narrator_text"],
                            audio_dir / tip_file
                        )
                        total_chars += len(tip["narrator_text"])
                        total_files += 1

            print(f"     Files generated: {total_files}")

    print(f"\n{'='*60}")
    print(f"📊 TTS Summary:")
    print(f"   Total characters: {total_chars:,}")
    print(f"   Total audio files: {total_files}")
    estimated_cost = (total_chars / 1_000_000) * 16  # $16 per 1M chars for Neural2
    print(f"   Estimated cost: ${estimated_cost:.2f}")
    print(f"\n✅ Phase 10 complete!")


def _generate_audio(client, voice, audio_config, text, output_path):
    """Generate a single TTS audio file."""
    from google.cloud import texttospeech

    if output_path.exists():
        return  # Skip if already generated

    ssml = narrator_to_ssml(text)

    synthesis_input = texttospeech.SynthesisInput(ssml=ssml)

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    with open(output_path, "wb") as f:
        f.write(response.audio_content)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run(target)
