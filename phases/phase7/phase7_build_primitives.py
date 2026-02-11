"""\
Phase 7: Build primitives (deterministic).
Replaces LLM game classification with a stable primitives layer.

Inputs:
- phases/phase1/output/extracted/{subject}/ch*_*.json           (Phase 3)
- phases/phase1/output/extracted/{subject}/_figure_catalog.json (Phase 5) [optional]
- phases/phase1/output/extracted/{subject}/_glossary.json       (Phase 4) [optional]

Outputs:
- phases/phase7/output/primitives/{subject}/{section_id}.json
"""

import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from config import SECTIONS_DIR, GLOSSARY_DIR, FIGURE_CATALOG_DIR, PRIMITIVES_DIR, BOOKS
from utils.primitives_builder import build_primitives_for_section


def run(pdf_filename: str = None, chapter_num: int = None):
    subjects = [BOOKS[pdf_filename]] if pdf_filename and pdf_filename in BOOKS else list(BOOKS.values())

    for subject in subjects:
        subject_dir = SECTIONS_DIR / subject
        glossary_dir = GLOSSARY_DIR / subject
        figure_dir = FIGURE_CATALOG_DIR / subject
        out_dir = PRIMITIVES_DIR / subject
        out_dir.mkdir(parents=True, exist_ok=True)

        # Load figure catalog
        figure_catalog = {"figures": []}
        fig_path = figure_dir / "_figure_catalog.json"
        if fig_path.exists():
            figure_catalog = json.loads(fig_path.read_text(encoding="utf-8"))
        figures = figure_catalog.get("figures", []) or []

        # Load glossary
        glossary_terms = []
        glossary_path = glossary_dir / "_glossary.json"
        if glossary_path.exists():
            glossary = json.loads(glossary_path.read_text(encoding="utf-8"))
            glossary_terms = glossary.get("terms", []) or []

        chapter_files = sorted(subject_dir.glob("ch[0-9]*_*.json"))
        chapter_files = [f for f in chapter_files if "_assessment" not in f.name]
        if not chapter_files:
            print(f"⏭️  Skipping {subject}: No chapter files (run Phase 3)")
            continue

        print(f"\n{'='*60}")
        print(f"🧱 Building primitives: {subject}")
        print(f"{'='*60}")

        for ch_path in chapter_files:
            ch_data = json.loads(ch_path.read_text(encoding="utf-8"))
            ch_num = ch_data.get("chapter_number")
            if chapter_num is not None and int(ch_num) != int(chapter_num):
                continue

            chapter_title = ch_data.get("chapter_title", "?")
            equations = ch_data.get("equations_to_remember", []) or []

            for section in ch_data.get("sections", []) or []:
                sec_id = section.get("section_id")
                if not sec_id:
                    continue
                prim = build_primitives_for_section(
                    subject=subject,
                    chapter_number=int(ch_num) if ch_num else -1,
                    chapter_title=chapter_title,
                    section=section,
                    figure_catalog=figures,
                    glossary_terms=glossary_terms,
                    equations=equations,
                )
                out_path = out_dir / f"{sec_id}.json"
                out_path.write_text(json.dumps(prim, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"  ✅ {sec_id}: terms={prim['signals']['term_count']} processes={prim['signals']['process_count']} tables={prim['signals']['table_count']} figs={prim['signals']['figure_count']}")

        print(f"\n  💾 Primitives saved to: {out_dir}")

    print("\n✅ Phase 7 complete!")


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else None
    ch = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run(pdf, ch)
