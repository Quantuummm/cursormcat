"""
Quick Test: Verify Phase 7 → Phase 8.1 pipeline readiness

Checks that all input data from phases 3, 4, 5 is present before running
the main pipeline.

Usage:
    python scripts/test_phase7_8_1_readiness.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from config import SECTIONS_DIR, GLOSSARY_DIR, FIGURE_CATALOG_DIR, BOOKS

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def check_readiness():
    """Check if all required inputs from phases 3, 4, 5 exist."""
    print("\n" + "="*70)
    print("🔍 Phase 7 → 8.1 Pipeline Readiness Check")
    print("="*70)
    
    issues = []
    ready_count = 0
    
    for subject in BOOKS.values():
        print(f"\n📚 {subject.upper()}")
        
        # Check Phase 3 (sections)
        sections_dir = SECTIONS_DIR / subject
        section_files = list(sections_dir.glob("ch[0-9]*_*.json"))
        section_files = [f for f in section_files if "_assessment" not in f.name]
        
        if not section_files:
            print(f"  ❌ Phase 3: No section files found")
            issues.append(f"{subject}: Missing Phase 3 sections")
        else:
            print(f"  ✅ Phase 3: {len(section_files)} section files")
        
        # Check Phase 4 (glossary)
        glossary_path = GLOSSARY_DIR / subject / "_glossary.json"
        if subject == "cars":
            print(f"  ⏭️  Phase 4: Skipped (CARS has no glossary)")
        elif not glossary_path.exists():
            print(f"  ⚠️  Phase 4: Glossary not found (optional)")
        else:
            print(f"  ✅ Phase 4: Glossary found")
        
        # Check Phase 5 (figure catalog)
        fig_catalog_path = FIGURE_CATALOG_DIR / subject / "_figure_catalog.json"
        if subject == "cars":
            print(f"  ⏭️  Phase 5: Skipped (CARS has no figures)")
        elif not fig_catalog_path.exists():
            print(f"  ⚠️  Phase 5: Figure catalog not found (optional)")
        else:
            print(f"  ✅ Phase 5: Figure catalog found")
        
        # Overall readiness
        if section_files:
            ready_count += 1
            print(f"  ✅ Ready for Phase 7 → 8.1")
        else:
            print(f"  ❌ Not ready (missing core data)")
    
    print("\n" + "="*70)
    print(f"📊 Summary: {ready_count}/{len(BOOKS)} subjects ready")
    print("="*70)
    
    if issues:
        print("\n⚠️  Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
        print("\n❌ Pipeline cannot run until Phase 3 completes for all subjects.")
        print("\nTo fix, run:")
        print("  python scripts/parallel_pipeline.py --wave 1")
        return False
    else:
        print("\n✅ All subjects ready! You can now run:")
        print("\n  python scripts/run_phase7_to_phase8_1.py")
        print("\nOr for parallel processing:")
        print("  python scripts/run_phase7_to_phase8_1.py --parallel")
        return True


if __name__ == "__main__":
    ready = check_readiness()
    sys.exit(0 if ready else 1)
