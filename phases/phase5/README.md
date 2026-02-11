# Phase 5: Catalog Figures

Core Function: Catalog all figures with IDs, captions, section IDs, and structured fields; match figures to extracted images.
Role in Overall Pipeline: Enables figure references in guided learning and diagram-based modes.
Data Inputs:
- `pdfs/{book}.pdf`
- `phases/phase1/output/extracted/{book}/_toc.json`
- `phases/phase0/output/assets/{book}/_image_manifest.json`

Outputs:
- `phases/phase5/output/extracted/{book}/_figure_catalog.json`
- renamed images: `phases/phase0/output/assets/{book}/figures/*.png`
