"""
Phase 8: Restructure extracted content into ADHD-friendly guided learning format.
This is THE critical transformation — from flat Kaplan data to progressive game-ready lessons.

Requires: Phase 3 (sections) + Phase 5 (figures) + Phase 7 (game classification).

Usage:
    python scripts/phase8_restructure_guided_learning.py                    # All books
    python scripts/phase8_restructure_guided_learning.py biology.pdf        # One book
    python scripts/phase8_restructure_guided_learning.py biology.pdf 3      # One chapter
"""

import sys
import json
from pathlib import Path
from slugify import slugify

sys.path.insert(0, str(Path(__file__).parent))
from config import EXTRACTED_DIR, CLASSIFIED_DIR, STRUCTURED_DIR, PROMPTS_DIR, BOOKS
from utils.gemini_client import GeminiClient
from utils.schema_validator import validate_restructured, print_validation


def run(pdf_filename: str = None, chapter_num: int = None):
    """Restructure all sections into guided learning format."""
    client = GeminiClient()

    prompt_template = (PROMPTS_DIR / "restructure_guided_learning.txt").read_text(encoding="utf-8")

    subjects = [BOOKS[pdf_filename]] if pdf_filename and pdf_filename in BOOKS else BOOKS.values()

    for subject in subjects:
        subject_dir = EXTRACTED_DIR / subject
        classified_dir = CLASSIFIED_DIR / subject
        output_dir = STRUCTURED_DIR / subject
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load TOC for metadata
        toc_path = subject_dir / "_toc.json"
        if not toc_path.exists():
            print(f"⏭️  Skipping {subject}: Run Phase 1 first")
            continue
        toc = json.loads(toc_path.read_text(encoding="utf-8"))

        # Load figure catalog
        figure_catalog = {"figures": []}
        fig_path = subject_dir / "_figure_catalog.json"
        if fig_path.exists():
            figure_catalog = json.loads(fig_path.read_text(encoding="utf-8"))

        # Find all chapter extraction files
        chapter_files = sorted(subject_dir.glob("ch[0-9]*_*.json"))
        chapter_files = [f for f in chapter_files if "_assessment" not in f.name]

        if not chapter_files:
            print(f"⏭️  Skipping {subject}: No chapter files (run Phase 3)")
            continue

        print(f"\n{'='*60}")
        print(f"🧠 Restructuring guided learning: {subject}")
        print(f"{'='*60}")

        for ch_path in chapter_files:
            ch_data = json.loads(ch_path.read_text(encoding="utf-8"))
            ch_num = ch_data.get("chapter_number", "?")
            ch_title = ch_data.get("chapter_title", "?")

            if chapter_num is not None and ch_num != chapter_num:
                continue

            # Get chapter metadata from TOC
            toc_chapter = None
            for tch in toc.get("chapters", []):
                if tch["chapter_number"] == ch_num:
                    toc_chapter = tch
                    break

            aamc_categories = []
            if toc_chapter and toc_chapter.get("chapter_profile"):
                aamc_categories = toc_chapter["chapter_profile"].get("aamc_content_categories", [])

            print(f"\n  📖 Chapter {ch_num}: {ch_title}")

            # Get summary data for matching
            summary_by_section = {}
            for s in ch_data.get("summary", {}).get("by_section", []):
                summary_by_section[s["section_id"]] = s.get("summary_points", [])

            # Get concept checks by section
            checks_by_section = {}
            for q in ch_data.get("concept_checks", []):
                sec = q.get("section_tested", "unknown")
                if sec not in checks_by_section:
                    checks_by_section[sec] = []
                checks_by_section[sec].append(q)

            for section in ch_data.get("sections", []):
                sec_id = section.get("section_id", "?")
                sec_title = section.get("section_title", "?")
                is_hy = section.get("is_high_yield", False)

                print(f"\n     🎯 Section {sec_id}: {sec_title}", end="")
                if is_hy:
                    print(" [HIGH-YIELD]", end="")
                print()

                # Get figures for this section
                sec_figures = [
                    f for f in figure_catalog.get("figures", [])
                    if f.get("section_id") == sec_id
                ]

                # Get game classification
                safe_title = slugify(sec_title, max_length=40)
                game_path = classified_dir / f"{sec_id}-{safe_title}_games.json"
                game_classification = {"has_games": False, "games": []}
                if game_path.exists():
                    game_classification = json.loads(game_path.read_text(encoding="utf-8"))

                # Get callouts for this section
                callouts = section.get("callouts", [])

                # Build the restructuring prompt
                prompt = prompt_template.format(
                    book_subject=subject,
                    chapter_number=ch_num,
                    chapter_title=ch_title,
                    section_id=sec_id,
                    section_title=sec_title,
                    is_high_yield=str(is_hy).lower(),
                    aamc_categories=json.dumps(aamc_categories),
                    learning_objectives=json.dumps(section.get("learning_objectives", []), indent=2),
                    content_blocks_json=json.dumps(section.get("content_blocks", []), indent=2),
                    summary_points=json.dumps(summary_by_section.get(sec_id, []), indent=2),
                    concept_checks_json=json.dumps(checks_by_section.get(sec_id, []), indent=2),
                    callouts_json=json.dumps(callouts, indent=2),
                    figure_refs_json=json.dumps(sec_figures, indent=2),
                    game_classification_json=json.dumps(game_classification, indent=2),
                )

                print(f"        🔄 Restructuring with Gemini 3 Flash (30-90 seconds)...")

                try:
                    structured = client.restructure(prompt, phase=f"P8_restructure_{sec_id}")

                    # Handle case where Gemini returns a list instead of an object
                    if isinstance(structured, list):
                        # Take first item if it looks like a concept object
                        if structured and isinstance(structured[0], dict) and "levels" in structured[0]:
                            structured = structured[0]
                        else:
                            structured = {
                                "concept_id": f"{sec_id}-{safe_title}",
                                "title": sec_title,
                                "levels": structured if all(isinstance(x, dict) for x in structured) else [],
                            }

                    # Validate
                    issues = validate_restructured(structured)
                    print_validation(f"Section {sec_id}", issues)

                    levels = structured.get("levels", [])
                    total_questions = sum(
                        len(lv.get("check_questions", []))
                        + (1 if lv.get("apply_question") else 0)
                        for lv in levels
                    )
                    print(f"        Levels: {len(levels)}")
                    print(f"        Total questions: {total_questions}")
                    game_els = structured.get("game_elements", {})
                    has_games = game_els.get("has_games", False) if isinstance(game_els, dict) else False
                    print(f"        Has games: {has_games}")

                    # Save
                    concept_id = structured.get("concept_id", f"{sec_id}-{safe_title}")
                    output_path = output_dir / f"{concept_id}.json"
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(structured, f, indent=2, ensure_ascii=False)
                    print(f"        💾 Saved: {output_path.name}")

                except Exception as e:
                    print(f"        ❌ Failed to restructure {sec_id}: {e}")
                    print(f"        ⏭️  Skipping this section, continuing with next...")
                    continue

        print(f"\n  📁 Structured files saved to: {output_dir}")

    print(f"\n✅ Phase 8 complete!")


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else None
    ch = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run(pdf, ch)
