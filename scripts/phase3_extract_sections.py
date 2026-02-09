"""
Phase 3: Extract section content (the BIG extraction).
Extracts: learning objectives, typed content blocks, summaries, concept checks,
          callouts, equations, shared concepts — all per chapter.

Requires: Phase 1 complete (needs _toc.json).

Usage:
    python scripts/phase3_extract_sections.py                    # All books
    python scripts/phase3_extract_sections.py biology.pdf        # One book
    python scripts/phase3_extract_sections.py biology.pdf 3      # One chapter
"""

import sys
import json
from pathlib import Path
from slugify import slugify

sys.path.insert(0, str(Path(__file__).parent))
from config import PDFS_DIR, EXTRACTED_DIR, PROMPTS_DIR, BOOKS
from utils.gemini_client import GeminiClient
from utils.schema_validator import validate_extraction, print_validation


def run(pdf_filename: str = None, chapter_num: int = None):
    """Extract section content from chapters."""
    client = GeminiClient()

    prompt_template = (PROMPTS_DIR / "section_extraction.txt").read_text(encoding="utf-8")

    books_to_process = {}
    if pdf_filename:
        if pdf_filename not in BOOKS:
            print(f"❌ Unknown PDF: {pdf_filename}")
            return
        books_to_process = {pdf_filename: BOOKS[pdf_filename]}
    else:
        books_to_process = BOOKS

    for pdf_name, subject in books_to_process.items():
        pdf_path = PDFS_DIR / pdf_name
        toc_path = EXTRACTED_DIR / subject / "_toc.json"

        if not pdf_path.exists():
            print(f"⏭️  Skipping {subject}: PDF not found")
            continue
        if not toc_path.exists():
            print(f"⏭️  Skipping {subject}: Run Phase 1 first")
            continue

        toc = json.loads(toc_path.read_text(encoding="utf-8"))
        pdf_file = client.upload_pdf(pdf_path)

        print(f"\n{'='*60}")
        print(f"📚 Extracting section content: {subject}")
        print(f"{'='*60}")

        for chapter in toc.get("chapters", []):
            ch_num = chapter["chapter_number"]
            ch_title = chapter["chapter_title"]

            if chapter_num is not None and ch_num != chapter_num:
                continue

            sections = chapter.get("sections", [])
            section_list = ", ".join(
                f"{s['section_id']} {s['section_title']}" for s in sections
            )

            print(f"\n  📖 Chapter {ch_num}: {ch_title} ({len(sections)} sections)")

            prompt = prompt_template.format(
                chapter_number=ch_num,
                chapter_title=ch_title,
                section_list=section_list,
                book_subject=subject,
            )

            print(f"     🔍 Extracting (this may take 30-60 seconds)...")
            chapter_data = client.extract(prompt, pdf_file)

            # Validate
            issues = validate_extraction(chapter_data)
            print_validation(f"Ch{ch_num} sections", issues)

            # Print summary
            extracted_sections = chapter_data.get("sections", [])
            total_blocks = sum(
                len(s.get("content_blocks", [])) for s in extracted_sections
            )
            total_checks = len(chapter_data.get("concept_checks", []))
            total_callouts = sum(
                len(s.get("callouts", [])) for s in extracted_sections
            )
            print(f"     Sections: {len(extracted_sections)}")
            print(f"     Content blocks: {total_blocks}")
            print(f"     Concept checks: {total_checks}")
            print(f"     Callouts: {total_callouts}")
            print(f"     Equations: {len(chapter_data.get('equations_to_remember', []))}")
            print(f"     Shared concepts: {len(chapter_data.get('shared_concepts', []))}")

            # Save
            safe_title = slugify(ch_title, max_length=40)
            output_path = EXTRACTED_DIR / subject / f"ch{ch_num:02d}_{safe_title}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(chapter_data, f, indent=2, ensure_ascii=False)
            print(f"     💾 Saved: {output_path.name}")

    client.cleanup()
    print(f"\n✅ Phase 3 complete!")


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else None
    ch = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run(pdf, ch)
