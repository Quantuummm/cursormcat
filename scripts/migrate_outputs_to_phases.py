"""
Safe migration tool: move pre-existing top-level output folders into the new
per-phase output locations. Run with --dry-run to preview, or --force to
overwrite conflicts.

Example:
    python scripts/migrate_outputs_to_phases.py --dry-run
    python scripts/migrate_outputs_to_phases.py --force
"""
import argparse
import shutil
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
from config import (
    ASSETS_DIR,
    EXTRACTED_DIR,
    CLASSIFIED_DIR,
    STRUCTURED_DIR,
    COMPILED_DIR,
    PRIMITIVES_DIR,
    BRIDGES_DIR,
    AUDIO_DIR,
)

MAPPING = {
    PROJECT_ROOT / "assets": ASSETS_DIR,
    PROJECT_ROOT / "extracted": EXTRACTED_DIR,
    PROJECT_ROOT / "classified": CLASSIFIED_DIR,
    PROJECT_ROOT / "structured": STRUCTURED_DIR,
    PROJECT_ROOT / "compiled": COMPILED_DIR,
    PROJECT_ROOT / "primitives": PRIMITIVES_DIR,
    PROJECT_ROOT / "bridges": BRIDGES_DIR,
    PROJECT_ROOT / "audio": AUDIO_DIR,
}


def _ensure_parent(d: Path):
    d.parent.mkdir(parents=True, exist_ok=True)


def move_dir(src: Path, dst: Path, force: bool = False, dry_run: bool = True):
    if not src.exists():
        print(f"  ⏭️  Source not found: {src}")
        return

    print(f"  Moving: {src} → {dst}")
    if dry_run:
        # list items that would be moved
        for p in sorted(src.iterdir()):
            print(f"    would move: {p} → {dst / p.name}")
        return

    _ensure_parent(dst)
    dst.mkdir(parents=True, exist_ok=True)

    for item in sorted(src.iterdir()):
        dest_item = dst / item.name
        if dest_item.exists():
            if force:
                if dest_item.is_dir():
                    shutil.rmtree(dest_item)
                else:
                    dest_item.unlink()
            else:
                print(f"    ⚠️  Skipping existing: {dest_item} (use --force to overwrite)")
                continue
        print(f"    moving {item} → {dest_item}")
        shutil.move(str(item), str(dest_item))

    # if source dir is empty after moving, remove it
    try:
        if not any(src.iterdir()):
            src.rmdir()
            print(f"    removed empty source dir: {src}")
    except Exception:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate top-level outputs into per-phase output folders")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without moving files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files in destination")
    args = parser.parse_args()

    print("Migration plan:")
    for s, d in MAPPING.items():
        print(f"  {s}  →  {d}")

    if args.dry_run or not any(s.exists() for s in MAPPING.keys()):
        print("\nRunning dry-run (preview). To actually move files, rerun without --dry-run or pass --force to overwrite conflicts.)")

    for src, dst in MAPPING.items():
        move_dir(src, dst, force=args.force, dry_run=args.dry_run)

    # Move any usage_*.json files at project root into the appropriate phase usage folders
    usage_files = sorted([p for p in PROJECT_ROOT.glob("usage_*.json") if p.is_file()])
    if usage_files:
        print("\nFound usage logs at project root: ")
        for f in usage_files:
            print(f"  {f.name}")
        print("\nMapping usage logs to phase usage folders...")

    for f in usage_files:
        name = f.name
        if name.startswith("usage_phase3_") or name.startswith("usage_phase1_") or name.startswith("usage_phase2_"):
            dest = EXTRACTED_DIR.parent / "usage"  # phases/phase1/output/usage
        elif name.startswith("usage_fix_verify_") or "fix" in name:
            dest = PROJECT_ROOT / "phases" / "phase6_1" / "output" / "usage"
        else:
            # fallback to phase1 usage folder
            dest = EXTRACTED_DIR.parent / "usage"

        dest.mkdir(parents=True, exist_ok=True)
        target = dest / name
        print(f"  Moving {f} → {target}")
        if args.dry_run:
            continue
        if target.exists():
            if args.force:
                target.unlink()
            else:
                print(f"    ⚠️  Skipping existing: {target} (use --force to overwrite)")
                continue
        f.rename(target)

    print("\nMigration complete. Verify everything and run tests.")
