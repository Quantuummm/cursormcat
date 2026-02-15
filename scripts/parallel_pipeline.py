"""
Parallel Pipeline Orchestrator — Uses 5 API keys to process all 7 MCAT books.

Distributes work across 5 workers (each with its own API key), respecting phase
dependencies and tracking progress. Processes Phases 2-9 in dependency waves.

Usage:
    python scripts/parallel_pipeline.py                     # Full run
    python scripts/parallel_pipeline.py --wave 1            # Only Wave 1
    python scripts/parallel_pipeline.py --dry-run           # Show plan without executing
    python scripts/parallel_pipeline.py --status            # Show completion status
"""

import sys
import os
import json
import time
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Fix Windows encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ─── Book definitions ───────────────────────────────────────
BOOKS = {
    "MCAT Biology Review.pdf":                         "biology",
    "MCAT Biochemistry Review.pdf":                    "biochemistry",
    "MCAT General Chemistry Review.pdf":               "gen_chem",
    "MCAT Organic Chemistry Review.pdf":               "org_chem",
    "MCAT Physics and Math Review.pdf":                "physics",
    "MCAT Behavioral Sciences Review.pdf":             "psych_soc",
    "MCAT Critical Analysis and Reasoning Skills Review.pdf": "cars",
}

NUM_KEYS = 5
NUM_CHAPTERS = 12  # All books have 12 chapters

# ─── Output directories ────────────────────────────────────
PHASE_OUTPUT_DIRS = {
    0:   REPO_ROOT / "phases" / "phase0"  / "output" / "assets",
    1:   REPO_ROOT / "phases" / "phase1"  / "output" / "extracted",
    2:   REPO_ROOT / "phases" / "phase2"  / "output" / "extracted",
    3:   REPO_ROOT / "phases" / "phase3"  / "output" / "extracted",
    4:   REPO_ROOT / "phases" / "phase4"  / "output" / "extracted",
    5:   REPO_ROOT / "phases" / "phase5"  / "output" / "extracted",
    6:   REPO_ROOT / "phases" / "phase6"  / "output",
    6.1: REPO_ROOT / "phases" / "phase6_1"/ "output" / "verified",
    7:   REPO_ROOT / "phases" / "phase7"  / "output" / "primitives",
    8:   REPO_ROOT / "phases" / "phase8"  / "output" / "structured",
    8.1: REPO_ROOT / "phases" / "phase8_1"/ "output" / "compiled",
    8.2: REPO_ROOT / "phases" / "phase8_2"/ "output" / "verified",
    9:   REPO_ROOT / "phases" / "phase9"  / "output" / "bridges",
}


def check_phase_done(phase: float, subject: str, chapter: int = None) -> bool:
    """Check if a phase has output files for a given subject/chapter."""
    
    # CARS doesn't produce output for assessment/glossary/figure phases
    if subject == "cars" and phase in [2, 4, 5]:
        return True  # Skip these — CARS is passage-comprehension only
    
    base = PHASE_OUTPUT_DIRS.get(phase)
    if not base:
        return False
    
    subj_dir = base / subject
    
    if phase == 0:
        # Phase 0 outputs are in assets/{subject}/ — check any images exist
        return subj_dir.exists() and any(subj_dir.iterdir())
    
    elif phase == 1:
        return (subj_dir / "_toc.json").exists()
    
    elif phase == 2:
        if chapter:
            return (subj_dir / f"ch{chapter:02d}_assessment.json").exists()
        return len(list(subj_dir.glob("ch*_assessment.json"))) >= 10  # Most chapters
    
    elif phase == 3:
        if chapter:
            return any(subj_dir.glob(f"ch{chapter:02d}_*.json"))
        return len(list(subj_dir.glob("ch[0-9]*_*.json"))) >= 10
    
    elif phase == 4:
        return (subj_dir / "_glossary.json").exists()
    
    elif phase == 5:
        if chapter:
            return (subj_dir / f"ch{chapter:02d}_figure_catalog.json").exists()
        return (subj_dir / "_figure_catalog.json").exists()
    
    elif phase == 6:
        # Phase 6 output is under phase6/output/{subject}/
        p6_dir = REPO_ROOT / "phases" / "phase6" / "output" / subject
        if chapter:
            return (p6_dir / f"ch{chapter:02d}_assessment.json").exists()
        return p6_dir.exists() and len(list(p6_dir.glob("ch*_assessment.json"))) >= 10
    
    elif phase == 6.1:
        if chapter:
            return (subj_dir / f"ch{chapter:02d}_assessment.json").exists()
        return subj_dir.exists() and len(list(subj_dir.glob("ch*_assessment.json"))) >= 10
    
    elif phase == 7:
        if chapter:
            return any(subj_dir.glob(f"{chapter}.*json"))
        return subj_dir.exists() and len(list(subj_dir.glob("*.json"))) >= 5
    
    elif phase == 8:
        if chapter:
            return any(subj_dir.glob(f"{chapter}.*-*.json"))
        return subj_dir.exists() and len(list(subj_dir.glob("[0-9]*-*.json"))) >= 5
    
    elif phase == 8.1:
        if chapter:
            return any(subj_dir.glob(f"{chapter}.*_modes.json"))
        return subj_dir.exists() and len(list(subj_dir.glob("*_modes.json"))) >= 5
    
    elif phase == 8.2:
        if chapter:
            return any(subj_dir.glob(f"{chapter}.*-*.json"))
        return subj_dir.exists() and len(list(subj_dir.glob("[0-9]*-*.json"))) >= 5
    
    elif phase == 9:
        return (base / "_bridge_graph.json").exists()
    
    return False


def get_completion_matrix():
    """Build a matrix of what's done vs what needs doing."""
    matrix = {}
    for pdf, subject in BOOKS.items():
        matrix[subject] = {}
        for phase in [0, 1, 2, 3, 4, 5, 6, 6.1, 7, 8, 8.1, 8.2]:
            if phase in [4]:  # Book-wide phases 
                matrix[subject][phase] = {"done": check_phase_done(phase, subject)}
            else:
                chapter_status = {}
                for ch in range(1, NUM_CHAPTERS + 1):
                    chapter_status[ch] = check_phase_done(phase, subject, ch)
                matrix[subject][phase] = chapter_status
    matrix["_global"] = {9: {"done": check_phase_done(9, "global")}}
    return matrix


def print_status_matrix(matrix):
    """Print a readable status matrix."""
    phases = [2, 3, 4, 5, 6, 6.1, 7, 8, 8.1, 8.2]
    
    print(f"\n{'='*90}")
    print(f"📊 PIPELINE COMPLETION STATUS")
    print(f"{'='*90}")
    
    # Header
    header = f"{'Subject':<14}"
    for p in phases:
        p_str = str(p) if p != int(p) else str(int(p))
        header += f" P{p_str:>4}"
    print(header)
    print("-" * 90)
    
    for subject in sorted(BOOKS.values()):
        row = f"{subject:<14}"
        for phase in phases:
            data = matrix[subject].get(phase, {})
            if isinstance(data, dict) and "done" in data:
                # Book-wide phase
                row += "   ✅" if data["done"] else "   ❌"
            elif isinstance(data, dict):
                done = sum(1 for v in data.values() if v)
                total = len(data)
                if done == total:
                    row += f"  {done:2d}✅"
                elif done == 0:
                    row += f"  {done:2d}❌"
                else:
                    row += f" {done:2d}/{total}"
            else:
                row += "   ? "
        print(row)
    
    # Phase 9 status
    p9 = matrix.get("_global", {}).get(9, {}).get("done", False)
    print(f"\n{'Phase 9 (Bridges)':<14}: {'✅ Complete' if p9 else '❌ Pending (needs all Phase 3)'}")
    print(f"{'='*90}\n")


def generate_work_items(matrix):
    """Generate work items organized into dependency waves."""
    
    # Reverse map: subject -> pdf filename
    subject_to_pdf = {v: k for k, v in BOOKS.items()}
    
    waves = {
        "wave1": [],  # Phases 2, 3, 4, 5 (only need Phase 1)
        "wave2": [],  # Phase 6, 6.1, 7
        "wave3": [],  # Phase 8, 8.2, 8.1
        "wave4": [],  # Phase 9
    }
    
    for subject in BOOKS.values():
        pdf = subject_to_pdf[subject]
        
        # === WAVE 1: Extraction phases (2, 3, 4, 5) ===
        # Phase 2 & 3: per-chapter
        for ch in range(1, NUM_CHAPTERS + 1):
            data2 = matrix[subject].get(2, {})
            if isinstance(data2, dict) and not data2.get(ch, False):
                waves["wave1"].append({"phase": 2, "pdf": pdf, "chapter": ch, "subject": subject,
                                       "priority": 1, "api_needed": True})
            
            data3 = matrix[subject].get(3, {})
            if isinstance(data3, dict) and not data3.get(ch, False):
                waves["wave1"].append({"phase": 3, "pdf": pdf, "chapter": ch, "subject": subject,
                                       "priority": 2, "api_needed": True})
        
        # Phase 4: book-wide glossary
        data4 = matrix[subject].get(4, {})
        if isinstance(data4, dict) and not data4.get("done", False):
            waves["wave1"].append({"phase": 4, "pdf": pdf, "chapter": None, "subject": subject,
                                   "priority": 1, "api_needed": True})
        
        # Phase 5: per-chapter figures
        for ch in range(1, NUM_CHAPTERS + 1):
            data5 = matrix[subject].get(5, {})
            if isinstance(data5, dict) and not data5.get(ch, False):
                waves["wave1"].append({"phase": 5, "pdf": pdf, "chapter": ch, "subject": subject,
                                       "priority": 3, "api_needed": True})
        
        # === WAVE 2: Enrichment phases (6, 6.1, 7) ===
        for ch in range(1, NUM_CHAPTERS + 1):
            data6 = matrix[subject].get(6, {})
            if isinstance(data6, dict) and not data6.get(ch, False):
                waves["wave2"].append({"phase": 6, "pdf": pdf, "chapter": ch, "subject": subject,
                                       "priority": 1, "api_needed": True})
            
            data61 = matrix[subject].get(6.1, {})
            if isinstance(data61, dict) and not data61.get(ch, False):
                waves["wave2"].append({"phase": 6.1, "pdf": pdf, "chapter": ch, "subject": subject,
                                       "priority": 2, "api_needed": True})
            
            data7 = matrix[subject].get(7, {})
            if isinstance(data7, dict) and not data7.get(ch, False):
                waves["wave2"].append({"phase": 7, "pdf": pdf, "chapter": ch, "subject": subject,
                                       "priority": 3, "api_needed": False})
        
        # === WAVE 3: Structured content (8, 8.2, 8.1) ===
        for ch in range(1, NUM_CHAPTERS + 1):
            data8 = matrix[subject].get(8, {})
            if isinstance(data8, dict) and not data8.get(ch, False):
                waves["wave3"].append({"phase": 8, "pdf": pdf, "chapter": ch, "subject": subject,
                                       "priority": 1, "api_needed": True})
            
            data82 = matrix[subject].get(8.2, {})
            if isinstance(data82, dict) and not data82.get(ch, False):
                waves["wave3"].append({"phase": 8.2, "pdf": pdf, "chapter": ch, "subject": subject,
                                       "priority": 2, "api_needed": True})
            
            data81 = matrix[subject].get(8.1, {})
            if isinstance(data81, dict) and not data81.get(ch, False):
                waves["wave3"].append({"phase": 8.1, "pdf": pdf, "chapter": ch, "subject": subject,
                                       "priority": 3, "api_needed": False})
    
    # === WAVE 4: Phase 9 (cross-book bridges) ===
    if not matrix.get("_global", {}).get(9, {}).get("done", False):
        waves["wave4"].append({"phase": 9, "pdf": None, "chapter": None, "subject": "global",
                               "priority": 1, "api_needed": True})
    
    # Sort each wave by priority then subject for even distribution
    for wave_name in waves:
        waves[wave_name].sort(key=lambda x: (x["priority"], x["subject"], x.get("chapter", 0) or 0))
    
    return waves


# Pre-load API keys at module level (before any threading)
def _load_env_values():
    """Load .env values once at startup."""
    env_path = REPO_ROOT / ".env"
    vals = {}
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    vals[k.strip()] = v.strip()
    return vals

_ENV_VALS = _load_env_values()


def run_worker(item, key_index):
    """Run a single work item as a subprocess with the correct API key."""
    phase = item["phase"]
    pdf = item["pdf"]
    chapter = item["chapter"]
    subject = item["subject"]
    
    phase_str = str(phase) if phase != int(phase) else str(int(phase))
    ch_str = f"Ch{chapter}" if chapter else "ALL"
    
    cmd = [
        sys.executable, str(REPO_ROOT / "scripts" / "parallel_worker.py"),
        "--phase", str(phase),
        "--key-index", str(key_index),
    ]
    if pdf:
        cmd.extend(["--pdf", pdf])
    if chapter:
        cmd.extend(["--chapter", str(chapter)])
    
    # Set up environment with the correct API key
    env = os.environ.copy()
    key_var = f"GEMINI_API_KEY_{key_index + 1}"
    api_key = _ENV_VALS.get(key_var, _ENV_VALS.get("GEMINI_API_KEY", ""))
    env["GEMINI_API_KEY"] = api_key
    
    # Also pass through Google Cloud creds
    for k, v in _ENV_VALS.items():
        if k.startswith("GOOGLE_"):
            env[k] = v
    
    start = time.time()
    log_prefix = f"[Key{key_index+1}] P{phase_str} {subject} {ch_str}"
    print(f"  🚀 {log_prefix} — Starting...")
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=900,  # 15 min timeout per work item
            encoding="utf-8",
            errors="replace",
        )
        
        elapsed = time.time() - start
        
        if result.returncode == 0:
            print(f"  ✅ {log_prefix} — Done ({int(elapsed)}s)")
            return {"status": "success", "item": item, "elapsed": elapsed}
        else:
            # Extract last few lines of stderr for error context
            err_lines = (result.stderr or "").strip().split("\n")[-5:]
            err_summary = "\n".join(err_lines)
            print(f"  ❌ {log_prefix} — Failed ({int(elapsed)}s)")
            if err_summary:
                print(f"     Error: {err_summary[:200]}")
            return {"status": "failed", "item": item, "elapsed": elapsed,
                    "error": err_summary}
    
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        print(f"  ⏰ {log_prefix} — Timeout ({int(elapsed)}s)")
        return {"status": "timeout", "item": item, "elapsed": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        print(f"  💥 {log_prefix} — Error: {e}")
        return {"status": "error", "item": item, "elapsed": elapsed, "error": str(e)}


def execute_wave(wave_name, items, max_workers=5):
    """Execute a wave of work items across N workers."""
    if not items:
        print(f"\n✅ {wave_name}: Nothing to do — all complete!")
        return []
    
    # Split items into API-needing and non-API items
    api_items = [i for i in items if i.get("api_needed", True)]
    non_api_items = [i for i in items if not i.get("api_needed", True)]
    
    print(f"\n{'='*70}")
    print(f"🌊 {wave_name.upper()}: {len(items)} work items "
          f"({len(api_items)} API, {len(non_api_items)} deterministic)")
    print(f"{'='*70}")
    
    results = []
    
    # Run deterministic items first (no API key needed, fast)
    if non_api_items:
        print(f"\n  📐 Running {len(non_api_items)} deterministic items (Phase 7, 8.1)...")
        with ThreadPoolExecutor(max_workers=min(5, len(non_api_items))) as executor:
            futures = {
                executor.submit(run_worker, item, 0): item
                for item in non_api_items
            }
            for future in as_completed(futures):
                results.append(future.result())
    
    # Run API items with round-robin key assignment
    if api_items:
        print(f"\n  🔑 Running {len(api_items)} API items across {max_workers} keys...")
        
        # Group items by subject for better PDF caching (same PDF stays on same worker)
        subject_groups = defaultdict(list)
        for item in api_items:
            subject_groups[item["subject"]].append(item)
        
        # Assign subjects to workers round-robin
        subjects = list(subject_groups.keys())
        worker_queues = [[] for _ in range(max_workers)]
        for i, subj in enumerate(subjects):
            worker_idx = i % max_workers
            worker_queues[worker_idx].extend(subject_groups[subj])
        
        # Flatten back into ordered work items with key assignments
        assigned_items = []
        for key_idx, queue in enumerate(worker_queues):
            for item in queue:
                assigned_items.append((item, key_idx))
        
        # Process with thread pool — each thread runs a subprocess
        # Limit concurrency to avoid hitting per-key TPM limits
        # With 5 keys, run 5 items concurrently (1 per key at a time)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Track which keys are busy to avoid concurrent calls on same key
            futures = {}
            pending = list(assigned_items)
            active_keys = set()
            
            while pending or futures:
                # Submit new items if keys are available
                while pending:
                    item, key_idx = pending[0]
                    if key_idx not in active_keys:
                        active_keys.add(key_idx)
                        future = executor.submit(run_worker, item, key_idx)
                        futures[future] = (item, key_idx)
                        pending.pop(0)
                    else:
                        # This key is busy, try next item
                        found = False
                        for i, (it, ki) in enumerate(pending):
                            if ki not in active_keys:
                                active_keys.add(ki)
                                future = executor.submit(run_worker, it, ki)
                                futures[future] = (it, ki)
                                pending.pop(i)
                                found = True
                                break
                        if not found:
                            break  # All available keys are busy, wait
                
                # Wait for at least one to complete
                if futures:
                    done_futures = []
                    for future in list(futures.keys()):
                        if future.done():
                            done_futures.append(future)
                    
                    if not done_futures:
                        # None done yet, wait a bit
                        time.sleep(0.5)
                        continue
                    
                    for future in done_futures:
                        item, key_idx = futures.pop(future)
                        active_keys.discard(key_idx)
                        result = future.result()
                        results.append(result)
    
    # Summary
    successes = sum(1 for r in results if r["status"] == "success")
    failures = sum(1 for r in results if r["status"] != "success")
    total_time = sum(r.get("elapsed", 0) for r in results)
    
    print(f"\n  📊 {wave_name} Results: {successes}✅ {failures}❌ | Total worker-time: {int(total_time)}s")
    
    if failures > 0:
        print(f"\n  ⚠️  Failed items:")
        for r in results:
            if r["status"] != "success":
                item = r["item"]
                print(f"     P{item['phase']} {item['subject']} Ch{item.get('chapter', 'N/A')}: {r['status']}")
    
    return results


def save_run_log(all_results, start_time):
    """Save a comprehensive run log."""
    log_dir = REPO_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log = {
        "started": start_time.isoformat(),
        "finished": datetime.now().isoformat(),
        "elapsed_seconds": (datetime.now() - start_time).total_seconds(),
        "total_items": len(all_results),
        "successes": sum(1 for r in all_results if r["status"] == "success"),
        "failures": sum(1 for r in all_results if r["status"] != "success"),
        "results": [
            {
                "phase": r["item"]["phase"],
                "subject": r["item"]["subject"],
                "chapter": r["item"].get("chapter"),
                "status": r["status"],
                "elapsed": round(r.get("elapsed", 0), 1),
                "error": r.get("error", ""),
            }
            for r in all_results
        ],
    }
    
    path = log_dir / f"parallel_run_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)
    print(f"\n  💾 Run log saved: {path.relative_to(REPO_ROOT)}")


def main():
    parser = argparse.ArgumentParser(description="Parallel Pipeline Orchestrator")
    parser.add_argument("--wave", type=int, help="Run only this wave (1-4)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    parser.add_argument("--status", action="store_true", help="Show completion status only")
    parser.add_argument("--workers", type=int, default=NUM_KEYS, help=f"Number of parallel workers (default: {NUM_KEYS})")
    parser.add_argument("--retry-failed", action="store_true", help="Retry previously failed items")
    args = parser.parse_args()
    
    print(f"\n{'='*70}")
    print(f"🧬 MCAT MASTERY — PARALLEL PIPELINE ORCHESTRATOR")
    print(f"   Workers: {args.workers} | Keys: {NUM_KEYS} | Books: {len(BOOKS)} | Chapters: {NUM_CHAPTERS}")
    print(f"{'='*70}")
    
    # Build completion matrix
    matrix = get_completion_matrix()
    print_status_matrix(matrix)
    
    if args.status:
        return
    
    # Generate work items
    waves = generate_work_items(matrix)
    
    # Print plan
    for wave_name, items in waves.items():
        api_count = sum(1 for i in items if i.get("api_needed", True))
        det_count = len(items) - api_count
        print(f"  {wave_name}: {len(items)} items ({api_count} API calls, {det_count} deterministic)")
    
    total = sum(len(items) for items in waves.values())
    print(f"\n  Total: {total} work items across 4 waves")
    
    if args.dry_run:
        print("\n  [DRY RUN — not executing]")
        for wave_name, items in waves.items():
            if items:
                print(f"\n  {wave_name}:")
                for item in items[:20]:
                    ch = f"Ch{item['chapter']}" if item['chapter'] else "ALL"
                    print(f"    P{item['phase']} {item['subject']} {ch}")
                if len(items) > 20:
                    print(f"    ... and {len(items) - 20} more")
        return
    
    if total == 0:
        print("\n🎉 All phases complete! Nothing to do.")
        return
    
    # Execute waves in order
    start_time = datetime.now()
    all_results = []
    
    wave_order = ["wave1", "wave2", "wave3", "wave4"]
    
    if args.wave:
        wave_order = [f"wave{args.wave}"]
    
    for wave_name in wave_order:
        items = waves.get(wave_name, [])
        if not items:
            continue
        
        results = execute_wave(wave_name, items, max_workers=args.workers)
        all_results.extend(results)
        
        # Check if wave had critical failures that block next wave
        failures = [r for r in results if r["status"] != "success"]
        if failures:
            print(f"\n  ⚠️  {len(failures)} failures in {wave_name}.")
            if wave_name in ["wave1", "wave2"]:
                print(f"  Continuing to next wave — later phases may skip affected chapters.")
    
    # Save log
    save_run_log(all_results, start_time)
    
    # Final summary
    elapsed = (datetime.now() - start_time).total_seconds()
    successes = sum(1 for r in all_results if r["status"] == "success")
    failures = sum(1 for r in all_results if r["status"] != "success")
    
    print(f"\n{'='*70}")
    print(f"🏁 PARALLEL PIPELINE COMPLETE")
    print(f"   Total time:  {int(elapsed // 60)}m {int(elapsed % 60)}s")
    print(f"   Succeeded:   {successes}")
    print(f"   Failed:      {failures}")
    print(f"{'='*70}\n")
    
    if failures > 0:
        print("⚠️  To retry failed items: python scripts/parallel_pipeline.py --retry-failed")


if __name__ == "__main__":
    main()
