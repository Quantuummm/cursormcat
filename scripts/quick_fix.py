"""
Single fix pass for one section. Run repeatedly until verification passes.
Designed to complete within ~60 seconds (one Gemini call).

Usage:
    python scripts/quick_fix.py biology 1.2 fix       # Apply fix
    python scripts/quick_fix.py biology 1.2 verify     # Re-verify only
    python scripts/quick_fix.py biology 1.2 status     # Check current status
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import EXTRACTED_DIR, STRUCTURED_DIR, PROMPTS_DIR
from utils.gemini_client import GeminiClient


def get_original(subject, section_id):
    chapter_num = int(section_id.split(".")[0])
    ch_files = sorted((EXTRACTED_DIR / subject).glob(f"ch{chapter_num:02d}_*.json"))
    ch_files = [f for f in ch_files if "_assessment" not in f.name]
    if not ch_files:
        return {}, []
    ch_data = json.loads(ch_files[0].read_text(encoding="utf-8"))
    section = next((s for s in ch_data.get("sections", []) if s.get("section_id") == section_id), {})
    summary = []
    for s in ch_data.get("summary", {}).get("by_section", []):
        if s["section_id"] == section_id:
            summary = s.get("summary_points", [])
    return section, summary


def original_to_text(section, summary):
    parts = []
    parts.append(f"Learning Objectives: {json.dumps(section.get('learning_objectives', []))}")
    for block in section.get("content_blocks", []):
        fmt = block.get("format", "text")
        c = block.get("content", "")
        parts.append(f"[{fmt}] {json.dumps(c) if isinstance(c, list) else c}")
    if summary:
        parts.append(f"Summary: {json.dumps(summary)}")
    return "\n\n".join(parts)


def structured_to_claims(structured):
    parts = []
    for level in structured.get("levels", []):
        parts.append(f"=== Level {level.get('level','?')}: {level.get('title','')} ===")
        for seg in level.get("learn_segments", []):
            parts.append(f"LEARN: {seg.get('display_text', seg.get('narrator_text', ''))}")
        for q in level.get("check_questions", []):
            opts = q.get("options", [])
            cidx = q.get("correct_index")
            correct = opts[cidx] if cidx is not None and 0 <= cidx < len(opts) else "?"
            parts.append(f"Q: {q.get('question_text','')} [{' | '.join(opts)}] CORRECT: {correct}")
        aq = level.get("apply_question")
        if aq:
            opts = aq.get("options", [])
            cidx = aq.get("correct_index")
            correct = opts[cidx] if cidx is not None and 0 <= cidx < len(opts) else "?"
            parts.append(f"APPLY: {aq.get('question_text','')} [{' | '.join(opts)}] CORRECT: {correct}")
    return "\n".join(parts)


def find_struct_file(subject, section_id):
    for f in (STRUCTURED_DIR / subject).glob("*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("section_id") == section_id:
            return f
    return None


def cmd_status(subject, section_id):
    vf = STRUCTURED_DIR / subject / "_verification" / f"{section_id}_verification.json"
    if not vf.exists():
        print(f"  No verification yet — run: python scripts/quick_fix.py {subject} {section_id} verify")
        return
    v = json.loads(vf.read_text(encoding="utf-8"))
    issues = []
    for cat in ["hallucinations", "inaccuracies", "wrong_answers", "misleading_simplifications"]:
        for item in v.get("verification_details", {}).get(cat, []):
            issues.append(item)
    crit = sum(1 for i in issues if i.get("severity") == "critical")
    mod = sum(1 for i in issues if i.get("severity") == "moderate")
    minor = sum(1 for i in issues if i.get("severity") == "minor")
    print(f"  {section_id}: {crit} critical, {mod} moderate, {minor} minor")
    if crit == 0 and mod == 0:
        print(f"  STATUS: PASSED")
    else:
        print(f"  STATUS: NEEDS FIX")
        for i in issues:
            sev = i.get("severity", "?")
            if sev in ("critical", "moderate"):
                marker = "RED" if sev == "critical" else "YLW"
                cat = i.get("category", "?")
                text = i.get("structured_text", i.get("question_text", ""))[:80]
                print(f"    [{marker}] {cat}: {text}")


def cmd_verify(subject, section_id):
    client = GeminiClient()
    sf = find_struct_file(subject, section_id)
    if not sf:
        print(f"  No structured file for {section_id}")
        return
    structured = json.loads(sf.read_text(encoding="utf-8"))
    section, summary = get_original(subject, section_id)
    orig_text = original_to_text(section, summary)
    claims_text = structured_to_claims(structured)

    prompt_template = (PROMPTS_DIR / "verify_accuracy.txt").read_text(encoding="utf-8")
    prompt = prompt_template.format(
        original_content=orig_text[:8000],
        structured_content=claims_text[:8000],
        section_id=section_id,
        section_title=structured.get("title", ""),
    )
    print(f"  Verifying {section_id}...")
    result = client.enrich(prompt, phase=f"verify_{section_id}")

    vdir = STRUCTURED_DIR / subject / "_verification"
    vdir.mkdir(exist_ok=True)
    vpath = vdir / f"{section_id}_verification.json"
    with open(vpath, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    cmd_status(subject, section_id)


def cmd_fix(subject, section_id):
    client = GeminiClient()
    sf = find_struct_file(subject, section_id)
    if not sf:
        print(f"  No structured file for {section_id}")
        return

    vf = STRUCTURED_DIR / subject / "_verification" / f"{section_id}_verification.json"
    if not vf.exists():
        print(f"  No verification file — running verify first...")
        cmd_verify(subject, section_id)
        vf = STRUCTURED_DIR / subject / "_verification" / f"{section_id}_verification.json"

    structured = json.loads(sf.read_text(encoding="utf-8"))
    verification = json.loads(vf.read_text(encoding="utf-8"))

    # Collect critical+moderate issues
    issues = []
    for cat in ["hallucinations", "inaccuracies", "wrong_answers", "misleading_simplifications"]:
        for item in verification.get("verification_details", {}).get(cat, []):
            if item.get("severity") in ("critical", "moderate"):
                item["category"] = cat
                issues.append(item)

    if not issues:
        print(f"  No critical/moderate issues — {section_id} is clean!")
        return

    print(f"  Fixing {len(issues)} critical/moderate issues in {section_id}...")

    section, summary = get_original(subject, section_id)
    orig_text = original_to_text(section, summary)

    fix_template = (PROMPTS_DIR / "fix_content.txt").read_text(encoding="utf-8")
    prompt = fix_template.format(
        original_content=orig_text[:6000],
        current_structured=json.dumps(structured, indent=2)[:12000],
        issues_json=json.dumps(issues, indent=2),
    )

    print(f"  Calling Gemini 3 Flash to fix...")
    fixed = client.restructure(prompt, phase=f"fix_{section_id}")

    if isinstance(fixed, list):
        if fixed and isinstance(fixed[0], dict) and "levels" in fixed[0]:
            fixed = fixed[0]

    if not fixed.get("levels"):
        print(f"  Fix produced invalid output — try again")
        return

    with open(sf, "w", encoding="utf-8") as f:
        json.dump(fixed, f, indent=2, ensure_ascii=False)
    print(f"  Saved fixed version. Now run verify to check.")
    client.print_cost_summary()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python scripts/quick_fix.py <subject> <section_id> <fix|verify|status>")
        sys.exit(1)
    subj, sec, cmd = sys.argv[1], sys.argv[2], sys.argv[3]
    if cmd == "status":
        cmd_status(subj, sec)
    elif cmd == "verify":
        cmd_verify(subj, sec)
    elif cmd == "fix":
        cmd_fix(subj, sec)
    else:
        print(f"Unknown command: {cmd}. Use: fix, verify, or status")
