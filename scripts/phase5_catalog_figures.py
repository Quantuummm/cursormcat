"""
Phase 5: Catalog all figures/diagrams using Gemini + match with extracted images.
Requires: Phase 0 (images extracted) + Phase 1 (TOC) complete.

Usage:
    python scripts/phase5_catalog_figures.py                    # All books
    python scripts/phase5_catalog_figures.py biology.pdf        # One book
    python scripts/phase5_catalog_figures.py biology.pdf 3      # One chapter
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import PDFS_DIR, EXTRACTED_DIR, ASSETS_DIR, PROMPTS_DIR, BOOKS
from utils.gemini_client import GeminiClient
from utils.image_matcher import match_images_to_figures, rename_matched_images


def run(pdf_filename: str = None, chapter_num: int = None):
    """Catalog figures and match with extracted images."""
    client = GeminiClient()

    prompt_template = (PROMPTS_DIR / "figure_catalog.txt").read_text(encoding="utf-8")

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
        manifest_path = ASSETS_DIR / subject / "_image_manifest.json"

        if not pdf_path.exists():
            print(f"⏭️  Skipping {subject}: PDF not found")
            continue
        if not toc_path.exists():
            print(f"⏭️  Skipping {subject}: Run Phase 1 first")
            continue

        toc = json.loads(toc_path.read_text(encoding="utf-8"))

        # Load image manifest from Phase 0
        extracted_images = []
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            extracted_images = manifest.get("images", [])
            print(f"  📸 Loaded {len(extracted_images)} extracted images for matching")
        else:
            print(f"  ⚠️  No image manifest found — run Phase 0 first for image matching")

        pdf_file = client.upload_pdf(pdf_path)

        print(f"\n{'='*60}")
        print(f"🖼️  Cataloging figures: {subject}")
        print(f"{'='*60}")

        all_figures = []

        for chapter in toc.get("chapters", []):
            ch_num = chapter["chapter_number"]
            ch_title = chapter["chapter_title"]

            if chapter_num is not None and ch_num != chapter_num:
                continue

            print(f"\n  📖 Chapter {ch_num}: {ch_title}")

            prompt = prompt_template.format(
                chapter_number=ch_num,
                chapter_title=ch_title,
                book_subject=subject,
            )

            print(f"     🔍 Identifying figures...")
            catalog = client.extract(prompt, pdf_file)

            ch_figures = catalog.get("figures", [])
            print(f"     Found {len(ch_figures)} figures")

            # Match with extracted images
            if extracted_images:
                matched = match_images_to_figures(extracted_images, catalog)
                matched_count = sum(1 for f in matched if f.get("matched"))
                print(f"     Matched with images: {matched_count}/{len(ch_figures)}")

                # Rename matched images to clean names
                images_dir = ASSETS_DIR / subject / "figures"
                rename_matched_images(matched, images_dir)

                all_figures.extend(matched)
            else:
                all_figures.extend(ch_figures)

        # Save complete figure catalog
        catalog_output = {
            "book": subject,
            "total_figures": len(all_figures),
            "figures": all_figures,
        }

        output_path = EXTRACTED_DIR / subject / "_figure_catalog.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(catalog_output, f, indent=2, ensure_ascii=False)
        print(f"\n  💾 Complete catalog saved: {output_path.name}")
        print(f"     Total figures cataloged: {len(all_figures)}")

    client.cleanup()
    print(f"\n✅ Phase 5 complete!")


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else None
    ch = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run(pdf, ch)
