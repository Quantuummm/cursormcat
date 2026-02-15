"""
Phase 8: Restructure extracted content into ADHD-friendly guided learning format.
This is THE critical transformation — from flat Kaplan data to progressive game-ready lessons.

Requires: Phase 3 (sections) + Phase 5 (figures) + Phase 7 (game classification).

Usage:
    python phases/phase8/phase8_restructure_guided_learning.py                    # All books
    python phases/phase8/phase8_restructure_guided_learning.py biology.pdf        # One book
    python phases/phase8/phase8_restructure_guided_learning.py biology.pdf 3      # One chapter
"""

import sys
import json
import re
from pathlib import Path
from slugify import slugify

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from config import EXTRACTED_DIR, SECTIONS_DIR, FIGURE_CATALOG_DIR, CLASSIFIED_DIR, STRUCTURED_DIR, BOOKS, LORE_DIR
from utils.gemini_client import GeminiClient
from utils.schema_validator import validate_restructured, print_validation


# ─── Minimum learn segments per level (ADHD: need 2-3 segments before first quiz) ───
MIN_LEARN_SEGMENTS_PER_LEVEL = 2

# ─── Required final level patterns ───
MCAT_PATTERNS_TITLES = {"mcat patterns", "mcat testing patterns", "mcat strategy", "mcat question patterns"}


def _load_world():
    world_path = LORE_DIR / "world.json"
    if world_path.exists():
        return json.loads(world_path.read_text(encoding="utf-8"))
    return {}


def _load_specialists():
    spec_path = LORE_DIR / "characters" / "specialists.json"
    if spec_path.exists():
        return json.loads(spec_path.read_text(encoding="utf-8"))
    return {}


def _specialist_display_name(world: dict, specialists: dict, subject: str) -> str:
    """Get the specialist display name for a subject from the new lore structure."""
    specialist_id = world.get("subjects", {}).get(subject, {}).get("specialist_id")
    if specialist_id:
        spec = specialists.get("specialists", {}).get(specialist_id, {})
        return spec.get("display_name", specialist_id)
    return "Specialist"


def _deterministic_filename(sec_id: str, sec_title: str) -> str:
    """Generate a deterministic filename from section_id + title.
    Prevents duplicate files from Gemini returning different concept_id slugs."""
    safe = slugify(sec_title, max_length=50)
    return f"{sec_id}-{safe}.json"


def _cleanup_duplicate_outputs(output_dir: Path, sec_id: str, canonical_name: str):
    """Remove duplicate outputs for same section_id, keeping only the canonical file."""
    pattern = f"{sec_id}-*.json"
    candidates = list(output_dir.glob(pattern))
    for c in candidates:
        if c.name != canonical_name:
            archive_dir = output_dir / ".archive"
            archive_dir.mkdir(exist_ok=True)
            dest = archive_dir / c.name
            c.rename(dest)
            print(f"        🗑️  Archived duplicate: {c.name} → .archive/")


def _fix_match_up_questions(data: dict) -> dict:
    """Normalize match_up questions to use proper {items, matches} schema."""
    for level in data.get("levels", []):
        for q in level.get("check_questions", []) + ([level["apply_question"]] if level.get("apply_question") else []):
            if q.get("question_type") != "match_up":
                continue
            # Already has proper matches array — skip
            if isinstance(q.get("matches"), list) and q["matches"]:
                # Remove vestigial correct_index for match_up
                q.pop("correct_index", None)
                continue
            # Fix: options contain pre-joined strings like "Cation -> Positive"
            options = q.get("options", [])
            items = []
            matches = []
            for opt in options:
                opt_str = str(opt)
                # Try splitting on common delimiters: " -> ", " → ", ": ", " - "
                for sep in [" -> ", " → ", ": ", " – ", " — "]:
                    if sep in opt_str:
                        parts = opt_str.split(sep, 1)
                        items.append(parts[0].strip())
                        matches.append(parts[1].strip())
                        break
                else:
                    # No separator found — keep as item, leave match blank
                    items.append(opt_str)
                    matches.append("")
            if items and any(m for m in matches):
                q["options"] = items
                q["matches"] = matches
                q.pop("correct_index", None)  # Not applicable for match_up
    return data


def _ensure_min_learn_segments(data: dict, section_content: dict) -> dict:
    """Ensure every level has at least MIN_LEARN_SEGMENTS_PER_LEVEL learn segments.
    If a level has too few, synthesize additional segments from the source content blocks."""
    content_blocks = section_content.get("content_blocks", []) or []
    # Build a pool of unused content snippets for padding
    used_terms = set()
    for level in data.get("levels", []):
        for seg in level.get("learn_segments", []):
            used_terms.add((seg.get("key_term") or "").lower())

    text_pool = []
    for b in content_blocks:
        content = b.get("content", "")
        if isinstance(content, str) and len(content) > 30:
            text_pool.append(content)

    pool_idx = 0
    sec_id = data.get("section_id", "?")

    for level in data.get("levels", []):
        segments = level.get("learn_segments", []) or []
        lv = level.get("level", 1)
        while len(segments) < MIN_LEARN_SEGMENTS_PER_LEVEL and pool_idx < len(text_pool):
            # Create a supplementary learn segment from content pool
            raw = text_pool[pool_idx]
            pool_idx += 1
            # Truncate to ~50 words for narrator
            words = raw.split()
            narrator = " ".join(words[:45])
            if len(words) > 45:
                narrator += "..."
            new_seg = {
                "segment_id": f"{sec_id}-L{lv}-S{len(segments)+1}-pad",
                "speaker_id": "specialist",
                "narrator_text": narrator,
                "display_text": raw[:300],
                "key_term": None,
                "estimated_seconds": max(10, min(20, len(words) // 3)),
                "mnemonic": None,
                "figure_ref": None,
                "_auto_padded": True,
            }
            segments.append(new_seg)
        level["learn_segments"] = segments

    return data


def _has_mcat_patterns_level(data: dict) -> bool:
    """Check if a valid MCAT Patterns capstone level exists."""
    for level in data.get("levels", []):
        title = (level.get("title") or "").lower().strip()
        if any(p in title for p in MCAT_PATTERNS_TITLES):
            # Verify it actually has content (not just a stub)
            if level.get("learn_segments") and level.get("check_questions"):
                return True
    return False


def _inject_missing_pro_tips(data: dict, callouts: list, section_content: dict) -> dict:
    """Ensure pro tips exist where they should. Strategy:
    1. If Kaplan callouts (mcat_expertise type) exist but weren't included → inject them
    2. If a level has equations/calculations and no pro tip → add a generic MCAT calculation tip
    3. If a high-yield section has no pro tips at all → add a reminder tip
    """
    kaplan_tips = [c for c in callouts if c.get("type") in ("mcat_expertise", "mcat_pro_tip")]
    used_tip_texts = set()
    for level in data.get("levels", []):
        for tip in level.get("pro_tips", []) or []:
            used_tip_texts.add((tip.get("display_text") or "")[:50].lower())

    # 1. Inject unused Kaplan tips into the most relevant level
    for kt in kaplan_tips:
        tip_text = (kt.get("text") or kt.get("content") or "")
        if tip_text[:50].lower() in used_tip_texts:
            continue
        # Find the best level by keyword overlap
        best_level = None
        best_score = 0
        tip_words = set(tip_text.lower().split())
        for level in data.get("levels", []):
            level_text = " ".join(seg.get("display_text", "") for seg in level.get("learn_segments", []))
            level_words = set(level_text.lower().split())
            score = len(tip_words & level_words)
            if score > best_score:
                best_score = score
                best_level = level
        if best_level is None:
            best_level = data["levels"][-1] if data.get("levels") else None
        if best_level:
            if "pro_tips" not in best_level or best_level["pro_tips"] is None:
                best_level["pro_tips"] = []
            best_level["pro_tips"].append({
                "narrator_text": f"Quick MCAT tip. [PAUSE] {tip_text[:150]}",
                "display_text": f"🎯 **MCAT Pro Tip:** {tip_text[:200]}",
                "source": "Kaplan MCAT Expertise",
            })

    # 2. Check for calculation/equation levels without tips
    for level in data.get("levels", []):
        title_lower = (level.get("title") or "").lower()
        has_math = any(kw in title_lower for kw in ["calculation", "equation", "math", "formula", "process"])
        existing_tips = level.get("pro_tips") or []
        if has_math and not existing_tips:
            if "pro_tips" not in level or level["pro_tips"] is None:
                level["pro_tips"] = []
            level["pro_tips"].append({
                "narrator_text": "Quick test day tip. [PAUSE] On the MCAT, the periodic table and common constants are provided. [PAUSE] Focus on knowing WHEN to use each equation, not memorizing values.",
                "display_text": "🎯 **MCAT Pro Tip:** The MCAT provides the periodic table and constants. Focus on knowing *when* to apply each formula — that's what they're really testing.",
                "source": "MCAT Strategy",
            })

    # 3. High-yield sections with zero pro tips anywhere
    is_hy = data.get("is_high_yield", False)
    total_tips = sum(len(lv.get("pro_tips") or []) for lv in data.get("levels", []))
    if is_hy and total_tips == 0 and data.get("levels"):
        first_level = data["levels"][0]
        if "pro_tips" not in first_level or first_level["pro_tips"] is None:
            first_level["pro_tips"] = []
        first_level["pro_tips"].append({
            "narrator_text": "Heads up, this is high-yield. [PAUSE] The MCAT loves testing this topic. Expect one to two questions on it.",
            "display_text": "🎯 **High-Yield Alert:** This topic appears frequently on the MCAT. Pay close attention to the details here.",
            "source": "MCAT Strategy",
        })

    return data


def run(pdf_filename: str = None, chapter_num: int = None):
    """Restructure all sections into guided learning format."""
    client = GeminiClient()

    prompt_template = (Path(__file__).parent / "restructure_guided_learning.txt").read_text(encoding="utf-8")

    subjects = [BOOKS[pdf_filename]] if pdf_filename and pdf_filename in BOOKS else BOOKS.values()

    world = _load_world()
    specialists = _load_specialists()

    for subject in subjects:
        subject_dir = EXTRACTED_DIR / subject
        sections_dir = SECTIONS_DIR / subject
        figure_dir = FIGURE_CATALOG_DIR / subject
        classified_dir = CLASSIFIED_DIR / subject
        output_dir = STRUCTURED_DIR / subject
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load TOC for metadata
        toc_path = subject_dir / "_toc.json"
        if not toc_path.exists():
            print(f"⏭️  Skipping {subject}: Run Phase 1 first")
            continue
        toc = json.loads(toc_path.read_text(encoding="utf-8"))

        # Load figure catalog
        figure_catalog = {"figures": []}
        fig_path = figure_dir / "_figure_catalog.json"
        if fig_path.exists():
            figure_catalog = json.loads(fig_path.read_text(encoding="utf-8"))

        # Find all chapter extraction files
        chapter_files = sorted(sections_dir.glob("ch[0-9]*_*.json"))
        chapter_files = [f for f in chapter_files if "_assessment" not in f.name]

        if not chapter_files:
            print(f"⏭️  Skipping {subject}: No chapter files (run Phase 3)")
            continue

        print(f"\n{'='*60}")
        print(f"🧠 Restructuring guided learning: {subject}")
        print(f"{'='*60}")

        for ch_path in chapter_files:
            ch_data = json.loads(ch_path.read_text(encoding="utf-8"))
            ch_num = ch_data.get("chapter_number", "?")
            ch_title = ch_data.get("chapter_title", "?")

            if chapter_num is not None and ch_num != chapter_num:
                continue

            # Get chapter metadata from TOC
            toc_chapter = None
            for tch in toc.get("chapters", []):
                if tch["chapter_number"] == ch_num:
                    toc_chapter = tch
                    break

            aamc_categories = []
            if toc_chapter and toc_chapter.get("chapter_profile"):
                aamc_categories = toc_chapter["chapter_profile"].get("aamc_content_categories", [])

            print(f"\n  📖 Chapter {ch_num}: {ch_title}")

            # Get summary data for matching
            summary_by_section = {}
            for s in ch_data.get("summary", {}).get("by_section", []):
                summary_by_section[s["section_id"]] = s.get("summary_points", [])

            # Get concept checks by section
            checks_by_section = {}
            for q in ch_data.get("concept_checks", []):
                sec = q.get("section_tested", "unknown")
                if sec not in checks_by_section:
                    checks_by_section[sec] = []
                checks_by_section[sec].append(q)

            for section in ch_data.get("sections", []):
                sec_id = section.get("section_id", "?")
                sec_title = section.get("section_title", "?")
                is_hy = section.get("is_high_yield", False)

                print(f"\n     🎯 Section {sec_id}: {sec_title}", end="")
                if is_hy:
                    print(" [HIGH-YIELD]", end="")
                print()

                # Get figures for this section
                sec_figures = [
                    f for f in figure_catalog.get("figures", [])
                    if f.get("section_id") == sec_id
                ]

                # Get game classification
                safe_title = slugify(sec_title, max_length=40)
                game_path = classified_dir / f"{sec_id}-{safe_title}_games.json"
                game_classification = {"has_games": False, "games": []}
                if game_path.exists():
                    game_classification = json.loads(game_path.read_text(encoding="utf-8"))

                # Get callouts for this section
                callouts = section.get("callouts", [])

                # Deterministic filename — prevents duplicates from Gemini slug variance
                canonical_name = _deterministic_filename(sec_id, sec_title)
                canonical_path = output_dir / canonical_name

                # Clean up any existing duplicates for this section
                _cleanup_duplicate_outputs(output_dir, sec_id, canonical_name)

                # Skip if canonical file already exists
                if canonical_path.exists():
                    print(f"        ✅ {sec_id} (skipping - already exists: {canonical_name})")
                    continue

                specialist_display_name = _specialist_display_name(world, specialists, subject)

                # Get planet info for lore framing
                planet_id = world.get("subjects", {}).get(subject, {}).get("planet_id", "")

                # Build the restructuring prompt
                prompt = prompt_template.format(
                    book_subject=subject,
                    chapter_number=ch_num,
                    chapter_title=ch_title,
                    section_id=sec_id,
                    section_title=sec_title,
                    is_high_yield=str(is_hy).lower(),
                    aamc_categories=json.dumps(aamc_categories),
                    specialist_display_name=specialist_display_name,
                    planet_id=planet_id,
                    learning_objectives=json.dumps(section.get("learning_objectives", []), indent=2),
                    content_blocks_json=json.dumps(section.get("content_blocks", []), indent=2),
                    summary_points=json.dumps(summary_by_section.get(sec_id, []), indent=2),
                    concept_checks_json=json.dumps(checks_by_section.get(sec_id, []), indent=2),
                    callouts_json=json.dumps(callouts, indent=2),
                    figure_refs_json=json.dumps(sec_figures, indent=2),
                    game_classification_json=json.dumps(game_classification, indent=2),
                )

                print(f"        🔄 Restructuring with Gemini 3 Flash (30-90 seconds)...")

                try:
                    structured = client.restructure(prompt, phase=f"P8_restructure_{sec_id}")

                    # Handle case where Gemini returns a list instead of an object
                    if isinstance(structured, list):
                        # Take first item if it looks like a concept object
                        if structured and isinstance(structured[0], dict) and "levels" in structured[0]:
                            structured = structured[0]
                        else:
                            structured = {
                                "concept_id": f"{sec_id}-{safe_title}",
                                "title": sec_title,
                                "levels": structured if all(isinstance(x, dict) for x in structured) else [],
                            }

                    # Validate
                    issues = validate_restructured(structured)
                    print_validation(f"Section {sec_id}", issues)

                    # ─── Post-processing fixes (deterministic) ───────────

                    # Fix 1: Normalize match_up questions to proper schema
                    structured = _fix_match_up_questions(structured)

                    # Fix 2: Ensure minimum learn segments per level (ADHD: don't quiz too fast)
                    structured = _ensure_min_learn_segments(structured, section)

                    # Fix 3: Inject missing pro tips from Kaplan callouts
                    structured = _inject_missing_pro_tips(structured, callouts, section)

                    # Fix 4: Check for MCAT Patterns capstone level
                    if not _has_mcat_patterns_level(structured):
                        print(f"        ⚠️  No MCAT Patterns capstone level detected — flagging for Phase 8.2 repair")
                        structured["_needs_mcat_patterns_level"] = True

                    # Fix 5: Force deterministic concept_id to match filename
                    structured["concept_id"] = canonical_name.replace(".json", "")

                    levels = structured.get("levels", [])
                    total_questions = sum(
                        len(lv.get("check_questions", []))
                        + (1 if lv.get("apply_question") else 0)
                        for lv in levels
                    )
                    total_segments = sum(len(lv.get("learn_segments", [])) for lv in levels)
                    total_tips = sum(len(lv.get("pro_tips") or []) for lv in levels)
                    print(f"        Levels: {len(levels)}")
                    print(f"        Total learn segments: {total_segments}")
                    print(f"        Total questions: {total_questions}")
                    print(f"        Total pro tips: {total_tips}")
                    game_els = structured.get("game_elements", {})
                    has_games = game_els.get("has_games", False) if isinstance(game_els, dict) else False
                    print(f"        Has games: {has_games}")

                    # Save with deterministic filename
                    output_path = output_dir / canonical_name
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(structured, f, indent=2, ensure_ascii=False)
                    print(f"        💾 Saved: {output_path.name}")

                except Exception as e:
                    print(f"        ❌ Failed to restructure {sec_id}: {e}")
                    print(f"        ⏭️  Skipping this section, continuing with next...")
                    continue

        print(f"\n  📁 Structured files saved to: {output_dir}")

    print(f"\n✅ Phase 8 complete!")


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else None
    ch = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run(pdf, ch)
