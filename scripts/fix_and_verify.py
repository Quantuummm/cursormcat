"""
Auto-fix + verify loop: reads verification results, regenerates flagged content,
re-verifies, and repeats until the section passes or max iterations reached.

Usage:
    python scripts/fix_and_verify.py biology 1.2          # Fix one section
    python scripts/fix_and_verify.py biology 1             # Fix all sections in chapter
    python scripts/fix_and_verify.py biology               # Fix all sections
    python scripts/fix_and_verify.py biology 1.2 --max 5   # Max 5 iterations
"""

import sys
import json
from pathlib import Path
from slugify import slugify

sys.path.insert(0, str(Path(__file__).parent))
from config import EXTRACTED_DIR, STRUCTURED_DIR, PROMPTS_DIR
from utils.gemini_client import GeminiClient
from utils.schema_validator import validate_restructured, print_validation


def load_original_data(subject: str, section_id: str) -> tuple[dict, list]:
    """Load original extracted content for a section."""
    extracted_dir = EXTRACTED_DIR / subject
    chapter_num = int(section_id.split(".")[0])

    ch_files = sorted(extracted_dir.glob(f"ch{chapter_num:02d}_*.json"))
    ch_files = [f for f in ch_files if "_assessment" not in f.name]
    if not ch_files:
        return {}, []

    ch_data = json.loads(ch_files[0].read_text(encoding="utf-8"))

    section = None
    for sec in ch_data.get("sections", []):
        if sec.get("section_id") == section_id:
            section = sec
            break

    summary = []
    for s in ch_data.get("summary", {}).get("by_section", []):
        if s["section_id"] == section_id:
            summary = s.get("summary_points", [])
            break

    return section or {}, summary


def build_original_text(section: dict, summary: list) -> str:
    """Convert original section data to readable text for the fix prompt."""
    parts = []
    parts.append(f"Learning Objectives: {json.dumps(section.get('learning_objectives', []))}")
    for block in section.get("content_blocks", []):
        fmt = block.get("format", "text")
        content = block.get("content", "")
        if isinstance(content, str):
            parts.append(f"[{fmt}] {content}")
        elif isinstance(content, list):
            parts.append(f"[{fmt}] {json.dumps(content)}")
    if summary:
        parts.append(f"Summary: {json.dumps(summary)}")
    return "\n\n".join(parts)


def collect_issues(verification: dict) -> list[dict]:
    """Extract all issues from a verification result into a flat list."""
    issues = []
    details = verification.get("verification_details", {})
    for category in ["hallucinations", "inaccuracies", "wrong_answers",
                     "misleading_simplifications", "missing_critical_info"]:
        for item in details.get(category, []):
            item["category"] = category
            issues.append(item)
    return issues


def has_critical_or_moderate(verification: dict) -> bool:
    """Check if verification has critical or moderate issues."""
    issues = collect_issues(verification)
    for iss in issues:
        if iss.get("severity") in ("critical", "moderate"):
            return True
    return False


def fix_section(subject: str, section_id: str, client: GeminiClient,
                max_iterations: int = 3) -> bool:
    """
    Fix-and-verify loop for a single section.
    Returns True if section passes, False if max iterations exceeded.
    """
    fix_prompt_template = (PROMPTS_DIR / "fix_content.txt").read_text(encoding="utf-8")
    verify_prompt_template = (PROMPTS_DIR / "verify_accuracy.txt").read_text(encoding="utf-8")

    # Load original
    original_section, original_summary = load_original_data(subject, section_id)
    if not original_section:
        print(f"  ❌ No original data found for {section_id}")
        return False

    original_text = build_original_text(original_section, original_summary)

    # Find structured file
    struct_dir = STRUCTURED_DIR / subject
    struct_file = None
    for f in struct_dir.glob("*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("section_id") == section_id:
            struct_file = f
            break

    if not struct_file:
        print(f"  ❌ No structured file found for {section_id}")
        return False

    # Load current verification result
    verify_dir = struct_dir / "_verification"
    verify_file = verify_dir / f"{section_id}_verification.json"

    for iteration in range(1, max_iterations + 1):
        # Load current structured content
        structured = json.loads(struct_file.read_text(encoding="utf-8"))
        sec_title = structured.get("title", section_id)

        # Check if we have verification results
        if verify_file.exists():
            verification = json.loads(verify_file.read_text(encoding="utf-8"))
        else:
            # Run verification first
            print(f"  🔍 Running initial verification...")
            verification = run_verification(
                structured, original_section, original_summary,
                section_id, sec_title, verify_prompt_template, client
            )
            verify_dir.mkdir(exist_ok=True)
            with open(verify_file, "w", encoding="utf-8") as f:
                json.dump(verification, f, indent=2, ensure_ascii=False)

        # Check if already passing
        if not has_critical_or_moderate(verification):
            print(f"  ✅ {section_id} PASSES — no critical/moderate issues")
            return True

        issues = collect_issues(verification)
        crit_count = sum(1 for i in issues if i.get("severity") == "critical")
        mod_count = sum(1 for i in issues if i.get("severity") == "moderate")
        print(f"\n  🔧 Iteration {iteration}/{max_iterations}: Fixing {crit_count} critical + {mod_count} moderate issues")

        # Build fix prompt
        fix_prompt = fix_prompt_template.format(
            original_content=original_text[:6000],
            current_structured=json.dumps(structured, indent=2)[:12000],
            issues_json=json.dumps([i for i in issues if i.get("severity") in ("critical", "moderate")], indent=2),
        )

        # Call Gemini 3 Flash to fix
        print(f"     🔄 Regenerating with fixes...")
        try:
            fixed = client.restructure(fix_prompt, phase=f"fix_{section_id}_iter{iteration}")
        except Exception as e:
            print(f"     ❌ Fix failed: {e}")
            continue

        # Handle list return
        if isinstance(fixed, list):
            if fixed and isinstance(fixed[0], dict) and "levels" in fixed[0]:
                fixed = fixed[0]
            else:
                print(f"     ⚠️  Unexpected response format, skipping iteration")
                continue

        # Validate structure
        struct_issues = validate_restructured(fixed)
        if any("no levels" in i.lower() for i in struct_issues):
            print(f"     ⚠️  Fix produced invalid structure, skipping")
            continue

        # Save fixed version
        with open(struct_file, "w", encoding="utf-8") as f:
            json.dump(fixed, f, indent=2, ensure_ascii=False)
        print(f"     💾 Saved fixed version")

        # Re-verify
        print(f"     🔍 Re-verifying...")
        verification = run_verification(
            fixed, original_section, original_summary,
            section_id, sec_title, verify_prompt_template, client
        )
        with open(verify_file, "w", encoding="utf-8") as f:
            json.dump(verification, f, indent=2, ensure_ascii=False)

        # Check result
        new_issues = collect_issues(verification)
        new_crit = sum(1 for i in new_issues if i.get("severity") == "critical")
        new_mod = sum(1 for i in new_issues if i.get("severity") == "moderate")
        print(f"     📊 After fix: {new_crit} critical, {new_mod} moderate")

        if not has_critical_or_moderate(verification):
            print(f"  ✅ {section_id} PASSES after {iteration} fix iteration(s)!")
            return True

    print(f"  ⚠️  {section_id} still has issues after {max_iterations} iterations — needs manual review")
    return False


def run_verification(structured, original_section, original_summary,
                     section_id, section_title, prompt_template, client):
    """Run AI verification on structured content."""
    # Build original text
    original_parts = []
    original_parts.append(f"Learning Objectives: {json.dumps(original_section.get('learning_objectives', []))}")
    for block in original_section.get("content_blocks", []):
        fmt = block.get("format", "text")
        content = block.get("content", "")
        if isinstance(content, str):
            original_parts.append(f"[{fmt}] {content}")
        elif isinstance(content, list):
            original_parts.append(f"[{fmt}] {json.dumps(content)}")
    if original_summary:
        original_parts.append(f"Summary: {json.dumps(original_summary)}")
    original_content = "\n\n".join(original_parts)

    # Build structured text for verification
    structured_parts = []
    for level in structured.get("levels", []):
        structured_parts.append(f"=== Level {level.get('level','?')}: {level.get('title','')} ===")
        for seg in level.get("learn_segments", []):
            structured_parts.append(f"LEARN: {seg.get('display_text', seg.get('narrator_text', ''))}")
        for q in level.get("check_questions", []):
            options_str = " | ".join(q.get("options", []))
            cidx = q.get("correct_index")
            opts = q.get("options", [])
            correct = opts[cidx] if cidx is not None and isinstance(cidx, int) and 0 <= cidx < len(opts) else "?"
            structured_parts.append(f"Q: {q.get('question_text','')} [{options_str}] CORRECT: {correct}")
        aq = level.get("apply_question")
        if aq:
            options_str = " | ".join(aq.get("options", []))
            cidx = aq.get("correct_index")
            opts = aq.get("options", [])
            correct = opts[cidx] if cidx is not None and isinstance(cidx, int) and 0 <= cidx < len(opts) else "?"
            structured_parts.append(f"APPLY: {aq.get('question_text','')} [{options_str}] CORRECT: {correct}")
    structured_content = "\n".join(structured_parts)

    prompt = prompt_template.format(
        original_content=original_content[:8000],
        structured_content=structured_content[:8000],
        section_id=section_id,
        section_title=section_title,
    )
    return client.enrich(prompt, phase=f"verify_{section_id}")


def run(subject: str, target: str = None, max_iterations: int = 3):
    """Run fix+verify loop on sections."""
    client = GeminiClient()
    struct_dir = STRUCTURED_DIR / subject

    if not struct_dir.exists():
        print(f"No structured content for {subject}")
        return

    # Collect sections to process
    sections_to_fix = []
    for sf in sorted(struct_dir.glob("*.json")):
        data = json.loads(sf.read_text(encoding="utf-8"))
        sec_id = data.get("section_id", "?")

        if target:
            if "." in target:
                if sec_id != target:
                    continue
            else:
                if not sec_id.startswith(target + "."):
                    continue

        sections_to_fix.append(sec_id)

    print(f"{'='*70}")
    print(f"🔧 FIX & VERIFY LOOP: {subject}")
    print(f"   Sections: {', '.join(sections_to_fix)}")
    print(f"   Max iterations per section: {max_iterations}")
    print(f"{'='*70}")

    results = {}
    for sec_id in sections_to_fix:
        print(f"\n{'─'*50}")
        print(f"📋 {sec_id}")
        print(f"{'─'*50}")
        passed = fix_section(subject, sec_id, client, max_iterations)
        results[sec_id] = passed

    # Summary
    print(f"\n{'='*70}")
    print(f"📊 FIX & VERIFY RESULTS")
    print(f"{'='*70}")
    for sec_id, passed in results.items():
        status = "✅ PASSED" if passed else "⚠️  NEEDS MANUAL REVIEW"
        print(f"  {sec_id}: {status}")

    passed_count = sum(1 for v in results.values() if v)
    print(f"\n  {passed_count}/{len(results)} sections passed")

    client.print_cost_summary()
    client.save_usage_log(f"usage_fix_verify_{subject}.json")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/fix_and_verify.py <subject> [chapter_or_section] [--max N]")
        sys.exit(1)

    subj = sys.argv[1]
    tgt = None
    max_iter = 3

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--max" and i + 1 < len(args):
            max_iter = int(args[i + 1])
            i += 2
        else:
            tgt = args[i]
            i += 1

    run(subj, tgt, max_iter)
