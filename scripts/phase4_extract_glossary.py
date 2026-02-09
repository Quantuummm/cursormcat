"""
Phase 4: Extract glossary from each Kaplan book.
Requires: Phase 1 complete (needs _toc.json for glossary page range).

Usage:
    python scripts/phase4_extract_glossary.py                    # All books
    python scripts/phase4_extract_glossary.py biology.pdf        # One book
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import PDFS_DIR, EXTRACTED_DIR, PROMPTS_DIR, BOOKS
from utils.gemini_client import GeminiClient
from utils.schema_validator import validate_glossary, print_validation


def run(pdf_filename: str = None):
    """Extract glossary from one or all books."""
    client = GeminiClient()

    prompt_template = (PROMPTS_DIR / "glossary_extraction.txt").read_text(encoding="utf-8")

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

        if not toc.get("glossary_pages"):
            print(f"⏭️  Skipping {subject}: No glossary pages in TOC")
            continue

        print(f"\n{'='*60}")
        print(f"📖 Extracting glossary: {subject}")
        print(f"{'='*60}")

        pdf_file = client.upload_pdf(pdf_path)

        prompt = prompt_template.format(book_subject=subject)

        print(f"  🔍 Extracting glossary terms...")
        glossary = client.extract(prompt, pdf_file)

        # Validate
        issues = validate_glossary(glossary)
        print_validation("Glossary", issues)

        terms = glossary.get("terms", [])
        print(f"  📊 Terms extracted: {len(terms)}")
        if terms:
            letters = set(t.get("first_letter", "?") for t in terms)
            print(f"     Letters covered: {', '.join(sorted(letters))}")

        # Save
        output_path = EXTRACTED_DIR / subject / "_glossary.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(glossary, f, indent=2, ensure_ascii=False)
        print(f"  💾 Saved: {output_path.name}")

    client.cleanup()
    print(f"\n✅ Phase 4 complete!")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run(target)
