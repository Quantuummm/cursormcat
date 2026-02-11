# Phase 0: Extract Images

Core Function: Extract all images from each Kaplan PDF using PyMuPDF.
Role in Overall Pipeline: Produces raw figure assets and a manifest for later figure catalog matching.
Data Inputs: `pdfs/{book}.pdf`
Outputs: `phases/phase0/output/assets/{book}/figures/*.png`, `phases/phase0/output/assets/{book}/_image_manifest.json`
