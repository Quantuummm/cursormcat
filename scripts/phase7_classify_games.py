"""
Phase 7: Classify which sections can generate memorization games.
Analyzes content blocks, figures, and equations to determine game types.

Requires: Phase 3 (section extraction) + Phase 5 (figure catalog).

Usage:
    python scripts/phase7_classify_games.py                    # All books
    python scripts/phase7_classify_games.py biology.pdf        # One book
    python scripts/phase7_classify_games.py biology.pdf 3      # One chapter
"""

import sys
import json
from pathlib import Path
from slugify import slugify

sys.path.insert(0, str(Path(__file__).parent))
from config import EXTRACTED_DIR, CLASSIFIED_DIR, PROMPTS_DIR, BOOKS
from utils.gemini_client import GeminiClient


def run(pdf_filename: str = None, chapter_num: int = None):
    """Classify game potential for each section."""
    client = GeminiClient()

    prompt_template = (PROMPTS_DIR / "game_classification.txt").read_text(encoding="utf-8")

    subjects = [BOOKS[pdf_filename]] if pdf_filename and pdf_filename in BOOKS else BOOKS.values()

    for subject in subjects:
        subject_dir = EXTRACTED_DIR / subject
        output_dir = CLASSIFIED_DIR / subject
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load figure catalog
        figure_catalog = {"figures": []}
        fig_cat_path = subject_dir / "_figure_catalog.json"
        if fig_cat_path.exists():
            figure_catalog = json.loads(fig_cat_path.read_text(encoding="utf-8"))

        # Find all chapter extraction files
        chapter_files = sorted(subject_dir.glob("ch[0-9]*_*.json"))
        chapter_files = [f for f in chapter_files if "_assessment" not in f.name]

        if not chapter_files:
            print(f"⏭️  Skipping {subject}: No chapter files (run Phase 3)")
            continue

        print(f"\n{'='*60}")
        print(f"🎮 Classifying games: {subject}")
        print(f"{'='*60}")

        for ch_path in chapter_files:
            ch_data = json.loads(ch_path.read_text(encoding="utf-8"))
            ch_num = ch_data.get("chapter_number", "?")
            ch_title = ch_data.get("chapter_title", "?")

            if chapter_num is not None and ch_num != chapter_num:
                continue

            print(f"\n  📖 Chapter {ch_num}: {ch_title}")

            for section in ch_data.get("sections", []):
                sec_id = section.get("section_id", "?")
                sec_title = section.get("section_title", "?")

                # Get figures for this section
                sec_figures = [
                    f for f in figure_catalog.get("figures", [])
                    if f.get("section_id") == sec_id
                ]

                # Get equations for this section (from chapter-level)
                sec_equations = ch_data.get("equations_to_remember", [])

                prompt = prompt_template.format(
                    section_id=sec_id,
                    section_title=sec_title,
                    book_subject=subject,
                    chapter_number=ch_num,
                    content_blocks_json=json.dumps(section.get("content_blocks", []), indent=2),
                    figures_json=json.dumps(sec_figures, indent=2),
                    equations_json=json.dumps(sec_equations, indent=2),
                )

                print(f"     🎮 Section {sec_id}: {sec_title}...", end=" ")
                classification = client.enrich(prompt)

                games = classification.get("games", [])
                has_games = classification.get("has_games", False)

                if has_games and games:
                    game_types = [g.get("game_type") for g in games]
                    priorities = [g.get("repetition_priority") for g in games]
                    print(f"→ {len(games)} games ({', '.join(game_types)})")
                    if "critical" in priorities:
                        print(f"       🔴 CRITICAL repetition priority detected")
                else:
                    print(f"→ No games")

                # Save per-section
                safe_title = slugify(sec_title, max_length=40)
                output_path = output_dir / f"{sec_id}-{safe_title}_games.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(classification, f, indent=2, ensure_ascii=False)

        print(f"\n  💾 Classifications saved to: {output_dir}")

    print(f"\n✅ Phase 7 complete!")


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else None
    ch = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run(pdf, ch)
