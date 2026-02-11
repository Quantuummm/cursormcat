# MCAT Content Hub — Updated Instructions (Condensed)

Last updated: 2026-02-09

## Purpose
Extract Kaplan MCAT PDFs into structured, ADHD-friendly guided learning content and deterministic game-ready modes.

## Quick Start
1) Activate venv: `.\.venv\Scripts\Activate.ps1`
2) Verify Gemini key: `python -c "from scripts.config import GEMINI_API_KEY; print(len(GEMINI_API_KEY))"` (should be > 0)
3) Run a pipeline slice:
   - `python scripts/run_pipeline.py "MCAT Biology Review.pdf" 1 --from 3 --to 11 --verify-wrong-answers`

## Session Start Protocol
At the start of every session:
1) Check for existing progress: `python scripts/run_pipeline.py --report`
2) Analyze the global progress tracker: Identify which subjects and chapters have reached which phases.
3) Cross-reference with prerequisites: The pipeline now validates prerequisites (e.g., Phase 2 requires Phase 1). If you attempt to start a phase without its prerequisites, the orchestrator will block the run and tell you what is missing.
4) If resuming the most recent task, use: `python scripts/run_pipeline.py --resume`
5) To start a specific subject/chapter: `python scripts/run_pipeline.py "Subject.pdf" [CH] --from [PHASE]`

## Phase Map
- Phase 0: Extract images (PyMuPDF)
- Phase 1: Extract TOC
- Phase 2: Extract chapter assessments
- Phase 3: Extract section content
- Phase 4: Extract glossary
- Phase 5: Catalog figures
- Phase 6: Enrich wrong-answer explanations (Output to phase6/output)
- Phase 6.1: Verify & Auto-fix explanations (Mandatory loop, output to phase6_1/output)
- Phase 7: Build primitives (deterministic)
- Phase 7.1: Compile modes (engine-ready games)
- Phase 7 Legacy: LLM game classification (optional fallback)
- Phase 8: Restructure guided learning
- Phase 9: Enrich bridges
- Phase 10: Generate TTS audio (Google Cloud)
- Phase 11: Upload to Firestore

## Folder Layout (Key Paths)
- phases/phaseX/: Phase scripts + their prompt files
- scripts/: Orchestration, utilities, config, verification tools
- Per-phase outputs now live under each phase folder, e.g.:
  - `phases/phase0/output/assets/`  (images extracted)
  - `phases/phase1/output/extracted/` (TOC, metadata)
  - `phases/phase2/output/extracted/` (raw assessments)
  - `phases/phase3/output/extracted/` (sections)
  - `phases/phase4/output/extracted/` (glossary)
  - `phases/phase5/output/extracted/` (figure catalog)
  - `phases/phase6/output/enriched/` (assessments with AI-wrong-explanations)
  - `phases/phase6_1/output/verified/` (audited & fixed assessments + reports)
  - `phases/phase7/output/primitives/`
  - `phases/phase8_1/output/compiled/`
  - `phases/phase7_legacy/output/classified/`
  - `phases/phase8/output/structured/`
  - `phases/phase9/output/bridges/`
  - `phases/phase10/output/audio/`

Migration: To move existing top-level output folders into their new phase locations run:

```
python scripts/migrate_outputs_to_phases.py --dry-run
# inspect results, then:
python scripts/migrate_outputs_to_phases.py --force
```

## Running Phases
Use the orchestrator:
- `python scripts/run_pipeline.py "MCAT Biology Review.pdf" 1 --from 2 --to 8`
- The `run_pipeline.py` now includes Phase 6.1 automatically after Phase 6.
- To run from checkpoint: `python scripts/run_pipeline.py --resume`

Run a single phase script directly (examples):
- `python phases/phase3/phase3_extract_sections.py "MCAT Biology Review.pdf" 1`
- `python phases/phase7/phase7_build_primitives.py "MCAT Biology Review.pdf" 1`
- `python phases/phase8_1/phase8_1_compile_modes.py "MCAT Biology Review.pdf" 1`

## Golden Chapter Regression
- `python tests/golden_chapters/run_golden_chapter.py "MCAT Biology Review.pdf" 1 --from 3 --to 11 --verify-wrong-answers`

## Model Strategy (Feb 10 Update)
- **Primary Model**: `gemini-3-flash-preview` is now used for ALL phases (1–11).
- **Fallback**: `gemini-2.5-flash` is used if Gemini 3 fails or blocks text.
- **Model Choice**: The `Flash` series is preferred over `Pro` for high-volume extraction speed.

## Notes
- Phase 7 is deterministic primitives. Phase 7.1 compiles modes. Legacy LLM game classification is optional only.
- Prompts now live inside each phase folder.
- Verification tools:
  - Wrong answers: phases/phase6_1/phase6_1_verify_wrong_answers.py
  - Guided learning accuracy: scripts/verify_content.py + scripts/quick_fix.py
