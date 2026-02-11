"""
Phase 10: Generate multi-voice TTS audio from structured content.
Uses Google Cloud Text-to-Speech API with character-specific voices.

Each character (LYRA, specialists, Grimble) gets their own voice, speaking rate,
and pitch settings loaded from lore/audio/tts_voices.json.

NOTE: This phase uses your Google Cloud credits (not the free Gemini API).
      Skip this phase during development — the frontend can use browser-based TTS
      as a fallback until you're ready for production audio.

Requires: Phase 8 complete (needs structured/*.json files).

Usage:
    python phases/phase10/phase10_generate_tts.py                    # All books
    python phases/phase10/phase10_generate_tts.py biology             # One subject
"""

import sys
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from config import (
    STRUCTURED_DIR, VERIFIED_STRUCTURED_DIR, AUDIO_DIR,
    TTS_LANGUAGE_CODE, GOOGLE_CLOUD_PROJECT_ID,
    LORE_DIR, TTS_VOICES_PATH, BOOKS,
)


# ─── Voice Configuration ────────────────────────────────────

def _load_voice_config() -> dict:
    """Load character voice assignments from lore/audio/tts_voices.json."""
    if TTS_VOICES_PATH.exists():
        return json.loads(TTS_VOICES_PATH.read_text(encoding="utf-8"))
    return {}


def _load_world() -> dict:
    """Load world.json for subject→specialist mapping."""
    world_path = LORE_DIR / "world.json"
    if world_path.exists():
        return json.loads(world_path.read_text(encoding="utf-8"))
    return {}


def _resolve_speaker_voice(speaker_id: str, subject: str, voice_config: dict, world: dict) -> dict:
    """Resolve a speaker_id to its voice parameters.
    
    Returns dict with: voice_name, speaking_rate, pitch, voice_type
    """
    voices = voice_config.get("voice_assignments", {})
    
    # Direct character lookup (lyra, grimble)
    if speaker_id in voices:
        v = voices[speaker_id]
        return {
            "voice_name": v.get("voice_name", "en-US-Studio-O"),
            "speaking_rate": v.get("speaking_rate", 1.0),
            "pitch": v.get("pitch", 0),
            "voice_type": v.get("voice_type", "Studio"),
        }
    
    # "specialist" → resolve to actual specialist_id via world.json
    if speaker_id == "specialist":
        specialist_id = world.get("subjects", {}).get(subject, {}).get("specialist_id", "")
        if specialist_id and specialist_id in voices:
            v = voices[specialist_id]
            return {
                "voice_name": v.get("voice_name", "en-US-Journey-D"),
                "speaking_rate": v.get("speaking_rate", 1.0),
                "pitch": v.get("pitch", 0),
                "voice_type": v.get("voice_type", "Journey"),
            }
    
    # Fallback: LYRA's voice for unknown speakers
    lyra = voices.get("lyra", {})
    return {
        "voice_name": lyra.get("voice_name", "en-US-Studio-O"),
        "speaking_rate": lyra.get("speaking_rate", 1.05),
        "pitch": lyra.get("pitch", 0),
        "voice_type": lyra.get("voice_type", "Studio"),
    }


# ─── SSML Conversion ────────────────────────────────────────

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


# ─── Audio Generation ────────────────────────────────────────

def _generate_audio(client, voice_params: dict, text: str, output_path: Path):
    """Generate a single TTS audio file with character-specific voice."""
    from google.cloud import texttospeech

    if output_path.exists():
        return False  # Skip if already generated

    ssml = narrator_to_ssml(text)

    synthesis_input = texttospeech.SynthesisInput(ssml=ssml)

    voice = texttospeech.VoiceSelectionParams(
        language_code=TTS_LANGUAGE_CODE,
        name=voice_params["voice_name"],
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=voice_params["speaking_rate"],
        pitch=voice_params.get("pitch", 0),
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    with open(output_path, "wb") as f:
        f.write(response.audio_content)

    return True


# ─── Main Pipeline ───────────────────────────────────────────

def run(subject_filter: str = None):
    """Generate multi-voice TTS audio for all structured content."""
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
    voice_config = _load_voice_config()
    world = _load_world()

    if not voice_config:
        print("⚠️  No voice config found at lore/audio/tts_voices.json — using defaults")

    # Find all structured concept files (prefer verified, fallback to structured)
    subjects = [subject_filter] if subject_filter else [
        d.name for d in STRUCTURED_DIR.iterdir() if d.is_dir()
    ]

    total_chars = 0
    total_files = 0
    chars_by_speaker = {}

    for subject in subjects:
        # Prefer verified output (Phase 8.2), fallback to structured (Phase 8)
        verified_dir = VERIFIED_STRUCTURED_DIR / subject
        structured_dir = STRUCTURED_DIR / subject
        source_dir = verified_dir if verified_dir.exists() else structured_dir

        if not source_dir.exists():
            print(f"⏭️  Skipping {subject}: No structured files")
            continue

        print(f"\n{'='*60}")
        print(f"🔊 Generating multi-voice TTS: {subject}")
        print(f"{'='*60}")

        specialist_id = world.get("subjects", {}).get(subject, {}).get("specialist_id", "unknown")
        print(f"   Specialist: {specialist_id}")

        for concept_path in sorted(source_dir.glob("*.json")):
            concept = json.loads(concept_path.read_text(encoding="utf-8"))
            concept_id = concept.get("concept_id", concept_path.stem)

            audio_dir = AUDIO_DIR / subject / concept_id
            audio_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n  🎙️  {concept_id}")

            # ─── Mission briefing (LYRA's voice) ───
            briefing = concept.get("mission_briefing", {})
            if briefing.get("narrator_text"):
                speaker = briefing.get("speaker_id", "lyra")
                voice_params = _resolve_speaker_voice(speaker, subject, voice_config, world)
                generated = _generate_audio(
                    client, voice_params,
                    briefing["narrator_text"],
                    audio_dir / "mission_briefing.mp3"
                )
                if generated:
                    total_files += 1
                total_chars += len(briefing["narrator_text"])
                chars_by_speaker[speaker] = chars_by_speaker.get(speaker, 0) + len(briefing["narrator_text"])

            # ─── Level audio (specialist voice for learn, various for questions) ───
            for level in concept.get("levels", []):
                lv_num = level.get("level", "?")

                # Learn segments (usually specialist voice)
                for seg in level.get("learn_segments", []):
                    seg_id = seg.get("segment_id", f"L{lv_num}-S?")
                    narrator_text = seg.get("narrator_text", "")
                    speaker = seg.get("speaker_id", "specialist")

                    if narrator_text:
                        voice_params = _resolve_speaker_voice(speaker, subject, voice_config, world)
                        filename = f"{seg_id}.mp3"
                        generated = _generate_audio(
                            client, voice_params,
                            narrator_text,
                            audio_dir / filename
                        )
                        if generated:
                            total_files += 1
                        total_chars += len(narrator_text)
                        chars_by_speaker[speaker] = chars_by_speaker.get(speaker, 0) + len(narrator_text)

                # Pro tip audio (LYRA or specialist voice)
                for i, tip in enumerate(level.get("pro_tips", []) or []):
                    if tip.get("narrator_text"):
                        speaker = tip.get("speaker_id", "lyra")
                        voice_params = _resolve_speaker_voice(speaker, subject, voice_config, world)
                        tip_file = f"L{lv_num}-tip-{i}.mp3"
                        generated = _generate_audio(
                            client, voice_params,
                            tip["narrator_text"],
                            audio_dir / tip_file
                        )
                        if generated:
                            total_files += 1
                        total_chars += len(tip["narrator_text"])
                        chars_by_speaker[speaker] = chars_by_speaker.get(speaker, 0) + len(tip["narrator_text"])

                # Creature encounter audio (Grimble's voice for taunts)
                creature = level.get("creature_encounter")
                if creature and isinstance(creature, dict):
                    taunt = creature.get("taunt", "")
                    if taunt:
                        voice_params = _resolve_speaker_voice("grimble", subject, voice_config, world)
                        generated = _generate_audio(
                            client, voice_params,
                            taunt,
                            audio_dir / f"L{lv_num}-creature-taunt.mp3"
                        )
                        if generated:
                            total_files += 1
                        total_chars += len(taunt)
                        chars_by_speaker["grimble"] = chars_by_speaker.get("grimble", 0) + len(taunt)

                    freed = creature.get("freed_dialogue", "")
                    if freed:
                        voice_params = _resolve_speaker_voice("lyra", subject, voice_config, world)
                        generated = _generate_audio(
                            client, voice_params,
                            freed,
                            audio_dir / f"L{lv_num}-creature-freed.mp3"
                        )
                        if generated:
                            total_files += 1
                        total_chars += len(freed)
                        chars_by_speaker["lyra"] = chars_by_speaker.get("lyra", 0) + len(freed)

            print(f"     Files: {total_files}")

    # ─── Cost Summary ───
    print(f"\n{'='*60}")
    print(f"📊 TTS Summary:")
    print(f"   Total characters: {total_chars:,}")
    print(f"   Total audio files: {total_files}")
    print(f"\n   Characters by speaker:")
    for speaker, chars in sorted(chars_by_speaker.items(), key=lambda x: -x[1]):
        print(f"     {speaker}: {chars:,} chars")

    # Cost estimate: Studio voices = $16/1M chars, Journey = $16/1M chars
    estimated_cost = (total_chars / 1_000_000) * 16
    print(f"\n   Estimated cost: ${estimated_cost:.2f}")
    print(f"\n✅ Phase 10 complete!")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run(target)
