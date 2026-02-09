"""
Phase 1: Extract Table of Contents + metadata from each Kaplan PDF.
Captures: chapters, sections, HY markers, AAMC categories, chapter profiles, page ranges.

Usage:
    python scripts/phase1_extract_toc.py                    # All books
    python scripts/phase1_extract_toc.py biology.pdf        # One book
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import PDFS_DIR, EXTRACTED_DIR, PROMPTS_DIR, BOOKS
from utils.gemini_client import GeminiClient
from utils.schema_validator import validate_toc, print_validation


def run(pdf_filename: str = None):
    """Extract TOC from one or all Kaplan PDFs."""
    client = GeminiClient()

    # Load prompt template
    prompt_template = (PROMPTS_DIR / "toc_extraction.txt").read_text(encoding="utf-8")

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
        if not pdf_path.exists():
            print(f"⏭️  Skipping {subject}: {pdf_name} not found in pdfs/")
            continue

        output_dir = EXTRACTED_DIR / subject
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"📋 Extracting TOC from: {pdf_name}")
        print(f"{'='*60}")

        # Upload PDF to Gemini
        pdf_file = client.upload_pdf(pdf_path)

        # Extract TOC (light model — structured output fits easily)
        print(f"  🔍 Analyzing table of contents...")
        toc = client.extract_light(prompt_template, pdf_file, phase="P1_toc")

        # Validate
        issues = validate_toc(toc)
        print_validation("TOC extraction", issues)

        # Print summary
        chapters = toc.get("chapters", [])
        total_sections = sum(len(ch.get("sections", [])) for ch in chapters)
        print(f"\n  📊 Found:")
        print(f"     Chapters: {len(chapters)}")
        print(f"     Sections: {total_sections}")
        hy_count = sum(
            1 for ch in chapters
            for sec in ch.get("sections", [])
            if sec.get("is_high_yield")
        )
        print(f"     High-Yield sections: {hy_count}")

        # Save
        output_path = output_dir / "_toc.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(toc, f, indent=2, ensure_ascii=False)
        print(f"  💾 Saved: {output_path}")

    # Cleanup uploaded files
    client.cleanup()
    print(f"\n✅ Phase 1 complete!")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run(target)
