"""
Phase 11: Upload all processed data to Firebase Firestore.
This is the final phase — pushes everything to the cloud database.

NOTE: Requires Firebase project setup and service account credentials.
      Set GOOGLE_APPLICATION_CREDENTIALS in .env to your service account JSON path.

Usage:
    python scripts/phase11_upload_firestore.py                # Upload everything
    python scripts/phase11_upload_firestore.py biology         # One subject
    python scripts/phase11_upload_firestore.py --dry-run       # Preview without uploading
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    EXTRACTED_DIR, STRUCTURED_DIR, BRIDGES_DIR,
    BOOKS, GOOGLE_CLOUD_PROJECT_ID,
)


def run(subject_filter: str = None, dry_run: bool = False):
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

    subjects = [subject_filter] if subject_filter else list(BOOKS.values())

    counters = {"concepts": 0, "glossaries": 0, "assessments": 0, "bridges": 0}

    for subject in subjects:
        print(f"\n{'='*60}")
        print(f"☁️  Uploading: {subject}")
        print(f"{'='*60}")

        # ── Upload structured concepts ──────────────────────────
        structured_dir = STRUCTURED_DIR / subject
        if structured_dir.exists():
            for concept_path in sorted(structured_dir.glob("*.json")):
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

        # ── Upload glossary ─────────────────────────────────────
        glossary_path = EXTRACTED_DIR / subject / "_glossary.json"
        if glossary_path.exists():
            glossary = json.loads(glossary_path.read_text(encoding="utf-8"))

            if not dry_run:
                db.collection("glossaries").document(subject).set(glossary)

            counters["glossaries"] += 1
            terms_count = len(glossary.get("terms", []))
            print(f"  📖 Glossary: {terms_count} terms")

        # ── Upload assessments ──────────────────────────────────
        for assess_path in sorted((EXTRACTED_DIR / subject).glob("ch*_assessment.json")):
            assessment = json.loads(assess_path.read_text(encoding="utf-8"))
            ch_num = assessment.get("chapter_number", "?")
            doc_id = f"{subject}-ch{ch_num}"

            if not dry_run:
                db.collection("assessments").document(doc_id).set(assessment)

            counters["assessments"] += 1
            print(f"  📋 Assessment: {doc_id}")

        # ── Upload equations ────────────────────────────────────
        for ch_path in sorted((EXTRACTED_DIR / subject).glob("ch[0-9]*_*.json")):
            if "_assessment" in ch_path.name:
                continue
            ch_data = json.loads(ch_path.read_text(encoding="utf-8"))
            equations = ch_data.get("equations_to_remember", [])
            if equations and not dry_run:
                ch_num = ch_data.get("chapter_number")
                db.collection("equations").document(f"{subject}-ch{ch_num}").set({
                    "book": subject,
                    "chapter": ch_num,
                    "equations": equations,
                })

        # ── Upload figure catalog ───────────────────────────────
        fig_path = EXTRACTED_DIR / subject / "_figure_catalog.json"
        if fig_path.exists():
            fig_catalog = json.loads(fig_path.read_text(encoding="utf-8"))
            if not dry_run:
                db.collection("figures").document(subject).set(fig_catalog)
            print(f"  🖼️  Figures: {fig_catalog.get('total_figures', 0)}")

    # ── Upload bridges ──────────────────────────────────────────
    if BRIDGES_DIR.exists():
        for bridge_path in sorted(BRIDGES_DIR.glob("*.json")):
            if bridge_path.name == "_bridge_graph.json":
                bridge_graph = json.loads(bridge_path.read_text(encoding="utf-8"))
                if not dry_run:
                    db.collection("bridge_graph").document("main").set(bridge_graph)
                print(f"\n  🌉 Bridge graph: {bridge_graph.get('total_edges', 0)} edges")
            else:
                bridge = json.loads(bridge_path.read_text(encoding="utf-8"))
                bridge_id = bridge.get("bridge_id", bridge_path.stem)
                if not dry_run:
                    db.collection("shared_concepts").document(bridge_id).set(bridge)
                counters["bridges"] += 1

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"📊 Upload Summary:")
    print(f"   Concepts: {counters['concepts']}")
    print(f"   Glossaries: {counters['glossaries']}")
    print(f"   Assessments: {counters['assessments']}")
    print(f"   Bridges: {counters['bridges']}")
    if dry_run:
        print(f"\n   ⚠️  DRY RUN — nothing was actually uploaded")
    print(f"\n✅ Phase 11 complete!")


if __name__ == "__main__":
    args = sys.argv[1:]
    dry = "--dry-run" in args
    subject = next((a for a in args if a != "--dry-run"), None)
    run(subject, dry)
