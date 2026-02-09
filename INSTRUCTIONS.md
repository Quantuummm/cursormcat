# MCAT Content Hub — AI Agent Handoff Instructions

> **Purpose:** This document tells any AI agent (Cursor, Claude, GPT, etc.) everything
> it needs to continue building this project from exactly where it was left off.
> Last updated: February 9, 2026.

---

## 1. Project Overview

This is a **gamified MCAT study platform** that extracts content from Kaplan MCAT textbooks (PDFs) and restructures it into ADHD-friendly guided learning experiences with TTS narration, memorization games, and cross-topic bridges.

**Tech stack:** Python 3.12, Google Gemini API (free tier), PyMuPDF, Firebase (future), Google Cloud TTS (future).

**Repository:** https://github.com/Quantuummm/cursormcat

---

## 2. Current State (What's Done)

### Completed Infrastructure
- **12 pipeline scripts** (Phase 0-11) in `scripts/`
- **8 prompt templates** in `scripts/prompts/` (editable `.txt` files)
- **Utility modules:** Gemini client (with fallback + cost tracking), image matcher, schema validator
- **Config** with all paths, model settings, book definitions
- **Virtual environment** at `.venv/` with all dependencies installed

### Completed Data (Biology Book, Chapter 1 Only)
| Phase | Output | Location | Status |
|-------|--------|----------|--------|
| Phase 0 | 195 images extracted | `assets/biology/figures/` | ✅ Done |
| Phase 1 | TOC: 12 chapters, 38 sections | `extracted/biology/_toc.json` | ✅ Done |
| Phase 2 | Ch1 assessment: 15 MCQs + wrong explanations | `extracted/biology/ch01_assessment.json` | ✅ Done |
| Phase 3 | Ch1 sections: 5 sections, 92 content blocks | `extracted/biology/ch01_the-cell.json` | ✅ Done |
| Phase 4 | Glossary: 485 terms | `extracted/biology/_glossary.json` | ✅ Done |
| Phase 5 | Figures: 20 cataloged, 20 matched | `extracted/biology/_figure_catalog.json` | ✅ Done (Ch1 only) |
| Phase 6 | Wrong-answer enrichment for Ch1 assessment | Merged into `ch01_assessment.json` | ✅ Done |
| Phase 7 | Game classification: 22 games, 3 critical | `classified/biology/1.*_games.json` | ✅ Done (Ch1) |
| Phase 8 | Guided learning: 5 sections restructured | `structured/biology/1.*.json` | ✅ Done (Ch1) |
| Phase 9 | Bridge enrichment | Not started | ⬜ Pending |
| Phase 10 | TTS audio generation | Not started | ⬜ Pending (needs GCloud) |
| Phase 11 | Firestore upload | Not started | ⬜ Pending (needs Firebase) |

### Verification Status
| Section | Critical | Moderate | Status |
|---------|----------|----------|--------|
| 1.1 Cell Theory | 0 | 0 | ✅ Passed |
| 1.2 Eukaryotic Cells | 0 | 0 | ✅ Passed (after 3 fix iterations) |
| 1.3 Prokaryotic Cells | 1 | 3 | ❌ Needs more fixing |
| 1.4 Genetics & Growth | 2 | 2 | ❌ Needs more fixing |
| 1.5 Viruses | 1 | 3 | ❌ Needs more fixing |

---

## 3. How to Continue — Step by Step

### Prerequisites
1. Open project in Cursor: `C:\Users\Rauf\Documents\GitHub\cursormcat`
2. Activate venv: `.\.venv\Scripts\Activate.ps1`
3. Confirm API key works: `python -c "from scripts.config import GEMINI_API_KEY; print(len(GEMINI_API_KEY))"`
   Should print `39`.

### Step A: Fix Remaining Chapter 1 Sections (1.3, 1.4, 1.5)

Run fix → verify for each section. Max 3 loops per section:

```powershell
# For each section that NEEDS FIX:
python scripts/quick_fix.py biology 1.3 fix
python scripts/quick_fix.py biology 1.3 verify
# If still needs fix, repeat (max 3 times total)
python scripts/quick_fix.py biology 1.3 fix
python scripts/quick_fix.py biology 1.3 verify
# Check status:
python scripts/quick_fix.py biology 1.3 status

# Same for 1.4 and 1.5
python scripts/quick_fix.py biology 1.4 fix
python scripts/quick_fix.py biology 1.4 verify

python scripts/quick_fix.py biology 1.5 fix
python scripts/quick_fix.py biology 1.5 verify
```

If a section still fails after 3 fix iterations, **stop and review manually.** Open the verification file at `structured/biology/_verification/{section_id}_verification.json` to see exactly what's wrong.

### Step B: Process Remaining Chapters (2-12)

For each chapter, run phases 2, 3, 5, 6, 7, 8 in order. Phase 0 (images) and Phase 1 (TOC) and Phase 4 (glossary) are already done for the whole book.

```powershell
# Template for each chapter N (replace N with 2, 3, 4, ... 12):
python scripts/phase2_extract_assessments.py "MCAT Biology Review.pdf" N
python scripts/phase3_extract_sections.py "MCAT Biology Review.pdf" N
python scripts/phase5_catalog_figures.py "MCAT Biology Review.pdf" N
python scripts/phase6_enrich_wrong_answers.py "MCAT Biology Review.pdf"
python scripts/phase7_classify_games.py "MCAT Biology Review.pdf" N

# Then restructure each section individually (avoids timeout):
# First check what sections exist for chapter N:
python scripts/preview_toc.py biology
# Then for each section X.Y in that chapter:
python scripts/restructure_one_section.py biology N X.Y

# Then verify and fix:
python scripts/quick_fix.py biology X.Y verify
python scripts/quick_fix.py biology X.Y fix  # if needed, max 3 times
```

### Step C: Process Other Books

1. Drop the PDF into `pdfs/` named exactly as defined in `scripts/config.py`:
   - `MCAT Biochemistry Review.pdf`
   - `MCAT General Chemistry Review.pdf`
   - `MCAT Organic Chemistry Review.pdf`
   - `MCAT Physics and Math Review.pdf`
   - `MCAT Behavioral Sciences Review.pdf`
   - `MCAT Critical Analysis Review.pdf`

2. Run the full pipeline for each book:
```powershell
python scripts/phase0_extract_images.py "MCAT Biochemistry Review.pdf"
python scripts/phase1_extract_toc.py "MCAT Biochemistry Review.pdf"
python scripts/phase4_extract_glossary.py "MCAT Biochemistry Review.pdf"
# Then chapters one by one (same as Step B)
```

### Step D: Bridge Enrichment (after ALL books are processed)
```powershell
python scripts/phase9_enrich_bridges.py
```

### Step E: TTS Audio (requires Google Cloud setup)
1. Set up a Google Cloud project and enable Text-to-Speech API
2. Create a service account key and save it
3. Add to `.env`:
   ```
   GOOGLE_CLOUD_PROJECT_ID=your-project-id
   GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json
   ```
4. Run: `python scripts/phase10_generate_tts.py biology`

### Step F: Firestore Upload (requires Firebase setup)
1. Create a Firebase project at https://console.firebase.google.com
2. Enable Firestore Database
3. Add credentials to `.env`
4. Run: `python scripts/phase11_upload_firestore.py --dry-run` (preview first)
5. Run: `python scripts/phase11_upload_firestore.py biology` (actual upload)

---

## 4. Architecture Notes

### Model Strategy
- **PDF extraction (Phases 1-5):** Always uses `gemini-2.5-flash`. Gemini 3 refuses to extract verbatim text from copyrighted Kaplan books (returns `finish_reason: 4` / copyright error).
- **Generation (Phases 6-9):** Tries `gemini-3-flash-preview` first (best quality). If it fails for any reason, automatically falls back to `gemini-2.5-flash`. This fallback is built into the `GeminiClient._call_with_fallback()` method.
- **No PDF is attached to generation calls** — they work from already-extracted JSON, so no copyright trigger.

### Token Optimization
- Free tier limit: 15 requests/minute, ~1M tokens/minute
- Rate limiting is automatic (`GEMINI_DELAY_BETWEEN_REQUESTS` in config.py)
- Estimated cost per chapter: ~$0.26 (on paid tier; free tier = $0)
- Estimated cost for all 7 books: ~$21.50
- Cost tracking is automatic — every call prints token counts and running total
- Usage logs saved to `usage_*.json` files in project root

### Key Files
| File | Purpose |
|------|---------|
| `scripts/config.py` | All settings, paths, model names, book list |
| `scripts/utils/gemini_client.py` | API wrapper with fallback + cost tracking |
| `scripts/prompts/*.txt` | All prompt templates — edit these to improve output quality |
| `scripts/run_pipeline.py` | Master orchestrator (can run any range of phases) |
| `scripts/restructure_one_section.py` | Restructure a single section (avoids timeout) |
| `scripts/quick_fix.py` | Fix or verify a single section |
| `scripts/verify_content.py` | Run 3-layer verification on sections |

### Data Flow
```
Kaplan PDF
  → Phase 0: PyMuPDF extracts images → assets/{book}/figures/
  → Phase 1: Gemini extracts TOC → extracted/{book}/_toc.json
  → Phase 2: Gemini extracts assessments → extracted/{book}/ch*_assessment.json
  → Phase 3: Gemini extracts sections → extracted/{book}/ch*_{title}.json
  → Phase 4: Gemini extracts glossary → extracted/{book}/_glossary.json
  → Phase 5: Gemini catalogs figures → extracted/{book}/_figure_catalog.json
  → Phase 6: Gemini adds wrong-answer explanations → updates assessment files
  → Phase 7: Gemini classifies games → classified/{book}/*.json
  → Phase 8: Gemini restructures into guided learning → structured/{book}/*.json
  → Phase 9: Gemini enriches bridges → bridges/*.json
  → Phase 10: Google Cloud TTS → audio/{book}/{concept}/*.mp3
  → Phase 11: Upload to Firestore
```

### Structured Output Schema (Phase 8 output)
Each `structured/{book}/{concept_id}.json` contains:
- `concept_id`, `title`, `book`, `chapter`, `section_id`
- `is_high_yield`, `aamc_categories`
- `mission_briefing`: `{narrator_text, display_text}` — plays before Level 1
- `levels[]`: Array of 3-7 levels, each with:
  - `learn_segments[]`: `{segment_id, narrator_text, display_text, key_term, estimated_seconds, mnemonic, figure_ref}`
  - `check_questions[]`: `{question_id, question_type, question_text, options[], correct_index, correct_response, wrong_response, wrong_explanations{}}`
  - `apply_question`: Same structure as check question but with `scenario` and `reasoning` fields
  - `pro_tips[]`: MCAT Expertise callouts
- `bridges[]`: Cross-topic connections
- `game_elements`: Game classification data from Phase 7

### Question Types (7 varieties for ADHD engagement)
1. `snap_judgment` — True/False
2. `fill_the_gap` — Complete the sentence
3. `pick_one` — 4-option multiple choice
4. `what_breaks` — Predict consequence of failure
5. `put_in_order` — Arrange steps in sequence
6. `match_up` — Connect items from two lists
7. `spot_the_lie` — Find the false statement among true ones

### Verification System (3 layers)
1. **Automated (Layer 1):** Checks correct_index bounds, wrong_explanations completeness, narrator_text length
2. **Cross-reference (Layer 2):** Verifies key terms exist in original extraction
3. **AI Verification (Layer 3):** Gemini 3 compares structured output against original Kaplan content, flags hallucinations, wrong answers, inaccuracies

### Game Types
- `build` — Put steps of a process in order (drag-and-drop)
- `label` — Identify parts of a structure/diagram
- `enzyme` — Match enzymes to functions
- `regulate` — Apply inhibitors/activators
- `match` — Sort properties into correct categories
- `equation` — Name ↔ formula matching
- `rapid_recall` — Flash term, pick definition (timed)
- `diagram_label` — Tap regions of an image to label

---

## 5. Known Issues & Gotchas

1. **Cursor tool timeout:** Long-running Gemini calls (>90 seconds) will timeout in Cursor's tool runner. Use `scripts/restructure_one_section.py` and `scripts/quick_fix.py` to process one section at a time instead of whole chapters.

2. **Gemini 3 copyright block:** Never pass a PDF to Gemini 3 Flash with a prompt saying "extract verbatim." It will refuse. Only use 2.5 Flash for PDF extraction.

3. **Windows PowerShell encoding:** The config.py has a UTF-8 fix for Windows terminals. If you see encoding errors with emojis, ensure `sys.stdout.reconfigure(encoding="utf-8")` is running.

4. **JSON format inconsistency:** Sometimes Gemini returns a list `[{...}]` instead of an object `{...}`. All scripts handle this with `if isinstance(result, list)` checks. If you write new scripts, add this check.

5. **Verification false positives:** The AI verifier is strict. "Moderate" issues are often acceptable (rephrased terminology, additional context from AI's general knowledge). Only "critical" issues (wrong answers, factual errors) truly need fixing.

6. **Rate limiting:** Free tier = 15 RPM. The client auto-delays between calls. If you hit rate limits, increase `GEMINI_DELAY_BETWEEN_REQUESTS` in config.py.

7. **Book filenames:** Must match exactly what's in `config.py` BOOKS dict. If your PDF is named differently, update config.py.

---

## 6. Future Development Roadmap

### Immediate Next Steps
1. ☐ Finish fixing Ch1 sections 1.3, 1.4, 1.5
2. ☐ Process Biology chapters 2-12
3. ☐ Process remaining 6 Kaplan books
4. ☐ Run bridge enrichment (Phase 9) after all books done
5. ☐ Set up Firebase project + Firestore schema

### Frontend (Not Started)
- React/Next.js web app on Firebase Hosting
- Duolingo-style progressive lesson UI
- TTS audio playback synced with animated captions
- Drag-and-drop memorization games
- Bridge node graph visualization
- User authentication + progress tracking (Firebase Auth + Firestore)
- 2D tile exploration map for chapter navigation

### Backend Services (Not Started)
- Google Cloud TTS for pre-generated audio
- Cloud Storage for images + audio files
- Firestore for content delivery + user progress
- Firebase Hosting for the web app

---

## 7. Cost Summary So Far

| Phase | Model | Tokens | Est. Cost |
|-------|-------|--------|-----------|
| P1 TOC | 2.5-flash | ~240K | $0.039 |
| P2 Assessment Ch1 | 2.5-flash | ~238K | $0.038 |
| P3 Sections Ch1 | 2.5-flash | ~255K | $0.047 |
| P4 Glossary | 2.5-flash | ~259K | $0.050 |
| P5 Figures Ch1 | 2.5-flash | ~238K | $0.037 |
| P6 Wrong Answers | 3-flash | ~6.5K | $0.003 |
| P7 Games Ch1 | 3-flash | ~28K | $0.010 |
| P8 Restructure Ch1 | 3-flash | ~105K | $0.032 |
| Verification + Fixes | 3-flash | ~60K | $0.025 |
| **TOTAL** | | **~1.4M** | **~$0.28** |

**Projected remaining cost (paid tier):**
- Full Biology book: ~$3
- All 7 books: ~$21
- Free tier covers everything.
