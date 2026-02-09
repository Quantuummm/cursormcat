"""
Phase 0: Extract images from Kaplan PDFs using PyMuPDF.
This runs BEFORE any Gemini calls — no API key needed.

Usage:
    python scripts/phase0_extract_images.py                    # All books
    python scripts/phase0_extract_images.py biology.pdf        # One book
"""

import sys
from pathlib import Path
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from config import PDFS_DIR, ASSETS_DIR, BOOKS
from utils.image_matcher import extract_images_from_pdf


def run(pdf_filename: str = None):
    """Extract images from one or all Kaplan PDFs."""
    books_to_process = {}

    if pdf_filename:
        if pdf_filename not in BOOKS:
            print(f"❌ Unknown PDF: {pdf_filename}")
            print(f"   Available: {', '.join(BOOKS.keys())}")
            return
        books_to_process = {pdf_filename: BOOKS[pdf_filename]}
    else:
        books_to_process = BOOKS

    for pdf_name, subject in books_to_process.items():
        pdf_path = PDFS_DIR / pdf_name
        if not pdf_path.exists():
            print(f"⏭️  Skipping {subject}: {pdf_name} not found in pdfs/")
            continue

        output_dir = ASSETS_DIR / subject / "figures"
        print(f"\n{'='*60}")
        print(f"📸 Extracting images from: {pdf_name}")
        print(f"   Output: {output_dir}")
        print(f"{'='*60}")

        images = extract_images_from_pdf(pdf_path, output_dir)

        print(f"\n  📊 Results:")
        print(f"     Total images extracted: {len(images)}")
        if images:
            total_size = sum(img["file_size_kb"] for img in images)
            print(f"     Total size: {total_size:.1f} KB")
            print(f"     Largest: {max(images, key=lambda x: x['file_size_kb'])['filename']} "
                  f"({max(img['file_size_kb'] for img in images):.1f} KB)")
            print(f"     Pages with images: {len(set(img['page'] for img in images))}")

        # Save image manifest for later matching
        import json
        manifest_path = ASSETS_DIR / subject / "_image_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({"book": subject, "total_images": len(images), "images": images}, f, indent=2)
        print(f"  💾 Manifest saved: {manifest_path.name}")

    print(f"\n✅ Phase 0 complete!")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run(target)
