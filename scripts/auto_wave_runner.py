"""
Auto-Wave Runner — Monitors Wave 1 completion and chains Waves 2-4 automatically.

Polls pipeline status every 60 seconds. When the current wave is done,
launches the next wave. Reports progress along the way.

Usage:
    python scripts/auto_wave_runner.py
"""

import sys
import os
import time
import subprocess
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from parallel_pipeline import get_completion_matrix, generate_work_items, BOOKS

POLL_INTERVAL = 60  # seconds between status checks

def count_wave_items(wave_items):
    """Count total and API-needed items in a wave."""
    return len(wave_items)

def wave_is_empty(matrix, wave_name):
    """Check if a wave has zero remaining work items."""
    waves = generate_work_items(matrix)
    return len(waves.get(wave_name, [])) == 0

def print_progress(matrix):
    """Print a compact progress summary."""
    phases = [2, 3, 4, 5, 6, 6.1, 7, 8, 8.1, 8.2]
    for subject in sorted(BOOKS.values()):
        row = f"  {subject:14s}"
        for phase in phases:
            data = matrix[subject].get(phase, {})
            if isinstance(data, dict) and "done" in data:
                row += " ✅" if data["done"] else " ❌"
            elif isinstance(data, dict):
                done = sum(1 for v in data.values() if v)
                total = len(data)
                if done == total:
                    row += f" {done:2d}✅"
                elif done == 0:
                    row += f"  0❌"
                else:
                    row += f" {done:2d}/{total}"
        print(row)

def run_wave(wave_num):
    """Launch a pipeline wave and wait for it to complete."""
    print(f"\n{'='*60}")
    print(f"🚀 LAUNCHING WAVE {wave_num}")
    print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}\n")
    
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "parallel_pipeline.py"), "--wave", str(wave_num)],
        env=env,
        cwd=str(REPO_ROOT),
    )
    
    return result.returncode == 0

def main():
    print(f"\n{'='*60}")
    print(f"🤖 MCAT MASTERY — AUTO-WAVE RUNNER")
    print(f"   Monitors waves and chains them automatically")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Determine which wave to start from
    # Check if Wave 1 is already running (it should be from the background terminal)
    waves_to_run = []
    
    matrix = get_completion_matrix()
    all_waves = generate_work_items(matrix)
    
    for wave_num in [1, 2, 3, 4]:
        wave_key = f"wave{wave_num}"
        items = all_waves.get(wave_key, [])
        if items:
            waves_to_run.append(wave_num)
            print(f"  Wave {wave_num}: {len(items)} items remaining")
        else:
            print(f"  Wave {wave_num}: ✅ Complete")
    
    if not waves_to_run:
        print("\n✅ All waves complete! Pipeline finished.")
        return
    
    # If Wave 1 is the first remaining, wait for it (it's running in background)
    if waves_to_run[0] == 1:
        print(f"\n⏳ Wave 1 is running in background. Monitoring completion...")
        while True:
            time.sleep(POLL_INTERVAL)
            matrix = get_completion_matrix()
            
            if wave_is_empty(matrix, "wave1"):
                print(f"\n✅ Wave 1 COMPLETE at {datetime.now().strftime('%H:%M:%S')}!")
                print_progress(matrix)
                waves_to_run.pop(0)
                break
            else:
                remaining = len(generate_work_items(matrix).get("wave1", []))
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] Wave 1: {remaining} items remaining...")
    
    # Run remaining waves sequentially
    for wave_num in waves_to_run:
        matrix = get_completion_matrix()
        items = generate_work_items(matrix).get(f"wave{wave_num}", [])
        
        if not items:
            print(f"\n✅ Wave {wave_num}: Already complete, skipping")
            continue
        
        print(f"\n📊 Pre-Wave {wave_num} status:")
        print_progress(matrix)
        
        success = run_wave(wave_num)
        
        if not success:
            print(f"\n⚠️ Wave {wave_num} exited with errors. Checking remaining items...")
            matrix = get_completion_matrix()
            remaining = len(generate_work_items(matrix).get(f"wave{wave_num}", []))
            if remaining > 0:
                print(f"   {remaining} items still incomplete. Retrying wave {wave_num}...")
                run_wave(wave_num)
        
        matrix = get_completion_matrix()
        print(f"\n📊 Post-Wave {wave_num} status:")
        print_progress(matrix)
    
    # Final status
    print(f"\n{'='*60}")
    print(f"🎉 ALL WAVES COMPLETE!")
    print(f"   Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    matrix = get_completion_matrix()
    print_progress(matrix)

if __name__ == "__main__":
    main()
