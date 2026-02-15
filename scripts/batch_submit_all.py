import sys
import json
from pathlib import Path
import time
import traceback

# Add project root to sys.path
repo_root = Path(r"c:\Users\Rauf\Documents\GitHub\cursormcat")
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(repo_root / "scripts") not in sys.path:
    sys.path.insert(0, str(repo_root / "scripts"))

import config
from phases.phase1.phase1_extract_toc import run as run_phase1
from phases.phase2.phase2_extract_assessments import run as run_phase2
from phases.phase3.phase3_extract_sections import run as run_phase3
from phases.phase4.phase4_extract_glossary import run as run_phase4
from phases.phase5.phase5_catalog_figures import run as run_phase5

BOOKS = config.BOOKS

def check_exists(phase, subject, chapter=None):
    if phase == 1:
        p = repo_root / "phases/phase1/output/extracted" / subject / "_toc.json"
        return p.exists()
    if phase == 2:
        p = repo_root / "phases/phase2/output/extracted" / subject / f"ch{chapter:02d}_assessment.json"
        return p.exists()
    if phase == 3:
        d = repo_root / "phases/phase3/output/extracted" / subject
        if not d.exists(): return False
        files = list(d.glob(f"ch{chapter:02d}_*.json"))
        return len(files) > 0
    if phase == 4:
        p = repo_root / "phases/phase4/output/extracted" / subject / "_glossary.json"
        return p.exists()
    if phase == 5:
        p = repo_root / "phases/phase5/output/extracted" / subject / f"ch{chapter:02d}_figure_catalog.json"
        return p.exists()
    return False

def get_chapters(subject):
    toc_path = repo_root / "phases/phase1/output/extracted" / subject / "_toc.json"
    if not toc_path.exists():
        return []
    with open(toc_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [ch["chapter_number"] for ch in data.get("chapters", [])]

def main():
    print("🚀 Starting Batch Submission...")

    # Phase 1: TOC (Only CARS needs it according to user)
    for pdf, subject in BOOKS.items():
        if not check_exists(1, subject):
            print(f"Running Phase 1 for {subject} ({pdf})...")
            try:
                run_phase1(pdf)
            except Exception as e:
                print(f"❌ Failed Phase 1 for {subject}: {e}")

    # Reload BOOKS and subjects to ensure we have TOCs
    for pdf, subject in BOOKS.items():
        chapters = get_chapters(subject)
        if not chapters:
            print(f"⚠️ No chapters found for {subject}, skipping phases 2-5")
            continue

        # Phase 2: Assessments
        for ch in chapters:
            if not check_exists(2, subject, ch):
                print(f"Running Phase 2 for {subject} Ch {ch}...")
                try:
                    run_phase2(pdf, ch)
                except Exception as e:
                    print(f"❌ Failed Phase 2 for {subject} Ch {ch}: {e}")
                # Rate limiting is now handled dynamically in GeminiClient
                time.sleep(2)

        # Phase 3: Sections
        for ch in chapters:
            if not check_exists(3, subject, ch):
                print(f"Running Phase 3 for {subject} Ch {ch}...")
                try:
                    run_phase3(pdf, ch)
                except Exception as e:
                    print(f"❌ Failed Phase 3 for {subject} Ch {ch}: {e}")
                # Rate limiting is now handled dynamically in GeminiClient
                time.sleep(2)

        # Phase 4: Glossary
        if not check_exists(4, subject):
            print(f"Running Phase 4 for {subject}...")
            try:
                run_phase4(pdf)
            except Exception as e:
                print(f"❌ Failed Phase 4 for {subject}: {e}")
            # Rate limiting is now handled dynamically in GeminiClient
            time.sleep(2)

        # Phase 5: Figures
        for ch in chapters:
            if not check_exists(5, subject, ch):
                print(f"Running Phase 5 for {subject} Ch {ch}...")
                try:
                    run_phase5(pdf, ch)
                except Exception as e:
                    print(f"❌ Failed Phase 5 for {subject} Ch {ch}: {e}")
                # Rate limiting is now handled dynamically in GeminiClient
                time.sleep(2)

    print("✅ Batch Submission complete!")

if __name__ == "__main__":
    main()
