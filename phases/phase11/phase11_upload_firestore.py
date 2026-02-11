"""
Phase 11: Upload all processed data to Firebase Firestore.
This is the final phase — pushes everything to the cloud database.

Uploads:
  1. Concepts (guided learning missions) — from Phase 8/8.2
  2. Glossaries — from Phase 4
  3. Assessments — from Phase 2/6
  4. Equations — from Phase 3
  5. Figures — from Phase 5
  6. Bridge Missions — from Phase 9
  7. Game modes (compiled) — from Phase 8.1
  8. Game world config — from lore/
  9. Characters (LYRA, specialists, commanders, Grimble) — from lore/
  10. Planets — from lore/
  11. Creatures — from lore/
  12. Game systems (resonance, economy, energy, streaks, fog, progression) — from lore/
  13. Audio/TTS voice config — from lore/

NOTE: Requires Firebase project setup and service account credentials.
      Set GOOGLE_APPLICATION_CREDENTIALS in .env to your service account JSON path.

Usage:
    python phases/phase11/phase11_upload_firestore.py                # Upload everything
    python phases/phase11/phase11_upload_firestore.py biology         # One subject
    python phases/phase11/phase11_upload_firestore.py --dry-run       # Preview without uploading
    python phases/phase11/phase11_upload_firestore.py --lore-only     # Only upload lore/game data
"""

import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from config import (
    EXTRACTED_DIR, STRUCTURED_DIR, VERIFIED_STRUCTURED_DIR, COMPILED_DIR,
    BRIDGES_DIR, BOOKS, GOOGLE_CLOUD_PROJECT_ID,
    LORE_DIR, LORE_CHARACTERS_DIR, LORE_PLANETS_DIR, LORE_SYSTEMS_DIR, LORE_AUDIO_DIR,
)


def _upload_doc(db, collection: str, doc_id: str, data: dict, dry_run: bool):
    """Upload a single document to Firestore."""
    if not dry_run:
        db.collection(collection).document(doc_id).set(data)


def _upload_lore(db, dry_run: bool) -> dict:
    """Upload all lore/game configuration data to Firestore."""
    counters = {"world": 0, "characters": 0, "planets": 0, "creatures": 0, "systems": 0, "audio": 0}

    # ── World config ────────────────────────────────────────
    world_path = LORE_DIR / "world.json"
    if world_path.exists():
        world = json.loads(world_path.read_text(encoding="utf-8"))
        _upload_doc(db, "game_config", "world", world, dry_run)
        counters["world"] = 1
        print(f"  🌍 World config uploaded")

    # ── Characters ──────────────────────────────────────────
    if LORE_CHARACTERS_DIR.exists():
        for char_file in sorted(LORE_CHARACTERS_DIR.glob("*.json")):
            char_data = json.loads(char_file.read_text(encoding="utf-8"))
            doc_id = char_file.stem  # lyra, grimble, commanders, specialists
            _upload_doc(db, "characters", doc_id, char_data, dry_run)
            counters["characters"] += 1
            print(f"  👤 Character: {doc_id}")

    # ── Planets ─────────────────────────────────────────────
    if LORE_PLANETS_DIR.exists():
        for planet_file in sorted(LORE_PLANETS_DIR.glob("*.json")):
            planet_data = json.loads(planet_file.read_text(encoding="utf-8"))
            doc_id = planet_file.stem  # verdania, glycera, etc. or index
            _upload_doc(db, "planets", doc_id, planet_data, dry_run)
            counters["planets"] += 1
            print(f"  🪐 Planet: {doc_id}")

    # ── Creatures ───────────────────────────────────────────
    creatures_path = LORE_DIR / "creatures.json"
    if creatures_path.exists():
        creatures = json.loads(creatures_path.read_text(encoding="utf-8"))
        _upload_doc(db, "game_config", "creatures", creatures, dry_run)
        counters["creatures"] = 1
        print(f"  🐉 Creatures uploaded")

    # ── Game systems ────────────────────────────────────────
    if LORE_SYSTEMS_DIR.exists():
        for sys_file in sorted(LORE_SYSTEMS_DIR.glob("*.json")):
            sys_data = json.loads(sys_file.read_text(encoding="utf-8"))
            doc_id = sys_file.stem  # resonance, economy, energy, streaks, fog, progression
            _upload_doc(db, "game_systems", doc_id, sys_data, dry_run)
            counters["systems"] += 1
            print(f"  ⚙️  System: {doc_id}")

    # ── Audio/TTS config ────────────────────────────────────
    if LORE_AUDIO_DIR.exists():
        for audio_file in sorted(LORE_AUDIO_DIR.glob("*.json")):
            audio_data = json.loads(audio_file.read_text(encoding="utf-8"))
            doc_id = audio_file.stem  # music_and_sfx, tts_voices
            _upload_doc(db, "audio_config", doc_id, audio_data, dry_run)
            counters["audio"] += 1
            print(f"  🔊 Audio: {doc_id}")

    return counters


def run(subject_filter: str = None, dry_run: bool = False, lore_only: bool = False):
    """Upload all data to Firestore."""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError:
        print("❌ firebase-admin not installed. Run: pip install firebase-admin")
        return

    if not dry_run:
        if not GOOGLE_CLOUD_PROJECT_ID:
            print("❌ GOOGLE_CLOUD_PROJECT_ID not set in .env")
            return

        # Initialize Firebase
        try:
            firebase_admin.get_app()
        except ValueError:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {"projectId": GOOGLE_CLOUD_PROJECT_ID})

        db = firestore.client()
    else:
        db = None
        print("🏃 DRY RUN MODE — no data will be uploaded\n")

    # ── Always upload lore/game config ──────────────────────
    print(f"\n{'='*60}")
    print(f"🎮 Uploading game configuration (lore/)")
    print(f"{'='*60}")
    lore_counters = _upload_lore(db, dry_run)

    if lore_only:
        print(f"\n{'='*60}")
        print(f"📊 Lore Upload Summary:")
        for k, v in lore_counters.items():
            print(f"   {k}: {v}")
        if dry_run:
            print(f"\n   ⚠️  DRY RUN — nothing was actually uploaded")
        print(f"\n✅ Phase 11 (lore-only) complete!")
        return

    # ── Upload per-subject content ──────────────────────────
    subjects = [subject_filter] if subject_filter else list(BOOKS.values())
    counters = {"concepts": 0, "glossaries": 0, "assessments": 0, "bridges": 0, "compiled_modes": 0}

    for subject in subjects:
        print(f"\n{'='*60}")
        print(f"☁️  Uploading: {subject}")
        print(f"{'='*60}")

        # ── Upload structured concepts (prefer verified from Phase 8.2) ──
        verified_dir = VERIFIED_STRUCTURED_DIR / subject
        structured_dir = STRUCTURED_DIR / subject
        source_dir = verified_dir if verified_dir.exists() else structured_dir

        if source_dir.exists():
            for concept_path in sorted(source_dir.glob("*.json")):
                concept = json.loads(concept_path.read_text(encoding="utf-8"))
                concept_id = concept.get("concept_id", concept_path.stem)

                if not dry_run:
                    # Main concept document
                    doc_ref = db.collection("concepts").document(concept_id)
                    # Separate levels into subcollection to keep doc size manageable
                    levels = concept.pop("levels", [])
                    doc_ref.set(concept)

                    for level in levels:
                        level_num = level.get("level", 0)
                        doc_ref.collection("levels").document(str(level_num)).set(level)

                counters["concepts"] += 1
                print(f"  📝 Concept: {concept_id}")

        # ── Upload compiled game modes (Phase 8.1) ──────────
        compiled_dir = COMPILED_DIR / subject
        if compiled_dir.exists():
            for mode_path in sorted(compiled_dir.glob("*.json")):
                mode_data = json.loads(mode_path.read_text(encoding="utf-8"))
                mode_doc_id = mode_path.stem

                if not dry_run:
                    doc_ref = db.collection("compiled_modes").document(mode_doc_id)
                    # Separate mode_instances into subcollection
                    instances = mode_data.pop("mode_instances", [])
                    doc_ref.set(mode_data)

                    for inst in instances:
                        inst_id = inst.get("mode_id", f"mode_{instances.index(inst)}")
                        doc_ref.collection("instances").document(inst_id).set(inst)

                counters["compiled_modes"] += 1

        # ── Upload glossary ─────────────────────────────────
        glossary_path = EXTRACTED_DIR / subject / "_glossary.json"
        if glossary_path.exists():
            glossary = json.loads(glossary_path.read_text(encoding="utf-8"))
            _upload_doc(db, "glossaries", subject, glossary, dry_run)
            counters["glossaries"] += 1
            terms_count = len(glossary.get("terms", []))
            print(f"  📖 Glossary: {terms_count} terms")

        # ── Upload assessments ──────────────────────────────
        for assess_path in sorted((EXTRACTED_DIR / subject).glob("ch*_assessment.json")):
            assessment = json.loads(assess_path.read_text(encoding="utf-8"))
            ch_num = assessment.get("chapter_number", "?")
            doc_id = f"{subject}-ch{ch_num}"
            _upload_doc(db, "assessments", doc_id, assessment, dry_run)
            counters["assessments"] += 1
            print(f"  📋 Assessment: {doc_id}")

        # ── Upload equations ────────────────────────────────
        for ch_path in sorted((EXTRACTED_DIR / subject).glob("ch[0-9]*_*.json")):
            if "_assessment" in ch_path.name:
                continue
            ch_data = json.loads(ch_path.read_text(encoding="utf-8"))
            equations = ch_data.get("equations_to_remember", [])
            if equations:
                ch_num = ch_data.get("chapter_number")
                _upload_doc(db, "equations", f"{subject}-ch{ch_num}", {
                    "book": subject,
                    "chapter": ch_num,
                    "equations": equations,
                }, dry_run)

        # ── Upload figure catalog ───────────────────────────
        fig_path = EXTRACTED_DIR / subject / "_figure_catalog.json"
        if fig_path.exists():
            fig_catalog = json.loads(fig_path.read_text(encoding="utf-8"))
            _upload_doc(db, "figures", subject, fig_catalog, dry_run)
            print(f"  🖼️  Figures: {fig_catalog.get('total_figures', 0)}")

    # ── Upload bridges ──────────────────────────────────────
    if BRIDGES_DIR.exists():
        for bridge_path in sorted(BRIDGES_DIR.glob("*.json")):
            if bridge_path.name == "_bridge_graph.json":
                bridge_graph = json.loads(bridge_path.read_text(encoding="utf-8"))
                _upload_doc(db, "bridge_graph", "main", bridge_graph, dry_run)
                print(f"\n  🌉 Bridge graph: {bridge_graph.get('total_edges', 0)} edges")
            else:
                bridge = json.loads(bridge_path.read_text(encoding="utf-8"))
                bridge_id = bridge.get("bridge_id", bridge_path.stem)
                _upload_doc(db, "bridge_missions", bridge_id, bridge, dry_run)
                counters["bridges"] += 1

    # ── Summary ─────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"📊 Upload Summary:")
    print(f"\n   Game Config:")
    for k, v in lore_counters.items():
        print(f"     {k}: {v}")
    print(f"\n   Content:")
    print(f"     Concepts: {counters['concepts']}")
    print(f"     Compiled modes: {counters['compiled_modes']}")
    print(f"     Glossaries: {counters['glossaries']}")
    print(f"     Assessments: {counters['assessments']}")
    print(f"     Bridge missions: {counters['bridges']}")
    if dry_run:
        print(f"\n   ⚠️  DRY RUN — nothing was actually uploaded")
    print(f"\n✅ Phase 11 complete!")


if __name__ == "__main__":
    args = sys.argv[1:]
    dry = "--dry-run" in args
    lore = "--lore-only" in args
    subject = next((a for a in args if not a.startswith("--")), None)
    run(subject, dry, lore)
