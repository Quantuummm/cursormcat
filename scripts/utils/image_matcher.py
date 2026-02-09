"""
Image extraction from PDFs (PyMuPDF) and matching with Gemini's figure catalog.
"""

import fitz  # PyMuPDF
from pathlib import Path
from slugify import slugify


def extract_images_from_pdf(pdf_path: str | Path, output_dir: str | Path) -> list[dict]:
    """
    Extract all images from a PDF using PyMuPDF.
    Saves each image as a PNG file and returns metadata.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted images

    Returns:
        List of dicts with: filename, page, width, height, xref
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    images = []
    seen_xrefs = set()  # Avoid extracting duplicate images

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)

        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]

            # Skip duplicate images (same image reused across pages)
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)

            try:
                pix = fitz.Pixmap(doc, xref)

                # Skip tiny images (icons, bullets, decorations)
                if pix.width < 100 or pix.height < 100:
                    pix = None
                    continue

                # Convert CMYK to RGB if needed
                if pix.n >= 5:
                    pix = fitz.Pixmap(fitz.csRGB, pix)

                filename = f"page{page_num + 1:04d}_img{img_idx + 1:02d}.png"
                filepath = output_dir / filename
                pix.save(str(filepath))

                images.append({
                    "filename": filename,
                    "page": page_num + 1,
                    "width": pix.width,
                    "height": pix.height,
                    "xref": xref,
                    "file_size_kb": filepath.stat().st_size / 1024,
                })

                pix = None

            except Exception as e:
                print(f"  ⚠️  Could not extract image on page {page_num + 1}, img {img_idx + 1}: {e}")
                continue

    doc.close()
    return images


def match_images_to_figures(extracted_images: list[dict], figure_catalog: dict) -> list[dict]:
    """
    Match PyMuPDF-extracted images to Gemini's figure catalog using page numbers.
    Renames matched image files to clean figure names.

    Args:
        extracted_images: Output from extract_images_from_pdf()
        figure_catalog: Gemini's figure catalog JSON (has figure_id, page, title, etc.)

    Returns:
        List of enriched figure dicts with image_file paths
    """
    matched_figures = []

    for figure in figure_catalog.get("figures", []):
        fig_page = figure.get("page")
        fig_id = figure.get("figure_id", "unknown")
        fig_title = figure.get("title", "untitled")

        # Find images on the same page (±1 page tolerance for page number variance)
        page_images = [
            img for img in extracted_images
            if abs(img["page"] - fig_page) <= 1
        ]

        if page_images:
            # Pick the largest image on that page (most likely the figure)
            best_match = max(page_images, key=lambda x: x["width"] * x["height"])

            # Generate clean filename
            clean_name = f"fig_{fig_id}_{slugify(fig_title, max_length=50)}.png"

            matched_figures.append({
                **figure,
                "original_image_file": best_match["filename"],
                "image_file": clean_name,
                "image_dimensions": {
                    "width": best_match["width"],
                    "height": best_match["height"],
                },
                "matched": True,
            })
        else:
            matched_figures.append({
                **figure,
                "image_file": None,
                "matched": False,
                "note": f"No image found on page {fig_page} (±1). May be text-only or inline.",
            })

    return matched_figures


def rename_matched_images(matched_figures: list[dict], images_dir: str | Path):
    """
    Rename extracted image files to their clean figure names.
    Only renames successfully matched figures.
    """
    images_dir = Path(images_dir)

    for fig in matched_figures:
        if not fig.get("matched") or not fig.get("original_image_file"):
            continue

        original = images_dir / fig["original_image_file"]
        renamed = images_dir / fig["image_file"]

        if original.exists() and not renamed.exists():
            original.rename(renamed)
        elif original.exists() and renamed.exists():
            # Both exist — keep the renamed one, delete original
            original.unlink()
