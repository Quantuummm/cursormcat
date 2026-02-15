"""
Parallel Pipeline Worker — Runs a single phase for a specific book/chapter.
Called by parallel_pipeline.py with a specific API key set in the environment.

Usage (called by orchestrator, not directly):
    python scripts/parallel_worker.py --phase 3 --pdf "MCAT Biology Review.pdf" --chapter 2 --key-index 0
"""

import sys
import os
import argparse
import time
import traceback
from pathlib import Path

# Set up paths
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def run_phase(phase: float, pdf_filename: str = None, chapter_num: int = None):
    """Execute a single phase for a given book/chapter."""
    
    if phase == 0:
        from phases.phase0.phase0_extract_images import run
        run(pdf_filename)
    elif phase == 1:
        from phases.phase1.phase1_extract_toc import run
        run(pdf_filename)
    elif phase == 2:
        from phases.phase2.phase2_extract_assessments import run
        run(pdf_filename, chapter_num)
    elif phase == 3:
        from phases.phase3.phase3_extract_sections import run
        run(pdf_filename, chapter_num)
    elif phase == 4:
        from phases.phase4.phase4_extract_glossary import run
        run(pdf_filename)
    elif phase == 5:
        from phases.phase5.phase5_catalog_figures import run
        run(pdf_filename, chapter_num)
    elif phase == 6:
        from phases.phase6.phase6_enrich_wrong_answers import run
        run(pdf_filename, chapter_num)
    elif phase == 6.1:
        from phases.phase6_1.phase6_1_verify_wrong_answers import run
        run(pdf_filename, chapter_num)
    elif phase == 7:
        from phases.phase7.phase7_build_primitives import run
        run(pdf_filename, chapter_num)
    elif phase == 8:
        from phases.phase8.phase8_restructure_guided_learning import run
        run(pdf_filename, chapter_num)
    elif phase == 8.1:
        from phases.phase8_1.phase8_1_compile_modes import run
        run(pdf_filename, chapter_num)
    elif phase == 8.2:
        from phases.phase8_2.phase8_2_verify_and_fix import run_phase8_2
        run_phase8_2(pdf_filename, chapter_num)
    elif phase == 9:
        from phases.phase9.phase9_enrich_bridges import run
        run()
    elif phase == 10:
        import config
        subject = config.BOOKS.get(pdf_filename) if pdf_filename else None
        from phases.phase10.phase10_generate_tts import run
        run(subject)
    elif phase == 11:
        import config
        subject = config.BOOKS.get(pdf_filename) if pdf_filename else None
        from phases.phase11.phase11_upload_firestore import run
        run(subject)
    else:
        raise ValueError(f"Unknown phase: {phase}")


def main():
    parser = argparse.ArgumentParser(description="Pipeline Worker")
    parser.add_argument("--phase", type=float, required=True)
    parser.add_argument("--pdf", type=str, default=None)
    parser.add_argument("--chapter", type=int, default=None)
    parser.add_argument("--key-index", type=int, default=0,
                        help="Which API key to use (0-4)")
    args = parser.parse_args()
    
    # The orchestrator already sets GEMINI_API_KEY in the subprocess environment.
    # Just verify it's there. No need to load .env again.
    key_var = f"GEMINI_API_KEY_{args.key_index + 1}"
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        # Fallback: try loading from .env with the numbered key
        try:
            from dotenv import load_dotenv
            load_dotenv(REPO_ROOT / ".env")
            api_key = os.getenv(key_var, os.getenv("GEMINI_API_KEY_1", ""))
            if api_key:
                os.environ["GEMINI_API_KEY"] = api_key
        except ImportError:
            pass
    
    phase_str = str(args.phase) if args.phase != int(args.phase) else str(int(args.phase))
    pdf_short = Path(args.pdf).stem if args.pdf else "ALL"
    ch_str = f"Ch{args.chapter}" if args.chapter else "ALL"
    
    print(f"[Worker {args.key_index}] Phase {phase_str} | {pdf_short} {ch_str} | Key: {key_var}")
    
    start = time.time()
    try:
        run_phase(args.phase, args.pdf, args.chapter)
        elapsed = time.time() - start
        print(f"[Worker {args.key_index}] ✅ Phase {phase_str} {pdf_short} {ch_str} done in {int(elapsed)}s")
        sys.exit(0)
    except Exception as e:
        elapsed = time.time() - start
        print(f"[Worker {args.key_index}] ❌ Phase {phase_str} {pdf_short} {ch_str} FAILED after {int(elapsed)}s: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
