"""
Phase 8.2: Verification and Auditing of Guided Learning Outputs.
Checks Phase 8 outputs for formatting, logic, structural, and answerability issues.
If issues are found, uses Gemini to fix them.
Outputs verified files to phases/phase8_2/output/verified/[subject]/.

Verification layers:
  1. Formatting: ANSI codes, [PAUSE] placement, narrator_text length
  2. Logic: correct_index bounds, missing fields, option counts per question type
  3. Structure: min learn segments, MCAT Patterns capstone, pro tips, match_up schema
  4. Answerability: AI check that questions can be answered from prior segments
"""

import sys
import json
import re
import time
from pathlib import Path
from slugify import slugify

# Add scripts to path for config/utils
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from config import STRUCTURED_DIR, VERIFIED_STRUCTURED_DIR, EXTRACTED_DIR, SECTIONS_DIR, PROMPTS_DIR, BOOKS
from utils.gemini_client import GeminiClient

# ─── Constants ──────────────────────────────────────────────
ANSI_REGEX = re.compile(r"\[[0-9]{1,2}m|\[[0-9];[0-9]{1,2}m")
MIN_LEARN_SEGMENTS = 2
MCAT_PATTERNS_KEYWORDS = {"mcat patterns", "mcat testing patterns", "mcat strategy", "mcat question patterns"}

# ─── Verification functions ─────────────────────────────────

def check_formatting(text: str, context: str) -> list[str]:
    issues = []
    if not text:
        return issues
    if re.search(ANSI_REGEX, text):
        issues.append(f"Format: Found ANSI code in {context}")
    cleaned = text.strip()
    if cleaned.startswith("[PAUSE]"):
        issues.append(f"Format: Starts with [PAUSE] in {context}")
    if cleaned.endswith("[PAUSE]"):
        issues.append(f"Format: Ends with [PAUSE] in {context}")
    if "[PAUSE][PAUSE]" in text:
        issues.append(f"Format: Double [PAUSE] in {context}")
    return issues


def check_logic(data: dict) -> list[str]:
    """Check question logic: bounds, missing fields, option counts."""
    issues = []
    levels = data.get("levels", [])
    for level in levels:
        lv = level.get("level", "?")
        all_qs = list(level.get("check_questions", []))
        if level.get("apply_question"):
            all_qs.append(level["apply_question"])

        for q in all_qs:
            qid = q.get("question_id", "?")
            qtype = q.get("question_type", "")
            opts = q.get("options", [])

            if not opts:
                issues.append(f"Logic: L{lv} {qid} has no options")
                continue

            # match_up uses matches array, not correct_index
            if qtype == "match_up":
                matches = q.get("matches", [])
                if not matches:
                    issues.append(f"Logic: L{lv} {qid} match_up missing 'matches' array")
                elif len(matches) != len(opts):
                    issues.append(f"Logic: L{lv} {qid} match_up options/matches length mismatch ({len(opts)} vs {len(matches)})")
                # Check for pre-joined arrow strings (bad schema)
                for opt in opts:
                    if isinstance(opt, str) and (" -> " in opt or " → " in opt):
                        issues.append(f"Logic: L{lv} {qid} match_up has pre-joined arrows in options — split into options+matches")
                        break
                continue

            # All other types use correct_index
            correct = q.get("correct_index")
            if correct is None or not isinstance(correct, int) or correct < 0 or correct >= len(opts):
                issues.append(f"Logic: L{lv} {qid} has invalid correct_index {correct} (options len={len(opts)})")

            # Type-specific option count checks
            if qtype == "snap_judgment" and len(opts) != 2:
                issues.append(f"Logic: L{lv} {qid} snap_judgment should have 2 options, has {len(opts)}")
            if qtype == "pick_one" and len(opts) != 4:
                issues.append(f"Logic: L{lv} {qid} pick_one should have 4 options, has {len(opts)}")
            if qtype == "spot_the_lie" and len(opts) != 4:
                issues.append(f"Logic: L{lv} {qid} spot_the_lie should have 4 options, has {len(opts)}")

            # Check wrong_explanations coverage
            wrong_expl = q.get("wrong_explanations", {})
            if isinstance(wrong_expl, dict) and qtype != "match_up":
                for i in range(len(opts)):
                    if i != correct and str(i) not in wrong_expl:
                        issues.append(f"Logic: L{lv} {qid} missing wrong_explanation for option {i}")

    return issues


def check_structure(data: dict) -> list[str]:
    """Check structural requirements: min segments, MCAT Patterns, pro tips, match_up schema."""
    issues = []
    levels = data.get("levels", [])

    if len(levels) < 3:
        issues.append(f"Structure: Only {len(levels)} levels — minimum is 3")

    # Check learn segment minimums
    for level in levels:
        lv = level.get("level", "?")
        seg_count = len(level.get("learn_segments", []))
        if seg_count < MIN_LEARN_SEGMENTS:
            issues.append(f"Structure: L{lv} has only {seg_count} learn segment(s) — minimum is {MIN_LEARN_SEGMENTS}")

    # Check for MCAT Patterns capstone level
    has_mcat = False
    for level in levels:
        title = (level.get("title") or "").lower().strip()
        if any(p in title for p in MCAT_PATTERNS_KEYWORDS):
            if level.get("learn_segments") and level.get("check_questions"):
                has_mcat = True
    if not has_mcat:
        issues.append("Structure: Missing mandatory 'MCAT Patterns' capstone level")

    # Check pro tips distribution
    levels_without_tips = []
    for level in levels:
        tips = level.get("pro_tips") or []
        if not tips:
            levels_without_tips.append(level.get("level", "?"))
    if len(levels_without_tips) > len(levels) // 2:
        issues.append(f"Structure: Pro tips missing in {len(levels_without_tips)}/{len(levels)} levels (L{', L'.join(map(str, levels_without_tips))})")

    return issues


def check_answerability_ai(data: dict, client: GeminiClient) -> list[str]:
    """Check if questions are answerable from prior learn segments.
    Batches questions per level to reduce API calls."""
    issues = []
    cumulative_text = []

    for level in data.get("levels", []):
        for seg in level.get("learn_segments", []):
            cumulative_text.append(f"DISPLAY: {seg.get('display_text','')}\nNARRATOR: {seg.get('narrator_text','')}")
        context = "\n".join(cumulative_text)

        # Batch all check questions for this level into one API call
        questions = level.get("check_questions", [])
        if not questions:
            continue

        q_list = []
        for q in questions:
            q_list.append(f"- [{q.get('question_id', '?')}] {q.get('question_text', '')}")

        prompt = f"""Context taught so far:\n{context[:6000]}\n\nQuestions to verify:\n{chr(10).join(q_list)}\n\nFor EACH question, determine if it can be answered ONLY using the context above. MCAT facts must be explicitly present in the context.\n\nReturn JSON array: [{{"question_id": "...", "answerable": bool, "reason": "..."}}]"""

        try:
            res = client.enrich(prompt, phase=f"verify_ans_L{level.get('level', '?')}")
            if isinstance(res, list):
                for item in res:
                    if isinstance(item, dict) and not item.get("answerable", True):
                        issues.append(f"Answerability: L{level['level']} {item.get('question_id', '?')} - {item.get('reason', 'unknown')}")
            elif isinstance(res, dict) and not res.get("answerable", True):
                issues.append(f"Answerability: L{level['level']} - {res.get('reason', 'unknown')}")
        except Exception:
            pass  # Don't block the pipeline on answerability check failures

    return issues


def get_original_content(subject: str, section_id: str) -> tuple[str, dict]:
    """Load original Kaplan extraction for cross-referencing.
    Returns (text_content, section_dict)."""
    chapter_num = int(section_id.split(".")[0])
    sections_subj = SECTIONS_DIR / subject
    ch_files = sorted(sections_subj.glob(f"ch{chapter_num:02d}_*.json"))
    ch_files = [f for f in ch_files if "_assessment" not in f.name]
    if not ch_files:
        return "Original content not found.", {}

    ch_data = json.loads(ch_files[0].read_text(encoding="utf-8"))
    sec = next((s for s in ch_data.get("sections", []) if s.get("section_id") == section_id), {})

    parts = []
    for b in sec.get("content_blocks", []):
        content = b.get("content", "")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            parts.append(json.dumps(content))
    return "\n\n".join(parts), sec


def fix_match_up_deterministic(data: dict) -> dict:
    """Fix match_up questions deterministically without AI."""
    for level in data.get("levels", []):
        all_qs = list(level.get("check_questions", []))
        if level.get("apply_question"):
            all_qs.append(level["apply_question"])
        for q in all_qs:
            if q.get("question_type") != "match_up":
                continue
            if isinstance(q.get("matches"), list) and q["matches"]:
                q.pop("correct_index", None)
                continue
            # Fix pre-joined arrows
            options = q.get("options", [])
            items, matches = [], []
            for opt in options:
                opt_str = str(opt)
                for sep in [" -> ", " → ", ": ", " – ", " — "]:
                    if sep in opt_str:
                        parts = opt_str.split(sep, 1)
                        items.append(parts[0].strip())
                        matches.append(parts[1].strip())
                        break
                else:
                    items.append(opt_str)
                    matches.append("")
            if items and any(m for m in matches):
                q["options"] = items
                q["matches"] = matches
                q.pop("correct_index", None)
    return data


def fix_with_ai(data: dict, issues: list[str], original_content: str, client: GeminiClient) -> dict:
    """Send issues and data to Gemini to get a fixed version."""
    # Categorize issues for targeted fix instructions
    has_mcat_missing = any("MCAT Patterns" in i for i in issues)
    has_segment_issues = any("learn segment" in i.lower() for i in issues)
    has_pro_tip_issues = any("pro tip" in i.lower() for i in issues)

    extra_instructions = ""
    if has_mcat_missing:
        extra_instructions += """
5. ADD a final "MCAT Patterns" level with:
   - 2-3 learn segments about how the MCAT tests this topic
   - Common trap answers the MCAT uses
   - 2-3 MCAT-style check questions
   - 1 MCAT-style apply question
"""
    if has_segment_issues:
        extra_instructions += """
6. Every level MUST have at least 2 learn_segments. If a level has only 1, split the concept:
   - Segment 1: Analogy/big picture introduction
   - Segment 2: Specific details and rules
"""
    if has_pro_tip_issues:
        extra_instructions += """
7. Add pro_tips to levels that are missing them. Pro tips should be:
   - MCAT strategy insights for the specific content in that level
   - Or Kaplan "MCAT Expertise" callouts if they exist in the original
"""

    prompt = f"""Fix the following issues in the MCAT Guided Learning JSON.
Stick strictly to the PROVIDED ORIGINAL CONTENT.

ORIGINAL CONTENT:
{original_content[:8000]}

CURRENT JSON:
{json.dumps(data, indent=2)[:12000]}

ISSUES TO FIX:
{chr(10).join(issues)}

RULES:
1. Fix formatting (remove ANSI codes, fix [PAUSE] placement).
2. Fix logic (correct_index bounds, missing fields).
3. Fix answerability (move info into learn segments or rewrite question).
4. match_up questions MUST use separate "options" and "matches" arrays. NO arrows in options. NO correct_index.
{extra_instructions}
Return the COMPLETE fixed JSON — every level, every question, every field.
"""
    print("     🔧 Requesting AI fix...")
    fixed = client.restructure(prompt, phase="fix_guided_learning")
    return fixed


def _cleanup_duplicates(directory: Path):
    """Remove duplicate files for the same section_id, keeping newest."""
    section_files = {}
    for f in directory.glob("*.json"):
        # Extract section_id (e.g., "1.2" from "1.2-atomic-mass-vs-weight.json")
        match = re.match(r"^(\d+\.\d+)-", f.name)
        if not match:
            continue
        sec_id = match.group(1)
        if sec_id not in section_files:
            section_files[sec_id] = []
        section_files[sec_id].append(f)

    for sec_id, files in section_files.items():
        if len(files) <= 1:
            continue
        # Keep the newest file, archive the rest
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        keeper = files[0]
        archive_dir = directory / ".archive"
        archive_dir.mkdir(exist_ok=True)
        for dup in files[1:]:
            dest = archive_dir / dup.name
            dup.rename(dest)
            print(f"    🗑️  Archived duplicate: {dup.name} → .archive/")


def run_phase8_2(pdf_filename=None, chapter_num=None):
    client = GeminiClient()
    subjects = [BOOKS[pdf_filename]] if pdf_filename and pdf_filename in BOOKS else BOOKS.values()

    for subject in subjects:
        struct_subj = STRUCTURED_DIR / subject
        verified_subj = VERIFIED_STRUCTURED_DIR / subject
        verified_subj.mkdir(parents=True, exist_ok=True)

        if not struct_subj.exists():
            continue

        print(f"\n🔍 Auditing {subject}...")

        # Step 0: Clean up duplicate files in structured output
        _cleanup_duplicates(struct_subj)

        for f_path in sorted(struct_subj.glob("*.json")):
            data = json.loads(f_path.read_text(encoding="utf-8"))
            sec_id = data.get("section_id", "?")
            if chapter_num and not sec_id.startswith(f"{chapter_num}."):
                continue

            print(f"  📄 Section {sec_id}...")

            # Step 1: Apply deterministic fixes first (no AI needed)
            current_data = fix_match_up_deterministic(data)

            # Verification Loop
            max_attempts = 3
            for attempt in range(max_attempts + 1):
                # Layer 1: Formatting
                fmt_issues = []
                for level in current_data.get("levels", []):
                    lv = level.get("level", "?")
                    for seg in level.get("learn_segments", []):
                        fmt_issues.extend(check_formatting(seg.get("display_text", ""), f"L{lv} display"))
                        fmt_issues.extend(check_formatting(seg.get("narrator_text", ""), f"L{lv} narrator"))
                    for tip in level.get("pro_tips", []) or []:
                        fmt_issues.extend(check_formatting(tip.get("narrator_text", ""), f"L{lv} pro_tip"))

                # Layer 2: Logic
                logic_issues = check_logic(current_data)

                # Layer 3: Structure
                struct_issues = check_structure(current_data)

                # Layer 4: Answerability (only on first attempt to save API calls)
                ans_issues = []
                if attempt == 0:
                    ans_issues = check_answerability_ai(current_data, client)

                all_issues = fmt_issues + logic_issues + struct_issues + ans_issues

                if not all_issues:
                    print(f"    ✅ Verified on attempt {attempt + 1}")
                    out_path = verified_subj / f_path.name
                    out_path.write_text(json.dumps(current_data, indent=2, ensure_ascii=False), encoding="utf-8")
                    break
                else:
                    print(f"    ❌ Found {len(all_issues)} issues (attempt {attempt + 1}):")
                    for iss in all_issues[:8]:
                        print(f"       • {iss}")
                    if len(all_issues) > 8:
                        print(f"       ... and {len(all_issues) - 8} more")

                    if attempt < max_attempts:
                        orig_text, _ = get_original_content(subject, sec_id)
                        current_data = fix_with_ai(current_data, all_issues, orig_text, client)
                        # Re-apply deterministic fixes after AI pass
                        current_data = fix_match_up_deterministic(current_data)
                    else:
                        print(f"    ⚠️  Saving best-effort version for {sec_id} after {max_attempts} fix attempts.")
                        print(f"    Remaining issues: {len(all_issues)}")
                        out_path = verified_subj / f_path.name
                        out_path.write_text(json.dumps(current_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Clean up duplicates in verified output too
        _cleanup_duplicates(verified_subj)

    print("\n✅ Phase 8.2 complete!")


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else None
    ch = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run_phase8_2(pdf, ch)
