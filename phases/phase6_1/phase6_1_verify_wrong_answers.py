""" 
Phase 6.1: Verify (and optionally auto-fix) wrong-answer explanations + TTS feedback
for chapter assessment questions.

Why: Phase 6 generates content not explicitly in Kaplan, so we need a dedicated
sanity/accuracy check to catch hallucinations, contradictions, and tone issues.

Requires: Phase 2 (chapter assessments) + Phase 6 (wrong-answer enrichment).

Usage:
    python phases/phase6_1/phase6_1_verify_wrong_answers.py                    # All books
    python phases/phase6_1/phase6_1_verify_wrong_answers.py biology.pdf        # One book
    python phases/phase6_1/phase6_1_verify_wrong_answers.py biology.pdf 3      # One book, one chapter
    python phases/phase6_1/phase6_1_verify_wrong_answers.py --no-fix           # Only write reports
"""

import sys
import json
import argparse
import copy
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from config import ENRICHED_ASSESSMENTS_DIR, VERIFIED_ASSESSMENTS_DIR, TEMP_VERIFICATION_DIR, BOOKS
from utils.gemini_client import GeminiClient


def _letter_from_option(opt: str) -> str:
    opt = opt.strip()
    if len(opt) >= 2 and opt[1] == ')':
        return opt[0].upper()
    return ""


def _build_question_payload(q: dict) -> dict:
    return {
        "question_number": q.get("question_number"),
        "question_text": q.get("question_text", ""),
        "options": q.get("options", []),
        "correct_letter": q.get("correct_letter", ""),
        "kaplan_explanation": q.get("kaplan_explanation", ""),
        "wrong_explanations": q.get("wrong_explanations", {}) or {},
        "tts_wrong_feedback": q.get("tts_wrong_feedback", {}) or {},
    }


def _normalize_verify_response(resp):
    """Gemini sometimes returns dict-wrapped payloads."""
    if isinstance(resp, dict) and "results" in resp and isinstance(resp["results"], list):
        return resp["results"]
    if isinstance(resp, dict) and "questions" in resp and isinstance(resp["questions"], list):
        return resp["questions"]
    if isinstance(resp, list):
        return resp
    return []


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def _verify_questions(client: GeminiClient, prompt_template: str, questions: list, ch_num: int, attempt: int) -> list:
    all_results = []
    batch = 5
    for i in range(0, len(questions), batch):
        batch_qs = questions[i : i + batch]
        payload = [_build_question_payload(q) for q in batch_qs]
        prompt = prompt_template.format(questions_json=json.dumps(payload, indent=2))
        resp = client.enrich(prompt, phase=f"P6_1_verify_ch{ch_num}_at{attempt}_{i // batch + 1}")
        results = _normalize_verify_response(resp)
        all_results.extend(results)
    return all_results


def _apply_fixes(assessment: dict, by_qnum: dict) -> int:
    fixes_this_loop = 0
    for q in assessment.get("questions", []):
        qn = q.get("question_number")
        r = by_qnum.get(qn)
        if not r or r.get("status") != "needs_fix":
            continue

        fixed_we = r.get("fixed_wrong_explanations") or {}
        fixed_tts = r.get("fixed_tts_wrong_feedback") or {}

        if fixed_we:
            q.setdefault("wrong_explanations", {})
            q["wrong_explanations"].update(fixed_we)
        if fixed_tts:
            q.setdefault("tts_wrong_feedback", {})
            q["tts_wrong_feedback"].update(fixed_tts)

        if fixed_we or fixed_tts:
            fixes_this_loop += 1

    return fixes_this_loop


def run(pdf_filename: str = None, chapter_num: int = None, apply_fixes: bool = True):
    client = GeminiClient()
    prompt_template = (Path(__file__).parent / "verify_wrong_answers.txt").read_text(encoding="utf-8")

    subjects = [BOOKS[pdf_filename]] if pdf_filename and pdf_filename in BOOKS else list(BOOKS.values())

    for subject in subjects:
        source_dir = ENRICHED_ASSESSMENTS_DIR / subject
        verified_dir = VERIFIED_ASSESSMENTS_DIR / subject
        temp_dir = TEMP_VERIFICATION_DIR / subject
        verified_dir.mkdir(parents=True, exist_ok=True)
        temp_dir.mkdir(parents=True, exist_ok=True)

        assessment_files = sorted(source_dir.glob("ch*_assessment.json"))
        if not assessment_files:
            print(f"⏭️  Skipping {subject}: No enrichment found in Phase 6")
            continue

        print(f"\n{'='*60}")
        print(f"✅ Phase 6.1: Verifying & Auto-fixing: {subject}")
        print(f"{'='*60}")

        for assess_path in assessment_files:
            assessment_original = json.loads(assess_path.read_text(encoding="utf-8"))
            ch_num = assessment_original.get("chapter_number")

            if chapter_num is not None and ch_num != chapter_num:
                continue

            questions = assessment_original.get("questions", [])
            if not questions:
                continue

            # Only verify if wrong_explanations exist
            to_check_all = [q for q in questions if q.get("wrong_explanations")]
            if not to_check_all:
                print(f"  📝 Chapter {ch_num}: no questions with wrong_explanations")
                continue

            print(f"\n  📝 Chapter {ch_num}: Starting verification loop...")

            max_runs = 3
            current_assessment = copy.deepcopy(assessment_original)

            for attempt in range(1, max_runs + 1):
                needs_checking = [q for q in current_assessment.get("questions", []) if q.get("wrong_explanations")]
                print(f"     🔄 Loop {attempt}/{max_runs}: verifying {len(needs_checking)} questions")

                all_results = _verify_questions(client, prompt_template, needs_checking, ch_num, attempt)
                by_qnum = {r.get("question_number"): r for r in all_results if isinstance(r, dict)}
                fails = [r for r in all_results if isinstance(r, dict) and r.get("status") == "needs_fix"]

                print(f"     📊 Results: {len(all_results) - len(fails)} pass, {len(fails)} needs_fix")

                if attempt == 1:
                    report_base_dir = temp_dir
                elif attempt == 2:
                    report_base_dir = TEMP_VERIFICATION_DIR / "run1" / subject
                else:
                    report_base_dir = TEMP_VERIFICATION_DIR / "run2" / subject

                report_path = report_base_dir / "reports" / f"ch{int(ch_num):02d}_v_report_attempt_{attempt}.json"
                report = {
                    "subject": subject,
                    "chapter_number": ch_num,
                    "attempt": attempt,
                    "checked": len(needs_checking),
                    "needs_fix": len(fails),
                    "results": all_results,
                }
                _write_json(report_path, report)

                if len(fails) == 0:
                    if attempt == 1:
                        verified_source = assessment_original
                    else:
                        verified_source = current_assessment
                    verified_path = verified_dir / assess_path.name
                    _write_json(verified_path, verified_source)
                    print(f"     💾 Verified output saved to {verified_path.name}")
                    break

                if not apply_fixes:
                    print("     ⚠️ Fixes disabled (--no-fix). Skipping retries.")
                    break

                fixes_this_loop = _apply_fixes(current_assessment, by_qnum)
                if attempt == 1:
                    next_dir = TEMP_VERIFICATION_DIR / "run1" / subject
                elif attempt == 2:
                    next_dir = TEMP_VERIFICATION_DIR / "run2" / subject
                else:
                    next_dir = TEMP_VERIFICATION_DIR / "run3" / subject

                next_path = next_dir / assess_path.name
                _write_json(next_path, current_assessment)

                # Reload from the saved version to ensure the next loop uses the on-disk file.
                current_assessment = json.loads(next_path.read_text(encoding="utf-8"))

                if attempt == max_runs:
                    print(
                        f"     🚨 Verification failed after {max_runs} runs. "
                        f"Latest file saved to {next_path.parent}"
                    )
                else:
                    print(f"     🔧 Applied {fixes_this_loop} fixes. Saved next version to {next_path.parent}")

    print("\n✅ Phase 6.1 complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", nargs="?", help="PDF filename (e.g., biology.pdf)")
    parser.add_argument("chapter", nargs="?", type=int, help="Specific chapter")
    parser.add_argument("--no-fix", action="store_true", help="Only verify; do not apply fixes")
    args = parser.parse_args()

    run(args.pdf, args.chapter, apply_fixes=not args.no_fix)
