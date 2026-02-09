"""
Batch fix+verify for all Chapter 1 sections.
Runs autonomously — each section gets up to 3 fix iterations.
Prints a final summary at the end.

Usage:
    python scripts/fix_all_ch1.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fix_and_verify import fix_section
from utils.gemini_client import GeminiClient
from config import STRUCTURED_DIR

def main():
    client = GeminiClient()
    subject = "biology"
    sections = ["1.1", "1.2", "1.3", "1.4", "1.5"]
    max_iter = 3

    print("=" * 70)
    print("BATCH FIX+VERIFY: Biology Chapter 1")
    print(f"Sections: {', '.join(sections)}")
    print(f"Max iterations per section: {max_iter}")
    print("=" * 70)

    results = {}
    for sec_id in sections:
        print(f"\n{'─'*50}")
        print(f"Processing {sec_id}...")
        print(f"{'─'*50}")
        passed = fix_section(subject, sec_id, client, max_iter)
        results[sec_id] = passed

    print(f"\n{'='*70}")
    print(f"FINAL RESULTS")
    print(f"{'='*70}")
    for sec_id, passed in results.items():
        status = "PASSED" if passed else "NEEDS REVIEW"
        print(f"  {sec_id}: {status}")

    passed_count = sum(1 for v in results.values() if v)
    print(f"\n  {passed_count}/{len(results)} sections passed")

    client.print_cost_summary()
    client.save_usage_log("usage_fix_all_ch1.json")

if __name__ == "__main__":
    main()
