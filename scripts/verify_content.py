"""
Content Verification: Cross-checks structured guided learning against original Kaplan extraction.
Uses Gemini 3 Flash as an independent verifier to catch hallucinations, wrong answers, and inaccuracies.

Three verification layers:
  1. AUTOMATED: Check that every question's correct_index is within bounds
  2. CROSS-REFERENCE: Verify key terms in structured content exist in original extraction
  3. AI VERIFICATION: Send both to Gemini 3 and ask it to flag discrepancies

Usage:
    python scripts/verify_content.py biology 1.1              # Verify one section
    python scripts/verify_content.py biology 1                 # Verify all sections in chapter
    python scripts/verify_content.py biology                   # Verify all structured sections
"""

import sys
import json
from pathlib import Path
from slugify import slugify

sys.path.insert(0, str(Path(__file__).parent))
from config import EXTRACTED_DIR, STRUCTURED_DIR, PROMPTS_DIR
from utils.gemini_client import GeminiClient


def layer1_automated_checks(structured: dict) -> list[dict]:
    """Layer 1: Pure logic checks — no AI needed."""
    issues = []
    concept_id = structured.get("concept_id", "?")

    for level in structured.get("levels", []):
        lv = level.get("level", "?")

        # Check questions have valid correct_index
        for q in level.get("check_questions", []):
            qid = q.get("question_id", "?")
            options = q.get("options", [])
            correct_idx = q.get("correct_index")

            if correct_idx is None:
                issues.append({
                    "layer": "automated",
                    "severity": "critical",
                    "issue": f"L{lv} {qid}: correct_index is missing",
                })
            elif not isinstance(correct_idx, int):
                issues.append({
                    "layer": "automated",
                    "severity": "critical",
                    "issue": f"L{lv} {qid}: correct_index is not an integer: {correct_idx}",
                })
            elif correct_idx < 0 or correct_idx >= len(options):
                issues.append({
                    "layer": "automated",
                    "severity": "critical",
                    "issue": f"L{lv} {qid}: correct_index={correct_idx} out of bounds (options has {len(options)} items)",
                })

            # Check wrong_explanations cover all wrong indices
            wrong_exp = q.get("wrong_explanations", {})
            if options and correct_idx is not None and isinstance(correct_idx, int):
                for i in range(len(options)):
                    if i != correct_idx and str(i) not in wrong_exp:
                        issues.append({
                            "layer": "automated",
                            "severity": "minor",
                            "issue": f"L{lv} {qid}: missing wrong_explanation for option {i}",
                        })

        # Check apply question
        aq = level.get("apply_question")
        if aq:
            aq_id = aq.get("question_id", "?")
            aq_options = aq.get("options", [])
            aq_correct = aq.get("correct_index")
            if aq_correct is not None and isinstance(aq_correct, int):
                if aq_correct < 0 or aq_correct >= len(aq_options):
                    issues.append({
                        "layer": "automated",
                        "severity": "critical",
                        "issue": f"L{lv} {aq_id}: apply correct_index={aq_correct} out of bounds ({len(aq_options)} options)",
                    })

        # Check narrator_text length
        for seg in level.get("learn_segments", []):
            words = len(seg.get("narrator_text", "").split())
            if words > 80:
                issues.append({
                    "layer": "automated",
                    "severity": "minor",
                    "issue": f"L{lv} segment '{seg.get('segment_id','?')}': narrator_text is {words} words (target <60)",
                })

    return issues


def layer2_cross_reference(structured: dict, original_section: dict) -> list[dict]:
    """Layer 2: Check that key terms from structured content exist in original."""
    issues = []

    # Get all text from original section
    original_text = ""
    for block in original_section.get("content_blocks", []):
        content = block.get("content", "")
        if isinstance(content, str):
            original_text += " " + content
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, str):
                    original_text += " " + item
                elif isinstance(item, dict):
                    original_text += " " + str(item.get("text", ""))
    original_text = original_text.lower()

    # Check key_terms from structured learn segments
    for level in structured.get("levels", []):
        for seg in level.get("learn_segments", []):
            key_term = seg.get("key_term", "")
            if key_term and key_term.lower() not in original_text:
                # Not necessarily an error — the restructuring might use synonyms
                issues.append({
                    "layer": "cross_reference",
                    "severity": "moderate",
                    "issue": f"Key term '{key_term}' from L{level['level']} not found verbatim in original extraction (may be rephrased)",
                })

    return issues


def layer3_ai_verification(structured: dict, original_section: dict, original_summary: list,
                           section_id: str, section_title: str, client: GeminiClient) -> dict:
    """Layer 3: AI-powered deep verification against source material."""

    prompt_template = (PROMPTS_DIR / "verify_accuracy.txt").read_text(encoding="utf-8")

    # Build original content string
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
        original_parts.append(f"Summary points: {json.dumps(original_summary)}")

    original_content = "\n\n".join(original_parts)

    # Only send the levels + questions (the parts that could hallucinate)
    structured_parts = []
    for level in structured.get("levels", []):
        structured_parts.append(f"=== Level {level['level']}: {level.get('title','')} ===")
        for seg in level.get("learn_segments", []):
            structured_parts.append(f"LEARN: {seg.get('display_text', seg.get('narrator_text', ''))}")
        for q in level.get("check_questions", []):
            options_str = " | ".join(q.get("options", []))
            correct = q["options"][q["correct_index"]] if q.get("correct_index") is not None and q.get("options") else "?"
            structured_parts.append(f"QUESTION: {q.get('question_text','')} OPTIONS: [{options_str}] CORRECT: {correct}")
        aq = level.get("apply_question")
        if aq:
            options_str = " | ".join(aq.get("options", []))
            correct = aq["options"][aq["correct_index"]] if aq.get("correct_index") is not None and aq.get("options") else "?"
            structured_parts.append(f"APPLY: {aq.get('question_text','')} OPTIONS: [{options_str}] CORRECT: {correct}")

    structured_content = "\n".join(structured_parts)

    prompt = prompt_template.format(
        original_content=original_content[:8000],  # Cap to prevent token overflow
        structured_content=structured_content[:8000],
        section_id=section_id,
        section_title=section_title,
    )

    print(f"     🔬 AI verification (Gemini 3 Flash)...")
    result = client.enrich(prompt, phase=f"verify_{section_id}")
    return result


def run(subject: str, target: str = None):
    """Run verification on structured content."""
    client = GeminiClient()

    struct_dir = STRUCTURED_DIR / subject
    if not struct_dir.exists():
        print(f"No structured content found for {subject}")
        return

    # Load original chapter data
    extracted_dir = EXTRACTED_DIR / subject
    chapter_data = {}
    for ch_file in sorted(extracted_dir.glob("ch[0-9]*_*.json")):
        if "_assessment" in ch_file.name:
            continue
        ch = json.loads(ch_file.read_text(encoding="utf-8"))
        for sec in ch.get("sections", []):
            chapter_data[sec["section_id"]] = {
                "section": sec,
                "summary": [],
            }
        for s in ch.get("summary", {}).get("by_section", []):
            if s["section_id"] in chapter_data:
                chapter_data[s["section_id"]]["summary"] = s.get("summary_points", [])

    print(f"{'='*70}")
    print(f"🔍 CONTENT VERIFICATION: {subject}")
    print(f"{'='*70}")

    total_issues = {"critical": 0, "moderate": 0, "minor": 0}
    sections_passed = 0
    sections_total = 0

    for struct_file in sorted(struct_dir.glob("*.json")):
        structured = json.loads(struct_file.read_text(encoding="utf-8"))
        sec_id = structured.get("section_id", "?")
        sec_title = structured.get("title", struct_file.stem)

        # Filter by target
        if target:
            if "." in target:
                # Specific section
                if sec_id != target:
                    continue
            else:
                # Chapter number
                if not sec_id.startswith(target + "."):
                    continue

        sections_total += 1
        print(f"\n  📋 {sec_id}: {sec_title}")

        # Layer 1: Automated checks
        l1_issues = layer1_automated_checks(structured)
        if l1_issues:
            print(f"     Layer 1 (Logic): {len(l1_issues)} issues")
            for iss in l1_issues:
                sev = iss["severity"]
                total_issues[sev] = total_issues.get(sev, 0) + 1
                marker = "🔴" if sev == "critical" else "🟡" if sev == "moderate" else "⚪"
                print(f"       {marker} [{sev}] {iss['issue']}")
        else:
            print(f"     Layer 1 (Logic): ✅ All checks passed")

        # Layer 2: Cross-reference
        if sec_id in chapter_data:
            l2_issues = layer2_cross_reference(structured, chapter_data[sec_id]["section"])
            if l2_issues:
                print(f"     Layer 2 (Cross-ref): {len(l2_issues)} items to review")
                for iss in l2_issues:
                    sev = iss["severity"]
                    total_issues[sev] = total_issues.get(sev, 0) + 1
                    print(f"       🟡 {iss['issue']}")
            else:
                print(f"     Layer 2 (Cross-ref): ✅ Key terms match")
        else:
            print(f"     Layer 2 (Cross-ref): ⏭️  No original data found for {sec_id}")

        # Layer 3: AI verification
        if sec_id in chapter_data:
            try:
                ai_result = layer3_ai_verification(
                    structured,
                    chapter_data[sec_id]["section"],
                    chapter_data[sec_id]["summary"],
                    sec_id, sec_title, client
                )

                ai_issues = ai_result.get("issues_found", 0)
                ai_passed = ai_result.get("passed", False)
                claims_checked = ai_result.get("total_claims_checked", "?")

                if ai_passed:
                    print(f"     Layer 3 (AI):  ✅ Passed ({claims_checked} claims verified)")
                    sections_passed += 1
                else:
                    print(f"     Layer 3 (AI):  ⚠️  {ai_issues} issues found ({claims_checked} claims checked)")

                    details = ai_result.get("verification_details", {})
                    for category in ["hallucinations", "inaccuracies", "wrong_answers", "misleading_simplifications"]:
                        items = details.get(category, [])
                        for item in items:
                            sev = item.get("severity", "moderate")
                            total_issues[sev] = total_issues.get(sev, 0) + 1
                            marker = "🔴" if sev == "critical" else "🟡" if sev == "moderate" else "⚪"
                            text = item.get("structured_text", item.get("question_text", ""))
                            fix = item.get("fix_suggestion", item.get("actually_correct", ""))
                            print(f"       {marker} [{category}] {text[:100]}")
                            if fix:
                                print(f"         → Fix: {fix[:100]}")

                # Save verification result
                verify_dir = STRUCTURED_DIR / subject / "_verification"
                verify_dir.mkdir(exist_ok=True)
                verify_path = verify_dir / f"{sec_id}_verification.json"
                with open(verify_path, "w", encoding="utf-8") as f:
                    json.dump(ai_result, f, indent=2, ensure_ascii=False)

            except Exception as e:
                print(f"     Layer 3 (AI):  ❌ Error: {e}")

    # Summary
    print(f"\n{'='*70}")
    print(f"📊 VERIFICATION SUMMARY")
    print(f"{'='*70}")
    print(f"  Sections verified: {sections_total}")
    print(f"  AI-passed:         {sections_passed}/{sections_total}")
    print(f"  Critical issues:   {total_issues.get('critical', 0)} 🔴")
    print(f"  Moderate issues:   {total_issues.get('moderate', 0)} 🟡")
    print(f"  Minor issues:      {total_issues.get('minor', 0)} ⚪")

    if total_issues.get("critical", 0) > 0:
        print(f"\n  ⚠️  CRITICAL ISSUES FOUND — review and fix before using this content!")
    elif total_issues.get("moderate", 0) > 0:
        print(f"\n  🟡 Some moderate issues — worth reviewing but likely usable")
    else:
        print(f"\n  ✅ Content looks accurate!")

    client.print_cost_summary()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/verify_content.py <subject> [chapter_or_section]")
        sys.exit(1)
    subj = sys.argv[1]
    tgt = sys.argv[2] if len(sys.argv) > 2 else None
    run(subj, tgt)
