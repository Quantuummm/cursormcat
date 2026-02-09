"""
Phase 2: Extract Chapter Assessment questions (diagnostic MCQs at chapter start).
Requires: Phase 1 complete (needs _toc.json for page ranges).

Usage:
    python scripts/phase2_extract_assessments.py                    # All books
    python scripts/phase2_extract_assessments.py biology.pdf        # One book
    python scripts/phase2_extract_assessments.py biology.pdf 3      # One chapter
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import PDFS_DIR, EXTRACTED_DIR, PROMPTS_DIR, BOOKS
from utils.gemini_client import GeminiClient
from utils.schema_validator import validate_assessment, print_validation


def run(pdf_filename: str = None, chapter_num: int = None):
    """Extract chapter assessments from one or all books."""
    client = GeminiClient()

    prompt_template = (PROMPTS_DIR / "chapter_assessment.txt").read_text(encoding="utf-8")

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
            print(f"⏭️  Skipping {subject}: Run Phase 1 first (_toc.json missing)")
            continue

        toc = json.loads(toc_path.read_text(encoding="utf-8"))
        pdf_file = client.upload_pdf(pdf_path)

        print(f"\n{'='*60}")
        print(f"📝 Extracting chapter assessments: {subject}")
        print(f"{'='*60}")

        for chapter in toc.get("chapters", []):
            ch_num = chapter["chapter_number"]
            ch_title = chapter["chapter_title"]

            # Skip if targeting a specific chapter
            if chapter_num is not None and ch_num != chapter_num:
                continue

            # Check if assessment pages exist
            if not chapter.get("chapter_assessment_pages"):
                print(f"  ⏭️  Chapter {ch_num}: No assessment pages listed, skipping")
                continue

            print(f"\n  📋 Chapter {ch_num}: {ch_title}")

            prompt = prompt_template.format(
                chapter_number=ch_num,
                chapter_title=ch_title,
                book_subject=subject,
            )

            assessment = client.extract(prompt, pdf_file)

            # Validate
            issues = validate_assessment(assessment)
            print_validation(f"Ch{ch_num} assessment", issues)

            q_count = len(assessment.get("questions", []))
            print(f"     Questions extracted: {q_count}")

            # Save
            output_path = EXTRACTED_DIR / subject / f"ch{ch_num:02d}_assessment.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(assessment, f, indent=2, ensure_ascii=False)
            print(f"     💾 Saved: {output_path.name}")

    client.cleanup()
    print(f"\n✅ Phase 2 complete!")


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else None
    ch = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run(pdf, ch)
