"""
Phase 8.1: Compile engine-ready game modes ("mode compiler").

Inputs:
- `phases/phase3/output/extracted/{subject}/ch*_*.json`           (Phase 3)
- `phases/phase5/output/extracted/{subject}/_figure_catalog.json` (Phase 5)
- `phases/phase4/output/extracted/{subject}/_glossary.json`       (Phase 4) [optional but recommended]
- `phases/phase7_legacy/output/classified/{subject}/*_games.json` (Phase 7 legacy) [optional]
- `phases/phase8/output/structured/{subject}/*.json`              (Phase 8) [optional, improves key_terms]
- `phases/phase8_2/output/verified/{subject}/*.json`              (Phase 8.2) [Preferred source for guided learning]

Outputs:
- `phases/phase8_1/output/compiled/{subject}/{section_id}_modes.json`
"""

import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from config import SECTIONS_DIR, GLOSSARY_DIR, FIGURE_CATALOG_DIR, CLASSIFIED_DIR, STRUCTURED_DIR, VERIFIED_STRUCTURED_DIR, COMPILED_DIR, PRIMITIVES_DIR, BOOKS, PROJECT_ROOT
from utils.mode_compiler import (
    CompilationContext, compile_modes_for_section, load_world_config,
    compile_equation_forge_book_wide, compile_equation_forge_multibook,
)
from utils.primitives_builder import build_primitives_for_section


def run(pdf_filename: str = None, chapter_num: int = None):
    world = load_world_config(PROJECT_ROOT)

    subjects = [BOOKS[pdf_filename]] if pdf_filename and pdf_filename in BOOKS else BOOKS.values()

    for subject in subjects:
        subject_dir = SECTIONS_DIR / subject
        glossary_dir = GLOSSARY_DIR / subject
        figure_dir = FIGURE_CATALOG_DIR / subject
        classified_dir = CLASSIFIED_DIR / subject
        structured_dir = STRUCTURED_DIR / subject
        output_dir = COMPILED_DIR / subject
        primitives_dir = PRIMITIVES_DIR / subject
        output_dir.mkdir(parents=True, exist_ok=True)
        primitives_dir.mkdir(parents=True, exist_ok=True)

        # Load figure catalog
        figure_catalog = {"figures": []}
        fig_path = figure_dir / "_figure_catalog.json"
        if fig_path.exists():
            figure_catalog = json.loads(fig_path.read_text(encoding="utf-8"))

        # Load glossary
        glossary_terms = []
        glossary_path = glossary_dir / "_glossary.json"
        if glossary_path.exists():
            glossary = json.loads(glossary_path.read_text(encoding="utf-8"))
            glossary_terms = glossary.get("terms", []) or []

        # Find chapter files
        chapter_files = sorted(subject_dir.glob("ch[0-9]*_*.json"))
        chapter_files = [f for f in chapter_files if "_assessment" not in f.name]
        if not chapter_files:
            print(f"⏭️  Skipping {subject}: No chapter files (run Phase 3)")
            continue

        print(f"\n{'='*60}")
        print(f"🧩 Compiling modes: {subject}")
        print(f"{'='*60}")

        for ch_path in chapter_files:
            ch_data = json.loads(ch_path.read_text(encoding="utf-8"))
            
            # Handle both data formats from Phase 3:
            # 1. Top-level: {"chapter_number": 1, "sections": [...]}
            # 2. Nested: {"sections": [{"chapter_number": 1, "sections": [...]}]}
            if "chapter_number" not in ch_data and "sections" in ch_data:
                # Nested format - unwrap
                if ch_data["sections"] and isinstance(ch_data["sections"][0], dict):
                    ch_data = ch_data["sections"][0]
            
            ch_num = ch_data.get("chapter_number")
            chapter_title = ch_data.get("chapter_title", "?")
            if chapter_num is not None and ch_num != chapter_num:
                continue

            equations = ch_data.get("equations_to_remember", []) or []
            print(f"\n  📖 Chapter {ch_num}: {chapter_title}")
            chapter_title = ch_data.get("chapter_title", "?")

            for section in ch_data.get("sections", []) or []:
                sec_id = section.get("section_id", "?")
                sec_title = section.get("section_title", "?")

                # gather figures for section
                sec_figures = [f for f in figure_catalog.get("figures", []) if f.get("section_id") == sec_id]

                # PREFER Phase 8.2 verified output, fallback to Phase 8 structured
                structured_section = None
                verified_dir = VERIFIED_STRUCTURED_DIR / subject
                if verified_dir.exists():
                    candidates = list(verified_dir.glob(f"{sec_id}-*.json"))
                    if candidates:
                        structured_section = json.loads(candidates[0].read_text(encoding="utf-8"))
                        print(f"      🛡️  Using verified content for {sec_id}")

                if structured_section is None and structured_dir.exists():
                    # structured filenames often start with "{section_id}-" or "1.2-..."
                    candidates = list(structured_dir.glob(f"{sec_id}-*.json"))
                    if candidates:
                        structured_section = json.loads(candidates[0].read_text(encoding="utf-8"))

                # optional: load Phase 7 classification
                game_classification = None
                if classified_dir.exists():
                    candidates = list(classified_dir.glob(f"{sec_id}-*_games.json"))
                    if candidates:
                        game_classification = json.loads(candidates[0].read_text(encoding="utf-8"))

                ctx = CompilationContext(
                    subject=subject,
                    chapter_number=int(ch_num) if ch_num is not None else -1,
                    section_id=sec_id,
                    rng_seed=abs(hash(f"{subject}|{ch_num}|{sec_id}")) % (2**31),
                    world=world,
                    project_root=PROJECT_ROOT,
                )

                # Build or load primitives for this section (deterministic, game-ready data layer)
                prim_path = primitives_dir / f"{sec_id}.json"
                primitives = None
                if prim_path.exists():
                    try:
                        primitives = json.loads(prim_path.read_text(encoding="utf-8"))
                    except Exception:
                        primitives = None
                if primitives is None:
                    primitives = build_primitives_for_section(
                        subject=subject,
                        chapter_number=int(ch_num) if ch_num is not None else -1,
                        chapter_title=chapter_title,
                        section=section,
                        figure_catalog=figure_catalog.get("figures", []) or [],
                        glossary_terms=glossary_terms,
                        equations=equations,
                    )
                    prim_path.write_text(json.dumps(primitives, indent=2, ensure_ascii=False), encoding="utf-8")

                compiled = compile_modes_for_section(
                    ctx=ctx,
                    section=section,
                    figures=sec_figures,
                    equations=equations,
                    glossary_terms=glossary_terms,
                    primitives=primitives,
                    structured_section=structured_section,
                    game_classification=game_classification,
                )

                out_path = output_dir / f"{sec_id}_modes.json"
                out_path.write_text(json.dumps(compiled, indent=2, ensure_ascii=False), encoding="utf-8")

                mode_count = len(compiled.get("mode_instances", []))
                print(f"     ✅ {sec_id} {sec_title}: {mode_count} modes")

        print(f"\n  💾 Compiled modes saved to: {output_dir}")

    # ─── Book-wide equation forge for each subject ───
    print(f"\n{'='*60}")
    print(f"🧪 Compiling book-wide equation forge modes")
    print(f"{'='*60}")
    all_subjects_processed = []
    for subject in (BOOKS.values() if not pdf_filename else [BOOKS[pdf_filename]]):
        book_eq = compile_equation_forge_book_wide(PROJECT_ROOT, subject, world)
        if book_eq:
            out_dir = COMPILED_DIR / subject
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / "_book_wide_equation_forge.json"
            out_path.write_text(json.dumps(book_eq, indent=2, ensure_ascii=False), encoding="utf-8")
            eq_count = book_eq.get("total_equations", 0)
            mode_count = len(book_eq.get("mode_instances", []))
            print(f"  ✅ {subject}: {eq_count} equations → {mode_count} modes")
            all_subjects_processed.append(subject)
        else:
            print(f"  ⏭️  {subject}: Not enough equations for book-wide forge")

    # ─── Multi-book equation forge (all science books) ───
    if len(all_subjects_processed) >= 2:
        print(f"\n{'='*60}")
        print(f"🌐 Compiling multi-book equation forge")
        print(f"{'='*60}")
        multibook_eq = compile_equation_forge_multibook(PROJECT_ROOT, all_subjects_processed, world)
        if multibook_eq:
            out_dir = COMPILED_DIR / "_multibook"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / "_multibook_equation_forge.json"
            out_path.write_text(json.dumps(multibook_eq, indent=2, ensure_ascii=False), encoding="utf-8")
            eq_count = multibook_eq.get("total_equations", 0)
            subj_breakdown = multibook_eq.get("equations_by_subject", {})
            print(f"  ✅ Multi-book: {eq_count} equations from {len(subj_breakdown)} subjects")
            for s, c in subj_breakdown.items():
                print(f"      📘 {s}: {c} equations")
        else:
            print(f"  ⏭️  Not enough equations across subjects for multi-book forge")

    print("\n✅ Phase 8.1 complete!")


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else None
    ch = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run(pdf, ch)
