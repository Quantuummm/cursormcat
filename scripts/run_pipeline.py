"""
Master Pipeline Orchestrator — runs all phases in order.

Usage:
    python scripts/run_pipeline.py                         # Full pipeline, all books
    python scripts/run_pipeline.py biology.pdf             # Full pipeline, one book
    python scripts/run_pipeline.py biology.pdf --phase 1   # Run specific phase only
    python scripts/run_pipeline.py biology.pdf --from 3    # Start from Phase 3
    python scripts/run_pipeline.py biology.pdf --to 5      # Run up to Phase 5
    python scripts/run_pipeline.py biology.pdf 3           # One book, one chapter

Phase Reference:
    0  - Extract images (PyMuPDF, no API needed)
    1  - Extract table of contents + metadata
    2  - Extract chapter assessments (diagnostic MCQs)
    3  - Extract section content (the big one)
    4  - Extract glossary
    5  - Catalog figures + match images
    6  - Enrich wrong-answer explanations
    7  - Classify games per section
    8  - Restructure into guided learning (ADHD-optimized)
    9  - Enrich bridge connections (requires all books)
    10 - Generate TTS audio (requires Google Cloud credits)
    11 - Upload to Firestore (requires Firebase setup)
"""

import sys
import argparse
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(description="MCAT Content Pipeline Orchestrator")
    parser.add_argument("pdf", nargs="?", help="PDF filename (e.g., biology.pdf) or omit for all")
    parser.add_argument("chapter", nargs="?", type=int, help="Specific chapter number")
    parser.add_argument("--phase", type=int, help="Run only this phase")
    parser.add_argument("--from", dest="from_phase", type=int, default=0, help="Start from this phase")
    parser.add_argument("--to", type=int, default=11, help="Run up to this phase (inclusive)")

    args = parser.parse_args()

    pdf = args.pdf
    chapter = args.chapter
    phase_only = args.phase
    from_phase = args.from_phase
    to_phase = args.to

    if phase_only is not None:
        from_phase = phase_only
        to_phase = phase_only

    print(f"\n{'='*60}")
    print(f"🧬 MCAT CONTENT PIPELINE")
    print(f"{'='*60}")
    print(f"  Target: {pdf or 'ALL BOOKS'}")
    if chapter:
        print(f"  Chapter: {chapter}")
    print(f"  Phases: {from_phase} → {to_phase}")
    print(f"{'='*60}\n")

    start = time.time()

    # Phase 0: Image extraction (no API needed)
    if from_phase <= 0 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 0: Extract Images")
        print(f"{'─'*60}")
        from phase0_extract_images import run as run_phase0
        run_phase0(pdf)

    # Phase 1: TOC extraction
    if from_phase <= 1 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 1: Extract Table of Contents")
        print(f"{'─'*60}")
        from phase1_extract_toc import run as run_phase1
        run_phase1(pdf)

    # Phase 2: Chapter assessments
    if from_phase <= 2 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 2: Extract Chapter Assessments")
        print(f"{'─'*60}")
        from phase2_extract_assessments import run as run_phase2
        run_phase2(pdf, chapter)

    # Phase 3: Section content (big extraction)
    if from_phase <= 3 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 3: Extract Section Content")
        print(f"{'─'*60}")
        from phase3_extract_sections import run as run_phase3
        run_phase3(pdf, chapter)

    # Phase 4: Glossary
    if from_phase <= 4 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 4: Extract Glossary")
        print(f"{'─'*60}")
        from phase4_extract_glossary import run as run_phase4
        run_phase4(pdf)

    # Phase 5: Figure catalog
    if from_phase <= 5 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 5: Catalog Figures")
        print(f"{'─'*60}")
        from phase5_catalog_figures import run as run_phase5
        run_phase5(pdf, chapter)

    # Phase 6: Wrong-answer enrichment
    if from_phase <= 6 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 6: Enrich Wrong-Answer Explanations")
        print(f"{'─'*60}")
        from phase6_enrich_wrong_answers import run as run_phase6
        run_phase6(pdf)

    # Phase 7: Game classification
    if from_phase <= 7 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 7: Classify Games")
        print(f"{'─'*60}")
        from phase7_classify_games import run as run_phase7
        run_phase7(pdf, chapter)

    # Phase 8: Restructure guided learning
    if from_phase <= 8 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 8: Restructure Guided Learning")
        print(f"{'─'*60}")
        from phase8_restructure_guided_learning import run as run_phase8
        run_phase8(pdf, chapter)

    # Phase 9: Bridge enrichment (needs all books)
    if from_phase <= 9 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 9: Enrich Bridges")
        print(f"{'─'*60}")
        from phase9_enrich_bridges import run as run_phase9
        run_phase9()

    # Phase 10: TTS generation (needs Google Cloud)
    if from_phase <= 10 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 10: Generate TTS Audio")
        print(f"{'─'*60}")
        subject = None
        if pdf:
            from config import BOOKS
            subject = BOOKS.get(pdf)
        from phase10_generate_tts import run as run_phase10
        run_phase10(subject)

    # Phase 11: Upload to Firestore
    if from_phase <= 11 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 11: Upload to Firestore")
        print(f"{'─'*60}")
        subject = None
        if pdf:
            from config import BOOKS
            subject = BOOKS.get(pdf)
        from phase11_upload_firestore import run as run_phase11
        run_phase11(subject)

    # Done!
    elapsed = time.time() - start
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    print(f"\n{'='*60}")
    print(f"🎉 PIPELINE COMPLETE!")
    print(f"   Total time: {minutes}m {seconds}s")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
