"""
Verify Compiled Modes: Validates Phase 8.1 outputs for engine readiness, 
logic consistency, and common formatting issues.

Usage:
    python phases/phase8_1/validation/verify_compiled_modes.py --subject gen_chem
    python phases/phase8_1/validation/verify_compiled_modes.py --section 1.1
"""

import sys
import json
import argparse
import re
from pathlib import Path

# Add project root to path
# Path: phases/phase8_1/validation/verify_compiled_modes.py
# parents[0] = validation/
# parents[1] = phase8_1/
# parents[2] = phases/
# parents[3] = REPO_ROOT/
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# Try to import config, fallback if not possible
try:
    from scripts.config import COMPILED_DIR, BOOKS
except ImportError:
    # Manual fallback if script structure differs
    COMPILED_DIR = REPO_ROOT / "phases" / "phase8_1" / "output" / "compiled"
    BOOKS = {}

def check_payload(mode_type, payload, file_id):
    issues = []
    engine = payload.get("engine")
    
    if engine != mode_type:
        issues.append(f"[{file_id}] Engine mismatch: mode_type={mode_type} but engine={engine}")

    if mode_type == "rapid_recall":
        cards = payload.get("cards", [])
        if not cards:
            issues.append(f"[{file_id}] Rapid Recall: No cards in payload")
        for i, card in enumerate(cards):
            term = card.get("term")
            options = card.get("options", [])
            correct_idx = card.get("correct_index")
            
            if not term or str(term).strip() == "":
                issues.append(f"[{file_id}] Card {i}: Empty term")
            if len(options) != 4:
                issues.append(f"[{file_id}] Card {i}: Expected 4 options, found {len(options)}")
            if correct_idx is None or not isinstance(correct_idx, int):
                issues.append(f"[{file_id}] Card {i}: Missing or invalid correct_index")
            elif correct_idx < 0 or correct_idx >= len(options):
                issues.append(f"[{file_id}] Card {i}: correct_index {correct_idx} out of bounds")
            
            # Check for duplicate options
            if len(set(options)) < len(options) and len(options) > 0:
                issues.append(f"[{file_id}] Card {i}: Duplicate options found")
                
            # Check for placeholders
            for opt in options:
                if "[REDACTED]" in str(opt) or "TODO" in str(opt):
                    issues.append(f"[{file_id}] Card {i}: Placeholder found in options")

    elif mode_type == "sequence_builder":
        steps = payload.get("steps", [])
        correct_order = payload.get("correct_order", [])
        if not steps:
            issues.append(f"[{file_id}] Sequence Builder: No steps in payload")
        if len(steps) != len(correct_order):
            issues.append(f"[{file_id}] Sequence Builder: steps count ({len(steps)}) != correct_order count ({len(correct_order)})")
            
    elif mode_type == "sort_buckets":
        buckets = payload.get("buckets", [])
        items = payload.get("items", [])
        if not buckets:
            issues.append(f"[{file_id}] Sort Buckets: No buckets")
        if not items:
            issues.append(f"[{file_id}] Sort Buckets: No items")
        for i, it in enumerate(items):
            if "feature" not in it:
                issues.append(f"[{file_id}] Sort Item {i}: Missing feature")
            if "cells" not in it:
                issues.append(f"[{file_id}] Sort Item {i}: Missing cells")
            else:
                for b in buckets:
                    if b not in it["cells"]:
                        issues.append(f"[{file_id}] Sort Item {i}: Missing cell for bucket {b}")

    elif mode_type == "equation_forge":
        cards = payload.get("cards", [])
        if not cards:
            issues.append(f"[{file_id}] Equation Forge: No cards")
        for i, card in enumerate(cards):
            if not card.get("formula"):
                issues.append(f"[{file_id}] Equation Card {i}: Missing formula")

    elif mode_type == "label_text":
        items = payload.get("items", [])
        fig_ref = payload.get("figure_ref", {})
        if not items:
            issues.append(f"[{file_id}] Label Text: No items")
        if not fig_ref.get("image_file"):
            issues.append(f"[{file_id}] Label Text: Missing image_file reference")

    return issues

def verify_file(file_path):
    issues = []
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"Failed to parse JSON: {e}"]

    file_id = f"{data.get('subject', '?')}/{data.get('section_id', '?')}"
    
    # Check top-level fields
    for field in ["subject", "chapter_number", "section_id", "mode_instances"]:
        if field not in data:
            issues.append(f"[{file_id}] Missing top-level field: {field}")

    mode_instances = data.get("mode_instances", [])
    if not mode_instances:
        # Some sections might not have games if they have no content, but usually we expect some
        # issues.append(f"[{file_id}] No mode_instances found")
        pass

    mode_ids = set()
    for inst in mode_instances:
        m_id = inst.get("mode_id")
        m_type = inst.get("mode_type")
        payload = inst.get("payload", {})
        
        if not m_id:
            issues.append(f"[{file_id}] Missing mode_id")
        elif m_id in mode_ids:
            issues.append(f"[{file_id}] Duplicate mode_id: {m_id}")
        else:
            mode_ids.add(m_id)
            
        if not m_type:
            issues.append(f"[{file_id}] Missing mode_type for {m_id}")
            
        issues.extend(check_payload(m_type, payload, file_id))
        
        # Check LaTeX
        payload_str = json.dumps(payload)
        unclosed_latex = len(re.findall(r"\$", payload_str)) % 2 != 0
        if unclosed_latex:
            issues.append(f"[{file_id}] Possible unclosed LaTeX in payload for {m_id}")

    return issues

def main():
    parser = argparse.ArgumentParser(description="Verify compiled mode JSONs")
    parser.add_argument("--subject", help="Subject to filter by")
    parser.add_argument("--section", help="Section ID to filter by (e.g. 1.1)")
    args = parser.parse_args()

    print(f"🔍 Starting verification in {COMPILED_DIR}")
    
    if not COMPILED_DIR.exists():
        print(f"❌ Error: COMPILED_DIR does not exist: {COMPILED_DIR}")
        return

    subjects = [args.subject] if args.subject else [d.name for d in COMPILED_DIR.iterdir() if d.is_dir()]
    
    total_files = 0
    total_issues = 0
    files_with_issues = 0

    for subject in subjects:
        subj_path = COMPILED_DIR / subject
        if not subj_path.exists():
            continue
            
        file_pattern = f"{args.section}_modes.json" if args.section else "*_modes.json"
        mode_files = sorted(list(subj_path.glob(file_pattern)))
        
        if not mode_files:
            continue

        print(f"\n📂 Subject: {subject}")
        for mf in mode_files:
            total_files += 1
            issues = verify_file(mf)
            
            # Additional check: Does the internal subject match the folder name?
            try:
                data = json.loads(mf.read_text(encoding="utf-8"))
                int_subject = data.get("subject")
                if int_subject != subject:
                    issues.append(f"Internal subject '{int_subject}' does not match folder name '{subject}'")
            except:
                pass

            if issues:
                files_with_issues += 1
                total_issues += len(issues)
                print(f"\n❌ {mf.relative_to(REPO_ROOT)}")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                # print(f"✅ {mf.name}")
                pass

    print(f"\n{'='*40}")
    print(f"Scanned {total_files} files.")
    if total_issues == 0:
        print("🎉 No issues found! Phase 8.1 outputs look solid.")
    else:
        print(f"Found {total_issues} issues across {files_with_issues} files.")
        sys.exit(1)

if __name__ == "__main__":
    main()
