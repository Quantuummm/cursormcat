"""\
Golden Chapter Regression Runner
--------------------------------
Runs a targeted slice of the pipeline on a single chapter for regression checks.

Usage:
  python tests/golden_chapters/run_golden_chapter.py "MCAT Biology Review.pdf" 1 --from 3 --to 11 --verify-wrong-answers
"""

import sys
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def run_pipeline_slice(pdf: str, chapter: int, from_phase: int, to_phase: int,
                       verify_wrong_answers: bool, legacy_game_classifier: bool) -> None:
    if from_phase <= 0 <= to_phase:
        from phases.phase0.phase0_extract_images import run as run_phase0
        run_phase0(pdf)
    if from_phase <= 1 <= to_phase:
        from phases.phase1.phase1_extract_toc import run as run_phase1
        run_phase1(pdf)
    if from_phase <= 2 <= to_phase:
        from phases.phase2.phase2_extract_assessments import run as run_phase2
        run_phase2(pdf, chapter)
    if from_phase <= 3 <= to_phase:
        from phases.phase3.phase3_extract_sections import run as run_phase3
        run_phase3(pdf, chapter)
    if from_phase <= 4 <= to_phase:
        from phases.phase4.phase4_extract_glossary import run as run_phase4
        run_phase4(pdf)
    if from_phase <= 5 <= to_phase:
        from phases.phase5.phase5_catalog_figures import run as run_phase5
        run_phase5(pdf, chapter)
    if from_phase <= 6 <= to_phase:
        from phases.phase6.phase6_enrich_wrong_answers import run as run_phase6
        run_phase6(pdf)
        if verify_wrong_answers:
            from phases.phase6_1.phase6_1_verify_wrong_answers import run as run_phase6_1
            run_phase6_1(pdf, chapter)
    if from_phase <= 7 <= to_phase:
        if legacy_game_classifier:
            from phases.phase7_legacy.phase7_legacy_classify_games import run as run_phase7
            run_phase7(pdf, chapter)
        else:
            from phases.phase7.phase7_build_primitives import run as run_phase7
            run_phase7(pdf, chapter)
    if from_phase <= 8 <= to_phase:
        from phases.phase8.phase8_restructure_guided_learning import run as run_phase8
        run_phase8(pdf, chapter)
    if from_phase <= 8.1 <= to_phase:
        from phases.phase8_1.phase8_1_compile_modes import run as run_phase8_1
        run_phase8_1(pdf, chapter)
    if from_phase <= 9 <= to_phase:
        from phases.phase9.phase9_enrich_bridges import run as run_phase9
        run_phase9()
    if from_phase <= 10 <= to_phase:
        from phases.phase10.phase10_generate_tts import run as run_phase10
        subject = None
        if pdf:
            from config import BOOKS
            subject = BOOKS.get(pdf)
        run_phase10(subject)
    if from_phase <= 11 <= to_phase:
        from phases.phase11.phase11_upload_firestore import run as run_phase11
        subject = None
        if pdf:
            from config import BOOKS
            subject = BOOKS.get(pdf)
        run_phase11(subject)


def main() -> None:
    parser = argparse.ArgumentParser(description="Golden chapter regression runner")
    parser.add_argument("pdf", help="PDF filename (e.g., 'MCAT Biology Review.pdf')")
    parser.add_argument("chapter", type=int, help="Chapter number")
    parser.add_argument("--from", dest="from_phase", type=int, default=3, help="Start from this phase")
    parser.add_argument("--to", dest="to_phase", type=int, default=11, help="Run up to this phase")
    parser.add_argument("--verify-wrong-answers", action="store_true",
                        help="After Phase 6, run Phase 6.1 verification")
    parser.add_argument("--legacy-game-classifier", action="store_true",
                        help="Use legacy Phase 7 LLM game classification")
    args = parser.parse_args()

    run_pipeline_slice(
        pdf=args.pdf,
        chapter=args.chapter,
        from_phase=args.from_phase,
        to_phase=args.to_phase,
        verify_wrong_answers=args.verify_wrong_answers,
        legacy_game_classifier=args.legacy_game_classifier,
    )


if __name__ == "__main__":
    main()
