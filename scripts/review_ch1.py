"""Quick review of Chapter 1 proof-of-concept pipeline output."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import EXTRACTED_DIR, CLASSIFIED_DIR, STRUCTURED_DIR

print("=" * 70)
print("CHAPTER 1 PROOF-OF-CONCEPT: COMPLETE PIPELINE REVIEW")
print("=" * 70)

# --- Extraction ---
print("\n--- EXTRACTION (Phases 1-5) ---")

toc = json.loads((EXTRACTED_DIR / "biology" / "_toc.json").read_text(encoding="utf-8"))
chapters = toc["chapters"]
sections = sum(len(c["sections"]) for c in chapters)
print(f"  TOC: {len(chapters)} chapters, {sections} sections")

assess = json.loads((EXTRACTED_DIR / "biology" / "ch01_assessment.json").read_text(encoding="utf-8"))
has_wrong = sum(1 for q in assess["questions"] if q.get("wrong_explanations"))
print(f"  Assessment: {len(assess['questions'])} MCQs, {has_wrong} with wrong-answer explanations")

ch1 = json.loads((EXTRACTED_DIR / "biology" / "ch01_the-cell.json").read_text(encoding="utf-8"))
blocks = sum(len(s.get("content_blocks", [])) for s in ch1["sections"])
callouts = sum(len(s.get("callouts", [])) for s in ch1["sections"])
checks = len(ch1.get("concept_checks", []))
shared = len(ch1.get("shared_concepts", []))
print(f"  Sections: {len(ch1['sections'])} | Blocks: {blocks} | Checks: {checks} | Callouts: {callouts}")
print(f"  Shared concepts (bridges): {shared}")

glossary = json.loads((EXTRACTED_DIR / "biology" / "_glossary.json").read_text(encoding="utf-8"))
print(f"  Glossary: {len(glossary['terms'])} terms")

figs = json.loads((EXTRACTED_DIR / "biology" / "_figure_catalog.json").read_text(encoding="utf-8"))
matched = sum(1 for f in figs["figures"] if f.get("matched"))
print(f"  Figures: {figs['total_figures']} cataloged, {matched} matched to images")

img_count = len(list((Path("assets/biology/figures")).glob("*.png")))
print(f"  Images: {img_count} PNGs extracted from PDF")

# --- Games ---
print("\n--- GAME CLASSIFICATION (Phase 7) ---")
game_dir = CLASSIFIED_DIR / "biology"
total_games = 0
total_critical = 0
for gf in sorted(game_dir.glob("*.json")):
    g = json.loads(gf.read_text(encoding="utf-8"))
    games = g.get("games", [])
    total_games += len(games)
    types = [x.get("game_type", "?") for x in games]
    critical = sum(1 for x in games if x.get("repetition_priority") == "critical")
    total_critical += critical
    sec_id = g.get("section_id", gf.stem)
    if games:
        print(f"  {sec_id}: {len(games)} games ({', '.join(types)})" + (f" [{critical} CRITICAL]" if critical else ""))
    else:
        print(f"  {sec_id}: No games")
print(f"  TOTAL: {total_games} games, {total_critical} critical")

# --- Structured ---
print("\n--- GUIDED LEARNING (Phase 8, Gemini 3 Flash) ---")
struct_dir = STRUCTURED_DIR / "biology"
total_levels = 0
total_questions = 0
for sf in sorted(struct_dir.glob("*.json")):
    s = json.loads(sf.read_text(encoding="utf-8"))
    levels = s.get("levels", [])
    qs = sum(
        len(lv.get("check_questions", []))
        + (1 if lv.get("apply_question") else 0)
        for lv in levels
    )
    bridges = len(s.get("bridges", []))
    total_levels += len(levels)
    total_questions += qs
    print(f"  {sf.stem}: {len(levels)} levels, {qs} questions, {bridges} bridges")
print(f"  TOTAL: {total_levels} levels, {total_questions} questions across {len(list(struct_dir.glob('*.json')))} sections")

# --- Cost ---
print("\n--- ESTIMATED COST (all free tier, $0 actual) ---")
print("  Phase 1 (TOC):         ~$0.039")
print("  Phase 2 (Assessment):  ~$0.038")
print("  Phase 3 (Sections):    ~$0.047")
print("  Phase 4 (Glossary):    ~$0.050")
print("  Phase 5 (Figures):     ~$0.037")
print("  Phase 6 (Enrichment):  ~$0.003")
print("  Phase 7 (Games):       ~$0.010")
print("  Phase 8 (Restructure): ~$0.032")
print("  ─────────────────────────────")
print("  TOTAL Ch1 pipeline:    ~$0.256 (would cost on paid tier)")
print("  Projected full book:   ~$3.07 (12 chapters)")
print("  Projected all 7 books: ~$21.50")
print()
