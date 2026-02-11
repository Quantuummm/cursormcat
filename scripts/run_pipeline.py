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
    6.1- Verify wrong-answer explanations (optional)
    7  - Build primitives (deterministic)
    8  - Restructure into guided learning (ADHD-optimized)
    8.1- Compile modes (engine-ready games)
    7L - Legacy game classification (optional)
    9  - Enrich bridge connections (requires all books)
    10 - Generate TTS audio (requires Google Cloud credits)
    11 - Upload to Firestore (requires Firebase setup)
"""

# NOTE: Updated in second workflow (Feb 9, 2026).

import sys
import time
import argparse
from pathlib import Path
import signal
import sys

# Ensure scripts folder is in path for imports
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import config

# Track interrupt requests so we can require a double-C to force stop
INTERRUPT_COUNT = 0

def _sigint_handler(signum, frame):
    global INTERRUPT_COUNT
    INTERRUPT_COUNT += 1
    # Only trigger graceful exit on first interrupt
    # If the process just started, ignore one spurious SIGINT (Windows noise)
    if INTERRUPT_COUNT == 1:
        config.INTERRUPT_REQUESTED = True
        print("\n⚠️ Interrupt requested — will stop after the current Gemini call. Press Ctrl+C again to force immediate exit.")
    else:
        raise KeyboardInterrupt

signal.signal(signal.SIGINT, _sigint_handler)

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from utils.checkpoint_manager import save_checkpoint, get_last_checkpoint, print_status_report, check_prerequisites

sys.path.insert(0, str(Path(__file__).parent))


def main():
    # Initialize interrupt state for this run
    config.INTERRUPT_REQUESTED = False
    
    parser = argparse.ArgumentParser(description="MCAT Content Pipeline Orchestrator")
    parser.add_argument("pdf", nargs="?", help="PDF filename (e.g., biology.pdf) or omit for all")
    parser.add_argument("chapter", nargs="?", type=int, help="Specific chapter number")
    parser.add_argument("--phase", type=int, help="Run only this phase")
    parser.add_argument("--from", dest="from_phase", type=int, default=0, help="Start from this phase")
    parser.add_argument("--to", type=int, default=11, help="Run up to this phase (inclusive)")
    parser.add_argument("--verify-wrong-answers", action="store_true",
                        help="After Phase 6, run Phase 6.1 verification")
    parser.add_argument("--legacy-game-classifier", action="store_true",
                        help="Use legacy Phase 7 LLM game classification")
    parser.add_argument("--report", action="store_true", help="Print the last checkpoint report and exit")
    parser.add_argument("--resume", action="store_true", help="Resume from the last saved checkpoint")

    args = parser.parse_args()

    if args.report:
        print_status_report()
        return

    # If no arguments are provided (not even a PDF), show the report and help then exit
    # This prevents accidental full-pipeline runs and helps agents/users know what to do.
    if len(sys.argv) == 1:
        print_status_report()
        last = get_last_checkpoint()
        if last:
            next_phase = last.get("phase") + (1 if last.get("status") == "completed" else 0)
            print(f"👉 SUGGESTED NEXT STEP:")
            print(f"   To {'continue' if last.get('status') != 'completed' else 'advance to Phase ' + str(next_phase)} for {last.get('pdf')} Ch.{last.get('chapter')}:")
            print(f"   python scripts/run_pipeline.py \"{last.get('pdf')}\" {last.get('chapter')} --from {next_phase}")
            print(f"\n   Or simply use: python scripts/run_pipeline.py --resume\n")
        
        print("💡 Use 'python scripts/run_pipeline.py --help' to see all options.")
        return

    pdf = args.pdf
    chapter = args.chapter
    phase_only = args.phase
    from_phase = args.from_phase
    to_phase = args.to

    if args.resume:
        last = get_last_checkpoint()
        if last:
            pdf = last.get("pdf")
            chapter = last.get("chapter")
            # If the last one was success, start from next. If it crashed/failed, retry it.
            if last.get("status") == "completed":
                from_phase = last.get("phase") + 1
            else:
                from_phase = last.get("phase")
            print(f"🔄 Resuming from checkpoint: {pdf} Ch.{chapter} Phase {from_phase}")
        else:
            print("⚠️ No checkpoint found to resume from.")

    if phase_only is not None:
        from_phase = phase_only
        to_phase = phase_only

    # --- Prerequisite Validation ---
    # Only validate if we are running more than just one phase explicitly
    # (Allow user to override if they really want to run one specific phase)
    if from_phase != to_phase or True: # Check always for safety
        print("🔍 Validating prerequisites...")
        # Check start phase
        ok, missing = check_prerequisites(pdf, chapter, from_phase)
        if not ok:
            print(f"❌ Cannot start Phase {from_phase}. Missing prerequisites: {missing}")
            print(f"👉 Please run the missing phases first for this subject/chapter.")
            return

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
        from phases.phase0.phase0_extract_images import run as run_phase0
        run_phase0(pdf)
        save_checkpoint(pdf, chapter, 0, "Extract Images")

    # Phase 1: TOC extraction
    if from_phase <= 1 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 1: Extract Table of Contents")
        print(f"{'─'*60}")
        from phases.phase1.phase1_extract_toc import run as run_phase1
        run_phase1(pdf)
        save_checkpoint(pdf, chapter, 1, "Extract Table of Contents")

    # Phase 2: Chapter assessments
    if from_phase <= 2 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 2: Extract Chapter Assessments")
        print(f"{'─'*60}")
        from phases.phase2.phase2_extract_assessments import run as run_phase2
        run_phase2(pdf, chapter)
        save_checkpoint(pdf, chapter, 2, "Extract Chapter Assessments")

    # Phase 3: Section content (big extraction)
    if from_phase <= 3 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 3: Extract Section Content")
        print(f"{'─'*60}")
        globals()["CURRENT_PHASE"] = 3
        globals()["CURRENT_PHASE_NAME"] = "Extract Section Content"
        from phases.phase3.phase3_extract_sections import run as run_phase3
        run_phase3(pdf, chapter)
        save_checkpoint(pdf, chapter, 3, "Extract Section Content")

    # Phase 4: Glossary
    if from_phase <= 4 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 4: Extract Glossary")
        print(f"{'─'*60}")
        from phases.phase4.phase4_extract_glossary import run as run_phase4
        run_phase4(pdf)
        save_checkpoint(pdf, chapter, 4, "Extract Glossary")

    # Phase 5: Figure catalog
    if from_phase <= 5 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 5: Catalog Figures")
        print(f"{'─'*60}")
        from phases.phase5.phase5_catalog_figures import run as run_phase5
        run_phase5(pdf, chapter)
        save_checkpoint(pdf, chapter, 5, "Catalog Figures")

    # Phase 6: Wrong-answer enrichment (Generates explanations)
    if from_phase <= 6 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 6: Enrich Wrong-Answer Explanations")
        print(f"{'─'*60}")
        globals()["CURRENT_PHASE"] = 6
        globals()["CURRENT_PHASE_NAME"] = "Enrich Wrong-Answer Explanations"
        from phases.phase6.phase6_enrich_wrong_answers import run as run_phase6
        run_phase6(pdf, chapter)
        save_checkpoint(pdf, chapter, 6, globals()["CURRENT_PHASE_NAME"])

        # Phase 6.1: Verify (Mandatory loop/fix pass)
        print(f"\n{'─'*60}")
        print(f"PHASE 6.1: Verify & Auto-Fix Explanations")
        print(f"{'─'*60}")
        globals()["CURRENT_PHASE"] = 6.1
        globals()["CURRENT_PHASE_NAME"] = "Verify Wrong-Answer Explanations"
        from phases.phase6_1.phase6_1_verify_wrong_answers import run as run_phase6_1
        run_phase6_1(pdf, chapter)
        save_checkpoint(pdf, chapter, 6.1, globals()["CURRENT_PHASE_NAME"])

    # Phase 7: Primitives build (default) or legacy game classification
    if from_phase <= 7 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 7: Build Primitives")
        print(f"{'─'*60}")
        globals()["CURRENT_PHASE"] = 7
        globals()["CURRENT_PHASE_NAME"] = "Build Primitives"
        if args.legacy_game_classifier:
            print("  ⚠️  Using legacy LLM game classification")
            from phases.phase7_legacy.phase7_legacy_classify_games import run as run_phase7
            run_phase7(pdf, chapter)
            save_checkpoint(pdf, chapter, 7, "Build Primitives (Legacy)")
        else:
            from phases.phase7.phase7_build_primitives import run as run_phase7
            run_phase7(pdf, chapter)
            save_checkpoint(pdf, chapter, 7, "Build Primitives")

    # Phase 8: Restructure guided learning
    if from_phase <= 8 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 8: Restructure Guided Learning")
        print(f"{'─'*60}")
        globals()["CURRENT_PHASE"] = 8
        globals()["CURRENT_PHASE_NAME"] = "Restructure Guided Learning"
        from phases.phase8.phase8_restructure_guided_learning import run as run_phase8
        run_phase8(pdf, chapter)
        save_checkpoint(pdf, chapter, 8, "Restructure Guided Learning")


    # Phase 8.2: Verify & Fix Guided Learning
    if from_phase <= 8.2 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 8.2: Verify & Fix Guided Learning")
        print(f"{'─'*60}")
        globals()["CURRENT_PHASE"] = 8.2
        globals()["CURRENT_PHASE_NAME"] = "Verify & Fix Guided Learning"
        from phases.phase8_2.phase8_2_verify_and_fix import run_phase8_2
        run_phase8_2(pdf, chapter)
        save_checkpoint(pdf, chapter, 8.2, globals()["CURRENT_PHASE_NAME"])


    # Phase 8.1: Compile modes (engine-ready games)
    if from_phase <= 8.1 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 8.1: Compile Modes")
        print(f"{'─'*60}")
        from phases.phase8_1.phase8_1_compile_modes import run as run_phase8_1
        run_phase8_1(pdf, chapter)
        save_checkpoint(pdf, chapter, 8.1, "Compile Modes")

    # Phase 9: Bridge enrichment (needs all books)
    if from_phase <= 9 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 9: Enrich Bridges")
        print(f"{'─'*60}")
        from phases.phase9.phase9_enrich_bridges import run as run_phase9
        run_phase9()
        save_checkpoint(None, None, 9, "Enrich Bridges")

    # Phase 10: TTS generation (needs Google Cloud)
    if from_phase <= 10 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 10: Generate TTS Audio")
        print(f"{'─'*60}")
        subject = None
        if pdf:
            from config import BOOKS
            subject = BOOKS.get(pdf)
        from phases.phase10.phase10_generate_tts import run as run_phase10
        run_phase10(subject)
        save_checkpoint(pdf, None, 10, "Generate TTS Audio")

    # Phase 11: Upload to Firestore
    if from_phase <= 11 <= to_phase:
        print(f"\n{'─'*60}")
        print(f"PHASE 11: Upload to Firestore")
        print(f"{'─'*60}")
        subject = None
        if pdf:
            from config import BOOKS
            subject = BOOKS.get(pdf)
        from phases.phase11.phase11_upload_firestore import run as run_phase11
        run_phase11(subject)
        save_checkpoint(pdf, None, 11, "Upload to Firestore")

    # Done!
    elapsed = time.time() - start
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    print(f"\n{'='*60}")
    print(f"🎉 PIPELINE COMPLETE!")
    print(f"   Total time: {minutes}m {seconds}s")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Save an interrupted checkpoint using the last known global phase info if available
        from utils.checkpoint_manager import save_checkpoint, get_last_checkpoint
        import os
        from datetime import datetime

        cp = globals().get("CURRENT_PHASE")
        cp_name = globals().get("CURRENT_PHASE_NAME")
        last = get_last_checkpoint()

        # Determine pdf/chapter to record in checkpoint and log
        pdf_to_save = None
        chapter_to_save = None
        if last:
            pdf_to_save = last.get("pdf")
            chapter_to_save = last.get("chapter")

        timestamp = datetime.now().isoformat()
        log_dir = Path(__file__).resolve().parents[2] / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "interrupts.log"

        if cp is not None:
            save_checkpoint(pdf_to_save, chapter_to_save, cp, cp_name or f"Phase {cp} (interrupted)", status="interrupted")
            print(f"\n🛑 Interrupted during {cp_name or f'Phase {cp}'}. Saved interrupted checkpoint.")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"{timestamp}\tINTERRUPTED\tphase={cp}\tname={cp_name}\tpdf={pdf_to_save}\tchapter={chapter_to_save}\n")
        else:
            if last:
                save_checkpoint(last.get("pdf"), last.get("chapter"), last.get("phase"), f"Phase {last.get('phase')} (interrupted)", status="interrupted")
                print(f"\n🛑 Interrupted. Saved interrupted checkpoint at last known phase {last.get('phase')}.")
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"{timestamp}\tINTERRUPTED\tphase={last.get('phase')}\tpdf={last.get('pdf')}\tchapter={last.get('chapter')}\n")
            else:
                print("\n🛑 Interrupted before any checkpoint could be recorded.")
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"{timestamp}\tINTERRUPTED\tphase=unknown\tpdf=unknown\tchapter=unknown\n")
