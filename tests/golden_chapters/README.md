# Golden Chapter Regression

Core Function: Run a targeted pipeline slice for a single chapter to catch regressions.
Role in Overall Pipeline: Provides a repeatable, low-cost sanity check after prompt or schema changes.
Data Inputs: pdfs/{book}.pdf and whichever extracted assets are needed for selected phases.
Outputs: Per-phase outputs under `phases/phaseX/output/...` for the selected chapter (e.g., `phases/phase1/output/extracted/`, `phases/phase7/output/primitives/`, `phases/phase8/output/structured/`, `phases/phase8_1/output/compiled/`, etc.).

Usage:
- python tests/golden_chapters/run_golden_chapter.py "MCAT Biology Review.pdf" 1 --from 3 --to 11 --verify-wrong-answers
