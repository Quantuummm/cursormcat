"""
Verify Guided Learning Content (Phase 8).
Checks for:
1. Formatting issues: ANSI escape codes (e.g., [37m), improper [PAUSE] placement.
2. Logic issues: correct_index bounds, missing explanations.
3. Answerability: Do learn segments provide enough info for check questions? (AI-assisted)

Usage:
    python scripts/verify_guided_learning.py gen_chem 1.1
    python scripts/verify_guided_learning.py gen_chem 1
    python scripts/verify_guided_learning.py gen_chem
"""

import sys
import json
import re
from pathlib import Path

# Add scripts to path for config/utils
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from config import STRUCTURED_DIR, PROMPTS_DIR, BOOKS
from utils.gemini_client import GeminiClient

ANSI_REGEX = re.compile(r"(\[([0-9]{1,2};?)+m)")

def check_formatting(text: str, context: str) -> list[str]:
    issues = []
    if not text:
        return issues
    
    # Check for ANSI codes (looking for both literal and escaped variations)
    # Literal [37m or code \x1b[37m
    if "[3" in text and "m" in text:
        ansi_patterns = [r"\[[0-9]{1,2}m", r"\[[0-9];[0-9]{1,2}m"]
        for p in ansi_patterns:
            if re.search(p, text):
                issues.append(f"Format: Found ANSI-like code in {context}: {text}")
                break
             
    # Check for [PAUSE] issues
    cleaned = text.strip()
    if cleaned.startswith("[PAUSE]"):
        issues.append(f"Format: String starts with [PAUSE] in {context}")
    if cleaned.endswith("[PAUSE]"):
        issues.append(f"Format: String ends with [PAUSE] in {context}")
    if "[PAUSE][PAUSE]" in text:
        issues.append(f"Format: Double [PAUSE] found in {context}")
        
    return issues

def check_logic(data: dict) -> list[str]:
    issues = []
    levels = data.get("levels", [])
    if not levels:
        issues.append("Structure: No levels found")
        return issues

    for level in levels:
        lv = level.get("level", "?")
        
        # Check Questions
        cqs = level.get("check_questions", [])
        for q in cqs:
            qid = q.get("question_id", "?")
            opts = q.get("options", [])
            idx = q.get("correct_index")
            if not opts:
                issues.append(f"Logic: L{lv} {qid} has no options")
            if idx is None or not isinstance(idx, int) or idx < 0 or idx >= len(opts):
                issues.append(f"Logic: L{lv} {qid} has invalid correct_index {idx}")
            
            # Formatting in questions
            issues.extend(check_formatting(q.get("question_text", ""), f"L{lv} CQ {qid}"))
            issues.extend(check_formatting(q.get("correct_response", ""), f"L{lv} CQ {qid} response"))
            issues.extend(check_formatting(q.get("wrong_response", ""), f"L{lv} CQ {qid} wrong_response"))

        # Apply Question
        aq = level.get("apply_question")
        if aq:
            aqid = aq.get("question_id", "?")
            opts = aq.get("options", [])
            idx = aq.get("correct_index")
            if not opts:
                issues.append(f"Logic: L{lv} AQ {aqid} has no options")
            if idx is None or not isinstance(idx, int) or idx < 0 or idx >= len(opts):
                issues.append(f"Logic: L{lv} AQ {aqid} has invalid correct_index {idx}")
            
            issues.extend(check_formatting(aq.get("scenario", ""), f"L{lv} AQ {aqid} scenario"))
            issues.extend(check_formatting(aq.get("question_text", ""), f"L{lv} AQ {aqid} text"))

        # Mission Briefing
        mb = data.get("mission_briefing", {})
        issues.extend(check_formatting(mb.get("narrator_text", ""), "Mission Briefing narrator"))
        issues.extend(check_formatting(mb.get("display_text", ""), "Mission Briefing display"))

    return issues

def check_section_answerability(structured: dict, client: GeminiClient) -> list[dict]:
    """Use AI to verify if each check question is answerable from PRIOR learn segments."""
    issues = []
    levels = structured.get("levels", [])
    
    # Cumulative content
    cumulative_text = []
    
    for level in levels:
        lv_num = level.get("level", "?")
        
        # Add current level's learn segments to cumulative text
        for seg in level.get("learn_segments", []):
            cumulative_text.append(f"DISPLAY: {seg.get('display_text','')}")
            cumulative_text.append(f"NARRATOR: {seg.get('narrator_text', '')}")
            
        context_so_far = "\n".join(cumulative_text)
        
        # Check questions in this level
        for q in level.get("check_questions", []):
            qid = q.get("question_id", "?")
            q_text = q.get("question_text", "")
            
            prompt = f"""
You are a teaching assistant verifying a guided learning lesson.
The student has just seen the following information:

{context_so_far}

Now the student is asked this question:
Question: {q_text}

Can this question be answered ONLY using the information provided above? 
Note: If the question asks about basic common knowledge (like 1+1=2) it is OK, but if it's about MCAT facts (like specific masses or charges), it MUST be in the provided text.

If NO, explain what is missing.
If YES, simply respond with 'YES'.

Your response should be in JSON format:
{{
  "answerable": true,
  "reason": "If false, explanation of what's missing"
}}
"""
            # print(f"       Testing Q: {qid}...")
            try:
                res = client.enrich(prompt, phase=f"verify_q_{qid}")
                if not res.get("answerable"):
                    issues.append({
                        "id": qid,
                        "type": "check_question",
                        "issue": f"Not answerable from learn segments: {res.get('reason')}",
                        "level": lv_num
                    })
            except Exception as e:
                print(f"       ⚠️ Error verifying question {qid}: {e}")

        # Check apply question
        aq = level.get("apply_question")
        if aq:
            aq_id = aq.get("question_id", "?")
            aq_text = aq.get("question_text", "")
            aq_scenario = aq.get("scenario", "")
            
            # Apply questions ARE allowed to have a scenario that introduces new context, 
            # but the PRINCIPLE behind it should be taught.
            prompt = f"""
You are a teaching assistant verifying a guided learning lesson.
The student has just seen the following information:

{context_so_far}

Now the student is presented with this scenario/question:
Scenario: {aq_scenario}
Question: {aq_text}

Does the PRIOR information (not the scenario itself) teach the underlying concept needed to solve this?
If the information provided is completely unrelated to the scenario's requirements, flag it.

Response in JSON:
{{
  "answerable": true,
  "reason": "If false, explanation"
}}
"""
            try:
                res = client.enrich(prompt, phase=f"verify_aq_{aq_id}")
                if not res.get("answerable"):
                    issues.append({
                        "id": aq_id,
                        "type": "apply_question",
                        "issue": f"Concept not taught: {res.get('reason')}",
                        "level": lv_num
                    })
            except Exception as e:
                print(f"       ⚠️ Error verifying apply question {aq_id}: {e}")

    return issues

def run_verification(subject: str, target_id: str = None):
    client = GeminiClient()
    subject_dir = STRUCTURED_DIR / subject
    
    if not subject_dir.exists():
        print(f"Directory not found: {subject_dir}")
        return

    files = sorted(subject_dir.glob("*.json"))
    
    overall_summary = []

    for f in files:
        if target_id:
            if not (f.name.startswith(target_id) or f.stem == target_id):
                continue
                
        print(f"\n{'='*60}")
        print(f"📂 Verifying: {f.name}")
        print(f"{'='*60}")
        
        try:
            with open(f, "r", encoding="utf-8") as file:
                data = json.load(file)
            
            # 1. Logic & Basic Formatting
            logic_issues = check_logic(data)
            
            # Additional formatting for learn segments (manual loop)
            fmt_issues = []
            for level in data.get("levels", []):
                lv = level.get("level", "?")
                for seg in level.get("learn_segments", []):
                    fmt_issues.extend(check_formatting(seg.get("display_text", ""), f"L{lv} display_text"))
                    fmt_issues.extend(check_formatting(seg.get("narrator_text", ""), f"L{lv} narrator_text"))
            
            all_auto_issues = logic_issues + fmt_issues
            if all_auto_issues:
                print(f"  ❌ Automated Checks: {len(all_auto_issues)} issues")
                for iss in all_auto_issues:
                    print(f"     - {iss}")
            else:
                print(f"  ✅ Automated Checks: passed")

            # 2. Answerability Checks (AI assisted)
            print(f"  🔬 Verifying Answerability (Gemini 3 Flash)...")
            ans_issues = check_section_answerability(data, client)
            if ans_issues:
                print(f"  ❌ Answerability: {len(ans_issues)} issues")
                for iss in ans_issues:
                    print(f"     - L{iss['level']} [{iss['id']}]: {iss['issue']}")
            else:
                print(f"  ✅ Answerability: passed")
            
            overall_summary.append({
                "file": f.name,
                "auto_issues": len(all_auto_issues),
                "ans_issues": len(ans_issues)
            })
                
        except Exception as e:
            print(f"  💥 Error processing file {f.name}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"VERIFICATION SUMMARY")
    print(f"{'='*60}")
    for s in overall_summary:
        status = "❌" if s["auto_issues"] > 0 or s["ans_issues"] > 0 else "✅"
        print(f"{status} {s['file']}: {s['auto_issues']} auto issues, {s['ans_issues']} answerability issues")

if __name__ == "__main__":
    subj = sys.argv[1] if len(sys.argv) > 1 else "gen_chem"
    target = sys.argv[2] if len(sys.argv) > 2 else ""
    run_verification(subj, target)
