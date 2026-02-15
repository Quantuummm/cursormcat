"""
Execute Phase 7 → Phase 8.1 pipeline for all subjects.

This script bypasses phases 6, 6.1, and 8, going directly from Phase 5 outputs
into Phase 7 (build primitives) and then Phase 8.1 (compile modes).

Both phases are deterministic and don't require API calls, so they run fast.
After completion, runs validation to verify data integrity.

Usage:
    python scripts/run_phase7_to_phase8_1.py                    # All subjects
    python scripts/run_phase7_to_phase8_1.py --subject gen_chem # Single subject
    python scripts/run_phase7_to_phase8_1.py --validate-only    # Only run validation
"""

import sys
import os
import time
import argparse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Fix Windows encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from config import BOOKS, PRIMITIVES_DIR, COMPILED_DIR

# Map PDF filenames to subjects
SUBJECTS = list(BOOKS.values())
NUM_CHAPTERS = 12


def check_phase7_complete(subject: str) -> dict:
    """Check which chapters have Phase 7 primitives."""
    prim_dir = PRIMITIVES_DIR / subject
    if not prim_dir.exists():
        return {}
    
    files = list(prim_dir.glob("*.json"))
    # Parse section IDs like "1.1" from filenames
    completed = {}
    for f in files:
        name = f.stem  # e.g., "1.1"
        if "." in name:
            ch = int(name.split(".")[0])
            completed[ch] = completed.get(ch, 0) + 1
    return completed


def check_phase8_1_complete(subject: str) -> dict:
    """Check which chapters have Phase 8.1 compiled modes."""
    comp_dir = COMPILED_DIR / subject
    if not comp_dir.exists():
        return {}
    
    files = list(comp_dir.glob("*_modes.json"))
    completed = {}
    for f in files:
        name = f.stem.replace("_modes", "")  # e.g., "1.1"
        if "." in name:
            ch = int(name.split(".")[0])
            completed[ch] = completed.get(ch, 0) + 1
    return completed


def run_phase7_for_subject(subject: str):
    """Run Phase 7 (build primitives) for a single subject."""
    pdf = [k for k, v in BOOKS.items() if v == subject][0]
    
    print(f"\n{'='*70}")
    print(f"🧱 Phase 7: Building primitives for {subject}")
    print(f"{'='*70}")
    
    from phases.phase7.phase7_build_primitives import run
    
    start = time.time()
    try:
        run(pdf_filename=pdf, chapter_num=None)
        elapsed = time.time() - start
        print(f"  ✅ {subject} Phase 7 complete ({int(elapsed)}s)")
        return {"status": "success", "subject": subject, "phase": 7, "elapsed": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        print(f"  ❌ {subject} Phase 7 failed: {e}")
        return {"status": "failed", "subject": subject, "phase": 7, "elapsed": elapsed, "error": str(e)}


def run_phase8_1_for_subject(subject: str):
    """Run Phase 8.1 (compile modes) for a single subject."""
    pdf = [k for k, v in BOOKS.items() if v == subject][0]
    
    print(f"\n{'='*70}")
    print(f"🧩 Phase 8.1: Compiling modes for {subject}")
    print(f"{'='*70}")
    
    from phases.phase8_1.phase8_1_compile_modes import run
    
    start = time.time()
    try:
        run(pdf_filename=pdf, chapter_num=None)
        elapsed = time.time() - start
        print(f"  ✅ {subject} Phase 8.1 complete ({int(elapsed)}s)")
        return {"status": "success", "subject": subject, "phase": 8.1, "elapsed": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        print(f"  ❌ {subject} Phase 8.1 failed: {e}")
        return {"status": "failed", "subject": subject, "phase": 8.1, "elapsed": elapsed, "error": str(e)}


def run_validation(subject: str = None):
    """Run validation for compiled modes."""
    print(f"\n{'='*70}")
    print(f"🔍 Running validation for Phase 8.1 outputs")
    print(f"{'='*70}")
    
    validation_script = REPO_ROOT / "phases" / "phase8_1" / "validation" / "verify_compiled_modes.py"
    
    if not validation_script.exists():
        print(f"  ⚠️  Validation script not found: {validation_script}")
        return
    
    import subprocess
    
    subjects_to_validate = [subject] if subject else SUBJECTS
    
    for subj in subjects_to_validate:
        print(f"\n  🔍 Validating {subj}...")
        
        cmd = [sys.executable, str(validation_script), "--subject", subj]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=300,
                encoding="utf-8",
                errors="replace",
            )
            
            if result.returncode == 0:
                print(f"  ✅ {subj} validation passed")
                # Show summary from output
                lines = result.stdout.strip().split("\n")
                for line in lines[-10:]:  # Show last 10 lines
                    if line.strip():
                        print(f"     {line}")
            else:
                print(f"  ❌ {subj} validation found issues")
                err_lines = result.stderr.strip().split("\n")[:10]
                for line in err_lines:
                    if line.strip():
                        print(f"     {line}")
        
        except subprocess.TimeoutExpired:
            print(f"  ⏰ {subj} validation timeout")
        except Exception as e:
            print(f"  💥 {subj} validation error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Run Phase 7 → Phase 8.1 Pipeline")
    parser.add_argument("--subject", type=str, default=None,
                        help="Process only this subject (e.g., 'gen_chem')")
    parser.add_argument("--validate-only", action="store_true",
                        help="Skip processing, only run validation")
    parser.add_argument("--parallel", action="store_true",
                        help="Run subjects in parallel (uses 5 workers)")
    args = parser.parse_args()
    
    subjects = [args.subject] if args.subject else SUBJECTS
    
    # Validate subject names
    for subj in subjects:
        if subj not in SUBJECTS:
            print(f"❌ Unknown subject: {subj}")
            print(f"   Available: {', '.join(SUBJECTS)}")
            return
    
    start_time = time.time()
    
    if args.validate_only:
        print("\n🔍 Running validation only...")
        run_validation(args.subject)
        return
    
    print("\n" + "="*70)
    print("🚀 Phase 7 → Phase 8.1 Pipeline")
    print("="*70)
    print(f"📚 Subjects: {', '.join(subjects)}")
    print(f"⚙️  Mode: {'Parallel' if args.parallel else 'Sequential'}")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show current completion status
    print("\n📊 Current Status:")
    for subj in subjects:
        p7_done = check_phase7_complete(subj)
        p8_1_done = check_phase8_1_complete(subj)
        p7_sections = sum(p7_done.values())
        p8_1_sections = sum(p8_1_done.values())
        print(f"  {subj:15s} — P7: {p7_sections:3d} sections | P8.1: {p8_1_sections:3d} modes")
    
    # ─── PHASE 7: Build Primitives (Run all subjects first) ───
    print("\n" + "="*70)
    print("🧱 PHASE 7: Building Primitives (Deterministic)")
    print("="*70)
    print(f"Processing {len(subjects)} subjects with {'5 parallel workers' if args.parallel else 'sequential execution'}...")
    
    p7_results = []
    if args.parallel:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(run_phase7_for_subject, subj): subj for subj in subjects}
            for future in as_completed(futures):
                result = future.result()
                p7_results.append(result)
    else:
        for subj in subjects:
            result = run_phase7_for_subject(subj)
            p7_results.append(result)
    
    # Check Phase 7 completion before proceeding
    p7_failed = [r for r in p7_results if r["status"] != "success"]
    if p7_failed:
        print("\n❌ Phase 7 had failures. Cannot proceed to Phase 8.1.")
        for fail in p7_failed:
            print(f"   - {fail['subject']}: {fail.get('error', 'Unknown error')}")
        # Continue with validation anyway
        run_validation(args.subject)
        return
    
    # Verify all primitives exist
    print("\n" + "="*70)
    print("🔍 Verifying Phase 7 Outputs")
    print("="*70)
    
    all_verified = True
    for subj in subjects:
        p7_done = check_phase7_complete(subj)
        p7_sections = sum(p7_done.values())
        if p7_sections == 0:
            print(f"  ❌ {subj}: No primitives found")
            all_verified = False
        else:
            print(f"  ✅ {subj}: {p7_sections} primitive sections")
    
    if not all_verified:
        print("\n❌ Phase 7 verification failed. Cannot proceed to Phase 8.1.")
        return
    
    print("\n✅ Phase 7 complete for all subjects! Proceeding to Phase 8.1...")
    
    # ─── PHASE 8.1: Compile Modes (After Phase 7 is fully complete) ───
    print("\n" + "="*70)
    print("🧩 PHASE 8.1: Compiling Game Modes (Deterministic)")
    print("="*70)
    print(f"Processing {len(subjects)} subjects with {'5 parallel workers' if args.parallel else 'sequential execution'}...")
    
    p8_1_results = []
    if args.parallel:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(run_phase8_1_for_subject, subj): subj for subj in subjects}
            for future in as_completed(futures):
                result = future.result()
                p8_1_results.append(result)
    else:
        for subj in subjects:
            result = run_phase8_1_for_subject(subj)
            p8_1_results.append(result)
    
    # ─── VALIDATION ───
    run_validation(args.subject)
    
    # ─── SUMMARY ───
    elapsed = time.time() - start_time
    
    print("\n" + "="*70)
    print("📊 PIPELINE SUMMARY")
    print("="*70)
    
    p7_success = sum(1 for r in p7_results if r["status"] == "success")
    p7_failed = sum(1 for r in p7_results if r["status"] != "success")
    p8_1_success = sum(1 for r in p8_1_results if r["status"] == "success")
    p8_1_failed = sum(1 for r in p8_1_results if r["status"] != "success")
    
    print(f"⏱️  Total time: {int(elapsed)}s ({elapsed/60:.1f}m)")
    print(f"🧱 Phase 7:   {p7_success} success, {p7_failed} failed")
    print(f"🧩 Phase 8.1: {p8_1_success} success, {p8_1_failed} failed")
    
    if p7_failed > 0 or p8_1_failed > 0:
        print("\n⚠️  Some phases failed. Check logs above for details.")
    else:
        print("\n✅ All phases completed successfully!")
    
    # Show final completion status
    print("\n📊 Final Status:")
    for subj in subjects:
        p7_done = check_phase7_complete(subj)
        p8_1_done = check_phase8_1_complete(subj)
        p7_sections = sum(p7_done.values())
        p8_1_sections = sum(p8_1_done.values())
        print(f"  {subj:15s} — P7: {p7_sections:3d} sections | P8.1: {p8_1_sections:3d} modes")


if __name__ == "__main__":
    main()
