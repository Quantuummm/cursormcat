"""
Quick check: report whether configured per-phase output paths exist and list contents for a sample subject.
Usage:
    python scripts/check_phase_outputs.py --subject biology
"""
from pathlib import Path
from config import ASSETS_DIR, EXTRACTED_DIR, PRIMITIVES_DIR, STRUCTURED_DIR, COMPILED_DIR, BRIDGES_DIR, AUDIO_DIR
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--subject", help="Subject slug to inspect (e.g., biology)", default=None)
args = parser.parse_args()

paths = {
    "assets": ASSETS_DIR,
    "extracted": EXTRACTED_DIR,
    "primitives": PRIMITIVES_DIR,
    "structured": STRUCTURED_DIR,
    "compiled": COMPILED_DIR,
    "bridges": BRIDGES_DIR,
    "audio": AUDIO_DIR,
}

print("Per-phase output paths and existence:")
for k, p in paths.items():
    print(f"  {k}: {p} -> {'exists' if p.exists() else 'MISSING'}")

if args.subject:
    print(f"\nContents for subject: {args.subject}")
    for k, p in paths.items():
        subj_path = p / args.subject
        if subj_path.exists():
            items = list(subj_path.iterdir())
            print(f"  {k}: {len(items)} items in {subj_path}")
        else:
            print(f"  {k}: {subj_path} (missing)")

print("\nIf files are still in top-level folders (assets/, extracted/, etc.), run:")
print("  python scripts/migrate_outputs_to_phases.py --dry-run")
print("Then re-run without --dry-run or with --force to apply the move.")
