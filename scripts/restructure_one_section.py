"""
Restructure a SINGLE section into guided learning format.
Faster than running Phase 8 for the whole chapter — fits within tool timeout.

Usage:
    python scripts/restructure_one_section.py biology 1 1.2
"""
import sys
import json
from pathlib import Path
from slugify import slugify

sys.path.insert(0, str(Path(__file__).parent))
from config import EXTRACTED_DIR, CLASSIFIED_DIR, STRUCTURED_DIR, LORE_DIR
from utils.gemini_client import GeminiClient
from utils.schema_validator import validate_restructured, print_validation


def _load_world():
    world_path = LORE_DIR / "world.json"
    if world_path.exists():
        return json.loads(world_path.read_text(encoding="utf-8"))
    return {}


def _companion_display_name(world: dict, subject: str) -> str:
    companion_id = world.get("regions", {}).get(subject, {}).get("companion_id")
    if companion_id:
        return world.get("characters", {}).get(companion_id, {}).get("display_name", companion_id)
    return "Companion"


def run(subject: str, chapter_num: int, section_id: str):
    client = GeminiClient()
    prompt_template = (Path(__file__).resolve().parents[1] / "phases" / "phase8" / "restructure_guided_learning.txt").read_text(encoding="utf-8")

    # Load TOC
    toc = json.loads((EXTRACTED_DIR / subject / "_toc.json").read_text(encoding="utf-8"))

    # Find chapter data
    ch_files = sorted((EXTRACTED_DIR / subject).glob(f"ch{chapter_num:02d}_*.json"))
    ch_files = [f for f in ch_files if "_assessment" not in f.name]
    if not ch_files:
        print(f"No chapter file found for ch{chapter_num}")
        return
    ch_data = json.loads(ch_files[0].read_text(encoding="utf-8"))

    # Find the target section
    target_section = None
    for sec in ch_data.get("sections", []):
        if sec.get("section_id") == section_id:
            target_section = sec
            break
    if not target_section:
        print(f"Section {section_id} not found in chapter {chapter_num}")
        return

    sec_title = target_section["section_title"]
    is_hy = target_section.get("is_high_yield", False)

    # Get AAMC categories from TOC
    aamc_categories = []
    for tch in toc.get("chapters", []):
        if tch["chapter_number"] == chapter_num:
            aamc_categories = tch.get("chapter_profile", {}).get("aamc_content_categories", [])
            break

    # Get summary
    summary_points = []
    for s in ch_data.get("summary", {}).get("by_section", []):
        if s["section_id"] == section_id:
            summary_points = s.get("summary_points", [])
            break

    # Get concept checks
    concept_checks = [q for q in ch_data.get("concept_checks", []) if q.get("section_tested") == section_id]

    # Get figures
    fig_path = EXTRACTED_DIR / subject / "_figure_catalog.json"
    figures = []
    if fig_path.exists():
        fig_cat = json.loads(fig_path.read_text(encoding="utf-8"))
        figures = [f for f in fig_cat.get("figures", []) if f.get("section_id") == section_id]

    # Get game classification
    safe_title = slugify(sec_title, max_length=40)
    game_path = CLASSIFIED_DIR / subject / f"{section_id}-{safe_title}_games.json"
    game_classification = {"has_games": False, "games": []}
    if game_path.exists():
        game_classification = json.loads(game_path.read_text(encoding="utf-8"))

    print(f"🎯 Restructuring {section_id}: {sec_title} {'[HY]' if is_hy else ''}")

    world = _load_world()
    companion_display_name = _companion_display_name(world, subject)

    prompt = prompt_template.format(
        book_subject=subject,
        chapter_number=chapter_num,
        chapter_title=ch_data.get("chapter_title", ""),
        section_id=section_id,
        section_title=sec_title,
        is_high_yield=str(is_hy).lower(),
        aamc_categories=json.dumps(aamc_categories),
        companion_display_name=companion_display_name,
        learning_objectives=json.dumps(target_section.get("learning_objectives", []), indent=2),
        content_blocks_json=json.dumps(target_section.get("content_blocks", []), indent=2),
        summary_points=json.dumps(summary_points, indent=2),
        concept_checks_json=json.dumps(concept_checks, indent=2),
        callouts_json=json.dumps(target_section.get("callouts", []), indent=2),
        figure_refs_json=json.dumps(figures, indent=2),
        game_classification_json=json.dumps(game_classification, indent=2),
    )

    print(f"   🔄 Calling Gemini 3 Flash...")
    try:
        structured = client.restructure(prompt, phase=f"P8_{section_id}")

        if isinstance(structured, list):
            if structured and isinstance(structured[0], dict) and "levels" in structured[0]:
                structured = structured[0]
            else:
                structured = {"concept_id": f"{section_id}-{safe_title}", "title": sec_title, "levels": structured}

        issues = validate_restructured(structured)
        print_validation(f"Section {section_id}", issues)

        levels = structured.get("levels", [])
        total_q = sum(len(lv.get("check_questions", [])) + (1 if lv.get("apply_question") else 0) for lv in levels)
        print(f"   Levels: {len(levels)} | Questions: {total_q}")

        output_dir = STRUCTURED_DIR / subject
        output_dir.mkdir(parents=True, exist_ok=True)
        concept_id = structured.get("concept_id", f"{section_id}-{safe_title}")
        output_path = output_dir / f"{concept_id}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(structured, f, indent=2, ensure_ascii=False)
        print(f"   💾 Saved: {output_path.name}")

    except Exception as e:
        print(f"   ❌ Failed: {e}")

    client.print_cost_summary()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python scripts/restructure_one_section.py <subject> <chapter_num> <section_id>")
        sys.exit(1)
    run(sys.argv[1], int(sys.argv[2]), sys.argv[3])
